"""
CORE MODULE: AI ENGINE (BRAIN) - SENIOR TECHNICIAN EDITION
----------------------------------------------------------
Updates:
- System Persona upgraded to "Senior Field Engineer".
- Instructions for deep troubleshooting steps (not just summary).
- Mandate to use specific parameters and technical values from manuals.
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
        """Εύρεση διαθέσιμου μοντέλου (Auto-Discovery)."""
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            
            priorities = [
                "models/gemini-1.5-pro-latest", # Προτιμάμε το PRO για ανάλυση βάθους
                "models/gemini-1.5-pro",
                "models/gemini-1.5-flash",
                "models/gemini-1.5-flash-latest",
                "models/gemini-pro"
            ]

            for priority in priorities:
                if priority in available_models:
                    return priority
            
            for m in available_models:
                if "gemini" in m: return m
            
            return "models/gemini-pro"
            
        except Exception as e:
            logger.error(f"Model Discovery Failed: {e}")
            return "models/gemini-pro"

    def analyze_content(self, prompt, context_text="", image=None, lang="gr"):
        """
        ΛΕΙΤΟΥΡΓΙΑ 1: CHAT (SENIOR TECH PERSONA)
        """
        if not self.model: return "⚠️ AI System Offline."

        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        # Η ΝΕΑ, ΒΕΛΤΙΩΜΕΝΗ ΠΡΟΣΩΠΙΚΟΤΗΤΑ
        system_persona = f"""
        INSTRUCTIONS:
        You are 'Mastro Nek', an Elite HVAC Technical Support Specialist suitable for enterprise use.
        You are talking to a professional technician on the field, not a homeowner.

        STRICT RULES:
        1. LANGUAGE: Answer ONLY in {target_lang}.
        2. DEPTH: Do NOT be brief. Provide comprehensive, step-by-step technical analysis.
        3. SOURCES: Combine the provided Manuals (Context) with your general engineering knowledge.
           - If the manual mentions specific Parameters (e.g., P 2.4.1), Safety Menus, or PCB Voltages, YOU MUST CITE THEM.
        4. STRUCTURE:
           - **Technical Diagnosis**: What specifically triggered the sensor?
           - **Probable Causes**: List from most common to rare (e.g., Pump, PCB, Wiring, Air).
           - **Step-by-Step Troubleshooting**: Numbered actions (Measure X, Check Y, Clean Z).
           - **Parameters/Settings**: Mention relevant service menu settings.
        
        CONTEXT DATA (Library Content):
        {context_text[:25000]}
        """

        try:
            contents = [system_persona]
            if image: contents.append(image)
            contents.append(f"USER TECHNICAL QUERY: {prompt}")

            response = self.model.generate_content(contents)
            return response.text
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        """
        ΛΕΙΤΟΥΡΓΙΑ 2: ORGANIZER (LIBRARIAN)
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