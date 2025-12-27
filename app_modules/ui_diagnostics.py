"""
MODULE: UI DIAGNOSTICS (WIZARD)
-------------------------------
Description: Interactive, step-by-step troubleshooting wizard.
"""

import streamlit as st
from services.diagnostics_logic import DiagnosticsService
import time

def render(user):
    st.header("🔧 Active Diagnostics / Διαδραστικός Οδηγός")
    st.caption("Step-by-Step AI Troubleshooting Wizard")
    
    if 'diag_step' not in st.session_state: st.session_state.diag_step = 0
    if 'diag_plan' not in st.session_state: st.session_state.diag_plan = None
    
    # 1. Input Section
    if not st.session_state.diag_plan:
        with st.container(border=True):
            st.subheader("🚀 Start New Diagnosis")
            error_input = st.text_input("Περιγράψτε το πρόβλημα (π.χ. Error 104)", placeholder="Error code...")
            
            # Προσπάθεια ανάκτησης Context από το Chat (αν υπάρχει)
            manual_context = ""
            if 'active_manuals' in st.session_state and st.session_state.active_manuals:
                st.info(f"📚 Context: {st.session_state.active_manuals[0]['name']}")
                manual_context = str(st.session_state.active_manuals[0])

            if st.button("🛠️ Δημιουργία Σχεδίου", type="primary", use_container_width=True):
                if error_input:
                    with st.spinner("🤖 Σχεδιασμός βημάτων ελέγχου..."):
                        service = DiagnosticsService()
                        plan = service.generate_checklist(error_input, manual_context)
                        
                        if plan:
                            st.session_state.diag_plan = plan
                            st.session_state.diag_step = 0
                            st.rerun()
                        else:
                            st.error("Απέτυχε η δημιουργία πλάνου.")
    
    # 2. Active Wizard
    else:
        plan = st.session_state.diag_plan
        steps = plan.get('steps', [])
        current_idx = st.session_state.diag_step
        
        st.subheader(f"🛡️ {plan.get('title', 'Troubleshooting')}")
        progress = (current_idx / len(steps))
        st.progress(progress, text=f"Βήμα {current_idx + 1} από {len(steps)}")
        
        if current_idx >= len(steps):
            st.success("✅ Η διαδικασία ολοκληρώθηκε!")
            if st.button("🔙 Νέα Διάγνωση"):
                st.session_state.diag_plan = None
                st.session_state.diag_step = 0
                st.rerun()
            return

        step = steps[current_idx]
        
        with st.container(border=True):
            st.markdown(f"### 🔹 Βήμα {step['id']}")
            st.markdown(f"**Ενέργεια:** {step['action']}")
            if 'tip' in step:
                st.info(f"💡 Tip: {step['tip']}")
            
            st.divider()
            st.markdown(f"❓ **Ερώτηση:** {step['question']}")
            
            c1, c2 = st.columns(2)
            
            if c1.button("✅ ΝΑΙ / Λύθηκε", use_container_width=True):
                st.balloons()
                st.success("Το πρόβλημα επιλύθηκε!")
                time.sleep(2)
                st.session_state.diag_plan = None
                st.rerun()
                
            if c2.button("❌ ΟΧΙ / Συνέχεια", use_container_width=True):
                st.session_state.diag_step += 1
                st.rerun()
        
        if st.button("⚠️ Ακύρωση"):
            st.session_state.diag_plan = None
            st.rerun()