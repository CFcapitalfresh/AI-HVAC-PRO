import streamlit as st
from core.auth_manager import AuthManager
from core.language_pack import get_text
# Προσθήκη του ui_search στα imports
from modules import ui_chat, ui_admin_panel, ui_clients, ui_dashboard, ui_organizer, ui_tools, ui_search

st.set_page_config(page_title="Mastro Nek AI", page_icon="🤖", layout="wide")

def init_session():
    if 'user_info' not in st.session_state: st.session_state.user_info = None
    if 'lang' not in st.session_state: st.session_state.lang = 'gr'

def handle_logout():
    st.session_state.user_info = None
    st.session_state.messages = [] 
    st.rerun()

def main():
    init_session()
    lang = st.session_state.lang

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
                    user, msg = AuthManager.verify_login(email, pwd)
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

    # SIDEBAR
    with st.sidebar:
        st.write(f"👤 **{user['name']}**")
        st.caption(f"Role: {role.upper()}")
        st.divider()
        
        # Γλώσσα
        l_sel = st.radio("🌐 Language", ["Ελληνικά", "English"], index=0 if lang=='gr' else 1, horizontal=True)
        new_lang = 'gr' if l_sel == "Ελληνικά" else 'en'
        if new_lang != lang:
            st.session_state.lang = new_lang
            st.rerun()

        st.divider()
        
        # Menu (Τώρα περιλαμβάνει τη Βιβλιοθήκη)
        opts = {
            get_text('menu_dashboard', new_lang): "dash",
            get_text('menu_chat', new_lang): "chat",
            get_text('menu_library', new_lang): "lib",  # <--- Η ΠΡΟΣΘΗΚΗ
            get_text('menu_clients', new_lang): "clients",
            get_text('menu_organizer', new_lang): "org",
            get_text('menu_tools', new_lang): "tools"
        }
        if role == 'admin':
            opts[get_text('menu_admin', new_lang)] = "admin"

        # Ελέγχουμε αν υπάρχει 'app_mode' από το Dashboard και το εφαρμόζουμε
        default_idx = 0
        if 'app_mode' in st.session_state:
            mode_map = {'chat': 1, 'library': 2, 'tools': 5} # Indices based on list above
            default_idx = mode_map.get(st.session_state.app_mode, 0)
            del st.session_state.app_mode # Clear it

        selection_label = st.radio(get_text('menu_header', new_lang), list(opts.keys()), index=default_idx)
        selection_code = opts[selection_label]
        
        st.divider()
        
        # ΚΟΥΜΠΙ ΝΕΑ ΣΥΝΟΜΙΛΙΑ (ΣΤΟ SIDEBAR)
        if selection_code == "chat":
            if st.button(f"➕ {get_text('new_chat_side', new_lang)}", type="primary", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        if st.button(get_text('logout', new_lang)):
            handle_logout()

    # ROUTING
    if selection_code == "dash": ui_dashboard.render(user)
    elif selection_code == "chat": ui_chat.render(user)
    elif selection_code == "lib": ui_search.render(user) # <--- Η ΣΥΝΔΕΣΗ
    elif selection_code == "clients": ui_clients.render(user)
    elif selection_code == "org": ui_organizer.render(user)
    elif selection_code == "tools": ui_tools.render(user)
    elif selection_code == "admin": ui_admin_panel.render(user)

if __name__ == "__main__":
    main()