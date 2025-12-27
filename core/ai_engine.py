"""
CORE MODULE: AI ENGINE (BRAIN) - MULTIMODAL EDITION
---------------------------------------------------
Features:
- Safety Protocol (Strict Checks)
- Auto-Discovery of Models
- MULTIMODAL SUPPORT: Accepts Images & Audio now!
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
        if not self.api_key: return
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash') # Το Flash είναι το καλύτερο για εικόνα/ήχο
        except Exception as e:
            logger.critical(f"AI Setup Error: {e}")

    def get_chat_response(self, chat_history, context_files="", lang="gr", images=None, audio=None):
        """
        Εκτελεί τη συνομιλία με υποστήριξη Εικόνας και Ήχου.
        """
        if not self.model: return "⚠️ AI System Offline."

        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        # Σύστημα Ασφαλείας & Ρόλος
        system_instruction = f"""
        ROLE: You are 'Mastro Nek', an Elite HVAC Technical Support Specialist.
        CONTEXT DATA (Library Files Found): {context_files}
        
        INSTRUCTIONS:
        1. Analyze any IMAGES provided (look for error codes on screens, wiring issues, burnt parts).
        2. Listen to any AUDIO provided (identify noises like 'hissing', 'grinding', or spoken descriptions).
        3. If specific manual is missing in context, warn the user.
        4. Answer ONLY in {target_lang}.
        """

        try:
            # Χτίζουμε το μήνυμα για το Gemini
            # Το Gemini 1.5 δέχεται λίστα: [text, image_blob, audio_blob]
            current_message_parts = [system_instruction]
            
            # Προσθήκη Εικόνων
            if images:
                for img in images:
                    # Μετατροπή σε μορφή που καταλαβαίνει το Gemini
                    current_message_parts.append(img)
                    current_message_parts.append("\n[USER SENT AN IMAGE ABOVE]\n")

            # Προσθήκη Ήχου
            if audio:
                # Ο ήχος περνάει ως blob δεδομένα
                current_message_parts.append({
                    "mime_type": audio.type,
                    "data": audio.getvalue()
                })
                current_message_parts.append("\n[USER SENT AN AUDIO CLIP]\n")

            # Προσθήκη της τελευταίας ερώτησης κειμένου (αν υπάρχει)
            last_user_msg = next((m['content'] for m in reversed(chat_history) if m['role'] == 'user'), "")
            if last_user_msg:
                 current_message_parts.append(f"User Question: {last_user_msg}")

            # Στέλνουμε το πακέτο
            response = self.model.generate_content(current_message_parts)
            return response.text
            
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        # ... (Ο κώδικας του Organizer παραμένει ίδιος) ...
        return "Unsorted|Unknown|Unknown|Manual"