"""
SERVICE: DIAGNOSTICS LOGIC
--------------------------
Description: Specialized AI service that generates step-by-step 
diagnostic checklists in structured JSON format.
"""

import google.generativeai as genai
import json
import logging
from core.config_loader import ConfigLoader

logger = logging.getLogger("Service.Diagnostics")

class DiagnosticsService:
    def __init__(self):
        self.api_key = ConfigLoader.get_gemini_key()
        self.model = None
        self._setup()

    def _setup(self):
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Χρησιμοποιούμε το flash για ταχύτητα
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')

    def generate_checklist(self, error_code, manual_text=""):
        """Δημιουργεί λίστα ελέγχου (Checklist) σε μορφή JSON."""
        if not self.model: return None

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
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            clean_json = response.text.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:-3]
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:-3]
                
            return json.loads(clean_json)
            
        except Exception as e:
            logger.error(f"Diagnostics JSON Error: {e}")
            return None