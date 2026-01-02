"""
MODULE: UI LICENSING
--------------------
Description: Streamlit UI for license management.
Provides user-facing license status and activation, and admin-facing tools
for managing user roles and license expirations.
"""

import streamlit as st
import logging
from core.licensing_manager import LicensingManager
from core.db_connector import DatabaseConnector
from core.language_pack import get_text
import pandas as pd
from datetime import datetime, date

logger = logging.getLogger("Module_Licensing_UI")

def render(user):
    lang = st.session_state.get('lang', 'gr')

    st.header(get_text('lic_page_title', lang))
    st.divider()

    # --- USER SECTION ---
    st.subheader(get_text('lic_user_section_title', lang))
    
    current_license_status = LicensingManager.get_license_status(user['email'], user['role'])
    
    # Display current status
    status_text = ""
    status_color = "gray"
    if current_license_status['status'] == "valid":
        status_text = get_text('lic_status_valid', lang)
        status_color = "green"
    elif current_license_status['status'] == "expired":
        status_text = get_text('lic_status_expired', lang)
        status_color = "red"
    elif current_license_status['status'] == "invalid":
        status_text = get_text('lic_status_invalid', lang)
        status_color = "red"
    elif current_license_status['status'] == "pending":
        status_text = get_text('lic_status_pending', lang)
        status_color = "orange"
    else:
        status_text = get_text('lic_status_not_found', lang)
        status_color = "gray"

    st.markdown(f"**{get_text('lic_status_label', lang)}** :{status_color}[{status_text}]")
    st.info(current_license_status['message']) # Display detailed message

    # License activation form
    with st.form("activate_license_form"):
        license_key = st.text_input(get_text('lic_enter_key', lang), placeholder=get_text('lic_key_ph', lang))
        submitted = st.form_submit_button(get_text('lic_btn_activate', lang), use_container_width=True)

        if submitted:
            try:
                # Rule 4: Error Handling
                activation_result = LicensingManager.activate_license(user['email'], license_key)
                if activation_result["success"]:
                    st.success(get_text('lic_activation_success', lang))
                    logger.info(f"User {user['email']} successfully activated license (simulated).")
                    st.rerun() # Refresh to show new status
                else:
                    st.error(f"{get_text('lic_activation_fail', lang)}: {activation_result['message']}")
                    logger.warning(f"User {user['email']} failed to activate license with key: {license_key[:5]}... - {activation_result['message']}")
            except Exception as e:
                logger.error(f"Error activating license for {user['email']}: {e}", exc_info=True)
                st.error(f"{get_text('general_ui_error', lang).format(error=e)}")

    st.divider()

    # --- ADMIN SECTION ---
    if user['role'] == 'admin':
        st.subheader(get_text('lic_admin_section_title', lang))

        try:
            # Rule 6: Streamlit State (ensure df_users is loaded once or cached)
            if 'admin_users_data' not in st.session_state:
                st.session_state.admin_users_data = DatabaseConnector.fetch_data("Users")
            
            df_users = st.session_state.admin_users_data
            
            if df_users.empty:
                st.info(get_text('lic_admin_no_licenses', lang))
            else:
                st.caption(get_text('lic_admin_all_licenses', lang))
                
                # Search/Filter users
                search_query = st.text_input(get_text('lic_admin_filter_users', lang), key="admin_user_filter")
                filtered_df = df_users.copy()
                if search_query:
                    filtered_df = filtered_df[
                        filtered_df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                    ]

                for index, row in filtered_df.iterrows():
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        # Display User Info
                        col1.markdown(f"**{get_text('lic_admin_user_email', lang)}:** {row['email']}")
                        col1.markdown(f"**{get_text('lic_admin_current_role', lang)}:** {row['role'].upper()}")

                        # Role selection
                        available_roles = ['pending', 'active', 'admin', 'inactive']
                        current_role_idx = available_roles.index(row['role']) if row['role'] in available_roles else 0
                        new_role = col2.selectbox(
                            get_text('lic_admin_new_role', lang),
                            options=[get_text(f'lic_admin_role_{role}', lang) for role in available_roles],
                            index=current_role_idx,
                            key=f"role_sel_{row['email']}"
                        )
                        # Map back to English role for DB
                        new_role_en = available_roles[[get_text(f'lic_admin_role_{role}', lang) for role in available_roles].index(new_role)]

                        # Expiry Date (Placeholder for future implementation)
                        # col3.caption(get_text('lic_admin_set_expiry', lang))
                        # current_expiry = datetime.strptime(row['expiry_date'], '%Y-%m-%d').date() if 'expiry_date' in row and pd.notna(row['expiry_date']) else date.today()
                        # new_expiry = col3.date_input(
                        #     get_text('lic_admin_new_license_expiry', lang),
                        #     value=current_expiry,
                        #     key=f"expiry_date_{row['email']}"
                        # )

                        # Action Buttons
                        c_btn1, c_btn2 = st.columns(2)
                        
                        if c_btn1.button(get_text('lic_admin_btn_update_role', lang), key=f"update_lic_{row['email']}", use_container_width=True):
                            try:
                                # Update the role in the DataFrame
                                st.session_state.admin_users_data.loc[index, 'role'] = new_role_en
                                # st.session_state.admin_users_data.loc[index, 'expiry_date'] = new_expiry.strftime('%Y-%m-%d') # Future
                                
                                # Update the database
                                if DatabaseConnector.update_all_data("Users", st.session_state.admin_users_data):
                                    st.success(get_text('lic_admin_role_updated', lang))
                                    logger.info(f"Admin {user['email']} updated role for {row['email']} to {new_role_en}.")
                                    st.rerun()
                                else:
                                    st.error(get_text('lic_admin_error_update', lang))
                                    logger.error(f"Admin {user['email']} failed to update role for {row['email']}.")
                            except Exception as e:
                                logger.error(f"Error updating user role for {row['email']}: {e}", exc_info=True)
                                st.error(f"{get_text('general_ui_error', lang).format(error=e)}")

                        if c_btn2.button(get_text('lic_admin_btn_revoke', lang), key=f"revoke_lic_{row['email']}", type="secondary", use_container_width=True):
                            try:
                                # Set role to 'pending' or 'inactive'
                                st.session_state.admin_users_data.loc[index, 'role'] = 'pending' # Or 'inactive'
                                
                                if DatabaseConnector.update_all_data("Users", st.session_state.admin_users_data):
                                    st.warning(get_text('lic_admin_activation_updated', lang))
                                    logger.info(f"Admin {user['email']} deactivated license for {row['email']}.")
                                    st.rerun()
                                else:
                                    st.error(get_text('lic_admin_error_update', lang))
                                    logger.error(f"Admin {user['email']} failed to deactivate license for {row['email']}.")
                            except Exception as e:
                                logger.error(f"Error deactivating license for {row['email']}: {e}", exc_info=True)
                                st.error(f"{get_text('general_ui_error', lang).format(error=e)}")

        except Exception as e:
            logger.error(f"Licensing UI: General rendering error in admin section for user {user['email']}: {e}", exc_info=True)
            st.error(f"{get_text('general_ui_error', lang).format(error=e)}")