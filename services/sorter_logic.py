"""
SERVICE: AI SORTER LOGIC (DYNAMIC DISCOVERY EDITION)
----------------------------------------------------
Features:
- AUTO-DETECT MODEL: Ρωτάει την Google ποιο μοντέλο είναι ενεργό (Gemini 2.0, 1.5, Pro κλπ).
- NO HARDCODED NAMES: Δεν κρασάρει αν αλλάξει η ονομασία.
- 4-Level Sorting: Category > Brand > Model > Type
- ENHANCED FEEDBACK: Provides more detailed progress to the UI.
- CANCELLATION: Adds a mechanism to stop the sorting process.
- NEW: Irrelevant/Unknown File Handling
- NEW: Duplicate File Detection (Hashing)
- NEW: AI-driven File Renaming
- NEW: Enhanced Summary Reporting for UI
- NEW: Force Full Rescan option.
"""
import streamlit as st
from core.drive_manager import DriveManager
from core.config_loader import ConfigLoader
import google.generativeai as genai
import logging
import time
import io
import os
import pypdf
import re
import tempfile
import hashlib # ΝΕΟ: Για υπολογισμό hash
from collections import defaultdict # ΝΕΟ: Για πιο εύκολη καταμέτρηση στατιστικών
from datetime import datetime # ΝΕΟ: Για timestamp

from core.ai_engine import AIEngine # Rule 3: Use central AI Engine

logger = logging.getLogger("Sorter")

ALLOWED_CATEGORIES = [
    "Heating_Boilers", "Heat_Pumps", "Air_Conditioning", "Solar_Systems", 
    "Water_Heaters", "Thermostats_Controllers", "Spare_Parts_Valves", "Other_HVAC"
]

ALLOWED_TYPES = [
    "User_Manual", "Service_Manual", "Installation_Manual", 
    "Technical_Data", "Error_Codes", "Spare_Parts_List", "General_Manual" # Added General_Manual
]

# ΝΕΟΙ ΦΑΚΕΛΟΙ: Για άσχετα/μη αναγνωρίσιμα και διπλότυπα
IRRELEVANT_OR_UNKNOWN_FOLDER = "_IRRELEVANT_OR_UNKNOWN"
DUPLICATES_FOLDER = "_DUPLICATES"
MANUAL_REVIEW_FOLDER = "_MANUAL_REVIEW" # Added for consistency

# IGNORED_FOLDERS_TOP_LEVEL now includes the new special folders
IGNORED_FOLDERS_TOP_LEVEL = [
    MANUAL_REVIEW_FOLDER, 
    "_AI_ERROR", 
    "Trash", 
    "_NEEDS_OCR",
    IRRELEVANT_OR_UNKNOWN_FOLDER, 
    DUPLICATES_FOLDER 
]

class SorterService:
    def __init__(self):
        self.drive = DriveManager()
        # Rule 3: Use the central AIEngine instance.
        # It handles its own setup and model discovery.
        self.ai_engine = AIEngine() 
        self.model = self.ai_engine.model # Get the already initialized model
        self.api_key = self.ai_engine.api_key # Get API key from AIEngine
        self.root_id = ConfigLoader.get_drive_folder_id()
        # Removed redundant _setup_ai() call here, as AIEngine's __init__ handles it.

    # Removed _setup_ai method as AIEngine handles it centrally (Rule 3)

    def _calculate_file_hash(self, file_bytes):
        """Υπολογίζει το SHA256 hash του αρχείου."""
        if file_bytes is None:
            return None
        return hashlib.sha256(file_bytes).hexdigest()

    def _extract_text_from_pdf(self, file_id):
        """Εξάγει κείμενο και bytes από PDF, υπολογίζοντας και το hash."""
        try:
            stream = self.drive.download_file_content(file_id)
            if not stream: return None, None, None
            stream.seek(0)
            file_bytes = stream.read()
            
            file_hash = self._calculate_file_hash(file_bytes)

            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text = ""
            # Extract text from first few pages to limit token usage for AI
            for i in range(min(8, len(reader.pages))): 
                text += reader.pages[i].extract_text() or ""
            return text[:5000], file_bytes, file_hash 
        except Exception as e:
            logger.error(f"Error extracting text or calculating hash for file {file_id}: {e}", exc_info=True)
            return None, None, None

    def _get_ai_classification(self, filename: str, file_text: str):
        """
        Χρησιμοποιεί το AI για να κατηγοριοποιήσει και να ονομάσει το αρχείο.
        """
        if not self.model:
            logger.error("AI model not initialized for classification.")
            return None, None, None, None, None

        # Rule 5: Ensure prompt is multilingual or robust to different languages if input is varied
        # For now, English for processing, output format dictates GR/EN
        prompt = f"""
        Analyze the following document and determine its Category, Brand, Model, and Meta_Type.
        Also, suggest a new, cleaned filename based on the extracted metadata and the original name.
        The document's content starts with:
        ---
        {file_text}
        ---
        Original filename: {filename}

        Allowed Categories: {', '.join(ALLOWED_CATEGORIES)}
        Allowed Meta_Types: {', '.join(ALLOWED_TYPES)}

        If you cannot confidently determine a value, use 'Unknown'.
        If the document is clearly irrelevant to HVAC, use 'IRRELEVANT_OR_UNKNOWN' for Category and Meta_Type.

        Output MUST be in JSON format:
        {{
            "category": "Determined_Category",
            "brand": "Determined_Brand",
            "model": "Determined_Model",
            "meta_type": "Determined_Meta_Type",
            "error_codes": "Comma_separated_error_codes_found_in_document_or_empty",
            "suggested_filename": "CLEAN_BRAND_MODEL_TYPE_NAME.pdf"
        }}
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            response_text = response.text.strip()
            # Robust JSON parsing (Rule 4)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                clean_json_str = response_text[start_idx:end_idx]
                classification = json.loads(clean_json_str)
                
                cat = classification.get('category', 'Unknown').replace(" ", "_")
                brand = classification.get('brand', 'Unknown').replace(" ", "_")
                model = classification.get('model', 'General_Model').replace(" ", "_")
                m_type = classification.get('meta_type', 'General_Manual').replace(" ", "_")
                errors = classification.get('error_codes', '')
                suggested_filename = classification.get('suggested_filename', filename)

                # Validate against allowed categories/types
                if cat not in ALLOWED_CATEGORIES:
                    if cat == "IRRELEVANT_OR_UNKNOWN":
                        cat = IRRELEVANT_OR_UNKNOWN_FOLDER # Map to special folder
                        m_type = IRRELEVANT_OR_UNKNOWN_FOLDER
                    else:
                        logger.warning(f"AI suggested invalid category '{cat}'. Defaulting to 'Other_HVAC'.")
                        cat = "Other_HVAC"
                
                if m_type not in ALLOWED_TYPES and m_type != IRRELEVANT_OR_UNKNOWN_FOLDER:
                    logger.warning(f"AI suggested invalid meta_type '{m_type}'. Defaulting to 'General_Manual'.")
                    m_type = "General_Manual"

                return cat, brand, model, m_type, errors, suggested_filename
            else:
                logger.error(f"AI returned invalid JSON: {response_text}")
                return None, None, None, None, None, None

        except Exception as e:
            logger.error(f"AI classification failed for {filename}: {e}", exc_info=True)
            return None, None, None, None, None, None

    def _get_or_create_path(self, parent_id, path_parts):
        """Δημιουργεί μια ιεραρχία φακέλων στο Drive αν δεν υπάρχει."""
        current_parent_id = parent_id
        for part in path_parts:
            # Avoid creating folders for special top-level ignored names (Rule 3)
            if part in IGNORED_FOLDERS_TOP_LEVEL and current_parent_id == self.root_id:
                folder_id = self.drive.create_folder(part, current_parent_id) # Ensure special folders exist
                if not folder_id: raise Exception(f"Failed to get/create special folder: {part}")
                return folder_id # For these special folders, the path ends here for sorting purposes.

            folder_id = self.drive.create_folder(part, current_parent_id)
            if not folder_id:
                raise Exception(f"Failed to get or create folder: {part} under {current_parent_id}")
            current_parent_id = folder_id
        return current_parent_id

    def run_sorter(self, my_bar: st.progress, progress_text_container: st.empty, stop_flag_key: str, force_full_rescan: bool = False):
        """
        Εκτελεί τη διαδικασία ταξινόμησης, μετονομασίας και οργάνωσης αρχείων.
        Ενημερώνει μια μπάρα προόδου στο Streamlit.
        """
        logger.info(f"AI Sorter started. Force full rescan: {force_full_rescan}")
        progress_text_container.text("Αρχικοποίηση οργανωτή...")
        
        if not self.root_id:
            logger.error("Root Drive folder ID is missing.")
            progress_text_container.error("Root Drive folder ID is missing. Please check config.")
            return None

        if not self.model:
            logger.error("AI model is not initialized. Cannot run sorter.")
            progress_text_container.error("AI model is not initialized. Cannot run sorter.")
            return None

        current_run_log = []
        summary = {
            "last_run_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_files_scanned": 0,
            "total_successfully_sorted": 0,
            "total_moved_to_manual_review": 0,
            "total_moved_to_irrelevant": 0,
            "total_moved_to_duplicates": 0,
            "failed_files": [],
            "manual_review_files": [],
            "irrelevant_files": [],
            "duplicate_files": [],
            "category_counts": defaultdict(int),
            "brand_counts": defaultdict(int),
            "type_counts": defaultdict(int),
        }

        # Clear existing special folders if force_full_rescan (Rule 3)
        if force_full_rescan:
            progress_text_container.text("Διαγραφή υπαρχόντων φακέλων...")
            logger.info("Force full rescan enabled. Deleting existing categorized folders.")
            try:
                # Get all children of root, excluding index file and other known files
                all_root_children = self.drive.list_files_in_folder(self.root_id)
                folders_to_delete = [
                    f for f in all_root_children 
                    if f['mimeType'] == 'application/vnd.google-apps.folder' and 
                       f['name'] not in [f for f in IGNORED_FOLDERS_TOP_LEVEL if not f.startswith('_')] # Protect system folders
                ]
                for folder in folders_to_delete:
                    self.drive.delete_file(folder['id'])
                    logger.info(f"Deleted folder: {folder['name']} ({folder['id']})")
                current_run_log.append(f"✅ Deleted {len(folders_to_delete)} top-level categories due to full rescan.")

                # Delete files in the root that are not part of known system files (e.g., unsorted files)
                root_files_to_delete = [
                    f for f in all_root_children
                    if f['mimeType'] != 'application/vnd.google-apps.folder' and 
                       not f['name'].startswith('drive_index') and 
                       not f['name'].startswith('drive_config') and
                       not f['name'].startswith('SpyLogs') # Protect system logs
                ]
                for file_item in root_files_to_delete:
                    self.drive.delete_file(file_item['id'])
                    logger.info(f"Deleted root file: {file_item['name']} ({file_item['id']})")
                current_run_log.append(f"✅ Deleted {len(root_files_to_delete)} unsorted files from root due to full rescan.")

            except Exception as e:
                logger.error(f"Error during full rescan folder cleanup: {e}", exc_info=True)
                current_run_log.append(f"❌ Error during full rescan cleanup: {e}")
                progress_text_container.error(f"Σφάλμα κατά τον καθαρισμό: {e}")
                return None


        # 1. Βρείτε όλα τα αρχεία για επεξεργασία (Rule 3)
        files_to_process = []
        all_drive_files = self.drive.list_files_in_folder(self.root_id)
        
        # Collect files not in predefined (ignored) folders
        for file_item in all_drive_files:
            # Check if file is directly in root and is a PDF
            is_pdf = file_item['mimeType'] == 'application/pdf'
            
            # Check if it's in an ignored folder (e.g. _MANUAL_REVIEW) (Rule 3)
            is_in_ignored_folder = False
            if 'parents' in file_item and file_item['parents']:
                parent_folder_id = file_item['parents'][0] # Assuming single parent
                parent_files = self.drive.list_files_in_folder(parent_folder_id) # Get parent details
                parent_name = next((f['name'] for f in parent_files if f['id'] == parent_folder_id), '') # Get parent name
                if parent_name in IGNORED_FOLDERS_TOP_LEVEL:
                    is_in_ignored_folder = True

            # Process only PDFs that are not in ignored folders and are not the index file, or config files.
            if is_pdf and not is_in_ignored_folder and not file_item['name'].startswith('drive_index') and not file_item['name'].startswith('drive_config'):
                files_to_process.append(file_item)

        if not files_to_process:
            progress_text_container.info("Δεν βρέθηκαν αρχεία για ταξινόμηση.")
            current_run_log.append("ℹ️ No files found to process.")
            my_bar.progress(100)
            return summary, current_run_log
        
        total_files = len(files_to_process)
        summary["total_files_scanned"] = total_files
        file_hashes = {} # Για ανίχνευση διπλότυπων (Rule 3)

        for i, file_item in enumerate(files_to_process):
            if st.session_state.get(stop_flag_key, False):
                current_run_log.append(f"⚠️ Sorter stopped by user at file {i+1}/{total_files}.")
                progress_text_container.warning("Ο οργανωτής σταμάτησε από τον χρήστη.")
                break

            progress_percent = int(((i + 1) / total_files) * 100)
            progress_text_container.text(f"Επεξεργασία αρχείου ({i+1}/{total_files}): {file_item['name']}")
            my_bar.progress(progress_percent)

            file_id = file_item['id']
            original_filename = file_item['name']

            try:
                file_text, file_bytes, file_hash = self._extract_text_from_pdf(file_id)

                # Check for duplicates (Rule 3)
                if file_hash:
                    if file_hash in file_hashes:
                        duplicate_info = file_hashes[file_hash]
                        logger.info(f"Detected duplicate: {original_filename} is a duplicate of {duplicate_info['original_name']}")
                        current_run_log.append(f"ℹ️ Duplicate found: '{original_filename}'. Original: '{duplicate_info['original_name']}'. Moving to '{DUPLICATES_FOLDER}'.")
                        
                        duplicate_folder_id = self._get_or_create_path(self.root_id, [DUPLICATES_FOLDER])
                        if self.drive.move_file(file_id, duplicate_folder_id):
                            summary["total_moved_to_duplicates"] += 1
                            summary["duplicate_files"].append(file_item)
                        else:
                            current_run_log.append(f"❌ Failed to move duplicate file {original_filename}.")
                        continue
                    else:
                        file_hashes[file_hash] = {"file_id": file_id, "original_name": original_filename}

                if not file_text:
                    logger.warning(f"Could not extract text from {original_filename}. Moving to '{MANUAL_REVIEW_FOLDER}'.")
                    current_run_log.append(f"⚠️ No text extracted from '{original_filename}'. Moving to '{MANUAL_REVIEW_FOLDER}'.")
                    manual_review_folder_id = self._get_or_create_path(self.root_id, [MANUAL_REVIEW_FOLDER])
                    self.drive.move_file(file_id, manual_review_folder_id)
                    summary["total_moved_to_manual_review"] += 1
                    summary["manual_review_files"].append(file_item)
                    continue

                category, brand, model, meta_type, error_codes, suggested_filename = self._get_ai_classification(original_filename, file_text)

                if category == IRRELEVANT_OR_UNKNOWN_FOLDER:
                    logger.info(f"File '{original_filename}' classified as irrelevant/unknown. Moving to '{IRRELEVANT_OR_UNKNOWN_FOLDER}'.")
                    current_run_log.append(f"ℹ️ File '{original_filename}' classified as irrelevant/unknown. Moving to '{IRRELEVANT_OR_UNKNOWN_FOLDER}'.")
                    irrelevant_folder_id = self._get_or_create_path(self.root_id, [IRRELEVANT_OR_UNKNOWN_FOLDER])
                    self.drive.move_file(file_id, irrelevant_folder_id)
                    summary["total_moved_to_irrelevant"] += 1
                    summary["irrelevant_files"].append(file_item)
                    continue


                if not (category and brand and model and meta_type):
                    logger.warning(f"AI could not fully classify '{original_filename}'. Moving to '{MANUAL_REVIEW_FOLDER}'.")
                    current_run_log.append(f"⚠️ AI could not fully classify '{original_filename}'. Moving to '{MANUAL_REVIEW_FOLDER}'.")
                    manual_review_folder_id = self._get_or_create_path(self.root_id, [MANUAL_REVIEW_FOLDER])
                    self.drive.move_file(file_id, manual_review_folder_id)
                    summary["total_moved_to_manual_review"] += 1
                    summary["manual_review_files"].append(file_item)
                    continue

                # Construct new path (Rule 3)
                new_path_parts = [category, brand, model]
                target_folder_id = self._get_or_create_path(self.root_id, new_path_parts)
                
                # Construct new file name: Category | Brand | Model | Meta_Type | Original_Name
                # Use suggested filename if provided and clean, otherwise construct
                if suggested_filename and suggested_filename != original_filename:
                    # Clean suggested filename to ensure it doesn't contain path separators
                    clean_suggested_filename = suggested_filename.replace("/", "_").replace("\\", "_")
                    new_filename = f"{category} | {brand} | {model} | {meta_type} | {clean_suggested_filename}"
                else:
                    new_filename = f"{category} | {brand} | {model} | {meta_type} | {original_filename}"
                
                # Rename and Move (Rule 3)
                self.drive.rename_file(file_id, new_filename)
                self.drive.move_file(file_id, target_folder_id)
                
                logger.info(f"Successfully sorted and renamed '{original_filename}' to '{new_filename}' in path: {'/'.join(new_path_parts)}")
                current_run_log.append(f"✅ Sorted '{original_filename}' to '{'/'.join(new_path_parts)}' as '{new_filename}'")
                
                summary["total_successfully_sorted"] += 1
                summary["category_counts"][category] += 1
                summary["brand_counts"][brand] += 1
                summary["type_counts"][meta_type] += 1

            except Exception as e:
                logger.error(f"Error processing file {original_filename} (ID: {file_id}): {e}", exc_info=True)
                current_run_log.append(f"❌ Failed to process '{original_filename}': {e}")
                summary["failed_files"].append(file_item)
                # Move to an error folder if processing failed
                try:
                    error_folder_id = self._get_or_create_path(self.root_id, ["_AI_ERROR"])
                    self.drive.move_file(file_id, error_folder_id)
                    current_run_log.append(f"ℹ️ Moved failed file '{original_filename}' to '_AI_ERROR' folder.")
                except Exception as move_e:
                    logger.error(f"Failed to move problematic file {original_filename} to _AI_ERROR: {move_e}", exc_info=True)
                    current_run_log.append(f"❌ CRITICAL: Failed to move problematic file '{original_filename}' to '_AI_ERROR'.")

        my_bar.progress(100, text="Ολοκληρώθηκε!")
        logger.info("AI Sorter finished.")
        return summary, current_run_log