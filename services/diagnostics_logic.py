"""
SERVICE: DIAGNOSTICS LOGIC (LOCALIZED & ROBUST)
-----------------------------------------------
Description: Specialized AI service that generates step-by-step 
diagnostic checklists.
FEATURES:
- Smart Model Discovery (No 404 errors)
- Multi-language Support (Greek/English)
- Centralized system checks
"""

import google.generativeai as genai
import json
import logging
import streamlit as st
import pypdf # For PDF engine check
from io import BytesIO # For PDF engine check

from core.config_loader import ConfigLoader
from core.ai_engine import AIEngine # Rule 3: Use central AI Engine

logger = logging.getLogger("Service.Diagnostics")

class DiagnosticsService:
    def __init__(self):
        # Rule 3: Use the central AIEngine instance.
        # It handles its own setup and model discovery.
        self.ai_engine = AIEngine() 
        self.model = self.ai_engine.model # Get the already initialized model
        self.api_key = self.ai_engine.api_key

    def _get_best_model_name_internal(self) -> Optional[str]:
        """Internal method to get the selected model name from AIEngine."""
        if self.ai_engine and self.ai_engine.model:
            return self.ai_engine.model.model_name
        return None

    def check_gemini_key(self) -> Dict[str, Any]:
        """Checks if the Gemini API Key is available."""
        if self.api_key:
            mask = self.api_key[:5] + "..." + self.api_key[-4:]
            return {"status": "success", "message": mask}
        return {"status": "error", "message": "No API Key found."}

    def test_ai_connection(self) -> Dict[str, Any]:
        """Tests connection to Google AI and lists models."""
        if not self.api_key:
            return {"status": "error", "message": "API Key missing."}
        
        try:
            # Re-configure genai just to be sure, though AIEngine already does it.
            genai.configure(api_key=self.api_key) 
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            count = len(models)
            return {"status": "success", "message": f"{count} models found."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def test_ai_generation(self) -> Dict[str, Any]:
        """Tests a simple content generation from the active AI model."""
        if not self.model:
            return {"status": "error", "message": self.ai_engine.last_error or "AI Model not initialized."}
        
        try:
            response = self.model.generate_content("Write the word 'OK'.")
            if response.text:
                return {"status": "success", "message": response.text.strip()}
            return {"status": "warning", "message": "Empty response from AI."}
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg: return {"status": "error", "message": "Quota Exceeded (429)."}
            if "403" in error_msg or "API_KEY_INVALID" in error_msg: return {"status": "error", "message": "Invalid API Key."}
            if "404" in error_msg: return {"status": "error", "message": "Model not found."}
            return {"status": "error", "message": error_msg}

    def check_pdf_engine(self) -> Dict[str, Any]:
        """Checks if pypdf library can process PDFs."""
        try:
            # Test reading a tiny, empty PDF
            pypdf.PdfReader(BytesIO(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0>>endobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000055 00000 n\ntrailer<</Size 3/Root 1 0 R>>startxref\n104\n%%EOF"))
            return {"status": "success", "message": "pypdf can read PDFs."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

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
                logger.warning(f"Invalid JSON from AI in generate_checklist: {text}", exc_info=True)
                return None
            
        except Exception as e:
            st.error(f"❌ System Error ({type(e).__name__}): {str(e)}")
            logger.error(f"Diagnostics Error during checklist generation: {e}", exc_info=True)
            return None