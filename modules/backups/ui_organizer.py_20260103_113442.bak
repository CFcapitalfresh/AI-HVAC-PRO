import streamlit as st
from services.sorter_logic import SorterService, ALLOWED_CATEGORIES, ALLOWED_TYPES, IRRELEVANT_OR_UNKNOWN_FOLDER, DUPLICATES_FOLDER, IGNORED_FOLDERS_TOP_LEVEL # ΝΕΟ: Εισαγωγή IGNORED_FOLDERS_TOP_LEVEL
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

    # Initialize session state for sorter flags and results
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
    if 'org_selected_category' not in st.session_state: st.session_state.org_selected_category = None
    if 'org_selected_brand' not in st.session_state: st.session_state.org_selected_brand = None
    if 'org_selected_model' not in st.session_state: st.session_state.org_selected_model = None
    if 'org_selected_type' not in st.session_state: st.session_state.org_selected_type = None

    # --- Tabs for Organizer functionalities ---
    tab1, tab2, tab3, tab4 = st.tabs([ # Αναδιάταξη tabs
        "📊 Σύνοψη & Εκτέλεση", 
        "🔍 Περιήγηση Αρχείων", 
        "⚠️ Αναθεώρηση / Σφάλματα", 
        "📜 Πλήρες Log"
    ])

    with tab1: # Summary & Execution
        st.divider()
        # --- Εμφάνιση Συνοπτικών Στατιστικών ---
        if st.session_state.sorter_summary:
            summary = st.session_state.sorter_summary
            st.subheader("📊 Σύνοψη Τελευταίας Εκτέλεσης")
            st.caption(f"Τελευταία ενημέρωση: {summary.get('last_run_timestamp', 'N/A')}")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Σαρωμένα Αρχεία", summary.get('total_files_scanned', 0))
            col2.metric("Επιτυχώς Ταξινομημένα", summary.get('total_successfully_sorted', 0))
            col3.metric("Για Χειροκίνητο Έλεγχο", summary.get('total_moved_to_manual_review', 0))
            col4.metric("Άσχετα/Άγνωστα", summary.get('total_moved_to_irrelevant', 0))
            col5.metric("Διπλότυπα", summary.get('total_moved_to_duplicates', 0))

            if summary.get('total_successfully_sorted', 0) > 0:
                st.markdown("---")
                st.subheader("Αναλυτική Κατανομή Επιτυχών Ταξινομήσεων")
                
                tab_cat, tab_brand, tab_type = st.tabs(["Κατηγορίες", "Μάρκες", "Τύποι Εγχειριδίων"])
                
                with tab_cat:
                    if summary['category_counts']:
                        df_categories = pd.DataFrame(summary['category_counts'].items(), columns=['Κατηγορία', 'Πλήθος'])
                        st.dataframe(df_categories.sort_values(by='Πλήθος', ascending=False), use_container_width=True, hide_index=True)
                        st.bar_chart(df_categories.set_index('Κατηγορία'))
                    else:
                        st.info("Δεν υπάρχουν δεδομένα για κατηγορίες.")
                
                with tab_brand:
                    if summary['brand_counts']:
                        df_brands = pd.DataFrame(summary['brand_counts'].items(), columns=['Μάρκα', 'Πλήθος'])
                        st.dataframe(df_brands.sort_values(by='Πλήθος', ascending=False), use_container_width=True, hide_index=True)
                        st.bar_chart(df_brands.set_index('Μάρκα'))
                    else:
                        st.info("Δεν υπάρχουν δεδομένα για μάρκες.")

                with tab_type:
                    if summary['type_counts']:
                        df_types = pd.DataFrame(summary['type_counts'].items(), columns=['Τύπος Εγχειριδίου', 'Πλήθος'])
                        st.dataframe(df_types.sort_values(by='Πλήθος', ascending=False), use_container_width=True, hide_index=True)
                        st.bar_chart(df_types.set_index('Τύπος Εγχειριδίου'))
                    else:
                        st.info("Δεν υπάρχουν δεδομένα για τύπους εγχειριδίων.")
            st.markdown("---")

        # --- Action Buttons (Start/Stop/Refresh/Force Resort) ---
        col_start, col_stop = st.columns(2)

        with col_start:
            if st.button(f"🚀 {get_text('org_start', lang)}", type="primary", use_container_width=True, disabled=st.session_state['sorter_running']):
                st.session_state['sorter_running'] = True
                st.session_state['sorter_stop_flag'] = False 
                st.session_state.force_full_resort = False # Normal run
                st.rerun()

        with col_stop:
            if st.button("🛑 Διακοπή", type="secondary", use_container_width=True, disabled=not st.session_state['sorter_running']):
                st.session_state['sorter_stop_flag'] = True 
                logger.info("Sorter stop flag set. Waiting for process to halt.")
        
        st.markdown("---")
        st.info("ℹ️ Χρησιμοποιήστε την 'Πλήρη Επανεπεξεργασία' για να ξαναταξινομήσετε όλα τα αρχεία σας από την αρχή. (Προσοχή: Μπορεί να διαρκέσει πολύ).")
        if st.button("🔄 Έναρξη Πλήρους Επανεπεξεργασίας (Reset & Re-Sort)", use_container_width=True, disabled=st.session_state['sorter_running']):
            st.session_state['sorter_running'] = True
            st.session_state['sorter_stop_flag'] = False
            st.session_state.force_full_resort = True # Set flag for full resort
            st.rerun()
        
        st.markdown("---") # Διαχωριστικό πριν τα logs/progress

    with tab2: # Browse Organized Files (πρώην tab2)
        st.subheader("🔍 Περιήγηση Οργανωμένων Αρχείων")
        st.caption("Εξερευνήστε την ιεραρχία των ταξινομημένων εγχειριδίων.")
        
        # Load library_cache if not already loaded or if empty
        if 'library_cache' not in st.session_state or not st.session_state.library_cache:
            sync_service = SyncService()
            with st.spinner("Φόρτωση ευρετηρίου βιβλιοθήκης..."):
                # Call scan_library() to ensure a complete and up-to-date index for browsing
                st.session_state.library_cache = sync_service.scan_library() 
            if not st.session_state.library_cache:
                st.info("Η βιβλιοθήκη είναι κενή. Εκτελέστε τον Organizer ή συγχρονίστε τη βιβλιοθήκη.")
                return

        library_data = st.session_state.library_cache

        # Back button logic
        if st.session_state.org_browse_level != "categories":
            if st.button("⬅️ Πίσω"):
                if st.session_state.org_browse_level == "brands":
                    st.session_state.org_browse_level = "categories"
                    st.session_state.org_selected_category = None
                elif st.session_state.org_browse_level == "models":
                    st.session_state.org_browse_level = "brands"
                    st.session_state.org_selected_brand = None
                elif st.session_state.org_browse_level == "types":
                    st.session_state.org_browse_level = "models"
                    st.session_state.org_selected_model = None
                elif st.session_state.org_browse_level == "files":
                    st.session_state.org_browse_level = "types"
                    st.session_state.org_selected_type = None
                st.rerun()
        
        st.markdown("---")

        if st.session_state.org_browse_level == "categories":
            st.markdown("#### Επιλέξτε Κατηγορία:")
            # Use 'category' metadata for browsing, allowing special folders like _IRRELEVANT_OR_UNKNOWN
            categories = sorted(list(set(item.get('category') for item in library_data if item.get('category'))))
            # Optional: Filter out 'Trash' or other unwanted top-level internal categories here if needed for display
            categories = [c for c in categories if c not in ["Trash"]] 
            
            if categories:
                for cat in categories:
                    if st.button(f"📁 {cat.replace('_', ' ')}", key=f"cat_{cat}", use_container_width=True):
                        st.session_state.org_selected_category = cat
                        st.session_state.org_browse_level = "brands"
                        st.rerun()
            else:
                st.info("Δεν βρέθηκαν κατηγορίες.")

        elif st.session_state.org_browse_level == "brands":
            st.markdown(f"#### Κατηγορία: **{st.session_state.org_selected_category.replace('_', ' ')}** - Επιλέξτε Μάρκα:")
            brands = sorted(list(set(item.get('brand') for item in library_data if item.get('category') == st.session_state.org_selected_category and item.get('brand'))))
            if brands:
                for brand in brands:
                    if st.button(f"🏭 {brand.replace('_', ' ')}", key=f"brand_{brand}", use_container_width=True):
                        st.session_state.org_selected_brand = brand
                        st.session_state.org_browse_level = "models"
                        st.rerun()
            else:
                st.info("Δεν βρέθηκαν μάρκες σε αυτή την κατηγορία.")

        elif st.session_state.org_browse_level == "models":
            st.markdown(f"#### Κατηγορία: **{st.session_state.org_selected_category.replace('_', ' ')}** > **{st.session_state.org_selected_brand.replace('_', ' ')}** - Επιλέξτε Μοντέλο:")
            models = sorted(list(set(item.get('model') for item in library_data if item.get('category') == st.session_state.org_selected_category and item.get('brand') == st.session_state.org_selected_brand and item.get('model'))))
            if models:
                for model in models:
                    if st.button(f"⚙️ {model.replace('_', ' ')}", key=f"model_{model}", use_container_width=True):
                        st.session_state.org_selected_model = model
                        st.session_state.org_browse_level = "types"
                        st.rerun()
            else:
                st.info("Δεν βρέθηκαν μοντέλα για αυτή τη μάρκα.")

        elif st.session_state.org_browse_level == "types":
            st.markdown(f"#### Κατηγορία: **{st.session_state.org_selected_category.replace('_', ' ')}** > **{st.session_state.org_selected_brand.replace('_', ' ')}** > **{st.session_state.org_selected_model.replace('_', ' ')}** - Επιλέξτε Τύπο Εγχειριδίου:")
            types = sorted(list(set(item.get('meta_type') for item in library_data if item.get('category') == st.session_state.org_selected_category and item.get('brand') == st.session_state.org_selected_brand and item.get('model') == st.session_state.org_selected_model and item.get('meta_type'))))
            if types:
                for doc_type in types:
                    if st.button(f"📄 {doc_type.replace('_', ' ')}", key=f"type_{doc_type}", use_container_width=True):
                        st.session_state.org_selected_type = doc_type
                        st.session_state.org_browse_level = "files"
                        st.rerun()
            else:
                st.info("Δεν βρέθηκαν τύποι εγχειριδίων για αυτό το μοντέλο.")

        elif st.session_state.org_browse_level == "files":
            st.markdown(f"#### Κατηγορία: **{st.session_state.org_selected_category.replace('_', ' ')}** > **{st.session_state.org_selected_brand.replace('_', ' ')}** > **{st.session_state.org_selected_model.replace('_', ' ')}** > **{st.session_state.org_selected_type.replace('_', ' ')}** - Αρχεία:")
            files_in_type = [item for item in library_data if item.get('category') == st.session_state.org_selected_category and item.get('brand') == st.session_state.org_selected_brand and item.get('model') == st.session_state.org_selected_model and item.get('meta_type') == st.session_state.org_selected_type]
            
            if files_in_type:
                for file_item in files_in_type:
                    with st.container(border=True):
                        st.markdown(f"**{file_item.get('original_name', file_item.get('name', 'N/A'))}**")
                        if file_item.get('error_codes'):
                            st.caption(f"Error Codes: {file_item.get('error_codes')}")
                        if file_item.get('link'):
                            st.link_button("📂 Άνοιγμα στο Drive", file_item['link'], use_container_width=True)
                        else:
                            st.caption("No link available.")
            else:
                st.info("Δεν βρέθηκαν αρχεία σε αυτό τον τύπο εγχειριδίου.")
        
    with tab3: # Manual Review / Errors (πρώην tab3)
        st.subheader("⚠️ Αρχεία για Χειροκίνητη Αναθεώρηση / Σφάλματα")

        all_issues = []
        
        for item in st.session_state['sorter_manual_review_files']:
            all_issues.append({
                "type": "Manual Review",
                "file": item['file'], 
                "reason": item['reason'], 
                "output": item['output']
            })
        for item in st.session_state['sorter_irrelevant_files']:
            all_issues.append({
                "type": "Irrelevant/Unknown",
                "file": item['file'], 
                "reason": item['reason'], 
                "output": item['output']
            })
        for item in st.session_state['sorter_duplicate_files']:
            all_issues.append({
                "type": "Duplicate",
                "file": item['file'], 
                "reason": item['reason'], 
                "output": item['output']
            })
        for item in st.session_state['sorter_failed_files']:
            all_issues.append({
                "type": "Failed Processing",
                "file": item['file'], 
                "reason": item['reason'], 
                "output": item['output']
            })

        if all_issues:
            for i, issue in enumerate(all_issues):
                file_name = issue['file'].get('name', 'N/A')
                file_id = issue['file'].get('id', 'N/A')
                link = issue['file'].get('webViewLink', f"https://drive.google.com/file/d/{file_id}/view" if file_id != 'N/A' else '#')

                with st.expander(f"📁 {file_name} - **{issue['type']}**: {issue['reason']}"):
                    st.write(f"**Original File:** `{file_name}`")
                    st.write(f"**Drive ID:** `{file_id}`")
                    st.write(f"**Link:** [Open in Drive]({link})")
                    st.write(f"**AI Output:** `{issue['output']}`")

                    if issue['type'] in ["Manual Review", "Failed Processing", "Irrelevant/Unknown"]:
                        st.markdown("---")
                        st.markdown("**Χειροκίνητη Ταξινόμηση/Επανεπεξεργασία:**")
                        
                        manual_category = st.selectbox(
                            "Κατηγορία", ALLOWED_CATEGORIES + ["_MANUAL_REVIEW", "_AI_ERROR", "_NEEDS_OCR", IRRELEVANT_OR_UNKNOWN_FOLDER],
                            index=ALLOWED_CATEGORIES.index("Other_HVAC") if "Other_HVAC" in ALLOWED_CATEGORIES else 0,
                            key=f"manual_cat_{file_id}_{i}"
                        )
                        manual_brand = st.text_input("Μάρκα", value="UNKNOWN", key=f"manual_brand_{file_id}_{i}")
                        manual_model = st.text_input("Μοντέλο", value="MISC", key=f"manual_model_{file_id}_{i}")
                        manual_type = st.selectbox(
                            "Τύπος Εγχειριδίου", ALLOWED_TYPES, 
                            index=ALLOWED_TYPES.index("General_Manual") if "General_Manual" in ALLOWED_TYPES else 0,
                            key=f"manual_type_{file_id}_{i}"
                        )

                        if st.button("Επανεπεξεργασία (χειροκίνητα)", key=f"reprocess_{file_id}_{i}", use_container_width=True):
                            manual_data = {
                                "category": manual_category,
                                "brand": manual_brand,
                                "model": manual_model,
                                "type": manual_type
                            }
                            sorter = SorterService()
                            with st.spinner(f"Επανεπεξεργασία αρχείου: {file_name}"):
                                sorter.process_unsorted_files(update_ui, specific_file_id=file_id, manual_inputs=manual_data)
                            st.rerun() 
                    else:
                        st.caption("Αρχεία διπλότυπων συνήθως διαχειρίζονται με μαζική διαγραφή ή αρχειοθέτηση.")

        else:
            st.info("Δεν υπάρχουν αρχεία για αναθεώρηση.")

    with tab4: # Full Log (πρώην tab4)
        st.subheader(get_text('org_log', lang))
        # Placeholder for the dynamic log messages and progress bar
        progress_bar_placeholder = st.empty()
        log_box = st.container(height=500, border=True)

        # Callback function to update UI in real-time
        def update_ui(msg, type_):
            log_entry = {'msg': msg, 'type': type_}
            st.session_state.sorter_run_log.append(log_entry)
            
            with log_box:
                if type_ == "info": st.info(msg)
                elif type_ == "success": st.success(msg)
                elif type_ == "error": st.error(msg)
                elif type_ == "warning": st.warning(msg)
                else: st.write(f"⚙️ {msg}")
            
            current_progress = st.session_state.sorter_progress_data["current"]
            total_progress = st.session_state.sorter_progress_data["total"]
            progress_text = st.session_state.sorter_progress_data["text"]

            if total_progress > 0:
                progress_value = current_progress / total_progress
                progress_bar_placeholder.progress(progress_value, text=progress_text)
            else:
                progress_bar_placeholder.progress(0, text="Εκκίνηση...")


        if st.session_state['sorter_running']:
            sorter = SorterService()
            progress_bar_placeholder.progress(0, text="Αρχικοποίηση...")
            try:
                # Pass the force_full_resort flag
                sorter.process_unsorted_files(update_ui, force_full_resort=st.session_state.force_full_resort)
                st.session_state['sorter_running'] = False 
                st.session_state.force_full_resort = False # Reset flag after run
                logger.info("Sorter process completed or stopped. Rerunning UI.")
                st.rerun() 
            except Exception as e:
                logger.error(f"Error during sorter execution: {e}", exc_info=True)
                update_ui(f"Κρίσιμο σφάλμα κατά την εκτέλεση του Organizer: {e}", "error")
                st.session_state['sorter_running'] = False
                st.session_state.force_full_resort = False # Reset flag on error too
                st.rerun()

        if st.session_state['sorter_run_log']:
            with log_box: 
                log_box.empty()
                for log_entry in st.session_state['sorter_run_log']:
                    if log_entry['type'] == 'info': st.info(log_entry['msg'])
                    elif log_entry['type'] == 'success': st.success(log_entry['msg'])
                    elif log_entry['type'] == 'error': st.error(log_entry['msg'])
                    elif log_entry['type'] == 'warning': st.warning(log_entry['msg'])
                    else: st.write(f"⚙️ {log_entry['msg']}")

        if not st.session_state['sorter_running'] and st.session_state.sorter_progress_data["total"] > 0:
            final_progress_value = st.session_state.sorter_progress_data["current"] / st.session_state.sorter_progress_data["total"]
            final_progress_text = st.session_state.sorter_progress_data["text"] 
            progress_bar_placeholder.progress(final_progress_value, text=final_progress_text)