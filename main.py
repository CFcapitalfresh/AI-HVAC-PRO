"""
MASTRO NEK AI - PLATINUM EDITION (v7.0)
---------------------------------------
Modular Monolith Architecture
"""
import streamlit as st
from core.language_pack import get_text
from core.auth_manager import AuthManager

# Safe Imports for Modules
try:
    from modules import ui_chat, ui_search, ui_organizer, ui_clients, ui_admin_panel, ui_tools, ui_help_user, ui_tech_specs
except ImportError as e:
    st.error(f"Critical Module Error: {e}")

# --- CONFIG ---
st.set_page_config(page_title="Mastro Nek AI", page_icon="⚡", layout="wide")

def init_state():
    if 'user' not in st.session_state: st.session_state.user = None
    if 'lang' not in st.session_state: st.session_state.lang = 'gr'
    if 'app_mode' not in st.session_state: st.session_state.app_mode = 'chat'

def render_sidebar():
    user = st.session_state.user
    with st.sidebar:
        # Language Switcher
        lang = st.selectbox("Language", ['Ελληνικά', 'English'])
        st.session_state.lang = 'gr' if lang == 'Ελληνικά' else 'en'
        
        st.divider()
        st.write(f"👤 **{user['name']}**")
        
        # Menu Construction
        menu = {
            'chat': get_text('menu_chat', st.session_state.lang),
            'library': get_text('menu_library', st.session_state.lang),
            'clients': get_text('menu_clients', st.session_state.lang),
            'tools': get_text('menu_tools', st.session_state.lang),
            'help': get_text('menu_help', st.session_state.lang),
        }
        
        if user['role'] == 'admin':
            menu['organizer'] = get_text('menu_organizer', st.session_state.lang)
            menu['admin'] = get_text('menu_admin', st.session_state.lang)
            menu['specs'] = get_text('menu_specs', st.session_state.lang)

        # Radio Button
        selection = st.radio("Menu", list(menu.values()), label_visibility="collapsed")
        
        # Reverse Lookup (Value -> Key)
        st.session_state.app_mode = [k for k, v in menu.items() if v == selection][0]
        
        st.divider()
        if st.button(get_text('logout', st.session_state.lang)):
            st.session_state.user = None
            st.rerun()

def main():
    init_state()
    
    # 1. Login Gate
    if not st.session_state.user:
        st.title("🛡️ Mastro Nek AI")
        with st.form("login"):
            email = st.text_input(get_text('email_lbl', st.session_state.lang))
            pwd = st.text_input(get_text('pass_lbl', st.session_state.lang), type="password")
            if st.form_submit_button(get_text('btn_login', st.session_state.lang)):
                u, s = AuthManager.verify_login(email, pwd)
                if s == "OK": 
                    st.session_state.user = u
                    st.rerun()
                else: st.error(s)
        return

    # 2. Main App
    render_sidebar()
    mode = st.session_state.app_mode
    user = st.session_state.user
    
    # 3. Routing
    try:
        if mode == 'chat': ui_chat.render(user)
        elif mode == 'library': ui_search.render(user)
        elif mode == 'organizer': ui_organizer.render(user)
        elif mode == 'clients': ui_clients.render(user)
        elif mode == 'admin': ui_admin_panel.render(user)
        elif mode == 'specs': ui_tech_specs.render(user)
        elif mode == 'help': ui_help_user.render(user)
        else: st.write("Module under construction")
    except Exception as e:
        st.error(f"Application Error: {e}")

if __name__ == "__main__":
    main()