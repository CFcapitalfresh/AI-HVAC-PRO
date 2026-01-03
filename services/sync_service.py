"""
SERVICE: SYNC SERVICE (FINAL SELF-CONTAINED FIX)
------------------------------------------------
1. Path Aware: Captures 'Brand | Model' properly.
2. Direct API Calls: Bypasses missing methods in DriveManager.
3. Update Only: Updates existing 'drive_index.json' to avoid Quota limits.
4. METADATA EXTRACTION: Extracts Brand, Model, and Meta_Type from file paths.
5. IMPROVEMENT: Scans ALL folders to build a complete index for browsing.
"""
import streamlit as st
import json
import os
from core.drive_manager import DriveManager # Rule 7
from core.config_loader import ConfigLoader
import logging
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from services.sorter_logic import IGNORED_FOLDERS_TOP_LEVEL # Rule 3: Use shared ignored folders list
from typing import List, Dict, Any, Optional # For type hinting

logger = logging.getLogger("Sync") # Rule 4: Logging
INDEX_FILENAME = "drive_index.json"

class SyncService:
    def __init__(self):
        self.drive = DriveManager() # Rule 7
        self.root_id = self.drive.root_id # Use DriveManager's cached root_id (Rule 7)

    def scan_library(self):
        """Σαρώνει και ΕΝΗΜΕΡΩΝΕΙ (Update) το αρχείο στο Cloud."""
        logger.info("🔄 Starting Sync (Direct Mode)...") # Rule 4
        
        if not self.root_id: 
            logger.error("❌ Root ID missing in SyncService. Cannot proceed.") # Rule 4
            st.error("⚠️ Σφάλμα: Το ID του φακέλου Google Drive δεν βρέθηκε.") # Rule 5
            return []
        
        # Μπάρα Προόδου
        progress_text_msg = "⏳ Σάρωση & Ενημέρωση..."
        my_bar = st.progress(0, text=progress_text_msg)
        
        # 1. ΣΑΡΩΣΗ (Path Aware)
        # Call _scan_recursive to scan all files, without skipping any categorized folders
        # Pass force_full_rescan_for_sync=True to ensure all nested files are rescanned for the index.
        all_files = self._scan_recursive(
            current_folder_id=self.root_id, 
            path_prefix="", 
            my_bar=my_bar, 
            progress_text=progress_text_msg, 
            current_progress=0, 
            total_progress_steps=80, 
            force_full_rescan_for_sync=True # Important for a complete index
        )
        
        my_bar.progress(80, text=f"✅ Βρέθηκαν {len(all_files)} αρχεία. Εγγραφή στο Cloud...")
        logger.info(f"✅ Scan Complete. Found {len(all_files)} manuals.") # Rule 4

        # 2. Αποθήκευση Τοπικά (Backup)
        try: # Rule 4: Error Handling
            with open(INDEX_FILENAME, "w", encoding="utf-8") as f:
                json.dump(all_files, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Local index saved: {INDEX_FILENAME}") # Rule 4
        except Exception as e:
            logger.warning(f"Failed to save local index: {e}", exc_info=True) # Rule 4

        # 3. CLOUD UPDATE (Direct API Call - Χωρίς μεσάζοντες)
        try: # Rule 4: Error Handling
            # Απευθείας αναζήτηση μέσω του service (παρακάμπτουμε το DriveManager για την ενημέρωση του index file)
            query = f"name = '{INDEX_FILENAME}' and '{self.root_id}' in parents and trashed = false"
            results = self.drive.service.files().list(q=query, fields="files(id, name)").execute() # Rule 7: Direct service call for index update.
            found_files = results.get('files', [])
            
            if not found_files:
                logger.error("❌ CLOUD ERROR: Δεν βρέθηκε το 'drive_index.json'!") # Rule 4
                st.error("⚠️ Σφάλμα: Πρέπει να δημιουργήσετε ένα κενό αρχείο 'drive_index.json' στον κεντρικό φάκελο του Drive σας!") # Rule 5
                return all_files

            # Παίρνουμε το ID του αρχείου
            target_file_id = found_files[0]['id']
            logger.info(f"📂 Found Cloud Index ID: {target_file_id}") # Rule 4
            
            # Ετοιμάζουμε τα δεδομένα
            json_str = json.dumps(all_files, ensure_ascii=False, indent=2)
            media = MediaIoBaseUpload(io.BytesIO(json_str.encode('utf-8')), mimetype='application/json', resumable=True)

            # ΕΚΤΕΛΕΣΗ UPDATE
            self.drive.service.files().update( # Rule 7: Direct service call for index update.
                fileId=target_file_id,
                media_body=media
            ).execute()
            
            logger.info(f"☁️ Cloud Index OVERWRITTEN successfully!") # Rule 4
            my_bar.progress(100, text="✅ Ολοκληρώθηκε! Η βάση ενημερώθηκε.")
            
            # Καθαρισμός Session State Caches (Rule 6)
            if 'library_index' in st.session_state:
                del st.session_state['library_index']
            if 'library_cache' in st.session_state: # Clear cache from ui_search
                del st.session_state['library_cache']
                
            return all_files
            
        except Exception as e:
            logger.error(f"❌ Cloud Update Failed: {e}", exc_info=True) # Rule 4
            st.error(f"❌ Σφάλμα κατά την ενημέρωση Cloud: {e}") # Rule 5
            return all_files

    def _scan_recursive(self, current_folder_id: str, path_prefix: str, my_bar: Any, progress_text: str, current_progress: int, total_progress_steps: int, force_full_rescan_for_sync: bool = False) -> List[Dict[str, Any]]:
        """
        Αναδρομική σάρωση φακέλων στο Google Drive.
        Τώρα εξαιρεί τους IGNORED_FOLDERS_TOP_LEVEL μόνο αν δεν είναι πλήρης επανεξέταση.
        """
        all_files_metadata = []
        try: # Rule 4: Error Handling
            # Rule 7: Use DriveManager to list files
            items = self.drive.list_files_in_folder(current_folder_id)

            total_items = len(items)
            processed_items = 0

            for item in items:
                # Update progress bar more frequently for long scans
                processed_items += 1
                new_progress = current_progress + int((processed_items / total_items) * (total_progress_steps / 100))
                my_bar.progress(min(new_progress, 99), text=f"{progress_text} {path_prefix}/{item['name']}")

                full_name_path = f"{path_prefix}/{item['name']}" if path_prefix else item['name']
                original_filename = item['name'] # Keep original filename

                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Check if this is a top-level ignored folder (only if not force_full_rescan_for_sync)
                    if not path_prefix and item['name'] in IGNORED_FOLDERS_TOP_LEVEL and not force_full_rescan_for_sync:
                        logger.info(f"Skipping ignored top-level folder: {full_name_path}") # Rule 4
                        continue # Skip this folder and its contents
                    
                    # Recursively scan subfolder
                    all_files_metadata.extend(
                        self._scan_recursive(
                            item['id'], 
                            full_name_path, 
                            my_bar, 
                            progress_text, 
                            current_progress, 
                            total_progress_steps # Pass same total steps for sub-scan
                        )
                    )
                elif item['mimeType'] == 'application/pdf':
                    # Extract metadata from the full path name
                    metadata = self._extract_metadata_from_name(full_name_path, original_filename)
                    
                    file_entry = {
                        "file_id": item['id'],
                        "name": full_name_path, # The full path in Drive
                        "link": item['webViewLink'],
                        "mime": item['mimeType'],
                        **metadata # Unpack the extracted metadata
                    }
                    all_files_metadata.append(file_entry)
                    logger.debug(f"Indexed file: {full_name_path}") # Rule 4
            return all_files_metadata
        except Exception as e:
            logger.error(f"Error during recursive scan in folder {current_folder_id} (path: {path_prefix}): {e}", exc_info=True) # Rule 4
            return all_files_metadata # Return what was found so far

    def _extract_metadata_from_name(self, full_path_name: str, original_filename: str) -> Dict[str, str]:
        """
        Εξάγει μεταδεδομένα (category, brand, model, meta_type, error_codes) από ένα όνομα αρχείου
        που έχει μορφοποιηθεί από τον Sorter (π.χ., "Category | Brand | Model | Type | Filename.pdf")
        ή από την original_filename αν δεν υπάρχει πλήρης διαδρομή.
        """
        metadata = {
            'category': 'Unknown', 
            'brand': 'Unknown',
            'model': 'General_Model',
            'meta_type': 'DOC',
            'error_codes': '', 
            'original_name': original_filename 
        }

        # Προσπαθούμε να διασπάσουμε με βάση το '|' από την πλήρη διαδρομή
        parts = [p.strip() for p in full_path_name.split('|')]
        
        # Αν η πλήρης διαδρομή είναι μορφοποιημένη (π.χ., Category | Brand | Model | Type | ...)
        if len(parts) >= 5: # Category | Brand | Model | Type | Original filename...
            metadata['category'] = parts[0]
            metadata['brand'] = parts[1]
            metadata['model'] = parts[2]
            metadata['meta_type'] = parts[3]
            # Error codes might be embedded in original_name or require more advanced regex/AI
            # For now, we'll try to extract simple error codes if they appear in the original filename
            error_match = re.search(r'(E\d+)', original_filename, re.IGNORECASE)
            if error_match:
                metadata['error_codes'] = error_match.group(1).upper()
        elif len(parts) >= 4: # Brand | Model | Type | Filename.pdf (assume category is first folder)
            # This logic needs to be careful, it's better if Sorter always provides full path
            # But as fallback, derive from parts
            metadata['brand'] = parts[0] if parts[0] != 'User_Uploads' else 'Unknown' # Prevent "User_Uploads" as brand
            metadata['model'] = parts[1]
            metadata['meta_type'] = parts[2]
            error_match = re.search(r'(E\d+)', original_filename, re.IGNORECASE)
            if error_match: metadata['error_codes'] = error_match.group(1).upper()
        else:
            # Fallback to extract from original filename, assuming pattern "BRAND_MODEL_TYPE.pdf" or similar
            # This is less reliable but better than nothing
            name_no_ext = os.path.splitext(original_filename)[0]
            filename_parts = name_no_ext.replace('-', '_').split('_')
            if len(filename_parts) >= 2:
                metadata['brand'] = filename_parts[0].upper()
                metadata['model'] = filename_parts[1]
            
            # Simple heuristic for meta_type based on keywords in filename
            if any(kw in original_filename.lower() for kw in ["user manual", "χρήστη"]):
                metadata['meta_type'] = "User_Manual"
            elif any(kw in original_filename.lower() for kw in ["service manual", "τεχνικό"]):
                metadata['meta_type'] = "Service_Manual"
            elif any(kw in original_filename.lower() for kw in ["installation", "εγκατάσταση"]):
                metadata['meta_type'] = "Installation_Manual"
            elif any(kw in original_filename.lower() for kw in ["error", "βλάβη"]):
                metadata['meta_type'] = "Error_Codes"

            error_match = re.search(r'(E\d+)', original_filename, re.IGNORECASE)
            if error_match:
                metadata['error_codes'] = error_match.group(1).upper()

        # Clean up values (e.g., replace underscores with spaces for display, but keep for internal use)
        # We store them as they are parsed, let UI handle display formatting if needed.
        return metadata

    def load_index(self) -> List[Dict[str, Any]]:
        """
        Φορτώνει τον index από τοπικό αρχείο `drive_index.json` ή από το Google Drive.
        """
        # Rule 6: Cache in session_state to avoid repeated loads
        if 'library_index' in st.session_state:
            return st.session_state.library_index

        # 1. Προσπάθεια φόρτωσης από τοπικό αρχείο
        if os.path.exists(INDEX_FILENAME):
            try: # Rule 4: Error Handling
                with open(INDEX_FILENAME, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    st.session_state.library_index = data # Store in session state
                    logger.info(f"Loaded index from local file: {INDEX_FILENAME}") # Rule 4
                    return data
            except Exception as e:
                logger.warning(f"Error loading local index '{INDEX_FILENAME}': {e}", exc_info=True) # Rule 4
        
        # 2. Αν αποτύχει τοπικά, προσπάθησε να το κατεβάσεις από το Drive
        logger.info("Local index not found or failed to load. Attempting to download from Drive.") # Rule 4
        try: # Rule 4: Error Handling
            # Rule 7: Use DriveManager to find and download the index file
            # Assuming `drive_index.json` is in the root folder
            query = f"name = '{INDEX_FILENAME}' and '{self.root_id}' in parents and trashed = false"
            results = self.drive.service.files().list(q=query, fields="files(id)").execute() # Rule 7
            files = results.get('files', [])

            if files:
                file_id = files[0]['id']
                stream = self.drive.download_file_content(file_id) # Rule 7
                if stream:
                    data = json.load(stream)
                    st.session_state.library_index = data # Store in session state
                    logger.info("Successfully downloaded and loaded index from Google Drive.") # Rule 4
                    # Optionally, save a local copy for next time
                    try: # Rule 4
                        with open(INDEX_FILENAME, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        logger.info(f"Saved downloaded index to local file: {INDEX_FILENAME}") # Rule 4
                    except Exception as e:
                        logger.warning(f"Failed to save downloaded index locally: {e}", exc_info=True) # Rule 4
                    return data
                else:
                    logger.error(f"Failed to download content for index file ID {file_id} from Drive.") # Rule 4
            else:
                logger.warning("Index file 'drive_index.json' not found in Google Drive root.") # Rule 4

        except Exception as e:
            logger.error(f"Error downloading index from Drive: {e}", exc_info=True) # Rule 4

        # Αν όλα αποτύχουν, επέστρεψε κενή λίστα
        st.session_state.library_index = [] # Store empty list in session state
        return []