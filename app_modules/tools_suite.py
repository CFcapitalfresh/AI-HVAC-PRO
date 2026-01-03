"""
MODULE: Tools Suite & Clients
VERSION: 1.5.0 (TITANIUM)
DESCRIPTION: Περιέχει τα υπολογιστικά εργαλεία και την προβολή πελατολογίου.
             **Αυτό το module φαίνεται να είναι πλέον ΑΝΕΝΕΡΓΟ/REDUNDANT, καθώς το `main.py`
             χρησιμοποιεί `modules/ui_tools.py` και `modules/ui_clients.py` ξεχωριστά
             για τις αντίστοιχες λειτουργίες.**
             Εάν υπάρχουν μοναδικές λειτουργίες εδώ, θα πρέπει να μεταφερθούν στα `modules/ui_tools.py`
             και `modules/ui_clients.py` ή να διαγραφεί για καθαρότερη αρχιτεκτονική.
"""

import streamlit as st
import pandas as pd
from typing import Any
from core.language_pack import get_text # Rule 5
import logging # Rule 4

logger = logging.getLogger("Module_Tools_Suite")

def render_tools_page() -> None:
    """Εμφανίζει τα εργαλεία υπολογισμού."""
    lang = st.session_state.get('lang', 'gr') # Rule 6, 5
    st.title(get_text('menu_tools', lang)) # Rule 5
    
    t1, t2 = st.tabs([get_text('tool_btu_tab', lang), get_text('tool_conv_tab', lang)]) # Rule 5
    
    with t1:
        st.subheader(get_text('tool_btu_tab', lang)) # Rule 5
        
        c1, c2 = st.columns(2)
        with c1:
            area = st.number_input(get_text('tool_area', lang), min_value=1.0, value=20.0, step=1.0, key="ts_btu_area") # Rule 5, 6
            height = st.number_input(get_text('tool_height', lang), min_value=2.0, value=3.0, step=0.1, key="ts_btu_height") # Rule 5, 6
        with c2:
            ins_opts = [get_text('ins_good', lang), get_text('ins_avg', lang), get_text('ins_bad', lang)] # Rule 5
            sun_opts = [get_text('sun_low', lang), get_text('sun_med', lang), get_text('sun_high', lang)] # Rule 5
            
            insulation = st.selectbox(get_text('tool_insulation', lang), ins_opts, key="ts_btu_insulation") # Rule 5, 6
            sun = st.selectbox(get_text('tool_sun', lang), sun_opts, key="ts_btu_sun") # Rule 5, 6
            
        # Logic
        factor = 500 # Base
        # Using index for language independence
        ins_idx = ins_opts.index(insulation)
        sun_idx = sun_opts.index(sun)

        if ins_idx == 0: factor -= 50 # Good insulation
        if ins_idx == 2: factor += 100 # Bad insulation
        if sun_idx == 2: factor += 80 # High sun exposure
        
        # Volume Correction
        vol_correction = 1.0
        if height > 3.0: vol_correction = height / 3.0
        
        result = area * factor * vol_correction
        
        st.divider()
        st.success(f"📌 {get_text('tool_calc_res', lang)}: **{int(result):,} BTU/h**") # Rule 5
        st.info(get_text('tool_note_empirical', lang) if 'tool_note_empirical' in LANGUAGE_PACK else "ℹ️ *Ο υπολογισμός είναι εμπειρικός.*") # Rule 5

    with t2:
        st.write(get_text('tool_converter_soon', lang) if 'tool_converter_soon' in LANGUAGE_PACK else "🔧 Converter coming soon...") # Rule 5

def render_clients_viewer(data_manager: Any) -> None:
    """
    Εμφανίζει το πελατολόγιο από τα Google Sheets.
    Args:
        data_manager: Μια κλάση/μέθοδος από το main.py που φέρνει δεδομένα.
    """
    lang = st.session_state.get('lang', 'gr') # Rule 6, 5
    st.title(get_text('menu_clients', lang)) # Rule 5
    
    # Φόρτωση δεδομένων
    with st.spinner(get_text('clients_loading_spinner', lang) if 'clients_loading_spinner' in LANGUAGE_PACK else "Φόρτωση Πελατών..."): # Rule 5
        # Υποθέτουμε ότι το DataManager έχει μέθοδο fetch_sheet_data
        try: # Rule 4
            df = data_manager.fetch_sheet_data("Clients")
        except Exception as e:
            st.error(f"{get_text('clients_error_fetching', lang).format(error=e)}" if 'clients_error_fetching' in LANGUAGE_PACK else f"Error fetching clients: {e}")
            logger.error(f"Error fetching clients in tools_suite: {e}", exc_info=True) # Rule 4
            return

    if df.empty:
        st.warning(get_text('clients_no_found', lang) if 'clients_no_found' in LANGUAGE_PACK else "Η λίστα πελατών είναι κενή.") # Rule 5
        return

    # Αναζήτηση
    search = st.text_input(get_text('clients_search_input', lang), placeholder="Όνομα, Τηλέφωνο ή Διεύθυνση...", key="ts_client_search") # Rule 5, 6
    
    if search:
        mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
        df = df[mask]
        st.success(f"{get_text('clients_found_records', lang).format(count=len(df))}" if 'clients_found_records' in LANGUAGE_PACK else f"Βρέθηκαν {len(df)} εγγραφές.") # Rule 5
        
    st.dataframe(df, use_container_width=True, hide_index=True)