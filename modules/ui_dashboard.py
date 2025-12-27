import streamlit as st
from core.language_pack import get_text

def render(user):
    lang = st.session_state.get('lang', 'gr')
    
    # Τίτλος & Υπότιτλος (Μεταφρασμένα)
    st.title(f"{get_text('dash_welcome', lang)}, {user['name']}")
    st.markdown(f"### {get_text('dash_subtitle', lang)}")
    st.divider()

    # --- Γρήγορες Ενέργειες ---
    st.subheader(get_text('dash_quick', lang))
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"🤖 **{get_text('dash_chat_card', lang)}**")
        st.write(get_text('dash_chat_desc', lang))
        # Χρησιμοποιούμε κενό κουμπί που απλά ενημερώνει (για UX)
        if st.button(get_text('dash_btn_chat', lang), use_container_width=True):
             st.info("Select 'AI Chat' from the left menu.")

    with col2:
        st.warning(f"📚 **{get_text('dash_lib_card', lang)}**")
        st.write(get_text('dash_lib_desc', lang))
        if st.button(get_text('dash_btn_lib', lang), use_container_width=True):
             st.info("Select 'Manuals Library' from the left menu.")

    with col3:
        st.success(f"🧮 **{get_text('dash_tool_card', lang)}**")
        st.write(get_text('dash_tool_desc', lang))
        if st.button(get_text('dash_btn_tool', lang), use_container_width=True):
             st.info("Select 'Tools' from the left menu.")

    st.divider()
    st.caption(get_text('dash_status', lang))