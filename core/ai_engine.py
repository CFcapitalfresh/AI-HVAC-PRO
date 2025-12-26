"""
CORE MODULE: AI ENGINE (BRAIN) - SAFETY FIRST EDITION
-----------------------------------------------------
Updates:
- STRICT SAFETY PROTOCOL: Warns user if specific manual is missing.
- Verification Logic: Checks match between User Query and Context Files.
- Auto-Discovery: Finds the best available Gemini model automatically.
"""

import google.generativeai as genai
import logging
from core.config_loader import ConfigLoader

logger = logging.getLogger("Core.AI")

class AIEngine:
    def __init__(self):
        self.api_key = ConfigLoader.get_gemini_key()
        self.model = None
        self._setup()

    def _setup(self):
        """Αρχική ρύθμιση με αυτόματη εύρεση μοντέλου."""
        if not self.api_key:
            logger.critical("AI Setup Failed: No API Key.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            best_model = self._find_best_model()
            logger.info(f"✅ AI selected model: {best_model}")
            self.model = genai.GenerativeModel(best_model)
        except Exception as e:
            logger.critical(f"AI Setup Error: {e}")

    def _find_best_model(self):
        """Βρίσκει το καλύτερο διαθέσιμο μοντέλο για να αποφύγει τα 404 errors."""
        try:
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Λίστα προτεραιότητας
            priorities = [
                "models/gemini-1.5-pro-latest", 
                "models/gemini-1.5-pro", 
                "models/gemini-1.5-flash",
                "models/gemini-1.5-flash-latest",
                "models/gemini-pro"
            ]
            
            for p in priorities:
                if p in available: return p
            
            return available[0] if available else "models/gemini-pro"
        except: return "models/gemini-pro"

    def get_chat_response(self, chat_history, context_files="", lang="gr"):
        """
        Εκτελεί τη συνομιλία με το Πρωτόκολλο Ασφαλείας.
        """
        if not self.model: return "⚠️ AI System Offline."

        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        # --- ΤΟ ΝΕΟ ΑΥΣΤΗΡΟ ΠΡΩΤΟΚΟΛΛΟ ΑΣΦΑΛΕΙΑΣ ---
        system_instruction = f"""
        ROLE: You are 'Mastro Nek', an Elite HVAC Technical Support Specialist.
        
        CONTEXT DATA (Library Files Found): {context_files}
        
        SAFETY PROTOCOL (CRITICAL RULES):
        1. **MATCH CHECK**: Check if the User's requested Model Name exists in the 'CONTEXT DATA' filenames provided above.
        2. **MISSING MANUAL WARNING**: 
           - If the specific manual for the requested model is NOT in the context data, you MUST start your response with: 
             "⚠️ **Προσοχή:** Δεν βρέθηκε το συγκεκριμένο εγχειρίδιο στη Βιβλιοθήκη. Η απάντηση βασίζεται σε γενική εμπειρία και ενδέχεται να διαφέρει ανά έκδοση."
           - In this case, do NOT state error codes as absolute facts. Use phrases like "Usually refers to..." or "In similar models...".
        3. **CORRECTIONS**: If the user corrects you technically (e.g., "It has no pressure switch"), accept it immediately ("You are correct, apologies") and adjust your diagnosis.
        4. **DEPTH**: Be technical, structured (Diagnosis -> Causes -> Steps), and professional.
        
        LANGUAGE: Answer ONLY in {target_lang}.
        """

        try:
            # Δημιουργία ιστορικού για το Gemini
            gemini_history = []
            
            # 1. System Prompt (Η Ταυτότητα & Οι Κανόνες)
            gemini_history.append({"role": "user", "parts": [system_instruction]})
            gemini_history.append({"role": "model", "parts": ["Understood. I am Mastro Nek. I will follow the Safety Protocol strictly."]})

            # 2. Προσθήκη ιστορικού συζήτησης
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})

            # 3. Λήψη απάντησης
            response = self.model.generate_content(gemini_history)
            return response.text
            
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        """Λειτουργία για τον AI Organizer (Βιβλιοθηκονόμος)."""
        if not self.model: return "Unsorted|Unknown|Unknown|Manual"

        sys_prompt = f"""
        ACT AS AN HVAC EXPERT LIBRARIAN.
        Analyze the text from this document.
        
        FILENAME: {filename}
        TEXT CONTENT SAMPLE:
        {text[:15000]}

        YOUR TASK: Classify this document into 4 levels.
        
        1. CATEGORY: [Boilers, AirConditioners, HeatPumps, Solar, WaterHeaters, Controllers, Underfloor, Tools, Other]
        2. BRAND: Manufacturer (e.g. Ariston, Daikin). If unknown, use "Unknown".
        3. MODEL: Specific model series (e.g. Clas One). If general, use "General".
        4. TYPE: Choose strictly one: [ServiceManual, UserManual, InstallationManual, WiringDiagram, SpareParts, Certificates, Brochure]

        OUTPUT FORMAT: CATEGORY|BRAND|MODEL|TYPE
        CRITICAL: If uncertain, output: MANUAL_REVIEW
        """
        
        try:
            response = self.model.generate_content(sys_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Organizer AI Error: {e}")
            return "Unsorted|Unknown|Unknown|Manual"