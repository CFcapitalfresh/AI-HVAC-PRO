"""
MODULE: Admin Dashboard
VERSION: 3.0.0 (TITANIUM)
DESCRIPTION: Κέντρο ελέγχου διαχειριστή. Περιλαμβάνει Logs, Users, Sync και Updates.
**Αυτό το module φαίνεται να είναι πλέον ΑΝΕΝΕΡΓΟ/REDUNDANT, καθώς το `main.py`
χρησιμοποιεί `modules/ui_admin_panel.py` για την κύρια λειτουργία διαχείρισης.
Εάν υπάρχουν μοναδικές λειτουργίες εδώ, θα πρέπει να μεταφερθούν στο `modules/ui_admin_panel.py`.**
"""

import streamlit as st
import subprocess
import time
import logging
from typing import Any
from core.language_pack import get_text # Rule 5

logger = logging.getLogger("Module_Admin")

def _run_git_pull() -> str:
    """Εκτελεί git pull για updates."""
    try:
        result = subprocess.run(["git", "pull"], capture_output=True, text=True, check=True) # Rule 4: Add check=True
        return result.stdout
    except subprocess.CalledProcessError as e: # Rule 4: Specific error handling
        logger.error(f"Git pull failed: {e.stderr}", exc_info=True)
        return f"Error running git pull: {e.stderr}"
    except Exception as e: # Rule 4: General error handling
        logger.error(f"Unexpected error during git pull: {e}", exc_info=True)
        return f"Error: {e}"

def render_admin_panel(data_manager: Any, smart_lib_module: Any, drive_module: Any) -> None:
    """
    Κύρια συνάρτηση Admin Panel.
    Args:
        data_manager: Το DataManager class από το main.py
        smart_lib_module: Το module smart_library.py
        drive_module: Το module drive.py
    """
    lang = st.session_state.get('lang', 'gr') # Rule 5, 6

    st.title(get_text('menu_admin', lang)) # Rule 5
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        get_text('admin_logs_tab', lang) if 'admin_logs_tab' in LANGUAGE_PACK else "📊 System Logs", # Fallback for new keys
        get_text('admin_users_tab', lang) if 'admin_users_tab' in LANGUAGE_PACK else "👥 User Management",
        get_text('admin_sync_tab', lang) if 'admin_sync_tab' in LANGUAGE_PACK else "☁️ Library Sync",
        get_text('admin_maintenance_tab', lang) if 'admin_maintenance_tab' in LANGUAGE_PACK else "🔄 Maintenance"
    ])

    # --- TAB 1: LOGS ---
    with tab1:
        st.subheader(get_text('admin_audit_logs', lang) if 'admin_audit_logs' in LANGUAGE_PACK else "Audit Logs (Security & Usage)")
        try: # Rule 4
            df_logs = data_manager.fetch_sheet_data("Logs")
            if not df_logs.empty:
                st.dataframe(df_logs.sort_values(by="timestamp", ascending=False if 'timestamp' in df_logs.columns else True), use_container_width=True)
            else:
                st.info(get_text('admin_no_logs_found', lang) if 'admin_no_logs_found' in LANGUAGE_PACK else "No logs found.")
        except Exception as e:
            st.error(f"{get_text('admin_fail_load_logs', lang).format(error=e)}" if 'admin_fail_load_logs' in LANGUAGE_PACK else f"Failed to load logs: {e}")
            logger.error(f"Failed to load logs in admin panel: {e}", exc_info=True) # Rule 4

    # --- TAB 2: USERS ---
    with tab2:
        st.subheader(get_text('admin_registered_users', lang) if 'admin_registered_users' in LANGUAGE_PACK else "Registered Users")
        try: # Rule 4
            df_users = data_manager.fetch_sheet_data("Users")
            st.dataframe(df_users, use_container_width=True)
        except Exception as e:
            st.error(f"{get_text('admin_fail_load_users', lang).format(error=e)}" if 'admin_fail_load_users' in LANGUAGE_PACK else f"Failed to load users: {e}")
            logger.error(f"Failed to load users in admin panel: {e}", exc_info=True) # Rule 4

    # --- TAB 3: SYNC ---
    with tab3:
        st.subheader(get_text('admin_google_drive_sync', lang) if 'admin_google_drive_sync' in LANGUAGE_PACK else "Google Drive Synchronization")
        st.write(get_text('admin_sync_info', lang) if 'admin_sync_info' in LANGUAGE_PACK else "Use this tool if the library appears empty or if you've added new manuals.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"{get_text('admin_current_files_memory', lang).format(count=len(st.session_state.get('library_cache', [])))}" if 'admin_current_files_memory' in LANGUAGE_PACK else f"Current Files in Memory: **{len(st.session_state.get('library_cache', []))}**")
        
        with col2:
            if st.button(get_text('admin_force_full_sync', lang) if 'admin_force_full_sync' in LANGUAGE_PACK else "🚀 FORCE FULL SYNC", type="primary"):
                if not (smart_lib_module and drive_module):
                    st.error(get_text('admin_missing_sync_modules', lang) if 'admin_missing_sync_modules' in LANGUAGE_PACK else "Missing Modules (smart_library or drive). Cannot sync.")
                else:
                    try: # Rule 4
                        # 1. Load Config (Folder ID)
                        folder_id = drive_module.load_config() # Assuming drive_module has a load_config method for root_id
                        if not folder_id:
                            st.error(get_text('admin_drive_config_missing', lang) if 'admin_drive_config_missing' in LANGUAGE_PACK else "Drive Config missing (Folder ID).")
                            logger.warning("Drive Config missing (Folder ID) during manual sync.")
                        else:
                            with st.spinner(get_text('admin_scanning_drive_spinner', lang) if 'admin_scanning_drive_spinner' in LANGUAGE_PACK else "⏳ Scanning Google Drive (This may take time)..."):
                                count = smart_lib_module.run_full_maintenance(folder_id) # Assuming this triggers the main sync logic
                                st.success(f"{get_text('admin_sync_complete', lang).format(count=count)}" if 'admin_sync_complete' in LANGUAGE_PACK else f"Sync Complete! Indexed {count} files.")
                                time.sleep(2)
                                st.rerun()
                    except Exception as e:
                        st.error(f"{get_text('admin_sync_failed', lang).format(error=e)}" if 'admin_sync_failed' in LANGUAGE_PACK else f"Sync Failed: {e}")
                        logger.error(f"Manual Sync Error: {e}", exc_info=True) # Rule 4

    # --- TAB 4: UPDATES ---
    with tab4:
        st.subheader(get_text('admin_software_updates', lang) if 'admin_software_updates' in LANGUAGE_PACK else "Software Updates")
        if st.button(get_text('admin_check_github_updates', lang) if 'admin_check_github_updates' in LANGUAGE_PACK else "Check GitHub for Updates"):
            with st.spinner(get_text('admin_pulling_repo_spinner', lang) if 'admin_pulling_repo_spinner' in LANGUAGE_PACK else "Pulling from repository..."):
                output = _run_git_pull()
                st.code(output)
                if "Already up to date" not in output:
                    st.warning(get_text('admin_new_code_pulled', lang) if 'admin_new_code_pulled' in LANGUAGE_PACK else "⚠️ New code pulled. Please restart the app.")
                else:
                    st.info(get_text('admin_up_to_date', lang) if 'admin_up_to_date' in LANGUAGE_PACK else "✅ Already up to date.")