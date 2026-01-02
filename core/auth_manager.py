import streamlit as st
import bcrypt
from core.db_connector import DatabaseConnector
from datetime import datetime
import logging

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
        # 1. ΚΑΘΑΡΙΣΜΟΣ INPUT (Αυτό λύνει το πρόβλημα του κινητού)
        if email:
            email = email.strip().lower()
        else:
            return None, "Email required"
            
        if password:
            password = password.strip()
        else:
            return None, "Password required"

        user_data = None
        source_db = "Google Sheets"

        # 2. ΕΛΕΓΧΟΣ ΑΠΟ ΤΟΠΙΚΗ ΒΑΣΗ (αν ζητηθεί)
        if use_local_db_for_check:
            local_users_df = DatabaseConnector.fetch_data("Users", use_local_db=True)
            if not local_users_df.empty:
                local_user = local_users_df[local_users_df['email'] == email]
                if not local_user.empty:
                    user_data = local_user.iloc[0]
                    source_db = "SQLite Local"
                    logger.info(f"User '{email}' found in local SQLite.")

        # 3. ΕΛΕΓΧΟΣ ΑΠΟ CLOUD ΒΑΣΗ (αν δεν βρέθηκε τοπικά ή αν δεν ζητήθηκε τοπικός έλεγχος)
        if user_data is None:
            users_df = DatabaseConnector.fetch_data("Users") # GSheets
            if not users_df.empty:
                cloud_user = users_df[users_df['email'] == email]
                if not cloud_user.empty:
                    user_data = cloud_user.iloc[0]
                    source_db = "Google Sheets"
                    logger.info(f"User '{email}' found in Google Sheets.")
            else:
                return None, "No users found in database(s)"

        if user_data is None: 
            return None, "User not found"
        
        stored_hash = user_data['password_hash']
        
        # 4. ΕΛΕΓΧΟΣ ΚΩΔΙΚΟΥ
        try:
            # Περίπτωση Α: Παλιός κωδικός (απλό κείμενο - Legacy)
            if not stored_hash.startswith('$2b$'):
                if stored_hash == password:
                    if user_data['role'] == 'active' or user_data['role'] == 'admin':
                        logger.info(f"User '{email}' logged in successfully from {source_db}.")
                        return user_data.to_dict(), "OK"
                    else:
                        return None, "Account Pending Approval"
                else:
                    logger.warning(f"Failed login attempt for '{email}'. Wrong password (legacy check).")
                    return None, "Wrong password"
            
            # Περίπτωση Β: Νέος ασφαλής κωδικός (Hash - Bcrypt)
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                if user_data['role'] == 'active' or user_data['role'] == 'admin':
                    logger.info(f"User '{email}' logged in successfully from {source_db}.")
                    return user_data.to_dict(), "OK"
                else:
                    return None, "Account Pending Approval"
            else:
                logger.warning(f"Failed login attempt for '{email}'. Wrong password (bcrypt check).")
                return None, "Wrong password"
        except Exception as e:
            logger.error(f"Auth Error for '{email}': {str(e)}", exc_info=True)
            return None, f"Auth Error: {str(e)}"

    @staticmethod
    def register_new_user(email: str, name: str, password: str) -> bool:
        """
        Εγγράφει νέο χρήστη ως 'pending' στα Google Sheets.
        Επίσης, προσθέτει τον χρήστη στην τοπική SQLite βάση ως 'pending' για μελλοντική χρήση.
        """
        # 1. ΚΑΘΑΡΙΣΜΟΣ INPUT
        if email: email = email.strip().lower()
        if name: name = name.strip()
        if password: password = password.strip()

        if not email or not password:
            st.error("Email και Κωδικός απαιτούνται.")
            return False

        # 2. ΕΛΕΓΧΟΣ ΑΝ ΥΠΑΡΧΕΙ ΗΔΗ ΣΕ GSheets
        users_gsheets = DatabaseConnector.fetch_data("Users")
        if not users_gsheets.empty and email in users_gsheets['email'].values:
            st.warning("Το email υπάρχει ήδη. Παρακαλώ συνδεθείτε ή χρησιμοποιήστε διαφορετικό email.")
            return False 
        
        # 3. ΚΡΥΠΤΟΓΡΑΦΗΣΗ (HASHING)
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 4. ΔΗΜΙΟΥΡΓΙΑ ΕΓΓΡΑΦΗΣ
        new_user_data = {
            "created_at": str(datetime.now()), 
            "email": email,
            "name": name,
            "password_hash": hashed,
            "role": "pending" 
        }
        
        # 5. ΑΠΟΘΗΚΕΥΣΗ ΣΕ GSheets (primary source for admin approval)
        gsheets_success = DatabaseConnector.append_data("Users", list(new_user_data.values()), use_local_db=False)
        if not gsheets_success:
            logger.error(f"Failed to register user '{email}' in Google Sheets.")
            st.error("Αποτυχία εγγραφής χρήστη στα Google Sheets.")
            return False

        # 6. ΑΠΟΘΗΚΕΥΣΗ ΣΕ SQLite (για τοπική χρήση / μελλοντικές native apps)
        # Εδώ, το SQLite μπορεί να μην έχει όλες τις στήλες. Πρέπει να είμαστε σίγουροι ότι υπάρχουν.
        # Θα ανακτήσουμε τα ονόματα στηλών από την SQLite για να αποφύγουμε σφάλματα.
        local_users_df = DatabaseConnector.fetch_data("Users", use_local_db=True)
        if not local_users_df.empty: # Αν υπάρχει ήδη πίνακας Users
            sqlite_columns = local_users_df.columns.tolist()
            # Δημιουργία λίστας δεδομένων με τη σωστή σειρά για την SQLite
            sqlite_row_data = [new_user_data.get(col) for col in sqlite_columns]
            sqlite_success = DatabaseConnector.append_data("Users", sqlite_row_data, use_local_db=True)
            if not sqlite_success:
                logger.warning(f"Failed to register user '{email}' in local SQLite DB.")
        else:
            logger.warning("SQLite Users table not yet initialized or empty. Skipping local registration for now.")

        logger.info(f"User '{email}' registered successfully.")
        return True

    @staticmethod
    def log_interaction(user_email: str, action: str, description: str):
        """
        Καταγράφει μια αλληλεπίδραση χρήστη στο φύλλο "Logs" (και τοπικά).
        """
        try:
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_email": user_email,
                "action": action,
                "description": description
            }
            # Αποθήκευση σε GSheets
            gsheets_success = DatabaseConnector.append_data("Logs", list(log_entry.values()), use_local_db=False)
            if not gsheets_success:
                logger.warning(f"Failed to log interaction for '{user_email}' in Google Sheets.")

            # Αποθήκευση σε SQLite
            # Πρέπει να είμαστε σίγουροι ότι ο πίνακας Logs στην SQLite έχει τις ίδιες στήλες
            local_logs_df = DatabaseConnector.fetch_data("Logs", use_local_db=True)
            if not local_logs_df.empty:
                sqlite_columns = local_logs_df.columns.tolist()
                sqlite_row_data = [log_entry.get(col) for col in sqlite_columns]
                sqlite_success = DatabaseConnector.append_data("Logs", sqlite_row_data, use_local_db=True)
                if not sqlite_success:
                    logger.warning(f"Failed to log interaction for '{user_email}' in local SQLite DB.")
            else:
                logger.warning("SQLite Logs table not yet initialized or empty. Skipping local log for now.")

        except Exception as e:
            logger.error(f"Error logging interaction for '{user_email}': {e}", exc_info=True)
            # st.error(f"Error logging interaction: {e}") # Δεν θέλουμε να εμφανίζεται στον χρήστη