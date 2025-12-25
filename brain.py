# Αρχείο: brain.py
# ΕΚΔΟΣΗ: 2.2.0 - CROSS-REFERENCE EDITION

import google.generativeai as genai
import PIL.Image
import os
import json
import pandas as pd
import pypdf
import re
import drive

INDEX_FILE = "drive_index.json"

def setup_ai(api_key):
    if api_key:
        genai.configure(api_key=api_key)

def find_best_model():
    """Επιλέγει δυναμικά το μοντέλο για αποφυγή σφαλμάτων 404."""
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-2.0-flash-exp']:
            if pref in available_models: return pref
        return available_models[0]
    except: return 'gemini-1.5-flash'

def load_comprehensive_context(user_query):
    """
    Εντοπίζει ΟΛΑ τα σχετικά αρχεία για τη μάρκα/μοντέλο 
    ώστε το AI να έχει πλήρη εικόνα της βιβλιοθήκης.
    """
    context = ""
    try:
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
                
                # Εντοπισμός μάρκας από την ερώτηση
                detected_brand = ""
                for entry in db:
                    if entry['brand'].lower() in user_query.lower():
                        detected_brand = entry['brand']
                        break
                
                if detected_brand:
                    relevant = [e for e in db if e['brand'] == detected_brand]
                    context = f"\n--- ΔΙΑΘΕΣΙΜΑ ΕΓΧΕΙΡΙΔΙΑ ΓΙΑ {detected_brand.upper()} ---\n"
                    for item in relevant:
                        context += f"- [{item['meta_type']}]: {item['name']}\n"
                    context += "\nΟΔΗΓΙΑ: Χρησιμοποίησε συνδυαστικά πληροφορίες από τα παραπάνω αν χρειαστεί.\n"
    except: pass
    return context

def smart_solve(user_query, pdf_paths, img_files, audio_file, history, mode="General"):
    try:
        selected_model = find_best_model()
        model = genai.GenerativeModel(selected_model)
        
        # Φόρτωση σφαιρικού πλαισίου (Cross-Reference)
        library_context = load_comprehensive_context(user_query)
        
        system_instruction = f"""
        Είσαι ο 'Mastro Nek AI', ένας Senior HVAC Expert.
        
        ΣΤΡΑΤΗΓΙΚΗ ΑΝΑΛΥΣΗΣ:
        1. ΣΥΝΔΥΑΣΤΙΚΗ ΣΚΕΨΗ: Μην βασίζεσαι σε ένα μόνο έγγραφο. Αν για μια βλάβη (π.χ. Error 104) το Service Manual μιλά για κυκλοφορία και το Installation Manual δείχνει τη θέση της αντλίας, σύνθεσε τις πληροφορίες.
        2. ΔΙΑΣΤΑΥΡΩΣΗ: Αν ένα έγγραφο (π.χ. Electric Diagram) δεν επαρκεί για την ερμηνεία μιας βλάβης, ανάφερέ το και χρησιμοποίησε τη γενική τεχνική σου γνώση για να συμπληρώσεις τα κενά.
        3. ΑΝΑΦΟΡΑ ΠΗΓΩΝ: Αν η απάντηση προέρχεται από 2 ή 3 διαφορετικά manuals, ανάφερέ τα όλα.
        4. ΤΕΧΝΙΚΗ ΑΚΡΙΒΕΙΑ: Δώσε έμφαση στις λεπτομέρειες που κάνουν τη διαφορά (π.χ. ρυθμίσεις παραμέτρων, έλεγχος αισθητήρων NTC).
        
        {library_context}
        """
        
        contents = [system_instruction]
        if history:
            for msg in history[-6:]:
                contents.append(f"{msg['role'].upper()}: {msg['content']}")

        # Επεξεργασία Πολυμέσων (Ήχος/Εικόνα)
        if audio_file:
            contents.append({"mime_type": "audio/wav", "data": audio_file.read() if hasattr(audio_file, 'read') else audio_file})
        if img_files:
            for img in img_files:
                if img: contents.append(PIL.Image.open(img))

        # Ανάλυση PDF (Ανέβασμα από τον χρήστη)
        if pdf_paths:
            combined_pdf_text = ""
            for path in pdf_paths:
                try:
                    reader = pypdf.PdfReader(path)
                    for i in range(min(15, len(reader.pages))):
                        combined_pdf_text += f"--- Από αρχείο {os.path.basename(path)} ---\n"
                        combined_pdf_text += reader.pages[i].extract_text() + "\n"
                except: pass
            contents.append(f"ΠΕΡΙΕΧΟΜΕΝΟ ΑΝΕΒΑΣΜΕΝΩΝ PDF:\n{combined_pdf_text[:20000]}")

        contents.append(f"ΕΡΩΤΗΣΗ ΧΡΗΣΤΗ: {user_query}")
        
        response = model.generate_content(contents)
        final_text = response.text

        # Προσθήκη Πολλαπλών Links Πηγών
        if os.path.exists(INDEX_FILE):
            try:
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    db = json.load(f)
                    links = []
                    # Εντοπισμός όλων των σχετικών αρχείων που αναφέρθηκαν ή είναι σχετικά
                    for entry in db:
                        if entry['brand'].lower() in final_text.lower() and entry['model'].lower() in final_text.lower():
                            link_md = f"\n📂 **Σχετικό Έγγραφο:** [{entry['name']}](https://drive.google.com/open?id={entry['file_id']})"
                            if link_md not in links: links.append(link_md)
                    
                    if links:
                        final_text += "\n\n**Πηγές από τη Βιβλιοθήκη σου:**\n" + "".join(links)
            except: pass

        return final_text
    except Exception as e:
        return f"❌ Σφάλμα συστήματος: {str(e)}"