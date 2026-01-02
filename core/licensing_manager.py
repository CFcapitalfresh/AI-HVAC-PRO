"""
CORE MODULE: LICENSING MANAGER
------------------------------
Manages application licensing for future native desktop/mobile applications.
For now, it's a placeholder, primarily checking user roles.
"""

import streamlit as st
import logging
from core.db_connector import DatabaseConnector
from core.language_pack import get_text
from datetime import datetime, timedelta

logger = logging.getLogger("Core.Licensing")

class LicensingManager:
    """
    Διαχειρίζεται τις άδειες χρήσης της εφαρμογής.
    Προς το παρόν, χρησιμοποιεί τον ρόλο του χρήστη ως βασικό έλεγχο.
    Μελλοντικά, μπορεί να ενσωματώσει πιο σύνθετους μηχανισμούς.
    """

    @staticmethod
    def get_license_status(user_email: str, user_role: str) -> dict:
        """
        Ελέγχει την κατάσταση της άδειας χρήσης για έναν συγκεκριμένο χρήστη.
        Args:
            user_email (str): Το email του χρήστη.
            user_role (str): Ο ρόλος του χρήστη (π.χ., 'active', 'admin', 'pending').
        Returns:
            dict: Περιέχει 'status' (valid, expired, invalid, not_found) και 'message'.
        """
        # --- PHASE 1: Simple Role-Based Check ---
        if user_role in ['admin', 'active']:
            return {
                "status": "valid",
                "message": get_text('lic_activated', st.session_state.lang),
                "is_active": True
            }
        elif user_role == 'pending':
            return {
                "status": "pending",
                "message": get_text('reg_success', st.session_state.lang),
                "is_active": False
            }
        else:
            return {
                "status": "invalid",
                "message": get_text('lic_invalid', st.session_state.lang),
                "is_active": False
            }

        # --- FUTURE EXPANSION (Comments for future development) ---
        # 1. Check for a specific license key in a local file or registry (for native apps)
        #    Example: license_key = ConfigLoader.get_local_license_key()
        # 2. Validate license key against an online licensing server
        #    Example: response = requests.post(LICENSE_SERVER_URL, data={'key': license_key, 'email': user_email})
        # 3. Check expiration dates (if subscription-based)
        #    Example: expiry_date = some_logic_to_get_expiry(user_email)
        #    if datetime.now() > expiry_date:
        #        return {"status": "expired", "message": get_text('lic_expired', st.session_state.lang), "is_active": False}
        
        # If no explicit license is found (e.g., in a local file for a native app setup)
        # return {"status": "not_found", "message": get_text('lic_not_found', st.session_state.lang), "is_active": False}

    @staticmethod
    def activate_license(user_email: str, license_key: str) -> dict:
        """
        (Placeholder) Προσπαθεί να ενεργοποιήσει μια άδεια χρήσης.
        Στη φάση 1, απλά επιστρέφει επιτυχία αν ο χρήστης είναι ήδη ενεργός/admin.
        """
        # Retrieve user role (e.g., from DB or session)
        # For current setup, we assume role is already known or passed
        
        # This function would involve:
        # 1. Sending license_key and user_email to a licensing server.
        # 2. Receiving a response (success/fail, expiry date).
        # 3. Storing license info locally (if native app) or updating user role in cloud.
        
        logger.info(f"Attempting to activate license for {user_email} with key {license_key[:5]}...")
        
        # For now, simulate success if a key is provided
        if license_key:
            return {
                "success": True, 
                "message": get_text('lic_activated', st.session_state.lang) + " (Simulated)",
                "status": "valid"
            }
        return {
            "success": False, 
            "message": get_text('lic_invalid', st.session_state.lang) + " (Simulated)",
            "status": "invalid"
        }