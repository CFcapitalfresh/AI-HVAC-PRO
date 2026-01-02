# -*- coding: utf-8 -*-
import streamlit as st
from core.auth_manager import AuthManager
from core.language_pack import get_text
# NEW: Import sync_current_spy_logs_to_drive for uploading
from core.spy_logger import setup_spy, sync_current_spy_logs_to_drive 
# NEW: Import DatabaseConnector for Drive log management methods
from core.db_connector import DatabaseConnector 
from core.licensing_manager import LicensingManager 
import logging # For main logger

# Imports Modules
from modules import ui_chat, ui_admin_panel, ui_clients, ui_dashboard, ui_organizer, ui_tools, ui_search, ui_diagnostics, ui_licensing 

logger = logging.getLogger("main") # Main logger for errors

st.set_page_config(page_title="Mastro Nek AI", page_icon="🤖", layout="wide")

def init_session():
    if 'user_info' not in st.session_state: st.session_state.user_info = None
    if 'lang' not in st.session_state: st.session_state.lang = 'gr'
    if 'messages' not in st.session_state: st.session_state.messages = [] 
    
    # NEW: Αρχικοποίηση της τοπικής βάσης SQLite για τους πίνακες Users, Clients, Logs
    # Ο πίνακας SpyLogs έχει μεταφερθεί στο Google Drive.
    if 'local_db_initialized' not in st.session_state:
        if DatabaseConnector.init_local_db():
            st.session_state.local_db_initialized = True
            logger.info("Local SQLite for Users/Clients/Logs initialized.")
        else:
            st.session_state.local_db_initialized = False
            logger.error("Failed to initialize local SQLite for Users/Clients/Logs.")
    
    # Το setup_spy τώρα διαχειρίζεται τα logs στο st.session_state και ενημερώνει ότι αποθηκεύονται στο Drive.
    setup_spy() 

def handle_logout():
    st.session_state.user_info = None
    st.session_state.messages = [] 
    st.session_state.diag_plan = None 
    # Clean up admin_users_data cache if exists
    if 'admin_users_data' in st.session_state:
        del st.session_state.admin_users_data
    # Clear any stored link for uploaded logs
    if 'last_uploaded_spy_log_link' in st.session_state:
        del st.session_state['last_uploaded_spy_log_link']
    st.rerun()

def main():
    init_session()
    lang = st.session_state.lang

    # --- SIDEBAR SPY (LIVE DEBUGGER) ---
    with st.sidebar:
        st.markdown("### 🕵️ System Spy")
        
        # Το παράθυρο που δείχνει τα logs
        with st.expander("📜 Ζωντανή Καταγραφή", expanded=True):
            if "spy_logs" in st.session_state and st.session_state.spy_logs:
                # Δείχνουμε τα logs
                for log in st.session_state.spy_logs:
                    st.markdown(log)
            else:
                st.caption("No logs yet...")
        
        # NEW: Layout for upload and clear buttons
        col_upload, col_clear = st.columns(2) 
        
        # NEW: Upload Logs to Drive button
        if col_upload.button("📤 Upload Logs to Drive", use_container_width=True):
            with st.spinner("Uploading logs to Google Drive..."):
                try:
                    drive_link = sync_current_spy_logs_to_drive()
                    if drive_link:
                        st.session_state['last_uploaded_spy_log_link'] = drive_link
                        st.success("Logs uploaded to Drive!")
                        # st.markdown(f"[View Uploaded Logs]({drive_link})") # Display link below buttons
                    else:
                        st.error("Failed to upload logs to Drive.")
                except Exception as e:
                    st.error(f"Error uploading logs: {e}")
                    logger.error(f"Error uploading spy logs from UI: {e}", exc_info=True)
            # Rerun to clear spinner and update UI with link
            st.rerun()

        # MODIFIED: "Clear All Logs" button, now also clears from Drive
        if col_clear.button("🗑️ Clear All Logs", use_container_width=True): 
            st.session_state.spy_logs = []
            if 'last_uploaded_spy_log_link' in st.session_state:
                del st.session_state['last_uploaded_spy_log_link'] # Clear cached link
            try:
                if DatabaseConnector.clear_all_spy_logs_from_drive(): # NEW: Clear from Drive
                    st.success("All logs (local session & Drive) cleared.")
                else:
                    st.warning("Local session logs cleared, but failed to clear all logs from Drive.")
            except Exception as e:
                st.error(f"Error clearing logs: {e}")
                logger.error(f"Error clearing all spy logs from UI: {e}", exc_info=True)
            st.rerun() # Force rerun to clear display

        # Display last uploaded link if available
        if 'last_uploaded_spy_log_link' in st.session_state and st.session_state.last_uploaded_spy_log_link:
            st.markdown(f"**Τελευταία Μεταφόρτωση:** [Link]({st.session_state.last_uploaded_spy_log_link})")
            
        st.divider()

    # --- LOGIN SCREEN ---
    if not st.session_state.user_info:
        st.header(f"🔐 {get_text('app_title', lang)}")
        
        c_lang, _ = st.columns([1,5])
        with c_lang:
            sel = st.selectbox("🌐 Language", ["Ελληνικά", "English"], index=0 if lang=='gr' else 1)
            st.session_state.lang = 'gr' if sel == "Ελληνικά" else 'en'
            if st.session_state.lang != lang: st.rerun()

        t1, t2 = st.tabs([get_text('login_tab', lang), get_text('register_tab', lang)])
        
        with t1:
            with st.form("login"):
                email = st.text_input(get_text('email_lbl', lang))
                pwd = st.text_input(get_text('pass_lbl', lang), type="password")
                if st.form_submit_button(get_text('btn_login', lang), use_container_width=True):
                    # Always try local first, then GSheets for login
                    user, msg = AuthManager.verify_login(email, pwd, use_local_db_for_check=True) 
                    if user:
                        st.session_state.user_info = user
                        st.rerun()
                    else: st.error(msg)
        with t2:
            with st.form("reg"):
                ne = st.text_input(get_text('email_lbl', lang))
                nn = st.text_input(get_text('name_lbl', lang))
                np = st.text_input(get_text('pass_lbl', lang), type="password")
                if st.form_submit_button(get_text('btn_register', lang), use_container_width=True):
                    if AuthManager.register_new_user(ne, nn, np): st.success(get_text('reg_success', lang))
                    else: st.error("Error")
        return 

    # --- MAIN APP ---
    user = st.session_state.user_info
    role = user.get('role', 'active')

    # ΝΕΟ: Έλεγχος άδειας χρήσης
    license_status = LicensingManager.get_license_status(user['email'], role)
    if not license_status["is_active"]:
        st.error(f"❌ {license_status['message']}")
        st.info("Παρακαλώ επικοινωνήστε με τον διαχειριστή για ενεργοποίηση.")
        
    # Sidebar Menu
    with st.sidebar:
        st.write(f"👤 **{user['name']}**")
        if not license_status["is_active"]:
             st.warning(f"⚠️ {get_text('lic_status_label', lang)}: {get_text('lic_status_pending', lang)}")
        else:
             st.success(f"✅ {get_text('lic_status_label', lang)}: {get_text('lic_status_valid', lang)}")
        st.divider()
        
        opts = {
            get_text('menu_dashboard', lang): "dash",
            get_text('menu_diagnostics', lang): "diag", 
            get_text('menu_chat', lang): "chat",
            get_text('menu_library', lang): "lib",
            get_text('menu_clients', lang): "clients",
            get_text('menu_organizer', lang): "org",
            get_text('menu_tools', lang): "tools",
            get_text('menu_licensing', lang): "licensing" 
        }
        if role == 'admin':
            opts[get_text('menu_admin', lang)] = "admin"

        # Auto-Routing Logic
        default_idx = 0
        if 'app_mode' in st.session_state:
            try:
                target = st.session_state.app_mode
                if target == 'library': target = 'lib'
                vals = list(opts.values())
                if target in vals: default_idx = vals.index(target)
            except: pass
            del st.session_state.app_mode

        selection_label = st.radio(get_text('menu_header', lang), list(opts.keys()), index=default_idx)
        selection_code = opts[selection_label]
        
        st.divider()
        if st.button(get_text('logout', lang)):
            handle_logout()

    # Routing
    if selection_code == "dash": ui_dashboard.render(user)
    elif selection_code == "chat": ui_chat.render(user)
    elif selection_code == "diag": ui_diagnostics.render(user)
    elif selection_code == "lib": ui_search.render(user)
    elif selection_code == "clients": ui_clients.render(user)
    elif selection_code == "org": ui_organizer.render(user)
    elif selection_code == "tools": ui_tools.render(user)
    elif selection_code == "licensing": ui_licensing.render(user) 
    elif selection_code == "admin": ui_admin_panel.render(user)

if __name__ == "__main__":
    main()