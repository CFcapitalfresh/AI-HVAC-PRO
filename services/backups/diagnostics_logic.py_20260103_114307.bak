"""
SERVICE: DIAGNOSTICS LOGIC (LOCALIZED & ROBUST)
-----------------------------------------------
Description: Specialized AI service that generates step-by-step 
diagnostic checklists.
FEATURES:
- Smart Model Discovery (No 404 errors)
- Multi-language Support (Greek/English)
"""

import google.generativeai as genai
import json
import logging
import streamlit as st
from core.config_loader import ConfigLoader
from core.ai_engine import AIEngine # Import AIEngine to leverage its setup

logger = logging.getLogger("Service.Diagnostics")

class DiagnosticsService:
    def __init__(self):
        # Leverage AIEngine for API key and model setup (Rule 3)
        self.ai_engine = AIEngine()
        self.api_key = self.ai_engine.api_key
        self.model = self.ai_engine.model
        # The AIEngine already logs setup errors, so no need to duplicate here

    def generate_checklist(self, error_code: str, manual_text: str = "", lang: str = "gr") -> Optional[Dict[str, Any]]:
        """
        Δημιουργεί λίστα ελέγχου (Checklist) σε μορφή JSON.
        Args:
            error_code: Ο κωδικός σφάλματος.
            manual_text: Context από το manual (αν υπάρχει).
            lang: 'gr' για Ελληνικά, 'en' για Αγγλικά.
        Returns:
            Optional[Dict[str, Any]]: The generated checklist as a dictionary, or None if failed.
        """
        if not self.model: 
            error_message = f"❌ Το AI Model δεν έχει αρχικοποιηθεί: {self.ai_engine.last_error or 'Unknown error'}"
            st.error(error_message)
            logger.error(error_message) # Rule 4
            return None

        # Επιλογή Γλώσσας Στόχου για το AI
        target_lang_str = "GREEK (Ελληνικά)" if lang == 'gr' else "ENGLISH"

        prompt = f"""
        ROLE: You are an Expert HVAC Field Technician.
        TASK: Create a strictly structured troubleshooting checklist for the following issue.
        
        ISSUE/ERROR CODE: {error_code}
        MANUAL CONTEXT: {manual_text[:5000]} (Use this if relevant and available)

        CRITICAL LANGUAGE INSTRUCTION:
        The user speaks {target_lang_str}. 
        You MUST output all text values (title, action, question, tip) in {target_lang_str}.
        Translate technical terms where appropriate for a technician, but keep error codes intact.

        REQUIREMENTS:
        1. Break down the solution into logical, sequential STEPS.
        2. Each step must be a binary check (Yes/No) or an Action.
        3. OUTPUT FORMAT: Pure JSON only. No markdown.
        
        JSON STRUCTURE:
        {{
            "title": "Diagnosis Title (in {target_lang_str})",
            "steps": [
                {{
                    "id": 1,
                    "action": "Description of action (in {target_lang_str})",
                    "question": "Question for the user (in {target_lang_str})",
                    "tip": "Helpful tip (in {target_lang_str})"
                }}
            ]
        }}
        """
        
        try:
            # Ζητάμε JSON response
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            text = response.text.strip()
            
            # --- ROBUST JSON PARSING ---
            # Search for the first '{' and last '}' to handle potential preamble/postamble text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                clean_json = text[start_idx:end_idx]
                return json.loads(clean_json)
            else:
                logger.warning(f"⚠️ Invalid JSON from AI in Diagnostics: {text[:200]}...") # Rule 4
                st.warning(f"⚠️ {st.session_state.get('lang', 'gr')}: {text[:100]}...")
                return None
            
        except Exception as e:
            error_msg = f"❌ System Error ({type(e).__name__}): {str(e)}"
            st.error(error_msg)
            logger.error(f"Diagnostics Error during checklist generation: {e}", exc_info=True) # Rule 4
            return None