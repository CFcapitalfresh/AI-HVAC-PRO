"""
SERVICE: DIAGNOSTICS LOGIC (ROBUST & DEBUG VERSION)
---------------------------------------------------
Description: Specialized AI service that generates step-by-step 
diagnostic checklists. Includes advanced JSON parsing and error reporting.
"""

import google.generativeai as genai
import json
import logging
import streamlit as st  # <--- Προσθήκη για να δείχνουμε τα σφάλματα στην οθόνη
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
                self.model = genai.GenerativeModel('models/gemini-1.5-flash')
            except Exception as e:
                st.error(f"⚠️ AI Configuration Error: {e}")
        else:
            st.error("❌ API Key Missing! Ελέγξτε το αρχείο secrets.toml.")

    def generate_checklist(self, error_code, manual_text=""):
        """Δημιουργεί λίστα ελέγχου (Checklist) σε μορφή JSON."""
        if not self.model: 
            st.error("❌ Το AI Model δεν έχει αρχικοποιηθεί (Model is None).")
            return None

        prompt = f"""
        ROLE: You are an Expert HVAC Field Technician.
        TASK: Create a strictly structured troubleshooting checklist for the following issue.
        
        ISSUE/ERROR CODE: {error_code}
        MANUAL CONTEXT: {manual_text[:5000]} (Use this if relevant)

        REQUIREMENTS:
        1. Break down the solution into logical, sequential STEPS.
        2. Each step must be a binary check (Yes/No) or an Action.
        3. OUTPUT FORMAT: Pure JSON only. No markdown.
        
        JSON STRUCTURE:
        {{
            "title": "Diagnosis for [Error Code]",
            "steps": [
                {{
                    "id": 1,
                    "action": "Check water pressure gauge.",
                    "question": "Is the pressure above 1.0 bar?",
                    "tip": "Locate the gauge usually at the bottom."
                }},
                {{
                    "id": 2,
                    "action": "Reset the device.",
                    "question": "Did the error clear after reset?",
                    "tip": "Press and hold 'R' for 5 seconds."
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
            
            # --- ΠΡΟΗΓΜΕΝΟΣ ΚΑΘΑΡΙΣΜΟΣ JSON ---
            # Βρίσκουμε την πρώτη αγκύλη '{' και την τελευταία '}'
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                clean_json = text[start_idx:end_idx]
                return json.loads(clean_json)
            else:
                # Αν αποτύχει, δείχνουμε τι έστειλε το AI για να καταλάβουμε
                st.warning(f"⚠️ Το AI επέστρεψε μη έγκυρη μορφή: {text[:100]}...")
                return None
            
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON Error: Δεν μπορώ να διαβάσω την απάντηση του AI. ({e})")
            return None
        except Exception as e:
            # Εμφάνιση του πραγματικού σφάλματος στην οθόνη
            st.error(f"❌ System Error: {str(e)}")
            logger.error(f"Diagnostics Error: {e}")
            return None