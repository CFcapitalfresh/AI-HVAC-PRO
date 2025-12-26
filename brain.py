# Αρχείο: brain.py
# ΕΚΔΟΣΗ: 3.1.0 (MOBILE SAFE & REMOTE DB AWARE)

import google.generativeai as genai
import os
import streamlit as st
import pypdf
from PIL import Image
import remote_db # Για να μπορεί να διαβάζει τα links αν χρειαστεί

# Ρυθμίσεις Ασφαλείας
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def get_api_key():
    key = os.environ.get("GEMINI_KEY")
    if not key:
        try: key = st.secrets.get("GEMINI_KEY")
        except: pass
    return key

def find_working_model():
    """Αυτόματη εύρεση μοντέλου."""
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferences = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        for p in preferences:
            if p in models: return p
        return models[0] if models else "models/gemini-1.5-flash"
    except: return "models/gemini-1.5-flash"

def setup_ai():
    api_key = get_api_key()
    if not api_key: return None, "MISSING_KEY"
    try:
        genai.configure(api_key=api_key)
        model_name = find_working_model()
        return model_name, "OK"
    except Exception as e:
        return None, str(e)

def extract_text_from_pdf_safe(pdf_files):
    """ΑΣΦΑΛΗΣ ανάγνωση PDF. Αν είναι None, επιστρέφει κενό."""
    if not pdf_files or not isinstance(pdf_files, list):
        return ""
    
    text = ""
    for file_path in pdf_files:
        if file_path is None: continue # Προσπέραση αντικειμένων None
        try:
            reader = pypdf.PdfReader(file_path)
            for i in range(min(len(reader.pages), 10)):
                t = reader.pages[i].extract_text()
                if t: text += f"\n--- PDF TEXT ---\n{t}"
        except: pass
    return text

def smart_solve(user_query, pdf_files=None, image_files=None, audio_file=None, history=[]):
    """
    Η Κύρια Συνάρτηση. Έχει προστασία για να μην κρασάρει αν λάβει None.
    """
    # 1. SANITIZATION (ΚΑΘΑΡΙΣΜΟΣ ΔΕΔΟΜΕΝΩΝ ΑΠΟ ΚΙΝΗΤΟ)
    # Βεβαιωνόμαστε ότι είναι λίστες και όχι None
    if pdf_files is None: pdf_files = []
    if image_files is None: image_files = []
    if not user_query: user_query = "Ανάλυση Δεδομένων"

    # 2. SETUP
    model_name, status = setup_ai()
    if status != "OK": return f"⚠️ Σφάλμα AI: {status}"

    try:
        model = genai.GenerativeModel(model_name=model_name, safety_settings=SAFETY_SETTINGS)
        content_parts = []

        # 3. CONTEXT (Από τη μνήμη RAM που φόρτωσε το remote_db)
        library_ctx = ""
        relevant_docs = []
        
        # Ψάχνουμε στη cache της εφαρμογής (που έχει γεμίσει το remote_db)
        if 'library_cache' in st.session_state and st.session_state['library_cache']:
            db = st.session_state['library_cache']
            # Απλή αναζήτηση λέξεων κλειδιών
            query_parts = user_query.lower().split()
            
            for item in db:
                # Αν η μάρκα υπάρχει στην ερώτηση
                if item.get('brand', '').lower() in user_query.lower():
                    relevant_docs.append(item)
            
            if relevant_docs:
                library_ctx = f"\n--- ΣΧΕΤΙΚΑ MANUAL ΣΤΗ ΒΙΒΛΙΟΘΗΚΗ ({len(relevant_docs)}) ---\n"
                for doc in relevant_docs[:10]: # Μέχρι 10 για να μην γεμίζει
                    library_ctx += f"- {doc['name']} ({doc['meta_type']})\n"

        # 4. PROMPT
        sys_prompt = f"""
        Είσαι ο 'Mastro Nek AI', Senior HVAC Expert.
        
        ΔΕΔΟΜΕΝΑ ΒΙΒΛΙΟΘΗΚΗΣ:
        {library_ctx}
        
        ΟΔΗΓΙΕΣ:
        1. Αν η απάντηση υπάρχει στα παραπάνω manuals, γράψε: "✅ Σύμφωνα με το αρχείο [Όνομα]..."
        2. Αν όχι, γράψε: "🔧 Βάσει Γενικής Εμπειρίας..."
        3. Να είσαι αναλυτικός και να προειδοποιείς για ασφάλεια.
        """
        content_parts.append(sys_prompt)

        # 5. ΠΡΟΣΘΗΚΗ ΠΕΡΙΕΧΟΜΕΝΟΥ
        # Ιστορικό
        if history:
            h_text = "\nΙΣΤΟΡΙΚΟ:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history[-5:]])
            content_parts.append(h_text)

        # Εικόνες (Με έλεγχο None)
        for img in image_files:
            if img: content_parts.append(Image.open(img))

        # Ήχος
        if audio_file:
            content_parts.append({"mime_type": "audio/wav", "data": audio_file.read()})
            content_parts.append("Ανάλυσε τον ήχο.")

        # PDF που ανέβασε ο χρήστης τώρα
        pdf_text = extract_text_from_pdf_safe(pdf_files)
        if pdf_text: content_parts.append(pdf_text)

        # Ερώτηση
        content_parts.append(f"Ερώτηση: {user_query}")

        # 6. ΕΚΤΕΛΕΣΗ
        response = model.generate_content(content_parts)
        final_text = response.text

        # 7. LINKS (Post-processing)
        if relevant_docs:
            final_text += "\n\n---\n**Σχετικά Έγγραφα:**\n"
            added = 0
            for doc in relevant_docs:
                if added >= 5: break
                link = doc.get('link', '#') # Αν δεν έχει link, βάλε #
                # Χρήση του 'webViewLink' που παίρνουμε από το Drive API
                final_text += f"📂 [{doc['meta_type']}] [{doc['name']}]({link})\n"
                added += 1

        return final_text

    except Exception as e:
        return f"❌ Σφάλμα AI: {str(e)}"