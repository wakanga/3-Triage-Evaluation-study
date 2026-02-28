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
    "prior_triage_training",
    "fatigue_status",
    "consent_given",
    "tool_id",
    "scenario_type",
    "patient_id",
    "patient_sequence_order",
    "event_type",
    "action_key",
    "decision_raw",
    "decision_normalized",
    "gold_standard",
    "correct",
    "error_type",
    "deviation",
    "t_real_ms",
    "t_sim_ms",
]

def _session_state_path(session_id):
    return os.path.join("data_out", f"session_{session_id}.json")

def _dt_to_iso(dt):
    return dt.isoformat() if dt else None

def _dt_from_iso(value):
    return datetime.fromisoformat(value) if value else None

def get_investigation_result(patient_row, action_key):
    """
    Returns the text result for an action.
    If the Excel cell is empty/NaN, returns the clinical default.
    """
    # 1. Get the raw value from the patient row
    # Note: Column names are usually "{action_key}_Text"
    # But let's check if the patient_row key exists directly or we need to append _Text
    # The structure in render_patient_card implies keys are like 'walk_Text'
    
    col_name = f"{action_key}_Text"
    raw_text = patient_row.get(col_name)
    
    # 2. Check if it is valid (not empty/NaN)
    if pd.notna(raw_text) and str(raw_text).strip() != "":
        return str(raw_text)
    
    # 3. If empty, return Defaults based on Key
    defaults = {
        'temp': "Normothermic",
        'history': "History is as given",
        'bp': "Hemodynamically Stable",
        'pain': "Pain Score: Unknown/Unable to elicit",
        'spo2': "SpO2: >94% on room air",
        'pupils': "Pupils Equal and Reactive",
        'bsl': "BSL: 5.5 mmol/L"
    }
    
    return defaults.get(action_key, "No specific abnormality detected.")

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
        "prior_triage_training": st.session_state.get("prior_triage_training"),
        "pre_confidence": st.session_state.get("pre_confidence"),
        "pre_understanding": st.session_state.get("pre_understanding"),
        "consent_given": st.session_state.get("consent_given", False),
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
        "pending_triage": st.session_state.get("pending_triage"),
        "pre_practice_active": st.session_state.get("pre_practice_active", False),
        "practice_transition_active": st.session_state.get("practice_transition_active", False),
        "post_perception_done": st.session_state.get("post_perception_done", False),
        "washout_animation_done": st.session_state.get("washout_animation_done", False),
        "washout_logged": st.session_state.get("washout_logged", False),
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
    params = st.query_params
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
    st.session_state.prior_triage_training = payload.get("prior_triage_training")
    st.session_state.pre_confidence = payload.get("pre_confidence")
    st.session_state.pre_understanding = payload.get("pre_understanding")
    st.session_state.consent_given = payload.get("consent_given", False)
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
    st.session_state.pending_triage = payload.get("pending_triage")
    st.session_state.pre_practice_active = payload.get("pre_practice_active", False)
    st.session_state.practice_transition_active = payload.get("practice_transition_active", False)
    st.session_state.post_perception_done = payload.get("post_perception_done", False)
    st.session_state.washout_animation_done = payload.get("washout_animation_done", False)
    st.session_state.washout_logged = payload.get("washout_logged", False)

    st.session_state.log_filepath = payload.get("log_filepath")
    if not st.session_state.log_filepath:
        timestamp = st.session_state.session_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.log_filepath = f"data_out/logs_{st.session_state.session_id}_{timestamp}.csv"
    return True

def ensure_query_param():
    if "session_id" in st.session_state:
        st.query_params["sid"] = st.session_state.session_id

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
        st.session_state.pending_triage = None

        # Ensure data_out directory exists
        os.makedirs("data_out", exist_ok=True)

        st.session_state.log_filepath = f"data_out/logs_{st.session_state.session_id}_{timestamp}.csv"
        save_session_state()

def get_gold_standard(patient, tool_id):
    """
    Retrieves the specific consensus reference for the tool.
    """
    if tool_id == "SMART":
        col_name = "Ref_SMART"
    elif tool_id == "TST":
        col_name = "Ref_Standard_TST"
    else:
        col_name = f"Ref_{tool_id}"
    
    # 1. Try specific column
    val = patient.get(col_name)
    if pd.notna(val):
        return str(val)
        
    # 2. Fallback
    return "NA"

def calculate_deviation(gold_std, selected):
    """
    Calculates numerical deviation between Gold Standard and Selected.
    Mapping (Implied Ordinality):
    Black (Dead) = 0
    Red (Immediate) = 1
    Yellow (Urgent) = 2
    Green (Ambulatory) = 3
    
    Note: The user asked for "Undertriage" to be negative deviation.
    If Gold=Red(1) and Selected=Green(3) -> Underrated severity? 
    Wait, "Undertriage" means you treated them as LESS urgent than they are.
    
    Let's stick to standard clinical urgency scales:
    1 = Immediate (Most Urgent)
    2 = Urgent
    3 = Non-Urgent
    4 = Dead? No, Dead is usually 0 or separate.
    
    Let's use the USER'S example:
    "0 would be in midline with the goldstandard. 1 would be 1+ SD above GS. and -1 would be 1 SD undertriage"
    
    Hypothesis:
    Higher Score = Higher Urgency? Or Higher Score = "More Intervention"?
    Usually "Overtriage" = Assigning a higher priority than needed (e.g. Red instead of Yellow).
    
    Let's assign Priority Levels (Higher Number = HIGHER PRIORITY/More Urgent):
    Green = 1
    Yellow = 2
    Red = 3
    (Black is tricky. If GS=Red and you say Black, is that under or over? It's "undertriage" of resources, but "overestimation" of injury severity.
     Usually in MCIs:
     Green (3) -> Yellow (2) -> Red (1). 
     Let's use:
     Red: 3
     Yellow: 2
     Green: 1
     Black: 0
     
     Example 1: Gold=Yellow(2). User=Red(3).
     Score = User(3) - Gold(2) = +1. (Overtriage). Matches user logic.
     
     Example 2: Gold=Red(3). User=Green(1).
     Score = User(1) - Gold(3) = -2. (Undertriage). Matches user logic.
     
     Perfect.
    """
    
    mapping = {
        "Black": 0, "Dead": 0,
        "Green": 1, 
        "Yellow": 2,
        "Red": 3,
        "Blue": 1, "White": 1
    }
    
    val_gold = mapping.get(gold_std, -100)
    val_sel = mapping.get(selected, -100)
    
    if val_gold == -100 or val_sel == -100:
        return None
        
    return val_sel - val_gold

def log_event(event_type, action_key=None, decision_raw=None, decision_normalized=None, notes=None):
    """Logs an event to the CSV file and optionally to Google Sheets."""
    if "log_filepath" not in st.session_state:
        return # Should not happen

    patient = get_current_patient()
    
    # Do not log data for practice cases
    if patient and patient.get("Is_Practice") == True:
        return
    
    patient_id = patient["ID"] if patient else "NA"
    scenario_type = patient["Scenario"] if patient else "NA"
    
    # Gold Standard Fetch
    tool_id = st.session_state.get("tool_id", "NA")
    gold_standard = "NA"
    if patient and tool_id != "NA":
        gold_standard = get_gold_standard(patient, tool_id)

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

    # Grading & Metrics
    is_correct = ""
    deviation = ""
    error_type = ""
    
    if event_type == "decision" and gold_standard != "NA" and decision_normalized:
        # Correctness
        is_correct = 1 if (gold_standard == decision_normalized) else 0
        
        # Deviation
        dev_val = calculate_deviation(gold_standard, decision_normalized)
        deviation = dev_val if dev_val is not None else "ERR"

        if deviation == 0:
            error_type = "correct"
        elif deviation is not None and deviation > 0:
            error_type = "overtriage"
        elif deviation is not None and deviation < 0:
            error_type = "undertriage"

    row = {
        "timestamp_utc": now.isoformat(),
        "app_version": st.session_state.app_version,
        "content_pack_hash": st.session_state.content_pack_hash,
        "session_id": st.session_state.session_id,
        "participant_role": st.session_state.get("participant_role", "NA"),
        "prior_triage_training": st.session_state.get("prior_triage_training", "NA"),
        "fatigue_status": st.session_state.get("fatigue_status", "NA"),
        "consent_given": st.session_state.get("consent_given", False),
        "tool_id": tool_id,
        "scenario_type": scenario_type,
        "patient_id": patient_id,
        "patient_sequence_order": st.session_state.get("current_patient_index", 0) + 1 if patient else "",
        "event_type": event_type,
        "action_key": action_key if action_key else "",
        "decision_raw": decision_raw if decision_raw else "",
        "decision_normalized": decision_normalized if decision_normalized else "",
        "gold_standard": gold_standard,
        "correct": is_correct,
        "error_type": error_type,
        "deviation": deviation, 
        "t_real_ms": t_real_ms,
        "t_sim_ms": t_sim_ms,
    }

    # New Columns Requirement: 
    # participant_code (session_id), profession (participant_role), triage_system_id (tool_id), 
    # scenario_id (scenario_type), start/end (timestamp implies end, card_start implies start)
    
    header = not os.path.exists(st.session_state.log_filepath)
    
    # Update LOG_COLUMNS dynamically if needed, 
    # but better to keep the global constant aligned.
    # We need to update the global LOG_COLUMNS variable too.
    
    with open(st.session_state.log_filepath, "a", newline="", encoding="utf-8") as f:
        # Note: We must ensure LOG_COLUMNS matches the row keys
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        if header:
            writer.writeheader()
        writer.writerow(row)
        f.flush()

    # Log to Google Sheets if in Mode C and this is a triage decision
    if event_type == "decision" and st.session_state.get("data_mode") == "Mode C":
        active_sheet = st.session_state.get("active_google_sheet")
        if active_sheet:
            from src import cloud
            triage_cat = decision_normalized if decision_normalized else decision_raw
            clinician_notes = notes if notes else ""
            cloud.append_triage_log(
                active_sheet,
                [now.isoformat(), patient_id, triage_cat, clinician_notes]
            )

def log_nasa_tlx(data):
    """Logs NASA-TLX results to a separate CSV."""
    filepath = "data_out/nasa_tlx_logs.csv"
    
    # We need to capture context: Session, Role, Tool, Scenario (Just Finished)
    # The 'current' patient index points to the NEXT patient (usually). 
    # But NASA-TLX happens *between* scenarios. 
    # We need to know which scenario just finished. 
    # Ideally, we stored `completed_scenario_id` in session state or we infer it.
    # For now, let's use the `scenario_type` from the *previous* patient if possible, 
    # or rely on `washout_pending_scenario` logic from app.py.
    
    # Actually, simpler: app.py triggers this when `prev_patient["Scenario"] != curr_patient["Scenario"]`.
    # So the scenario we just finished is `prev_patient["Scenario"]`.
    # But engine.py doesn't have easy access to app.py variables.
    # We can pass the scenario name in `data` or infer it.
    
    # Let's assume the caller (component) might not know it easily.
    # Better: Use `st.session_state.get('last_finished_scenario', 'Unknown')`
    
    scenario = st.session_state.get('last_finished_scenario', 'Unknown')
    
    row = {
        "timestamp_utc": datetime.now().isoformat(),
        "session_id": st.session_state.session_id,
        "participant_role": st.session_state.get("participant_role", "NA"),
        "tool_id": st.session_state.get("tool_id", "NA"),
        "scenario_type": scenario,
        **data
    }
    
    columns = [
        "timestamp_utc", "session_id", "participant_role", "tool_id", "scenario_type",
        "nasa_mental", "nasa_physical", "nasa_temporal", "nasa_performance", 
        "nasa_effort", "nasa_frustration", "nasa_raw_score", "comments"
    ]
    
    header = not os.path.exists(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if header:
            writer.writeheader()
        writer.writerow(row)
        f.flush()

def log_post_perception(data):
    """Logs post-simulation perception results to a separate CSV."""
    filepath = "data_out/post_perception_logs.csv"
    
    row = {
        "timestamp_utc": datetime.now().isoformat(),
        "session_id": st.session_state.session_id,
        "participant_role": st.session_state.get("participant_role", "NA"),
        "tool_id": st.session_state.get("tool_id", "NA"),
        **data
    }
    
    columns = [
        "timestamp_utc", "session_id", "participant_role", "tool_id", 
        "post_understanding", "post_preparedness", "post_tool_effective"
    ]
    
    header = not os.path.exists(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if header:
            writer.writeheader()
        writer.writerow(row)
        f.flush()

def generate_patient_queue():
    """Generates the patient queue from the content pack."""
    df_patients = st.session_state.content_pack["Patients"]
    
    # Check if 'ID' exists?
    if "ID" not in df_patients.columns:
        st.error("Patients sheet missing 'ID' column.")
        st.stop()
        
    # Logic:
    # 1. Practice patients first (Is_Practice == True)
    # 2. Scenarios: Group by Scenario. Randomize order of Scenarios? Or randomize patients within Scenarios?
    # Usually: Randomized Scenarios, or Set Order.
    # README says: "Scenarios: Blocks of patients presented in randomized order."
    
    tutorials = df_patients[df_patients["Is_Practice"] == True].to_dict("records")
    
    # Get Scenarios
    scenarios = df_patients[df_patients["Is_Practice"] != True]
    scenario_names = scenarios["Scenario"].unique()
    
    # Shuffle Scenario Blocks?
    # "Blocks of patients presented in randomized order." implies:
    # Block A (Patients 1,2,3), Block B (Patients 4,5,6).
    # Shuffle Blocks: B, A.
    # Then within Block... usually randomized too? Or fixed?
    # Let's assume Shuffle Blocks, then Shuffle Patients Within Block (common in studies).
    # Or just Shuffle Blocks.
    
    # Let's just shuffle blocks for now.
    import random
    scenario_list = list(scenario_names)
    random.shuffle(scenario_list)
    
    study_queue = []
    for sc_name in scenario_list:
        block_patients = scenarios[scenarios["Scenario"] == sc_name].to_dict("records")
        # Shuffle within block? Let's do it to be safe for "randomized order".
        random.shuffle(block_patients)
        study_queue.extend(block_patients)
        
    # Combine
    full_queue = tutorials + study_queue
    
    # Store IDs in session state
    st.session_state.patient_queue = full_queue
    st.session_state.patient_queue_ids = [p["ID"] for p in full_queue]


def get_current_patient():
    """Returns the current patient dictionary or None."""
    idx = st.session_state.current_patient_index
    queue = st.session_state.patient_queue
    if 0 <= idx < len(queue):
        return queue[idx]
    return None


def start_new_patient():
    """Resets state for the new patient card."""
    st.session_state.card_start_time = datetime.now()
    st.session_state.revealed_actions = set() # Reset revealed actions
    st.session_state.accumulated_cost_ms = 0
    st.session_state.last_decision = None
    st.session_state.pending_triage = None
