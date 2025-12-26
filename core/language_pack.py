"""
CORE MODULE: LANGUAGE PACK
--------------------------
Central dictionary for all UI text strings.
Supports: Greek ('gr'), English ('en')
"""

TRANS = {
    # --- GENERAL UI ---
    'app_title': {
        'gr': "Mastro Nek AI | Platinum",
        'en': "Mastro Nek AI | Platinum"
    },
    'welcome_msg': {
        'gr': "Καλωσήρθες στο επαγγελματικό σύστημα υποστήριξης HVAC.",
        'en': "Welcome to the professional HVAC support system."
    },
    'loading': {
        'gr': "Φόρτωση...",
        'en': "Loading..."
    },
    
    # --- SIDEBAR MENU ---
    'menu_header': {'gr': "Πλοήγηση", 'en': "Navigation"},
    'menu_chat': {'gr': "💬 Συνομιλία (AI)", 'en': "💬 Chat (AI)"},
    'menu_library': {'gr': "🔎 Βιβλιοθήκη Manuals", 'en': "🔎 Manuals Library"},
    'menu_organizer': {'gr': "🧠 AI Organizer", 'en': "🧠 AI Organizer"},
    'menu_clients': {'gr': "📇 Πελατολόγιο", 'en': "📇 Client CRM"},
    'menu_tools': {'gr': "🧮 Εργαλεία", 'en': "🧮 Tools"},
    'menu_help': {'gr': "❓ Βοήθεια Χρήστη", 'en': "❓ User Help"},
    'menu_admin': {'gr': "⚙️ Admin Panel", 'en': "⚙️ Admin Panel"},
    'menu_specs': {'gr': "🧬 Τεχνική Ανάλυση", 'en': "🧬 System Specs"},
    'logout': {'gr': "🚪 Αποσύνδεση", 'en': "🚪 Logout"},

    # --- LOGIN SCREEN ---
    'login_prompt': {'gr': "Σύνδεση στο Σύστημα", 'en': "System Login"},
    'email_lbl': {'gr': "Email Χρήστη", 'en': "User Email"},
    'pass_lbl': {'gr': "Κωδικός Πρόσβασης", 'en': "Password"},
    'btn_login': {'gr': "Είσοδος", 'en': "Login"},
    'btn_register': {'gr': "Εγγραφή Νέου", 'en': "Register New"},
    'error_auth': {'gr': "❌ Λάθος στοιχεία ή μη ενεργός λογαριασμός.", 'en': "❌ Invalid credentials or inactive account."},
    'pending_auth': {'gr': "⏳ Ο λογαριασμός σας αναμένει έγκριση.", 'en': "⏳ Account pending approval."},
    
    # --- ORGANIZER ---
    'org_title': {'gr': "Έξυπνη Ταξινόμηση Εγγράφων", 'en': "Smart Document Sorting"},
    'org_start': {'gr': "🚀 Έναρξη AI Ανάλυσης", 'en': "🚀 Start AI Analysis"},
    'org_scan': {'gr': "Σάρωση φακέλου...", 'en': "Scanning directory..."},
    'org_success': {'gr': "Η ταξινόμηση ολοκληρώθηκε.", 'en': "Sorting completed."},

    # --- HELP ---
    'help_title': {'gr': "Οδηγός Χρήσης", 'en': "User Manual"},
    
    # --- TECH SPECS ---
    'specs_title': {'gr': "Τεχνικές Προδιαγραφές Συστήματος", 'en': "System Technical Specifications"}
}

def get_text(key: str, lang: str = 'gr') -> str:
    """Safely retrieves text based on language code."""
    try:
        return TRANS.get(key, {}).get(lang, f"[{key}]")
    except Exception:
        return f"ERR:{key}"