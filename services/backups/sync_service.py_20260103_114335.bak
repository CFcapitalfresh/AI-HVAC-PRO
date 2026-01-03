"""
SERVICE: SYNC SERVICE (FINAL SELF-CONTAINED FIX)
------------------------------------------------
1. Path Aware: Captures 'Brand | Model' properly.
2. Direct API Calls: Bypasses missing methods in DriveManager.
3. Update Only: Updates existing 'drive_index.json' to avoid Quota limits.
4. METADATA EXTRACTION: Extracts Brand, Model, and Meta_Type from file paths.
5. IMPROVEMENT: Scans ALL folders to build a complete index for browsing.
6. NEW: `force_full_rescan_for_sync` to explicitly rescan ignored folders.
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
        # Call _scan_recursive to scan all files, with force_full_rescan_for_sync=True
        # to ensure all folders (even those normally ignored by Sorter) are included in the index.
        all_files = self._scan_recursive(self.root_id, path_prefix="", my_bar=my_bar, progress_text=progress_text, current_progress=0, total_progress_steps=80, force_full_rescan_for_sync=True)
        
        my_bar.progress(80, text=f"✅ Βρέθηκαν {len(all_files)} αρχεία. Εγγραφή στο Cloud...")
        logger.info(f"✅ Scan Complete. Found {len(all_files)} manuals.")

        # 2. Αποθήκευση Τοπικά (Backup)
        try:
            with open(INDEX_FILENAME, "w", encoding="utf-8") as f:
                json.dump(all_files, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Local index saved: {INDEX_FILENAME}")
        except Exception as e:
            logger.warning(f"Failed to save local index: {e}")

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
            logger.error(f"❌ Cloud Update Failed: {e}", exc_info=True)
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
        
        # Αν η πλήρης διαδρομή είναι μορφοποιημένη
        if len(parts) >= 2:
            metadata['category'] = parts[0]
            metadata['brand'] = parts[1]
            if len(parts) >= 3:
                metadata['model'] = parts[2]
            if len(parts) >= 4:
                metadata['meta_type'] = parts[3]
            
            # Try to extract error codes if they appear in original filename
            error_code_match = re.search(r'[E|F|P|C][0-9]{1,3}', original_filename, re.IGNORECASE)
            if error_code_match:
                metadata['error_codes'] = error_code_match.group(0).upper()
            
        # Fallback for simpler filenames or those not yet sorted
        else:
            # Attempt to parse brand from the start of the original filename
            brand_match = re.match(r'([A-Za-z0-9_]+)', original_filename)
            if brand_match:
                metadata['brand'] = brand_match.group(1).replace('_', ' ').strip()
            
            # Also try to get error codes from original name if path is not formatted
            error_code_match = re.search(r'[E|F|P|C][0-9]{1,3}', original_filename, re.IGNORECASE)
            if error_code_match:
                metadata['error_codes'] = error_code_match.group(0).upper()

        return metadata

    def _scan_recursive(self, folder_id, path_prefix="", my_bar=None, progress_text="", current_progress=0, total_progress_steps=100, force_full_rescan_for_sync=False):
        """
        Σαρώνει αναδρομικά φακέλους στο Google Drive, εξάγοντας μεταδεδομένα.
        `force_full_rescan_for_sync`: Αν είναι True, δεν αγνοεί φακέλους όπως `_MANUAL_REVIEW`, `_IRRELEVANT_OR_UNKNOWN`, κλπ.
        """
        files_data = []
        try:
            items = self.drive.list_files_in_folder(folder_id)
            for i, item in enumerate(items):
                # Update progress bar
                if my_bar:
                    step_progress = (i + 1) / len(items) if len(items) > 0 else 0
                    total_progress = current_progress + (step_progress * total_progress_steps) / 100
                    my_bar.progress(min(int(total_progress), 100), text=f"{progress_text} {path_prefix}{item['name']}")

                item_name = item['name']
                
                # Check if it's a folder
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Only ignore if not forced to rescan AND the folder is in the ignored list
                    if not force_full_rescan_for_sync and item_name in IGNORED_FOLDERS_TOP_LEVEL:
                        logger.debug(f"Skipping ignored folder: {path_prefix}{item_name}")
                        continue
                    
                    # Recursive call
                    nested_files = self._scan_recursive(item['id'], path_prefix=f"{path_prefix}{item_name} | ", my_bar=my_bar, progress_text=progress_text, current_progress=total_progress, total_progress_steps=total_progress_steps, force_full_rescan_for_sync=force_full_rescan_for_sync)
                    files_data.extend(nested_files)
                else:
                    # It's a file
                    full_path_name = f"{path_prefix}{item_name}"
                    # Use original_name for better metadata extraction
                    original_name = item_name # At this stage, item_name is the original name
                    metadata = self._extract_metadata_from_name(full_path_name, original_name)
                    
                    files_data.append({
                        "file_id": item['id'],
                        "name": full_path_name, # The full path including category, brand, model
                        "link": item['webViewLink'],
                        "mime": item['mimeType'],
                        **metadata # Unpack the extracted metadata
                    })
        except Exception as e:
            logger.error(f"Error scanning folder {folder_id} ('{path_prefix}'): {e}", exc_info=True)
        
        return files_data

    @st.cache_data(ttl=3600, show_spinner="Φόρτωση ευρετηρίου Manuals από το Drive...")
    def load_index(_self): # Use _self to mark it as instance method, not class method for Streamlit cache
        """Φορτώνει το αρχείο json από το Drive ή από τον τοπικό δίσκο."""
        # logger.info("Attempting to load index from Drive.")
        try:
            # 1. Πρώτα δοκιμάζουμε να το κατεβάσουμε από το Drive
            query = f"name = '{INDEX_FILENAME}' and '{_self.root_id}' in parents and trashed = false"
            results = _self.drive.service.files().list(q=query, fields="files(id, name)").execute()
            found_files = results.get('files', [])

            if found_files:
                target_file_id = found_files[0]['id']
                file_stream = _self.drive.download_file_content(target_file_id)
                if file_stream:
                    data = json.load(file_stream)
                    logger.info(f"✅ Loaded index from Google Drive: {INDEX_FILENAME}")
                    return data
            
            logger.warning(f"'{INDEX_FILENAME}' not found in Google Drive. Attempting local load.")

        except Exception as e:
            logger.error(f"Error loading index from Google Drive: {e}", exc_info=True)
            logger.warning(f"Could not load index from Drive. Attempting local load from {INDEX_FILENAME}.")

        # 2. Fallback: Φόρτωση από τοπικό αρχείο αν δεν υπάρχει στο Drive ή απέτυχε η λήψη
        if os.path.exists(INDEX_FILENAME):
            try:
                with open(INDEX_FILENAME, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"💾 Loaded local index from: {INDEX_FILENAME}")
                    return data
            except Exception as e:
                logger.error(f"Error loading local index: {e}", exc_info=True)
        
        logger.warning("No index found locally or on Drive. Returning empty list.")
        return []