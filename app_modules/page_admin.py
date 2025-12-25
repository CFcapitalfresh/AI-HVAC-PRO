import streamlit as st
import subprocess
import sys
import time
import os

try:
    from version import VERSION
except ImportError:
    VERSION = "Unknown"

def show_admin_page():
    st.header("⚙️ Διαχείριση Συστήματος")
    
    st.info(f"Τρέχουσα Έκδοση Συστήματος: **{VERSION}**")
    
    st.subheader("🔄 Αναβάθμιση Λογισμικού")
    st.write("Πάτα το κουμπί για να ελέγξεις αν υπάρχει νεότερη έκδοση στο GitHub.")

    if st.button("Έλεγχος & Αναβάθμιση Τώρα"):
        with st.spinner("Γίνεται επικοινωνία με τον Server (GitHub)..."):
            try:
                # Εντολή git pull για τράβηγμα αλλαγών
                result = subprocess.run(["git", "pull"], capture_output=True, text=True)
                
                if "Already up to date" in result.stdout:
                    st.success("✅ Το σύστημα είναι ενημερωμένο! Δεν χρειάζεται αλλαγή.")
                else:
                    st.success("✅ Η αναβάθμιση ολοκληρώθηκε επιτυχώς!")
                    st.code(result.stdout)
                    st.warning("⚠️ Το πρόγραμμα θα επανεκκινήσει σε 3 δευτερόλεπτα...")
                    time.sleep(3)
                    st.rerun() # Επανεκκίνηση για να πάρει τις αλλαγές
                    
            except Exception as e:
                st.error(f"❌ Υπήρξε σφάλμα κατά την αναβάθμιση: {e}")
                st.write("Δοκίμασε να κάνεις Sync manual από το VS Code.")

    st.divider()
    st.subheader("🛠️ Εργαλεία Βάσης")
    if st.button("Επιδιόρθωση Βάσης Δεδομένων (Self-Heal)"):
        # Εδώ καλούμε τη συνάρτηση από το smart_library
        from smart_library import auto_fix_database
        auto_fix_database('drive_index.json')
        st.success("Ο έλεγχος και η επιδιόρθωση ολοκληρώθηκαν!")