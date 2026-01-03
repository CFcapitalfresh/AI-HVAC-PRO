# -*- coding: utf-8 -*-
# ... (τυχόν σχόλια ή άλλα imports) ...

LANGUAGE_PACK = {
    # --- General App ---
    "app_title": {"gr": "Mastro Nek AI", "en": "Mastro Nek AI"},
    "login_tab": {"gr": "Σύνδεση", "en": "Login"},
    # ...
    "lic_page_title": {"gr": "Διαχείριση Άδειας Χρήσης", "en": "License Management"},
    "lic_user_section_title": {"gr": "Η Άδειά Σου", "en": "Your License"},
    "lic_status_label": {"gr": "Κατάσταση Άδειας:", "en": "License Status:"},
    "lic_expiry_label": {"gr": "Ημερομηνία Λήξης:", "en": "Expiration Date:"},
    "lic_enter_key": {"gr": "Εισάγετε Κλειδί Άδειας", "en": "Enter License Key"},
    "lic_key_ph": {"gr": "XYZ-ABCD-1234-EFGH", "en": "XYZ-ABCD-1234-EFGH"},
    "lic_btn_activate": {"gr": "Ενεργοποίηση Άδειας", "en": "Activate License"},
    "lic_activation_success": {"gr": "Η άδεια σας ενεργοποιήθηκε επιτυχώς!", "en": "Your license has been activated successfully!"},
    "lic_activation_fail": {"gr": "Αποτυχία ενεργοποίησης άδειας. Ελέγξτε το κλειδί.", "en": "License activation failed. Please check the key."},
    "lic_admin_section_title": {"gr": "Διαχείριση Αδειών Διαχειριστή", "en": "Admin License Management"},
    "lic_admin_user_email": {"gr": "Email Χρήστη", "en": "User Email"},
    "lic_admin_current_role": {"gr": "Τρέχων Ρόλος", "en": "Current Role"},
    "lic_admin_new_role": {"gr": "Νέος Ρόλος", "en": "New Role"},
    "lic_admin_set_expiry": {"gr": "Ορισμός Λήξης", "en": "Set Expiry"},
    "lic_admin_btn_update_role": {"gr": "Ενημέρωση Ρόλου", "en": "Update Role"},
    "lic_admin_btn_revoke": {"gr": "Απενεργοποίηση", "en": "Deactivate"},
    "lic_admin_role_updated": {"gr": "Ο ρόλος του χρήστη ενημερώθηκε.", "en": "User role updated."},
    "lic_admin_activation_updated": {"gr": "Η άδεια χρήσης ενημερώθηκε.", "en": "License status updated."},
    "lic_admin_error_update": {"gr": "Σφάλμα κατά την ενημέρωση.", "en": "Error during update."},
    "lic_admin_all_licenses": {"gr": "Όλες οι Άδειες Χρήσης", "en": "All Licenses"},
    "lic_admin_no_licenses": {"gr": "Δεν βρέθηκαν καταχωρημένες άδειες.", "en": "No registered licenses found."},
    "lic_admin_filter_users": {"gr": "Φιλτράρισμα Χρηστών...", "en": "Filter Users..."},
    "lic_admin_new_license_expiry": {"gr": "Ημερομηνία Λήξης Άδειας", "en": "License Expiry Date"},
    "lic_admin_select_role": {"gr": "Επιλέξτε Ρόλο", "en": "Select Role"},
    "lic_admin_role_active": {"gr": "Ενεργός", "en": "Active"},
    "lic_admin_role_pending": {"gr": "Εκκρεμής", "en": "Pending"},
    "lic_admin_role_admin": {"gr": "Διαχειριστής", "en": "Admin"},
    "lic_admin_role_inactive": {"gr": "Ανενεργός", "en": "Inactive"},

    # --- NEW: UI Chat Tabs & Upload Specific Messages ---
    "chat_tab_text": {"gr": "Κείμενο", "en": "Text"},
    "chat_tab_voice": {"gr": "Φωνή", "en": "Voice"},
    "chat_tab_upload": {"gr": "Manual Upload", "en": "Manual Upload"},
    "chat_voice_under_dev": {"gr": "🎧 Λειτουργία φωνητικής εντολής υπό ανάπτυξη...", "en": "🎧 Voice command feature under development..."},
    "chat_upload_instructions": {"gr": "Ανεβάστε ένα PDF ή μια εικόνα για να το στείλετε στο AI.", "en": "Upload a PDF or image to send its content to the AI."},
    "chat_uploaded_content_preview": {"gr": "Προεπισκόπηση περιεχομένου:", "en": "Content Preview:"},
    "chat_send_manual_to_ai": {"gr": "Στείλε Manual στο AI", "en": "Send Manual to AI"},
    "chat_load_first_manual": {"gr": "Φόρτωσε πρώτο Manual από Βιβλιοθήκη", "en": "Load first Manual from Library"},
    "chat_no_manuals_in_lib": {"gr": "Δεν βρέθηκαν manuals στη βιβλιοθήκη.", "en": "No manuals found in library."},
    "chat_error_loading_manual": {"gr": "Σφάλμα φόρτωσης manual από βιβλιοθήκη.", "en": "Error loading manual from library."},
    "chat_image_ocr_warning": {"gr": "⚠️ Το AI θα λάβει τη φωτογραφία, αλλά η εξαγωγή κειμένου (OCR) είναι περιορισμένη.", "en": "⚠️ The AI will receive the image, but text extraction (OCR) is limited."},
    "chat_file_too_large": {"gr": "Το αρχείο είναι πολύ μεγάλο για επεξεργασία κειμένου.", "en": "File is too large for text processing."},
    "chat_manual_query_ph": {"gr": "Πες στο AI τι να κάνει με το manual...", "en": "Tell the AI what to do with the manual..."},


}

def get_text(key: str, lang: str = 'gr') -> str:
    """
    Ανακτά το μεταφρασμένο κείμενο για ένα δεδομένο κλειδί και γλώσσα.
    """
    if key in LANGUAGE_PACK:
        if lang in LANGUAGE_PACK[key]:
            return LANGUAGE_PACK[key][lang]
        else:
            return LANGUAGE_PACK[key].get('gr', f"Missing '{lang}' translation for key '{key}'")
    else:
        return f"MISSING_TEXT_KEY[{key}]"