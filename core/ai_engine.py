"""
CORE MODULE: AI ENGINE (BRAIN) - TITANIUM EDITION
-------------------------------------------------
Features:
1. CHAT MEMORY: Handles full conversation history.
2. SOURCE AWARENESS: Knows which manuals are available.
3. PERSONA REFINEMENT: Accepts technical corrections immediately.
4. AUTO-DISCOVERY: Finds best Google Model.
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
            best_model = self._find_best_model()
            self.model = genai.GenerativeModel(best_model)
        except Exception as e:
            logger.critical(f"AI Setup Error: {e}")

    def _find_best_model(self):
        """Auto-discovery of best available model."""
        try:
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            priorities = [
                "models/gemini-1.5-pro-latest", 
                "models/gemini-1.5-pro", 
                "models/gemini-1.5-flash",
                "models/gemini-pro"
            ]
            for p in priorities:
                if p in available: return p
            return available[0] if available else "models/gemini-pro"
        except: return "models/gemini-pro"

    def get_chat_response(self, chat_history, context_files="", lang="gr"):
        """
        Εκτελεί συνομιλία λαμβάνοντας υπόψη όλο το ιστορικό.
        Args:
            chat_history: Λίστα με μηνύματα [{'role': 'user', 'content': '...'}, ...]
            context_files: Λίστα με τα ονόματα των manual που βρέθηκαν.
        """
        if not self.model: return "⚠️ AI System Offline."

        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        # Η ΝΕΑ "ΤΑΠΕΙΝΗ" & ΕΞΥΠΝΗ ΠΡΟΣΩΠΙΚΟΤΗΤΑ
        system_instruction = f"""
        ROLE: You are 'Mastro Nek', an Elite HVAC Technical Support Specialist.
        
        STRICT RULES:
        1. LANGUAGE: Answer ONLY in {target_lang}.
        2. CONTEXT: The user has these manuals available: {context_files}. 
           - Suggest checking them if relevant.
        3. ADAPTABILITY: **CRITICAL**: If the user corrects you technically (e.g., "This model has no pressure switch"), ACCEPT IT IMMEDIATELY. 
           - Say: "You are correct, my apologies."
           - Then re-evaluate the diagnosis based on the user's correction. 
           - DO NOT argue or repeat generic advice that contradicts the user.
        4. TONE: Professional, technical, structured (Diagnosis -> Causes -> Steps).
        """

        try:
            # Μετατροπή του History σε format Gemini
            gemini_history = []
            
            # Πρώτα βάζουμε την προσωπικότητα ως "system" οδηγία (ή user prompt στην αρχή)
            gemini_history.append({"role": "user", "parts": [system_instruction]})
            gemini_history.append({"role": "model", "parts": ["Understood. I am Mastro Nek. I am ready."]})

            # Μετά προσθέτουμε τη συζήτηση
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})

            # Στέλνουμε το τελευταίο μήνυμα (που είναι ήδη στο history) μέσω start_chat; 
            # Όχι, το Gemini ChatSession θέλει το history ΧΩΡΙΣ το τελευταίο μήνυμα, και μετά send_message.
            
            # Λύση για robustness: Χρησιμοποιούμε generate_content με όλο το πακέτο
            response = self.model.generate_content(gemini_history)
            return response.text
            
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        """Organizer Logic (Παραμένει ίδια)."""
        if not self.model: return "Unsorted|Unknown|Unknown|Manual"
        sys_prompt = f"Analyze HVAC Manual: {filename}\n{text[:15000]}\nOutput: CATEGORY|BRAND|MODEL|TYPE"
        try:
            return self.model.generate_content(sys_prompt).text
        except: return "Unsorted|Unknown|Unknown|Manual"