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
        self.sync = SyncService() # Rule 3
        self.drive = DriveManager() # Rule 7
        self.ai_engine = AIEngine() # Rule 3
        # Rule 6: Ensure library_cache is initialized once
        if 'library_cache' not in st.session_state:
            try: # Rule 4: Error Handling
                st.session_state.library_cache = self.sync.load_index()
                logger.info("Library cache loaded during ChatSessionService init.") # Rule 4
            except Exception as e:
                logger.error(f"Failed to load library cache in ChatSessionService: {e}", exc_info=True) # Rule 4
                st.session_state.library_cache = [] # Ensure it's a list even on error
        logger.info("ChatSessionService initialized.") # Rule 4

    def get_brands(self) -> List[str]:
        """Επιστρέφει τις μάρκες από τα metadata του ευρετηρίου."""
        data = st.session_state.get('library_cache', []) # Rule 6
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
        data = st.session_state.get('library_cache', []) # Rule 6
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

    def handle_manual_upload(self, uploaded_file: Any, brand: str, model: str) -> bool:
        """
        Χειρίζεται την μεταφόρτωση αρχείων (PDF/Εικόνων) από τον χρήστη στο Google Drive.
        """
        # Rule 7: Ensure DriveManager is used correctly.
        root_id = self.drive.root_id
        if not root_id: 
            logger.error("Drive root folder ID is missing. Cannot upload user manual.") # Rule 4
            return False

        try: # Rule 4: Error Handling
            # Create a dedicated "User_Uploads" folder if it doesn't exist
            user_uploads_folder_id = self.drive.create_folder("User_Uploads", root_id) # Rule 7
            if not user_uploads_folder_id:
                logger.error("Failed to create/find 'User_Uploads' folder in Drive.") # Rule 4
                return False

            # Construct a descriptive filename for the uploaded file in Drive
            safe_name = f"User_Uploads | {brand if brand != '-' else 'Unknown_Brand'} | {model if model else 'Unknown_Model'} | {uploaded_file.name}"
            
            # Use DriveManager's upload_stream method
            file_id = self.drive.upload_stream(uploaded_file, safe_name, user_uploads_folder_id) # Rule 7
            
            if file_id:
                # Add the newly uploaded file to the session_state.library_cache
                # This ensures it's immediately available for the current session.
                new_entry = {
                    'file_id': file_id, 
                    'name': safe_name, 
                    'link': self.drive.get_file_link(file_id), # Rule 7
                    'mime': uploaded_file.type,
                    'category': 'User_Uploads', # Custom category for user uploads
                    'brand': brand if brand != '-' else 'Unknown_Brand',
                    'model': model if model else 'Unknown_Model',
                    'meta_type': 'User_Upload',
                    'error_codes': '',
                    'original_name': uploaded_file.name
                }
                st.session_state.library_cache.append(new_entry) # Rule 6
                logger.info(f"User file '{uploaded_file.name}' uploaded to Drive with ID: {file_id}") # Rule 4
                return True
            else:
                logger.error(f"Failed to get file ID after uploading '{uploaded_file.name}'.") # Rule 4
                return False
        except Exception as e:
            logger.error(f"Error handling manual upload for '{uploaded_file.name}': {e}", exc_info=True) # Rule 4
            return False

    def _extract_text_from_stream(self, file_bytes: bytes) -> Optional[str]:
        """Utility function to extract text from a PDF byte stream."""
        try: # Rule 4: Error Handling
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for i in range(min(5, len(reader.pages))): # Limit pages for performance and token economy
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from file stream: {e}", exc_info=True) # Rule 4
            return None

    def get_manual_content_from_id(self, file_id: str) -> Optional[str]: 
        """
        Κατεβάζει ένα manual από το Drive και εξάγει το κείμενο του.
        """
        try: # Rule 4: Error Handling
            stream = self.drive.download_file_content(file_id) # Rule 7
            if stream:
                stream.seek(0)
                file_bytes = stream.read()
                return self._extract_text_from_stream(file_bytes)
            logger.warning(f"Failed to download content for file ID: {file_id}") # Rule 4
            return None
        except Exception as e:
            logger.error(f"Error getting manual content for ID '{file_id}': {e}", exc_info=True) # Rule 4
            return None

    def smart_solve(
        self, 
        user_query: str, 
        uploaded_pdfs: List[Any], 
        uploaded_imgs: List[Any], 
        history: List[Dict[str, str]],
        selected_brand: str, # NEW: for context-aware search
        selected_model: str, # NEW: for context-aware search
        lang: str = "gr" # Rule 5
    ) -> str:
        """
        Χρησιμοποιεί το AI για να απαντήσει στην ερώτηση του χρήστη,
        λαμβάνοντας υπόψη το ιστορικό, τα ανεβασμένα αρχεία και τα σχετικά manuals.
        """
        # Rule 3: Delegates to AIEngine
        # Rule 4: Error Handling
        if not self.ai_engine.model:
            logger.error("AI Engine model not initialized for smart_solve.") # Rule 4
            return f"{self.ai_engine.last_error or 'AI Model not initialized.'}"

        content_parts = []
        manual_text_content = "" # For text extracted from prioritized manuals

        # 1. Add user query to content parts
        content_parts.append({"text": user_query})

        # 2. Process uploaded files (Rule 2)
        if uploaded_pdfs:
            for uploaded_file in uploaded_pdfs:
                try: # Rule 4
                    file_bytes = uploaded_file.getvalue()
                    content_parts.append({"mime_type": "application/pdf", "data": file_bytes})
                    logger.info(f"Added uploaded PDF '{uploaded_file.name}' to AI context.") # Rule 4
                except Exception as e:
                    logger.error(f"Error processing uploaded PDF '{uploaded_file.name}': {e}", exc_info=True) # Rule 4

        if uploaded_imgs:
            for uploaded_file in uploaded_imgs:
                try: # Rule 4
                    file_bytes = uploaded_file.getvalue()
                    content_parts.append({"mime_type": uploaded_file.type, "data": file_bytes})
                    logger.info(f"Added uploaded image '{uploaded_file.name}' to AI context.") # Rule 4
                except Exception as e:
                    logger.error(f"Error processing uploaded image '{uploaded_file.name}': {e}", exc_info=True) # Rule 4

        # 3. Get relevant manuals based on current context (brand/model) and user query
        if selected_brand and selected_brand != '-':
            # Get a few highly prioritized manuals
            prioritized_manuals = self.get_prioritized_manuals(selected_brand, selected_model, user_query)
            
            # Limit to top 2-3 manuals for token efficiency (adjust as needed)
            for manual in prioritized_manuals[:3]: 
                try: # Rule 4
                    manual_content = self.get_manual_content_from_id(manual['file_id'])
                    if manual_content:
                        manual_text_content += f"\n\n--- MANUAL: {manual.get('original_name', manual['name'])} ---\n{manual_content}"
                        logger.info(f"Added text from manual '{manual.get('original_name', manual['name'])}' to AI context.") # Rule 4
                except Exception as e:
                    logger.error(f"Error retrieving content for manual ID {manual['file_id']}: {e}", exc_info=True) # Rule 4

        # 4. Add conversation history
        for msg in history:
            content_parts.append({"text": f"{msg['role']}: {msg['content']}"})

        # 5. Call AI Engine with all collected parts
        try: # Rule 4: Error Handling
            response = self.ai_engine.get_chat_response(
                content_parts=content_parts,
                lang=lang,
                manual_file_content=manual_text_content # Pass extracted text separately
            )
            return response
        except Exception as e:
            logger.error(f"Error calling AI Engine for smart_solve: {e}", exc_info=True) # Rule 4
            return f"❌ {self.ai_engine.last_error or 'AI system error'}: {e}"