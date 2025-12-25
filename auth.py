import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from streamlit_gsheets import GSheetsConnection

# Σύνδεση με το Google Sheets
def get_db_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(email, password):
    # Ο Admin παραμένει "καρφωτός" για ασφάλεια
    if email == "admin" and password == "admin":
        return {"email": "admin", "role": "admin", "name": "Master Admin", "status": "approved"}, "OK"
    
    conn = get_db_connection()
    try:
        # Διαβάζουμε την καρτέλα Users
        df = conn.read(worksheet="Users")
        email = email.lower().strip()
        
        user_row = df[df['email'] == email]
        
        if not user_row.empty:
            stored_pass = user_row.iloc[0]['password']
            status = user_row.iloc[0]['status']
            
            if stored_pass == hash_pass(password):
                if status == "approved":
                    return user_row.iloc[0].to_dict(), "OK"
                elif status == "blocked":
                    return None, "BLOCKED"
                else:
                    return None, "PENDING"
        return None, "WRONG"
    except:
        return None, "ERROR"

def register_user(email, name, password):
    conn = get_db_connection()
    df = conn.read(worksheet="Users")
    email = email.lower().strip()
    
    if email in df['email'].values:
        return False
    
    new_user = pd.DataFrame([{
        "email": email,
        "name": name,
        "password": hash_pass(password),
        "role": "user",
        "status": "pending",
        "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    
    updated_df = pd.concat([df, new_user], ignore_index=True)
    conn.update(worksheet="Users", data=updated_df)
    return True

def log_interaction(user_email, question, answer):
    conn = get_db_connection()
    try:
        df = conn.read(worksheet="Logs")
        new_log = pd.DataFrame([{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_email,
            "question": question,
            "answer": answer[:500] # Κρατάμε τα πρώτα 500 γράμματα
        }])
        updated_df = pd.concat([df, new_log], ignore_index=True)
        conn.update(worksheet="Logs", data=updated_df)
    except:
        pass