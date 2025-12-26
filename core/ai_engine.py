"""
CORE MODULE: AI ENGINE (BRAIN) - SELF HEALING & PERSONA
-------------------------------------------------------
Features:
1. AUTO-DISCOVERY: Finds available models automatically (Fixes 404 errors).
2. Mastro Nek Persona: Strict HVAC Expert for Chat.
3. Deep Librarian Logic: For the AI Organizer.
4. Language Enforcement: Greek/English.
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
        """Αρχική ρύθμιση με Αυτόματη Επιλογή Μοντέλου."""
        if not self.api_key:
            logger.critical("AI Setup Failed: No API Key.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # --- AUTO DISCOVERY LOGIC ---
            best_model_name = self._find_best_model()
            logger.info(f"✅ AI selected model: {best_model_name}")
            
            self.model = genai.GenerativeModel(best_model_name)
            
        except Exception as e:
            logger.critical(f"AI Setup Error: {e}")

    def _find_best_model(self):
        """
        Ρωτάει την Google ποια μοντέλα είναι διαθέσιμα και διαλέγει το καλύτερο.
        """
        try:
            # 1. Λήψη λίστας διαθέσιμων μοντέλων
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            
            # 2. Λίστα Προτεραιότητας (Ψάχνουμε με αυτή τη σειρά)
            # Προτιμάμε το 1.5 Flash για ταχύτητα, μετά το Pro, μετά το απλό 1.0
            priorities = [
                "models/gemini-1.5-flash",
                "models/gemini-1.5-flash-latest",
                "models/gemini-1.5-flash-001",
                "models/gemini-1.5-pro",
                "models/gemini-1.5-pro-latest",
                "models/gemini-pro"
            ]

            # 3. Έλεγχος αν υπάρχει κάποιο από τα αγαπημένα μας
            for priority in priorities:
                if priority in available_models:
                    return priority
            
            # 4. Fallback: Αν δεν βρούμε κανένα γνωστό, παίρνουμε το πρώτο διαθέσιμο "gemini"
            for m in available_models:
                if "gemini" in m:
                    return m
            
            # 5. Απόλυτη λύση ανάγκης
            return "models/gemini-pro"
            
        except Exception as e:
            logger.error(f"Model Discovery Failed: {e}")
            return "models/gemini-pro" # Default safe choice

    def analyze_content(self, prompt, context_text="", image=None, lang="gr"):
        """
        ΛΕΙΤΟΥΡΓΙΑ 1: CHAT (Με Προσωπικότητα)
        """
        if not self.model: return "⚠️ AI System Offline (Model not loaded)."

        # Επιλογή Γλώσσας
        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        # System Prompt (Ταυτότητα)
        system_persona = f"""
        INSTRUCTIONS:
        You are 'Mastro Nek', an expert HVAC Technician Assistant.
        
        STRICT RULES:
        1. LANGUAGE: You MUST answer ONLY in {target_lang}.
        2. DOMAIN: You answer ONLY about Heating, Cooling, Boilers, Heat Pumps, and Hydraulic systems.
        3. CONTEXT: 
           - If user says "Clas One", they refer to "Ariston Clas One Boiler".
           - If user says "Error 104" (for Ariston), it means "Poor Circulation/Pump issue".
           - Ignore unrelated topics like VPNs, Semiconductor design, or Cisco.
        4. TONE: Professional, technical, concise. Use bullet points for solutions.
        
        USER CONTEXT DATA (Manuals found):
        {context_text[:20000]}
        """

        try:
            contents = [system_persona]
            if image: contents.append(image)
            contents.append(f"USER QUESTION: {prompt}")

            response = self.model.generate_content(contents)
            return response.text
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        """
        ΛΕΙΤΟΥΡΓΙΑ 2: ORGANIZER (Βιβλιοθηκονόμος)
        """
        if not self.model: return "Unsorted|Unknown|Unknown|Manual"

        sys_prompt = f"""
        ACT AS AN HVAC EXPERT LIBRARIAN.
        Analyze the text from this document.
        
        FILENAME: {filename}
        TEXT CONTENT SAMPLE:
        {text[:25000]}

        YOUR TASK: Classify this document into 4 levels.
        
        1. CATEGORY: [Boilers, AirConditioners, HeatPumps, Solar, WaterHeaters, Controllers, Underfloor, Tools, Other]
        2. BRAND: The manufacturer (e.g. Ariston, Daikin, Mitsubishi). If unknown, use "Unknown".
        3. MODEL: The specific model series (e.g. Clas One, Altherma 3, Alterra). If general, use "General".
        4. TYPE: What kind of document is this? Choose strictly one:
           - [ServiceManual] (Technical repair guide, error codes, dismantling)
           - [UserManual] (Instructions for the end user)
           - [InstallationManual] (For installers, dimensions, piping)
           - [WiringDiagram] (Electrical schematics only)
           - [SpareParts] (Exploded views, part codes)
           - [Certificates] (CE, Declaration of conformity)
           - [Brochure] (Marketing material)

        OUTPUT FORMAT: CATEGORY|BRAND|MODEL|TYPE
        EXAMPLE: Boilers|Ariston|Clas One|ServiceManual
        
        CRITICAL: If you cannot identify the Brand or Category with high confidence, output: MANUAL_REVIEW
        """
        
        try:
            response = self.model.generate_content(sys_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Organizer AI Error: {e}")
            return "Unsorted|Unknown|Unknown|Manual"