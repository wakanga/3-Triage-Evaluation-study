import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
import os
import random
import time
import json
import csv

APP_VERSION = "v1.0.0"
SESSION_STATE_VERSION = 1
LOG_COLUMNS = [
    "timestamp_utc",
    "app_version",
    "content_pack_hash",
    "session_id",
    "participant_role",
    "tool_id",
    "scenario_type",
    "patient_id",
    "event_type",
    "action_key",
    "decision_raw",
    "decision_normalized",
    "t_real_ms",
    "t_sim_ms",
    "gold_standard",
    "is_critical_fail",
    "is_over_triage",
]

def _session_state_path(session_id):
    return os.path.join("data_out", f"session_{session_id}.json")

def _dt_to_iso(dt):
    return dt.isoformat() if dt else None

def _dt_from_iso(value):
    return datetime.fromisoformat(value) if value else None

def build_patient_map():
    df_patients = st.session_state.content_pack["Patients"]
    records = df_patients.to_dict("records")
    return {record["ID"]: record for record in records}

def save_session_state():
    if "session_id" not in st.session_state:
        return

    payload = {
        "version": SESSION_STATE_VERSION,
        "session_id": st.session_state.session_id,
        "session_timestamp": st.session_state.get("session_timestamp"),
        "content_pack_hash": st.session_state.get("content_pack_hash"),
        "app_version": st.session_state.get("app_version"),
        "participant_role": st.session_state.get("participant_role"),
        "years_exp": st.session_state.get("years_exp"),
        "fatigue_status": st.session_state.get("fatigue_status"),
        "tool_id": st.session_state.get("tool_id"),
        "onboarding_complete": st.session_state.get("onboarding_complete", False),
        "patient_queue_ids": st.session_state.get("patient_queue_ids", []),
        "current_patient_index": st.session_state.get("current_patient_index", 0),
        "card_start_time": _dt_to_iso(st.session_state.get("card_start_time")),
        "revealed_actions": list(st.session_state.get("revealed_actions", set())),
        "accumulated_cost_ms": st.session_state.get("accumulated_cost_ms", 0),
        "washout_active": st.session_state.get("washout_active", False),
        "washout_start_time": _dt_to_iso(st.session_state.get("washout_start_time")),
        "last_decision": st.session_state.get("last_decision"),
        "log_filepath": st.session_state.get("log_filepath"),
    }

    os.makedirs("data_out", exist_ok=True)
    path = _session_state_path(st.session_state.session_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

def delete_session_state():
    if "session_id" not in st.session_state:
        return
    path = _session_state_path(st.session_state.session_id)
    if os.path.exists(path):
        os.remove(path)

def try_resume_session(content_pack, content_hash):
    params = st.experimental_get_query_params()
    session_id = None
    if "sid" in params and params["sid"]:
        session_id = params["sid"][0]

    if not session_id:
        return False

    path = _session_state_path(session_id)
    if not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if payload.get("content_pack_hash") != content_hash:
        st.warning("Content pack changed since this session started. Starting a new session.")
        return False

    st.session_state.session_id = payload.get("session_id", session_id)
    st.session_state.session_timestamp = payload.get("session_timestamp")
    st.session_state.content_pack_hash = content_hash
    st.session_state.app_version = payload.get("app_version", APP_VERSION)
    st.session_state.content_pack = content_pack

    st.session_state.participant_role = payload.get("participant_role")
    st.session_state.years_exp = payload.get("years_exp")
    st.session_state.fatigue_status = payload.get("fatigue_status")
    st.session_state.tool_id = payload.get("tool_id")
    st.session_state.onboarding_complete = payload.get("onboarding_complete", False)

    st.session_state.patient_map = build_patient_map()
    st.session_state.patient_queue_ids = payload.get("patient_queue_ids", [])
    st.session_state.patient_queue = [
        st.session_state.patient_map[pid]
        for pid in st.session_state.patient_queue_ids
        if pid in st.session_state.patient_map
    ]
    if len(st.session_state.patient_queue) != len(st.session_state.patient_queue_ids):
        st.warning("Some patients from the saved session were missing in the current content pack.")
    st.session_state.current_patient_index = payload.get("current_patient_index", 0)

    st.session_state.card_start_time = _dt_from_iso(payload.get("card_start_time"))
    st.session_state.revealed_actions = set(payload.get("revealed_actions", []))
    st.session_state.accumulated_cost_ms = payload.get("accumulated_cost_ms", 0)

    st.session_state.washout_active = payload.get("washout_active", False)
    st.session_state.washout_start_time = _dt_from_iso(payload.get("washout_start_time"))
    st.session_state.last_decision = payload.get("last_decision")

    st.session_state.log_filepath = payload.get("log_filepath")
    if not st.session_state.log_filepath:
        timestamp = st.session_state.session_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.log_filepath = f"data_out/logs_{st.session_state.session_id}_{timestamp}.csv"
    return True

def ensure_query_param():
    if "session_id" in st.session_state:
        st.experimental_set_query_params(sid=st.session_state.session_id)

def initialize_session(content_pack, content_hash):
    """Initializes the session state if not already present."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.content_pack_hash = content_hash
        st.session_state.app_version = APP_VERSION
        st.session_state.content_pack = content_pack
        st.session_state.patient_map = build_patient_map()

        # Onboarding flags
        st.session_state.onboarding_complete = False

        # Patient State
        st.session_state.patient_queue = []
        st.session_state.patient_queue_ids = []
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
        save_session_state()

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
    st.session_state.patient_queue_ids = [patient["ID"] for patient in queue]
    st.session_state.current_patient_index = 0
    save_session_state()

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
        save_session_state()

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
    if event_type in {"washout_start", "washout_complete"}:
        t_real_ms = 0
        t_sim_ms = 0
    else:
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

    header = not os.path.exists(st.session_state.log_filepath)
    with open(st.session_state.log_filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        if header:
            writer.writeheader()
        writer.writerow(row)
        f.flush()
