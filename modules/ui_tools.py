import streamlit as st
from core.language_pack import get_text

def render(user):
    st.header(get_text('menu_tools', st.session_state.lang))
    
    # CSS για μεγάλα κουμπιά (Touch friendly)
    st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3em;
        font-size: 18px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    # Οι 3 Καρτέλες
    tab1, tab2, tab3 = st.tabs(["❄️ BTU Calc", "📏 Μετατροπέας", "🔥 Σωληνώσεις"])
    
    # --- 1. ΥΠΟΛΟΓΙΣΜΟΣ BTU ---
    with tab1:
        st.subheader("Υπολογισμός Ψυκτικών Φορτίων")
        
        c1, c2 = st.columns(2)
        with c1:
            area = st.number_input("Τετραγωνικά Μέτρα (m²)", min_value=5, value=25, step=1)
            height = st.number_input("Ύψος Χώρου (m)", min_value=2.0, value=2.8, step=0.1)
        
        with c2:
            insulation = st.selectbox("Μόνωση", ["Καλή (Νέα Κουφώματα)", "Μέτρια (Διπλά Τζάμια 10ετίας)", "Κακή (Μονά Τζάμια/Αμόνωτο)"])
            sun = st.selectbox("Προσανατολισμός", ["Σκιερό / Βόρειο", "Μέτρια Ηλιοφάνεια", "Πολύ Ήλιος / Ρετιρέ"])
            
        # Λογική Υπολογισμού
        base_factor = 400
        if insulation == "Καλή (Νέα Κουφώματα)": base_factor = 350
        elif insulation == "Μέτρια (Διπλά Τζάμια 10ετίας)": base_factor = 450
        elif insulation == "Κακή (Μονά Τζάμια/Αμόνωτο)": base_factor = 600
        
        if sun == "Πολύ Ήλιος / Ρετιρέ": base_factor += 100
        elif sun == "Σκιερό / Βόρειο": base_factor -= 50
        
        final_factor = base_factor
        if height > 3.0: final_factor *= (height / 3.0)
        
        btu_result = int(area * final_factor)
        kw_result = round(btu_result / 3412, 2)
        
        st.divider()
        st.success(f"📊 Απαιτούμενη Ισχύς: **{btu_result:,} BTU/h** ({kw_result} kW)")
        
        # Πρόταση
        rec = "9άρι" if btu_result < 9000 else "12άρι" if btu_result < 13000 else "18άρι" if btu_result < 19000 else "24άρι" if btu_result < 25000 else "24άρι+ / Multi"
        st.info(f"💡 Προτεινόμενο: **{rec}**")

    # --- 2. ΜΕΤΑΤΡΟΠΕΑΣ ---
    with tab2:
        st.subheader("Μετατροπέας Μονάδων")
        type_ = st.radio("Επιλογή", ["Πίεση (Bar/PSI)", "Θερμοκρασία (C/F)", "Ισχύς (kW/BTU)"], horizontal=True)
        val = st.number_input("Τιμή", value=1.0)
        
        if "Πίεση" in type_:
            st.write(f"➡️ **{round(val * 14.5038, 2)} PSI**")
        elif "Θερμοκρασία" in type_:
            st.write(f"➡️ **{round((val * 9/5) + 32, 1)} °F**")
        elif "Ισχύς" in type_:
            st.write(f"➡️ **{int(val * 3412)} BTU/h**")

    # --- 3. ΣΩΛΗΝΩΣΕΙΣ ---
    with tab3:
        st.subheader("Οδηγός Διαμέτρων (R32/R410a)")
        data = {
            "BTU": ["9.000", "12.000", "18.000", "24.000"],
            "Υγρού (Liquid)": ["1/4''", "1/4''", "1/4''", "3/8''"],
            "Αερίου (Gas)": ["3/8''", "1/2''", "1/2''", "5/8''"]
        }
        st.table(data)