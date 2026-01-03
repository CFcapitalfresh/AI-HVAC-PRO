import streamlit as st
from core.db_connector import DatabaseConnector # Rule 3
from core.language_pack import get_text # Rule 5
import logging # Rule 4
import pandas as pd # To ensure pandas is explicitly imported if not already.

logger = logging.getLogger("Module_Clients_UI") # Rule 4

def render(user):
    lang = st.session_state.get('lang', 'gr') # Rule 6, 5
    st.header(get_text('menu_clients', lang)) # Rule 5
    
    # Fetch Data
    df = pd.DataFrame() # Initialize empty DataFrame for type consistency
    try: # Rule 4: Error Handling
        df = DatabaseConnector.fetch_data("Clients") # Rule 3
    except Exception as e:
        logger.error(f"Error fetching clients from database: {e}", exc_info=True) # Rule 4
        st.error(f"{get_text('clients_error_fetching', lang) if 'clients_error_fetching' in LANGUAGE_PACK else 'Error fetching clients'}: {e}") # Rule 5
        return # Exit if data cannot be fetched

    if df.empty:
        st.info(get_text('clients_no_found', lang)) # Rule 5
    else:
        # Rule 6: Initialize search input in session state if not present.
        if "clients_search_query" not in st.session_state:
            st.session_state.clients_search_query = ""

        search_query = st.text_input(get_text('clients_search_input', lang), key="clients_search_input_widget", value=st.session_state.clients_search_query) # Rule 5
        st.session_state.clients_search_query = search_query # Update session state

        if search_query:
            try: # Rule 4: Error Handling for dataframe operations
                mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                df = df[mask]
                st.success(f"{get_text('clients_found_records', lang) if 'clients_found_records' in LANGUAGE_PACK else 'Found {count} records.'}".format(count=len(df))) # Rule 5
            except Exception as e:
                logger.error(f"Error filtering client data: {e}", exc_info=True) # Rule 4
                st.error(f"{get_text('general_ui_error', lang).format(error='filtering clients')}: {e}") # Rule 5
        
        st.dataframe(df, use_container_width=True, hide_index=True)