"""
MODULE: Search Engine System
VERSION: 2.1.0 (TITANIUM)
DESCRIPTION: Μηχανή αναζήτησης στα Manuals της μνήμης (Session State).
"""

import streamlit as st
import logging
from typing import List, Dict, Any

logger = logging.getLogger("Module_Search")

def _get_badge_color(meta_type: str) -> str:
    """Helper Function: Επιστρέφει χρώμα ανάλογα με τον τύπο εγγράφου."""
    if not meta_type: return "gray"
    meta = meta_type.upper()
    if "ERROR" in meta: return "red"
    if "SERVICE" in meta: return "orange"
    if "USER" in meta: return "green"
    if "INSTALL" in meta: return "blue"
    return "gray"

def render_search_page(library_data: List[Dict[str, Any]]) -> None:
    """
    Εμφανίζει τη σελίδα αναζήτησης.
    Args:
        library_data: Η λίστα με τα manuals από το st.session_state['library_cache']
    """
    st.header("🔍 Global Library Search")
    st.caption("Enterprise Indexing System | Google Drive Integration")

    # 1. Έλεγχος Δεδομένων
    if not library_data:
        st.warning("⚠️ Η βιβλιοθήκη είναι κενή.")
        st.info("Το σύστημα προσπαθεί να συγχρονίσει... Αν επιμένει, ειδοποιήστε τον Admin.")
        return

    # 2. Στατιστικά (Collapsible)
    with st.expander(f"📊 Στατιστικά Ευρετηρίου ({len(library_data)} έγγραφα)", expanded=False):
        unique_brands = sorted(list(set(item.get('brand', 'Unknown') for item in library_data)))
        st.write(f"**Μάρκες:** {', '.join(unique_brands[:10])}...")

    # 3. Μπάρα Αναζήτησης
    query = st.text_input("🔎 Αναζήτηση (Μάρκα, Μοντέλο, Κωδικός Error)...", 
                         placeholder="π.χ. Daikin Altherma J3 Error").strip().lower()

    # 4. Λογική Αναζήτησης (AND Logic)
    results = []
    if query:
        search_terms = query.split()
        for item in library_data:
            # Δημιουργία ενός "Searchable String" από όλα τα πεδία
            full_text = f"{item.get('brand', '')} {item.get('model', '')} {item.get('name', '')} {item.get('error_codes', '')}".lower()
            
            # Έλεγχος: Όλοι οι όροι πρέπει να υπάρχουν
            if all(term in full_text for term in search_terms):
                results.append(item)
        
        logger.info(f"User searched for '{query}' - Found {len(results)} matches.")
    else:
        # Αν δεν γράψει τίποτα, δείχνουμε τα πρόσφατα
        results = library_data[:5]
        st.caption("Πρόσφατα καταχωρημένα αρχεία:")

    # 5. Εμφάνιση Αποτελεσμάτων
    if not results and query:
        st.error("Δεν βρέθηκαν αποτελέσματα.")
    else:
        for res in results:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                
                # Στήλη 1: Brand & Badge
                with c1:
                    st.markdown(f"**{res.get('brand', 'Unknown')}**")
                    color = _get_badge_color(res.get('meta_type', 'MANUAL'))
                    st.markdown(f":{color}[{res.get('meta_type', 'DOC')}]")

                # Στήλη 2: Λεπτομέρειες
                with c2:
                    st.markdown(f"📄 **{res.get('model', 'General Model')}**")
                    st.caption(f"Filename: {res.get('name')}")
                
                # Στήλη 3: Κουμπί
                with c3:
                    link = res.get('link')
                    # Fallback link generation
                    if not link and res.get('file_id') and res.get('file_id') != 'Unknown':
                        link = f"https://drive.google.com/file/d/{res['file_id']}/view"
                    
                    if link:
                        st.link_button("📂 Άνοιγμα", link, use_container_width=True)
                    else:
                        st.caption("No Link Available")