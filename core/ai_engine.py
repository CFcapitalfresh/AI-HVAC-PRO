"""
CORE MODULE: AI ENGINE (BRAIN) - SELF HEALING EDITION
-----------------------------------------------------
Integration with Google Gemini.
Features:
- Automatic Model Discovery (No hardcoded 404 errors)
- Prioritized Selection (Pro > Flash > Standard)
- Robust Error Handling
"""

import google.generativeai as genai
import logging
from core.config_loader import ConfigLoader
import time

logger = logging.getLogger("Core.AI")

class AIEngine:
    """Κεντρική Μηχανή Τεχνητής Νοημοσύνης με Αυτόματη Επιλογή Μοντέλου."""

    def __init__(self):
        self.api_key = ConfigLoader.get_gemini_key()
        self.model = None
        self.model_name = "Unknown"
        self._setup()

    def _setup(self):
        """Ρύθμιση του Gemini με αυτόματη εύρεση του καλύτερου μοντέλου."""
        if not self.api_key:
            logger.critical("AI Setup Failed: No API Key.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # 1. AUTO-DISCOVERY: Ρωτάμε την Google τι έχει διαθέσιμο
            best_model = self._find_best_available_model()
            
            self.model_name = best_model
            self.model = genai.GenerativeModel(best_model)
            logger.info(f"✅ AI Initialized using model: {best_model}")
            
        except Exception as e:
            logger.critical(f"AI Critical Setup Error: {e}")

    def _find_best_available_model(self):
        """
        Σαρώνει τα διαθέσιμα μοντέλα και επιλέγει το καλύτερο βάσει ιεραρχίας.
        """
        try:
            # Λίστα προτίμησης (Από το καλύτερο/γρηγορότερο στο παλιότερο)
            # Το σύστημα θα προσπαθήσει να βρει το πρώτο που υπάρχει στη λίστα της Google
            preferences = [
                "models/gemini-1.5-flash", # Γρήγορο & Φθηνό (Ιδανικό για Chat)
                "models/gemini-1.5-pro",   # Πιο έξυπνο (Ιδανικό για ανάλυση)
                "models/gemini-pro",       # Παλιό κλασικό
                "models/gemini-1.0-pro"    # Legacy
            ]
            
            # Ζητάμε από την Google τη λίστα των μοντέλων
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            
            # Έλεγχος: Υπάρχει κάποιο από τα αγαπημένα μας;
            for pref in preferences:
                if pref in available_models:
                    return pref
            
            # Fallback: Αν δεν βρούμε κανένα από τα γνωστά, παίρνουμε το πρώτο διαθέσιμο
            if available_models:
                logger.warning(f"Preferred models not found. Using fallback: {available_models[0]}")
                return available_models[0]
            
            return "models/gemini-1.5-flash" # Hard fallback αν αποτύχουν όλα

        except Exception as e:
            logger.error(f"Model Discovery Failed: {e}")
            return "models/gemini-1.5-flash" # Default σε περίπτωση ανάγκης

    def analyze_content(self, prompt, context_text="", image=None):
        """
        Γενική μέθοδος ερώτησης στο AI.
        """
        if not self.model: return "⚠️ AI System Offline (Initialization Failed)."

        try:
            contents = []
            
            # Προσθήκη Context
            if context_text:
                contents.append(f"CONTEXT DATA (Technical Manuals):\n{context_text[:15000]}\n") 
            
            # Προσθήκη Εικόνας
            if image:
                contents.append(image)
                
            # Προσθήκη Ερώτησης
            contents.append(f"USER QUERY: {prompt}")

            # Κλήση στο API
            response = self.model.generate_content(contents)
            return response.text

        except Exception as e:
            error_msg = str(e)
            logger.error(f"AI Generation Error: {e}")
            
            if "404" in error_msg:
                return f"⚠️ Σφάλμα Μοντέλου: Το μοντέλο {self.model_name} δεν βρέθηκε. Κάντε επανεκκίνηση για νέα σάρωση."
            elif "429" in error_msg:
                return "⚠️ Το σύστημα είναι φορτωμένο (Quota Exceeded). Δοκιμάστε ξανά σε λίγο."
            
            return f"⚠️ Σφάλμα AI: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        """Ειδική μέθοδος για τον Organizer."""
        sys_prompt = f"""
        Analyze this HVAC manual header.
        Filename: {filename}
        Text Sample: {text[:1000]}

        Extract:
        1. Category (Boilers, AirConditioners, HeatPumps, Solar, Controllers, Other)
        2. Brand (Manufacturer Name)
        3. Model Series

        Format: CATEGORY|BRAND|MODEL
        Use "Unknown" if unsure.
        """
        return self.analyze_content(sys_prompt)