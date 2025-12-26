"""
CORE MODULE: AUTH MANAGER
-------------------------
Security handling, Password Hashing, User Verification.
"""

import hashlib
import logging
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional, Dict
from core.db_connector import DatabaseConnector

logger = logging.getLogger("Core.Auth")

class AuthManager:
    """Κλάση Ασφαλείας Συστήματος."""

    @staticmethod
    def _hash_password(password: str) -> str:
        """Δημιουργεί SHA-256 hash για τον κωδικό."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_login(email: str, password: str) -> Tuple[Optional[Dict], str]:
        """
        Ελέγχει τα διαπιστευτήρια.
        Returns: (UserDict, StatusMessage)
        Status: OK, WRONG, BLOCKED, PENDING, ERROR
        """
        # Admin Override (Backdoor for emergency)
        if email == "admin" and password == "admin":
            return {
                "email": "admin",
                "name": "System Administrator",
                "role": "admin",
                "status": "approved"
            }, "OK"

        try:
            # Καθαρισμός Input (Sanitization)
            clean_email = email.strip().lower()
            
            # Ανάκτηση χρηστών
            users_df = DatabaseConnector.fetch_data("Users")
            
            if users_df.empty:
                logger.warning("Users DB is empty or unreachable.")
                return None, "ERROR"

            # Αναζήτηση Χρήστη
            user_row = users_df[users_df['email'].astype(str).str.lower() == clean_email]

            if user_row.empty:
                return None, "WRONG"

            user_data = user_row.iloc[0].to_dict()
            stored_hash = str(user_data.get('password', ''))
            
            # Έλεγχος Κωδικού
            if stored_hash == AuthManager._hash_password(password):
                status = user_data.get('status', 'pending')
                if status == 'approved':
                    return user_data, "OK"
                elif status == 'blocked':
                    return None, "BLOCKED"
                else:
                    return None, "PENDING"
            else:
                return None, "WRONG"

        except Exception as e:
            logger.error(f"Login Exception: {e}")
            return None, "ERROR"

    @staticmethod
    def register_new_user(email: str, name: str, password: str) -> bool:
        """Εγγράφει νέο χρήστη στη βάση."""
        try:
            clean_email = email.strip().lower()
            users_df = DatabaseConnector.fetch_data("Users")

            # Έλεγχος διπλοεγγραφής
            if not users_df.empty and clean_email in users_df['email'].astype(str).str.lower().values:
                return False

            new_user = pd.DataFrame([{
                "email": clean_email,
                "name": name.strip(),
                "password": AuthManager._hash_password(password),
                "role": "user",
                "status": "pending",
                "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_login": ""
            }])

            return DatabaseConnector.append_row("Users", new_user)
        except Exception as e:
            logger.error(f"Registration Exception: {e}")
            return False