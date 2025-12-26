# Αρχείο: brain.py
# ΕΚΔΟΣΗ: 2.3.0 - ULTIMATE ROBUST (FULL FEATURES + MOBILE FIX + CROSS REFERENCE)

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

# --- ΡΥΘΜΙΣΕΙΣ ---
INDEX_FILE = "drive_index.json"
ACTIVE_MODEL_NAME = None
LAST_ERROR = ""

# Ρυθμίσεις ασφαλείας (Διατηρήθηκαν από τον παλιό κώδικα)
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def setup_ai(api_key):
    """
    Ρύθμιση του AI με διαχείριση σφαλμάτων για κινητά και Cloud.
    """
    global ACTIVE_MODEL_NAME, LAST_ERROR
    
    # 1. Έλεγχος αν το κλειδί είναι κενό ή None
    if not api_key: 
        # Προσπάθεια ανάκτησης από το περιβάλλον (Fallback για mobile)
        api_key = os.environ.get("GEMINI_KEY")
        if not api_key:
            try:
                api_key = st.secrets.get("GEMINI_KEY")
            except: pass
            
        if not api_key:
            LAST_ERROR = "No API Key provided. Please check Streamlit Secrets."
            return

    try:
        genai.configure(api_key=api_key)
        
        # 2. Εύρεση του καλύτερου μοντέλου (Logic από τον παλιό κώδικα + Νέα μοντέλα)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Προτεραιότητα: Flash 1.5 (Γρήγορο/Stable) -> Pro 1.5 -> Παλιά
        preferred_order = [
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-pro",
            "models/gemini-2.0-flash-exp",
            "gemini-1.5-flash"
        ]
        
        selected_model = None
        for p in preferred_order:
            if p in available_models:
                selected_model = p
                break
        
        if not selected_model and available_models:
            selected_model = available_models[0]
            
        ACTIVE_MODEL_NAME = selected_model
        # print(f"DEBUG: Active Model set to {ACTIVE_MODEL_NAME}")

    except Exception as e:
        LAST_ERROR = f"Setup Error: {str(e)}"
        print(LAST_ERROR)

def extract_text_from_pdf(file_path, max_pages=15):
    """Βοηθητική συνάρτηση για ασφαλή ανάγνωση PDF."""
    text = ""
    try:
        reader = pypdf.PdfReader(file_path)
        count = len(reader.pages)
        limit = min(count, max_pages)
        for i in range(limit):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n{page_text}"
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
    return text

def load_comprehensive_context(user_query):
    """
    ΝΕΑ ΛΕΙΤΟΥΡΓΙΑ: Εντοπίζει ΟΛΑ τα σχετικά αρχεία για τη μάρκα/μοντέλο 
    ώστε το AI να κάνει Cross-Reference (Διασταύρωση).
    """
    context = ""
    try:
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
                
                # Εντοπισμός μάρκας από την ερώτηση
                detected_brand = ""
                # Απλή αναζήτηση μάρκας
                for entry in db:
                    if entry['brand'].lower() in user_query.lower() and entry['brand'] != "Unknown":
                        detected_brand = entry['brand']
                        break
                
                if detected_brand:
                    relevant = [e for e in db if e['brand'] == detected_brand]
                    context = f"\n--- ΒΡΕΘΗΚΑΝ ΣΤΗ ΒΙΒΛΙΟΘΗΚΗ ΤΑ ΕΞΗΣ MANUAL ΓΙΑ {detected_brand.upper()} ---\n"
                    # Κατηγοριοποίηση για το AI
                    for item in relevant:
                        context += f"- Τύπος: [{item['meta_type']}] | Αρχείο: {item['name']}\n"
                    
                    context += "\nΟΔΗΓΙΑ ΠΡΟΣ AI: Χρησιμοποίησε συνδυαστικά πληροφορίες από τα παραπάνω (Service, Installation, Electric) για να δώσεις πλήρη εικόνα.\n"
    except Exception as e:
        print(f"Library Context Error: {e}")
    return context

def smart_solve(user_query, pdf_files, image_files, audio_file, history, mode="General"):
    """
    Η ΚΥΡΙΑ ΣΥΝΑΡΤΗΣΗ ΤΟΥ ΕΓΚΕΦΑΛΟΥ.
    Συνδυάζει: Κείμενο, Ήχο, Εικόνα, PDF Chat, PDF Βιβλιοθήκης.
    """
    global ACTIVE_MODEL_NAME
    
    # Έλεγχος αν έχουμε μοντέλο
    if not ACTIVE_MODEL_NAME:
        # Προσπάθεια ανάκτησης κλειδιού τελευταία στιγμή (για mobile)
        key = st.secrets.get("GEMINI_KEY")
        if key: setup_ai(key)
        
        if not ACTIVE_MODEL_NAME:
            return "⚠️ Σφάλμα Σύνδεσης: Δεν έχει οριστεί το AI Model. Ελέγξτε το API Key."

    try:
        model = genai.GenerativeModel(
            model_name=ACTIVE_MODEL_NAME,
            safety_settings=SAFETY_SETTINGS
        )

        content_parts = []

        # 1. Φόρτωση Πλαισίου Βιβλιοθήκης (Cross-Reference)
        library_context = load_comprehensive_context(user_query)

        # 2. System Instruction (Ο Ρόλος του Mastro Nek)
        system_prompt = f"""
        Είσαι ο 'Mastro Nek AI', ένας έμπειρος Senior Τεχνικός HVAC (Θέρμανση, Κλιματισμός, Αέριο).
        
        ΟΔΗΓΙΕΣ ΑΝΑΛΥΣΗΣ:
        1. ΣΥΝΔΥΑΣΤΙΚΗ ΣΚΕΨΗ: Μην βασίζεσαι σε ένα μόνο έγγραφο. Αν για μια βλάβη (π.χ. Error 104) το Service Manual μιλά για κυκλοφορία και το Installation Manual δείχνει την αντλία, σύνθεσε τις πληροφορίες.
        2. ΤΕΧΝΙΚΗ ΑΝΑΛΥΣΗ: Εξήγησε ΤΙ φταίει και ΓΙΑΤΙ. Δώσε βήματα ελέγχου (1, 2, 3...).
        3. ΑΣΦΑΛΕΙΑ: Πάντα να προειδοποιείς για ρεύμα/αέριο.
        4. ΑΝΑΦΟΡΑ ΠΗΓΩΝ: Αν βρήκες τη λύση σε συγκεκριμένο manual, γράψε το όνομά του.
        
        {library_context}
        """
        content_parts.append(system_prompt)

        # 3. Ιστορικό Συνομιλίας
        if history:
            history_text = "\nΙΣΤΟΡΙΚΟ ΣΥΖΗΤΗΣΗΣ:\n"
            for msg in history[-6:]:
                role = "ΧΡΗΣΤΗΣ" if msg["role"] == "user" else "MASTRO NEK"
                history_text += f"{role}: {msg['content']}\n"
            content_parts.append(history_text)

        # 4. Διαχείριση Ήχου (Διατηρήθηκε η παλιά λογική)
        if audio_file:
            # Το Gemini Flash υποστηρίζει ήχο. Τον στέλνουμε ως blob.
            try:
                audio_bytes = audio_file.getvalue()
                content_parts.append({
                    "mime_type": "audio/wav", # Ή audio/mp3, το Gemini συνήθως το βρίσκει
                    "data": audio_bytes
                })
                content_parts.append("Ανάλυσε τον ήχο της βλάβης ή την φωνητική ερώτηση.")
            except Exception as e:
                content_parts.append(f"Σφάλμα φόρτωσης ήχου: {e}")

        # 5. Διαχείριση Εικόνων
        if image_files:
            for img_file in image_files:
                if img_file:
                    try:
                        img = Image.open(img_file)
                        content_parts.append(img)
                    except: pass
            content_parts.append("Δες τις φωτογραφίες για κωδικούς, πινακίδες ή βλάβες.")

        # 6. Διαχείριση PDF που ανέβασε ο χρήστης ΤΩΡΑ στο Chat
        if pdf_files:
            pdf_text_combined = ""
            for pdf in pdf_files:
                pdf_text_combined += extract_text_from_pdf(pdf)
            if pdf_text_combined:
                content_parts.append(f"ΠΕΡΙΕΧΟΜΕΝΟ PDF ΧΡΗΣΤΗ:\n{pdf_text_combined[:20000]}")

        # 7. Η Ερώτηση
        content_parts.append(f"ΕΡΩΤΗΣΗ: {user_query}")

        # 8. Κλήση AI
        response = model.generate_content(content_parts)
        final_text = response.text

        # 9. Προσθήκη Links από τη Βιβλιοθήκη (Post-Processing)
        if os.path.exists(INDEX_FILE):
            try:
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    db = json.load(f)
                    links = []
                    # Ψάχνουμε αν το κείμενο της απάντησης περιέχει αναφορές σε αρχεία
                    for entry in db:
                        # Αν το όνομα του αρχείου ή ο συνδυασμός Μάρκα+Μοντέλο υπάρχει στην απάντηση
                        is_relevant = (entry['name'] in final_text) or \
                                      (entry['brand'].lower() in final_text.lower() and entry['model'].lower() in final_text.lower())
                        
                        if is_relevant:
                            link_md = f"\n📂 **Manual:** [{entry['name']}](https://drive.google.com/open?id={entry['file_id']})"
                            if link_md not in links: links.append(link_md)
                    
                    if links:
                        # Βάζουμε μέχρι 5 links για να μην γεμίσει ο τόπος
                        final_text += "\n\n**Σχετικά Έγγραφα:**\n" + "".join(list(set(links))[:5])
            except: pass

        return final_text

    except Exception as e:
        return f"❌ Σφάλμα Mastro Nek: {str(e)}\n(Δοκίμασε ξανά ή έλεγξε το API Key)"