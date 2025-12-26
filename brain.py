# Αρχείο: brain.py
# ΕΚΔΟΣΗ: 2.4.0 - EXPLICIT SOURCES & GENERAL KNOWLEDGE

import google.generativeai as genai
import time
import json
import os
import streamlit as st
import pypdf
from PIL import Image

# --- ΡΥΘΜΙΣΕΙΣ ---
INDEX_FILE = "drive_index.json"
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
        api_key = os.environ.get("GEMINI_KEY")
        if not api_key:
            try: api_key = st.secrets.get("GEMINI_KEY")
            except: pass
        if not api_key: return

    try:
        genai.configure(api_key=api_key)
        try:
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        except: models = []
        
        preferred = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "gemini-1.5-flash"]
        selected = next((m for m in preferred if m in models), "models/gemini-1.5-flash")
        ACTIVE_MODEL_NAME = selected
    except Exception as e:
        LAST_ERROR = str(e)

def extract_text_from_pdf(file_path, max_pages=15):
    text = ""
    try:
        reader = pypdf.PdfReader(file_path)
        for i in range(min(len(reader.pages), max_pages)):
            t = reader.pages[i].extract_text()
            if t: text += f"\n[Σελίδα {i+1}]: {t}"
    except: pass
    return text

def load_comprehensive_context(user_query):
    context = ""
    try:
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
                detected_brand = next((e['brand'] for e in db if e['brand'].lower() in user_query.lower() and e['brand']!="Unknown"), "")
                
                if detected_brand:
                    relevant = [e for e in db if e['brand'] == detected_brand]
                    context = f"\n--- ΕΝΤΟΠΙΣΤΗΚΑΝ ΠΟΛΛΑΠΛΑ MANUALS ΓΙΑ {detected_brand.upper()} ---\n"
                    for item in relevant:
                        context += f"- Τύπος: [{item['meta_type']}] | Αρχείο: {item['name']}\n"
                    context += "\nΟΔΗΓΙΑ: Έχεις πρόσβαση σε ΟΛΑ τα παραπάνω. Συνδύασέ τα.\n"
    except: pass
    return context

def smart_solve(user_query, pdf_files, image_files, audio_file, history):
    global ACTIVE_MODEL_NAME
    if not ACTIVE_MODEL_NAME:
        key = st.secrets.get("GEMINI_KEY")
        if key: setup_ai(key)
        if not ACTIVE_MODEL_NAME: return "⚠️ Σφάλμα API Key."

    try:
        model = genai.GenerativeModel(model_name=ACTIVE_MODEL_NAME, safety_settings=SAFETY_SETTINGS)
        content_parts = []

        # 1. Context Βιβλιοθήκης
        library_ctx = load_comprehensive_context(user_query)

        # 2. ΑΥΣΤΗΡΟ SYSTEM PROMPT ΓΙΑ ΠΗΓΕΣ
        sys_prompt = f"""
        Είσαι ο 'Mastro Nek AI', Senior HVAC Expert.
        
        ΚΑΝΟΝΕΣ ΠΗΓΩΝ & ΓΝΩΣΗΣ:
        1. **ΠΟΛΛΑΠΛΕΣ ΠΗΓΕΣ:** Αν υπάρχουν πολλά manuals (Service, Install, User), διάβασέ τα όλα. Συνδύασε πληροφορίες (π.χ. Υδραυλικά από Install, Βλάβες από Service).
        2. **ΔΙΑΧΩΡΙΣΜΟΣ:** Πρέπει να είσαι ξεκάθαρος.
           - Όταν η πληροφορία είναι από το manual, γράψε: "Σύμφωνα με το [Όνομα Manual]..."
           - Όταν η πληροφορία είναι από τη δική σου γνώση, γράψε: "Βάσει της Γενικής Τεχνικής Εμπειρίας (General Knowledge)..."
        3. **ΚΕΝΑ:** Αν τα manuals δεν καλύπτουν το θέμα, πες το ανοιχτά και δώσε λύση από τη Γενική Γνώση.
        4. **ΑΣΦΑΛΕΙΑ:** Πάντα προειδοποιήσεις για ρεύμα/αέριο.
        
        {library_ctx}
        """
        content_parts.append(sys_prompt)

        # 3. Ιστορικό
        if history:
            h_text = "\nΙΣΤΟΡΙΚΟ:\n" + "\n".join([f"{'ΧΡΗΣΤΗΣ' if m['role']=='user' else 'AI'}: {m['content']}" for m in history[-6:]])
            content_parts.append(h_text)

        # 4. Πολυμέσα
        if audio_file:
            try:
                d = audio_file.getvalue() if hasattr(audio_file, 'getvalue') else audio_file.read()
                content_parts.append({"mime_type": "audio/wav", "data": d})
                content_parts.append("Ανάλυσε τον ήχο/φωνή.")
            except: pass

        if image_files:
            for img in image_files:
                if img: content_parts.append(Image.open(img))
            content_parts.append("Ανάλυσε τις εικόνες.")

        if pdf_files:
            pt = "".join([extract_text_from_pdf(p) for p in pdf_files])
            if pt: content_parts.append(f"PDF ΧΡΗΣΤΗ:\n{pt[:15000]}")

        content_parts.append(f"ΕΡΩΤΗΣΗ: {user_query}")

        response = model.generate_content(content_parts)
        final_text = response.text

        # 5. Προσθήκη Links
        if os.path.exists(INDEX_FILE):
            try:
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    db = json.load(f)
                    links = set()
                    for e in db:
                        if e['name'] in final_text or (e['brand'].lower() in final_text.lower() and e['model'].lower() in final_text.lower()):
                            links.add(f"\n📂 **Πηγή:** [{e['name']}](https://drive.google.com/open?id={e['file_id']})")
                    if links: final_text += "\n\n**Χρησιμοποιήθηκαν τα εξής έγγραφα:**\n" + "".join(list(links)[:5])
            except: pass

        return final_text

    except Exception as e:
        return f"❌ Σφάλμα: {str(e)}"