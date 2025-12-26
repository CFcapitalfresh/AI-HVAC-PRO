"""
CORE MODULE: AI ENGINE (BRAIN) - FINAL PLATINUM EDITION
-------------------------------------------------------
Features:
1. Mastro Nek Persona (Strict HVAC Expert for Chat).
2. Deep Librarian Logic (Category|Brand|Model|Type for Organizer).
3. Language Enforcement (Greek/English).
4. Robust Error Handling.
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
        """Αρχική ρύθμιση σύνδεσης με Google Gemini."""
        if not self.api_key:
            logger.critical("AI Setup Failed: No API Key.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            # Χρησιμοποιούμε το flash μοντέλο για ταχύτητα.
            # Αν θες πιο έξυπνο (αλλά πιο αργό), βάλε 'gemini-1.5-pro'
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            logger.critical(f"AI Setup Error: {e}")

    def analyze_content(self, prompt, context_text="", image=None, lang="gr"):
        """
        ΛΕΙΤΟΥΡΓΙΑ 1: CHAT
        Εκτελεί ερώτηση με αυστηρή προσωπικότητα HVAC (Mastro Nek).
        """
        if not self.model: return "⚠️ AI System Offline."

        # 1. Επιλογή Γλώσσας
        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        # 2. Η "Ταυτότητα" του Συστήματος (System Prompt)
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
        ΛΕΙΤΟΥΡΓΙΑ 2: ORGANIZER (LIBRARIAN)
        Αναλύει το κείμενο PDF για ταξινόμηση 4 επιπέδων.
        Επιστρέφει: CATEGORY | BRAND | MODEL | TYPE
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