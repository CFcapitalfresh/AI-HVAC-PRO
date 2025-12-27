"""
CORE MODULE: AI ENGINE (BRAIN) - AUTO MODEL DISCOVERY
-----------------------------------------------------
Features:
- Auto-Detects Best Available Gemini Model (Fixes 404 Errors)
- Supports Images & Audio (Multimodal)
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
            
            # --- SMART MODEL DISCOVERY ---
            # Ψάχνουμε ποιο μοντέλο είναι διαθέσιμο για να αποφύγουμε το 404
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Λίστα προτίμησης (από το πιο γρήγορο/κατάλληλο προς τα παλιά)
            preferred = [
                "models/gemini-1.5-flash",
                "models/gemini-1.5-pro",
                "models/gemini-2.0-flash-exp",
                "models/gemini-pro"
            ]
            
            selected_model = "models/gemini-1.5-flash" # Default fallback
            
            # 1. Έλεγχος αν υπάρχει κάποιο από τα αγαπημένα μας
            for p in preferred:
                if p in available_models:
                    selected_model = p
                    break
            
            logger.info(f"AI Engine selected model: {selected_model}")
            self.model = genai.GenerativeModel(selected_model)
            
        except Exception as e:
            logger.critical(f"AI Setup Error: {e}")

    def get_chat_response(self, chat_history, context_files="", lang="gr", images=None, audio=None):
        """
        Εκτελεί τη συνομιλία με υποστήριξη Εικόνας και Ήχου.
        """
        if not self.model: return "⚠️ AI System Offline (Check API Key)."

        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        system_instruction = f"""
        ROLE: You are 'Mastro Nek', an Elite HVAC Technical Support Specialist.
        CONTEXT DATA: {context_files}
        
        INSTRUCTIONS:
        1. Analyze IMAGES (error codes, wiring).
        2. Listen to AUDIO (noises, descriptions).
        3. Answer ONLY in {target_lang}.
        """

        try:
            current_message_parts = [system_instruction]
            
            # Εικόνες
            if images:
                for img in images:
                    current_message_parts.append(img)
                    current_message_parts.append("\n[USER IMAGE]\n")

            # Ήχος (Live Recording ή Upload)
            if audio:
                # To st.audio_input επιστρέφει buffer, οπότε παίρνουμε τα bytes
                audio_bytes = audio.getvalue()
                current_message_parts.append({
                    "mime_type": "audio/wav", # Το Streamlit recorder γράφει σε wav
                    "data": audio_bytes
                })
                current_message_parts.append("\n[USER AUDIO MESSAGE]\n")

            # Κείμενο
            last_user_msg = next((m['content'] for m in reversed(chat_history) if m['role'] == 'user'), "")
            if last_user_msg:
                 current_message_parts.append(f"User Question: {last_user_msg}")

            response = self.model.generate_content(current_message_parts)
            return response.text
            
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        # Απλή υλοποίηση για τον Organizer
        return "Unsorted|Unknown|Unknown|Manual"