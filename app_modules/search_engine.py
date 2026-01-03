"""
MODULE: Search Engine System
VERSION: 2.2.0 (TITANIUM)
DESCRIPTION: Μηχανή αναζήτησης στα Manuals της μνήμης (Session State).
ENHANCEMENT: Integrated Speech-to-Text Button.
"""

import streamlit as st
import logging
from typing import List, Dict, Any
from core.language_pack import get_text

# Import Speech-to-Text library with graceful error handling (Rule 1)
try:
    from streamlit_mic_recorder import mic_recorder
    # Placeholder for actual STT service integration
    # For a real application, you'd integrate with Google Speech-to-Text, AWS Transcribe, etc.
    # For now, we'll simulate text output from a fixed string or a simple placeholder.
    # from some_stt_service import SpeechToTextService 
    # stt_service = SpeechToTextService()
except ImportError:
    mic_recorder = None
    # stt_service = None

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
    lang = st.session_state.get('lang', 'gr')

    st.header(get_text('menu_library', lang)) # The UI Search module should set its own header
    st.caption("Enterprise Indexing System | Google Drive Integration")

    # 1. Έλεγχος Δεδομένων
    if not library_data:
        st.warning(get_text('search_library_empty_warning', lang))
        st.info(get_text('search_library_sync_info', lang))
        return

    # 2. Στατιστικά (Collapsible)
    with st.expander(get_text('search_stats_expander', lang).format(count=len(library_data)), expanded=False):
        unique_brands = sorted(list(set(item.get('brand', 'Unknown') for item in library_data if item.get('brand', 'Unknown') != 'UNKNOWN')))
        st.write(f"**{get_text('search_brands', lang)}:** {', '.join(unique_brands[:10])}{'...' if len(unique_brands) > 10 else ''}")
        unique_types = sorted(list(set(item.get('meta_type', 'DOC') for item in library_data if item.get('meta_type', 'DOC') != 'DOC')))
        st.write(f"**{get_text('search_doc_types', lang)}:** {', '.join(unique_types[:10])}{'...' if len(unique_types) > 10 else ''}")

    # 3. Μπάρα Αναζήτησης με Φωνητική Εντολή
    search_col, stt_col = st.columns([8, 1])
    
    # Initialize search input text in session state if not present (Rule 6)
    if "library_search_input_text" not in st.session_state:
        st.session_state.library_search_input_text = ""

    with search_col:
        query = st.text_input("🔎 Αναζήτηση (Μάρκα, Μοντέλο, Κωδικός Error)...", 
                             placeholder=get_text('search_input_ph', lang), 
                             key="library_search_input",
                             value=st.session_state.library_search_input_text).strip().lower()
        # Update session state with the current text input value
        st.session_state.library_search_input_text = query
    
    with stt_col:
        st.write("") # Για ευθυγράμμιση
        st.write("")
        # Rule 1: Microphone/Audio button
        if mic_recorder:
            audio_bytes = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key="search_stt_button")
            if audio_bytes:
                st.info(get_text('voice_stt_processing', lang))
                try:
                    # Placeholder for actual Speech-to-Text integration
                    # For demonstration, we simulate an STT response.
                    # In a real app, this would be an API call to a STT service.
                    simulated_stt_text = "Daikin Error E3" # Replace with actual STT output
                    # if stt_service:
                    #    text_output = stt_service.convert(audio_bytes)
                    # else:
                    #    text_output = simulated_stt_text
                    
                    st.session_state.library_search_input_text = simulated_stt_text.lower() # Update the search input
                    logger.info(f"STT recognized: '{st.session_state.library_search_input_text}'")
                    st.rerun() # Re-run to update search input field and re-trigger search
                except Exception as e:
                    st.error(get_text('voice_stt_error', lang).format(error=str(e)))
                    logger.error(f"Error during STT processing in search: {e}", exc_info=True)
        else:
            st.button("🎤", key="stt_button_placeholder_search")
            st.info(get_text('search_voice_info', lang))


    # 4. Λογική Αναζήτησης (AND Logic) - Τώρα χρησιμοποιεί τα εμπλουτισμένα μεταδεδομένα
    results = []
    # Use the value from the text input, or from the mic recorder if it updated the state
    search_query_final = st.session_state.get("library_search_input_text", "").strip().lower()

    if search_query_final:
        search_terms = search_query_final.split()
        for item in library_data:
            # Δημιουργία ενός "Searchable String" από όλα τα πεδία
            # Χρησιμοποιούμε τα νέα πεδία: brand, model, meta_type, error_codes
            full_text = (
                f"{item.get('brand', '')} "
                f"{item.get('model', '')} "
                f"{item.get('meta_type', '')} "
                f"{item.get('name', '')} " # Full path name from Drive
                f"{item.get('original_name', '')} " # Original filename
                f"{item.get('error_codes', '')}" # If error codes are added to metadata
            ).lower()
            
            # Έλεγχος: Όλοι οι όροι πρέπει να υπάρχουν
            if all(term in full_text for term in search_terms):
                results.append(item)
        logger.info(f"User searched for '{search_query_final}' - Found {len(results)} matches.")
    else:
        # Αν δεν γράψει τίποτα, δείχνουμε τα πρόσφατα
        # Sort by file_id for consistent "recent" order if no other timestamp is available
        results = sorted(library_data, key=lambda x: x.get('file_id', ''))[:10] 
        st.caption(get_text('search_recent_files', lang))

    # 5. Εμφάνιση Αποτελεσμάτων
    if not results and search_query_final:
        st.error(get_text('search_no_results', lang))
    else:
        st.success(get_text('search_docs_found', lang).format(count=len(results)))
        for res in results:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                
                # Στήλη 1: Brand & Badge
                with c1:
                    st.markdown(f"**{res.get('brand', 'Unknown')}**")
                    color = _get_badge_color(res.get('meta_type', 'DOC'))
                    st.markdown(f":{color}[{res.get('meta_type', 'DOC')}]")

                # Στήλη 2: Λεπτομέρειες
                with c2:
                    st.markdown(f"📄 **{res.get('model', 'General Model')}**")
                    st.caption(f"{get_text('search_file_name', lang)}: {res.get('original_name', res.get('name'))}")
                    if res.get('error_codes'):
                        st.markdown(f"**Error Codes:** {res['error_codes']}")
                
                # Στήλη 3: Κουμπιά
                with c3:
                    if st.button(get_text('search_view_manual', lang), key=f"view_{res['file_id']}", use_container_width=True):
                        # Άνοιγμα σε νέο tab
                        st.markdown(f"<a href='{res['link']}' target='_blank' style='text-decoration: none;'></a>", unsafe_allow_html=True)
                        st.link_button(get_text('search_view_manual', lang), res['link'], help=f"Open {res['original_name']} in Google Drive", type="secondary", use_container_width=True)
                    
                    # ΝΕΟ: Κουμπί Λήψης (Download)
                    if st.button(get_text('search_download_manual', lang), key=f"download_{res['file_id']}", use_container_width=True):
                        try:
                            drive_manager = st.session_state.get('drive_manager_instance')
                            if not drive_manager:
                                from core.drive_manager import DriveManager
                                drive_manager = DriveManager()
                                st.session_state['drive_manager_instance'] = drive_manager # Cache it
                            
                            file_content_stream = drive_manager.download_file_content(res['file_id'])
                            if file_content_stream:
                                st.download_button(
                                    label=get_text('search_download_manual', lang),
                                    data=file_content_stream.getvalue(),
                                    file_name=res.get('original_name', f"manual_{res['file_id']}.pdf"),
                                    mime=res.get('mime', 'application/octet-stream'),
                                    key=f"dl_content_{res['file_id']}"
                                )
                                logger.info(f"User downloaded file: {res['original_name']} ({res['file_id']})")
                            else:
                                st.error(get_text('search_download_error', lang).format(error="No content found."))
                        except Exception as e:
                            logger.error(f"Error downloading file {res['file_id']}: {e}", exc_info=True)
                            st.error(get_text('search_download_error', lang).format(error=str(e)))