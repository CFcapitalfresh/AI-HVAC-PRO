import streamlit as st
from core.language_pack import get_text
from core.ai_engine import AIEngine

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
    prompt = st.chat_input("Γράψε τη βλάβη ή το μοντέλο...")
    
    if prompt:
        # User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # AI Response
        with st.chat_message("assistant"):
            with st.spinner(get_text('loading', st.session_state.lang)):
                # ΠΡΟΣΟΧΗ: Εδώ στέλνουμε πλέον και το context (αν έχουμε manual) και τη ΓΛΩΣΣΑ
                # Προς το παρόν context στέλνουμε κενό, μέχρι να συνδέσουμε την αναζήτηση
                # Αλλά στέλνουμε τη Γλώσσα!
                response = brain.analyze_content(
                    prompt, 
                    context_text="", 
                    lang=st.session_state.lang
                )
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})