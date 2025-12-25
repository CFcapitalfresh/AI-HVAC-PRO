import streamlit as st
import tempfile
import os
import time
import pandas as pd
import smart_library
from datetime import datetime
from streamlit_gsheets import GSheetsConnection 

# Εισαγωγή των νέων σελίδων από τον φάκελο app_modules
from app_modules import page_search
from app_modules import page_review
from app_modules import page_admin  # <--- ΝΕΑ ΠΡΟΣΘΗΚΗ

# Τα δικά σου αρχεία
import auth   
import brain  
import drive
import organizer

# --- ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Mastro Nek", page_icon="⚡", layout="wide")

# 👇 ΤΟ LINK ΣΟΥ 👇
SHEET_URL = "https://docs.google.com/spreadsheets/d/16rFxNyROnqOawQ2UJkGy2_aekOv3klZQ1mNmjfGOaRY/edit?usp=sharing"

# --- STYLE ---
st.markdown("""<style>
    .admin-badge { color: red; border: 1px solid red; padding: 2px 5px; border-radius: 5px; font-weight: bold;}
    .footer { font-size: 11px; color: #666; text-align: center; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }
    .help-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #0068c9; }
</style>""", unsafe_allow_html=True)

if "user" not in st.session_state: st.session_state.user = None
if "messages" not in st.session_state: st.session_state.messages = []

# --- ΣΥΝΔΕΣΗ (ΜΟΝΟ ΓΙΑ ΕΓΓΡΑΦΕΣ) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    pass 

# --- ΒΟΗΘΗΤΙΚΗ ΣΥΝΑΡΤΗΣΗ ΓΙΑ ΑΝΑΓΝΩΣΗ (BYPASS) ---
def read_sheet(sheet_name):
    csv_url = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet={sheet_name}")
    try:
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame() 

# --- LOGIN (SIDEBAR) ---
if not st.session_state.user:
    st.title("🔐 Mastro Nek Login") 
    tab1, tab2 = st.tabs(["Είσοδος", "Εγγραφή"])
    
    with tab1:
        e_in = st.text_input("Email").lower().strip()
        p_in = st.text_input("Password", type="password")
        if st.button("Login"):
            users_df = read_sheet("Users")
            if not users_df.empty:
                found = users_df[users_df['email'] == e_in]
                if not found.empty:
                    try:
                        user, msg = auth.check_login(e_in, p_in)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                             st.warning("⚠️ Λειτουργία Bypass (λόγω σφάλματος σύνδεσης)")
                             st.session_state.user = found.iloc[0].to_dict()
                             st.rerun()
                    except:
                        st.session_state.user = found.iloc[0].to_dict()
                        st.rerun()
                else:
                    st.error("❌ Το email δεν βρέθηκε.")
            else:
                st.error("❌ Δεν μπόρεσα να διαβάσω τη βάση δεδομένων.")

    with tab2:
        ne = st.text_input("New Email"); nn = st.text_input("Name"); np = st.text_input("New Password", type="password")
        if st.button("Register"): 
            users_df = read_sheet("Users")
            if ne in users_df['email'].values:
                st.error("Το email υπάρχει ήδη.")
            else:
                try:
                    import hashlib
                    hashed = hashlib.sha256(np.encode()).hexdigest()
                    new_user = pd.DataFrame([{
                        "email": ne, "name": nn, "password": hashed, 
                        "role": "user", "status": "pending", 
                        "joined": str(datetime.now())
                    }])
                    conn.update(spreadsheet=SHEET_URL, worksheet="Users", data=pd.concat([users_df, new_user], ignore_index=True))
                    st.success("✅ Αίτηση εστάλη! Περίμενε έγκριση.")
                except Exception as e:
                    st.error(f"Σφάλμα εγγραφής: {e}")
    st.stop()

# --- ΚΥΡΙΩΣ ΕΦΑΡΜΟΓΗ ---
user = st.session_state.user

with st.sidebar:
    st.header(f"👤 {user['name']}")
    if user.get('role') == 'admin': st.markdown('<span class="admin-badge">ADMIN</span>', unsafe_allow_html=True)
    if st.button("🗑️ Νέα Συζήτηση"): st.session_state.messages = []; st.rerun()
    st.divider()
    
    # --- ΤΡΟΠΟΠΟΙΗΜΕΝΟ ΜΕΝΟΥ ---
    menu_options = ["Chat (AI)", "🧮 Εργαλεία", "📇 Πελατολόγιο", "Βοήθεια"]
    if user.get('role') == 'admin': 
        # ΠΡΟΣΘΕΣΑ ΤΟ "⚙️ Ρυθμίσεις" ΣΤΟ ΤΕΛΟΣ
        menu_options.extend(["Users", "Drive & Library", "🔍 Αναζήτηση", "🛠️ Διόρθωση", "Logs", "⚙️ Ρυθμίσεις"])
    
    mode = st.sidebar.radio("Μενού", menu_options)
    
    st.divider()
    if st.button("Logout"): st.session_state.user = None; st.rerun()
    st.markdown("---"); st.markdown("<div class='footer'>Mastro Nek AI</div>", unsafe_allow_html=True)

# 1. CHAT
if mode == "Chat (AI)":
    st.title("⚡ Mastro Nek AI")
    c1, c2 = st.columns(2)
    with c1: img_file = st.file_uploader("📸 Φωτογραφία", type=['png', 'jpg', 'jpeg'])
    with c2: audio_val = st.audio_input("🎙️ Πες τη βλάβη")
    pdf_files = st.file_uploader("📂 PDF Manual", accept_multiple_files=True, type=['pdf'])
    
    uploaded_pdfs = []
    if pdf_files:
        for f in pdf_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f.name) as tmp:
                tmp.write(f.getvalue()); uploaded_pdfs.append(tmp.name)
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    user_input = st.chat_input("Γράψε τη βλάβη...")
    
    if user_input or audio_val or img_file:
        prompt_text = user_input if user_input else ("(Audio)" if audio_val else "(Image)")
        if prompt_text and (len(st.session_state.messages)==0 or st.session_state.messages[-1]["content"] != prompt_text):
            st.session_state.messages.append({"role": "user", "content": prompt_text})
            with st.chat_message("user"): st.markdown(prompt_text)
            
            with st.chat_message("assistant"):
                with st.spinner("🧠 Σκέφτομαι..."):
                    brain.setup_ai(st.secrets["GEMINI_KEY"])
                    resp = brain.smart_solve(user_input, uploaded_pdfs, [img_file] if img_file else [], audio_val, st.session_state.messages[:-1], "General")
                    st.markdown(resp)
                    try: 
                        logs_df = read_sheet("Logs")
                        new_log = pd.DataFrame([{"user": user['email'], "query": prompt_text, "response": resp[:100], "time": str(datetime.now())}])
                        conn.update(spreadsheet=SHEET_URL, worksheet="Logs", data=pd.concat([logs_df, new_log], ignore_index=True))
                    except: pass
            st.session_state.messages.append({"role": "assistant", "content": resp})
            st.session_state['last_response'] = resp

# 2. TOOLS
elif mode == "🧮 Εργαλεία":
    st.title("🧮 Εργαλεία")
    st.info("Εργαλεία BTU και Φρέον...")

# 3. CLIENTS
elif mode == "📇 Πελατολόγιο":
    st.title("📇 Πελατολόγιο")
    clients_df = read_sheet("Clients")
    st.dataframe(clients_df, use_container_width=True)

# 4. HELP
elif mode == "Βοήθεια":
    st.title("📖 Βοήθεια"); st.write("Οδηγίες χρήσης...")

# ADMIN - Users
elif mode == "Users":
    st.title("👥 Users")
    users_df = read_sheet("Users")
    st.dataframe(users_df)

# ADMIN - Drive & Library
elif mode == "Drive & Library":
    st.title("☁️ Drive & Library Manager")
    
    current_folder = drive.load_config()
    new_folder_id = st.text_input("📂 ID Φακέλου Google Drive", value=current_folder)
    
    if st.button("💾 Αποθήκευση ID"):
        drive.save_config(new_folder_id.strip())
        st.success("OK"); st.rerun()

    st.divider()

    # --- STATISTICS & EXPORT ---
    df = smart_library.get_stats_dataframe()
    if df is not None and not df.empty:
        st.subheader(f"📊 Στατιστικά Βιβλιοθήκης ({len(df)} Αρχεία)")
        
        c1, c2, c3 = st.columns(3)
        sm_count = len(df[df['meta_type'].str.contains("SERVICE", case=False, na=False)])
        um_count = len(df[df['meta_type'].str.contains("USER", case=False, na=False)])
        err_count = len(df[df['meta_type'].str.contains("ERROR", case=False, na=False)])
        
        c1.metric("🛠️ Service", sm_count)
        c2.metric("📖 User", um_count)
        c3.metric("⚠️ Errors", err_count)

        # BUTTON EXPORT
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Κατέβασμα Λίστας σε Excel (CSV)",
            data=csv,
            file_name=f"hvac_library_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        with st.expander("🔎 Δείτε όλα τα αρχεία αναλυτικά"):
            st.dataframe(df[['name', 'brand', 'model', 'meta_type']], use_container_width=True)
            
        st.caption("Κατανομή ανά Μάρκα:")
        st.bar_chart(df['brand'].value_counts().head(10))
    else:
        st.info("Δεν βρέθηκαν στατιστικά ακόμα. Τρέξτε τη συντήρηση.")

    st.divider()
    
    st.subheader("⚙️ Εργασίες Συντήρησης")
    if st.button("🚀 ΕΝΑΡΞΗ: Deep Organize & Index", type="primary", use_container_width=True):
        smart_library.run_full_maintenance(new_folder_id)
        st.success("Ολοκληρώθηκε!"); st.rerun()

# --- ΝΕΕΣ ΣΕΛΙΔΕΣ ΑΠΟ APP_MODULES ---

elif mode == "🔍 Αναζήτηση":
    page_search.show_search_page()

elif mode == "🛠️ Διόρθωση":
    page_review.show_review_page()

elif mode == "⚙️ Ρυθμίσεις":  # <--- Η ΝΕΑ ΣΕΛΙΔΑ
    page_admin.show_admin_page()

# ADMIN - Logs
elif mode == "Logs":
    st.title("📜 Logs")
    st.dataframe(read_sheet("Logs"))