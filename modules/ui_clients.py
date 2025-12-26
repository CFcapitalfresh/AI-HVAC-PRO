import streamlit as st
from core.db_connector import DatabaseConnector
from core.language_pack import get_text

def render(user):
    st.header(get_text('menu_clients', st.session_state.lang))
    
    # Fetch Data
    df = DatabaseConnector.fetch_data("Clients")
    
    if df.empty:
        st.info("No clients found.")
    else:
        search = st.text_input("Search Client...")
        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        st.dataframe(df, use_container_width=True)