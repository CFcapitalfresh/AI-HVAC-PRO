import streamlit as st
import json

INDEX_FILE = "drive_index.json"

def show_search_page():
    st.header("🔍 Έξυπνη Αναζήτηση Manual")
    
    # Φόρτωση δεδομένων
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        st.warning("Η βιβλιοθήκη είναι κενή. Τρέξτε πρώτα τη συντήρηση.")
        return

    # Πεδίο αναζήτησης
    query = st.text_input("Αναζήτηση (π.χ. Daikin, Midea, Error Code)...").lower()
    
    if query:
        # Φιλτράρισμα με βάση το όνομα, τη μάρκα ή το μοντέλο
        results = [
            item for item in data 
            if query in item.get('name', '').lower() or 
               query in item.get('brand', '').lower() or 
               query in item.get('model', '').lower()
        ]
        
        st.write(f"✅ Βρέθηκαν {len(results)} αποτελέσματα:")
        
        for res in results:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.write(f"**Μάρκα:** {res['brand']}")
                col2.write(f"**Μοντέλο:** {res['model']}")
                url = f"https://drive.google.com/file/d/{res['id']}/view"
                col3.link_button("📄 Άνοιγμα", url)
    else:
        st.info("Πληκτρολογήστε κάτι παραπάνω για να ξεκινήσει η αναζήτηση.")