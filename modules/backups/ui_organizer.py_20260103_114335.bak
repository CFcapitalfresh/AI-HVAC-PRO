import streamlit as st
from services.sorter_logic import SorterService, ALLOWED_CATEGORIES, ALLOWED_TYPES, IRRELEVANT_OR_UNKNOWN_FOLDER, DUPLICATES_FOLDER, IGNORED_FOLDERS_TOP_LEVEL, MANUAL_REVIEW_FOLDER # ΝΕΟ: Εισαγωγή MANUAL_REVIEW_FOLDER
from core.language_pack import get_text
from core.db_connector import DatabaseConnector # For potential future admin updates
import logging
import pandas as pd
from datetime import datetime
from services.sync_service import SyncService 

logger = logging.getLogger("Module_Organizer_UI")

def render(user):
    lang = st.session_state.get('lang', 'gr')
    st.header(get_text('menu_organizer', lang))
    
    st.markdown(f"""
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;'>
        {get_text('org_desc', lang)}
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    # Only Admin can use the organizer
    if user['role'] != 'admin':
        st.warning("You must be an Administrator to use the AI Organizer.")
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
    if 'org_browse_level' not in st.session_state: st.session_state.org_browse_level = "categories"
    if 'org_current_folder_id' not in st.session_state: st.session_state.org_current_folder_id = SorterService().drive.root_id
    if 'org_folder_history' not in st.session_state: st.session_state.org_folder_history = []
    
    sorter_service = SorterService() # Instantiate SorterService

    # --- Tabs for Organizer functionalities ---
    tab1, tab2, tab3, tab4 = st.tabs([ # Αναδιάταξη tabs
        get_text('org_tab_summary', lang), 
        get_text('org_tab_browse', lang), 
        get_text('org_tab_review', lang), 
        get_text('org_tab_log', lang)
    ])

    with tab1: # Summary & Execution
        st.divider()
        # --- Εμφάνιση Συνοπτικών Στατιστικών ---
        if st.session_state.sorter_summary:
            summary = st.session_state.sorter_summary
            st.subheader("📊 Σύνοψη Τελευταίας Εκτέλεσης")
            st.caption(f"{get_text('org_summary_last_run', lang)}: {summary.get('last_run_timestamp', 'N/A')}")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric(get_text('org_summary_scanned', lang), summary.get('total_files_scanned', 0))
            col2.metric(get_text('org_summary_sorted', lang), summary.get('total_successfully_sorted', 0))
            col3.metric(get_text('org_summary_manual_review', lang), summary.get('total_moved_to_manual_review', 0))
            col4.metric(get_text('org_summary_irrelevant', lang), summary.get('total_moved_to_irrelevant', 0))
            col5.metric(get_text('org_summary_duplicates', lang), summary.get('total_moved_to_duplicates', 0))

            if summary.get('total_successfully_sorted', 0) > 0:
                st.markdown("---")
                st.subheader(get_text('org_summary_categories', lang))
                
                tab_cat, tab_brand, tab_type = st.tabs([get_text('org_summary_categories', lang), get_text('org_summary_brands', lang), get_text('org_summary_types', lang)])
                
                with tab_cat:
                    if summary['category_counts']:
                        df_categories = pd.DataFrame(summary['category_counts'].items(), columns=[get_text('org_summary_categories', lang), get_text('org_summary_scanned', lang)])
                        st.dataframe(df_categories.sort_values(by=get_text('org_summary_scanned', lang), ascending=False), use_container_width=True, hide_index=True)
                        st.bar_chart(df_categories.set_index(get_text('org_summary_categories', lang)))
                    else:
                        st.info(get_text('org_no_data_for_category', lang))
                
                with tab_brand:
                    if summary['brand_counts']:
                        df_brands = pd.DataFrame(summary['brand_counts'].items(), columns=[get_text('org_summary_brands', lang), get_text('org_summary_scanned', lang)])
                        st.dataframe(df_brands.sort_values(by=get_text('org_summary_scanned', lang), ascending=False), use_container_width=True, hide_index=True)
                        st.bar_chart(df_brands.set_index(get_text('org_summary_brands', lang)))
                    else:
                        st.info(get_text('org_no_data_for_brand', lang))

                with tab_type:
                    if summary['type_counts']:
                        df_types = pd.DataFrame(summary['type_counts'].items(), columns=[get_text('org_summary_types', lang), get_text('org_summary_scanned', lang)])
                        st.dataframe(df_types.sort_values(by=get_text('org_summary_scanned', lang), ascending=False), use_container_width=True, hide_index=True)
                        st.bar_chart(df_types.set_index(get_text('org_summary_types', lang)))
                    else:
                        st.info(get_text('org_no_data_for_type', lang))

        st.markdown("---")
        # --- Εκκίνηση / Διακοπή Οργανωτή ---
        st.subheader("⚙️ Έλεγχος Λειτουργίας")

        # Force Full Rescan Option (Rule 3)
        force_rescan = st.checkbox(get_text('org_force_rescan_checkbox', lang), key="force_full_resort")
        if force_rescan:
            st.warning(get_text('org_force_rescan_warning', lang))

        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button(get_text('org_start_button', lang), use_container_width=True, type="primary", disabled=st.session_state.sorter_running):
                st.session_state.sorter_running = True
                st.session_state.sorter_stop_flag = False
                st.session_state.sorter_run_log = [] # Clear previous run log
                st.session_state.sorter_failed_files = []
                st.session_state.sorter_manual_review_files = []
                st.session_state.sorter_irrelevant_files = []
                st.session_state.sorter_duplicate_files = []

                progress_bar_placeholder = st.empty()
                progress_text_placeholder = st.empty()
                progress_bar = progress_bar_placeholder.progress(0)

                with st.status(get_text('org_running_msg', lang), expanded=True) as status:
                    try:
                        summary_result, log_entries = sorter_service.run_sorter(
                            progress_bar, 
                            progress_text_placeholder, 
                            'sorter_stop_flag', 
                            force_full_rescan=st.session_state.force_full_resort
                        )
                        st.session_state.sorter_summary = summary_result
                        st.session_state.sorter_run_log.extend(log_entries)
                        st.session_state.sorter_failed_files = summary_result['failed_files']
                        st.session_state.sorter_manual_review_files = summary_result['manual_review_files']
                        st.session_state.sorter_irrelevant_files = summary_result['irrelevant_files']
                        st.session_state.sorter_duplicate_files = summary_result['duplicate_files']
                        status.update(label=get_text('org_stopped_msg', lang), state="complete", expanded=False)
                        st.success("Διαδικασία ολοκληρώθηκε!")
                        SyncService().scan_library() # Re-sync library after sorting (Rule 3)
                        st.rerun() # Refresh UI
                    except Exception as e:
                        logger.error(f"AI Sorter execution failed: {e}", exc_info=True) # Rule 4
                        st.session_state.sorter_run_log.append(f"❌ CRITICAL ERROR: {e}")
                        status.update(label=f"Σφάλμα: {e}", state="error", expanded=True)
                        st.error(f"{get_text('org_error_occurred', lang).format(error=e)}")
                    finally:
                        st.session_state.sorter_running = False
                        st.session_state.sorter_stop_flag = False # Reset stop flag

        with col_stop:
            if st.button(get_text('org_stop_button', lang), use_container_width=True, disabled=not st.session_state.sorter_running):
                st.session_state.sorter_stop_flag = True
                st.warning(get_text('org_stopped_msg', lang))
                logger.info("AI Sorter stop flag set.")

    with tab2: # File Browser
        st.subheader(get_text('org_tab_browse', lang))
        st.caption(f"{get_text('org_browse_current_path', lang)} {st.session_state.org_current_folder_id}")

        col_back, col_refresh, _ = st.columns([1, 1, 3])
        with col_back:
            if st.button(get_text('org_browse_back', lang), disabled=not st.session_state.org_folder_history):
                st.session_state.org_current_folder_id = st.session_state.org_folder_history.pop()
                st.rerun()
        with col_refresh:
            if st.button(get_text('org_browse_refresh', lang)):
                # Clear children cache to force re-fetch
                if 'org_folder_children_cache' in st.session_state:
                    del st.session_state.org_folder_children_cache
                st.rerun()

        # Cache folder children (Rule 6)
        if 'org_folder_children_cache' not in st.session_state or \
           st.session_state.org_folder_children_cache.get('folder_id') != st.session_state.org_current_folder_id:
            try:
                st.session_state.org_folder_children_cache = {
                    'folder_id': st.session_state.org_current_folder_id,
                    'children': sorter_service.drive.list_files_in_folder(st.session_state.org_current_folder_id)
                }
                logger.info(f"Loaded children for folder ID: {st.session_state.org_current_folder_id}")
            except Exception as e:
                logger.error(f"Error listing folder children: {e}", exc_info=True) # Rule 4
                st.error(f"{get_text('org_browse_error', lang).format(error=e)}")
                st.session_state.org_folder_children_cache = {'folder_id': st.session_state.org_current_folder_id, 'children': []}


        folder_items = st.session_state.org_folder_children_cache['children']
        if not folder_items:
            st.info(get_text('org_browse_no_items', lang))
        else:
            for item in sorted(folder_items, key=lambda x: (x['mimeType'] != 'application/vnd.google-apps.folder', x['name'])):
                with st.container(border=True):
                    col_icon, col_name, col_actions = st.columns([0.5, 4, 2.5])
                    
                    icon = "📁" if item['mimeType'] == 'application/vnd.google-apps.folder' else "📄"
                    col_icon.write(icon)
                    col_name.write(item['name'])

                    if item['mimeType'] == 'application/vnd.google-apps.folder':
                        if col_actions.button("📂 Άνοιγμα", key=f"open_folder_{item['id']}", use_container_width=True):
                            st.session_state.org_folder_history.append(st.session_state.org_current_folder_id)
                            st.session_state.org_current_folder_id = item['id']
                            st.rerun()
                    else:
                        c_link, c_rename, c_delete, c_move = col_actions.columns(4)
                        c_link.link_button(get_text('org_browse_open_drive', lang), url=item.get('webViewLink', '#'), help="Opens in Google Drive", key=f"view_{item['id']}")
                        
                        # Rename functionality
                        with c_rename:
                            if st.button(get_text('org_browse_rename', lang), key=f"rename_{item['id']}", use_container_width=True):
                                new_name = st.text_input("Νέο Όνομα", value=item['name'], key=f"rename_input_{item['id']}")
                                if st.button("Αποθήκευση", key=f"save_rename_{item['id']}"):
                                    try:
                                        sorter_service.drive.rename_file(item['id'], new_name)
                                        st.success(get_text('org_rename_success', lang))
                                        st.rerun()
                                    except Exception as e:
                                        logger.error(f"Rename failed: {e}", exc_info=True) # Rule 4
                                        st.error(f"{get_text('org_rename_fail', lang).format(error=e)}")
                        
                        # Delete functionality
                        with c_delete:
                            if st.button(get_text('org_browse_delete', lang), key=f"delete_{item['id']}", use_container_width=True):
                                if st.warning("Είστε σίγουρος/η;"):
                                    if st.button("ΝΑΙ, Διαγραφή", key=f"confirm_delete_{item['id']}"):
                                        try:
                                            sorter_service.drive.delete_file(item['id'])
                                            st.success(get_text('org_delete_success', lang))
                                            st.rerun()
                                        except Exception as e:
                                            logger.error(f"Delete failed: {e}", exc_info=True) # Rule 4
                                            st.error(f"{get_text('org_delete_fail', lang).format(error=e)}")
                        
                        # Move to Manual Review
                        with c_move:
                            if st.button("➡️ Αναθεώρηση", key=f"move_review_{item['id']}", use_container_width=True):
                                try:
                                    manual_review_folder_id = sorter_service._get_or_create_path(sorter_service.root_id, [MANUAL_REVIEW_FOLDER])
                                    sorter_service.drive.move_file(item['id'], manual_review_folder_id)
                                    st.success(get_text('org_manual_move_success', lang))
                                    st.rerun()
                                except Exception as e:
                                    logger.error(f"Move to Manual Review failed: {e}", exc_info=True) # Rule 4
                                    st.error(f"{get_text('org_manual_move_fail', lang).format(error=e)}")


    with tab3: # Review / Errors
        st.subheader(get_text('org_tab_review', lang))

        if st.session_state.sorter_summary:
            summary = st.session_state.sorter_summary
            # Use buttons to view relevant lists dynamically
            if st.button(f"{get_text('org_view_manual_review', lang).format(count=len(summary['manual_review_files']))}"):
                st.session_state.current_review_list = 'manual_review_files'
            if st.button(f"{get_text('org_view_failed', lang).format(count=len(summary['failed_files']))}"):
                st.session_state.current_review_list = 'failed_files'
            if st.button(f"{get_text('org_view_irrelevant', lang).format(count=len(summary['irrelevant_files']))}"):
                st.session_state.current_review_list = 'irrelevant_files'
            if st.button(f"{get_text('org_view_duplicates', lang).format(count=len(summary['duplicate_files']))}"):
                st.session_state.current_review_list = 'duplicate_files'
        else:
            st.info("Εκτελέστε τον οργανωτή για να δείτε αρχεία προς αναθεώρηση.")
            st.session_state.current_review_list = None
        
        if st.session_state.get('current_review_list'):
            current_list = st.session_state.sorter_summary[st.session_state.current_review_list]
            if current_list:
                for item in current_list:
                    with st.container(border=True):
                        st.write(f"📄 **{item['name']}**")
                        st.caption(f"ID: {item['id']}")
                        st.link_button(get_text('org_browse_open_drive', lang), url=item.get('webViewLink', '#'), key=f"review_view_{item['id']}")
                        # Option to manually move to a folder
                        if st.session_state.current_review_list != 'failed_files': # Failed files usually need re-processing
                            if st.button("Μετακίνηση σε...", key=f"move_from_review_{item['id']}", use_container_width=True):
                                # This would open a small form or allow selection of a target folder
                                st.info("Manual move functionality to be implemented.")
            else:
                st.info("Η επιλεγμένη λίστα είναι κενή.")

    with tab4: # Full Log
        st.subheader(get_text('org_tab_log', lang))
        if st.session_state.sorter_run_log:
            for entry in st.session_state.sorter_run_log:
                st.markdown(entry)
        else:
            st.info("No log entries yet. Run the organizer.")