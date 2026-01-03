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
        if DatabaseConnector.init_local_db():
            st.session_state.db_initialized = True
            logger.info(get_text('db_init_success', st.session_state.lang))
        else:
            st.session_state.db_initialized = False
            logger.error(get_text('db_init_fail', st.session_state.lang))
            st.error(get_text('db_init_fail', st.session_state.lang))

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
                    if AuthManager.register_new_user(reg_email, reg_name, reg_password):
                        st.success(get_text('reg_success', lang))
                        logger.info(f"User {reg_email} registered successfully (pending).")
                    else:
                        st.error("Registration failed. Please try again.")
                        logger.warning(f"Registration failed for {reg_email}.")
        return # ΣΗΜΑΝΤΙΚΟ: Αυτό το return διασφαλίζει ότι η υπόλοιπη εφαρμογή τρέχει μόνο αν ο χρήστης είναι συνδεδεμένος.

    # --- ΚΥΡΙΩΣ ΕΦΑΡΜΟΓΗ (μετά την επιτυχή σύνδεση) ---
    user = st.session_state.user_info
    
    # Sidebar
    with st.sidebar:
        # Λογότυπο/Τίτλος Εφαρμογής
        # Αν έχετε εικόνα λογότυπου, αποσχολιάστε και δείξτε την:
        # st.image("assets/logo.png", use_column_width=True) 
        st.markdown(f"<h1 style='text-align: center;'>{get_text('app_title', lang)}</h1>", unsafe_allow_html=True)
        st.caption(f"v{VERSION} | Συνδεδεμένος ως: **{user['name']}** ({user['role']})")
        st.divider()

        st.subheader(get_text('menu_header', lang))
        menu_options = {
            get_text('menu_dashboard', lang): "Dashboard",
            get_text('menu_chat', lang): "AI Chat",
            get_text('menu_library', lang): "Manuals Library",
            get_text('menu_clients', lang): "Clients",
            get_text('menu_organizer', lang): "AI Organizer",
            get_text('menu_tools', lang): "Tools",
            get_text('menu_diagnostics', lang): "Diagnostics",
            get_text('menu_licensing', lang): "Licensing"
        }
        
        # Admin specific menu items
        if user['role'] == 'admin':
            menu_options[get_text('menu_admin', lang)] = "Admin"
            menu_options[get_text('menu_tech_specs', lang)] = "Tech Specs"
        
        menu_options[get_text('menu_help_user', lang)] = "Help"

        # Διατηρούμε την επιλεγμένη σελίδα σε όλες τις επανεκτελέσεις
        selected_page_display = st.radio(
            "Navigation", 
            list(menu_options.keys()), 
            index=list(menu_options.values()).index(st.session_state.page),
            key="main_menu_radio"
        )
        st.session_state.page = menu_options[selected_page_display]

        st.divider()

        # Κανόνας 1: Κουμπί μικροφώνου (πάντα παρόν)
        if st.button("🎤 Φωνητική Εντολή", use_container_width=True, key="sidebar_mic_button"):
            st.toast("🎧 Λειτουργία φωνητικής εντολής υπό ανάπτυξη...", icon="🎧") # Μικρό μήνυμα ειδοποίησης

        # Επιλογέας γλώσσας στη Sidebar (προαιρετικό, αλλά καλό για γρήγορη πρόσβαση)
        st.markdown("---")
        sidebar_lang_sel = st.selectbox(
            "🌐 Language", 
            ["Ελληνικά", "English"], 
            index=0 if lang=='gr' else 1, 
            key="sidebar_lang_selector"
        )
        if (st.session_state.lang == 'gr' and sidebar_lang_sel == "English") or \
           (st.session_state.lang == 'en' and sidebar_lang_sel == "Ελληνικά"):
            st.session_state.lang = 'gr' if sidebar_lang_sel == "Ελληνικά" else 'en'
            st.rerun()

        # Κουμπί αποσύνδεσης
        if st.button(get_text('logout', lang), key="logout_button", type="secondary", use_container_width=True):
            AuthManager.log_interaction(user['email'], "Logout", "User logged out.")
            st.session_state.user_info = None
            st.session_state.messages = [] # Καθαρισμός ιστορικού συνομιλίας
            st.session_state.page = "Dashboard" # Επαναφορά σελίδας
            st.success("Έχετε αποσυνδεθεί επιτυχώς!")
            st.rerun()
            
        # Spy Logs (Μόνο για Admin, ή πάντα ενεργό σε αναδιπλούμενη ενότητα)
        if user['role'] == 'admin':
            with st.expander("🕵️ Spy Logs", expanded=False):
                if 'spy_logs' in st.session_state:
                    st.markdown("---")
                    st.caption("Τελευταίες δραστηριότητες:")
                    log_container = st.container(height=200, border=True)
                    for log_entry in st.session_state.spy_logs:
                        log_container.markdown(log_entry, unsafe_allow_html=True)
                    
                    if st.button("☁️ Ανέβασμα Spy Logs στο Drive", use_container_width=True, key="upload_spy_logs_btn"):
                        log_link = sync_current_spy_logs_to_drive()
                        if log_link:
                            st.success(f"Τα logs ανέβηκαν στο Drive! [Δείτε εδώ]({log_link})")
                            st.session_state['last_uploaded_spy_log_link'] = log_link
                        else:
                            st.error("Αποτυχία ανεβάσματος logs.")
                    
                    if 'last_uploaded_spy_log_link' in st.session_state:
                        st.markdown(f"Τελευταίο ανέβασμα: [Δείτε]({st.session_state['last_uploaded_spy_log_link']})")
                        if st.button("🗑️ Καθαρισμός Όλων των Spy Logs από το Drive", use_container_width=True, key="clear_all_spy_logs_btn"):
                            if DatabaseConnector.clear_all_spy_logs_from_drive():
                                st.success("Όλα τα spy logs διαγράφηκαν από το Drive!")
                                if 'last_uploaded_spy_log_link' in st.session_state:
                                    del st.session_state['last_uploaded_spy_log_link']
                                st.rerun()
                            else:
                                st.error("Αποτυχία καθαρισμού spy logs από το Drive.")

    # --- Απόδοση επιλεγμένου περιεχομένου σελίδας ---
    try:
        if st.session_state.page == "Dashboard":
            ui_dashboard.render(user)
        elif st.session_state.page == "AI Chat":
            ui_chat.render(user)
        elif st.session_state.page == "Manuals Library":
            ui_search.render(user)
        elif st.session_state.page == "Clients":
            ui_clients.render(user)
        elif st.session_state.page == "AI Organizer":
            ui_organizer.render(user)
        elif st.session_state.page == "Tools":
            ui_tools.render(user)
        elif st.session_state.page == "Diagnostics":
            ui_diagnostics.render(user)
        elif st.session_state.page == "Licensing":
            ui_licensing.render(user)
        elif st.session_state.page == "Admin":
            ui_admin_panel.render(user)
        elif st.session_state.page == "Tech Specs":
            ui_tech_specs.render(user)
        elif st.session_state.page == "Help":
            ui_help_user.render(user)
        else:
            st.warning(f"Η σελίδα '{st.session_state.page}' δεν βρέθηκε.")
            logger.warning(f"Attempted to navigate to unknown page: {st.session_state.page}")

    except Exception as e:
        logger.error(f"Error rendering page '{st.session_state.page}': {e}", exc_info=True)
        st.error(get_text('general_ui_error', lang).format(error=e))

if __name__ == "__main__":
    main()