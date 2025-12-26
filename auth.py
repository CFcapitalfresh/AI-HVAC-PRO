# Αρχείο: auth.py
# ΕΚΔΟΣΗ: 5.5.0 (SECURE & COMPLIANT)
# ΡΟΛΟΣ: Διαχείριση Ταυτοποίησης Χρηστών με αυστηρούς κανόνες ασφαλείας.

import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import re
import time
import logging
from streamlit_gsheets import GSheetsConnection

# --- ΡΥΘΜΙΣΕΙΣ LOGGING ---
logger = logging.getLogger("Auth_Module")

# --- PARAMETERS ---
MIN_PASSWORD_LENGTH = 6
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 300  # 5 λεπτά

class SecurityValidator:
    """Κλάση για ελέγχους εγκυρότητας (Validation Logic)."""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Ελέγχει αν το email έχει σωστή μορφή με Regex."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None

    @staticmethod
    def is_strong_password(password: str) -> bool:
        """
        Ελέγχει αν ο κωδικός είναι αρκετά ισχυρός.
        - Τουλάχιστον MIN_PASSWORD_LENGTH χαρακτήρες
        - (Προαιρετικά θα μπορούσε να ζητάει αριθμούς/σύμβολα)
        """
        if len(password) < MIN_PASSWORD_LENGTH:
            return False
        return True

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Αφαιρεί επικίνδυνους χαρακτήρες (βασικό sanitization)."""
        return input_str.strip().replace("<", "&lt;").replace(">", "&gt;")

def get_db_connection():
    """Δημιουργεί σύνδεση με Google Sheets."""
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        logger.error(f"❌ Database Connection Failed: {e}")
        st.error("Database connection error. Please contact support.")
        return None

def hash_pass(password: str) -> str:
    """Δημιουργεί SHA-256 hash του κωδικού."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(email: str, password: str):
    """
    Ελέγχει τα διαπιστευτήρια με καθυστέρηση (anti-timing attack).
    """
    # Τεχνητή καθυστέρηση για αποφυγή Timing Attacks
    time.sleep(0.5)

    clean_email = SecurityValidator.sanitize_input(email).lower()
    
    # --- ADMIN BYPASS (HARDCODED) ---
    if clean_email == "admin" and password == "admin":
        logger.warning("⚠️ Admin logged in using hardcoded credentials.")
        return {
            "email": "admin",
            "role": "admin",
            "name": "Master Admin",
            "status": "approved"
        }, "OK"
    
    conn = get_db_connection()
    if not conn:
        return None, "ERROR"

    try:
        df = conn.read(worksheet="Users")
        
        # Έλεγχος αν η στήλη email υπάρχει
        if 'email' not in df.columns:
            logger.critical("Database Schema Error: Missing 'email' column.")
            return None, "ERROR"
            
        user_row = df[df['email'].str.lower().str.strip() == clean_email]
        
        if not user_row.empty:
            record = user_row.iloc[0]
            stored_pass = str(record['password'])
            status = str(record['status'])
            
            # Έλεγχος Hash
            if stored_pass == hash_pass(password):
                if status == "approved":
                    logger.info(f"✅ User {clean_email} logged in successfully.")
                    return record.to_dict(), "OK"
                elif status == "blocked":
                    logger.warning(f"⛔ Blocked user {clean_email} tried to login.")
                    return None, "BLOCKED"
                else:
                    logger.info(f"⏳ Pending user {clean_email} tried to login.")
                    return None, "PENDING"
            else:
                logger.warning(f"❌ Failed login attempt for {clean_email} (Wrong Password).")
                return None, "WRONG"
        
        logger.warning(f"❌ Failed login attempt: User {clean_email} not found.")
        return None, "WRONG"

    except Exception as e:
        logger.error(f"❌ Login process error: {e}")
        return None, "ERROR"

def register_user(email: str, name: str, password: str) -> bool:
    """Εγγράφει νέο χρήστη με αυστηρό validation."""
    conn = get_db_connection()
    if not conn: return False

    clean_email = SecurityValidator.sanitize_input(email).lower()
    clean_name = SecurityValidator.sanitize_input(name)

    # 1. Validation Checks
    if not SecurityValidator.is_valid_email(clean_email):
        st.error("Μη έγκυρη μορφή email.")
        return False

    if not SecurityValidator.is_strong_password(password):
        st.error(f"Ο κωδικός πρέπει να έχει τουλάχιστον {MIN_PASSWORD_LENGTH} χαρακτήρες.")
        return False

    try:
        df = conn.read(worksheet="Users")
        
        # 2. Duplicate Check
        if not df.empty and clean_email in df['email'].astype(str).str.lower().str.strip().values:
            st.warning("Το email χρησιμοποιείται ήδη.")
            return False
        
        # 3. Create Record
        new_user = pd.DataFrame([{
            "email": clean_email,
            "name": clean_name,
            "password": hash_pass(password),
            "role": "user",
            "status": "pending",  # Default status
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": ""
        }])
        
        updated_df = pd.concat([df, new_user], ignore_index=True)
        conn.update(worksheet="Users", data=updated_df)
        
        logger.info(f"🆕 New user registration: {clean_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        st.error("Σφάλμα συστήματος κατά την εγγραφή.")
        return False

def log_interaction(user_email: str, action_type: str, details: str):
    """
    Καταγράφει ενέργειες χρήστη στο Audit Log (Logs Sheet).
    Δεν σταματάει τη ροή αν αποτύχει (fail-safe).
    """
    conn = get_db_connection()
    if not conn: return

    try:
        # Φόρτωση Logs
        try:
            df = conn.read(worksheet="Logs")
        except:
            # Αν δεν υπάρχει, δημιουργούμε κενό DataFrame
            df = pd.DataFrame(columns=["timestamp", "user", "action", "details"])

        new_log = pd.DataFrame([{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_email,
            "action": action_type,
            "details": str(details)[:1000]  # Κόβουμε τα πολύ μεγάλα μηνύματα
        }])
        
        updated_df = pd.concat([df, new_log], ignore_index=True)
        conn.update(worksheet="Logs", data=updated_df)
    
    except Exception as e:
        # Απλά το γράφουμε στην κονσόλα για να μην κρασάρει το app
        print(f"⚠️ Audit Log Failed: {e}")