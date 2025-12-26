import streamlit as st
from core.db_connector import DatabaseConnector

def render(user):
    st.header("⚙️ Admin Panel")
    
    t1, t2 = st.tabs(["Users", "Logs"])
    
    with t1:
        st.subheader("User Management")
        df = DatabaseConnector.fetch_data("Users")
        st.dataframe(df)
        
    with t2:
        st.subheader("System Logs")
        df = DatabaseConnector.fetch_data("Logs")
        st.dataframe(df)