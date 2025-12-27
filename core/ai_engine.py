"""
CORE MODULE: AI ENGINE (BRAIN) - FULL CAPACITY
----------------------------------------------
Features:
- Smart Model Discovery (No 404 Errors)
- Multi-Modal: Images, Audio AND PDF Reading (Restored)
- Enhanced Technician Persona
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
        self._setup()

    def _setup(self):
        """Εκκίνηση με έλεγχο διαθέσιμων μοντέλων (Ping Test)."""
        if not self.api_key:
            logger.critical("AI Setup Failed: No API Key.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # Λίστα προτεραιότητας μοντέλων
            candidates = [
                "gemini-1.5-flash",
                "models/gemini-1.5-flash",
                "gemini-1.5-pro",
                "models/gemini-1.5-pro",
                "gemini-pro"
            ]
            
            active_model = None
            for m in candidates:
                try:
                    test_model = genai.GenerativeModel(m)
                    test_model.generate_content("Hi") # Test
                    active_model = m
                    logger.info(f"✅ AI Connected: {m}")
                    break
                except: continue
            
            if active_model:
                self.model = genai.GenerativeModel(active_model)
            else:
                logger.critical("❌ AI Connection Failed.")
                
        except Exception as e:
            logger.critical(f"AI Critical Error: {e}")

    def _extract_text_from_pdfs(self, pdf_files):
        """Επαναφορά της λογικής ανάγνωσης PDF από το παλιό brain.py"""
        text_content = ""
        if not pdf_files: return ""
        
        for pdf in pdf_files:
            try:
                reader = pypdf.PdfReader(pdf)
                # Διαβάζουμε τις πρώτες 10 σελίδες για ταχύτητα & όριο tokens
                limit = min(len(reader.pages), 15) 
                text_content += f"\n--- ΑΡΧΕΙΟ: {pdf.name} ---\n"
                for i in range(limit):
                    page_text = reader.pages[i].extract_text()
                    if page_text: text_content += page_text + "\n"
            except Exception as e:
                logger.error(f"PDF Read Error ({pdf.name}): {e}")
        return text_content

    def get_chat_response(self, chat_history, context_files="", lang="gr", images=None, audio=None, pdf_files=None):
        """Κύρια συνάρτηση απάντησης με ΟΛΑ τα δεδομένα."""
        if not self.model: return "⚠️ AI System Offline."

        target_lang = "GREEK" if lang == 'gr' else "ENGLISH"
        
        # --- ΠΡΟΣΩΠΙΚΟΤΗΤΑ & ΟΔΗΓΙΕΣ ---
        system_instruction = f"""
        ROLE: You are 'Mastro Nek', an Elite HVAC Technical Support Specialist.
        CONTEXT INFO: The user may have uploaded manuals or asked about specific files: {context_files}.
        
        INSTRUCTIONS:
        1. **ANALYZE UPLOADS**: If PDF content is provided below, USE IT to answer specifically.
        2. **STRUCTURE**: Use Bullet Points, Steps (1, 2, 3), and Bold Text. No huge walls of text.
        3. **DIAGNOSIS**: If an error code is given, explain the Cause and the Solution.
        4. **MISSING INFO**: If you don't have the manual, warn the user.
        5. **TONE**: Professional, Technical, Helpful.
        
        LANGUAGE: Answer ONLY in {target_lang}.
        """

        try:
            msg_parts = [system_instruction]
            
            # 1. Προσθήκη Κειμένου από PDF (Η μεγάλη επιστροφή!)
            if pdf_files:
                pdf_text = self._extract_text_from_pdfs(pdf_files)
                if pdf_text:
                    msg_parts.append(f"\n[USER UPLOADED MANUAL CONTENT]:\n{pdf_text}\n")

            # 2. Εικόνες
            if images:
                for img in images:
                    msg_parts.append(img)
                    msg_parts.append("\n[Analyze this image]\n")

            # 3. Ήχος
            if audio:
                audio_bytes = audio.getvalue()
                msg_parts.append({"mime_type": "audio/wav", "data": audio_bytes})
                msg_parts.append("\n[Listen to this audio]\n")

            # 4. Ερώτηση Χρήστη
            last_msg = next((m['content'] for m in reversed(chat_history) if m['role'] == 'user'), "")
            if last_msg: msg_parts.append(f"Question: {last_msg}")

            # Ρυθμίσεις generation
            gen_config = genai.types.GenerationConfig(temperature=0.3, max_output_tokens=1500)

            response = self.model.generate_content(msg_parts, generation_config=gen_config)
            return response.text
            
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    def extract_metadata_from_text(self, text, filename):
        # Fallback για τον Organizer
        try:
            return self.model.generate_content(f"Classify CATEGORY|BRAND|MODEL|TYPE for: {filename}\n{text[:500]}").text
        except: return "Unsorted|Unknown|Unknown|Manual"