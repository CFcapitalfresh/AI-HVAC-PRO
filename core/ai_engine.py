"""
CORE MODULE: AI ENGINE (BRAIN) - REAL AUTO-DISCOVERY
----------------------------------------------------
Features:
- Queries Google API for available models.
- Forces Citation of Sources.
"""

import google.generativeai as genai
import logging
import pypdf
from core.config_loader import ConfigLoader

logger = logging.getLogger("Core.AI")

class AIEngine:
    def __init__(self):
        self.api_key = ConfigLoader.get_gemini_key()
        self.model = None
        self.last_error = None
        self._setup()

    def _setup(self):
        if not self.api_key:
            self.last_error = "MISSING API KEY"
            return
        
        try:
            genai.configure(api_key=self.api_key)
            available_models = []
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)
            except: pass

            preferred_order = [
                "models/gemini-1.5-pro-latest", "models/gemini-1.5-pro",
                "models/gemini-1.5-flash-latest", "models/gemini-1.5-flash",
                "models/gemini-pro"
            ]
            
            selected_model_name = None
            for p in preferred_order:
                if p in available_models:
                    selected_model_name = p
                    break
            
            if not selected_model_name and available_models:
                selected_model_name = available_models[0]

            if selected_model_name:
                self.model = genai.GenerativeModel(selected_model_name)
                self.last_error = None
            else:
                self.last_error = "No valid model found."
                
        except Exception as e:
            self.last_error = str(e)

    def _extract_text_from_pdfs(self, pdf_files):
        text_content = ""
        if not pdf_files: return ""
        for pdf in pdf_files:
            try:
                reader = pypdf.PdfReader(pdf)
                limit = min(len(reader.pages), 15) 
                text_content += f"\n--- USER UPLOADED FILE: {pdf.name} ---\n"
                for i in range(limit):
                    t = reader.pages[i].extract_text()
                    if t: text_content += t + "\n"
            except: pass
        return text_content

    def get_chat_response(self, chat_history, context_files="", lang="gr", images=None, audio=None, pdf_files=None):
        if not self.model: 
            return f"⚠️ **AI System Offline** ({self.last_error})"

        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        # --- ΑΥΣΤΗΡΟ ΠΡΩΤΟΚΟΛΛΟ ΠΗΓΩΝ ---
        system_instruction = f"""
        ROLE: You are 'Mastro Nek', an Elite HVAC Technical Support Specialist.
        
        CONTEXT DATA (Library Manuals Found): {context_files}
        
        INSTRUCTIONS:
        1. **CITATION IS MANDATORY**: 
           - If the answer is based on a specific manual from 'CONTEXT DATA' or a 'USER UPLOADED FILE', start with: "📖 **Source:** [Exact Filename]"
           - If the manual is NOT in the data, start with: "⚠️ **Source:** General Knowledge (Manual not found)"
        
        2. **DIAGNOSIS**: If an error code is given, explain Cause & Solution steps clearly.
        3. **FORMAT**: Use bold keys, bullet points, and numbered lists.
        
        LANGUAGE: Answer ONLY in {target_lang}.
        """

        try:
            msg_parts = [system_instruction]
            
            if pdf_files:
                pdf_text = self._extract_text_from_pdfs(pdf_files)
                msg_parts.append(pdf_text)

            if images:
                for img in images:
                    msg_parts.append(img)
                    msg_parts.append("Analyze this image.")

            if audio:
                msg_parts.append({"mime_type": "audio/wav", "data": audio.getvalue()})

            last_msg = next((m['content'] for m in reversed(chat_history) if m['role'] == 'user'), "")
            if last_msg: msg_parts.append(f"Question: {last_msg}")

            response = self.model.generate_content(msg_parts)
            return response.text
            
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        try: return self.model.generate_content(f"Classify CATEGORY|BRAND|MODEL|TYPE for: {filename}\n{text[:500]}").text
        except: return "Unsorted|Unknown|Unknown|Manual"