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
from pypdf import PdfReader # Used for text extraction
from PIL import Image # For image processing (if needed for AI)

logger = logging.getLogger("Service.ChatSession")

class ChatSessionService:
    def __init__(self):
        self.sync = SyncService()
        self.drive = DriveManager()
        self.ai_engine = AIEngine()
        if 'library_cache' not in st.session_state:
            st.session_state.library_cache = self.sync.load_index()
        logger.info("ChatSessionService initialized.")

    def get_brands(self) -> List[str]:
        """Επιστρέφει τις μάρκες από τα metadata του ευρετηρίου."""
        data = st.session_state.get('library_cache', [])
        brands = set()
        for item in data:
            brand = item.get('brand', 'Unknown').upper() # Use extracted metadata field directly
            if brand and brand != 'UNKNOWN': brands.add(brand)
        return sorted(list(brands))

    def get_prioritized_manuals(self, brand: str, model_keyword: str, user_query: str) -> List[Dict[str, Any]]:
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
        
        # 1. Βασικό Φιλτράρισμα (Use metadata fields)
        for item in data:
            item_brand = item.get('brand', '').upper()
            item_model = item.get('model', '').upper()
            
            if item_brand == target_brand:
                if not target_model or target_model in item_model: # Allow model match or no model filter
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

    def _calculate_score(self, item: Dict[str, Any], intent: str) -> int:
        """Δίνει πόντους στο αρχείο ανάλογα με το αν ταιριάζει στην ερώτηση."""
        meta_type = item.get('meta_type', '').upper() # Use new metadata field
        score = 0
        
        # --- SCORING RULES --- (Refined to use meta_type)
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

    def get_manual_text_content(self, file_id: str) -> Optional[str]:
        """Κατεβάζει ένα manual από το Drive και εξάγει το κείμενο."""
        try:
            file_stream = self.drive.download_file_content(file_id)
            if file_stream:
                reader = PdfReader(file_stream)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
            return None
        except Exception as e:
            logger.error(f"Error extracting text from PDF (file ID: {file_id}): {e}", exc_info=True)
            return None

    def handle_manual_upload(self, uploaded_file, brand, model) -> Optional[str]:
        """
        Ανεβάζει ένα αρχείο στο Drive και επιστρέφει το ID του.
        (UNUSED IN CURRENT UI, KEPT FOR POTENTIAL FUTURE USE OR AI-DIRECTED UPLOAD)
        """
        root_id = self.drive.root_id
        if not root_id:
            logger.error("Root Drive folder ID is not configured.")
            return None
        
        # Create a structured name for the uploaded file
        safe_name = f"User_Uploads | {brand or 'Unknown'} | {model or 'Generic'} | {uploaded_file.name}"
        try:
            file_id = self.drive.upload_stream(uploaded_file, safe_name, root_id)
            return file_id
        except Exception as e:
            logger.error(f"Failed to upload user file '{uploaded_file.name}' to Drive: {e}", exc_info=True)
            return None

    def get_ai_response(self, user_prompt: Optional[str], uploaded_files: List[Any], 
                        manual_contexts: List[str], chat_history: List[Dict[str, str]], lang: str) -> str:
        """
        Επικοινωνεί με το AI Engine για να λάβει απάντηση,
        συμπεριλαμβάνοντας κείμενο, ανεβασμένα αρχεία και manual contexts.
        """
        content_parts = []

        # Add chat history as text parts for context
        for msg in chat_history:
            content_parts.append({"text": f"{msg['role']}: {msg['content']}"})

        # Add the current user prompt
        if user_prompt:
            content_parts.append({"text": f"user: {user_prompt}"})

        # Add uploaded files (images & PDFs)
        for uploaded_file in uploaded_files:
            file_type = uploaded_file.type
            file_bytes = uploaded_file.getvalue()
            
            if "image" in file_type:
                img = Image.open(io.BytesIO(file_bytes))
                content_parts.append(img) # AI Engine expects PIL Image directly
            elif "pdf" in file_type:
                # For PDFs, extract text and send as text_part (or directly as bytes for Vision if supported)
                # Current AIEngine expects file-like objects for direct PDF parsing
                content_parts.append(io.BytesIO(file_bytes)) # Pass as bytes stream for direct AI parsing
            else:
                logger.warning(f"Unsupported file type uploaded: {file_type}")
        
        # Add manual contexts
        if manual_contexts:
            context_text = "\n\n--- MANUAL CONTEXT ---\n" + "\n\n".join(manual_contexts)
            content_parts.append({"text": context_text})
            logger.info(f"AI Call: Added {len(manual_contexts)} manual contexts.")

        try:
            if not content_parts: # Should not happen if prompt or files are present
                return "Παρακαλώ δώστε μια ερώτηση ή ανεβάστε αρχείο."
            
            response = self.ai_engine.get_chat_response(content_parts, lang=lang)
            return response
        except Exception as e:
            logger.error(f"Error getting AI response in ChatSessionService: {e}", exc_info=True)
            return f"❌ Σφάλμα επικοινωνίας με το AI: {e}"