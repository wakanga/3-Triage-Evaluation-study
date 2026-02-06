import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from src import utils, engine, components

# Set Page Config
st.set_page_config(page_title="Triage Study", page_icon="🚑", layout="wide")

# Constants
CONTENT_PACK_PATH = "config/study_content_pack.xlsx"

def main():
    # 1. Load & Validate Content (Cached/Once)
    # We do this outside the main render loop to ensure it happens on startup
    if "content_pack" not in st.session_state:
        # Load
        if not os.path.exists(CONTENT_PACK_PATH):
             st.error("Content pack not found!")
             st.stop()

        content_hash = utils.calculate_hash(CONTENT_PACK_PATH)
        sheets = utils.load_content_pack(CONTENT_PACK_PATH)

        # Validate
        utils.validate_content_pack(sheets)

        # Try Resume or Initialize
        resumed = engine.try_resume_session(sheets, content_hash)
        if not resumed:
            engine.initialize_session(sheets, content_hash)
            engine.generate_patient_queue()
            engine.save_session_state()

        engine.ensure_query_param()

    # 2. Check for "Withdraw" (Footer/Sidebar)
    with st.sidebar:
        st.write(f"Session ID: {st.session_state.session_id}")
        st.write(f"Version: {st.session_state.app_version}")
        if st.button("Withdraw & Delete Session", type="primary"):
            if os.path.exists(st.session_state.log_filepath):
                os.remove(st.session_state.log_filepath)
            engine.delete_session_state()
            st.warning("Session withdrawn and log deleted.")
            st.stop()

    # 3. Handle Transitions (from previous interaction)
    if st.session_state.get("last_decision") == "made":
        st.session_state.last_decision = None # Reset flag

        # Logic to determine if washout is needed BEFORE moving index?
        # No, we move index, then see if the NEW patient starts a new block.

        prev_idx = st.session_state.current_patient_index
        st.session_state.current_patient_index += 1
        curr_idx = st.session_state.current_patient_index

        queue = st.session_state.patient_queue

        if curr_idx < len(queue):
            prev_patient = queue[prev_idx]
            curr_patient = queue[curr_idx]

            # Washout Check
            # Trigger between Scenario A and B.
            # Assuming Tutorial is always first.
            # So if Prev != Curr, and neither is Tutorial, then Washout.

            if (prev_patient["Scenario"] != curr_patient["Scenario"]) and \
               (prev_patient["Scenario"] != "Tutorial") and \
               (curr_patient["Scenario"] != "Tutorial"):
                st.session_state.washout_active = True
                st.session_state.washout_start_time = datetime.now()
                st.session_state.card_start_time = None
                st.session_state.accumulated_cost_ms = 0
                engine.save_session_state()
                # Do NOT start new patient yet. Wait for washout to finish.
            else:
                engine.start_new_patient()
        else:
            # End of queue
            engine.save_session_state()

        st.rerun()

    # 4. Phase 1: Onboarding
    if not st.session_state.onboarding_complete:
        st.title("Triage Study: Onboarding")


        with st.form("onboarding_form"):
            role = st.selectbox("Role", ["-- Click here --", "Paramedic", "Nurse", "Doctor", "Police", "Fire/Rescue", "Student/Other"])
            years = st.selectbox("Years Experience", ["-- Click here --", "0-2 years", "2-5 years", "5-10 years", "10+ years"])
            fatigue = st.selectbox("Fatigue Status", ["-- Click here --", "On Shift (Currently working)", "Off Shift (<12 hours since last shift)", "Rested (>12 hours since last shift)"])

            # Tool Selection (Implicitly defined? Or User selects?
            # README says: "Triage Decision: User sees buttons defined in the Tools Excel tab for their assigned tool."
            # "Inputs: Role, Years Exp, Fatigue Status."
            # It doesn't explicitly say user chooses Tool. But "participant_role" is logged. "tool_id" is logged.
            # Usually in studies, tool is assigned or user selects.
            # "Triage Decision: User sees buttons defined in the Tools Excel tab for their assigned tool."
            # I will add a dropdown for Tool ID for now, as it's critical.

            tool_id = st.selectbox("Assigned Tool", ["-- Click here --", "ATS", "SMART", "10S"])

            submitted = st.form_submit_button("Start Study")
            if submitted:
                # Validate that all fields were selected (not placeholder)
                if role == "-- Click here --" or years == "-- Click here --" or fatigue == "-- Click here --" or tool_id == "-- Click here --":
                    st.error("Please select an option for all fields before proceeding.")
                else:
                    st.session_state.participant_role = role
                    st.session_state.years_exp = years
                    st.session_state.fatigue_status = fatigue
                    st.session_state.tool_id = tool_id
                    st.session_state.onboarding_complete = True
                    engine.save_session_state()
                    engine.start_new_patient()
                    st.rerun()

        # --- Test Mode: Rapid Onboarding ---
        st.divider()
        st.subheader("Rapid Entry")
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            if st.button("⚡ Rapid ATS", type="primary"):
                st.session_state.participant_role = "Paramedic"
                st.session_state.years_exp = "5-10 years"
                st.session_state.fatigue_status = "Rested"
                st.session_state.tool_id = "ATS"
                st.session_state.onboarding_complete = True
                engine.save_session_state()
                engine.start_new_patient()
                st.rerun()
        with rc2:
            if st.button("⚡ Rapid SMART", type="primary"):
                st.session_state.participant_role = "Paramedic"
                st.session_state.years_exp = "5-10 years"
                st.session_state.fatigue_status = "Rested"
                st.session_state.tool_id = "SMART"
                st.session_state.onboarding_complete = True
                engine.save_session_state()
                engine.start_new_patient()
                st.rerun()
        with rc3:
            if st.button("⚡ Rapid 10S", type="primary"):
                st.session_state.participant_role = "Paramedic"
                st.session_state.years_exp = "5-10 years"
                st.session_state.fatigue_status = "Rested"
                st.session_state.tool_id = "10S"
                st.session_state.onboarding_complete = True
                engine.save_session_state()
                engine.start_new_patient()
                st.rerun()
        # -----------------------------------

        return

    # 5. Phase 4: Washout (Active?)
    if st.session_state.washout_active:
        components.render_washout()
        st.session_state.washout_active = False
        engine.save_session_state()
        engine.start_new_patient() # Now start the patient timer
        st.rerun()
        return

    # 6. Phase 2 & 3: Main Scenario / Tutorial
    patient = engine.get_current_patient()

    if patient:
        # Header
        st.progress((st.session_state.current_patient_index) / len(st.session_state.patient_queue))
        st.caption(f"Patient {st.session_state.current_patient_index + 1} / {len(st.session_state.patient_queue)}")

        # Custom CSS for HUD Layout - COMPREHENSIVE SPACING COLLAPSE
        st.markdown(
            """
            <style>
            /* ===== HUD STYLING ===== */
            
            /* Right Columns (Col 2 & 3): Sticky HUD Elements */
            [data-testid="stColumn"]:nth-of-type(2) > div,
            [data-testid="stColumn"]:nth-of-type(3) > div {
                position: sticky;
                top: 1rem;
                height: 95vh;
                overflow-y: auto;
                padding-right: 5px;
                background-color: transparent;
            }

            /* Ensure Image in HUD scales nicely */
            [data-testid="stColumn"]:nth-of-type(3) img {
                max-height: 40vh; /* Increased size */
                object-fit: contain;
                width: 100%; /* Full width */
                display: block;
                padding: 0px !important;
                margin-bottom: 0.5rem;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Render HUD Layout (3 Columns)
        # Left: Actions (A-E)
        # Mid: Clinical Findings (Results)
        # Right: Triage Decision + Context
        c_left, c_mid, c_right = st.columns([0.4, 0.4, 0.2], gap="medium")

        with c_left:
            components.render_patient_header(patient)
            st.divider()
            st.markdown("### Actions")
            components.render_action_buttons(patient, st.session_state.content_pack["Config"])
        
        with c_mid:
            components.render_clinical_findings(patient)

        with c_right:
            components.render_patient_avatar(patient)
            st.divider()
            components.render_triage_tools(st.session_state.content_pack["Tools"], st.session_state.tool_id)

    else:
        # Phase 5: Completion
        st.balloons()
        st.title("Study Complete")
        st.success("Thank you for your participation.")

        timestamp = st.session_state.get("session_timestamp", "0000")
        code = f"{st.session_state.session_id[-6:]}_{timestamp[-4:]}"
        st.subheader(f"Completion Code: {code}")
        st.info("Please record this code.")

if __name__ == "__main__":
    main()
