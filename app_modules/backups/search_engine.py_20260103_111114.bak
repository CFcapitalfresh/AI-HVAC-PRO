"""
MODULE: Search Engine System
VERSION: 2.1.0 (TITANIUM)
DESCRIPTION: Μηχανή αναζήτησης στα Manuals της μνήμης (Session State).
ENHANCEMENT: Added Speech-to-Text Button Placeholder.
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
    if "TECHNICAL" in meta: return "violet"
    if "SPARE" in meta: return "yellow"
    if "OTHER" in meta or "GENERAL" in meta or "DOC" in meta: return "gray"
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
        unique_brands = sorted(list(set(item.get('brand', 'Unknown') for item in library_data if item.get('brand', 'Unknown') != 'UNKNOWN')))
        st.write(f"**Μάρκες:** {', '.join(unique_brands[:10])}{'...' if len(unique_brands) > 10 else ''}")
        unique_types = sorted(list(set(item.get('meta_type', 'DOC') for item in library_data if item.get('meta_type', 'DOC') != 'DOC')))
        st.write(f"**Τύποι Εγγράφων:** {', '.join(unique_types[:10])}{'...' if len(unique_types) > 10 else ''}")
        # Add filtering options if desired in future, e.g., multiselect for brand/type

    # 3. Μπάρα Αναζήτησης με Φωνητική Εντολή
    search_col, stt_col = st.columns([8, 1])
    with search_col:
        query = st.text_input("🔎 Αναζήτηση (Μάρκα, Μοντέλο, Κωδικός Error)...", 
                             placeholder="π.χ. Daikin Altherma J3 Error", key="library_search_input").strip().lower()
    
    with stt_col:
        st.write("") # Για ευθυγράμμιση
        st.write("")
        # Rule 1: Microphone/Audio button
        if st.button("🎤", key="stt_button"):
            # Placeholder for actual Speech-to-Text integration
            st.info("🎧 Λειτουργία φωνητικής αναζήτησης υπό ανάπτυξη...")
            # In a real application, this would call a STT service
            # For example: audio_input = get_audio_input()
            #              text_output = speech_to_text(audio_input)
            #              st.session_state.library_search_input = text_output
            #              st.experimental_rerun() # Or manually update the text_input widget if possible

    # 4. Λογική Αναζήτησης (AND Logic) - Τώρα χρησιμοποιεί τα εμπλουτισμένα μεταδεδομένα
    results = []
    if query:
        search_terms = query.split()
        for item in library_data:
            # Δημιουργία ενός "Searchable String" από όλα τα πεδία
            # Χρησιμοποιούμε τα νέα πεδία: brand, model, meta_type, error_codes
            full_text = (
                f"{item.get('brand', '')} "
                f"{item.get('model', '')} "
                f"{item.get('meta_type', '')} "
                f"{item.get('name', '')} " # Full path name
                f"{item.get('original_name', '')} " # Original filename
                f"{item.get('error_codes', '')}" # If error codes are added to metadata
            ).lower()
            
            # Έλεγχος: Όλοι οι όροι πρέπει να υπάρχουν
            if all(term in full_text for term in search_terms):
                results.append(item)
        
        logger.info(f"User searched for '{query}' - Found {len(results)} matches.")
    else:
        # Αν δεν γράψει τίποτα, δείχνουμε τα πρόσφατα
        # Using 'name' for consistent sorting if no other timestamp is available
        results = sorted(library_data, key=lambda x: x.get('name', ''), reverse=True)[:10] 
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
                    st.markdown(f"**{res.get('brand', 'Unknown').title()}**") # Title case for better display
                    color = _get_badge_color(res.get('meta_type', 'DOC'))
                    st.markdown(f":{color}[{res.get('meta_type', 'DOC').replace('_', ' ')}]") # Replace underscore for readability

                # Στήλη 2: Λεπτομέρειες
                with c2:
                    st.markdown(f"📄 **{res.get('model', 'General Model').title()}**")
                    st.caption(f"Filename: {res.get('original_name', res.get('name'))}") # Display original filename
                    if res.get('error_codes'):
                        st.text(f"Error Code: {res.get('error_codes')}")
                
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