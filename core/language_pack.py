### FILE: services/chat_session.py
"""
SERVICE: CHAT SESSION (INTENT AWARE)
------------------------------------
Sorts manuals based on user query keywords.
"""
import streamlit as st
from services.sync_service import SyncService
from core.drive_manager import DriveManager
from core.ai_engine import AIEngine
from typing import List, Dict, Any, Optional
import logging
import io
from pypdf import PdfReader

logger = logging.getLogger("Service.ChatSession")

class ChatSessionService:
    def __init__(self):
        self.sync = SyncService()
        self.drive = DriveManager()
        self.ai_engine = AIEngine()
        if 'library_cache' not in st.session_state:
            st.session_state.library_cache = self.sync.load_index()
        logger.info("ChatSessionService initialized.")

    def get_brands(self):
        """Επιστρέφει τις μάρκες."""
        data = st.session_state.get('library_cache', [])
        brands = set()
        for item in data:
            brand = item.get('brand', '') # Use extracted metadata field directly
            if brand and brand != 'UNKNOWN': brands.add(brand)
        return sorted(list(brands))

    def get_prioritized_manuals(self, brand, model_keyword, user_query):
        """
        ΤΟ ΜΥΣΤΙΚΟ ΟΠΛΟ:
        1. Βρίσκει τα αρχεία της μάρκας.
        2. Καταλαβαίνει τι ρωτάει ο χρήστης (Intent).
        3. Αλλάζει τη σειρά των αρχείων δυναμικά.
        """
        data = st.session_state.get('library_cache', [])
        results = []
        target_brand = brand.upper()
        target_model = model_keyword.upper() if model_keyword else None

        # 1. Βασικό Φιλτράρισμα (χρησιμοποιώντας τα μεταδεδομένα)
        for item in data:
            if item.get('brand', '').upper() == target_brand:
                if target_model and item.get('model', '').upper() == target_model:
                    results.append(item)
                elif not target_model:
                    results.append(item)

        # 2. Ανίχνευση Πρόθεσης (Intent)
        query = user_query.upper()
        intent = "GENERAL"

        if any(x in query for x in ["ERROR", "ΒΛΑΒΗ", "ΣΦΑΛΜΑ", "FAULT", "CODE", "ΚΩΔΙΚΟΣ", "FIX", "PROBLEM"]):
            intent = "ERROR"
        elif any(x in query for x in ["INSTALL", "ΕΓΚΑΤΑΣΤΑΣΗ", "ΣΥΝΔΕΣΗ", "PIPE", "WIRING", "ΔΙΑΣΤΑΣΕΙΣ"]):
            intent = "INSTALL"
        elif any(x in query for x in ["USER", "ΧΡΗΣΗ", "ΟΔΗΓΙΕΣ", "RESET", "ΚΟΥΜΠΙ", "MODE", "ECO"]):
            intent = "USER"
        elif any(x in query for x in ["PART", "ΑΝΤΑΛΛΑΚΤΙΚ", "SPARE", "VALVE", "PCB", "SENSOR", "ΑΙΣΘΗΤΗΡ", "ΤΙΜΗ"]):
            intent = "PARTS"

        # 3. Δυναμική Βαθμολόγηση (Scoring)
        results.sort(key=lambda item: self._calculate_score(item, intent), reverse=True)

        return results

    def _calculate_score(self, item, intent):
        """Δίνει πόντους στο αρχείο ανάλογα με το αν ταιριάζει στην ερώτηση."""
        meta_type = item.get('meta_type', '').upper()
        score = 0

        # --- SCORING RULES ---
        if intent == "PARTS":
            if "SPARE" in meta_type: score += 100
            elif "SERVICE" in meta_type: score += 50
            else: score += 10

        elif intent == "ERROR":
            if "SERVICE" in meta_type: score += 100
            elif "INSTALLATION" in meta_type: score += 90
            elif "USER" in meta_type: score += 40
            elif "SPARE" in meta_type: score += 10

        elif intent == "INSTALL":
            if "INSTALLATION" in meta_type: score += 100
            elif "TECHNICAL" in meta_type: score += 80
            elif "SERVICE" in meta_type: score += 60

        elif intent == "USER":
            if "USER" in meta_type: score += 100
            elif "INSTALLATION" in meta_type: score += 50

        else: # GENERAL (Default)
            if "SERVICE" in meta_type: score += 90
            elif "INSTALLATION" in meta_type: score += 80
            elif "USER" in meta_type: score += 70
            elif "SPARE" in meta_type: score += 20

        return score

    def handle_manual_upload(self, uploaded_file, brand, model):
        root_id = ConfigLoader.get_drive_folder_id()
        if not root_id: return False
        safe_name = f"User_Uploads | {brand} | {model} | {uploaded_file.name}"
        file_id = self.drive.upload_stream(uploaded_file, safe_name, root_id)
        if file_id:
            new_entry = {'file_id': file_id, 'name': safe_name, 'link': f"https://drive.google.com/file/d/{file_id}/view", 'mime': 'application/pdf'}
            st.session_state.library_cache.append(new_entry)
            return True
        return False

    def get_manual_content_from_id(self, file_id: str) -> Optional[str]:
        """Κατεβάζει ένα manual από το Drive και εξάγει το κείμενό του."""
        try:
            stream = self.drive.download_file_content(file_id)
            if not stream:
                logger.error(f"Failed to download content for file_id: {file_id}")
                return None

            reader = PdfReader(io.BytesIO(stream.getvalue()))
            text = ""
            for i in range(min(5, len(reader.pages))):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + "\n"

            logger.info(f"Extracted {len(text)} characters from manual ID: {file_id}")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from manual ID: {file_id}. Error: {e}", exc_info=True)
            return None

    def smart_solve(self, user_query: str, uploaded_pdfs: List[Any], uploaded_imgs: List[Any], history: List[Dict], lang: str = "gr", manual_file_content: Optional[str] = None) -> str:
        """
        Λογική επίλυσης προβλημάτων που χρησιμοποιεί AI και επισυναπτόμενα αρχεία.
        Προετοιμάζει τα content parts για το AI Engine.
        """
        if not self.ai_engine.model:
            logger.error(f"AI System Error: AI Engine not initialized in ChatSessionService. Last error: {self.ai_engine.last_error or 'Unknown'}")
            return f"❌ **AI System Error:** AI Engine not initialized. {self.ai_engine.last_error or ''}"

        # 1. Προετοιμασία Content Parts (History)
        content_parts = []
        for msg in history[-10:]:
            content_parts.append({"text": f"Προηγούμενος Χρήστης: {msg['content']}"})

        # 2. Προσθήκη PDF αρχείων (από το βασικό chat input)
        for pdf_file in uploaded_pdfs:
            pdf_bytes = pdf_file.getvalue()
            content_parts.append({"mime_type": "application/pdf", "data": pdf_bytes})
            content_parts.append({"text": f"Αρχείο PDF: {pdf_file.name}"})

        # 3. Προσθήκη εικόνων (από το βασικό chat input)
        for img_file in uploaded_imgs:
            img_bytes = img_file.getvalue()
            content_parts.append({"mime_type": img_file.type, "data": img_bytes})
            content_parts.append({"text": f"Εικόνα: {img_file.name}"})

        # 4. Προσθήκη της τρέχουσας ερώτησης του χρήστη
        content_parts.append({"text": f"Τρέχουσα Ερώτηση Χρήστη: {user_query}"})

        # 5. Κλήση του AI Engine
        # Διορθώθηκε η κλήση για να χρησιμοποιεί το `manual_file_content` που περνάει από το UI
        response = self.ai_engine.get_chat_response(content_parts=content_parts, lang=lang, manual_file_content=manual_file_content)
        return response