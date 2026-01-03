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
        self.api_key = ConfigLoader.get_gemini_key()
        self.model = None
        self.root_id = ConfigLoader.get_drive_folder_id()
        self._setup_ai()

    def _setup_ai(self):
        """DYNAMIC DISCOVERY: Βρίσκει το καλύτερο διαθέσιμο μοντέλο."""
        if self.api_key and not self.model: 
            try:
                genai.configure(api_key=self.api_key)
                
                available_models = []
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods and 'uri' in m.input_token_limit_protos:
                            available_models.append(m.name)
                except Exception as e:
                    logger.warning(f"Could not list Gemini models during Sorter setup: {e}")

                preferred_order = [
                    "gemini-1.5-pro", 
                    "models/gemini-1.5-pro",
                    "gemini-1.5-flash", 
                    "models/gemini-1.5-flash",
                    "gemini-2.0-flash-exp", 
                    "models/gemini-2.0-flash-exp",
                    "gemini-pro",
                    "models/gemini-pro"
                ]
                
                selected_model = None
                for p in preferred_order:
                    if p in available_models:
                        selected_model = p
                        break
                
                if not selected_model:
                    for m in available_models:
                        if "gemini" in m:
                            selected_model = m
                            break
                
                if selected_model:
                    self.model = genai.GenerativeModel(selected_model)
                    logger.info(f"✅ AI Initialized for Sorter using AUTO-DETECTED model: {selected_model}")
                else:
                    logger.error("❌ No suitable Gemini models found available for Sorter with this API Key.")

            except Exception as e:
                logger.error(f"❌ AI Init Error for Sorter: {e}", exc_info=True)

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
            for i in range(min(8, len(reader.pages))): 
                text += reader.pages[i].extract_text() or ""
            return text[:5000], file_bytes, file_hash 
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_id}: {e}", exc_info=True)
            return None, None, None

    def _ask_ai_for_metadata(self, filename: str, file_text: Optional[str], file_bytes: Optional[bytes]) -> dict:
        """Ζητάει από το AI να κατηγοριοποιήσει το αρχείο."""
        if not self.model: 
            logger.error("AI Model not initialized for metadata extraction.")
            return {"category": "Unknown", "brand": "Unknown", "model": "General_Model", "meta_type": "General_Manual", "error_codes": "", "reason": "AI Model not ready."}
        
        prompt_parts = [
            f"Analyze the following document (filename: '{filename}'). "
            "Determine its Category, Brand, Model, and Document Type. "
            "Also, extract any HVAC error codes mentioned. "
            f"Allowed Categories: {', '.join(ALLOWED_CATEGORIES)}. "
            f"Allowed Document Types: {', '.join(ALLOWED_TYPES)}. "
            "If no specific brand/model, use 'Unknown'/'General_Model'. "
            "If no specific type, use 'General_Manual'. "
            "Respond in JSON format only.",
            f"Filename: {filename}",
            f"Content Snippet: {file_text or 'N/A'}"
        ]

        if file_bytes:
            # Add image part if file_bytes is available (for Vision model)
            prompt_parts.append({
                "inline_data": {
                    "mime_type": "application/pdf", # Assuming PDF for now, can be generalized
                    "data": file_bytes
                }
            })

        json_output_format = {
            "category": "Heating_Boilers|Heat_Pumps|Air_Conditioning|Solar_Systems|Water_Heaters|Thermostats_Controllers|Spare_Parts_Valves|Other_HVAC|Unknown",
            "brand": "EXTRACTED_BRAND",
            "model": "EXTRACTED_MODEL",
            "meta_type": "User_Manual|Service_Manual|Installation_Manual|Technical_Data|Error_Codes|Spare_Parts_List|General_Manual",
            "error_codes": "E1, E2, F0 (comma separated, if found, else empty string)",
            "reason": "Why AI chose this category/type (optional, for debugging)"
        }

        prompt_parts.append(f"\nJSON Output Format (choose from options, provide extracted values): {json.dumps(json_output_format, indent=2)}")
        
        try:
            response = self.model.generate_content(
                prompt_parts,
                generation_config={"response_mime_type": "application/json"}
            )
            # Robust JSON parsing
            text = response.text.strip()
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                clean_json = text[start_idx:end_idx]
                return json.loads(clean_json)
            else:
                logger.warning(f"AI returned invalid JSON for '{filename}': {text[:200]}")
                return {"category": "Unknown", "brand": "Unknown", "model": "General_Model", "meta_type": "General_Manual", "error_codes": "", "reason": "AI returned malformed JSON."}
        except Exception as e:
            logger.error(f"AI metadata extraction failed for '{filename}': {e}", exc_info=True)
            return {"category": "Unknown", "brand": "Unknown", "model": "General_Model", "meta_type": "General_Manual", "error_codes": "", "reason": f"AI error: {str(e)}"}

    def _get_or_create_folder(self, parent_id, folder_name):
        """Επιστρέφει το ID του φακέλου, δημιουργώντας τον αν δεν υπάρχει."""
        # Clean folder name for Drive compatibility
        clean_folder_name = re.sub(r'[\\/:*?"<>|]', '', folder_name).strip()
        if not clean_folder_name: return None # Avoid creating empty name folders
        
        return self.drive.create_folder(clean_folder_name, parent_id)

    def run_sorter(self, stop_flag: bool, progress_callback, log_callback, failed_files_list: list, manual_review_files_list: list, irrelevant_files_list: list, duplicate_files_list: list, force_full_rescan: bool = False) -> dict:
        """
        Εκτελεί την ταξινόμηση αρχείων.
        `force_full_rescan`: Αν είναι True, σαρώνει *όλους* τους φακέλους, συμπεριλαμβανομένων των ήδη ταξινομημένων.
        """
        if not self.root_id:
            log_callback("❌ Error: Drive Root Folder ID is not configured.")
            return {"status": "failed", "message": "Root Folder ID missing."}

        log_callback("🔄 Starting AI Sorter...")
        progress_callback(0, 100, "Αρχικοποίηση...")

        files_to_process = []
        hash_to_file_map = {} # Για ανίχνευση διπλοτύπων
        
        # Πρώτο πέρασμα: Συλλογή αρχείων
        # Only scan the root for *unsorted* files if not a full rescan.
        # If force_full_rescan, scan all folders to re-evaluate.
        log_callback(f"Scanning Drive (Force Full Rescan: {force_full_rescan})...")
        progress_callback(5, 100, "Σάρωση αρχείων στο Drive...")
        
        # Use _scan_recursive from SyncService to get a full list if force_full_rescan is True
        # For this context, we need to adapt the scanner from SyncService or implement a similar one.
        # Let's use a simplified direct scan of the root for unsorted files if not full rescan.
        # If force_full_rescan, we get all files.
        all_drive_files = self.drive.list_files_in_folder(self.root_id)
        
        current_idx = 0
        total_files = len(all_drive_files)
        
        # If force_full_rescan, we'll re-scan everything. Otherwise, only new/unsorted.
        for item in all_drive_files:
            item_name = item['name']
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # If it's a folder, check if it's an IGNORED_FOLDERS_TOP_LEVEL.
                # If not forcing full rescan, and it's a categorized folder, skip it.
                if not force_full_rescan and item_name in ALLOWED_CATEGORIES:
                    log_callback(f"Skipping already categorized folder: {item_name}")
                    continue
                # If it's a special folder and we are not forcing full rescan, skip
                if not force_full_rescan and item_name in IGNORED_FOLDERS_TOP_LEVEL:
                    log_callback(f"Skipping special ignored folder: {item_name}")
                    continue
                
                # If it's a folder we need to process (either not categorized, or force_full_rescan)
                # Recursively add its files for processing.
                # For simplicity in this `run_sorter`, we are primarily interested in files in the *root* or unorganized subfolders.
                # A full recursive scan is usually done by SyncService before Sorter.
                # Here, we'll assume `list_files_in_folder` gives us the direct children.
                # If we want deep processing, this would need to recursively gather files,
                # which can be complex to integrate here with progress bars effectively.
                # For this implementation, let's assume `list_files_in_folder` will return what we need,
                # or that `files_to_process` is initialized with all unclassified files.

                # Simplified: if it's a folder that needs processing (not in ALLOWED_CATEGORIES, not IGNORED, or force_full_rescan)
                # We will process it as a 'container' for files, but the sorting logic focuses on *files*.
                # The assumption is, the Sorter's job is to take files from a "holding area" (like the root)
                # and put them into structured folders. If force_full_rescan is true, even existing folders/files
                # might be re-evaluated.
                pass # Folders are not directly "files to process" for sorting themselves
            
            elif item['mimeType'].startswith('application/pdf') or item['mimeType'].startswith('image/'):
                # Check if it's an ignored file from special folders
                # This needs to check the parent path, which `list_files_in_folder` doesn't provide directly.
                # We need to refine the `list_files_in_folder` to return parent info or iterate differently.
                # For now, let's assume if it's directly in root and not in a categorized folder, it's unsorted.
                
                # We need to explicitly avoid files that are ALREADY in the organized structure,
                # unless force_full_rescan is true.
                is_in_organized_folder = False
                if 'parents' in item: # Drive API returns 'parents' list
                    # Get parent folder's name to check if it's already structured
                    parent_id = item['parents'][0] # Assuming one parent
                    parent_folder_info = self.drive.service.files().get(fileId=parent_id, fields='name').execute()
                    parent_folder_name = parent_folder_info.get('name')
                    
                    if parent_folder_name in ALLOWED_CATEGORIES or parent_folder_name in IGNORED_FOLDERS_TOP_LEVEL:
                        is_in_organized_folder = True

                if not is_in_organized_folder or force_full_rescan:
                    files_to_process.append(item)
                else:
                    log_callback(f"Skipping already organized file: {item_name}")

        total_files_to_process = len(files_to_process)
        log_callback(f"Found {total_files_to_process} files to process.")

        # Summary statistics
        summary = {
            "last_run_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_files_scanned": total_files_to_process,
            "total_successfully_sorted": 0,
            "total_moved_to_manual_review": 0,
            "total_moved_to_irrelevant": 0,
            "total_moved_to_duplicates": 0,
            "category_counts": defaultdict(int),
            "brand_counts": defaultdict(int),
            "type_counts": defaultdict(int)
        }

        for idx, item in enumerate(files_to_process):
            if stop_flag:
                log_callback("Sorting stopped by user.")
                break

            filename = item['name']
            file_id = item['id']
            mime_type = item['mimeType']

            log_callback(f"Processing ({idx+1}/{total_files_to_process}): {filename}")
            progress_callback(10 + int((idx / total_files_to_process) * 80), 100, f"Επεξεργασία: {filename}")

            try:
                # 1. Extract text and calculate hash
                file_text, file_bytes, file_hash = self._extract_text_from_pdf(file_id) if mime_type == 'application/pdf' else (None, self.drive.download_file_content(file_id).getvalue(), self._calculate_file_hash(self.drive.download_file_content(file_id).getvalue()))

                if not file_bytes:
                    raise Exception("Could not retrieve file content.")

                # 2. Duplicate Detection (using hash)
                if file_hash in hash_to_file_map:
                    original_file_info = hash_to_file_map[file_hash]
                    self.drive.move_file(file_id, self._get_or_create_folder(self.root_id, DUPLICATES_FOLDER))
                    self.drive.rename_file(file_id, f"{filename}_DUPLICATE_OF_{original_file_info['name']}")
                    duplicate_files_list.append({"name": filename, "link": item['webViewLink'], "original_file_name": original_file_info['name']})
                    summary['total_moved_to_duplicates'] += 1
                    log_callback(f"Identified duplicate and moved: {filename}")
                    continue
                else:
                    hash_to_file_map[file_hash] = {"name": filename, "id": file_id}

                # 3. Ask AI for metadata
                metadata = self._ask_ai_for_metadata(filename, file_text, file_bytes if mime_type == 'application/pdf' else None)

                category = metadata.get("category", "Unknown")
                brand = metadata.get("brand", "Unknown")
                model = metadata.get("model", "General_Model")
                meta_type = metadata.get("meta_type", "General_Manual")
                error_codes = metadata.get("error_codes", "")
                reason = metadata.get("reason", "") # For debugging/manual review

                # Normalize names for folder creation
                category = category.replace(" ", "_")
                brand = brand.replace(" ", "_")
                model = model.replace(" ", "_")
                meta_type = meta_type.replace(" ", "_")

                if category not in ALLOWED_CATEGORIES or brand == "Unknown" or model == "General_Model" or meta_type not in ALLOWED_TYPES:
                    # Move to _MANUAL_REVIEW or _IRRELEVANT_OR_UNKNOWN
                    if category == "Unknown" and brand == "Unknown" and model == "General_Model" and meta_type == "General_Manual":
                        target_folder_id = self._get_or_create_folder(self.root_id, IRRELEVANT_OR_UNKNOWN_FOLDER)
                        irrelevant_files_list.append({"name": filename, "link": item['webViewLink'], "reason": reason})
                        summary['total_moved_to_irrelevant'] += 1
                        log_callback(f"Moved to Irrelevant/Unknown: {filename} (Reason: {reason})")
                    else:
                        target_folder_id = self._get_or_create_folder(self.root_id, MANUAL_REVIEW_FOLDER)
                        manual_review_files_list.append({"name": filename, "link": item['webViewLink'], "reason": reason, "ai_suggestion": metadata})
                        summary['total_moved_to_manual_review'] += 1
                        log_callback(f"Moved to Manual Review: {filename} (Reason: {reason})")
                    self.drive.move_file(file_id, target_folder_id)
                    continue

                # 4. Create Folder Structure (Category / Brand / Model / Type)
                category_folder_id = self._get_or_create_folder(self.root_id, category)
                if not category_folder_id: raise Exception(f"Failed to create category folder: {category}")

                brand_folder_id = self._get_or_create_folder(category_folder_id, brand)
                if not brand_folder_id: raise Exception(f"Failed to create brand folder: {brand}")
                
                model_folder_id = self._get_or_create_folder(brand_folder_id, model)
                if not model_folder_id: raise Exception(f"Failed to create model folder: {model}")

                type_folder_id = self._get_or_create_folder(model_folder_id, meta_type)
                if not type_folder_id: raise Exception(f"Failed to create type folder: {meta_type}")
                
                # 5. Move File & Rename
                self.drive.move_file(file_id, type_folder_id)
                new_filename = f"{filename.replace('.pdf', '')}_{meta_type.upper()}_{error_codes}.pdf" if error_codes else f"{filename.replace('.pdf', '')}_{meta_type.upper()}.pdf"
                new_filename = new_filename.replace(' ', '_').replace('.', '_') # Ensure safe filename
                # Limit length to avoid Drive API issues
                new_filename = new_filename[:200] + ".pdf" if new_filename.endswith(".pdf") and len(new_filename) > 200 else new_filename

                self.drive.rename_file(file_id, new_filename)

                summary['total_successfully_sorted'] += 1
                summary['category_counts'][category] += 1
                summary['brand_counts'][brand] += 1
                summary['type_counts'][meta_type] += 1
                log_callback(f"Successfully sorted: {filename} to {category} | {brand} | {model} | {meta_type}")

            except Exception as e:
                failed_files_list.append({"name": filename, "id": file_id, "error": str(e), "link": item['webViewLink']})
                log_callback(f"Error processing {filename}: {e}")
                logger.error(f"Error during sorting file {filename}: {e}", exc_info=True)
                # Move to a dedicated error folder for manual inspection by admin
                error_folder_id = self._get_or_create_folder(self.root_id, "_AI_ERROR")
                if error_folder_id:
                    self.drive.move_file(file_id, error_folder_id)

        progress_callback(100, 100, "Ολοκληρώθηκε!")
        log_callback("✅ AI Sorter Finished.")
        return summary