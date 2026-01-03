import streamlit as st
from core.language_pack import get_text

def render(user):
    lang = st.session_state.get('lang', 'gr')
    st.header(get_text('menu_tools', lang))
    
    st.markdown("""<style>div.stButton > button:first-child {height: 3em; font-size: 18px; font-weight: bold;}</style>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([get_text('tool_btu_tab', lang), get_text('tool_conv_tab', lang), get_text('tool_pipe_tab', lang)])
    
    # --- BTU CALC ---
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            area = st.number_input(get_text('tool_area', lang), min_value=5, value=25)
            height = st.number_input(get_text('tool_height', lang), min_value=2.0, value=2.8, step=0.1)
        
        with c2:
            # Δημιουργούμε λίστες επιλογών που αντιστοιχούν στις μεταφράσεις
            ins_opts = [get_text('ins_good', lang), get_text('ins_avg', lang), get_text('ins_bad', lang)]
            sun_opts = [get_text('sun_low', lang), get_text('sun_med', lang), get_text('sun_high', lang)]
            
            insulation = st.selectbox(get_text('tool_insulation', lang), ins_opts)
            sun = st.selectbox(get_text('tool_sun', lang), sun_opts)
            
        # Logic (Βασίζεται στο index για να δουλεύει ανεξαρτήτως γλώσσας)
        # Index 0: Good/Low, 1: Avg/Med, 2: Bad/High
        ins_idx = ins_opts.index(insulation)
        sun_idx = sun_opts.index(sun)

        base_factor = 400
        if ins_idx == 0: base_factor = 350
        elif ins_idx == 1: base_factor = 450
        elif ins_idx == 2: base_factor = 600
        
        if sun_idx == 2: base_factor += 100
        elif sun_idx == 0: base_factor -= 50
        
        final_factor = base_factor * (height / 3.0) if height > 3.0 else base_factor
        btu_result = int(area * final_factor)
        kw_result = round(btu_result / 3412, 2)
        
        st.divider()
        st.success(f"📊 {get_text('tool_calc_res', lang)}: **{btu_result:,} BTU/h** ({kw_result} kW)")
        
        rec = "9000" if btu_result < 9000 else "12000" if btu_result < 13000 else "18000" if btu_result < 19000 else "24000"
        st.info(f"💡 {get_text('tool_rec', lang)}: **{rec} BTU**")

    # --- CONVERTER ---
    with tab2:
        val = st.number_input("Value", value=1.0)
        c_type = st.radio("Type", ["Bar -> PSI", "C -> F", "kW -> BTU"])
        if c_type == "Bar -> PSI": st.write(f"➡️ **{round(val * 14.5038, 2)} PSI**")
        elif c_type == "C -> F": st.write(f"➡️ **{round((val * 9/5) + 32, 1)} °F**")
        elif c_type == "kW -> BTU": st.write(f"➡️ **{int(val * 3412)} BTU/h**")

    # --- PIPING ---
    with tab3:
        st.subheader("R32/R410a Guide")
        data = {
            "BTU": ["9.000", "12.000", "18.000", "24.000"],
            get_text('pipe_liquid', lang): ["1/4''", "1/4''", "1/4''", "3/8''"],
            get_text('pipe_gas', lang): ["3/8''", "1/2''", "1/2''", "5/8''"]
        }
        st.table(data)