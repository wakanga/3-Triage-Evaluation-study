import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
import os
import random
import time

APP_VERSION = "v1.0.0"

def initialize_session(content_pack, content_hash):
    """Initializes the session state if not already present."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.content_pack_hash = content_hash
        st.session_state.app_version = APP_VERSION
        st.session_state.content_pack = content_pack

        # Onboarding flags
        st.session_state.onboarding_complete = False

        # Patient State
        st.session_state.patient_queue = []
        st.session_state.current_patient_index = 0

        # Card State
        st.session_state.card_start_time = None
        st.session_state.revealed_actions = set()
        st.session_state.accumulated_cost_ms = 0

        # Washout State
        st.session_state.washout_active = False
        st.session_state.washout_start_time = None

        # Logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.session_timestamp = timestamp

        # Ensure data_out directory exists
        os.makedirs("data_out", exist_ok=True)

        st.session_state.log_filepath = f"data_out/logs_{st.session_state.session_id}_{timestamp}.csv"

def generate_patient_queue():
    """Generates the randomized patient queue."""
    df_patients = st.session_state.content_pack["Patients"]

    # 1. Tutorial Patients
    tutorial_patients = df_patients[df_patients["Is_Tutorial"] == True].to_dict('records')

    # 2. Scenario Blocks
    scenarios = df_patients[df_patients["Is_Tutorial"] == False]
    entrapment = scenarios[scenarios["Scenario"] == "Entrapment"].to_dict('records')
    violence = scenarios[scenarios["Scenario"] == "Violence"].to_dict('records')

    # Randomize order within blocks (optional, but good practice)
    random.shuffle(entrapment)
    random.shuffle(violence)

    # Randomize block order
    blocks = [entrapment, violence]
    random.shuffle(blocks)

    # Flatten queue: Tutorial -> Block A -> Block B
    # We will handle Washout logic by checking Scenario changes during traversal
    queue = tutorial_patients + blocks[0] + blocks[1]

    st.session_state.patient_queue = queue
    st.session_state.current_patient_index = 0

def start_new_patient():
    """Resets card state for the new patient."""
    st.session_state.card_start_time = datetime.now()
    st.session_state.revealed_actions = set()
    st.session_state.accumulated_cost_ms = 0

    # Auto-reveal 'visual' and 'walk' if specified?
    # README says: "User clicks 'Check Pulse'. Logic: Check revealed_actions."
    # Visual is implicit (cost 0), so it's always "revealed" in a sense, but maybe we don't log it unless explicitly asked?
    # Actually, visual is usually immediate info.
    # But let's stick to the mechanics: user clicks buttons.
    # However, 'Visible_Text' is always shown.

    current_patient = get_current_patient()
    if current_patient:
        log_event(event_type="card_start", action_key="system")

def get_current_patient():
    """Returns the current patient dict or None if finished."""
    if st.session_state.current_patient_index < len(st.session_state.patient_queue):
        return st.session_state.patient_queue[st.session_state.current_patient_index]
    return None

def log_event(event_type, action_key=None, decision_raw=None, decision_normalized=None):
    """Logs an event to the CSV file."""
    if "log_filepath" not in st.session_state:
        return # Should not happen

    patient = get_current_patient()
    # Handle washout or end-of-game where patient might be None or we are in transition
    # If washout, we log against the *next* scenario? Or previous?
    # README: "Log washout_start and washout_complete"

    patient_id = patient["ID"] if patient else "NA"
    scenario_type = patient["Scenario"] if patient else "NA"
    gold_standard = patient["Gold_Standard_Normalized"] if patient else "NA"

    # Timing
    now = datetime.now()
    if st.session_state.card_start_time:
        t_real_ms = int((now - st.session_state.card_start_time).total_seconds() * 1000)
    else:
        t_real_ms = 0

    t_sim_ms = t_real_ms + st.session_state.accumulated_cost_ms

    # Grading
    is_critical_fail = False
    is_over_triage = False

    if event_type == "decision":
        if gold_standard == "Red" and decision_normalized != "Red":
            is_critical_fail = True
        if gold_standard != "Red" and decision_normalized == "Red":
            is_over_triage = True

    row = {
        "timestamp_utc": now.isoformat(),
        "app_version": st.session_state.app_version,
        "content_pack_hash": st.session_state.content_pack_hash,
        "session_id": st.session_state.session_id,
        "participant_role": st.session_state.get("participant_role", "NA"),
        "tool_id": st.session_state.get("tool_id", "NA"),
        "scenario_type": scenario_type,
        "patient_id": patient_id,
        "event_type": event_type,
        "action_key": action_key if action_key else "",
        "decision_raw": decision_raw if decision_raw else "",
        "decision_normalized": decision_normalized if decision_normalized else "",
        "t_real_ms": t_real_ms,
        "t_sim_ms": t_sim_ms,
        "gold_standard": gold_standard,
        "is_critical_fail": is_critical_fail,
        "is_over_triage": is_over_triage
    }

    df = pd.DataFrame([row])

    # Write to file
    header = not os.path.exists(st.session_state.log_filepath)
    df.to_csv(st.session_state.log_filepath, mode='a', header=header, index=False)
