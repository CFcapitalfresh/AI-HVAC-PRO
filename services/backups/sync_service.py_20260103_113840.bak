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
from core.drive_manager import DriveManager
from core.config_loader import ConfigLoader
import logging
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from services.sorter_logic import IGNORED_FOLDERS_TOP_LEVEL # Rule 3: Use shared ignored folders list

logger = logging.getLogger("Sync")
INDEX_FILENAME = "drive_index.json"

class SyncService:
    def __init__(self):
        self.drive = DriveManager()
        self.root_id = ConfigLoader.get_drive_folder_id()

    def scan_library(self):
        """Σαρώνει και ΕΝΗΜΕΡΩΝΕΙ (Update) το αρχείο στο Cloud."""
        logger.info("🔄 Starting Sync (Direct Mode)...")
        
        if not self.root_id: 
            logger.error("❌ Root ID missing.")
            return []
        
        # Μπάρα Προόδου
        progress_text = "⏳ Σάρωση & Ενημέρωση..."
        my_bar = st.progress(0, text=progress_text)
        
        # 1. ΣΑΡΩΣΗ (Path Aware)
        # Call _scan_recursive to scan all files, without skipping any categorized folders
        # Rule 3: Pass force_full_rescan_for_sync to avoid scanning ignored folders during a regular sync,
        # but scan them if explicitly told to for a full re-index.
        all_files = self._scan_recursive(self.root_id, path_prefix="", my_bar=my_bar, progress_text=progress_text, current_progress=0, total_progress_steps=80, force_full_rescan_for_sync=True)
        
        my_bar.progress(80, text=f"✅ Βρέθηκαν {len(all_files)} αρχεία. Εγγραφή στο Cloud...")
        logger.info(f"✅ Scan Complete. Found {len(all_files)} manuals.")

        # 2. Αποθήκευση Τοπικά (Backup)
        try:
            with open(INDEX_FILENAME, "w", encoding="utf-8") as f:
                json.dump(all_files, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Local index saved: {INDEX_FILENAME}")
        except Exception as e:
            logger.warning(f"Failed to save local index: {e}", exc_info=True) # Rule 4

        # 3. CLOUD UPDATE (Direct API Call - Χωρίς μεσάζοντες)
        try:
            # Απευθείας αναζήτηση μέσω του service (παρακάμπτουμε το DriveManager)
            query = f"name = '{INDEX_FILENAME}' and '{self.root_id}' in parents and trashed = false"
            results = self.drive.service.files().list(q=query, fields="files(id, name)").execute()
            found_files = results.get('files', [])
            
            if not found_files:
                logger.error("❌ CLOUD ERROR: Δεν βρέθηκε το 'drive_index.json'!")
                st.error("⚠️ Σφάλμα: Πρέπει να δημιουργήσετε ένα κενό αρχείο 'drive_index.json' στο Drive σας!")
                return all_files

            # Παίρνουμε το ID του αρχείου
            target_file_id = found_files[0]['id']
            logger.info(f"📂 Found Cloud Index ID: {target_file_id}")
            
            # Ετοιμάζουμε τα δεδομένα
            json_str = json.dumps(all_files, ensure_ascii=False, indent=2)
            media = MediaIoBaseUpload(io.BytesIO(json_str.encode('utf-8')), mimetype='application/json', resumable=True)

            # ΕΚΤΕΛΕΣΗ UPDATE
            self.drive.service.files().update(
                fileId=target_file_id,
                media_body=media
            ).execute()
            
            logger.info(f"☁️ Cloud Index OVERWRITTEN successfully!")
            my_bar.progress(100, text="✅ Ολοκληρώθηκε! Η βάση ενημερώθηκε.")
            
            # Καθαρισμός Session
            if 'library_index' in st.session_state:
                del st.session_state['library_index']
            if 'library_cache' in st.session_state: # Clear cache from ui_search
                del st.session_state['library_cache']
                
            return all_files
            
        except Exception as e:
            logger.error(f"❌ Cloud Update Failed: {e}", exc_info=True) # Rule 4
            st.error(f"❌ Σφάλμα κατά την ενημέρωση Cloud: {e}")
            return all_files

    def _extract_metadata_from_name(self, full_path_name: str, original_filename: str) -> dict:
        """
        Εξάγει μεταδεδομένα (category, brand, model, meta_type, error_codes) από ένα όνομα αρχείου
        που έχει μορφοποιηθεί από τον Sorter (π.χ., "Category | Brand | Model | Type | Filename.pdf")
        ή από την original_filename αν δεν υπάρχει πλήρης διαδρομή.
        """
        metadata = {
            'category': 'Unknown', # NEW: Include category in metadata
            'brand': 'Unknown',
            'model': 'General_Model', # Changed from 'General Model' for consistency
            'meta_type': 'General_Manual', # Changed from 'DOC' for consistency with Sorter
            'error_codes': '', 
            'original_name': original_filename 
        }

        # Προσπαθούμε να διασπάσουμε με βάση το '|' από την πλήρη διαδρομή
        parts = [p.strip() for p in full_path_name.split('|')]
        
        if len(parts) >= 5: # Assuming format "Category | Brand | Model | Type | Filename"
            metadata['category'] = parts[0].replace(" ", "_")
            metadata['brand'] = parts[1].replace(" ", "_")
            metadata['model'] = parts[2].replace(" ", "_")
            metadata['meta_type'] = parts[3].replace(" ", "_")
            # The last part is the original filename, but error codes might be embedded.
            # For now, error_codes is still extracted by AI, but we can look for common patterns.
        elif len(parts) >= 4: # Assuming format "Category | Brand | Model | Filename" (Type might be missing)
            metadata['category'] = parts[0].replace(" ", "_")
            metadata['brand'] = parts[1].replace(" ", "_")
            metadata['model'] = parts[2].replace(" ", "_")
            # meta_type defaults, or can be inferred from filename if simple.
        
        # Simple regex for error codes in original filename
        error_match = re.search(r'[E]{1}\d+', original_filename, re.IGNORECASE)
        if error_match:
            metadata['error_codes'] = error_match.group(0).upper()

        return metadata

    def _scan_recursive(self, folder_id, path_prefix="", my_bar=None, progress_text="", current_progress=0, total_progress_steps=100, force_full_rescan_for_sync: bool = False):
        """
        Σαρώνει αναδρομικά όλους τους φακέλους στο Google Drive και συλλέγει πληροφορίες αρχείων.
        Ενημερώνει τη μπάρα προόδου.
        Args:
            folder_id (str): Το ID του φακέλου από όπου θα ξεκινήσει η σάρωση.
            path_prefix (str): Το prefix της διαδρομής για την τρέχουσα αναδρομική κλήση.
            my_bar (st.progress): Η μπάρα προόδου του Streamlit.
            progress_text (str): Το κείμενο που θα εμφανίζεται στην μπάρα προόδου.
            current_progress (int): Η τρέχουσα τιμή προόδου.
            total_progress_steps (int): Το συνολικό εύρος προόδου για αυτή τη σάρωση.
            force_full_rescan_for_sync (bool): Αν είναι True, σαρώνει και τους ειδικούς φακέλους (π.χ., _IRRELEVANT_OR_UNKNOWN).
        Returns:
            List[Dict]: Λίστα με πληροφορίες αρχείων.
        """
        all_files_info = []
        q_param = f"'{folder_id}' in parents and trashed = false"

        try:
            # Λίστα φακέλων και αρχείων
            response = self.drive.service.files().list(
                q=q_param, fields="files(id, name, mimeType, webViewLink, parents)"
            ).execute()
            items = response.get('files', [])

            # Υπολογίζουμε ένα βήμα προόδου για κάθε στοιχείο σε αυτό το επίπεδο
            # Δεν ενημερώνουμε τη μπάρα εδώ, αφήνουμε τον καλούντα να το κάνει
            
            for item in items:
                file_name = item['name']
                mime_type = item['mimeType']
                file_id = item['id']

                full_path_name = f"{path_prefix} | {file_name}" if path_prefix else file_name
                
                if mime_type == 'application/vnd.google-apps.folder':
                    # Rule 3: Do not scan ignored folders UNLESS force_full_rescan_for_sync is True (for a complete index)
                    if file_name.startswith('_') and file_name in IGNORED_FOLDERS_TOP_LEVEL and not force_full_rescan_for_sync:
                        logger.info(f"Skipping ignored folder: {full_path_name}")
                        continue
                    # Αναδρομική κλήση για υποφακέλους
                    nested_files = self._scan_recursive(
                        file_id, full_path_name, my_bar, progress_text, 
                        current_progress, total_progress_steps, force_full_rescan_for_sync
                    )
                    all_files_info.extend(nested_files)
                elif mime_type == 'application/pdf':
                    # Εξαγωγή μεταδεδομένων
                    metadata = self._extract_metadata_from_name(full_path_name, file_name)
                    all_files_info.append({
                        'file_id': file_id,
                        'name': full_path_name, # The full path name created by sorter
                        'link': item.get('webViewLink'),
                        'mime': mime_type,
                        'category': metadata['category'], # NEW METADATA FIELD
                        'brand': metadata['brand'],
                        'model': metadata['model'],
                        'meta_type': metadata['meta_type'],
                        'error_codes': metadata['error_codes'],
                        'original_name': file_name # Keep the original filename
                    })
                    # Update progress bar (Rule 3)
                    if my_bar:
                        # Increment progress by a tiny amount for each file found
                        current_progress += 1 
                        my_bar.progress(min(current_progress, total_progress_steps), text=f"{progress_text} - Scanning: {file_name}")

            return all_files_info
        except Exception as e:
            logger.error(f"Error scanning folder {folder_id} with prefix '{path_prefix}': {e}", exc_info=True) # Rule 4
            return []

    def load_index(self) -> List[Dict[str, Any]]:
        """
        Φορτώνει το 'drive_index.json' από τοπικό δίσκο ή το Google Drive.
        Επίσης, cache-άρει το αποτέλεσμα στο session state.
        """
        if 'library_index' in st.session_state and st.session_state.library_index:
            logger.info("Serving library index from session cache.")
            return st.session_state.library_index

        logger.info("Loading library index...")
        index_data = []

        # 1. Προσπάθεια φόρτωσης από τοπικό αρχείο
        if os.path.exists(INDEX_FILENAME):
            try:
                with open(INDEX_FILENAME, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
                logger.info("Local index loaded successfully.")
                st.session_state.library_index = index_data
                return index_data
            except Exception as e:
                logger.warning(f"Failed to load local index file: {e}", exc_info=True) # Rule 4

        # 2. Αν αποτύχει, προσπάθεια φόρτωσης από Google Drive
        if self.root_id:
            try:
                query = f"name = '{INDEX_FILENAME}' and '{self.root_id}' in parents and trashed = false"
                results = self.drive.service.files().list(q=query, fields="files(id, name)").execute()
                found_files = results.get('files', [])

                if found_files:
                    file_id = found_files[0]['id']
                    file_content_stream = self.drive.download_file_content(file_id)
                    if file_content_stream:
                        index_data = json.load(file_content_stream)
                        logger.info("Cloud index loaded successfully.")
                        
                        # Αποθήκευση και τοπικά για μελλοντική χρήση (Rule 4)
                        with open(INDEX_FILENAME, "w", encoding="utf-8") as f:
                            json.dump(index_data, f, ensure_ascii=False, indent=2)
                        logger.info("Cloud index saved locally.")

                        st.session_state.library_index = index_data
                        return index_data
                    else:
                        logger.error(f"Failed to download content of '{INDEX_FILENAME}' from Drive.") # Rule 4
                else:
                    logger.warning(f"'{INDEX_FILENAME}' not found in Google Drive root folder.") # Rule 4
            except Exception as e:
                logger.error(f"Failed to load index from Google Drive: {e}", exc_info=True) # Rule 4
        else:
            logger.warning("Root Drive folder ID is not configured. Cannot load index from Drive.") # Rule 4

        logger.warning("No library index could be loaded. Returning empty list.")
        st.session_state.library_index = [] # Rule 6
        return []