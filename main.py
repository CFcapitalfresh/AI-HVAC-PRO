import streamlit as st
from core.auth_manager import AuthManager
# ΕΔΩ ΗΤΑΝ ΤΟ ΛΑΘΟΣ - Τώρα καλούμε τα σωστά αρχεία που ήδη έχεις:
from modules import ui_chat, ui_admin_panel, ui_clients, ui_dashboard, ui_organizer, ui_tools

# --- 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(
    page_title="Mastro Nek AI",
    page_icon="🤖", 
    layout="wide"
)

# --- 2. ΣΥΝΑΡΤΗΣΕΙΣ STARTUP ---
def init_session():
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None

def handle_logout():
    st.session_state.user_info = None
    st.session_state.messages = [] 
    st.rerun()

# --- 3. ΚΥΡΙΑ ΕΦΑΡΜΟΓΗ ---
def main():
    init_session()

    # --- A. LOGIN SCREEN ---
    if not st.session_state.user_info:
        st.header("🔐 Είσοδος Τεχνικού")
        tab_login, tab_register = st.tabs(["Είσοδος", "📝 Νέα Εγγραφή"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Κωδικός", type="password")
                submit = st.form_submit_button("Είσοδος", use_container_width=True)
                if submit:
                    user, msg = AuthManager.verify_login(email, password)
                    if user:
                        st.session_state.user_info = user
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        with tab_register:
            with st.form("register_form"):
                new_email = st.text_input("Email")
                new_name = st.text_input("Ονοματεπώνυμο")
                new_pass = st.text_input("Κωδικός", type="password")
                reg_submit = st.form_submit_button("Εγγραφή", use_container_width=True)
                if reg_submit:
                    if AuthManager.register_new_user(new_email, new_name, new_pass):
                        st.success("✅ Η εγγραφή ολοκληρώθηκε! Αναμείνατε έγκριση.")
                    else:
                        st.error("❌ Σφάλμα εγγραφής.")
        return 

    # --- B. MAIN APP (Αφού μπει) ---
    user = st.session_state.user_info
    role = user.get('role', 'active')

    # SIDEBAR
    with st.sidebar:
        st.write(f"👤 **{user['name']}**")
        st.caption(f"Role: {role.upper()}")
        st.divider()
        
        # Το Μενού με ΟΛΑ τα αρχεία σου
        options = ["📊 Dashboard", "💬 AI Chat", "📇 Πελάτες", "📅 Organizer", "🛠️ Εργαλεία"]
        
        if role == 'admin':
            options.append("⚙️ Admin Panel")
            
        selection = st.radio("Μενού", options)
        
        st.divider()
        if st.button("🚪 Αποσύνδεση"):
            handle_logout()

    # ROUTING (Εδώ συνδέουμε τα κουμπιά με τα αρχεία σου)
    if selection == "📊 Dashboard":
        try: ui_dashboard.render(user)
        except: st.info("Το Dashboard ετοιμάζεται...")

    elif selection == "💬 AI Chat":
        try: ui_chat.render(user)  # <--- Τώρα καλεί το σωστό αρχείο!
        except Exception as e: st.error(f"Chat Error: {e}")

    elif selection == "📇 Πελάτες":
        try: ui_clients.render(user)
        except: st.info("Η σελίδα Πελάτες ετοιμάζεται...")

    elif selection == "📅 Organizer":
        try: ui_organizer.render(user)
        except: st.info("Ο Organizer ετοιμάζεται...")

    elif selection == "🛠️ Εργαλεία":
        try: ui_tools.render(user)
        except: st.info("Τα Εργαλεία ετοιμάζονται...")

    elif selection == "⚙️ Admin Panel":
        if role == 'admin':
            try: ui_admin_panel.render(user)
            except Exception as e: st.error(f"Admin Error: {e}")
        else:
            st.error("⛔ Απαγορεύεται η πρόσβαση.")

if __name__ == "__main__":
    main()