import streamlit as st
import pandas as pd
import os
import time
import hashlib
import io
from datetime import datetime
from src import utils, engine, components, cloud

# Set Page Config
st.set_page_config(page_title="STEP: Triage Study", page_icon="🚑", layout="wide")

# Constants
CONTENT_PACK_PATH = "config/study_content_pack.xlsx"

def main():
    with st.sidebar:
        st.header("Admin Settings")
        data_mode = st.radio("Data Source", [
            "Mode A: In App (.xlsx)", 
            "Mode B: Upload (.xlsx)", 
            "Mode C: Cloud Upload"
        ])
        st.divider()

    # Admin Logic: What data mode is selected?
    if "content_pack" not in st.session_state:
        sheets = None
        content_hash = None

        if "Mode A" in data_mode:
            config_dir = "config"
            if not os.path.exists(config_dir):
                st.sidebar.error(f"Config directory '{config_dir}' not found!")
                st.stop()
                
            local_files = [f for f in os.listdir(config_dir) if f.endswith('.xlsx') and not f.startswith('~')]
            
            if not local_files:
                st.sidebar.warning(f"No .xlsx files found in '{config_dir}' folder!")
                st.stop()
                
            selected_local_file = st.sidebar.selectbox("Select In-App Config File", local_files, index=None, placeholder="Choose a file...")
            
            if selected_local_file:
                pack_path = os.path.join(config_dir, selected_local_file)
                content_hash = utils.calculate_hash(pack_path)
                sheets = utils.load_content_pack(pack_path)
                st.session_state.data_mode = "Mode A"
            else:
                st.info("Please select a config file from the sidebar to begin.")
                st.stop()
            
        elif "Mode B" in data_mode:
            uploaded_file = st.sidebar.file_uploader("Upload Local Content Pack", type=["xlsx"])
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                content_hash = hashlib.sha256(bytes_data).hexdigest()
                sheets = utils.load_content_pack(io.BytesIO(bytes_data))
                st.session_state.data_mode = "Mode B"
            else:
                st.info("Please upload a local patient queue (.xlsx) to begin.")
                st.stop()
        else:
            # Mode C
            st.session_state.data_mode = "Mode C"
            available_sheets = cloud.get_available_sheets()
            if not available_sheets:
                st.sidebar.warning("No Google Sheets found or authentication failed.")
                st.stop()
            
            selected_sheet = st.sidebar.selectbox("Select Study Content Pack", available_sheets, index=None, placeholder="Choose a sheet...")
            if selected_sheet:
                content_hash = hashlib.sha256(selected_sheet.encode()).hexdigest()
                sheets = cloud.fetch_gsheet_data(selected_sheet)
                st.session_state.active_google_sheet = selected_sheet
                
                if not sheets:
                    st.error("Failed to load data from the selected Google Sheet.")
                    st.stop()
            else:
                st.info("Please select a Google Sheet to begin.")
                st.stop()

        # Validate
        utils.validate_content_pack(sheets)
        
        # Defensively cast Is_Practice to boolean in case of string parsing (GSheets)
        if "Patients" in sheets:
            sheets["Patients"]["Is_Practice"] = sheets["Patients"].get("Is_Practice", False).apply(
                lambda x: True if str(x).strip().upper() == "TRUE" or x is True else False
            )

        st.session_state.content_pack = sheets # Make sure this is set so resume/initialize doesn't fail if they need it immediately
        
        # Try Resume or Initialize
        resumed = engine.try_resume_session(sheets, content_hash)
        if not resumed:
            engine.initialize_session(sheets, content_hash)
            engine.generate_patient_queue()
            engine.save_session_state()

        engine.ensure_query_param()
        st.rerun()
    else:
        # If content pack is loaded, display the status in the sidebar
        if "Mode C" in st.session_state.get("data_mode", ""):
            st.sidebar.success(f"Connected to: {st.session_state.get('active_google_sheet', 'Google Sheets')}")
        else:
            st.sidebar.success(f"Mode: {st.session_state.get('data_mode', 'Local')}")

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

            if prev_patient.get("Is_Practice", False) and not curr_patient.get("Is_Practice", False):
                # Trigger Practice Transition Screen
                st.session_state.practice_transition_active = True
                # Reset any accumulated session-level practice data if needed
                st.session_state.card_start_time = None
                engine.save_session_state()

            elif (prev_patient["Scenario"] != curr_patient["Scenario"]) and \
               (prev_patient["Scenario"] != "Tutorial") and \
               (curr_patient["Scenario"] != "Tutorial"):
                
                # Check if the JUST FINISHED scenario was a practice
                # prev_patient is the last one of the block we just finished.
                is_prev_practice = prev_patient.get("Is_Practice", False)
                
                if not is_prev_practice:
                    # TRIGGER NASA-TLX FIRST
                    st.session_state.nasa_tlx_active = True
                    st.session_state.last_finished_scenario = prev_patient["Scenario"]
                
                    # THEN PREPARE WASHOUT
                    st.session_state.washout_active = True
                    st.session_state.washout_start_time = datetime.now()
                    st.session_state.card_start_time = None
                    st.session_state.accumulated_cost_ms = 0
                    engine.save_session_state()
                else:
                    # If it WAS a tutorial, skip NASA TLX AND skip Washout.
                    # Just go straight to the next patient.
                    engine.start_new_patient()
            else:
                engine.start_new_patient()
        else:
            # End of queue
            engine.save_session_state()

        st.rerun()

    # 4. Phase 1: Onboarding
    if not st.session_state.onboarding_complete:
        if not st.session_state.get("splash_viewed", False):
            ph = st.empty()
            ph.markdown("""
            <style>
            @keyframes fadeInOut {
                0% { opacity: 0; }
                15% { opacity: 1; }
                85% { opacity: 1; }
                100% { opacity: 0; }
            }
            .splash {
                text-align: center;
                margin-top: 30vh;
                animation: fadeInOut 4.5s forwards;
            }
            </style>
            <div class="splash">
                <h1 style="font-size: 3.5em; margin-bottom: 0; line-height: 1.2;">Welcome to the Standardised Triage Evaluation Platform (STEP)</h1>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(4.8)
            ph.empty()
            st.session_state.splash_viewed = True

        st.title("Onboarding")


        with st.form("onboarding_form"):
            role = st.selectbox("Role", ["-- Click here --", "Paramedic", "Nurse", "Doctor", "Police", "Fire/Rescue", "Student/Other"])
            years = st.selectbox("Years Experience", ["-- Click here --", "0-2 years", "2-5 years", "5-10 years", "10+ years"])
            fatigue = st.selectbox("Fatigue Status", ["-- Click here --", "On Shift (Currently working)", "Off Shift (<12 hours since last shift)", "Rested (>12 hours since last shift)"])
            prior_triage = st.selectbox("Prior Triage Training", ["-- Click here --", "None", "MIMMS", "Hospital Triage Only", "TST Training", "SMART Training", "Other"])
            tool_id = st.selectbox("Assigned Tool", ["-- Click here --", "SMART", "TST"])

            st.markdown("### Pre-Simulation Readiness")
            pre_conf = st.slider("I feel confident triaging in an MCI.", 0, 100, 50)
            pre_und = st.slider("I understand the differences between common triage scales.", 0, 100, 50)
            
            st.markdown("### Ethics & Consent")
            consent_1 = st.checkbox("I understand this is a research simulation and not clinical training certification.")
            consent_2 = st.checkbox("I consent to anonymised data use.")

            submitted = st.form_submit_button("Start Study")
            if submitted:
                # Validate that all fields were selected (not placeholder)
                if "-- Click here --" in [role, years, fatigue, prior_triage, tool_id]:
                    st.error("Please select an option for all dropdown fields before proceeding.")
                elif not (consent_1 and consent_2):
                    st.error("You must explicitly consent and acknowledge the simulation nature to participate.")
                else:
                    st.session_state.participant_role = role
                    st.session_state.years_exp = years
                    st.session_state.fatigue_status = fatigue
                    st.session_state.prior_triage_training = prior_triage
                    st.session_state.tool_id = tool_id
                    st.session_state.pre_confidence = pre_conf
                    st.session_state.pre_understanding = pre_und
                    st.session_state.consent_given = True
                    st.session_state.onboarding_complete = True
                    st.session_state.pre_practice_active = True
                    engine.save_session_state()
                    st.rerun()

        # --- Test Mode: Rapid Onboarding ---
        st.divider()
        st.subheader("Rapid Entry")
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("⚡ Rapid SMART", type="primary"):
                st.session_state.participant_role = "Paramedic"
                st.session_state.years_exp = "5-10 years"
                st.session_state.fatigue_status = "Rested"
                st.session_state.tool_id = "SMART"
                st.session_state.onboarding_complete = True
                st.session_state.pre_practice_active = True
                engine.save_session_state()
                st.rerun()
        with rc2:
            if st.button("⚡ Rapid TST", type="primary"):
                st.session_state.participant_role = "Paramedic"
                st.session_state.years_exp = "5-10 years"
                st.session_state.fatigue_status = "Rested"
                st.session_state.tool_id = "TST"
                st.session_state.onboarding_complete = True
                st.session_state.pre_practice_active = True
                engine.save_session_state()
                st.rerun()
        # -----------------------------------

        return

    # Phase 1b: Pre-Practice Orientation Screen
    if st.session_state.get("pre_practice_active", False):
        st.title("Orientation")
        st.markdown("""
        ### Welcome to the Simulation
        
        Before the main study begins, you will be presented with **two practice cases**. Feel free to explore the interface, click on the clinical assessments, and familiarize yourself with the layout. 

        *Imagine you have just arrived at a chaotic mass casualty scene. You are walking from patient to patient, making rapid initial assessments.*
        
        When you are ready to evaluate the next patient, simply click on the appropriate triage colour block at the bottom.
        
        **Note:** These practice cases are entirely for your orientation and will not be scored or included in the final analysis.
        """)
        
        if st.button("Start Practice", type="primary"):
            st.session_state.pre_practice_active = False
            engine.start_new_patient()
            engine.save_session_state()
            st.rerun()
        return

    # Phase 4a: NASA-TLX (Before Washout)
    if st.session_state.get("nasa_tlx_active", False):
        components.render_nasa_tlx()
        return

    # 5. Phase 4b: Washout (Active?)
    if st.session_state.washout_active:
        components.render_washout()
        return

    # Phase 4c: Practice Transition Screen
    if st.session_state.get("practice_transition_active", False):
        st.title("Practice Complete")
        st.info("The practice cases are now complete. The live simulation begins now.")
        st.warning("All subsequent cases will be timed and logged for analysis. Please treat them as a real scenario.")
        if st.button("Start Simulation", type="primary"):
            st.session_state.practice_transition_active = False
            from datetime import datetime
            st.session_state.block_start_time = datetime.now()
            engine.start_new_patient() 
            engine.save_session_state()
            st.rerun()
        return

    # 6. Phase 2 & 3: Main Scenario / Tutorial
    patient = engine.get_current_patient()

    if patient:
        # Header
        st.progress((st.session_state.current_patient_index) / len(st.session_state.patient_queue))
        st.caption(f"Patient {st.session_state.current_patient_index + 1} / {len(st.session_state.patient_queue)}")

        if "header_sticky" not in st.session_state:
            st.session_state.header_sticky = False

        # Custom CSS for HUD Layout
        components.inject_custom_css()

        # === HEADER LAYOUT (Unified) ===
        with st.container():
            c_patient, c_triage = st.columns([0.65, 0.35], gap="large")
            
            # 1. Patient Section (Left)
            with c_patient:
                # Avatar Left | Info Right
                c_avatar, c_info = st.columns([0.25, 0.75], gap="small")
                with c_avatar:
                    components.render_patient_avatar(patient)
                with c_info:
                    components.render_patient_info(patient)

            # 2. Triage Section (Right)
            with c_triage:
                st.markdown("#### Triage decision.")
                # Render Tools
                components.render_triage_tools(st.session_state.content_pack["Tools"], st.session_state.tool_id)
        
        st.divider()
        
        # === ACTION GRID (Full Width) ===
        st.markdown("### Actions")
        components.render_action_buttons(patient, st.session_state.content_pack["Config"])
        
        # Sidebar Removed completely from this view.

    else:
        # Phase 5: Completion
        st.title("STEP: Study Complete")

        if not st.session_state.get("post_perception_done"):
            st.markdown("### Final Feedback")
            st.info("Please answer a few final questions about your experience.")
            with st.form("post_sim_form"):
                post_und = st.slider("My understanding of triage scale differences improved.", 0, 100, 50)
                post_prep = st.slider("I feel more prepared to triage in an MCI.", 0, 100, 50)
                post_tool = st.slider("This tool structured my thinking effectively.", 0, 100, 50)
                
                if st.form_submit_button("Submit & Finish"):
                    st.session_state.post_perception_done = True
                    data = {
                        "post_understanding": post_und,
                        "post_preparedness": post_prep,
                        "post_tool_effective": post_tool,
                    }
                    engine.log_post_perception(data)
                    engine.log_session_end()
                    # save_session_state is called inside log_session_end
                    st.rerun()
            return

        st.balloons()
        st.success("Thank you for your participation.")

        code = st.session_state.get("completion_code", "UNKNOWN")
        st.subheader(f"Completion Code: {code}")
        st.info("Please record this code.")

if __name__ == "__main__":
    main()
