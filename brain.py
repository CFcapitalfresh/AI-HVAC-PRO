# Αρχείο: brain.py
# ΕΚΔΟΣΗ: 3.0.0 - AGGRESSIVE LINKING & SOURCE TRUTH

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
    """Ασφαλής ανάκτηση κλειδιού."""
    key = os.environ.get("GEMINI_KEY")
    if not key:
        try: key = st.secrets.get("GEMINI_KEY")
        except: pass
    return key

def find_working_model():
    """Βρίσκει το πρώτο διαθέσιμο μοντέλο (Fix 404)."""
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferences = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        for p in preferences:
            if p in models: return p
        return models[0] if models else "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

def setup_ai(api_key=None):
    global ACTIVE_MODEL_NAME
    if not api_key: api_key = get_api_key()
    if not api_key: return "MISSING_KEY"

    try:
        genai.configure(api_key=api_key)
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

def get_relevant_files(user_query):
    """Επιστρέφει ΛΙΣΤΑ με τα σχετικά αρχεία για να φτιάξουμε τα links μετά."""
    relevant_items = []
    try:
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
                # Βρες τη μάρκα
                detected_brand = next((e['brand'] for e in db if e['brand'].lower() in user_query.lower() and e['brand']!="Unknown"), "")
                
                if detected_brand:
                    # Φιλτράρουμε όλα τα αρχεία αυτής της μάρκας
                    relevant_items = [e for e in db if e['brand'] == detected_brand]
    except: pass
    return relevant_items

def smart_solve(user_query, pdf_files, image_files, audio_file, history):
    global ACTIVE_MODEL_NAME
    
    status = setup_ai(None)
    if status == "MISSING_KEY": return "⚠️ Σφάλμα: Δεν βρέθηκε κλειδί API."
    if not ACTIVE_MODEL_NAME: return "⚠️ Σφάλμα Σύνδεσης AI."

    try:
        model = genai.GenerativeModel(model_name=ACTIVE_MODEL_NAME, safety_settings=SAFETY_SETTINGS)
        content_parts = []

        # 1. Εύρεση Σχετικών Αρχείων Βιβλιοθήκης
        relevant_docs = get_relevant_files(user_query)
        
        # Δημιουργία Context κειμένου για το AI
        library_ctx = ""
        if relevant_docs:
            library_ctx = f"\n--- ΕΝΤΟΠΙΣΤΗΚΑΝ ΤΑ ΕΞΗΣ MANUALS ΣΤΗ ΒΙΒΛΙΟΘΗΚΗ ({len(relevant_docs)}) ---\n"
            for item in relevant_docs:
                library_ctx += f"- Τύπος: {item['meta_type']} | Όνομα: {item['name']}\n"
            library_ctx += "\nΟΔΗΓΙΑ: Έχεις πρόσβαση στους τίτλους αυτών των αρχείων. Αν η ερώτηση αφορά κωδικό σφάλματος (π.χ. 104), συνδύασε τη γνώση σου για αυτό το μοντέλο με τα manuals.\n"

        # 2. SYSTEM PROMPT (ΑΥΣΤΗΡΟ)
        sys_prompt = f"""
        Είσαι ο 'Mastro Nek AI', Senior HVAC Expert.
        
        ΟΔΗΓΙΕΣ ΑΠΑΝΤΗΣΗΣ:
        1. **ΔΙΑΧΩΡΙΣΜΟΣ ΠΗΓΩΝ (Υποχρεωτικό):**
           - Πρέπει να ξεκινάς την τεχνική ανάλυση λέγοντας: "📚 **Σύμφωνα με τα εγχειρίδια (Manuals):**" ή "🔧 **Βάσει Γενικής Εμπειρίας:**".
           - Αν η απάντηση προκύπτει από συνδυασμό (π.χ. το manual λέει "Error 104", η εμπειρία λέει "Κυκλοφορητής"), γράψε το ξεκάθαρα.
        
        2. **ΠΟΛΛΑΠΛΗ ΑΝΑΛΥΣΗ:**
           - Μην κοιτάς μόνο το Service Manual. Σκέψου και το Installation Manual (υδραυλικά) και το User Manual (reset).
        
        3. **ΤΕΧΝΙΚΗ ΑΚΡΙΒΕΙΑ:**
           - Προσοχή στους κωδικούς! (Π.χ. Ariston Error 104 = Insufficient Circulation/Pump issues, όχι πάντα NTC).
           
        4. **ΑΣΦΑΛΕΙΑ:** Πάντα προειδοποιήσεις.
        
        {library_ctx}
        """
        content_parts.append(sys_prompt)

        # 3. Ιστορικό
        if history:
            h_text = "\nΙΣΤΟΡΙΚΟ:\n" + "\n".join([f"{'User' if m['role']=='user' else 'AI'}: {m['content']}" for m in history[-6:]])
            content_parts.append(h_text)

        # 4. Πολυμέσα
        if audio_file:
            try:
                d = audio_file.getvalue() if hasattr(audio_file, 'getvalue') else audio_file.read()
                content_parts.append({"mime_type": "audio/wav", "data": d})
                content_parts.append("Ανάλυσε τον ήχο.")
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

        # 5. ΑΥΤΟΜΑΤΗ ΠΡΟΣΘΗΚΗ LINKS (AGGRESSIVE MODE)
        # Τώρα προσθέτουμε τα links ΑΝΕΞΑΡΤΗΤΑ από το αν τα ανέφερε το AI, 
        # αρκεί να είναι σχετικά με τη μάρκα που συζητάμε.
        if relevant_docs:
            links_md = []
            for item in relevant_docs:
                # Φιλτράρουμε να μην βάλουμε άσχετα αν η λίστα είναι τεράστια, 
                # αλλά εδώ βάζουμε τα 5 πιο σχετικά (π.χ. Service, User).
                link = f"📂 **[{item['meta_type']}] {item['name']}**: [Άνοιγμα Αρχείου](https://drive.google.com/open?id={item['file_id']})"
                links_md.append(link)
            
            # Παίρνουμε τα 5 πρώτα/σημαντικότερα
            final_text += "\n\n---\n### 📎 Σχετικά Εγχειρίδια από τη Βιβλιοθήκη:\n"
            final_text += "\n".join(links_md[:6])
            
        return final_text

    except Exception as e:
        return f"❌ Σφάλμα AI: {str(e)}"