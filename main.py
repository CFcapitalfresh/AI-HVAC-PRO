"""
MASTRO NEK AI - ENTERPRISE EDITION
----------------------------------
Main Entry Point
Features:
- Login / Register Tabs
- Role Based Access Control
- Modular Routing
"""
import streamlit as st
from core.language_pack import get_text
from core.auth_manager import AuthManager

# Safe Imports (για να μην κρασάρει αν λείπει κάτι)
try:
    from modules import ui_chat, ui_search, ui_organizer, ui_clients, ui_admin_panel, ui_tools, ui_help_user, ui_tech_specs
except ImportError as e:
    st.error(f"System Error: Modules not found. {e}")

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
        lang = st.selectbox("Language / Γλώσσα", ['Ελληνικά', 'English'])
        st.session_state.lang = 'gr' if lang == 'Ελληνικά' else 'en'
        
        st.divider()
        st.write(f"👤 **{user['name']}**")
        role_badge = "🔴 ADMIN" if user['role'] == 'admin' else "🟢 TECH"
        st.caption(f"Role: {role_badge}")
        
        # Menu Items
        menu = {
            'chat': get_text('menu_chat', st.session_state.lang),
            'library': get_text('menu_library', st.session_state.lang),
            'clients': get_text('menu_clients', st.session_state.lang),
            'tools': get_text('menu_tools', st.session_state.lang),
            'help': get_text('menu_help', st.session_state.lang),
        }
        
        # Admin Only Items
        if user['role'] == 'admin':
            menu['organizer'] = get_text('menu_organizer', st.session_state.lang)
            menu['admin'] = get_text('menu_admin', st.session_state.lang)
            menu['specs'] = get_text('menu_specs', st.session_state.lang)

        # Navigation
        selection = st.radio("Menu", list(menu.values()), label_visibility="collapsed")
        
        # Routing Logic
        found_keys = [k for k, v in menu.items() if v == selection]
        if found_keys:
            st.session_state.app_mode = found_keys[0]
        
        st.divider()
        if st.button(get_text('logout', st.session_state.lang), use_container_width=True):
            st.session_state.user = None
            st.rerun()

def main():
    init_state()
    
    # --- 1. LOGIN / REGISTER SCREEN ---
    if not st.session_state.user:
        st.title("🛡️ Mastro Nek AI")
        st.markdown("### Σύστημα Τεχνικής Υποστήριξης")
        
        # ΕΔΩ ΕΙΝΑΙ Η ΑΛΛΑΓΗ: Προσθήκη Καρτελών (Tabs)
        tab_login, tab_register = st.tabs(["🔐 Είσοδος", "📝 Νέα Εγγραφή"])
        
        # --- LOGIN TAB ---
        with tab_login:
            with st.form("login_form"):
                email = st.text_input(get_text('email_lbl', st.session_state.lang))
                pwd = st.text_input(get_text('pass_lbl', st.session_state.lang), type="password")
                submit = st.form_submit_button(get_text('btn_login', st.session_state.lang), use_container_width=True)
                
                if submit:
                    u, s = AuthManager.verify_login(email, pwd)
                    if s == "OK": 
                        st.session_state.user = u
                        st.rerun()
                    else: 
                        st.error(f"❌ {get_text('error_auth', st.session_state.lang)} ({s})")

        # --- REGISTER TAB (Το κομμάτι που έλειπε) ---
        with tab_register:
            st.warning("⚠️ Οι νέοι χρήστες απαιτούν έγκριση από τον Admin.")
            with st.form("register_form"):
                new_email = st.text_input("Email")
                new_name = st.text_input("Ονοματεπώνυμο")
                new_pass = st.text_input("Κωδικός", type="password")
                confirm_pass = st.text_input("Επιβεβαίωση Κωδικού", type="password")
                
                reg_submit = st.form_submit_button("Δημιουργία Λογαριασμού", use_container_width=True)
                
                if reg_submit:
                    if new_pass != confirm_pass:
                        st.error("❌ Οι κωδικοί δεν ταιριάζουν.")
                    elif len(new_pass) < 6:
                        st.error("❌ Ο κωδικός πρέπει να είναι τουλάχιστον 6 χαρακτήρες.")
                    else:
                        success = AuthManager.register_new_user(new_email, new_name, new_pass)
                        if success:
                            st.success("✅ Η εγγραφή ολοκληρώθηκε! Επικοινωνήστε με τον Admin για ενεργοποίηση.")
                        else:
                            st.error("❌ Το Email υπάρχει ήδη ή παρουσιάστηκε σφάλμα.")
        return

    # --- 2. MAIN APP ---
    render_sidebar()
    mode = st.session_state.app_mode
    user = st.session_state.user
    
    try:
        if mode == 'chat': ui_chat.render(user)
        elif mode == 'library': ui_search.render(user)
        elif mode == 'organizer': ui_organizer.render(user)
        elif mode == 'clients': ui_clients.render(user)
        elif mode == 'admin': ui_admin_panel.render(user)
        elif mode == 'specs': ui_tech_specs.render(user)
        elif mode == 'help': ui_help_user.render(user)
        elif mode == 'tools': ui_tools.render(user)
    except Exception as e:
        st.error(f"Module Error: {e}")

if __name__ == "__main__":
    main()