import streamlit as st
from services.sorter_logic import SorterService, ALLOWED_CATEGORIES, ALLOWED_TYPES, IRRELEVANT_OR_UNKNOWN_FOLDER, DUPLICATES_FOLDER, IGNORED_FOLDERS_TOP_LEVEL, MANUAL_REVIEW_FOLDER # ΝΕΟ: Εισαγωγή MANUAL_REVIEW_FOLDER
from core.language_pack import get_text # Rule 5
from core.db_connector import DatabaseConnector # For potential future admin updates
import logging # Rule 4
import pandas as pd
from datetime import datetime
from services.sync_service import SyncService # Rule 3

logger = logging.getLogger("Module_Organizer_UI") # Rule 4

def render(user):
    lang = st.session_state.get('lang', 'gr') # Rule 6, 5
    st.header(get_text('menu_organizer', lang)) # Rule 5
    
    st.markdown(f"""
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;'>
        {get_text('org_desc', lang)}
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    # Only Admin can use the organizer
    if user['role'] != 'admin':
        st.warning(get_text('org_admin_only', lang)) # Rule 5
        return

    # Initialize session state for sorter flags and results (Rule 6)
    if 'sorter_stop_flag' not in st.session_state: st.session_state['sorter_stop_flag'] = False
    if 'sorter_running' not in st.session_state: st.session_state['sorter_running'] = False
    if 'sorter_failed_files' not in st.session_state: st.session_state['sorter_failed_files'] = []
    if 'sorter_manual_review_files' not in st.session_state: st.session_state['sorter_manual_review_files'] = []
    if 'sorter_irrelevant_files' not in st.session_state: st.session_state['sorter_irrelevant_files'] = []
    if 'sorter_duplicate_files' not in st.session_state: st.session_state['sorter_duplicate_files'] = []
    if 'sorter_progress_data' not in st.session_state: st.session_state.sorter_progress_data = {"current": 0, "total": 0, "text": ""}
    if 'sorter_run_log' not in st.session_state: st.session_state.sorter_run_log = []
    if 'sorter_summary' not in st.session_state: st.session_state.sorter_summary = None
    if 'force_full_resort' not in st.session_state: st.session_state.force_full_resort = False # ΝΕΟ: Flag για πλήρη επανεπεξεργασία

    # --- Session state για περιήγηση αρχείων ---
    # Rule 6: Initialize navigation states
    sorter_service_instance = SorterService() # Instantiate SorterService to get root_id, etc. (Rule 3)
    if 'org_browse_level' not in st.session_state: st.session_state.org_browse_level = "categories"
    if 'org_current_folder_id' not in st.session_state: st.session_state.org_current_folder_id = sorter_service_instance.drive.root_id
    if 'org_folder_history' not in st.session_state: st.session_state.org_folder_history = []
    # Initialize these to None or specific default values
    if 'org_selected_category' not in st.session_state: st.session_state.org_selected_category = None
    if 'org_selected_brand' not in st.session_state: st.session_state.org_selected_brand = None
    if 'org_selected_model' not in st.session_state: st.session_state.org_selected_model = None
    if 'org_selected_type' not in st.session_state: st.session_state.org_selected_type = None

    sorter_service = sorter_service_instance # Use the already instantiated service.

    # --- Progress bar for live updates ---
    progress_bar = st.progress(st.session_state.sorter_progress_data["current"], text=st.session_state.sorter_progress_data["text"])

    def update_progress(current, text):
        st.session_state.sorter_progress_data["current"] = current
        st.session_state.sorter_progress_data["text"] = text
        progress_bar.progress(current, text)

    # --- Tabs for Organizer functionalities ---
    tab1, tab2, tab3, tab4 = st.tabs([ # Αναδιάταξη tabs
        get_text('org_tab_summary', lang), # Rule 5
        get_text('org_tab_browse', lang), # Rule 5
        get_text('org_tab_review', lang), # Rule 5
        get_text('org_tab_log', lang) # Rule 5
    ])

    with tab1: # Summary & Execution
        st.divider()
        # --- Εμφάνιση Συνοπτικών Στατιστικών ---
        if st.session_state.sorter_summary:
            summary = st.session_state.sorter_summary
            st.subheader(get_text('org_tab_summary', lang)) # Rule 5
            st.caption(f"{get_text('org_summary_last_run', lang)}: {summary.get('last_run_timestamp', 'N/A')}") # Rule 5
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric(get_text('org_summary_scanned', lang), summary.get('total_files_scanned', 0)) # Rule 5
            col2.metric(get_text('org_summary_sorted', lang), summary.get('total_successfully_sorted', 0)) # Rule 5
            col3.metric(get_text('org_summary_manual_review', lang), summary.get('total_moved_to_manual_review', 0)) # Rule 5
            col4.metric(get_text('org_summary_irrelevant', lang), summary.get('total_moved_to_irrelevant', 0)) # Rule 5
            col5.metric(get_text('org_summary_duplicates', lang), summary.get('total_moved_to_duplicates', 0)) # Rule 5

            if summary.get('total_successfully_sorted', 0) > 0:
                st.markdown("---")
                st.subheader(get_text('org_summary_categories', lang)) # Rule 5
                
                tab_cat, tab_brand, tab_type = st.tabs([get_text('org_summary_categories', lang), get_text('org_summary_brands', lang), get_text('org_summary_types', lang)]) # Rule 5
                
                with tab_cat:
                    if summary['category_counts']:
                        df_categories = pd.DataFrame(summary['category_counts'].items(), columns=[get_text('org_summary_categories', lang), get_text('org_summary_scanned', lang)]) # Rule 5
                        st.dataframe(df_categories.sort_values(by=get_text('org_summary_scanned', lang), ascending=False), use_container_width=True, hide_index=True)
                        st.bar_chart(df_categories.set_index(get_text('org_summary_categories', lang))) # Rule 5
                    else:
                        st.info(get_text('org_no_data_for_category', lang)) # Rule 5
                
                with tab_brand:
                    if summary['brand_counts']:
                        df_brands = pd.DataFrame(summary['brand_counts'].items(), columns=[get_text('org_summary_brands', lang), get_text('org_summary_scanned', lang)]) # Rule 5
                        st.dataframe(df_brands.sort_values(by=get_text('org_summary_scanned', lang), ascending=False), use_container_width=True, hide_index=True)
                        st.bar_chart(df_brands.set_index(get_text('org_summary_brands', lang))) # Rule 5
                    else:
                        st.info(get_text('org_no_data_for_brand', lang)) # Rule 5

                with tab_type:
                    if summary['type_counts']:
                        df_types = pd.DataFrame(summary['type_counts'].items(), columns=[get_text('org_summary_types', lang), get_text('org_summary_scanned', lang)]) # Rule 5
                        st.dataframe(df_types.sort_values(by=get_text('org_summary_scanned', lang), ascending=False), use_container_width=True, hide_index=True)
                        st.bar_chart(df_types.set_index(get_text('org_summary_types', lang))) # Rule 5
                    else:
                        st.info(get_text('org_no_data_for_type', lang)) # Rule 5

        st.markdown("---")
        st.subheader(get_text('org_tab_summary', lang)) # Rule 5
        
        st.session_state.force_full_resort = st.checkbox(
            get_text('org_force_full_rescan', lang) if 'org_force_full_rescan' in LANGUAGE_PACK else "Πλήρης Επανεξέταση Όλων των Αρχείων", # Rule 5
            value=st.session_state.force_full_resort, key="force_full_resort_checkbox" # Rule 6
        )
        st.caption(get_text('org_force_rescan_info', lang)) # Rule 5

        col_run, col_stop = st.columns(2)
        with col_run:
            if st.button(get_text('org_btn_start_sorter', lang), type="primary", use_container_width=True, disabled=st.session_state.sorter_running): # Rule 5
                st.session_state.sorter_running = True
                st.session_state.sorter_stop_flag = False # Reset stop flag
                st.session_state.sorter_run_log.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sorter started. Full Rescan: {st.session_state.force_full_resort}") # Rule 4
                st.rerun()
        with col_stop:
            if st.button(get_text('org_btn_stop_sorter', lang), type="secondary", use_container_width=True, disabled=not st.session_state.sorter_running): # Rule 5
                st.session_state.sorter_stop_flag = True # Set stop flag
                logger.info("AI Sorter stop flag set.") # Rule 4
                st.session_state.sorter_run_log.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sorter stop requested.") # Rule 4
                # No rerun here, let the loop check the flag and stop naturally.

        if st.session_state.sorter_running:
            st.info(get_text('org_sorter_running', lang)) # Rule 5
            
            try: # Rule 4
                # Run the sorter logic
                summary_result = sorter_service.run_sorter(
                    stop_flag=st.session_state, # Pass session_state to allow internal modification of stop_flag (Rule 6)
                    progress_callback=update_progress,
                    full_rescan=st.session_state.force_full_resort
                )
                st.session_state.sorter_summary = summary_result # Store summary
                st.session_state.sorter_running = False
                st.session_state.sorter_stop_flag = False
                if summary_result.get("status") == "canceled":
                    st.warning(get_text('org_sorter_canceled', lang)) # Rule 5
                    st.session_state.sorter_run_log.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sorter cancelled by user.") # Rule 4
                else:
                    st.success(get_text('org_sorter_complete', lang)) # Rule 5
                    st.session_state.sorter_run_log.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sorter completed. Summary: {summary_result}") # Rule 4
                st.rerun() # Rerun to update UI after completion
            except Exception as e:
                st.error(f"{get_text('org_sorter_fatal_error', lang).format(error=e)}") # Rule 5
                logger.critical(f"FATAL ERROR during AI Sorter run: {e}", exc_info=True) # Rule 4
                st.session_state.sorter_running = False
                st.session_state.sorter_stop_flag = False
                st.session_state.sorter_run_log.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sorter stopped with FATAL ERROR: {e}") # Rule 4
                st.rerun() # Rerun to update UI after error
        else:
            if st.session_state.sorter_summary:
                st.info(get_text('org_sorter_stopped', lang)) # Rule 5
            else:
                st.info(get_text('org_sorter_ready', lang) if 'org_sorter_ready' in LANGUAGE_PACK else "Ο AI Sorter είναι έτοιμος να ξεκινήσει.") # Rule 5

    with tab2: # File Browser
        st.subheader(get_text('org_tab_browse', lang)) # Rule 5
        st.markdown(f"**{get_text('org_browse_current_path', lang)}** `{st.session_state.org_current_folder_id}`") # Rule 5

        # Back button
        if st.session_state.org_folder_history and st.button(get_text('org_browse_back_btn', lang)): # Rule 5
            st.session_state.org_current_folder_id = st.session_state.org_folder_history.pop()
            st.rerun()

        try: # Rule 4
            current_folder_contents = sorter_service.drive.list_files_in_folder(st.session_state.org_current_folder_id) # Rule 7
            
            if not current_folder_contents:
                st.info(get_text('org_browse_empty', lang)) # Rule 5
            else:
                folders = sorted([item for item in current_folder_contents if item['mimeType'] == 'application/vnd.google-apps.folder'], key=lambda x: x['name'])
                files = sorted([item for item in current_folder_contents if item['mimeType'] != 'application/vnd.google-apps.folder'], key=lambda x: x['name'])

                if folders:
                    st.markdown(f"#### {get_text('org_browse_folders', lang)}") # Rule 5
                    for folder in folders:
                        if st.button(f"📁 {folder['name']}", key=f"folder_{folder['id']}"):
                            st.session_state.org_folder_history.append(st.session_state.org_current_folder_id)
                            st.session_state.org_current_folder_id = folder['id']
                            st.rerun()
                
                if files:
                    st.markdown(f"#### {get_text('org_browse_files', lang)}") # Rule 5
                    for file_item in files:
                        with st.container(border=True):
                            col_f1, col_f2 = st.columns([4, 1])
                            col_f1.markdown(f"📄 {file_item['name']}")
                            with col_f2:
                                if st.button(get_text('org_browse_download', lang), key=f"download_{file_item['id']}", use_container_width=True): # Rule 5
                                    st.link_button(get_text('org_browse_link', lang) if 'org_browse_link' in LANGUAGE_PACK else "🔗 Link", url=file_item['webViewLink'], key=f"link_{file_item['id']}", help="View in Drive", use_container_width=True) # Rule 5
                        
        except Exception as e:
            st.error(f"{get_text('general_ui_error', lang).format(error=e)}") # Rule 5
            logger.error(f"Error browsing files in Organizer: {e}", exc_info=True) # Rule 4

    with tab3: # Review / Errors
        st.subheader(get_text('org_tab_review', lang)) # Rule 5

        # Rule 6: Accessing session state lists
        manual_review_files = st.session_state.sorter_manual_review_files
        irrelevant_files = st.session_state.sorter_irrelevant_files
        duplicate_files = st.session_state.sorter_duplicate_files
        failed_files = st.session_state.sorter_failed_files

        # Display and actions for files needing manual review
        st.markdown(f"##### {get_text('org_review_pending', lang).format(count=len(manual_review_files))}") # Rule 5
        if manual_review_files:
            for file_data in manual_review_files:
                with st.container(border=True):
                    st.markdown(f"**{get_text('org_review_filename', lang)}:** {file_data['name']}") # Rule 5
                    st.markdown(f"**{get_text('org_review_reason', lang)}:** {file_data.get('reason', 'AI could not classify or extract text.')}") # Rule 5
                    
                    col_move, col_reprocess = st.columns(2)
                    with col_move:
                        # Manual move option (simplified for now, full UI would involve selecting target folder)
                        if st.button(get_text('org_review_btn_manual_move', lang), key=f"manual_move_{file_data['id']}", use_container_width=True): # Rule 5
                            st.info("Feature for manual move not fully implemented. Please use Google Drive directly.")
                    with col_reprocess:
                        if st.button(get_text('org_review_btn_reprocess', lang), key=f"reprocess_manual_{file_data['id']}", use_container_width=True): # Rule 5
                            st.warning("Reprocessing feature not yet implemented for individual files.")
        else:
            st.info(get_text('org_no_manual_review', lang) if 'org_no_manual_review' in LANGUAGE_PACK else "Δεν υπάρχουν αρχεία για χειροκίνητη αναθεώρηση.") # Rule 5

        # Display and actions for irrelevant files
        st.markdown(f"##### {get_text('org_review_irrelevant', lang).format(count=len(irrelevant_files))}") # Rule 5
        if irrelevant_files:
            for file_data in irrelevant_files:
                with st.container(border=True):
                    st.markdown(f"**{get_text('org_review_filename', lang)}:** {file_data['name']}") # Rule 5
                    st.markdown(f"**{get_text('org_review_reason', lang)}:** {file_data.get('reason', 'Classified as irrelevant by AI.')}") # Rule 5
                    # Add reprocess button or delete button if needed
        else:
            st.info(get_text('org_no_irrelevant', lang) if 'org_no_irrelevant' in LANGUAGE_PACK else "Δεν υπάρχουν άσχετα αρχεία.") # Rule 5
        
        # Display and actions for duplicate files
        st.markdown(f"##### {get_text('org_review_duplicates', lang).format(count=len(duplicate_files))}") # Rule 5
        if duplicate_files:
            for file_data in duplicate_files:
                with st.container(border=True):
                    st.markdown(f"**{get_text('org_review_filename', lang)}:** {file_data['name']}") # Rule 5
                    st.markdown(f"**{get_text('org_review_reason', lang)}:** {file_data.get('reason', 'Duplicate of an existing file.')}") # Rule 5
                    # Add reprocess button or delete button if needed
        else:
            st.info(get_text('org_no_duplicates', lang) if 'org_no_duplicates' in LANGUAGE_PACK else "Δεν υπάρχουν διπλότυπα αρχεία.") # Rule 5

        # Display files that failed to process (e.g., PDF corruption, AI error)
        st.markdown(f"##### {get_text('org_review_failed', lang).format(count=len(failed_files))}") # Rule 5
        if failed_files:
            for file_data in failed_files:
                with st.container(border=True):
                    st.markdown(f"**{get_text('org_review_filename', lang)}:** {file_data['name']}") # Rule 5
                    st.markdown(f"**{get_text('org_review_reason', lang)}:** {file_data.get('error', 'Unknown processing error.')}") # Rule 5
        else:
            st.info(get_text('org_no_failed', lang) if 'org_no_failed' in LANGUAGE_PACK else "Δεν υπάρχουν αρχεία με σφάλμα ταξινόμησης.") # Rule 5


    with tab4: # Full Log
        st.subheader(get_text('org_log_entries', lang)) # Rule 5
        if st.session_state.sorter_run_log:
            for entry in st.session_state.sorter_run_log:
                st.code(entry)
        else:
            st.info(get_text('org_log_empty', lang)) # Rule 5