import streamlit as st
from core.language_pack import get_text

def render(user):
    st.header(get_text('menu_tools', st.session_state.lang))
    
    # CSS για να κάνουμε τα κουμπιά πιο φιλικά για δάχτυλα (Touch friendly)
    st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3em;
        font-size: 18px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    # Οι 3 Καρτέλες του Τεχνικού
    tab1, tab2, tab3 = st.tabs(["❄️ BTU Calc", "📏 Μετατροπέας", "🔥 Σωληνώσεις"])
    
    # --- 1. ΥΠΟΛΟΓΙΣΜΟΣ BTU ---
    with tab1:
        st.subheader("Υπολογισμός Ψυκτικών Φορτίων")
        st.caption("Γρήγορος υπολογισμός για επιλογή κλιματιστικού.")
        
        c1, c2 = st.columns(2)
        with c1:
            area = st.number_input("Τετραγωνικά Μέτρα (m²)", min_value=5, value=25, step=1)
            height = st.number_input("Ύψος Χώρου (m)", min_value=2.0, value=2.8, step=0.1)
        
        with c2:
            insulation = st.selectbox("Μόνωση", ["Καλή (Νέα Κουφώματα)", "Μέτρια (Διπλά Τζάμια 10ετίας)", "Κακή (Μονά Τζάμια/Αμόνωτο)"])
            sun = st.selectbox("Προσανατολισμός", ["Σκιερό / Βόρειο", "Μέτρια Ηλιοφάνεια", "Πολύ Ήλιος / Ρετιρέ"])
            
        # Λογική Υπολογισμού (Εμπειρικός Κανόνας Αγοράς)
        base_factor = 400 # Βάση
        
        if insulation == "Καλή (Νέα Κουφώματα)": base_factor = 350
        elif insulation == "Μέτρια (Διπλά Τζάμια 10ετίας)": base_factor = 450
        elif insulation == "Κακή (Μονά Τζάμια/Αμόνωτο)": base_factor = 600
        
        if sun == "Πολύ Ήλιος / Ρετιρέ": base_factor += 100
        elif sun == "Σκιερό / Βόρειο": base_factor -= 50
        
        # Διόρθωση για ύψος (αν είναι πάνω από 3μ)
        final_factor = base_factor
        if height > 3.0: final_factor *= (height / 3.0)
        
        btu_result = int(area * final_factor)
        kw_result = round(btu_result / 3412, 2)
        
        st.divider()
        col_res1, col_res2 = st.columns([2,1])
        with col_res1:
            st.success(f"📊 Απαιτούμενη Ισχύς: **{btu_result:,} BTU/h**")
            st.caption(f"Περίπου {kw_result} kW ψυκτικής ισχύος")
        
        with col_res2:
            # Πρόταση Μηχανήματος
            rec = ""
            if btu_result < 9000: rec = "9άρι (9.000)"
            elif btu_result < 13000: rec = "12άρι (12.000)"
            elif btu_result < 19000: rec = "18άρι (18.000)"
            elif btu_result < 25000: rec = "24άρι (24.000)"
            else: rec = "24άρι+ ή Multi"
            st.info(f"💡 Βάλε: **{rec}**")

    # --- 2. ΜΕΤΑΤΡΟΠΕΑΣ ---
    with tab2:
        st.subheader("Μετατροπέας Μονάδων")
        
        type_ = st.radio("Τι θέλεις να μετατρέψεις;", ["Πίεση (Bar/PSI)", "Θερμοκρασία (C/F)", "Ισχύς (kW/BTU)"], horizontal=True)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            val = st.number_input("Τιμή Εισόδου", value=1.0)
            
        with c2:
            if "Πίεση" in type_:
                st.write(f"➡️ **{round(val * 14.5038, 2)} PSI**")
                st.write(f"➡️ **{round(val * 100, 2)} kPa**")
            elif "Θερμοκρασία" in type_:
                f = (val * 9/5) + 32
                st.write(f"➡️ **{round(f, 1)} °F**")
            elif "Ισχύς" in type_:
                st.write(f"➡️ **{int(val * 3412)} BTU/h**")
                st.write(f"➡️ **{int(val * 860)} kcal/h**")

    # --- 3. ΣΩΛΗΝΩΣΕΙΣ (Σκονάκι) ---
    with tab3:
        st.subheader("Οδηγός Διαμέτρων (R32/R410a)")
        st.markdown("Ενδεικτικές διατομές χαλκού για Split Units:")
        
        data = {
            "Μηχάνημα": ["9.000 BTU", "12.000 BTU", "18.000 BTU", "24.000 BTU"],
            "Υγρού (Liquid)": ["1/4''", "1/4''", "1/4''", "3/8''"],
            "Αερίου (Gas)": ["3/8''", "1/2''", "1/2''", "5/8''"]
        }
        st.table(data)
        st.warning("⚠️ Πάντα να συμβουλεύεστε το manual του κατασκευαστή για μέγιστα μήκη.")