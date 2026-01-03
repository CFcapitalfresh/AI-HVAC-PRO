# -*- coding: utf-8 -*-
"""
CORE: LANGUAGE PACK
-------------------
Centralizes all text strings for multilingual support.
"""

# The central dictionary containing all translations.
# Each key corresponds to a UI element or message.
# The value is another dictionary with 'gr' and 'en' translations.
LANGUAGE_PACK = {
    # --- General App ---
    "app_title": {"gr": "Mastro Nek AI | Platinum", "en": "Mastro Nek AI | Platinum"}, # Kept "Platinum" from existing core
    "login_tab": {"gr": "Σύνδεση", "en": "Login"},
    "register_tab": {"gr": "Εγγραφή", "en": "Register"},
    "email_lbl": {"gr": "Email", "en": "Email"},
    "pass_lbl": {"gr": "Κωδικός", "en": "Password"},
    "btn_login": {"gr": "Σύνδεση", "en": "Login"},
    "name_lbl": {"gr": "Όνομα", "en": "Name"},
    "btn_register": {"gr": "Εγγραφή", "en": "Register"},
    "reg_success": {"gr": "Η εγγραφή ολοκληρώθηκε! Περιμένετε την έγκριση.", "en": "Registration successful! Awaiting approval."},
    "logout": {"gr": "Αποσύνδεση", "en": "Logout"},
    "menu_header": {"gr": "Πλοήγηση", "en": "Navigation"}, # Changed from "Κεντρικό Μενού" for consistency
    "general_ui_error": {"gr": "Προέκυψε σφάλμα στην εμφάνιση: {error}", "en": "An error occurred in the UI: {error}"},
    "db_init_success": {"gr": "Τοπική βάση δεδομένων (SQLite) αρχικοποιήθηκε.", "en": "Local database (SQLite) initialized."},
    "db_init_fail": {"gr": "Αποτυχία αρχικοποίησης τοπικής βάσης δεδομένων.", "en": "Failed to initialize local database."},
    "lic_activated": {"gr": "Άδεια χρήσης ενεργοποιήθηκε!", "en": "License activated!"},
    "lic_expired": {"gr": "Η άδεια χρήσης έχει λήξει.", "en": "License expired."},
    "lic_invalid": {"gr": "Μη έγκυρη άδεια χρήσης.", "en": "Invalid license."},
    "lic_not_found": {"gr": "Δεν βρέθηκε άδεια χρήσης.", "en": "No license found."},
    "lic_pending": {"gr": "Η άδεια είναι σε εκκρεμότητα.", "en": "License is pending."},
    "lic_status_valid": {"gr": "Ενεργή", "en": "Active"},
    "lic_status_expired": {"gr": "Ληγμένη", "en": "Expired"},
    "lic_status_invalid": {"gr": "Μη Έγκυρη", "en": "Invalid"},
    "lic_status_pending": {"gr": "Εκκρεμής", "en": "Pending"},
    "lic_status_not_found": {"gr": "Δεν Βρέθηκε", "en": "Not Found"},

    # --- Menu Items ---
    "menu_dashboard": {"gr": "📊 Επισκόπηση", "en": "📊 Dashboard"},
    "menu_diagnostics": {"gr": "🔧 Διαγνωστικά", "en": "🔧 Diagnostics"}, # Corrected icon
    "menu_chat": {"gr": "💬 AI Συνομιλία", "en": "💬 AI Chat"},
    "menu_library": {"gr": "🔎 Βιβλιοθήκη Manuals", "en": "🔎 Manuals Library"},
    "menu_clients": {"gr": "📇 Πελατολόγιο", "en": "📇 Client CRM"}, # Changed from "Clients" for consistency
    "menu_organizer": {"gr": "📅 AI Organizer", "en": "📅 AI Organizer"},
    "menu_tools": {"gr": "🛠️ Εργαλεία", "en": "🛠️ Tools"},
    "menu_admin": {"gr": "⚙️ Διαχείριση", "en": "⚙️ Admin Panel"}, # Changed from "Admin" for consistency
    "menu_licensing": {"gr": "🔑 Διαχείριση Αδειών", "en": "🔑 Licensing"}, # Corrected icon
    "menu_tech_specs": {"gr": "📝 Τεχνικές Προδιαγραφές", "en": "📝 Tech Specs"},
    "menu_help_user": {"gr": "❓ Βοήθεια", "en": "❓ Help"},

    # --- DASHBOARD ---
    'dash_welcome': {'gr': "👋 Καλωσήρθες", 'en': "👋 Welcome"},
    'dash_subtitle': {'gr': "Κέντρο Ελέγχου Τεχνικής Υποστήριξης", 'en': "Technical Support Control Center"},
    'dash_quick': {'gr': "🚀 Γρήγορες Ενέργειες", 'en': "🚀 Quick Actions"},
    'dash_chat_card': {'gr': "AI Τεχνικός Βοηθός", 'en': "AI Technical Assistant"},
    'dash_chat_desc': {'gr': "Διάγνωση βλαβών & Λύσεις", 'en': "Diagnosis & Solutions"},
    'dash_btn_chat': {'gr': "💬 Έναρξη Συνομιλίας", 'en': "💬 Start Chat"},
    'dash_lib_card': {'gr': "Βιβλιοθήκη Manuals", 'en': "Manuals Library"},
    'dash_lib_desc': {'gr': "Αναζήτηση Εγχειριδίων", "en": "Search Manuals"},
    'dash_btn_lib': {'gr': "🔎 Αναζήτηση", 'en': "🔎 Search"},
    'dash_tool_card': {'gr': "Εργαλεία HVAC", 'en': "HVAC Tools"},
    'dash_tool_desc': {'gr': "BTU Calc & Μετατροπές", 'en': "BTU Calc & Converters"},
    'dash_btn_tool': {'gr': "🛠️ Άνοιγμα Εργαλείων", 'en': "🛠️ Open Tools"},
    'dash_status': {'gr': "Κατάσταση Συστήματος: 🟢 Online | AI Engine: Ready", 'en': "System Status: 🟢 Online | AI Engine: Ready"},

    # --- UI Diagnostics (Troubleshooting Wizard) - MERGED FROM OLD diagnose.py ---
    "diag_title": {"gr": "Διαγνωστικός Οδηγός", "en": "Diagnostic Guide"},
    "diag_subtitle": {"gr": "Βήμα-προς-Βήμα αντιμετώπιση προβλημάτων", "en": "Step-by-step troubleshooting"},
    "diag_start_new": {"gr": "Έναρξη Νέας Διάγνωσης", "en": "Start New Diagnosis"},
    "diag_input_ph": {"gr": "Περιγράψτε το πρόβλημα (π.χ. 'Error E3', 'Δεν ψύχει')", "en": "Describe the problem (e.g. 'Error E3', 'Not cooling')"},
    "diag_context": {"gr": "Ενεργό Context:", "en": "Active Context:"},
    "diag_btn_create": {"gr": "Δημιουργία Πλάνου Διάγνωσης", "en": "Create Diagnosis Plan"},
    "diag_spinner": {"gr": "Δημιουργία πλάνου από AI...", "en": "Generating plan by AI..."},
    "diag_fail": {"gr": "Αδυναμία δημιουργίας πλάνου διάγνωσης.", "en": "Failed to generate diagnosis plan."},
    "diag_step": {"gr": "Βήμα", "en": "Step"},
    "diag_of": {"gr": "από", "en": "of"},
    "diag_done": {"gr": "✅ Η διάγνωση ολοκληρώθηκε!", "en": "✅ Diagnosis complete!"},
    "diag_btn_new": {"gr": "Νέα Διάγνωση", "en": "New Diagnosis"},
    "diag_action": {"gr": "Ενέργεια:", "en": "Action:"},
    "diag_question": {"gr": "Ερώτηση:", "en": "Question:"},
    "diag_yes": {"gr": "✅ Ναι", "en": "✅ Yes"},
    "diag_no": {"gr": "❌ Όχι", "en": "❌ No"},
    "diag_tip": {"gr": "Συμβουλή:", "en": "Tip:"},
    # --- UI Diagnostics (NEW AI System Status) ---
    "diag_ai_section_title": {"gr": "🔬 Έλεγχος Κατάστασης AI Συστήματος", "en": "🔬 AI System Status Check"},
    "diag_api_key_check": {"gr": "1. Έλεγχος Gemini API Key", "en": "1. Gemini API Key Check"},
    "diag_api_key_found": {"gr": "Το API Key βρέθηκε ({masked_key})", "en": "API Key found ({masked_key})"},
    "diag_api_key_not_found": {"gr": "Δεν βρέθηκε το GEMINI_KEY στο secrets.toml", "en": "GEMINI_KEY not found in secrets.toml"},
    "diag_api_key_info": {"gr": "Φτιάξτε φάκελο .streamlit/secrets.toml και βάλτε μέσα: GEMINI_KEY = 'YOUR_KEY'", "en": "Create .streamlit/secrets.toml and add: GEMINI_KEY = 'YOUR_KEY'"},
    "diag_ai_conn_test": {"gr": "2. Σύνδεση με Google AI (Ping Test)", "en": "2. Google AI Connection (Ping Test)"},
    "diag_ai_conn_attempt": {"gr": "Προσπάθεια σύνδεσης με Google Servers", "en": "Attempting connection to Google Servers"},
    "diag_ai_conn_success": {"gr": "Επιτυχία! Συνδέθηκε και βρήκε {count} διαθέσιμα μοντέλα.", "en": "Success! Connected and found {count} available models."},
    "diag_ai_conn_fail": {"gr": "Αποτυχία Σύνδεσης: {error}", "en": "Connection Failed: {error}"},
    "diag_pdf_test": {"gr": "3. Έλεγχος PDF Engine (pypdf)", "en": "3. PDF Engine Check (pypdf)"},
    "diag_pdf_read_success": {"gr": "Το PDF engine (pypdf) λειτουργεί κανονικά.", "en": "PDF engine (pypdf) is working correctly."},
    "diag_pdf_read_fail": {"gr": "Το PDF engine απέτυχε να διαβάσει ένα PDF: {error}", "en": "PDF engine failed to read a PDF: {error}"},
    "diag_simulation_title": {"gr": "4. Προσομοίωση Απάντησης (Test Run)", "en": "4. Response Simulation (Test Run)"},
    "diag_simulation_prompt": {"gr": "Στέλνω δοκιμαστική ερώτηση στο AI", "en": "Sending test query to AI"},
    "diag_simulation_success": {"gr": "AI Response: {response_start}...", "en": "AI Response: {response_start}..."},
    "diag_simulation_fail": {"gr": "Αποτυχία λήψης απάντησης από AI: {error}", "en": "Failed to get AI response: {error}"},
    "diag_selected_model": {"gr": "Το σύστημα επέλεξε αυτόματα το μοντέλο: **{model_name}**", "en": "The system automatically selected model: **{model_name}**"},


    # --- CHAT & MEDIA ---
    'chat_placeholder': {'gr': "Περιγράψτε το πρόβλημα...", 'en': "Describe the issue..."},
    'chat_thinking': {'gr': "🤔 Ο Mastro Nek αναλύει...", 'en': "🤔 Mastro Nek is thinking..."},
    'chat_intro': {'gr': "👋 Γεια σου! Ρώτησέ με για βλάβες ή manuals.", 'en': "👋 Hello! Ask me about faults or manuals."},
    'media_expander': {'gr': "📸 Κάμερα & 🎙️ Φωνητική Εντολή", 'en': "📸 Camera & 🎙️ Voice Input"}, # UNUSED FOR NOW
    'camera_label': {'gr': "📸 Τράβηξε Φωτογραφία", 'en': "📸 Take Photo"}, # UNUSED FOR NOW
    'audio_label': {'gr': "🎙️ Ηχογράφηση / Αρχείο Ήχου", 'en': "🎙️ Voice Message / Audio File"}, # UNUSED FOR NOW
    'media_sent': {'gr': "✅ Τα αρχεία επισυνάφθηκαν!", 'en': "✅ Files attached!"}, # UNUSED FOR NOW
    'brand_label': {'gr': "Μάρκα", 'en': "Brand"}, # Standardized
    'model_label': {'gr': "Μοντέλο", 'en': "Model"}, # Standardized
    'manual_retrieval_error': {'gr': "Σφάλμα ανάκτησης manual: {error}", 'en': "Manual retrieval error: {error}"},
    'manuals_found': {'gr': "Βρέθηκαν {count} σχετικά manuals.", 'en': "{count} relevant manuals found."},
    'no_manuals': {'gr': "Δεν βρέθηκαν manuals για τη μάρκα/μοντέλο.", 'en': "No manuals found for brand/model."},
    'select_brand_for_search': {'gr': "Επιλέξτε μάρκα για αναζήτηση.", 'en': "Select a brand to search."},
    'chat_input_placeholder': {'gr': "Περιγράψτε το πρόβλημα ή τον κωδικό βλάβης...", 'en': "Describe the issue or error code..."},
    'voice_input_help': {'gr': "Χρησιμοποιήστε μικρόφωνο για φωνητική εντολή.", "en": "Use microphone for voice input."},
    'voice_input_activated': {'gr': "Αναμονή για φωνητική εντολή...", "en": "Waiting for voice input..."},
    'upload_manual_label': {'gr': "Ανεβάστε PDF/Εικόνες", 'en': "Upload PDF/Images"}, # From old chat
    'upload_manual_help': {'gr': "Ανεβάστε αρχεία για ανάλυση από το AI.", 'en': "Upload files for AI analysis."}, # From old chat
    'processing_uploaded_file': {'gr': "Επεξεργασία ανεβασμένου αρχείου: '{name}'", 'en': "Processing uploaded file: '{name}'"},
    'studying_sources': {'gr': "Μελετώ {count} πηγές...", 'en': "Studying {count} sources..."},
    'tab_text': {'gr': "⌨️ Κείμενο", 'en': "⌨️ Text"}, # NEW KEY
    'tab_voice': {'gr': "🎙️ Φωνή", 'en': "🎙️ Voice"}, # NEW KEY
    'tab_upload': {'gr': "📎 Ανέβασμα", 'en': "📎 Upload"}, # NEW KEY
    'upload_files_label': {'gr': "Ανεβάστε PDF/Εικόνα", 'en': "Upload PDF/Image"}, # NEW KEY
    'ai_engine_error': {'gr': "Σφάλμα AI:", 'en': "AI Error:"}, # NEW KEY
    'analyzing': {'gr': "Ανάλυση...", 'en': "Analyzing..."}, # NEW KEY

    # --- UI ADMIN PANEL ---
    'admin_title': {"gr": "Πίνακας Διαχείρισης", "en": "Admin Panel"},
    'admin_no_users': {"gr": "Δεν βρέθηκαν χρήστες.", "en": "No users found."},
    'admin_pending': {"gr": "Αιτήματα για Έγκριση", "en": "Pending Approvals"},
    'admin_no_pending': {"gr": "Δεν υπάρχουν εκκρεμή αιτήματα.", "en": "No pending requests."},
    'admin_btn_activate': {"gr": "Ενεργοποίηση", "en": "Activate"},
    'admin_msg_active': {"gr": "Ο χρήστης ενεργοποιήθηκε", "en": "User activated"},
    'admin_btn_delete': {"gr": "Διαγραφή", "en": "Delete"},
    'admin_msg_del': {"gr": "Ο χρήστης διαγράφηκε", "en": "User deleted"},
    'admin_all_users': {"gr": "Όλοι οι Χρήστες", "en": "All Users"},
    'admin_all_users_cap': {"gr": "Διαχείριση δικαιωμάτων & ρόλων χρηστών", "en": "Manage user rights & roles"},

    # --- UI TOOLS ---
    'tool_btu_tab': {'gr': "❄️ Υπολογιστής BTU", 'en': "❄️ BTU Calculator"},
    'tool_conv_tab': {'gr': "🔄 Μετατροπές", 'en': "🔄 Converters"},
    'tool_pipe_tab': {'gr': "📏 Οδηγός Σωληνώσεων", 'en': "📏 Piping Guide"},
    'tool_area': {'gr': "Εμβαδόν Χώρου (m²)", 'en': "Room Area (m²)"},
    'tool_height': {'gr': "Ύψος (m)", 'en': "Height (m)"},
    'tool_insulation': {'gr': "Μόνωση", 'en': "Insulation"},
    'ins_good': {'gr': "Καλή", 'en': "Good"},
    'ins_avg': {'gr': "Μέτρια", 'en': "Average"},
    'ins_bad': {'gr': "Κακή", 'en': "Bad"},
    'tool_sun': {'gr': "Έκθεση στον Ήλιο", 'en': "Sun Exposure"},
    'sun_low': {'gr': "Χαμηλή", 'en': "Low"},
    'sun_med': {'gr': "Μέτρια", 'en': "Medium"},
    'sun_high': {'gr': "Υψηλή", 'en': "High"},
    'tool_calc_res': {'gr': "Απαιτούμενη Ισχύς", 'en': "Required Power"},
    'tool_rec': {'gr': "Προτεινόμενο AC", 'en': "Recommended AC"},
    'pipe_liquid': {'gr': "Υγρό", 'en': "Liquid"},
    'pipe_gas': {'gr': "Αέριο", 'en': "Gas"},

    # --- UI LICENSING ---
    "lic_page_title": {"gr": "Διαχείριση Αδειών Χρήσης", "en": "License Management"},
    "lic_user_section_title": {"gr": "Κατάσταση Άδειας Χρήστη", "en": "User License Status"},
    "lic_status_label": {"gr": "Κατάσταση:", "en": "Status:"},
    "lic_enter_key": {"gr": "Εισάγετε Κωδικό Άδειας", "en": "Enter License Key"},
    "lic_key_ph": {"gr": "Πληκτρολογήστε τον κωδικό άδειας εδώ...", "en": "Type your license key here..."},
    "lic_btn_activate": {"gr": "Ενεργοποίηση Άδειας", "en": "Activate License"},
    "lic_activation_success": {"gr": "Η άδεια ενεργοποιήθηκε με επιτυχία!", "en": "License activated successfully!"},
    "lic_activation_fail": {"gr": "Αποτυχία ενεργοποίησης άδειας", "en": "License activation failed"},
    "lic_admin_section_title": {"gr": "Διαχείριση Αδειών (Admin)", "en": "License Management (Admin)"},
    "lic_admin_no_licenses": {"gr": "Δεν βρέθηκαν καταχωρημένες άδειες.", "en": "No registered licenses found."},
    "lic_admin_all_licenses": {"gr": "Όλοι οι Χρήστες & Άδειες", "en": "All Users & Licenses"},
    "lic_admin_filter_users": {"gr": "Φιλτράρισμα χρηστών...", "en": "Filter users..."},
    "lic_admin_role": {"gr": "Ρόλος", "en": "Role"},
    "lic_admin_expiry_date": {"gr": "Ημερομηνία Λήξης", "en": "Expiry Date"},
    "lic_admin_update_license": {"gr": "Ενημέρωση Άδειας", "en": "Update License"},
    "lic_admin_update_success": {"gr": "Οι ρυθμίσεις άδειας ενημερώθηκαν.", "en": "License settings updated."},
    "lic_admin_update_fail": {"gr": "Αποτυχία ενημέρωσης ρυθμίσεων άδειας.", "en": "Failed to update license settings."},
    "lic_admin_grant_license": {"gr": "Εκχώρηση Άδειας", "en": "Grant License"},
    "lic_admin_revoke_license": {"gr": "Ανάκληση Άδειας", "en": "Revoke License"},

    # --- UI ORGANIZER ---
    "org_desc": {"gr": "Αυτόματο σύστημα ταξινόμησης και οργάνωσης εγχειριδίων στο Google Drive. Χρησιμοποιεί τεχνητή νοημοσύνη για να αναγνωρίσει, να μετονομάσει και να αρχειοθετήσει αυτόματα τα αρχεία σας σε μια δομημένη ιεραρχία.", "en": "Automatic system for sorting and organizing manuals in Google Drive. Uses AI to automatically recognize, rename, and archive your files into a structured hierarchy."},
    "org_start_sorting": {"gr": "Έναρξη Αυτόματης Ταξινόμησης", "en": "Start Auto-Sorting"},
    "org_stop_sorting": {"gr": "Διακοπή Ταξινόμησης", "en": "Stop Sorting"},
    "org_full_resort_checkbox": {"gr": "Πλήρης Επανεπεξεργασία (διαγράφει τα παλιά αρχεία και ξαναταξινομεί)", "en": "Full Resort (deletes old files and resorts)"},
    "org_progress_title": {"gr": "Εξέλιξη Ταξινόμησης:", "en": "Sorting Progress:"},
    "org_summary_tab": {"gr": "📊 Σύνοψη & Εκτέλεση", "en": "📊 Summary & Execution"},
    "org_browse_tab": {"gr": "🔍 Περιήγηση Αρχείων", "en": "🔍 Browse Files"},
    "org_review_tab": {"gr": "⚠️ Αναθεώρηση / Σφάλματα", "en": "⚠️ Review / Errors"},
    "org_log_tab": {"gr": "📜 Πλήρες Log", "en": "📜 Full Log"},
    "org_summary_title": {"gr": "📊 Σύνοψη Τελευταίας Εκτέλεσης", "en": "📊 Last Run Summary"},
    "org_last_update": {"gr": "Τελευταία ενημέρωση:", "en": "Last Update:"},
    "org_scanned_files": {"gr": "Σαρωμένα Αρχεία", "en": "Scanned Files"},
    "org_sorted_successfully": {"gr": "Επιτυχώς Ταξινομημένα", "en": "Successfully Sorted"},
    "org_manual_review": {"gr": "Για Χειροκίνητο Έλεγχο", "en": "For Manual Review"},
    "org_irrelevant": {"gr": "Άσχετα/Άγνωστα", "en": "Irrelevant/Unknown"},
    "org_duplicates": {"gr": "Διπλότυπα", "en": "Duplicates"},
    "org_distribution_success": {"gr": "Αναλυτική Κατανομή Επιτυχών Ταξινομήσεων", "en": "Detailed Distribution of Successful Sorts"},
    "org_category_tab": {"gr": "Κατηγορίες", "en": "Categories"},
    "org_brand_tab": {"gr": "Μάρκες", "en": "Brands"},
    "org_type_tab": {"gr": "Τύποι Εγχειριδίων", "en": "Manual Types"},
    "org_no_summary_data": {"gr": "Δεν υπάρχουν δεδομένα σύνοψης.", "en": "No summary data available."},
    "org_browse_title": {"gr": "Περιήγηση Ταξινομημένων Αρχείων", "en": "Browse Sorted Files"},
    "org_go_back": {"gr": "Επιστροφή", "en": "Go Back"},
    "org_select_category": {"gr": "Επιλέξτε Κατηγορία", "en": "Select Category"},
    "org_select_brand": {"gr": "Επιλέξτε Μάρκα", "en": "Select Brand"},
    "org_select_model": {"gr": "Επιλέξτε Μοντέλο", "en": "Select Model"},
    "org_select_type": {"gr": "Επιλέξτε Τύπο", "en": "Select Type"},
    "org_current_level": {"gr": "Τρέχον επίπεδο:", "en": "Current Level:"},
    "org_files_in_category": {"gr": "Αρχεία στην Κατηγορία '{category}'", "en": "Files in Category '{category}'"},
    "org_files_in_brand": {"gr": "Αρχεία στη Μάρκα '{brand}' (Κατηγορία: {category})", "en": "Files in Brand '{brand}' (Category: {category})"},
    "org_files_in_model": {"gr": "Αρχεία στο Μοντέλο '{model}' (Μάρκα: {brand})", "en": "Files in Model '{model}' (Brand: {brand})"},
    "org_files_in_type": {"gr": "Αρχεία Τύπου '{type}' (Μοντέλο: {model})", "en": "Files of Type '{type}' (Model: {model})"},
    "org_review_title": {"gr": "Αρχεία για Χειροκίνητο Έλεγχο & Σφάλματα", "en": "Files for Manual Review & Errors"},
    "org_manual_review_info": {"gr": "Αυτά τα αρχεία μετακινήθηκαν στο φάκελο '_MANUAL_REVIEW' γιατί το AI δεν ήταν σίγουρο για την ταξινόμησή τους.", "en": "These files were moved to '_MANUAL_REVIEW' because the AI was unsure about their classification."},
    "org_irrelevant_info": {"gr": "Αυτά τα αρχεία μετακινήθηκαν στο φάκελο '_IRRELEVANT_OR_UNKNOWN' γιατί δεν σχετίζονται με HVAC ή δεν μπορούσαν να αναγνωριστούν.", "en": "These files were moved to '_IRRELEVANT_OR_UNKNOWN' because they are not HVAC-related or could not be identified."},
    "org_duplicate_info": {"gr": "Αυτά τα αρχεία είναι διπλότυπα και μετακινήθηκαν στο φάκελο '_DUPLICATES'.", "en": "These files are duplicates and have been moved to '_DUPLICATES' folder."},
    "org_failed_info": {"gr": "Αυτά τα αρχεία απέτυχαν να επεξεργαστούν λόγω τεχνικού προβλήματος.", "en": "These files failed to process due to a technical issue."},
    "org_view_on_drive": {"gr": "Προβολή στο Drive", "en": "View on Drive"},
    "org_full_log_title": {"gr": "Πλήρες Ημερολόγιο Εκτέλεσης", "en": "Full Execution Log"},
    "org_log_empty": {"gr": "Το ημερολόγιο εκτέλεσης είναι κενό.", "en": "The execution log is empty."},

    # --- UI CLIENTS ---
    "client_no_clients": {"gr": "Δεν βρέθηκαν πελάτες.", "en": "No clients found."},
    "client_search_ph": {"gr": "Αναζήτηση Πελάτη...", "en": "Search Client..."},

    # --- UI TECH SPECS ---
    "specs_title": {"gr": "Τεχνικές Προδιαγραφές", "en": "Technical Specifications"},
    "specs_system_architecture": {"gr": "🧬 Αρχιτεκτονική Συστήματος", "en": "🧬 System Architecture"},
    "specs_status_monitor": {"gr": "📊 Έλεγχος Κατάστασης", "en": "📊 Status Monitor"},
    "specs_python_version": {"gr": "Έκδοση Python", "en": "Python Version"},
    "specs_session_cache": {"gr": "Cache Session", "en": "Session Cache"},
    "specs_user_role": {"gr": "Ρόλος Χρήστη", "en": "User Role"},
    "specs_language": {"gr": "Γλώσσα", "en": "Language"},

    # --- UI HELP USER ---
    "help_title": {"gr": "Βοήθεια Χρήσης", "en": "Help"},
    "help_info": {"gr": "ℹ️ Οδηγός Χρήσης Mastro Nek AI", "en": "ℹ️ Mastro Nek AI User Guide"},
    "help_chat_q": {"gr": "💬 Πώς χρησιμοποιώ το Chat;", "en": "💬 How do I use the Chat?"},
    "help_chat_a": {"gr": "1. Πήγαινε στο μενού 'AI Συνομιλία'.\n2. Γράψε την ερώτησή σου στο κάτω μέρος.\n3. Μπορείς να ανεβάσεις φωτογραφίες ή PDF από το tab 'Ανέβασμα'.", "en": "1. Go to the 'AI Chat' menu.\n2. Type your question at the bottom.\n3. You can upload photos or PDFs from the 'Upload' tab."},
    "help_manuals_q": {"gr": "🔎 Πώς βρίσκω Manuals;", "en": "🔎 How do I find Manuals?"},
    "help_manuals_a": {"gr": "1. Πήγαινε στη 'Βιβλιοθήκη Manuals'.\n2. Γράψε το μοντέλο ή τη μάρκα στην αναζήτηση.\n3. Πάτα το Link για να ανοίξει το PDF.", "en": "1. Go to the 'Manuals Library'.\n2. Type the model or brand in the search bar.\n3. Click the Link to open the PDF."},
    "help_organizer_q": {"gr": "🧠 Πώς λειτουργεί ο Organizer (Admin);", "en": "🧠 How does the Organizer (Admin) work?"},
    "help_organizer_a": {"gr": "1. Πήγαινε στο 'AI Organizer' (μόνο Admin).\n2. Πάτα 'Έναρξη Αυτόματης Ταξινόμησης'.\n3. Το σύστημα θα διαβάσει τα ατακτοποίητα PDF και θα τα βάλει σε φακέλους αυτόματα.", "en": "1. Go to 'AI Organizer' (Admin only).\n2. Click 'Start Auto-Sorting'.\n3. The system will read unsorted PDFs and automatically place them into folders."}
}

def get_text(key: str, lang: str = 'gr') -> str:
    """
    Ανακτά τη μετάφραση για ένα συγκεκριμένο κλειδί και γλώσσα.
    Εάν το κλειδί ή η γλώσσα δεν βρεθεί, επιστρέφει το κλειδί
    ή ένα placeholder σφάλματος.
    """
    if key in LANGUAGE_PACK:
        if lang in LANGUAGE_PACK[key]:
            return LANGUAGE_PACK[key][lang]
        else:
            logging.warning(f"Language '{lang}' not found for key '{key}'. Using default 'gr'.")
            return LANGUAGE_PACK[key].get('gr', f"[{key} - lang missing]")
    else:
        logging.warning(f"Key '{key}' not found in LANGUAGE_PACK.")
        return f"[{key}]"