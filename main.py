# Αρχείο: main.py (v3 - With Reset Button)
import streamlit as st
import tempfile
import os
import pandas as pd 
import auth   
import brain  
import drive  

st.set_page_config(page_title="HVAC Master", page_icon="⚡", layout="wide")

# --- STYLE ---
st.markdown("""<style>
    .admin-badge { color: red; border: 1px solid red; padding: 2px 5px; border-radius: 5px; font-weight: bold;}
    .reset-btn { width: 100%; border: 1px solid #ff4b4b; color: #ff4b4b; }
</style>""", unsafe_allow_html=True)

# --- INIT ---
if "user" not in st.session_state: st.session_state.user = None
if "messages" not in st.session_state: st.session_state.messages = []

# Setup AI Key
if "GEMINI_KEY" in st.secrets:
    brain.setup_ai(st.secrets["GEMINI_KEY"])
else:
    st.error("Missing GEMINI_KEY"); st.stop()

# --- LOGIN FLOW ---
if not st.session_state.user:
    st.title("🔐 HVAC Login")
    tab1, tab2 = st.tabs(["Είσοδος", "Εγγραφή"])
    
    with tab1:
        e = st.text_input("Email").lower().strip()
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            user, msg = auth.check_login(e, p)
            if user: st.session_state.user = user; st.rerun()
            elif msg == "PENDING": st.warning("⏳ Ο λογαριασμός είναι υπό έγκριση.")
            elif msg == "BLOCKED": st.error("⛔ Blocked.")
            else: st.error("Λάθος στοιχεία.")
            
    with tab2:
        ne = st.text_input("New Email").lower().strip()
        nn = st.text_input("Name")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            if auth.register_user(ne, nn, np): st.success("✅ Εστάλη! Αναμονή έγκρισης.")
            else: st.error("Το email υπάρχει ήδη.")
    st.stop()

# --- MAIN APP FLOW ---
user = st.session_state.user

# Sidebar
with st.sidebar:
    st.header(f"👤 {user['name']}")
    
    # --- ΚΟΥΜΠΙ RESET (ΝΕΑ ΔΙΑΓΝΩΣΗ) ---
    st.warning("👇 Ξεκινάς νέα βλάβη;")
    if st.button("🗑️ Νέα Συζήτηση (Reset)", use_container_width=True):
        st.session_state.messages = [] # Καθαρισμός μνήμης
        st.toast("Η μνήμη καθάρισε! Έτοιμος για νέα βλάβη.", icon="🧹")
        st.rerun() # Επανεκκίνηση σελίδας
        
    st.divider()
    
    if user['role'] == 'admin': 
        st.markdown("<span class='admin-badge'>ADMIN</span>", unsafe_allow_html=True)
        mode = st.radio("Menu", ["Chat", "Users", "Drive & Library", "Logs"])
    else:
        mode = "Chat"
    
    st.divider()
    if st.button("Logout"): st.session_state.user = None; st.rerun()

# 1. CHAT INTERFACE
if mode == "Chat":
    st.title("⚡ HVAC Expert")
    tech_type = st.radio("Ειδικότητα:", ["AC", "Ψύξη", "Θέρμανση"], horizontal=True)
    
    # Uploads
    uploaded_paths = []
    with st.expander("📸 Manual Upload (Αν θες να ανεβάσεις τώρα)"):
        files = st.file_uploader("Αρχεία", accept_multiple_files=True)
        if files:
            for f in files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f.name) as tmp:
                    tmp.write(f.getvalue()); uploaded_paths.append(tmp.name)
    
    # Chat History
    if not st.session_state.messages:
        st.info("👋 Γεια σου! Περιέγραψέ μου τη βλάβη ή τον κωδικό σφάλματος.")
        
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
        
    if prompt := st.chat_input("Περιγραφή προβλήματος..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🧠 Ανάλυση & Σκέψη..."):
                resp = brain.smart_solve(prompt, uploaded_paths, st.session_state.messages[:-1], tech_type)
                st.markdown(resp)
        
        st.session_state.messages.append({"role": "assistant", "content": resp})
        auth.log_interaction(user['email'], prompt, resp, tech_type)

# 2. ADMIN: USERS
elif mode == "Users":
    st.title("👥 Διαχείριση Χρηστών")
    users = auth.load_data(auth.USERS_FILE)
    for email, u in users.items():
        if email == "admin": continue
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: st.write(f"**{u['name']}** ({u['status']})")
        with c2:
            if u['status'] == 'pending':
                if st.button("✅ Approve", key=f"app_{email}"):
                    users[email]['status'] = 'approved'; auth.save_data(auth.USERS_FILE, users); st.rerun()
        with c3:
            if u['role'] != 'admin' and u['status'] == 'approved':
                if st.button("🎖️ Make Admin", key=f"adm_{email}"):
                    users[email]['role'] = 'admin'; auth.save_data(auth.USERS_FILE, users); st.rerun()

# 3. ADMIN: DRIVE & LIBRARY
elif mode == "Drive & Library":
    st.title("☁️ Διαχείριση Βιβλιοθήκης")
    
    saved_id = drive.load_config()
    fid = st.text_input("Google Drive Folder ID", value=saved_id)
    
    if st.button("🔄 Ενημέρωση Βιβλιοθήκης (Sync)"):
        count = drive.sync_drive_folder(fid)
        if count is not None: st.success(f"✅ Βρέθηκαν {count} manuals!")
        else: st.error("Σφάλμα σύνδεσης.")
        
    st.divider()
    st.subheader("📚 Περιεχόμενα Βιβλιοθήκης (Smart View)")
    
    files_list = drive.get_files_list()
    if files_list:
        st.info(f"Σύνολο Αρχείων: {len(files_list)}")
        df = pd.DataFrame(files_list)
        
        if not df.empty:
            if 'real_model' not in df.columns: df['real_model'] = df.get('name', 'Unknown')
            if 'topics' not in df.columns: df['topics'] = '-'
            if 'type' not in df.columns: df['type'] = 'General'
            
            df_show = df[['real_model', 'type', 'topics', 'name']]
            df_show.columns = ["Μοντέλο (AI)", "Τύπος", "Περιεχόμενο", "Όνομα Αρχείου"]
            st.dataframe(df_show, use_container_width=True)
    else:
        st.warning("Η βιβλιοθήκη είναι άδεια. Πατήστε 'Ενημέρωση'.")

# 4. ADMIN: LOGS
elif mode == "Logs":
    st.title("📊 Chat Logs")
    logs = auth.load_data(auth.LOGS_FILE)
    st.dataframe(logs)