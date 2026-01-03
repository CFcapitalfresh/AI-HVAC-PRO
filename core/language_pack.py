"""
CORE: LANGUAGE PACK
-------------------
Centralizes all text strings for multilingual support.
"""

TRANS = {
    # --- GENERAL UI ---
    'app_title': {'gr': "Mastro Nek AI | Platinum", 'en': "Mastro Nek AI | Platinum"},
    'menu_header': {'gr': "Πλοήγηση", 'en': "Navigation"},
    'menu_dashboard': {'gr': "📊 Επισκόπηση", 'en': "📊 Dashboard"},
    'menu_chat': {'gr': "💬 AI Συνομιλία", 'en': "💬 AI Chat"},
    'menu_library': {'gr': "🔎 Βιβλιοθήκη Manuals", 'en': "🔎 Manuals Library"},
    'menu_organizer': {'gr': "📅 AI Organizer", 'en': "📅 AI Organizer"},
    'menu_clients': {'gr': "📇 Πελατολόγιο", 'en': "📇 Client CRM"},
    'menu_tools': {'gr': "🛠️ Εργαλεία", 'en': "🛠️ Tools"},
    'menu_admin': {'gr': "⚙️ Διαχείριση", 'en': "⚙️ Admin Panel"},
    'logout': {'gr': "🚪 Αποσύνδεση", 'en': "🚪 Logout"},
    'new_chat_side': {'gr': "🧹 Νέα Συνομιλία", 'en': "🧹 New Chat"},

    # --- DASHBOARD ---
    'dash_welcome': {'gr': "👋 Καλωσήρθες", 'en': "👋 Welcome"},
    'dash_subtitle': {'gr': "Κέντρο Ελέγχου Τεχνικής Υποστήριξης", 'en': "Technical Support Control Center"},
    'dash_quick': {'gr': "🚀 Γρήγορες Ενέργειες", 'en': "🚀 Quick Actions"},
    'dash_chat_card': {'gr': "AI Τεχνικός Βοηθός", 'en': "AI Technical Assistant"},
    'dash_chat_desc': {'gr': "Διάγνωση βλαβών & Λύσεις", 'en': "Diagnosis & Solutions"},
    'dash_btn_chat': {'gr': "💬 Έναρξη Συνομιλίας", 'en': "💬 Start Chat"},
    'dash_lib_card': {'gr': "Βιβλιοθήκη Manuals", 'en': "Manuals Library"},
    'dash_lib_desc': {'gr': "Αναζήτηση Εγχειριδίων", 'en': "Search Manuals"},
    'dash_btn_lib': {'gr': "🔎 Αναζήτηση", 'en': "🔎 Search"},
    'dash_tool_card': {'gr': "Εργαλεία HVAC", 'en': "HVAC Tools"},
    'dash_tool_desc': {'gr': "BTU Calc & Μετατροπές", 'en': "BTU Calc & Converters"},
    'dash_btn_tool': {'gr': "🛠️ Άνοιγμα Εργαλείων", 'en': "🛠️ Open Tools"},
    'dash_status': {'gr': "Κατάσταση Συστήματος: 🟢 Online | AI Engine: Ready", 'en': "System Status: 🟢 Online | AI Engine: Ready"},

    # --- CHAT & MEDIA ---
    'chat_placeholder': {'gr': "Περιγράψτε το πρόβλημα...", 'en': "Describe the issue..."},
    'chat_thinking': {'gr': "🤔 Ο Mastro Nek αναλύει...", 'en': "🤔 Mastro Nek is thinking..."},
    'chat_intro': {'gr': "👋 Γεια σου! Ρώτησέ με για βλάβες ή manuals.", 'en': "👋 Hello! Ask me about faults or manuals."},
    'media_expander': {'gr': "📸 Κάμερα & 🎙️ Φωνητική Εντολή", 'en': "📸 Camera & 🎙️ Voice Input"},
    'camera_label': {'gr': "📸 Τράβηξε Φωτογραφία", 'en': "📸 Take Photo"},
    'audio_label': {'gr': "🎙️ Ηχογράφηση / Αρχείο Ήχου", 'en': "🎙️ Voice Message / Audio File"},
    'media_sent': {'gr': "✅ Τα αρχεία επισυνάφθηκαν!", 'en': "✅ Files attached!"},
    'brand_label': {'gr': "Επιλογή Μάρκας", 'en': "Select Brand"},
    'model_label': {'gr': "Μοντέλο", 'en': "Model"},
    'manual_retrieval_error': {'gr': "Σφάλμα ανάκτησης manual: {error}", 'en': "Manual retrieval error: {error}"},
    'manuals_found': {'gr': "Βρέθηκαν {count} σχετικά manuals.", 'en': "{count} relevant manuals found."},
    'no_manuals': {'gr': "Δεν βρέθηκαν manuals για τη μάρκα/μοντέλο.", 'en': "No manuals found for brand/model."},
    'select_brand_for_search': {'gr': "Επιλέξτε μάρκα για αναζήτηση.", 'en': "Select a brand to search."},
    'chat_input_placeholder': {'gr': "Περιγράψτε το πρόβλημα ή τον κωδικό βλάβης...", 'en': "Describe the issue or error code..."},
    'voice_input_help': {'gr': "Χρησιμοποιήστε μικρόφωνο για φωνητική εντολή.", 'en': "Use microphone for voice input."},
    'voice_input_activated': {'gr': "Αναμονή για φωνητική εντολή...", 'en': "Waiting for voice input..."},
    'upload_manual_label': {'gr': "Ανεβάστε PDF/Εικόνες", 'en': "Upload PDF/Images"},
    'upload_manual_help': {'gr': "Ανεβάστε αρχεία για ανάλυση από το AI.", 'en': "Upload files for AI analysis."},
    'processing_uploaded_file': {'gr': "Επεξεργασία ανεβασμένου αρχείου: '{name}'", 'en': "Processing uploaded file: '{name}'"},
    'studying_sources': {'gr': "Μελετώ {count} πηγές...", 'en': "Studying {count} sources..."},
    'download_error': {'gr': "Σφάλμα κατά το κατέβασμα '{filename}': {error}", 'en': "Error downloading '{filename}': {error}"},
    'analyzing': {'gr': "Αναλύω...", 'en': "Analyzing..."},
    'ai_engine_error': {'gr': "Σφάλμα AI Engine: {error}", 'en': "AI Engine Error: {error}"},
    'tab_text': {'gr': "Κείμενο", 'en': "Text"},
    'tab_voice': {'gr': "Φωνή", 'en': "Voice"},
    'tab_upload': {'gr': "Upload", 'en': "Upload"},

    # --- TOOLS (BTU) ---
    'tool_btu_tab': {'gr': "❄️ BTU Calculator", 'en': "❄️ BTU Calculator"},
    'tool_conv_tab': {'gr': "📏 Μετατροπέας", 'en': "📏 Converter"},
    'tool_pipe_tab': {'gr': "🔥 Σωληνώσεις", 'en': "🔥 Piping Guide"},
    'tool_area': {'gr': "Τετραγωνικά (m²)", 'en': "Area (m²)"},
    'tool_height': {'gr': "Ύψος Χώρου (m)", 'en': "Ceiling Height (m)"},
    'tool_insulation': {'gr': "Μόνωση", 'en': "Insulation"},
    'tool_sun': {'gr': "Προσανατολισμός", 'en': "Sun Exposure"},
    'tool_calc_res': {'gr': "Απαιτούμενη Ισχύς", 'en': "Required Capacity"},
    'tool_rec': {'gr': "Προτεινόμενο", 'en': "Recommended"},
    'ins_good': {'gr': "Καλή (Νέα Κουφώματα)", 'en': "Good (New Frames)"},
    'ins_avg': {'gr': "Μέτρια (Διπλά Τζάμια 10ετ.)", 'en': "Average (Double Glazed)"},
    'ins_bad': {'gr': "Κακή (Μονά/Αμόνωτο)", 'en': "Poor (Single Glazed)"},
    'sun_low': {'gr': "Σκιερό / Βόρειο", 'en': "Shady / North"},
    'sun_med': {'gr': "Μέτρια Ηλιοφάνεια", 'en': "Medium Sun"},
    'sun_high': {'gr': "Πολύ Ήλιος / Ρετιρέ", 'en': "High Sun / Roof"},
    'pipe_liquid': {'gr': "Υγρού (Liquid)", 'en': "Liquid Line"},
    'pipe_gas': {'gr': "Αερίου (Gas)", 'en': "Gas Line"},

    # --- ORGANIZER ---
    'org_title': {'gr': "📅 AI Organizer", 'en': "📅 AI Organizer"},
    'org_desc': {'gr': "🤖 **AI Auto-Sorter**<br>Σαρώνει και ταξινομεί αρχεία.", 'en': "🤖 **AI Auto-Sorter**<br>Scans and sorts files automatically."},
    'org_start': {'gr': "Έναρξη Ταξινόμησης", 'en': "Start Sorting"},
    'org_log': {'gr': "📜 Καταγραφή (Live Log)", 'en': "📜 Live Log"},

    # --- CLIENTS ---
    'client_search': {'gr': "🔍 Αναζήτηση Πελάτη...", 'en': "🔍 Search Client..."},
    'client_found': {'gr': "Βρέθηκαν", 'en': "Found"},
    'client_empty': {'gr': "Η λίστα είναι κενή.", 'en': "Client list is empty."},

    # --- DIAGNOSTICS (NEW) ---
    'diag_title': {'gr': "🔧 Active Diagnostics / Διαδραστικός Οδηγός", 'en': "🔧 Active Diagnostics / Interactive Wizard"},
    'diag_subtitle': {'gr': "Οδηγός Επίλυσης Βλαβών βήμα-προς-βήμα με AI", 'en': "Step-by-Step AI Troubleshooting Wizard"},
    'diag_step': {'gr': "Βήμα", 'en': "Step"},
    'diag_action': {'gr': "Ενέργεια:", 'en': "Action:"},
    'diag_question': {'gr': "❓ Ερώτηση:", 'en': "❓ Question:"},
    'diag_yes': {'gr': "✅ ΝΑΙ / Λύθηκε", 'en': "✅ YES / Solved"},
    'diag_solved_msg': {'gr': "Το πρόβλημα επιλύθηκε!", 'en': "Problem solved!"},
    'diag_no': {'gr': "❌ ΟΧΙ / Συνέχεια", 'en': "❌ NO / Continue"},
    'diag_cancel': {'gr': "⚠️ Ακύρωση", 'en': "⚠️ Cancel"},
    'help_title': {'gr': "Βοήθεια", 'en': "Help"},
}

def get_text(key: str, lang: str = 'gr') -> str:
    """Retrieves text from the language pack based on key and language."""
    return TRANS.get(key, {}).get(lang, f"[{key}]")