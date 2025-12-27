"""
SERVICE: DIAGNOSTICS LOGIC (AUTO-DISCOVERY EDITION)
---------------------------------------------------
Description: Specialized AI service that generates step-by-step 
diagnostic checklists.
UPDATED: Now includes SMART MODEL DISCOVERY to avoid 404 errors.
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
                
                # --- SMART AUTO-DISCOVERY (Η Διόρθωση) ---
                # 1. Ρωτάμε το API τι μοντέλα είναι διαθέσιμα
                available_models = []
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            available_models.append(m.name)
                except: pass

                # 2. Λίστα προτίμησης (από το γρηγορότερο στο πιο έξυπνο)
                preferred_order = [
                    "models/gemini-1.5-flash", 
                    "models/gemini-1.5-flash-latest",
                    "models/gemini-1.5-pro",
                    "models/gemini-pro"
                ]
                
                selected_model = None
                
                # 3. Επιλογή του πρώτου διαθέσιμου
                for p in preferred_order:
                    if p in available_models:
                        selected_model = p
                        break
                
                # Fallback: Αν δεν βρήκε κανένα από τα preferred, πάρε το πρώτο διαθέσιμο
                if not selected_model and available_models:
                    selected_model = available_models[0]

                if selected_model:
                    # st.toast(f"Diagnostics using: {selected_model}") # Προαιρετικό debug
                    self.model = genai.GenerativeModel(selected_model)
                else:
                    st.error("❌ Δεν βρέθηκε κανένα διαθέσιμο μοντέλο Gemini.")
                    
            except Exception as e:
                st.error(f"⚠️ AI Configuration Error: {e}")
        else:
            st.error("❌ API Key Missing! Ελέγξτε το αρχείο secrets.toml.")

    def generate_checklist(self, error_code, manual_text=""):
        """Δημιουργεί λίστα ελέγχου (Checklist) σε μορφή JSON."""
        if not self.model: 
            st.error("❌ Το AI Model δεν έχει αρχικοποιηθεί.")
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
            
            # --- ROBUST JSON PARSING ---
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                clean_json = text[start_idx:end_idx]
                return json.loads(clean_json)
            else:
                st.warning(f"⚠️ Το AI επέστρεψε μη έγκυρη μορφή: {text[:100]}...")
                return None
            
        except Exception as e:
            # Ειδικός χειρισμός για το 404 (αν ξανασυμβεί)
            if "404" in str(e):
                st.error("❌ Σφάλμα 404: Το επιλεγμένο μοντέλο δεν βρέθηκε. Δοκίμασε να αλλάξεις API Key ή Region.")
            else:
                st.error(f"❌ System Error: {str(e)}")
            logger.error(f"Diagnostics Error: {e}")
            return None