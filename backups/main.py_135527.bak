import streamlit as st
import logging
from core.language_pack import get_text
from core.auth_manager import AuthManager
from core.db_connector import DatabaseConnector # Για init_local_db
from core.spy_logger import setup_spy, sync_current_spy_logs_to_drive # Για διαχείριση logs
from version import VERSION

# Εισαγωγή των UI Modules
from modules import ui_dashboard
from modules import ui_chat
from modules import ui_diagnostics
from modules import ui_search
from modules import ui_clients
from modules import ui_organizer
from modules import ui_tools
from modules import ui_admin_panel
from modules import ui_tech_specs
from modules import ui_help_user
from modules import ui_licensing

# Ρύθμιση Logger για το main.py
logger = logging.getLogger("MainApp")

def init_session():
    """
    Αρχικοποιεί τις μεταβλητές του session state και τον Spy Logger.
    Κανόνας 6: Έλεγχος initialization keys.
    """
    if 'lang' not in st.session_state:
        st.session_state.lang = 'gr'
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'messages' not in st.session_state:
        st.session_state.messages = [] # Για ιστορικό συνομιλίας
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard" # Προεπιλεγμένη σελίδα μετά τη σύνδεση

    # Αρχικοποίηση της τοπικής βάσης δεδομένων (SQLite) αν δεν έχει γίνει ήδη
    if 'db_initialized' not in st.session_state:
        try: # Κανόνας 4: Error Handling
            if DatabaseConnector.init_local_db():
                st.session_state.db_initialized = True
                logger.info(get_text('db_init_success', st.session_state.lang))
            else:
                st.session_state.db_initialized = False
                logger.error(get_text('db_init_fail', st.session_state.lang))
                st.error(get_text('db_init_fail', st.session_state.lang))
        except Exception as e:
            st.session_state.db_initialized = False
            logger.critical(f"Critical error during DB initialization: {e}", exc_info=True)
            st.error(f"{get_text('db_init_fail', st.session_state.lang)}: {e}")


    # Ρύθμιση του Spy Logger
    setup_spy()

def main():
    init_session() # Αρχικοποίηση session state και logger

    lang = st.session_state.lang # Τρέχουσα γλώσσα
    
    # Custom CSS για στοιχεία UI
    st.markdown("""
        <style>
            .stSidebar {
                background-color: #f0f2f6; /* Ανοιχτό γκρι για sidebar */
            }
            .stButton>button {
                width: 100%;
            }
            .chat-input {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background-color: white;
                padding: 1rem;
                border-top: 1px solid #ddd;
                z-index: 999;
            }
            /* Στυλ για το λογότυπο */
            .logo-img {
                display: block;
                margin-left: auto;
                margin-right: auto;
                width: 80%; /* Προσαρμόστε ανάλογα */
                max-width: 150px;
                margin-bottom: 20px;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- ΟΘΟΝΗ ΣΥΝΔΕΣΗΣ ---
    if not st.session_state.user_info:
        st.header(f"🔐 {get_text('app_title', lang)}")
        
        c_lang, _ = st.columns([1,5])
        with c_lang:
            sel = st.selectbox("🌐 Language", ["Ελληνικά", "English"], index=0 if lang=='gr' else 1, key="login_lang_selector")
            if (st.session_state.lang == 'gr' and sel == "English") or \
               (st.session_state.lang == 'en' and sel == "Ελληνικά"):
                st.session_state.lang = 'gr' if sel == "Ελληνικά" else 'en'
                st.rerun()

        # Καρτέλες Σύνδεσης/Εγγραφής
        login_tab, register_tab = st.tabs([get_text('login_tab', lang), get_text('register_tab', lang)])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input(get_text('email_lbl', lang), key="login_email")
                password = st.text_input(get_text('pass_lbl', lang), type="password", key="login_password")
                submitted = st.form_submit_button(get_text('btn_login', lang))

                if submitted:
                    user, msg = AuthManager.verify_login(email, password)
                    if msg == "OK":
                        st.session_state.user_info = user
                        logger.info(f"User {user['email']} logged in successfully.")
                        st.success(f"{get_text('dash_welcome', lang)}, {user['name']}!")
                        st.rerun()
                    else:
                        st.error(msg)
                        logger.warning(f"Login failed for {email}: {msg}")

        with register_tab:
            with st.form("register_form"):
                reg_email = st.text_input(get_text('email_lbl', lang), key="register_email")
                reg_name = st.text_input(get_text('name_lbl', lang), key="register_name")
                reg_password = st.text_input(get_text('pass_lbl', lang), type="password", key="register_password")
                submitted = st.form_submit_button(get_text('btn_register', lang))

                if submitted:
                    # Κανόνας 4: Error Handling
                    try:
                        if AuthManager.register_new_user(reg_email, reg_name, reg_password):
                            st.success(get_text('reg_success', lang))
                            logger.info(f"New user '{reg_email}' registered successfully (pending approval).")
                            # Optionally, redirect to login tab or show a message.
                        else:
                            st.error(get_text('reg_fail', lang))
                            logger.warning(f"Registration failed for '{reg_email}'.")
                    except Exception as e:
                        st.error(f"{get_text('reg_fail', lang)}: {e}")
                        logger.error(f"Error during registration for '{reg_email}': {e}", exc_info=True)
        return # Σταματάμε εδώ αν δεν έχει γίνει σύνδεση

    # --- ΚΥΡΙΩΣ ΕΦΑΡΜΟΓΗ (ΜΕΤΑ ΤΗ ΣΥΝΔΕΣΗ) ---
    user = st.session_state.user_info

    # Sidebar Navigation
    st.sidebar.image("assets/logo.png", use_column_width=True, caption=get_text('app_title', lang))
    st.sidebar.markdown(f"**{get_text('dash_welcome', lang)}, {user['name']}!**")
    st.sidebar.markdown(f"*{user['role'].upper()}*")
    st.sidebar.divider()
    
    st.sidebar.header(get_text('menu_header', lang))
    
    # Menus based on user role
    menu_options = [
        get_text('menu_dashboard', lang),
        get_text('menu_chat', lang),
        get_text('menu_library', lang),
        get_text('menu_diagnostics', lang), # NEW
        get_text('menu_clients', lang),
        get_text('menu_organizer', lang),
        get_text('menu_tools', lang),
        get_text('menu_licensing', lang), # NEW
        get_text('menu_help_user', lang), # NEW
        get_text('menu_tech_specs', lang), # NEW
    ]
    
    if user['role'] == 'admin':
        menu_options.append(get_text('menu_admin', lang))

    # Sidebar selection for page navigation
    # Rule 6: Ensure 'page' is initialized and keys are unique for `selectbox`
    current_page_index = menu_options.index(st.session_state.page) if st.session_state.page in menu_options else 0
    selected_page = st.sidebar.selectbox(" ", menu_options, index=current_page_index, key="main_menu_selector", label_visibility="collapsed")

    if selected_page:
        st.session_state.page = selected_page
        
    st.sidebar.divider()

    if st.sidebar.button(get_text('logout', lang), use_container_width=True):
        sync_current_spy_logs_to_drive() # Συγχρονισμός logs πριν την αποσύνδεση
        st.session_state.user_info = None
        st.session_state.messages = []
        st.session_state.page = "Dashboard" # Επαναφορά στην αρχική σελίδα μετά την αποσύνδεση
        # Clear other specific session state variables if needed for security/fresh start
        for key in ['library_cache', 'chat_session_service', 'diagnostics_service_instance', 'sorter_stop_flag', 'sorter_running', 'sorter_failed_files', 'sorter_manual_review_files', 'sorter_irrelevant_files', 'sorter_duplicate_files', 'sorter_progress_data', 'sorter_run_log', 'sorter_summary', 'org_browse_level', 'org_current_folder_id', 'org_folder_history', 'admin_users_data', 'force_full_resort', 'library_search_input_text']:
            if key in st.session_state:
                del st.session_state[key]
        logger.info(f"User {user['email']} logged out.")
        st.rerun()

    # Render selected page
    try: # Κανόνας 4: Error Handling
        if st.session_state.page == get_text('menu_dashboard', lang):
            ui_dashboard.render(user)
        elif st.session_state.page == get_text('menu_chat', lang):
            ui_chat.render(user)
        elif st.session_state.page == get_text('menu_library', lang):
            ui_search.render(user)
        elif st.session_state.page == get_text('menu_diagnostics', lang): # NEW
            ui_diagnostics.render(user)
        elif st.session_state.page == get_text('menu_clients', lang):
            ui_clients.render(user)
        elif st.session_state.page == get_text('menu_organizer', lang):
            ui_organizer.render(user)
        elif st.session_state.page == get_text('menu_tools', lang):
            ui_tools.render(user)
        elif st.session_state.page == get_text('menu_admin', lang):
            ui_admin_panel.render(user)
        elif st.session_state.page == get_text('menu_licensing', lang): # NEW
            ui_licensing.render(user)
        elif st.session_state.page == get_text('menu_tech_specs', lang): # NEW
            ui_tech_specs.render(user)
        elif st.session_state.page == get_text('menu_help_user', lang): # NEW
            ui_help_user.render(user)
        else: # Fallback
            ui_dashboard.render(user)
    except Exception as e:
        logger.error(f"Error rendering page '{st.session_state.page}': {e}", exc_info=True)
        st.error(f"{get_text('general_ui_error', lang).format(error=e)}")

if __name__ == "__main__":
    main()