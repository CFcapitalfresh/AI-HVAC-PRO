# Αρχείο: brain.py (v27 - Logic & Contradiction Fix)
import google.generativeai as genai
import time
import json
import os
import drive 
import streamlit as st
import pypdf
from google.api_core import exceptions
import re

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
    if not api_key: return
    genai.configure(api_key=api_key)
    try:
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferred = [m for m in all_models if 'gemini-1.5-flash' in m]
        if preferred: ACTIVE_MODEL_NAME = preferred[0]
        elif all_models: ACTIVE_MODEL_NAME = all_models[0]
        else: LAST_ERROR = "No models found."
        print(f"✅ AI: {ACTIVE_MODEL_NAME}")
    except Exception as e: LAST_ERROR = str(e)

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

def find_relevant_chunk(full_text, query):
    if not full_text: return ""
    clean_query = query.lower().replace("erron", "error")
    code_match = re.search(r'\b\d{3}\b', clean_query)
    search_terms = [clean_query]
    if code_match:
        code = code_match.group(0)
        search_terms.append(code)
        search_terms.append(f"{code[0]} {code[1:]}")
    
    lines = full_text.split('\n')
    relevant_lines = []
    
    for i, line in enumerate(lines):
        if any(term in line.lower() for term in search_terms if len(term) > 2):
            start = max(0, i - 2)
            end = min(len(lines), i + 20)
            relevant_lines.append("\n".join(lines[start:end]))

    if relevant_lines: return "\n--- EUREKA ---\n".join(relevant_lines)[:5000]
    else: return full_text[:800]

def find_best_manual_locally(query):
    if not os.path.exists("drive_index.json"): return None
    try:
        with open("drive_index.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except: return None
        
    query_lower = query.lower()
    query_words = [w for w in query_lower.split() if len(w) > 2]
    
    best_file = None
    best_score = -500
    
    for file in data:
        score = 0
        real_model = str(file.get('real_model', '')).lower()
        file_type = str(file.get('type', '')).lower()
        
        # 1. Ταύτιση Μοντέλου
        model_score = 0
        for word in query_words:
            if word in real_model: model_score += 100
        
        if "clas" in query_lower and "genus" in real_model: model_score -= 500
        if "one" in query_lower and "premium" in real_model: model_score -= 500
        
        # 2. Ταύτιση Τύπου
        type_score = 0
        is_tech_query = any(x in query_lower for x in ['error', 'code', '101', '501', 'βλαβη', 'e1'])
        if is_tech_query and "service" in file_type: type_score += 200
        
        score = model_score + type_score
        
        if score > best_score:
            best_score = score
            best_file = file
            
    return best_file

def smart_solve(prompt, user_uploads, history, tech_type):
    if not ACTIVE_MODEL_NAME: return f"⚠️ {LAST_ERROR}"
    model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
    
    context_text = ""
    source_info = "AI General Knowledge"

    if not user_uploads:
        best_file = find_best_manual_locally(prompt)
        if best_file:
            st.toast(f"Manual: {best_file['real_model']}", icon="🧠")
            pdf_path = drive.get_file_path(best_file['id'])
            if pdf_path:
                full_text = extract_text_from_pdf(pdf_path)
                found_chunk = find_relevant_chunk(full_text, prompt)
                if len(found_chunk) > 50:
                    context_text = found_chunk
                    source_info = f"MANUAL: {best_file['real_model']}"
                else:
                    source_info = f"Manual {best_file['real_model']} checked (no code found)."

    if user_uploads:
        for p in user_uploads:
            if p.endswith(".pdf"):
                full_text = extract_text_from_pdf(p)
                context_text += "\n" + find_relevant_chunk(full_text, prompt)
                source_info = "User Uploaded File"

    # --- ΤΟ ΝΕΟ ΕΞΥΠΝΟ PROMPT ---
    final_prompt = f"""
    ROLE: Είσαι Έμπειρος Αρχιτεχνίτης {tech_type} (20 χρόνια εμπειρία). Μιλάς Ελληνικά.
    
    CONTEXT:
    Πηγή: {source_info}
    Απόσπασμα Manual: {context_text}
    
    ΙΣΤΟΡΙΚΟ ΣΥΖΗΤΗΣΗΣ: {history}
    ΤΡΕΧΟΥΣΑ ΕΡΩΤΗΣΗ/ΠΑΡΑΤΗΡΗΣΗ ΠΕΛΑΤΗ: {prompt}
    
    ΚΡΙΣΙΜΕΣ ΟΔΗΓΙΕΣ ΛΟΓΙΚΗΣ (Logic Check):
    1. **ΕΛΕΓΧΟΣ ΑΝΤΙΦΑΣΕΩΝ:** Αν ο πελάτης λέει κάτι (π.χ. "Η πίεση είναι 1.5 bar") που ΑΝΤΙΦΑΣΚΕΙ με τον κωδικό βλάβης (π.χ. "Error E1" = Χαμηλή πίεση), ΜΗΝ πεις απλά "Μπράβο, όλα καλά".
    2. **ΕΡΜΗΝΕΙΑ:** Εξήγησε ότι υπάρχει ασυμφωνία. Π.χ. "Αφού βλέπεις 1.5 bar αλλά έχεις E1, τότε μάλλον κολλάει το μανόμετρο ή χάλασε ο αισθητήρας πίεσης".
    3. **ΒΗΜΑΤΑ:** Δώσε λύση για το πώς να ελέγξει ποιο από τα δύο λέει ψέματα (π.χ. "Άδειασε λίγο νερό να δεις αν πέφτει ο δείκτης").
    4. **MANUAL vs ΕΜΠΕΙΡΙΑ:** Αν το Manual δεν έχει τη λύση, δώσε τη λύση της εμπειρίας σου ξεκάθαρα.
    
    Ύφος: Επαγγελματικό, τεχνικό αλλά κατανοητό, σαν να μιλάς σε συνάδελφο.
    """

    try:
        return model.generate_content(final_prompt, safety_settings=SAFETY_SETTINGS).text
    except Exception as e:
        return f"⚠️ Error: {e}"