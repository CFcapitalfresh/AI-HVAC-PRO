"""
MODULE: Chat Interface System
VERSION: 2.0.0 (TITANIUM)
DESCRIPTION: Διαχειρίζεται το UI της συνομιλίας, τα Uploads και την αλληλεπίδραση με το AI.
"""

import streamlit as st
import logging
from typing import List, Dict, Any, Optional

# Ρύθμιση Logger για το Module
logger = logging.getLogger("Module_Chat")

def render_chat_interface(brain_module: Any, auth_module: Any, user_email: str) -> None:
    """
    Εμφανίζει το περιβάλλον συνομιλίας και διαχειρίζεται τη ροή μηνυμάτων.
    
    Args:
        brain_module: Το φορτωμένο module brain.py
        auth_module: Το φορτωμένο module auth.py (για logs)
        user_email: Το email του χρήστη για καταγραφή
    """
    st.header("⚡ Mastro Nek AI Assistant")
    
    # 1. Εμφάνιση Ιστορικού Μηνυμάτων
    # Χρησιμοποιούμε αμυντικό προγραμματισμό για να μην σκάσει αν η λίστα είναι None
    messages = st.session_state.get("messages", [])
    
    if not messages:
        st.info("👋 Γεια σου! Είμαι ο Mastro Nek AI. Ρώτησέ με για βλάβες, manuals ή ανταλλακτικά.")
    
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 2. Περιοχή Εισαγωγής (Input Area)
    # Το CSS στο main.py θα φροντίσει να είναι 'Sticky' στο κάτω μέρος
    user_prompt = st.chat_input("Περιγράψτε το πρόβλημα ή τον κωδικό βλάβης...")

    # 3. Sidebar Uploads (Mobile First Approach)
    # Τα uploads μπαίνουν στο sidebar για να μην πιάνουν χώρο στο chat
    with st.sidebar.expander("📎 Επισύναψη Αρχείων", expanded=False):
        uploaded_pdfs = st.file_uploader("Ανεβάστε PDF (Manuals)", type=["pdf"], accept_multiple_files=True, key="chat_pdf_uploader")
        uploaded_imgs = st.file_uploader("Ανεβάστε Φωτογραφίες", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="chat_img_uploader")
        
        if uploaded_pdfs or uploaded_imgs:
            st.success(f"Έτοιμα για αποστολή: {len(uploaded_pdfs or []) + len(uploaded_imgs or [])} αρχεία")

    # 4. Λογική Επεξεργασίας Μηνύματος
    if user_prompt:
        # A. Εμφάνιση μηνύματος χρήστη
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
            if uploaded_pdfs:
                st.markdown(f"*📎 Επισυνάφθηκαν {len(uploaded_pdfs)} PDF αρχεία*")
            if uploaded_imgs:
                st.markdown(f"*📸 Επισυνάφθηκαν {len(uploaded_imgs)} Εικόνες*")

        # B. Επεξεργασία από το AI
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            try:
                with st.spinner("🔄 Ανάλυση δεδομένων και εγχειριδίων..."):
                    if brain_module:
                        # Κλήση της συνάρτησης smart_solve του brain.py
                        # Περνάμε το ιστορικό για context
                        full_response = brain_module.smart_solve(
                            user_query=user_prompt,
                            uploaded_pdfs=uploaded_pdfs if uploaded_pdfs else [],
                            uploaded_imgs=uploaded_imgs if uploaded_imgs else [],
                            history=st.session_state.messages[:-1]
                        )
                    else:
                        full_response = "❌ **System Error:** Το Brain Module δεν είναι διαθέσιμο."
                        logger.critical("Brain module is missing during chat execution.")

                # C. Εμφάνιση απάντησης
                response_placeholder.markdown(full_response)
                
                # D. Αποθήκευση στο Session State
                st.session_state.messages.append({"role": "assistant", "content": full_response})

                # E. Καταγραφή στο Audit Log (αν υπάρχει το auth module)
                if auth_module:
                    auth_module.log_interaction(user_email, "Chat Query", user_prompt[:100])

            except Exception as e:
                error_msg = f"⚠️ **AI Execution Error:** {str(e)}"
                response_placeholder.error(error_msg)
                logger.error(f"Chat Error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": error_msg})