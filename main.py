import streamlit as st
from core.auth_manager import AuthManager
from core.language_pack import get_text
# Modules Import
from modules import ui_chat, ui_admin_panel, ui_clients, ui_dashboard, ui_organizer, ui_tools

# --- 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(
    page_title="Mastro Nek AI",
    page_icon="🤖", 
    layout="wide"
)

# --- 2. SESSION SETUP ---
def init_session():
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'lang' not in st.session_state:
        st.session_state.lang = 'gr' # Default Ελληνικά

def handle_logout():
    st.session_state.user_info = None
    st.session_state.messages = [] 
    st.rerun()

# --- 3. MAIN APPLICATION ---
def main():
    init_session()
    
    # Γλώσσα (Τρέχουσα)
    lang = st.session_state.lang

    # --- A. LOGIN SCREEN ---
    if not st.session_state.user_info:
        st.header(f"🔐 {get_text('app_title', lang)}")
        
        # Επιλογή Γλώσσας στο Login
        c_lang, _ = st.columns([1,5])
        with c_lang:
            sel_lang = st.selectbox("🌐 Language", ["Ελληνικά", "English"], index=0 if lang=='gr' else 1)
            st.session_state.lang = 'gr' if sel_lang == "Ελληνικά" else 'en'
            if st.session_state.lang != lang: st.rerun() # Refresh αν αλλάξει

        tab_login, tab_register = st.tabs([get_text('login_tab', lang), get_text('register_tab', lang)])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input(get_text('email_lbl', lang))
                password = st.text_input(get_text('pass_lbl', lang), type="password")
                submit = st.form_submit_button(get_text('btn_login', lang), use_container_width=True)
                if submit:
                    user, msg = AuthManager.verify_login(email, password)
                    if user:
                        st.session_state.user_info = user
                        st.success(get_text('login_success', lang))
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        with tab_register:
            with st.form("register_form"):
                new_email = st.text_input(get_text('email_lbl', lang))
                new_name = st.text_input(get_text('name_lbl', lang))
                new_pass = st.text_input(get_text('pass_lbl', lang), type="password")
                reg_submit = st.form_submit_button(get_text('btn_register', lang), use_container_width=True)
                if reg_submit:
                    if AuthManager.register_new_user(new_email, new_name, new_pass):
                        st.success(get_text('reg_success', lang))
                    else:
                        st.error("Error / Σφάλμα")
        return 

    # --- B. MAIN APP ---
    user = st.session_state.user_info
    role = user.get('role', 'active')

    # SIDEBAR
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
        st.write(f"👤 **{user['name']}**")
        st.caption(f"Role: {role.upper()}")
        
        st.divider()
        
        # Επιλογέας Γλώσσας (Μέσα στην εφαρμογή)
        lang_choice = st.radio("🌐 Language", ["Ελληνικά", "English"], index=0 if lang=='gr' else 1, horizontal=True)
        new_lang = 'gr' if lang_choice == "Ελληνικά" else 'en'
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

        st.divider()
        
        # Δυναμικό Μενού (Φέρνει τις λέξεις από το Λεξικό)
        opt_dash = get_text('menu_dashboard', new_lang)
        opt_chat = get_text('menu_chat', new_lang)
        opt_client = get_text('menu_clients', new_lang)
        opt_org = get_text('menu_organizer', new_lang)
        opt_tools = get_text('menu_tools', new_lang)
        opt_admin = get_text('menu_admin', new_lang)

        options = [opt_dash, opt_chat, opt_client, opt_org, opt_tools]
        
        if role == 'admin':
            options.append(opt_admin)
            
        selection = st.radio(get_text('menu_header', new_lang), options)
        
        st.divider()
        if st.button(get_text('logout', new_lang)):
            handle_logout()

    # ROUTING (Σύνδεση επιλογής με αρχεία)
    if selection == opt_dash:
        try: ui_dashboard.render(user)
        except: st.info("Dashboard loading...")

    elif selection == opt_chat:
        try: ui_chat.render(user)
        except Exception as e: st.error(f"Chat Error: {e}")

    elif selection == opt_client:
        try: ui_clients.render(user)
        except: st.info("Clients loading...")

    elif selection == opt_org:
        try: ui_organizer.render(user)
        except: st.info("Organizer loading...")

    elif selection == opt_tools:
        try: ui_tools.render(user)
        except: st.info("Tools loading...")

    elif selection == opt_admin:
        if role == 'admin':
            try: ui_admin_panel.render(user)
            except Exception as e: st.error(f"Admin Error: {e}")
        else:
            st.error("⛔ Access Denied")

if __name__ == "__main__":
    main()