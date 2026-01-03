import streamlit as st
import bcrypt
from core.db_connector import DatabaseConnector
from datetime import datetime
import logging
from core.language_pack import get_text # Rule 5

logger = logging.getLogger("Core.Auth")

class AuthManager:
    @staticmethod
    def verify_login(email: str, password: str, use_local_db_for_check: bool = False):
        """
        Ελέγχει τα στοιχεία εισόδου.
        Περιλαμβάνει καθαρισμό (trim) για κινητά και υποστήριξη τοπικής βάσης.
        Args:
            email (str): Email του χρήστη.
            password (str): Κωδικός χρήστη.
            use_local_db_for_check (bool): Αν είναι True, ελέγχει πρώτα την τοπική βάση.
        Returns:
            tuple: (user_data: dict, message: str)
        """
        lang = st.session_state.get('lang', 'gr') # Rule 6

        # 1. ΚΑΘΑΡΙΣΜΟΣ INPUT (Αυτό λύνει το πρόβλημα του κινητού)
        if email:
            email = email.strip().lower()
        else:
            return None, get_text('email_required', lang) if 'email_required' in LANGUAGE_PACK else "Email required"
            
        if password:
            password = password.strip()
        else:
            return None, get_text('pass_required', lang) if 'pass_required' in LANGUAGE_PACK else "Password required"

        user_data = None
        source_db = "Google Sheets"

        # 2. ΕΛΕΓΧΟΣ ΑΠΟ ΤΟΠΙΚΗ ΒΑΣΗ (αν ζητηθεί)
        if use_local_db_for_check:
            try: # Rule 4: Error Handling
                local_users_df = DatabaseConnector.fetch_data("Users", use_local_db=True)
                if not local_users_df.empty:
                    local_user = local_users_df[local_users_df['email'] == email]
                    if not local_user.empty:
                        user_data = local_user.iloc[0]
                        source_db = "SQLite Local"
                        logger.info(f"User '{email}' found in local SQLite.") # Rule 4
            except Exception as e:
                logger.error(f"Error fetching local users for login: {e}", exc_info=True) # Rule 4

        # 3. ΕΛΕΓΧΟΣ ΑΠΟ CLOUD ΒΑΣΗ (αν δεν βρέθηκε τοπικά ή αν δεν ζητήθηκε τοπικός έλεγχος)
        if user_data is None:
            try: # Rule 4: Error Handling
                users_df = DatabaseConnector.fetch_data("Users") # GSheets
                if not users_df.empty:
                    cloud_user = users_df[users_df['email'] == email]
                    if not cloud_user.empty:
                        user_data = cloud_user.iloc[0]
                        source_db = "Google Sheets"
                        logger.info(f"User '{email}' found in Google Sheets.") # Rule 4
                else:
                    return None, get_text('no_users_found_db', lang) if 'no_users_found_db' in LANGUAGE_PACK else "No users found in database(s)"
            except Exception as e:
                logger.error(f"Error fetching cloud users for login: {e}", exc_info=True) # Rule 4
                return None, f"{get_text('auth_db_conn_error', lang) if 'auth_db_conn_error' in LANGUAGE_PACK else 'Database connection error'}: {e}"


        if user_data is None: 
            return None, get_text('user_not_found', lang) if 'user_not_found' in LANGUAGE_PACK else "User not found"
        
        stored_hash = user_data['password_hash']
        
        # 4. ΕΛΕΓΧΟΣ ΚΩΔΙΚΟΥ
        try: # Rule 4: Error Handling
            # Περίπτωση Α: Παλιός κωδικός (απλό κείμενο - Legacy)
            if not stored_hash or not stored_hash.startswith('$2b$'): # Add check for empty stored_hash
                if stored_hash == password:
                    if user_data['role'] == 'active' or user_data['role'] == 'admin':
                        logger.info(f"User '{email}' logged in successfully from {source_db}.") # Rule 4
                        return user_data.to_dict(), "OK"
                    else:
                        logger.warning(f"Login failed for '{email}': Account pending approval.") # Rule 4
                        return None, get_text('account_pending_approval', lang) if 'account_pending_approval' in LANGUAGE_PACK else "Account Pending Approval"
                else:
                    logger.warning(f"Login failed for '{email}'. Wrong password (legacy check).") # Rule 4
                    return None, get_text('wrong_password', lang) if 'wrong_password' in LANGUAGE_PACK else "Wrong password"
            
            # Περίπτωση Β: Νέος ασφαλής κωδικός (Hash - Bcrypt)
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                if user_data['role'] == 'active' or user_data['role'] == 'admin':
                    logger.info(f"User '{email}' logged in successfully from {source_db}.") # Rule 4
                    return user_data.to_dict(), "OK"
                else:
                    logger.warning(f"Login failed for '{email}': Account pending approval.") # Rule 4
                    return None, get_text('account_pending_approval', lang) if 'account_pending_approval' in LANGUAGE_PACK else "Account Pending Approval"
            else:
                logger.warning(f"Failed login attempt for '{email}'. Wrong password (bcrypt check).") # Rule 4
                return None, get_text('wrong_password', lang) if 'wrong_password' in LANGUAGE_PACK else "Wrong password"
        except Exception as e:
            logger.error(f"Auth Error for '{email}': {str(e)}", exc_info=True) # Rule 4
            return None, f"{get_text('auth_error', lang) if 'auth_error' in LANGUAGE_PACK else 'Auth Error'}: {str(e)}"

    @staticmethod
    def register_new_user(email: str, name: str, password: str) -> bool:
        """
        Εγγράφει νέο χρήστη ως 'pending' στα Google Sheets.
        Επίσης, προσθέτει τον χρήστη στην τοπική SQLite βάση ως 'pending' για μελλοντική χρήση.
        """
        lang = st.session_state.get('lang', 'gr') # Rule 6

        # 1. ΚΑΘΑΡΙΣΜΟΣ INPUT
        if email: email = email.strip().lower()
        if name: name = name.strip()
        if password: password = password.strip()

        if not email or not password:
            logger.warning("Attempted registration with missing email or password.") # Rule 4
            st.warning(get_text('email_pass_required', lang) if 'email_pass_required' in LANGUAGE_PACK else "Email and password are required.") # Rule 5
            return False

        # 2. ΕΛΕΓΧΟΣ ΑΝ ΥΠΑΡΧΕΙ ΗΔΗ ΣΕ GSheets
        try: # Rule 4: Error Handling
            users_gsheets = DatabaseConnector.fetch_data("Users")
            if not users_gsheets.empty and email in users_gsheets['email'].values:
                logger.warning(f"Registration attempt for existing email: {email}") # Rule 4
                st.warning(get_text('reg_email_exists', lang)) # Rule 5
                return False
        except Exception as e:
            logger.error(f"Error checking existing users during registration: {e}", exc_info=True) # Rule 4
            st.error(f"{get_text('reg_fail', lang)}: {e}") # Rule 5
            return False

        # 3. ΚΡΥΠΤΟΓΡΑΦΗΣΗ (HASHING)
        try: # Rule 4: Error Handling
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password during registration for {email}: {e}", exc_info=True) # Rule 4
            st.error(f"{get_text('reg_fail', lang)}: {e}") # Rule 5
            return False
        
        # 4. ΔΗΜΙΟΥΡΓΙΑ ΕΓΓΡΑΦΗΣ
        new_user_data = [
            str(datetime.now()), # Timestamp
            email,
            name,
            hashed,
            "pending" # Role (Μπαίνει ως 'pending' και θέλει έγκριση από Admin)
        ]
        
        # 5. ΑΠΟΘΗΚΕΥΣΗ ΣΕ GOOGLE SHEETS
        gsheets_success = False
        try: # Rule 4: Error Handling
            gsheets_success = DatabaseConnector.append_data("Users", new_user_data, use_local_db=False)
            if not gsheets_success:
                logger.error(f"Failed to append new user '{email}' to Google Sheets.") # Rule 4
        except Exception as e:
            logger.error(f"Error appending new user '{email}' to GSheets: {e}", exc_info=True) # Rule 4

        # 6. ΑΠΟΘΗΚΕΥΣΗ ΣΕ ΤΟΠΙΚΗ SQLITE (ανεξάρτητα από GSheets για αντοχή)
        sqlite_success = False
        try: # Rule 4: Error Handling
            sqlite_success = DatabaseConnector.append_data("Users", new_user_data, use_local_db=True)
            if not sqlite_success:
                logger.error(f"Failed to append new user '{email}' to local SQLite.") # Rule 4
        except Exception as e:
            logger.error(f"Error appending new user '{email}' to SQLite: {e}", exc_info=True) # Rule 4

        return gsheets_success or sqlite_success # Θεωρούμε επιτυχημένη την εγγραφή αν αποθηκευτεί έστω σε μία βάση

    @staticmethod
    def log_interaction(user_email: str, action: str, description: str):
        """
        Καταγράφει μια αλληλεπίδραση χρήστη στο φύλλο "Logs" (και στην τοπική SQLite).
        """
        try: # Rule 4: Error Handling
            log_entry_values = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user_email,
                action,
                description
            ]
            
            # Προσθήκη σε Google Sheets
            gsheets_logged = DatabaseConnector.append_data("Logs", log_entry_values, use_local_db=False)
            if not gsheets_logged:
                logger.warning(f"Failed to log interaction to GSheets for user '{user_email}'.")

            # Προσθήκη σε τοπική SQLite
            sqlite_logged = DatabaseConnector.append_data("Logs", log_entry_values, use_local_db=True)
            if not sqlite_logged:
                logger.warning(f"Failed to log interaction to SQLite for user '{user_email}'.")

            if gsheets_logged or sqlite_logged:
                logger.info(f"Interaction logged: {action} by {user_email}")
            else:
                logger.error(f"Failed to log interaction anywhere for user '{user_email}'.")

        except Exception as e:
            logger.error(f"Critical error logging interaction for '{user_email}': {e}", exc_info=True) # Rule 4