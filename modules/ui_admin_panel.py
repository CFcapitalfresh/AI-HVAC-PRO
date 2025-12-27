import streamlit as st
from core.db_connector import DatabaseConnector
import pandas as pd

def render(user):
    st.title("⚙️ Κέντρο Διαχείρισης (Admin Panel)")
    
    # Φόρτωση Χρηστών
    users = DatabaseConnector.fetch_data("Users")
    if users.empty:
        st.warning("Δεν βρέθηκαν χρήστες.")
        return

    # --- 1. ΑΙΤΗΜΑΤΑ ΓΙΑ ΕΓΚΡΙΣΗ ---
    st.subheader("🔔 Εκκρεμή Αιτήματα (Pending)")
    
    # Βρίσκουμε ποιοι είναι 'pending'
    pending_mask = users['role'] == 'pending'
    pending_users = users[pending_mask]

    if pending_users.empty:
        st.success("✅ Όλα ήσυχα! Κανένα νέο αίτημα.")
    else:
        for index, row in pending_users.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"👤 **{row['name']}**")
                c1.caption(f"📧 {row['email']} | 📅 {row['created_at']}")
                
                # Κουμπί Ενεργοποίησης
                if c2.button("✅ Ενεργοποίηση", key=f"act_{index}", use_container_width=True):
                    # Αλλαγή στο τοπικό dataframe
                    users.at[index, 'role'] = 'active'
                    # Αποθήκευση στο Excel
                    if DatabaseConnector.update_all_data("Users", users):
                        st.success(f"Ο χρήστης {row['name']} ενεργοποιήθηκε!")
                        st.rerun()
                    else:
                        st.error("Σφάλμα αποθήκευσης.")

                # Κουμπί Διαγραφής
                if c3.button("🗑️ Διαγραφή", key=f"del_{index}", use_container_width=True):
                    # Διαγραφή γραμμής
                    users = users.drop(index)
                    if DatabaseConnector.update_all_data("Users", users):
                        st.warning("Το αίτημα διαγράφηκε.")
                        st.rerun()

    st.divider()

    # --- 2. ΟΛΟΙ ΟΙ ΧΡΗΣΤΕΣ ---
    with st.expander("👥 Προβολή Όλων των Χρηστών"):
        st.dataframe(users)
        st.caption("Εδώ βλέπετε όλους τους εγγεγραμμένους χρήστες.")