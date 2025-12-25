import streamlit as st
import json
import drive

INDEX_FILE = "drive_index.json"

def show_review_page():
    st.header("🛠️ Διόρθωση Unknown Αρχείων")
    
    # Φόρτωση δεδομένων
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        st.error("Δεν βρέθηκε το αρχείο ευρετηρίου.")
        return

    # Φιλτράρισμα μόνο για όσα θέλουν έλεγχο
    needs_review = [item for item in data if item.get("status") == "needs_review" or item.get("brand") == "Unknown"]
    
    if not needs_review:
        st.success("🎉 Όλα τα αρχεία είναι ταξινομημένα σωστά!")
        return

    st.write(f"Υπάρχουν {len(needs_review)} αρχεία που χρειάζονται τη ματιά σας.")

    for i, item in enumerate(needs_review):
        with st.expander(f"📄 {item['name']}"):
            new_brand = st.text_input("Σωστή Μάρκα", key=f"brand_{i}").strip().title()
            new_model = st.text_input("Σωστό Μοντέλο", value=item['model'], key=f"model_{i}")
            
            if st.button("Αποθήκευση & Μετακίνηση", key=f"btn_{i}"):
                if new_brand and new_brand != "Unknown":
                    # 1. Σύνδεση με Drive για μετακίνηση
                    service = drive.get_service()
                    
                    # Εύρεση ή δημιουργία φακέλου μάρκας
                    q = f"name = '{new_brand}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                    res = service.files().list(q=q).execute()
                    target_id = res['files'][0]['id'] if res.get('files') else service.files().create(body={'name': new_brand, 'mimeType': 'application/vnd.google-apps.folder'}, fields='id').execute().get('id')
                    
                    # Μετακίνηση αρχείου
                    file_info = service.files().get(fileId=item['id'], fields='parents').execute()
                    service.files().update(fileId=item['id'], addParents=target_id, removeParents=",".join(file_info.get('parents', []))).execute()
                    
                    # 2. Ενημέρωση JSON
                    for d in data:
                        if d['id'] == item['id']:
                            d['brand'] = new_brand
                            d['model'] = new_model
                            d['status'] = 'verified'
                    
                    with open(INDEX_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    
                    st.success(f"Το αρχείο μετακινήθηκε στον φάκελο {new_brand}!")
                    st.rerun()