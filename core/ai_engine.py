"""
CORE MODULE: AI ENGINE (BRAIN) - DIAGNOSTIC EDITION
---------------------------------------------------
Features:
- Smart Model Discovery
- DETAILED ERROR REPORTING (No more generic "Offline")
- PDF/Image/Audio Support
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
        self.last_error = None # Αποθήκευση του τελευταίου σφάλματος
        self._setup()

    def _setup(self):
        """Εκκίνηση με έλεγχο διαθέσιμων μοντέλων (Ping Test)."""
        if not self.api_key:
            self.last_error = "MISSING API KEY (Check .streamlit/secrets.toml)"
            logger.critical(self.last_error)
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # Λίστα προτεραιότητας
            candidates = [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            
            active_model = None
            for m in candidates:
                try:
                    test_model = genai.GenerativeModel(m)
                    # Test generation
                    test_model.generate_content("Hi")
                    active_model = m
                    logger.info(f"✅ AI Connected: {m}")
                    break
                except Exception as e:
                    self.last_error = f"Model {m} failed: {str(e)}"
                    continue
            
            if active_model:
                self.model = genai.GenerativeModel(active_model)
                self.last_error = None # Όλα καλά
            else:
                # Αν αποτύχουν όλα, κρατάμε το τελευταίο σφάλμα
                if not self.last_error: self.last_error = "All models failed connection check."
                logger.critical(f"❌ AI Connection Failed. Last error: {self.last_error}")
                
        except Exception as e:
            self.last_error = f"Configuration Error: {str(e)}"
            logger.critical(self.last_error)

    def _extract_text_from_pdfs(self, pdf_files):
        """Ανάγνωση PDF."""
        text_content = ""
        if not pdf_files: return ""
        
        for pdf in pdf_files:
            try:
                reader = pypdf.PdfReader(pdf)
                limit = min(len(reader.pages), 15) 
                text_content += f"\n--- ΑΡΧΕΙΟ: {pdf.name} ---\n"
                for i in range(limit):
                    page_text = reader.pages[i].extract_text()
                    if page_text: text_content += page_text + "\n"
            except Exception as e:
                logger.error(f"PDF Read Error ({pdf.name}): {e}")
        return text_content

    def get_chat_response(self, chat_history, context_files="", lang="gr", images=None, audio=None, pdf_files=None):
        """Κύρια συνάρτηση απάντησης."""
        
        # ΑΝ ΥΠΑΡΧΕΙ ΣΦΑΛΜΑ, ΤΟ ΕΜΦΑΝΙΖΟΥΜΕ ΣΤΟΝ ΧΡΗΣΤΗ
        if not self.model: 
            return f"⚠️ **AI System Offline**\n\n🔍 **Διάγνωση Σφάλματος:** `{self.last_error}`\n\nΠαρακαλώ ελέγξτε το API Key ή τη σύνδεση."

        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        system_instruction = f"""
        ROLE: You are 'Mastro Nek', an Elite HVAC Technical Support Specialist.
        CONTEXT INFO: The user may have uploaded manuals or asked about specific files: {context_files}.
        
        INSTRUCTIONS:
        1. **ANALYZE UPLOADS**: If PDF content is provided below, USE IT to answer specifically.
        2. **STRUCTURE**: Use Bullet Points, Steps (1, 2, 3), and Bold Text.
        3. **DIAGNOSIS**: If an error code is given, explain the Cause and the Solution.
        4. **TONE**: Professional, Technical, Helpful.
        
        LANGUAGE: Answer ONLY in {target_lang}.
        """

        try:
            msg_parts = [system_instruction]
            
            # 1. PDF Content
            if pdf_files:
                pdf_text = self._extract_text_from_pdfs(pdf_files)
                if pdf_text:
                    msg_parts.append(f"\n[USER UPLOADED MANUAL CONTENT]:\n{pdf_text}\n")

            # 2. Images
            if images:
                for img in images:
                    msg_parts.append(img)
                    msg_parts.append("\n[Analyze this image]\n")

            # 3. Audio
            if audio:
                audio_bytes = audio.getvalue()
                msg_parts.append({"mime_type": "audio/wav", "data": audio_bytes})
                msg_parts.append("\n[Listen to this audio]\n")

            # 4. Text
            last_msg = next((m['content'] for m in reversed(chat_history) if m['role'] == 'user'), "")
            if last_msg: msg_parts.append(f"Question: {last_msg}")

            gen_config = genai.types.GenerationConfig(temperature=0.3, max_output_tokens=1000)
            response = self.model.generate_content(msg_parts, generation_config=gen_config)
            return response.text
            
        except Exception as e:
            return f"⚠️ AI Runtime Error: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        try:
            return self.model.generate_content(f"Classify CATEGORY|BRAND|MODEL|TYPE for: {filename}\n{text[:500]}").text
        except: return "Unsorted|Unknown|Unknown|Manual"