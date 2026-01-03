import streamlit as st
from core.language_pack import get_text

def render(user):
    lang = st.session_state.get('lang', 'gr') # Rule 6
    st.header(get_text('help_title', lang))
    
    st.info(get_text('help_info_card', lang)) # Rule 5
    
    with st.expander(get_text('help_chat_expander', lang)): # Rule 5
        st.write(get_text('help_chat_1', lang)) # Rule 5
        st.write(get_text('help_chat_2', lang)) # Rule 5
        st.write(get_text('help_chat_3', lang)) # Rule 5
        
    with st.expander(get_text('help_search_expander', lang)): # Rule 5
        st.write(get_text('help_search_1', lang)) # Rule 5
        st.write(get_text('help_search_2', lang)) # Rule 5
        st.write(get_text('help_search_3', lang)) # Rule 5
        
    with st.expander(get_text('help_organizer_expander', lang)): # Rule 5
        st.write(get_text('help_organizer_1', lang)) # Rule 5
        st.write(get_text('help_organizer_2', lang)) # Rule 5
        st.write(get_text('help_organizer_3', lang)) # Rule 5