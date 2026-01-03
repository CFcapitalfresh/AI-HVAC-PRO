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
from typing import Dict, Any, Optional # For type hinting

from core.config_loader import ConfigLoader
from core.ai_engine import AIEngine # Rule 3: Use central AI Engine
from core.language_pack import get_text # Rule 5

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
        
        try: # Rule 4: Error Handling
            # Re-configure genai just to be sure, though AIEngine already does it.
            genai.configure(api_key=self.api_key) 
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            count = len(models)
            return {"status": "success", "message": f"{count} models found."}
        except Exception as e:
            logger.error(f"Google AI connection test failed: {e}", exc_info=True) # Rule 4
            return {"status": "error", "message": str(e)}

    def test_ai_generation(self) -> Dict[str, Any]:
        """Tests a simple content generation from the active AI model."""
        if not self.model:
            return {"status": "error", "message": self.ai_engine.last_error or "AI Model not initialized."}
        
        try: # Rule 4: Error Handling
            response = self.model.generate_content("Write the word 'OK'.")
            if response.text:
                return {"status": "success", "message": response.text.strip()}
            return {"status": "warning", "message": "Empty response from AI."}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"AI generation test failed: {e}", exc_info=True) # Rule 4
            if "429" in error_msg: return {"status": "error", "message": "Quota Exceeded (429)."}
            if "403" in error_msg or "API_KEY_INVALID" in error_msg: return {"status": "error", "message": "Invalid API Key."}
            if "404" in error_msg: return {"status": "error", "message": "Model not found."}
            return {"status": "error", "message": error_msg}

    def check_pdf_engine(self) -> Dict[str, Any]:
        """Checks if pypdf library can process PDFs."""
        try: # Rule 4: Error Handling
            # Test reading a tiny, empty PDF
            pypdf.PdfReader(BytesIO(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0>>endobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000055 00000 n\ntrailer<</Size 3/Root 1 0 R>>startxref\n104\n%%EOF"))
            return {"status": "success", "message": "pypdf can read PDFs."}
        except Exception as e:
            logger.error(f"PDF engine check failed: {e}", exc_info=True) # Rule 4
            return {"status": "error", "message": str(e)}

    def generate_checklist(self, error_code: str, manual_text: str = "", lang: str = "gr") -> Optional[Dict[str, Any]]:
        """
        Δημιουργεί λίστα ελέγχου (Checklist) σε μορφή JSON.
        Args:
            error_code: Ο κωδικός σφάλματος.
            manual_text: Context από το manual (αν υπάρχει).
            lang: 'gr' για Ελληνικά, 'en' για Αγγλικά.
        Returns:
            Optional[Dict[str, Any]]: Η λίστα ελέγχου σε μορφή JSON ή None σε περίπτωση σφάλματος.
        """
        if not self.model: 
            logger.error("AI Model not initialized for checklist generation.") # Rule 4
            return None

        # Επιλογή Γλώσσας Στόχου για το AI (Rule 5)
        target_lang_str = "GREEK (Ελληνικά)" if lang == 'gr' else "ENGLISH"

        prompt = f"""
        ROLE: You are an Expert HVAC Field Technician.
        TASK: Create a strictly structured troubleshooting checklist for the following issue.
        
        ISSUE/ERROR CODE: {error_code}
        MANUAL CONTEXT: {manual_text[:5000]} (Use this if relevant, prioritize it over general knowledge)

        CRITICAL LANGUAGE INSTRUCTION:
        The user speaks {target_lang_str}. 
        You MUST output all text values (title, action, question, tip) in {target_lang_str}.
        Translate technical terms where appropriate for a technician, but keep error codes intact.

        REQUIREMENTS:
        1. Break down the solution into logical, numbered steps.
        2. Each step MUST have:
           - "step_number": integer
           - "title": a concise title for the step.
           - "action": a clear instruction on what to do.
           - "question": a clear question to the user about the result of the action (e.g., "Did it fix the problem?", "Is the pressure X?").
           - "tip": (Optional) a helpful hint or warning.
        3. The checklist MUST be an array of step objects.
        4. If the manual context provides a specific solution, use it directly. Otherwise, provide general expert advice.
        5. The final JSON MUST be wrapped in a single root element "checklist".

        Output MUST be in JSON format:
        {{
          "checklist": [
            {{
              "step_number": 1,
              "title": "Initial Check",
              "action": "Inspect the power supply and connections.",
              "question": "Is the unit receiving power?",
              "tip": "Ensure the breaker is not tripped."
            }},
            {{
              "step_number": 2,
              "title": "Error Code Verification",
              "action": "Consult the provided manual for error code {error_code}.",
              "question": "Does the manual provide a specific solution for {error_code}?",
              "tip": "Look for the troubleshooting section."
            }}
            // ... more steps ...
          ]
        }}
        """

        try: # Rule 4: Error Handling
            response = self.model.generate_content(
                [{"text": prompt}],
                safety_settings=[ # Relax safety settings for technical content
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            # Attempt to parse the response as JSON
            checklist_data = json.loads(response.text)
            if "checklist" in checklist_data and isinstance(checklist_data["checklist"], list):
                logger.info("Successfully generated AI diagnostic checklist.") # Rule 4
                return checklist_data
            else:
                logger.warning(f"AI response did not contain a valid 'checklist' array. Raw response: {response.text}") # Rule 4
                return None
        except json.JSONDecodeError as e: # Rule 4: Specific JSON error
            logger.error(f"Failed to parse AI response as JSON: {e}. Raw response: {response.text}", exc_info=True) # Rule 4
            return None
        except Exception as e: # Rule 4: General error
            logger.error(f"Error during AI checklist generation: {e}", exc_info=True) # Rule 4
            return None