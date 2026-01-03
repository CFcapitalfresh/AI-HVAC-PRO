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