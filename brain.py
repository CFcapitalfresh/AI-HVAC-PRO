import google.generativeai as genai
import time
import json
import os
import drive 
import streamlit as st
import pypdf
import organizer
from google.api_core import exceptions
import re
from PIL import Image # Για τις εικόνες

ACTIVE_MODEL_NAME = None
LAST_ERROR = ""

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def setup_ai(api_key):
    global ACTIVE_MODEL_NAME, LAST_ERROR
    if not api_key: 
        LAST_ERROR = "No API Key provided."
        return
    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Προτεραιότητα σε μοντέλα που βλέπουν και ακούνε (Flash/Pro)
        preferred_order = [
            "gemini-2.0-flash-exp", "models/gemini-2.0-flash-exp",
            "gemini-1.5-pro", "models/gemini-1.5-pro",
            "gemini-1.5-flash", "models/gemini-1.5-flash"
        ]
        
        selected_model = None
        for p in preferred_order:
            if p in available_models:
                selected_model = p
                break
        
        if not selected_model:
            for m in available_models:
                if "gemini" in m: selected_model = m; break
        
        if selected_model:
            ACTIVE_MODEL_NAME = selected_model
            print(f"✅ AI Connected using: {ACTIVE_MODEL_NAME}")
        else:
            LAST_ERROR = "No compatible Gemini models found."
    except Exception as e: 
        LAST_ERROR = str(e)

def extract_text_from_pdf(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages):
            if i > 250: break 
            extract = page.extract_text()
            if extract: text += extract + "\n"
        return text
    except: return None

def find_best_manual_locally(query):
    # (Ίδια λογική με πριν για αναζήτηση manual)
    if not os.path.exists("drive_index.json"): return None
    try:
        with open("drive_index.json", "r", encoding="utf-8") as f: data = json.load(f)
    except: return None
        
    query_lower = query.lower()
    query_words = [w for w in query_lower.split() if len(w) > 2]
    best_file = None
    best_score = -500
    
    for file in data:
        score = 0
        real_model = str(file.get('real_model', '')).lower()
        search_terms = str(file.get('search_terms', '')).lower()
        for word in query_words:
            if word in real_model or word in search_terms: score += 100
        if score > best_score:
            best_score = score
            best_file = file
    return best_file

# --- Η ΝΕΑ ΕΞΥΠΝΗ ΣΥΝΑΡΤΗΣΗ ΜΕ ΟΡΑΣΗ ΚΑΙ ΑΚΟΗ ---
def smart_solve(prompt, pdf_files, image_files, audio_file, history, tech_type):
    if not ACTIVE_MODEL_NAME: return f"⚠️ System Error: {LAST_ERROR}"
    
    try:
        model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
    except Exception as e: return f"⚠️ Model Error: {e}"
    
    # 1. Προετοιμασία περιεχομένου για το AI
    content_parts = []
    
    # Προσθήκη Κειμένου Προτροπής
    base_prompt = f"ROLE: Είσαι Έμπειρος Αρχιτεχνίτης {tech_type} (Mastro Nek). Απάντα σύντομα και τεχνικά."
    if prompt:
        content_parts.append(base_prompt + "\nΕΡΩΤΗΣΗ: " + prompt)
    else:
        content_parts.append(base_prompt + "\nΑνάλυσε τα αρχεία που σου έστειλα (Εικόνα/Ήχο) και πες μου τη βλάβη.")

    # 2. Προσθήκη Εικόνων
    if image_files:
        for img_path in image_files:
            img = Image.open(img_path)
            content_parts.append(img)
            content_parts.append("Αυτή είναι η φωτογραφία της μονάδας/βλάβης.")

    # 3. Προσθήκη Ήχου (Φωνητική εντολή)
    if audio_file:
        # Το Gemini Flash υποστηρίζει ήχο απευθείας!
        # Χρειάζεται να το στείλουμε ως blob, αλλά για απλότητα εδώ
        # θα βασιστούμε στο ότι το upload στο UI δίνει αρχείο.
        # *Σημείωση: Το audio θέλει ειδική διαχείριση στο API, 
        # εδώ θα κάνουμε μια απλή προσπάθεια transcription αν αποτύχει το direct.*
        content_parts.append({
            "mime_type": "audio/wav",
            "data": audio_file.getvalue()
        })
        content_parts.append("Αυτή είναι η φωνητική εντολή του τεχνικού. Απάντα σε αυτό που ρωτάει.")

    # 4. Προσθήκη PDF Manuals (Αν υπάρχουν)
    if pdf_files:
        for p in pdf_files:
            text = extract_text_from_pdf(p)
            if text: content_parts.append(f"MANUAL DATA: {text[:5000]}") # Μικρό απόσπασμα για ταχύτητα

    # 5. Αναζήτηση στη Βιβλιοθήκη (Αν δεν έχουμε ανεβάσει κάτι τώρα)
    if not pdf_files and not image_files and prompt:
        best_file = find_best_manual_locally(prompt)
        if best_file:
            pdf_path = drive.get_file_path(best_file['id'])
            if pdf_path:
                text = extract_text_from_pdf(pdf_path)
                content_parts.append(f"ΒΡΗΚΑ ΑΥΤΟ ΤΟ MANUAL ΣΤΗ ΒΙΒΛΙΟΘΗΚΗ: {text[:4000]}")

    try:
        # Κλήση στο AI με όλα τα δεδομένα μαζί!
        response = model.generate_content(content_parts, safety_settings=SAFETY_SETTINGS)
        return response.text
    except Exception as e:
        return f"⚠️ Σφάλμα AI: {e}"