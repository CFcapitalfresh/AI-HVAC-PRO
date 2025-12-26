"""
CORE MODULE: AI ENGINE (BRAIN)
------------------------------
Integration with Google Gemini Pro & Flash models.
Handles text, images, and PDF inputs.
"""

import google.generativeai as genai
import logging
from core.config_loader import ConfigLoader
import time

logger = logging.getLogger("Core.AI")

class AIEngine:
    """Κεντρική Μηχανή Τεχνητής Νοημοσύνης."""

    def __init__(self):
        self.api_key = ConfigLoader.get_gemini_key()
        self.model = None
        self._setup()

    def _setup(self):
        """Ρύθμιση του Gemini."""
        if not self.api_key:
            logger.critical("AI Setup Failed: No API Key.")
            return
        
        genai.configure(api_key=self.api_key)
        # Χρησιμοποιούμε το flash για ταχύτητα, ή το pro για ακρίβεια
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_content(self, prompt, context_text="", image=None):
        """
        Γενική μέθοδος ερώτησης στο AI.
        Args:
            prompt: Η ερώτηση/εντολή.
            context_text: Κείμενο από manual (αν υπάρχει).
            image: Εικόνα (PIL Image) αν υπάρχει.
        """
        if not self.model: return "⚠️ AI System Offline (Key Missing)."

        try:
            contents = []
            
            # Προσθήκη Context
            if context_text:
                contents.append(f"CONTEXT DATA:\n{context_text[:10000]}\n") # Όριο χαρακτήρων για ασφάλεια
            
            # Προσθήκη Εικόνας
            if image:
                contents.append(image)
                
            # Προσθήκη Ερώτησης
            contents.append(f"USER QUERY: {prompt}")

            # Κλήση στο API
            response = self.model.generate_content(contents)
            return response.text

        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
            return f"⚠️ Σφάλμα AI: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        """
        Ειδική μέθοδος για τον Organizer. 
        Επιστρέφει: CATEGORY | BRAND | MODEL
        """
        sys_prompt = f"""
        Analyze this HVAC manual header.
        Filename: {filename}
        Text Sample: {text[:1000]}

        Extract the following strictly separated by pipes (|):
        1. Category (Boilers, AirConditioners, HeatPumps, Solar, Controllers, Other)
        2. Brand (Manufacturer Name)
        3. Model Series (Main model code/name)

        Format: CATEGORY|BRAND|MODEL
        Example: Boilers|Ariston|Clas One
        If unknown, use "Unknown".
        """
        return self.analyze_content(sys_prompt)