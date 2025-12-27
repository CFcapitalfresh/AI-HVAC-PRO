import streamlit as st
import bcrypt
from core.db_connector import DatabaseConnector
from datetime import datetime

class AuthManager:
    @staticmethod
    def verify_login(email, password):
        # 1. ΚΑΘΑΡΙΣΜΟΣ INPUT (Αυτό λύνει το πρόβλημα του κινητού)
        # Σβήνει κενά (space) από την αρχή και το τέλος
        # Μετατρέπει τα κεφαλαία σε μικρά για το email
        email = email.strip().lower()  
        password = password.strip()

        users = DatabaseConnector.fetch_data("Users")
        if users.empty: return None, "No users found"

        # Αναζήτηση χρήστη
        user = users[users['email'] == email]
        
        if user.empty: return None, "User not found"
        
        user_data = user.iloc[0]
        stored_hash = user_data['password_hash']
        
        # Έλεγχος Κωδικού
        try:
            # Περίπτωση 1: Παλιός κωδικός (απλό κείμενο)
            if not stored_hash.startswith('$2b$'):
                if stored_hash == password:
                    return user_data.to_dict(), "OK"
                else:
                    return None, "Wrong password"
            
            # Περίπτωση 2: Νέος ασφαλής κωδικός (Hash)
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                # Έλεγχος αν ο χρήστης είναι ενεργός
                if user_data['role'] == 'active' or user_data['role'] == 'admin':
                    return user_data.to_dict(), "OK"
                else:
                    return None, "Account Pending Approval" # Περιμένει έγκριση
            else:
                return None, "Wrong password"
        except:
            return None, "Auth Error"

    @staticmethod
    def register_new_user(email, name, password):
        # 1. ΚΑΘΑΡΙΣΜΟΣ INPUT
        email = email.strip().lower()
        name = name.strip()
        password = password.strip()

        # Έλεγχος αν υπάρχει ήδη το email
        users = DatabaseConnector.fetch_data("Users")
        if not users.empty and email in users['email'].values:
            return False
        
        # Κρυπτογράφηση κωδικού (Hash)
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Δημιουργία εγγραφής
        new_user = [
            str(datetime.now()), # Ημερομηνία
            email,
            name,
            hashed,
            "pending" # Role (Μπαίνει ως 'pending' και θέλει έγκριση από Admin)
        ]
        
        return DatabaseConnector.append_data("Users", new_user)