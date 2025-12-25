# Αρχείο: diagnose.py
# Εργαλείο Ελέγχου Συστημάτων HVAC App
# ΕΝΗΜΕΡΩΣΗ: Προστέθηκε Αυτόματος Εντοπισμός Μοντέλου (Auto-Detect)

import streamlit as st
import os
import sys
import time

st.set_page_config(page_title="System Diagnosis", page_icon="🩺")

st.title("🩺 HVAC System Diagnosis")
st.write("Εκτέλεση διαγνωστικών ελέγχων για εντοπισμό του προβλήματος...")

def status_write(msg, state="loading"):
    if state == "loading":
        return st.empty().info(f"⏳ {msg}...")
    elif state == "success":
        st.success(f"✅ {msg}")
    elif state == "error":
        st.error(f"❌ {msg}")
    elif state == "warning":
        st.warning(f"⚠️ {msg}")

# --- ΛΕΙΤΟΥΡΓΙΑ: ΑΥΤΟΜΑΤΟΣ ΕΝΤΟΠΙΣΜΟΣ ΜΟΝΤΕΛΟΥ ---
def get_best_model(api_key_val):
    """Βρίσκει ποιο μοντέλο λειτουργεί αυτή τη στιγμή"""
    import google.generativeai as genai
    genai.configure(api_key=api_key_val)
    
    try:
        # Ρωτάμε την Google τι έχει διαθέσιμο
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Λίστα προτίμησης (από το καλύτερο προς το χειρότερο)
        # Ψάχνουμε και με "models/" και χωρίς, για σιγουριά
        preferred = [
            "gemini-2.0-flash-exp", 
            "models/gemini-2.0-flash-exp",
            "gemini-1.5-pro", 
            "models/gemini-1.5-pro",
            "gemini-1.5-flash", 
            "models/gemini-1.5-flash",
            "gemini-pro",
            "models/gemini-pro"
        ]
        
        # 1. Ψάχνουμε τα αγαπημένα μας στη λίστα διαθέσιμων
        for p in preferred:
            if p in available_models:
                return p
        
        # 2. Αν δεν βρούμε συγκεκριμένο, παίρνουμε το πρώτο που έχει τη λέξη "gemini"
        for m in available_models:
            if "gemini" in m:
                return m
                
        return "models/gemini-1.5-flash" # Τελευταία ελπίδα
    except Exception as e:
        return "models/gemini-1.5-flash"

# --- CHECK 1: ENVIRONMENT & LIBRARIES ---
st.subheader("1. Έλεγχος Βιβλιοθηκών")
try:
    import google.generativeai as genai
    import pypdf
    from google.oauth2 import service_account
    status_write("Όλες οι βιβλιοθήκες (google-genai, pypdf) βρέθηκαν", "success")
except ImportError as e:
    status_write(f"Λείπει βιβλιοθήκη: {e}", "error")
    st.stop()

# --- CHECK 2: SECRETS FILE ---
st.subheader("2. Έλεγχος Κλειδιών (Secrets)")
api_key = None
try:
    if "GEMINI_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_KEY"]
        mask = api_key[:5] + "..." + api_key[-4:]
        status_write(f"Το API Key βρέθηκε ({mask})", "success")
    else:
        status_write("Δεν βρέθηκε το GEMINI_KEY στο secrets.toml", "error")
        st.info("Φτιάξε φάκελο .streamlit/secrets.toml και βάλε μέσα: GEMINI_KEY = 'YOUR_KEY'")
except FileNotFoundError:
    status_write("Δεν βρέθηκε φάκελος .streamlit ή αρχείο secrets.toml", "error")
except Exception as e:
    status_write(f"Σφάλμα ανάγνωσης secrets: {e}", "error")

# --- CHECK 3: GOOGLE AI CONNECTION (PING) ---
st.subheader("3. Σύνδεση με AI (Ping Test)")
if api_key:
    msg_box = status_write("Προσπάθεια σύνδεσης με Google Servers")
    try:
        genai.configure(api_key=api_key)
        # Προσπάθεια εύρεσης μοντέλων
        models = list(genai.list_models())
        count = len(models)
        status_write(f"Επιτυχία! Συνδέθηκε και βρήκε {count} διαθέσιμα μοντέλα.", "success")
            
    except Exception as e:
        status_write(f"Αποτυχία Σύνδεσης: {str(e)}", "error")
        st.error("Αυτό σημαίνει ότι το Κλειδί είναι λάθος ή μπλοκαρισμένο, ή δεν υπάρχει ίντερνετ.")

# --- CHECK 4: SIMULATION (GENERATION) ---
st.subheader("4. Προσομοίωση Απάντησης (Test Run)")
if api_key:
    # ΕΔΩ ΕΙΝΑΙ Η ΜΕΓΑΛΗ ΑΛΛΑΓΗ - ΑΥΤΟΜΑΤΗ ΕΠΙΛΟΓΗ
    active_model_name = get_best_model(api_key)
    st.info(f"ℹ️ Το σύστημα επέλεξε αυτόματα το μοντέλο: **{active_model_name}**")
    
    msg_box = status_write(f"Στέλνω δοκιμαστική ερώτηση στο {active_model_name}...")
    try:
        model = genai.GenerativeModel(active_model_name)
        # Στέλνουμε κάτι πολύ απλό
        response = model.generate_content("Γράψε τη λέξη 'OK'.")
        
        if response.text:
            status_write(f"Το AI απάντησε: '{response.text.strip()}'", "success")
        else:
            status_write("Το AI απάντησε αλλά το κείμενο ήταν κενό.", "warning")
            
    except Exception as e:
        status_write(f"CRITICAL ERROR: {str(e)}", "error")
        if "429" in str(e):
            st.error("👉 ΕΠΙΒΕΒΑΙΩΣΗ: Το πρόβλημα είναι το QUOTA (429). Το κλειδί έχει ξεπεράσει τα όρια.")
        elif "403" in str(e) or "API_KEY_INVALID" in str(e):
            st.error("👉 ΕΠΙΒΕΒΑΙΩΣΗ: Το κλειδί δεν είναι έγκυρο.")
        elif "404" in str(e):
             st.error("👉 ΕΠΙΒΕΒΑΙΩΣΗ: Το μοντέλο δεν βρέθηκε. Δοκίμασε να κάνεις update: pip install --upgrade google-generativeai")
        else:
             st.error("👉 Άγνωστο σφάλμα δικτύου/συστήματος.")

# --- CHECK 5: PDF ENGINE ---
st.subheader("5. Μηχανή PDF")
try:
    # Δημιουργία ενός dummy PDF στη μνήμη για έλεγχο
    from io import BytesIO
    from pypdf import PdfWriter, PdfReader
    
    buffer = BytesIO()
    w = PdfWriter()
    w.add_blank_page(width=100, height=100)
    w.write(buffer)
    buffer.seek(0)
    
    r = PdfReader(buffer)
    if len(r.pages) > 0:
        status_write("Η βιβλιοθήκη PDF λειτουργεί σωστά.", "success")
    else:
        status_write("Πρόβλημα στη βιβλιοθήκη PDF.", "error")
except Exception as e:
    status_write(f"Σφάλμα PDF: {e}", "error")

st.divider()
st.write("Η διάγνωση ολοκληρώθηκε.")