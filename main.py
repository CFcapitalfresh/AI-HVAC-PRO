import streamlit as st
from core.auth_manager import AuthManager
from modules import ui_chatbot, ui_admin_panel, ui_clients 
# Σημείωση: Αν έχεις κι άλλα modules (π.χ. ui_library), κάντα import εδώ.

# --- 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ (Πάντα πρώτη) ---
st.set_page_config(
    page_title="Mastro Nek AI",
    page_icon="🤖", # Ή βάλε "logo.png" αν το ανέβασες
    layout="wide"
)

# --- 2. ΣΥΝΑΡΤΗΣΕΙΣ BOOTSTRAP ---
def init_session():
    """Αρχικοποίηση μεταβλητών μνήμης"""
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "Chat"

def handle_logout():
    """Αποσύνδεση και καθαρισμός"""
    st.session_state.user_info = None
    st.session_state.messages = [] # Καθαρισμός ιστορικού chat
    st.rerun()

# --- 3. ΚΥΡΙΑ ΕΦΑΡΜΟΓΗ ---
def main():
    init_session()

    # --- A. ΠΕΡΙΠΤΩΣΗ: ΔΕΝ ΕΧΕΙ ΣΥΝΔΕΘΕΙ (LOGIN SCREEN) ---
    if not st.session_state.user_info:
        st.header("🔐 Είσοδος Τεχνικού")
        
        tab_login, tab_register = st.tabs(["Είσοδος", "📝 Νέα Εγγραφή"])
        
        # Φόρμα Εισόδου
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Κωδικός", type="password")
                submit = st.form_submit_button("Είσοδος", use_container_width=True)
                
                if submit:
                    user, msg = AuthManager.verify_login(email, password)
                    if user:
                        st.session_state.user_info = user
                        st.success(f"Καλωσήρθες {user['name']}!")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        # Φόρμα Εγγραφής
        with tab_register:
            with st.form("register_form"):
                new_email = st.text_input("Email")
                new_name = st.text_input("Ονοματεπώνυμο")
                new_pass = st.text_input("Κωδικός", type="password")
                reg_submit = st.form_submit_button("Δημιουργία Λογαριασμού", use_container_width=True)
                
                if reg_submit:
                    success = AuthManager.register_new_user(new_email, new_name, new_pass)
                    if success:
                        st.success("✅ Η εγγραφή ολοκληρώθηκε! Επικοινωνήστε με τον Admin για έγκριση.")
                    else:
                        st.error("❌ Σφάλμα: Το email υπάρχει ήδη ή λείπουν στοιχεία.")
        return # Σταματάμε εδώ αν δεν είναι συνδεδεμένος

    # --- B. ΠΕΡΙΠΤΩΣΗ: ΕΧΕΙ ΣΥΝΔΕΘΕΙ (MAIN APP) ---
    user = st.session_state.user_info
    role = user.get('role', 'active') # Αν δεν βρει ρόλο, θεωρεί active

    # --- SIDEBAR (ΜΕΝΟΥ) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100) # Προσωρινό εικονίδιο
        st.write(f"👤 **{user['name']}**")
        st.caption(f"Role: {role.upper()}")
        st.divider()
        
        # Επιλογές Μενού ανάλογα τον Ρόλο
        options = ["💬 AI Chat", "📇 Πελάτες"]
        
        # Αν είναι Admin, βλέπει και τα έξτρα
        if role == 'admin':
            options.append("⚙️ Admin Panel")
            
        selection = st.radio("Μενού", options)
        
        st.divider()
        if st.button("🚪 Αποσύνδεση", use_container_width=True):
            handle_logout()

    # --- ΚΥΡΙΩΣ ΟΘΟΝΗ (ROUTING) ---
    
    if selection == "💬 AI Chat":
        # Καλεί το Chatbot UI
        # (Βεβαιώσου ότι το αρχείο modules/ui_chatbot.py υπάρχει)
        try:
            ui_chatbot.render(user) 
        except Exception as e:
            st.error("⚠️ Το Chat Module λείπει ή έχει σφάλμα.")
            st.write(e)

    elif selection == "📇 Πελάτες":
        try:
            ui_clients.render(user)
        except Exception as e:
            st.info("🚧 Η ενότητα Πελάτες ετοιμάζεται.")
            st.error(e)

    elif selection == "⚙️ Admin Panel":
        # Έλεγχος ασφαλείας (διπλός έλεγχος)
        if role == 'admin':
            try:
                ui_admin_panel.render(user)
            except Exception as e:
                st.error("⚠️ Το Admin Panel έχει θέμα.")
                st.write(e)
        else:
            st.error("⛔ Δεν έχετε πρόσβαση εδώ.")

if __name__ == "__main__":
    main()