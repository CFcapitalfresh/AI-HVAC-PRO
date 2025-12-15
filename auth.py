# Αρχείο: auth.py
import json
import os
import hashlib
from datetime import datetime
import pandas as pd

USERS_FILE = "local_users_db.json"
LOGS_FILE = "chat_logs.json"

def load_data(filename):
    if not os.path.exists(filename): return {} if "users" in filename else []
    try:
        with open(filename, "r", encoding="utf-8") as f: return json.load(f)
    except: return {} if "users" in filename else []

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, default=str)

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(email, password):
    users = load_data(USERS_FILE)
    email = email.lower().strip()
    
    # Master Backdoor
    if email == "admin" and password == "admin":
        return {"email": "admin", "role": "admin", "name": "Master Admin", "status": "approved"}, "OK"
    
    if email in users:
        if users[email]["password"] == hash_pass(password):
            status = users[email].get("status", "pending")
            if status == "approved": return users[email], "OK"
            elif status == "blocked": return None, "BLOCKED"
            else: return None, "PENDING"
    return None, "WRONG"

def register_user(email, name, password):
    users = load_data(USERS_FILE)
    email = email.lower().strip()
    if email in users: return False
    
    users[email] = {
        "email": email,
        "name": name,
        "password": hash_pass(password),
        "role": "user",
        "status": "pending", # Default pending
        "joined": str(datetime.now())
    }
    save_data(USERS_FILE, users)
    return True

def log_interaction(user_email, question, answer, tech_type):
    logs = load_data(LOGS_FILE)
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_email,
        "type": tech_type,
        "question": question,
        "answer": answer[:200] + "..." 
    }
    logs.append(entry)
    save_data(LOGS_FILE, logs)