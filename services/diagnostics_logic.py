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

logger = logging.getLogger("Service.Diagnostics")

class DiagnosticsService:
    def __init__(self):
        self.api_key = ConfigLoader.get_gemini_key()
        self.model = None
        self._setup()

    def _setup(self):
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                
                # --- SMART AUTO-DISCOVERY ---
                available_models = []
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            available_models.append(m.name)
                except: pass

                preferred_order = [
                    "models/gemini-1.5-flash", 
                    "models/gemini-1.5-flash-latest",
                    "models/gemini-1.5-pro",
                    "models/gemini-pro"
                ]
                
                selected_model = None
                for p in preferred_order:
                    if p in available_models:
                        selected_model = p
                        break
                
                if not selected_model and available_models:
                    selected_model = available_models[0]

                if selected_model:
                    self.model = genai.GenerativeModel(selected_model)
                else:
                    st.error("❌ Δεν βρέθηκε κανένα διαθέσιμο μοντέλο Gemini.")
                    
            except Exception as e:
                st.error(f"⚠️ AI Configuration Error: {e}")
        else:
            st.error("❌ API Key Missing! Ελέγξτε το αρχείο secrets.toml.")

    def generate_checklist(self, error_code, manual_text="", lang="gr"):
        """
        Δημιουργεί λίστα ελέγχου (Checklist) σε μορφή JSON.
        Args:
            error_code: Ο κωδικός σφάλματος.
            manual_text: Context από το manual (αν υπάρχει).
            lang: 'gr' για Ελληνικά, 'en' για Αγγλικά.
        """
        if not self.model: 
            st.error("❌ Το AI Model δεν έχει αρχικοποιηθεί.")
            return None

        # Επιλογή Γλώσσας Στόχου για το AI
        target_lang_str = "GREEK (Ελληνικά)" if lang == 'gr' else "ENGLISH"

        prompt = f"""
        ROLE: You are an Expert HVAC Field Technician.
        TASK: Create a strictly structured troubleshooting checklist for the following issue.
        
        ISSUE/ERROR CODE: {error_code}
        MANUAL CONTEXT: {manual_text[:5000]} (Use this if relevant)

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
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                clean_json = text[start_idx:end_idx]
                return json.loads(clean_json)
            else:
                st.warning(f"⚠️ Invalid JSON from AI: {text[:100]}...")
                return None
            
        except Exception as e:
            st.error(f"❌ System Error ({type(e).__name__}): {str(e)}")
            logger.error(f"Diagnostics Error: {e}")
            return None