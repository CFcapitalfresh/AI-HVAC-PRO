# Αρχείο: brain.py
# ΕΚΔΟΣΗ: 2.5.0 - SELF-HEALING & EXPLICIT SOURCES

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

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def get_api_key():
    """Ασφαλής ανάκτηση κλειδιού από παντού."""
    key = os.environ.get("GEMINI_KEY")
    if not key:
        try: key = st.secrets.get("GEMINI_KEY")
        except: pass
    return key

def find_working_model():
    """Βρίσκει το πρώτο διαθέσιμο μοντέλο για να αποφύγει το 404."""
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Σειρά προτίμησης: Flash (γρήγορο), Pro (έξυπνο), Old Pro
        preferences = [
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-pro", 
            "models/gemini-pro"
        ]
        
        # Επιστρέφει το πρώτο που υπάρχει στη λίστα της Google
        for p in preferences:
            if p in models: return p
            
        return models[0] if models else "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash" # Λύση ανάγκης

def setup_ai(api_key):
    global ACTIVE_MODEL_NAME
    
    # Χειροκίνητη ή Αυτόματη εύρεση κλειδιού
    if not api_key: api_key = get_api_key()
    if not api_key: return "MISSING_KEY"

    try:
        genai.configure(api_key=api_key)
        # ΕΔΩ ΓΙΝΕΤΑΙ Η ΔΙΟΡΘΩΣΗ ΤΟΥ 404
        ACTIVE_MODEL_NAME = find_working_model()
        return "OK"
    except Exception as e:
        return str(e)

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
    
    # Setup κάθε φορά για να είμαστε σίγουροι
    status = setup_ai(None) 
    if status == "MISSING_KEY": return "⚠️ Σφάλμα: Δεν βρέθηκε κλειδί API (Streamlit Secrets)."
    if not ACTIVE_MODEL_NAME: return "⚠️ Σφάλμα Σύνδεσης AI."

    try:
        model = genai.GenerativeModel(model_name=ACTIVE_MODEL_NAME, safety_settings=SAFETY_SETTINGS)
        content_parts = []

        # 1. Context
        library_ctx = load_comprehensive_context(user_query)

        # 2. PROMPT
        sys_prompt = f"""
        Είσαι ο 'Mastro Nek AI', Senior HVAC Expert.
        
        ΟΔΗΓΙΕΣ ΠΗΓΩΝ:
        1. **ΔΙΑΧΩΡΙΣΜΟΣ:**
           - Αν η πληροφορία υπάρχει στο manual, ξεκίνα με: "✅ **Σύμφωνα με το [Όνομα Manual]:**"
           - Αν δεν υπάρχει, ξεκίνα με: "🔧 **Βάσει Γενικής Εμπειρίας (General Knowledge):**"
           - Αν υπάρχει και στα δύο, πες το: "Το manual λέει X, αλλά η εμπειρία δείχνει και Y."
        2. **ΠΟΛΛΑΠΛΑ MANUALS:** Αν έχεις Service, Install και User manuals, ψάξε σε όλα.
        3. **ΑΣΦΑΛΕΙΑ:** Πάντα προειδοποιήσεις.
        
        {library_ctx}
        """
        content_parts.append(sys_prompt)

        # 3. History
        if history:
            h_text = "\nΙΣΤΟΡΙΚΟ:\n" + "\n".join([f"{'User' if m['role']=='user' else 'AI'}: {m['content']}" for m in history[-6:]])
            content_parts.append(h_text)

        # 4. Multimedia
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

        # 5. Links
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
        return f"❌ Σφάλμα AI: {str(e)}"