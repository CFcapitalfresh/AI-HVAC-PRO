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
            # Smart Auto-Discovery: Ρωτάμε ποια μοντέλα είναι διαθέσιμα
            available_models = []
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)
            except: pass

            preferred = ["models/gemini-1.5-pro", "models/gemini-1.5-flash", "models/gemini-pro"]
            selected = None
            for p in preferred:
                if p in available_models:
                    selected = p
                    break
            if not selected and available_models: selected = available_models[0]

            if selected:
                self.model = genai.GenerativeModel(selected)
                self.last_error = None
            else:
                self.last_error = "No valid model found."
        except Exception as e:
            self.last_error = str(e)

    def _extract_text_from_pdfs(self, pdf_files):
        text = ""
        if not pdf_files: return ""
        for pdf in pdf_files:
            try:
                reader = pypdf.PdfReader(pdf)
                limit = min(len(reader.pages), 15)
                text += f"\n--- USER UPLOADED FILE: {pdf.name} ---\n"
                for i in range(limit):
                    t = reader.pages[i].extract_text()
                    if t: text += t + "\n"
            except: pass
        return text

    def get_chat_response(self, chat_history, context_files="", lang="gr", images=None, audio=None, pdf_files=None):
        if not self.model: return f"⚠️ AI Offline ({self.last_error})"
        
        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        # --- ΕΝΤΟΛΕΣ: VERIFY RELEVANCE & CITE SOURCES ---
        system_instruction = f"""
        ROLE: You are 'Mastro Nek', an Elite HVAC Technical Support Specialist.
        
        CONTEXT DATA (Best Matching Manuals): {context_files}
        
        CRITICAL INSTRUCTION ON SOURCES:
        I have provided you with the CLOSEST MATCHING MANUALS found.
        1. **VERIFY RELEVANCE**: Check if the manual belongs to the same **Product Family** (e.g., if user asks for "Next Evo X" and you have "Next Evo", IT IS RELEVANT).
        2. **USE IT**: If it is relevant, answer using the manual and cite it: "📖 **Πηγή / Source:** [Filename]".
        3. **FALLBACK**: Only if the manual is COMPLETELY UNRELATED (e.g. Air Conditioner vs Boiler), ignore it and use General Knowledge, stating: "⚠️ **Πηγή / Source:** Γενική Γνώση / General Knowledge (Manual not found)".
        
        OUTPUT FORMAT:
        - Diagnosis (Cause)
        - Solution (Steps 1, 2, 3...)
        - Tools needed
        
        LANGUAGE: Answer ONLY in {target_lang}.
        """

        try:
            msg_parts = [system_instruction]
            if pdf_files:
                msg_parts.append(self._extract_text_from_pdfs(pdf_files))
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