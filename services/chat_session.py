"""
SERVICE: CHAT SESSION (INTENT AWARE)
------------------------------------
Sorts manuals based on user query keywords.
Handles file uploads and AI interaction.
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
        # Rule 6: Ensure library_cache is initialized once
        if 'library_cache' not in st.session_state:
            try:
                st.session_state.library_cache = self.sync.load_index()
                logger.info("Library cache loaded during ChatSessionService init.")
            except Exception as e:
                logger.error(f"Failed to load library cache in ChatSessionService: {e}", exc_info=True)
                st.session_state.library_cache = [] # Ensure it's a list even on error
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

    def _extract_text_from_pdf_stream(self, file_bytes: bytes) -> Optional[str]:
        """Utility function to extract text from a PDF byte stream."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            # Extract text from first few pages to limit token usage for AI
            for i in range(min(5, len(reader.pages))): # Process first 5 pages
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF stream: {e}", exc_info=True)
            return None

    def _process_uploaded_file_for_ai(self, uploaded_file: Any) -> Optional[Dict[str, Any]]:
        """
        Επεξεργάζεται ένα Streamlit UploadedFile object για χρήση από το AI.
        Επιστρέφει ένα dictionary με το `mime_type` και τα `parts` για το AI.
        """
        try:
            file_bytes = uploaded_file.getvalue()
            mime_type = uploaded_file.type
            
            if "pdf" in mime_type:
                # Για PDF, εξάγουμε κείμενο και το στέλνουμε ως text_part
                text_content = self._extract_text_from_pdf_stream(file_bytes)
                if text_content:
                    return {"mime_type": mime_type, "parts": [
                        {"text": f"Uploaded PDF: {uploaded_file.name}\nContent:\n{text_content}"}
                    ]}
                else:
                    logger.warning(f"Could not extract text from PDF: {uploaded_file.name}")
                    return None
            elif "image" in mime_type:
                # Για εικόνες, το στέλνουμε ως encoded image part
                return {"mime_type": mime_type, "parts": [
                    {"image": file_bytes}
                ]}
            else:
                logger.warning(f"Unsupported uploaded file type: {mime_type} for {uploaded_file.name}")
                return None
        except Exception as e:
            logger.error(f"Error processing uploaded file {uploaded_file.name}: {e}", exc_info=True)
            return None

    def get_manual_content_from_id(self, file_id: str) -> Optional[str]: 
        """
        Κατεβάζει ένα manual από το Drive και εξάγει το κείμενο.
        """
        try:
            file_stream = self.drive.download_file_content(file_id)
            if file_stream:
                file_bytes = file_stream.getvalue()
                return self._extract_text_from_pdf_stream(file_bytes)
            return None
        except Exception as e:
            logger.error(f"Error extracting text from PDF (file ID: {file_id}): {e}", exc_info=True)
            return None

    def process_chat_input(
        self, 
        user_query: str, 
        selected_brand: str, 
        selected_model: str, 
        uploaded_pdfs: List[Any], 
        uploaded_images: List[Any], 
        history: List[Dict[str, Any]], 
        lang: str,
        user_email: str
    ) -> str:
        """
        Επεξεργάζεται την είσοδο του χρήστη, συμπεριλαμβανομένων των ανεβασμένων αρχείων,
        και αλληλεπιδρά με το AI Engine.
        Args:
            user_query: Το κείμενο της ερώτησης του χρήστη.
            selected_brand: Η επιλεγμένη μάρκα για context.
            selected_model: Το επιλεγμένο μοντέλο για context.
            uploaded_pdfs: Λίστα με Streamlit UploadedFile objects για PDF.
            uploaded_images: Λίστα με Streamlit UploadedFile objects για εικόνες.
            history: Ιστορικό συνομιλίας.
            lang: Τρέχουσα γλώσσα.
            user_email: Email χρήστη για logging.
        Returns:
            Η απάντηση του AI.
        """
        all_content_parts = []
        manual_context_text = ""

        # 1. Προσθήκη ιστορικού συνομιλίας ως content parts
        for msg in history:
            all_content_parts.append({"text": f"{msg['role']}: {msg['content']}"})

        # 2. Επεξεργασία ανεβασμένων αρχείων (Rule 2)
        if uploaded_pdfs or uploaded_images:
            for file in uploaded_pdfs + uploaded_images:
                file_ai_parts = self._process_uploaded_file_for_ai(file)
                if file_ai_parts:
                    all_content_parts.extend(file_ai_parts["parts"])
                    logger.info(f"Processed uploaded file '{file.name}' for AI.")
                else:
                    logger.warning(f"Skipping unsupported/unreadable uploaded file: {file.name}")

        # 3. Εύρεση και προσθήκη manuals από τη βιβλιοθήκη
        if selected_brand and selected_brand != "-":
            prioritized_manuals = self.get_prioritized_manuals(selected_brand, selected_model, user_query)
            
            # Λήψη περιεχομένου από τα κορυφαία manuals (π.χ., τα πρώτα 3)
            for manual in prioritized_manuals[:3]: # Limit to top 3 to control token usage
                try:
                    manual_content = self.get_manual_content_from_id(manual['file_id'])
                    if manual_content:
                        manual_context_text += f"\n\n--- MANUAL: {manual['name']} ---\n{manual_content[:5000]}" # Limit manual text
                        logger.info(f"Added manual '{manual['name']}' to AI context.")
                except Exception as e:
                    logger.error(f"Error getting manual content for {manual.get('name', 'N/A')}: {e}", exc_info=True)
            
            if manual_context_text:
                all_content_parts.append({"text": f"\n\n--- Relevant Manuals Context ---\n{manual_context_text}"})


        # 4. Προσθήκη του ερωτήματος του χρήστη
        all_content_parts.append({"text": user_query})

        # 5. Κλήση του AI Engine
        try:
            response = self.ai_engine.get_chat_response(
                content_parts=all_content_parts, 
                lang=lang, 
                manual_file_content=manual_context_text # Pass directly here
            )
            # Log successful interaction (Rule 4)
            # Assuming AuthManager.log_interaction exists and uses DBConnector.append_data
            try:
                from core.auth_manager import AuthManager
                AuthManager.log_interaction(user_email, "AI Chat Query", user_query[:100])
            except ImportError:
                logger.warning("AuthManager not available for logging chat interaction.")
            except Exception as e:
                logger.error(f"Failed to log chat interaction for {user_email}: {e}", exc_info=True)

            return response
        except Exception as e:
            logger.error(f"AI Engine chat response failed: {e}", exc_info=True) # Rule 4
            return f"❌ AI Engine Error: {e}"