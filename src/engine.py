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
SCHEMA_VERSION = "2.1"
SESSION_STATE_VERSION = 2
INCLUDE_TLX_PHYSICAL = False

LEDGER_COLUMNS = [
    # Base
    "t_run_ms", "ledger_row_index", "session_id", "completion_code", "record_type", "schema_version", 
    "app_version", "content_pack_hash", "participant_role", "fatigue_status", 
    "prior_triage_training",
    # Event + Encounter common
    "patient_id", "tool_id", "scenario_type", "is_practice", 
    # Event specific
    "event_type", "action_key", "decision_raw", "user_tag_normalized", 
    "reference_tag_normalized", "deviation", "t_real_ms", "t_sim_ms",
    # Encounter specific
    "patient_sequence_order", "Time_to_First_Action", "Time_to_Tag", 
    "Time_to_Hemorrhage_Ctrl", "Time_to_Airway_Ctrl", "Dwell_rr", "Dwell_pulse_rad", 
    "Dwell_Measurable", "Seq_Error_Count", "Seq_Error_Measurable", "LSI_Applicable", 
    "Required_LSI", "Missed_LSI_Flag", "Missing_LSI_List", "Error_Class",
    # TLX
    "nasa_mental", "nasa_temporal", "nasa_effort", "nasa_frustration", "nasa_performance",
    "nasa_physical",
    # Post
    "post_understanding", "post_preparedness", "post_tool_effective",
    # Session End
    "n_encounters_total", "n_practice_encounters", "n_real_encounters", 
    "n_decisions_made", "mean_time_to_tag_ms", "critical_under_rate",
    # Health Counters
    "total_ledger_rows", "total_event_rows", "total_encounter_rows", 
    "total_tlx_rows", "total_post_rows"
]

def safe_str(x):
    """Returns empty string for NA/None, else string version."""
    if x is None or pd.isna(x) or str(x).strip() == "NA" or str(x).strip() == "nan":
        return ""
    return str(x)

def append_ledger_row(row_data):
    """Writes a single row to the session's ledger CSV."""
    if "log_filepath" not in st.session_state or not st.session_state.log_filepath:
        return
        
    # 1) Increment global ledger row index
    if "ledger_row_index" not in st.session_state:
        st.session_state.ledger_row_index = 0
    st.session_state.ledger_row_index += 1
    
    rtype = row_data.get("record_type", "unknown")
    
    # 2) Increment specific row counters
    counter_key = f"total_{rtype}_rows"
    if counter_key not in st.session_state:
        st.session_state[counter_key] = 0
    st.session_state[counter_key] += 1
    
    st.session_state.total_ledger_rows = st.session_state.get("total_ledger_rows", 0) + 1
    
    # 3) Prevent carry-over bugs: Build a fresh dictionary mapped cleanly to LEDGER_COLUMNS
    fresh_row = {col: "" for col in LEDGER_COLUMNS}
    
    # Populate the relevant keys
    for k, v in row_data.items():
        if k in fresh_row:
            fresh_row[k] = safe_str(v)
            
    # Always write ledger row index and completion_code
    fresh_row["ledger_row_index"] = str(st.session_state.ledger_row_index)
    
    if st.session_state.get("completion_code"):
        fresh_row["completion_code"] = safe_str(st.session_state.completion_code)
    
    filepath = st.session_state.log_filepath
    header = not os.path.exists(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        if header:
            writer.writeheader()
        writer.writerow(fresh_row)
        f.flush()

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
        "block_start_time": _dt_to_iso(st.session_state.get("block_start_time")),
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
        "encounter_events": st.session_state.get("encounter_events", []),
        "completed_encounters": st.session_state.get("completed_encounters", []),
        "completion_code": st.session_state.get("completion_code", ""),
        "ledger_row_index": st.session_state.get("ledger_row_index", 0),
        "total_ledger_rows": st.session_state.get("total_ledger_rows", 0),
        "total_event_rows": st.session_state.get("total_event_rows", 0),
        "total_encounter_rows": st.session_state.get("total_encounter_rows", 0),
        "total_tlx_rows": st.session_state.get("total_tlx_rows", 0),
        "total_post_rows": st.session_state.get("total_post_rows", 0),
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
    st.session_state.block_start_time = _dt_from_iso(payload.get("block_start_time"))
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
    st.session_state.encounter_events = payload.get("encounter_events", [])
    st.session_state.completed_encounters = payload.get("completed_encounters", [])
    st.session_state.completion_code = payload.get("completion_code", "")
    st.session_state.ledger_row_index = payload.get("ledger_row_index", 0)
    st.session_state.total_ledger_rows = payload.get("total_ledger_rows", 0)
    st.session_state.total_event_rows = payload.get("total_event_rows", 0)
    st.session_state.total_encounter_rows = payload.get("total_encounter_rows", 0)
    st.session_state.total_tlx_rows = payload.get("total_tlx_rows", 0)
    st.session_state.total_post_rows = payload.get("total_post_rows", 0)

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
        st.session_state.block_start_time = datetime.now()
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
        st.session_state.encounter_events = []
        st.session_state.completed_encounters = []
        st.session_state.completion_code = ""
        st.session_state.ledger_row_index = 0
        st.session_state.total_ledger_rows = 0
        st.session_state.total_event_rows = 0
        st.session_state.total_encounter_rows = 0
        st.session_state.total_tlx_rows = 0
        st.session_state.total_post_rows = 0

        # Washout State
        st.session_state.washout_active = False
        st.session_state.washout_start_time = None

        # Logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.session_timestamp = timestamp
        st.session_state.pending_triage = None

        # Ensure data_out directory exists
        os.makedirs("data_out", exist_ok=True)

        st.session_state.log_filepath = f"data_out/session_{st.session_state.session_id}_{timestamp}.csv"
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
        "Black": 0, "Dead": 0, "White": 0,
        "Green": 1, 
        "Yellow": 2,
        "Red": 3,
        "Blue": 1
    }
    
    val_gold = mapping.get(gold_std, -100)
    val_sel = mapping.get(selected, -100)
    
    if val_gold == -100 or val_sel == -100:
        return None
        
    return val_sel - val_gold

def evaluate_outcome_class(user_tag, gold_tag):
    if user_tag in ["Black", "Dead", "Expectant", "White"] or gold_tag in ["Black", "Dead", "Expectant", "White"]:
        return "NA_Black"
    
    mapping = {
        "Green": 1, "Yellow": 2, "Red": 3, "P1": 3, "P2": 2, "P3": 1, "Blue": 1, "White": 0
    }
    val_user = mapping.get(user_tag, None)
    val_gold = mapping.get(gold_tag, None)
    
    if val_user is None or val_gold is None:
        return ""
        
    diff = val_user - val_gold
    if diff == 0:
        return "None"
    elif diff == 1:
        return "Minor_Over"
    elif diff >= 2:
        return "Major_Over"
    elif diff == -1:
        return "Minor_Under"
    elif diff <= -2:
        return "Critical_Under"
    
    return ""

def finalize_encounter_log(patient, tool_id):
    events = st.session_state.get("encounter_events", [])
    if not events:
        return
        
    target_events = [e for e in events if e.get("event_type") in ["reveal", "decision"]]
    first_action_ms = target_events[0]["t_real_ms"] if target_events else ""

    decision_events = [e for e in target_events if e.get("event_type") == "decision"]
    time_to_tag = decision_events[-1]["t_real_ms"] if decision_events else ""
        
    hem_events = [e for e in target_events if e.get("action_key") == "hemorrhage_ctrl"]
    t_hemorrhage = hem_events[0]["t_real_ms"] if hem_events else ""
        
    airway_events = [e for e in target_events if e.get("action_key") == "airway_man"]
    t_airway = airway_events[0]["t_real_ms"] if airway_events else ""
        
    dwell_rr, dwell_pulse = "", ""
    dwell_measurable = True
    
    for i, e in enumerate(target_events):
        if e.get("action_key") == "rr" and dwell_rr == "":
            if i + 1 < len(target_events):
                dwell_rr = target_events[i+1]["t_real_ms"] - e["t_real_ms"]
            else:
                dwell_measurable = False
        elif e.get("action_key") == "pulse_rad" and dwell_pulse == "":
            if i + 1 < len(target_events):
                dwell_pulse = target_events[i+1]["t_real_ms"] - e["t_real_ms"]
            else:
                dwell_measurable = False

    seq_error_count = 0
    seq_error_measurable = True
    max_order_seen = 0
    
    order_col = f"{tool_id}_Order"
    config_df = st.session_state.content_pack.get("Config")
    
    if config_df is not None and order_col in config_df.columns:
        order_map = {}
        for _, row in config_df.iterrows():
            key = row.get("Action_Key")
            order_val = row.get(order_col)
            if pd.notna(key) and pd.notna(order_val):
                try:
                    order_map[key] = int(float(order_val))
                except (ValueError, TypeError):
                    pass
        
        for e in target_events:
            k = e.get("action_key")
            o = order_map.get(k, 0)
            if o > 0:
                if o < max_order_seen:
                    seq_error_count += 1
                else:
                    max_order_seen = o
    else:
        seq_error_measurable = False
        seq_error_count = ""
        
    decision_event = decision_events[-1] if decision_events else None
    decision_normalized = decision_event.get("decision_normalized", "") if decision_event else ""
    gold_standard = get_gold_standard(patient, tool_id)
    
    error_class = evaluate_outcome_class(decision_normalized, gold_standard)
    
    lsi_app_raw = patient.get("LSI_Applicable", False)
    lsi_applicable = True if str(lsi_app_raw).strip().upper() == "TRUE" or lsi_app_raw is True else False
    
    req_lsi_raw = patient.get("Required_LSI", "")
    
    missed_lsi_flag = ""
    missing_lsi_list = ""
    
    if not lsi_applicable:
        pass # Stays ""
    else:
        if decision_normalized == "Red":
            req_keys = []
            if pd.notna(req_lsi_raw):
                req_keys = [k.strip().lower() for k in str(req_lsi_raw).split(",") if k.strip()]
                
            clicked_keys = set([str(e.get("action_key")).lower() for e in target_events if e.get("action_key")])
            
            missed = [k for k in req_keys if k not in clicked_keys]
            if missed:
                missed_lsi_flag = "True"
                missing_lsi_list = ",".join(missed)
            else:
                missed_lsi_flag = "False"
        else:
            missed_lsi_flag = ""

    now = datetime.now()
    if st.session_state.get("block_start_time"):
        t_run_ms = int((now - st.session_state.block_start_time).total_seconds() * 1000)
    else:
        t_run_ms = 0

    row = {
        "t_run_ms": t_run_ms,
        "session_id": st.session_state.session_id,
        "completion_code": st.session_state.get("completion_code", ""),
        "record_type": "encounter",
        "schema_version": SCHEMA_VERSION,
        "app_version": st.session_state.app_version,
        "content_pack_hash": st.session_state.content_pack_hash,
        "participant_role": st.session_state.get("participant_role", ""),
        "prior_triage_training": st.session_state.get("prior_triage_training", ""),
        "fatigue_status": st.session_state.get("fatigue_status", ""),
        
        "patient_id": patient.get("ID", ""),
        "tool_id": tool_id,
        "scenario_type": patient.get("Scenario", ""),
        "is_practice": patient.get("Is_Practice", False),
        "patient_sequence_order": st.session_state.get("current_patient_index", 0) + 1,
        
        "Time_to_First_Action": first_action_ms,
        "Time_to_Tag": time_to_tag,
        "Time_to_Hemorrhage_Ctrl": t_hemorrhage,
        "Time_to_Airway_Ctrl": t_airway,
        
        "Dwell_rr": dwell_rr,
        "Dwell_pulse_rad": dwell_pulse,
        "Dwell_Measurable": dwell_measurable,
        
        "Seq_Error_Count": seq_error_count,
        "Seq_Error_Measurable": seq_error_measurable,
        
        "Unassigned_Actions": "",
        "Unassigned_Actions_Measurable": False,
        
        "LSI_Applicable": lsi_applicable,
        "Required_LSI": req_lsi_raw if pd.notna(req_lsi_raw) else "",
        "Missed_LSI_Flag": missed_lsi_flag,
        "Missing_LSI_List": missing_lsi_list,
        
        "Error_Class": error_class
    }
    
    if "completed_encounters" not in st.session_state:
        st.session_state.completed_encounters = []
    
    # Also include the user tag and reference tag for final session aggregation lookup
    row["User_Tag"] = decision_normalized
    row["Reference_Tag"] = gold_standard
    st.session_state.completed_encounters.append(row)
    
    append_ledger_row(row)

def log_event(event_type, action_key=None, decision_raw=None, decision_normalized=None):
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
    deviation = ""
    
    if event_type == "decision" and gold_standard != "NA" and decision_normalized:
        # Deviation
        dev_val = calculate_deviation(gold_standard, decision_normalized)
        deviation = dev_val if dev_val is not None else "ERR"

    if st.session_state.get("block_start_time"):
        t_run_ms = int((now - st.session_state.block_start_time).total_seconds() * 1000)
    else:
        t_run_ms = 0

    row = {
        "t_run_ms": t_run_ms,
        "session_id": st.session_state.session_id,
        "completion_code": st.session_state.get("completion_code", ""),
        "record_type": "event",
        "schema_version": SCHEMA_VERSION,
        "app_version": st.session_state.app_version,
        "content_pack_hash": st.session_state.content_pack_hash,
        "participant_role": st.session_state.get("participant_role", "NA"),
        "fatigue_status": st.session_state.get("fatigue_status", "NA"),
        "prior_triage_training": st.session_state.get("prior_triage_training", "NA"),
        
        "patient_id": patient_id,
        "tool_id": tool_id,
        "scenario_type": scenario_type,
        "is_practice": patient.get("Is_Practice", False) if patient else False,
        
        "event_type": event_type,
        "action_key": action_key if action_key else "",
        "decision_raw": decision_raw if decision_raw else "",
        "user_tag_normalized": decision_normalized if decision_normalized else "",
        "reference_tag_normalized": gold_standard,
        "deviation": deviation, 
        "t_real_ms": t_real_ms,
        "t_sim_ms": t_sim_ms,
    }

    if "encounter_events" not in st.session_state:
        st.session_state.encounter_events = []
    
    # Store legacy key 'decision_normalized' internally for `finalize_encounter_log` to parse easily
    internal_row = dict(row)
    internal_row["decision_normalized"] = decision_normalized if decision_normalized else ""
    st.session_state.encounter_events.append(internal_row)

    append_ledger_row(row)

    if event_type == "decision" and patient:
        finalize_encounter_log(patient, tool_id)

    # Log to Google Sheets if in Mode C and this is a triage decision
    if event_type == "decision" and st.session_state.get("data_mode") == "Mode C":
        active_sheet = st.session_state.get("active_google_sheet")
        if active_sheet:
            from src import cloud
            triage_cat = decision_normalized if decision_normalized else decision_raw
            cloud.append_triage_log(
                active_sheet,
                [now.isoformat(), patient_id, triage_cat]
            )

def log_nasa_tlx(data):
    """Logs NASA-TLX results to the session ledger."""
    scenario = st.session_state.get('last_finished_scenario', 'Unknown')
    
    now = datetime.now()
    if st.session_state.get("block_start_time"):
        t_run_ms = int((now - st.session_state.block_start_time).total_seconds() * 1000)
    else:
        t_run_ms = 0

    row = {
        "t_run_ms": t_run_ms,
        "session_id": st.session_state.session_id,
        "completion_code": st.session_state.get("completion_code", ""),
        "record_type": "tlx",
        "schema_version": SCHEMA_VERSION,
        "app_version": st.session_state.app_version,
        "content_pack_hash": st.session_state.content_pack_hash,
        "participant_role": st.session_state.get("participant_role", "NA"),
        "fatigue_status": st.session_state.get("fatigue_status", "NA"),
        "prior_triage_training": st.session_state.get("prior_triage_training", "NA"),
        "tool_id": st.session_state.get("tool_id", "NA"),
        "scenario_type": scenario,
        **data
    }
    
    append_ledger_row(row)

def log_post_perception(data):
    """Logs post-simulation perception results to the session ledger."""
    now = datetime.now()
    if st.session_state.get("block_start_time"):
        t_run_ms = int((now - st.session_state.block_start_time).total_seconds() * 1000)
    else:
        t_run_ms = 0

    row = {
        "t_run_ms": t_run_ms,
        "session_id": st.session_state.session_id,
        "completion_code": st.session_state.get("completion_code", ""),
        "record_type": "post",
        "schema_version": SCHEMA_VERSION,
        "app_version": st.session_state.app_version,
        "content_pack_hash": st.session_state.content_pack_hash,
        "participant_role": st.session_state.get("participant_role", "NA"),
        "fatigue_status": st.session_state.get("fatigue_status", "NA"),
        "prior_triage_training": st.session_state.get("prior_triage_training", "NA"),
        "tool_id": st.session_state.get("tool_id", "NA"),
        **data
    }
    
    append_ledger_row(row)

def log_session_end():
    """Calculates final session metrics, generates completion code, and writes session index."""
    encounters = st.session_state.get("completed_encounters", [])
    n_total = len(encounters)
    practice_encs = [e for e in encounters if str(e.get("is_practice")).strip().lower() == "true"]
    real_encs = [e for e in encounters if str(e.get("is_practice")).strip().lower() != "true"]
    
    n_practice = len(practice_encs)
    n_real = len(real_encs)
    
    tag_times = []
    for e in real_encs:
        try:
            val = float(e.get("Time_to_Tag"))
            tag_times.append(val)
        except (ValueError, TypeError):
            pass
            
    mean_time = sum(tag_times) / len(tag_times) if tag_times else ""
    
    crit_under = len([e for e in real_encs if e.get("Error_Class") == "Critical_Under"])
    cu_rate = (crit_under / n_real) if n_real > 0 else ""
    
    timestamp_end = datetime.now()
    timestamp_str = st.session_state.get("session_timestamp", "0000")
    comp_code = f"{st.session_state.session_id[-6:]}_{timestamp_str[-4:]}"
    st.session_state.completion_code = comp_code

    if st.session_state.get("block_start_time"):
        t_run_ms = int((timestamp_end - st.session_state.block_start_time).total_seconds() * 1000)
    else:
        t_run_ms = 0

    row = {
        "t_run_ms": t_run_ms,
        "session_id": st.session_state.session_id,
        "completion_code": comp_code,
        "record_type": "session_end",
        "schema_version": SCHEMA_VERSION,
        "app_version": st.session_state.app_version,
        "content_pack_hash": st.session_state.content_pack_hash,
        "participant_role": st.session_state.get("participant_role", ""),
        "fatigue_status": st.session_state.get("fatigue_status", ""),
        "prior_triage_training": st.session_state.get("prior_triage_training", ""),
        
        "n_encounters_total": n_total,
        "n_practice_encounters": n_practice,
        "n_real_encounters": n_real,
        "n_decisions_made": n_total,
        "mean_time_to_tag_ms": mean_time,
        "critical_under_rate": cu_rate,
        
        "total_ledger_rows": st.session_state.get("total_ledger_rows", 0) + 1, # +1 for this row about to fall in
        "total_event_rows": st.session_state.get("total_event_rows", 0),
        "total_encounter_rows": st.session_state.get("total_encounter_rows", 0),
        "total_tlx_rows": st.session_state.get("total_tlx_rows", 0),
        "total_post_rows": st.session_state.get("total_post_rows", 0)
    }
    append_ledger_row(row)
    
    idx_row = {
        "timestamp_utc": timestamp_end.isoformat(),
        "session_id": st.session_state.session_id,
        "completion_code": comp_code,
        "participant_role": st.session_state.get("participant_role", ""),
        "fatigue_status": st.session_state.get("fatigue_status", ""),
        "prior_triage_training": st.session_state.get("prior_triage_training", ""),
        "app_version": st.session_state.app_version,
        "schema_version": SCHEMA_VERSION,
        "content_pack_hash": st.session_state.content_pack_hash,
        "n_real_encounters": n_real,
        "critical_under_rate": safe_str(cu_rate)
    }
    
    idx_path = "data_out/session_index.csv"
    idx_cols = list(idx_row.keys())
    header = not os.path.exists(idx_path)
    with open(idx_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=idx_cols)
        if header:
            writer.writeheader()
        writer.writerow(idx_row)
        f.flush()

    save_session_state()

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
    st.session_state.encounter_events = []
    st.session_state.last_decision = None
    st.session_state.pending_triage = None
