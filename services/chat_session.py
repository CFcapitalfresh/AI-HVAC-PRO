"""
SERVICE: CHAT SESSION (INTENT AWARE)
------------------------------------
Sorts manuals based on user query keywords.
"""
import streamlit as st
from services.sync_service import SyncService
from core.drive_manager import DriveManager
from core.ai_engine import AIEngine
from core.auth_manager import AuthManager # For logging user interactions
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
            brand = item.get('brand', 'Unknown').upper() # Use extracted metadata field directly (Rule 3)
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
        
        # 1. Βασικό Φιλτράρισμα (Use metadata fields) (Rule 3)
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
        meta_type = item.get('meta_type', '').upper() # Use new metadata field (Rule 3)
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

    def _extract_text_from_stream(self, file_bytes: bytes) -> Optional[str]:
        """Utility function to extract text from a PDF byte stream."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            # Extract text from first few pages to limit token usage for context (e.g., first 5 pages)
            for i in range(min(5, len(reader.pages))):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from file stream: {e}", exc_info=True) # Rule 4
            return None

    def get_manual_content_from_id(self, file_id: str) -> Optional[str]: 
        """
        Κατεβάζει ένα manual από το Drive και εξάγει το κείμενο.
        """
        try:
            file_stream = self.drive.download_file_content(file_id)
            if file_stream:
                file_bytes = file_stream.getvalue()
                return self._extract_text_from_stream(file_bytes)
            return None
        except Exception as e:
            logger.error(f"Error downloading or extracting text from PDF (file ID: {file_id}): {e}", exc_info=True) # Rule 4
            return None

    def smart_solve(self, user_query: str, selected_brand: str, selected_model: str, uploaded_files: List[Any], history: List[Dict[str, str]], lang: str, user_email: str) -> str:
        """
        Οργανώνει την κλήση του AI Engine λαμβάνοντας υπόψη όλα τα inputs:
        user_query, επιλεγμένο manual, uploaded files, και ιστορικό.
        """
        content_parts = []
        full_manual_content = None

        # 1. Προσθήκη ιστορικού συνομιλίας
        for msg in history:
            content_parts.append({"role": msg["role"], "parts": [msg["content"]]})

        # 2. Επεξεργασία uploaded files (Rule 2)
        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    file_bytes = uploaded_file.getvalue()
                    mime_type = uploaded_file.type
                    
                    if "pdf" in mime_type:
                        # Extract text from PDF for context, and pass the file for Vision if needed
                        pdf_text = self._extract_text_from_stream(file_bytes)
                        if pdf_text:
                            content_parts.append({"text": f"--- Συμφραζόμενα από Ανεβασμένο PDF ({uploaded_file.name}) ---\n{pdf_text[:5000]}\n--- Τέλος PDF Context ---"})
                        
                        # Pass PDF directly to Gemini Vision model
                        content_parts.append({
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": file_bytes
                            }
                        })
                        logger.info(f"Processed uploaded PDF: {uploaded_file.name}")
                    elif "image" in mime_type:
                        content_parts.append({
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": file_bytes
                            }
                        })
                        logger.info(f"Processed uploaded image: {uploaded_file.name}")
                except Exception as e:
                    logger.error(f"Error processing uploaded file {uploaded_file.name}: {e}", exc_info=True) # Rule 4
                    st.warning(f"⚠️ Σφάλμα στην επεξεργασία του αρχείου {uploaded_file.name}: {str(e)}")


        # 3. Εύρεση και φόρτωση σχετικών manuals από τη βιβλιοθήκη (μόνο το κορυφαίο 1-2)
        relevant_manuals = []
        if selected_brand != "-":
            relevant_manuals = self.get_prioritized_manuals(selected_brand, selected_model, user_query)
        
        if relevant_manuals:
            # Λαμβάνουμε το περιεχόμενο από τα 1-2 πιο σχετικά manuals για context
            # Για να μην ξεπεράσουμε τα token limits, μπορούμε να πάρουμε τα 1-2 πιο σχετικά
            for i, manual_item in enumerate(relevant_manuals[:2]): # Limit to top 2 manuals
                try:
                    manual_text = self.get_manual_content_from_id(manual_item['file_id'])
                    if manual_text:
                        # Προσθήκη του περιεχομένου ως text part
                        content_parts.append({"text": f"--- Technical Manual ({manual_item['original_name']}) ---\n{manual_text[:5000]}\n--- End Manual Context ---"})
                        logger.info(f"Added manual '{manual_item['original_name']}' to AI context.")
                    if i == 0: # Store the content of the primary manual to pass explicitly if get_chat_response uses it
                        full_manual_content = manual_text
                except Exception as e:
                    logger.error(f"Error fetching content for relevant manual {manual_item['file_id']}: {e}", exc_info=True) # Rule 4

        # 4. Προσθήκη του τρέχοντος ερωτήματος του χρήστη
        content_parts.append({"text": user_query})

        # 5. Κλήση του AI Engine (Rule 3)
        try:
            response = self.ai_engine.get_chat_response(content_parts, lang, manual_file_content=full_manual_content)
            AuthManager.log_interaction(user_email, "AI Chat", user_query[:100]) # Rule 4: Log interaction
            return response
        except Exception as e:
            logger.error(f"Error getting AI response in ChatSessionService: {e}", exc_info=True) # Rule 4
            AuthManager.log_interaction(user_email, "AI Chat Error", f"Query: {user_query[:50]} | Error: {str(e)[:50]}")
            return f"❌ AI System Error: {str(e)}"