import streamlit as st
from core.db_connector import DatabaseConnector
from core.language_pack import get_text
import pandas as pd

def render(user):
    lang = st.session_state.get('lang', 'gr')
    st.title(get_text('admin_title', lang))
    
    # Φόρτωση Χρηστών
    users = DatabaseConnector.fetch_data("Users")
    if users.empty:
        st.warning(get_text('admin_no_users', lang))
        return

    # --- 1. ΑΙΤΗΜΑΤΑ ΓΙΑ ΕΓΚΡΙΣΗ ---
    st.subheader(get_text('admin_pending', lang))
    
    # Βρίσκουμε ποιοι είναι 'pending'
    pending_mask = users['role'] == 'pending'
    pending_users = users[pending_mask]

    if pending_users.empty:
        st.success(get_text('admin_no_pending', lang))
    else:
        for index, row in pending_users.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"👤 **{row['name']}**")
                c1.caption(f"📧 {row['email']} | 📅 {row['created_at']}")
                
                # Κουμπί Ενεργοποίησης
                if c2.button(get_text('admin_btn_activate', lang), key=f"act_{index}", use_container_width=True):
                    users.at[index, 'role'] = 'active'
                    if DatabaseConnector.update_all_data("Users", users):
                        st.success(f"{get_text('admin_msg_active', lang)} ({row['name']})")
                        st.rerun()
                    else:
                        st.error("Error Saving.")

                # Κουμπί Διαγραφής
                if c3.button(get_text('admin_btn_delete', lang), key=f"del_{index}", use_container_width=True):
                    users = users.drop(index)
                    if DatabaseConnector.update_all_data("Users", users):
                        st.warning(get_text('admin_msg_del', lang))
                        st.rerun()

    st.divider()

    # --- 2. ΟΛΟΙ ΟΙ ΧΡΗΣΤΕΣ ---
    with st.expander(get_text('admin_all_users', lang)):
        st.dataframe(users)
        st.caption(get_text('admin_all_users_cap', lang))