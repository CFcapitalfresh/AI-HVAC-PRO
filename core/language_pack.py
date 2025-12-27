"""
CORE MODULE: LANGUAGE PACK
--------------------------
Central dictionary for all UI text strings.
Supports: Greek ('gr'), English ('en')
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

    # --- ADMIN PANEL ---
    'admin_title': {'gr': "⚙️ Κέντρο Διαχείρισης (Admin Panel)", 'en': "⚙️ Admin Control Center"},
    'admin_pending': {'gr': "🔔 Εκκρεμή Αιτήματα", 'en': "🔔 Pending Requests"},
    'admin_no_pending': {'gr': "✅ Όλα ήσυχα! Κανένα νέο αίτημα.", 'en': "✅ All clear! No new requests."},
    'admin_btn_activate': {'gr': "✅ Ενεργοποίηση", 'en': "✅ Activate"},
    'admin_btn_delete': {'gr': "🗑️ Διαγραφή", 'en': "🗑️ Delete"},
    'admin_msg_active': {'gr': "Ο χρήστης ενεργοποιήθηκε!", 'en': "User activated!"},
    'admin_msg_del': {'gr': "Το αίτημα διαγράφηκε.", 'en': "Request deleted."},
    'admin_all_users': {'gr': "👥 Προβολή Όλων των Χρηστών", 'en': "👥 View All Users"},
    'admin_all_users_cap': {'gr': "Εδώ βλέπετε όλους τους εγγεγραμμένους χρήστες.", 'en': "List of all registered users."},
    'admin_no_users': {'gr': "Δεν βρέθηκαν χρήστες.", 'en': "No users found."},

    # --- CHAT & MEDIA ---
    'chat_placeholder': {'gr': "Περιγράψτε το πρόβλημα...", 'en': "Describe the issue..."},
    'chat_thinking': {'gr': "🤔 Ο Mastro Nek αναλύει...", 'en': "🤔 Mastro Nek is thinking..."},
    'chat_intro': {'gr': "👋 Γεια σου! Ρώτησέ με για βλάβες ή manuals.", 'en': "👋 Hello! Ask me about faults or manuals."},
    'media_expander': {'gr': "📸 Κάμερα & 🎙️ Φωνητική Εντολή", 'en': "📸 Camera & 🎙️ Voice Input"},
    'camera_label': {'gr': "📸 Τράβηξε Φωτογραφία", 'en': "📸 Take Photo"},
    'audio_label': {'gr': "🎙️ Ηχογράφηση / Αρχείο Ήχου", 'en': "🎙️ Voice Message / Audio File"},
    'media_sent': {'gr': "✅ Τα αρχεία επισυνάφθηκαν!", 'en': "✅ Files attached!"},

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
    
    # --- LOGIN ---
    'login_tab': {'gr': "Είσοδος", 'en': "Login"},
    'register_tab': {'gr': "Εγγραφή", 'en': "Register"},
    'email_lbl': {'gr': "Email", 'en': "Email"},
    'pass_lbl': {'gr': "Κωδικός", 'en': "Password"},
    'name_lbl': {'gr': "Όνομα", 'en': "Name"},
    'btn_login': {'gr': "Είσοδος", 'en': "Login"},
    'btn_register': {'gr': "Εγγραφή", 'en': "Register"},
    'login_success': {'gr': "Επιτυχής Είσοδος!", 'en': "Login Successful!"},
    'reg_success': {'gr': "Η εγγραφή ολοκληρώθηκε!", 'en': "Registration complete!"}
}

def get_text(key: str, lang: str = 'gr') -> str:
    return TRANS.get(key, {}).get(lang, f"[{key}]")