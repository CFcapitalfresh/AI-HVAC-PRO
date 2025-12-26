import streamlit as st
from core.language_pack import get_text
from core.ai_engine import AIEngine
import core.auth_manager # Για logging αν χρειαστεί

def render(user):
    st.header(get_text('menu_chat', st.session_state.lang))
    
    # Init AI
    brain = AIEngine()

    # History
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    prompt = st.chat_input("...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner(get_text('loading', st.session_state.lang)):
                response = brain.analyze_content(prompt)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})