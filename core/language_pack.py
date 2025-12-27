"""
CORE MODULE: LANGUAGE PACK
--------------------------
Central dictionary for all UI text strings.
Supports: Greek ('gr'), English ('en')
"""

TRANS = {
    # --- GENERAL UI ---
    'app_title': {'gr': "Mastro Nek AI | Platinum", 'en': "Mastro Nek AI | Platinum"},
    'welcome_msg': {'gr': "Καλωσήρθες", 'en': "Welcome"},
    'loading': {'gr': "Φόρτωση...", 'en': "Loading..."},
    
    # --- SIDEBAR MENU ---
    'menu_header': {'gr': "Πλοήγηση", 'en': "Navigation"},
    'lang_select': {'gr': "Γλώσσα / Language", 'en': "Language / Γλώσσα"},
    'menu_dashboard': {'gr': "📊 Επισκόπηση (Dashboard)", 'en': "📊 Dashboard"},
    'menu_chat': {'gr': "💬 AI Συνομιλία", 'en': "💬 AI Chat"},
    'menu_library': {'gr': "🔎 Βιβλιοθήκη Manuals", 'en': "🔎 Manuals Library"},
    'menu_organizer': {'gr': "📅 AI Organizer", 'en': "📅 AI Organizer"},
    'menu_clients': {'gr': "📇 Πελατολόγιο", 'en': "📇 Client CRM"},
    'menu_tools': {'gr': "🛠️ Εργαλεία", 'en': "🛠️ Tools"},
    'menu_admin': {'gr': "⚙️ Διαχείριση (Admin)", 'en': "⚙️ Admin Panel"},
    'logout': {'gr': "🚪 Αποσύνδεση", 'en': "🚪 Logout"},

    # --- DASHBOARD ---
    'dash_quick': {'gr': "🚀 Γρήγορες Ενέργειες", 'en': "🚀 Quick Actions"},
    'dash_chat_card': {'gr': "AI Τεχνικός Βοηθός", 'en': "AI Technical Assistant"},
    'dash_chat_desc': {'gr': "Διάγνωση βλαβών & Λύσεις", 'en': "Diagnosis & Solutions"},
    'dash_btn_chat': {'gr': "💬 Έναρξη Συνομιλίας", 'en': "💬 Start Chat"},
    'dash_lib_card': {'gr': "Βιβλιοθήκη Manuals", 'en': "Manuals Library"},
    'dash_lib_desc': {'gr': "Αναζήτηση Εγχειριδίων", 'en': "Search Manuals"},
    'dash_btn_lib': {'gr': "🔎 Αναζήτηση", 'en': "🔎 Search"},
    'dash_tool_card': {'gr': "Εργαλεία HVAC", 'en': "HVAC Tools"},
    'dash_tool_desc': {'gr': "BTU Calc & Μετατροπές", 'en': "BTU Calc & Converters"},
    'dash_btn_tool': {'gr': "🛠️ Άνοιγμα", 'en': "🛠️ Open"},

    # --- CHAT ---
    'chat_new_btn': {'gr': "🧹 Νέα Συνομιλία", 'en': "🧹 New Chat"},
    'chat_placeholder': {'gr': "Περιγράψτε το πρόβλημα ή τον κωδικό βλάβης...", 'en': "Describe the issue or error code..."},
    'chat_thinking': {'gr': "🤔 Ο Mastro Nek αναλύει...", 'en': "🤔 Mastro Nek is thinking..."},
    
    # --- TOOLS ---
    'tool_btu_title': {'gr': "Υπολογισμός Ψυκτικών Φορτίων", 'en': "Cooling Load Calculator"},
    'tool_area': {'gr': "Τετραγωνικά Μέτρα (m²)", 'en': "Area (m²)"},
    'tool_height': {'gr': "Ύψος Χώρου (m)", 'en': "Height (m)"},
    'tool_insulation': {'gr': "Μόνωση", 'en': "Insulation"},
    'tool_sun': {'gr': "Προσανατολισμός", 'en': "Sun Exposure"},
    'tool_result': {'gr': "Απαιτούμενη Ισχύς", 'en': "Required Power"},
    
    # --- LOGIN ---
    'login_tab': {'gr': "Είσοδος", 'en': "Login"},
    'register_tab': {'gr': "Νέα Εγγραφή", 'en': "Register"},
    'email_lbl': {'gr': "Email", 'en': "Email"},
    'pass_lbl': {'gr': "Κωδικός", 'en': "Password"},
    'name_lbl': {'gr': "Ονοματεπώνυμο", 'en': "Full Name"},
    'btn_login': {'gr': "Είσοδος", 'en': "Login"},
    'btn_register': {'gr': "Εγγραφή", 'en': "Register"},
    'login_success': {'gr': "Επιτυχής Είσοδος!", 'en': "Login Successful!"},
    'reg_success': {'gr': "Η εγγραφή ολοκληρώθηκε! Αναμείνατε έγκριση.", 'en': "Registration complete! Await approval."}
}

def get_text(key: str, lang: str = 'gr') -> str:
    """Safely retrieves text based on language code."""
    return TRANS.get(key, {}).get(lang, f"[{key}]")