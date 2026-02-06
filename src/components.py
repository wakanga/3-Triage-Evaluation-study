import streamlit as st
import os
import pandas as pd
from PIL import Image
import time
from src.engine import log_event, save_session_state, get_investigation_result

def load_image(filename):
    """Loads an image from assets/img, falling back to default.png."""
    path = os.path.join("assets/img", filename)
    if not os.path.exists(path) or not filename:
        path = "assets/img/default.png"
    return Image.open(path)

def render_patient_header(patient):
    """Renders the patient textual info (ID, Name, Scenario, Description)."""
    st.subheader(f"Patient ID: {patient['ID']} | {patient.get('Patient_Name', '')}")
    st.markdown(f"**Scenario:** {patient['Scenario']}")
    visible_text = patient.get("Visible_Text")
    if pd.isna(visible_text) or visible_text is None:
        visible_text = "No visible findings recorded."
    st.info(visible_text)

def render_patient_avatar(patient):
    """Renders just the patient avatar image."""
    avatar_file = patient.get("Avatar_File", "default.png")
    # Handle NaN
    if pd.isna(avatar_file):
        avatar_file = "default.png"
    image = load_image(avatar_file)
    st.image(image, use_container_width=True)

def render_clinical_findings(patient):
    """Renders the revealed clinical findings in a clean list style with minimal spacing."""
    st.markdown("### Findings")
    if not st.session_state.revealed_actions:
        st.caption("No findings yet.")
        return

    # Use container with explicit minimal spacing
    
    # Mapping for cleaner labels
    label_map = {
        "airway_man": "Airway Maneuver",
        "airway_obs": "Airway Obstruction",
        "work_breath": "Work of Breathing",
        "pulse_rate": "Pulse Rate",
        "pulse_rad": "Radial Pulse",
        "cap_refill": "Capillary Refill",
        "bp": "Blood Pressure",
        "spo2": "SpO2",
        "rr": "Resp Rate",
        "gcs": "GCS",
        "avpu": "AVPU",
        "temp": "Temp",
        "hemorrhage": "Hemorrhage",
        "pupils": "Pupils",
        "walk": "Ambulatory",
        "pain": "Pain",
        "history": "History",
        "look_listen": "Look/Listen"
    }

    for action in st.session_state.revealed_actions:
        text = get_investigation_result(patient, action)
        
        # Polish the label
        # 1. Try exact match in map
        # 2. If not, replace underscores and title case
        clean_label = label_map.get(action.lower(), action.replace("_", " ").title())
        
        # Handle acronyms that might have been title-cased by fallback
        if clean_label.upper() in ["GCS", "AVPU", "BP", "RR", "SPO2", "ABC"]:
            clean_label = clean_label.upper()

        # Special Case: 'Walk' often reads better as a statement
        if action.lower() == "walk":
             st.success(f"{text}")
        else:
             st.success(f"**{clean_label}:** {text}")

def render_action_buttons(patient, config_df):
    """Renders the investigation buttons in a simple, reliable vertical stack."""
    
    # 1. Component-Specific CSS for Vertical Stack
    # Much simpler CSS instructions: Just ensure tight spacing between elements.
    st.markdown("""
        <style>
        /* Tighten vertical spacing between standard Streamlit elements */
        div[data-testid="stVerticalBlock"] {
            gap: 1rem !important;
        }
        
        /* Specific header styling for the categories */
        .category-header {
            font-weight: 800;
            font-size: 1.1rem;
            color: #444;
            margin-top: 1rem;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid #eee;
            padding-bottom: 4px;
        }

        /* Tweak button spacing */
        div.row-widget.stButton {
            margin-bottom: 0.4rem !important; /* Added spacing between items */
            padding-bottom: 0.0rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Get current tool to filter actions
    tool_id = st.session_state.get("tool_id", "ATS")
    valid_actions = config_df[config_df['Valid_Tools'].str.contains(tool_id, na=False)]

    categories = ['A', 'B', 'C', 'D', 'E']
    labels = {
        'A': 'Airway', 
        'B': 'Breathing', 
        'C': 'Circulation', 
        'D': 'Disability', 
        'E': 'Exposure & History'
    }

    # Consolidated Container for the Grid
    with st.container():
        for cat in categories:
            cat_actions = valid_actions[valid_actions['Category'] == cat]
            
            # --- pre-calculate visible buttons ---
            visible_buttons = []
            for _, row in cat_actions.iterrows():
                key = row['Action_Key']
                text_col = f"{key}_Text"
                raw_result = str(patient.get(text_col, ""))
                if "not applicable" in raw_result.lower():
                    continue
                if key == "airway_man":
                    airway_result = str(patient.get("airway_Text", ""))
                    if "clear" in airway_result.lower():
                        continue
                visible_buttons.append(row)

            if not visible_buttons:
                continue

            # --- RENDER STRATEGY: Simple Vertical Stack ---
            
            # 1. Render Category Header
            st.markdown(f"<div class='category-header'>{labels[cat]}</div>", unsafe_allow_html=True)

            # 2. Render Buttons sequentially
            for _, row in pd.DataFrame(visible_buttons).iterrows():
                _render_single_button_vertical(row)

def _render_single_button_vertical(row):
    """Helper to render a single action button vertically."""
    key = row['Action_Key']
    label = row['Button_Label']
    cost = row['Cost_ms']
    
    # Label cleanup
    for prefix in ["Airway:", "Breathing:", "Circulation:", "Disability:"]:
        if label.startswith(prefix):
            label = label[len(prefix):].strip()
    label = label.strip()
    
    is_revealed = key in st.session_state.revealed_actions
    
    # Toggle behavior
    btn_type = "primary" if is_revealed else "secondary"
    # Optional: Add checkmark to show it's active
    display_label = f"✓ {label}" if is_revealed else label
    
    # Use standard buttons (not container width) for a 'narrower' look
    if st.button(display_label, key=f"btn_{key}", type=btn_type):
        if is_revealed:
            st.session_state.revealed_actions.remove(key)
            log_event(event_type="hide", action_key=key)
        else:
            st.session_state.revealed_actions.add(key)
            st.session_state.accumulated_cost_ms += cost
            log_event(event_type="reveal", action_key=key)
            
        save_session_state()
        st.rerun()

def render_triage_tools(tools_df, tool_id):
    """Renders the triage decision buttons for the selected tool with tight spacing."""
    st.markdown("### Triage Decision")

    # Filter tools by the selected Tool_ID
    my_tools = tools_df[tools_df["Tool_ID"] == tool_id]

    # Single column stack for narrow sidebar with minimal spacing
    for i, (_, row) in enumerate(my_tools.iterrows()):
        label = row['Button_Label']
        normalized = row['Normalized_Value']
        
        emoji_map = {
            "Red": "🔴",
            "Yellow": "🟡",
            "Green": "🟢",
            "Black": "⚫",
            "White": "⚪",
            "Blue": "🔵",
            "Orange": "🟠"
        }

        btn_label = f"{emoji_map.get(normalized, '')} {label}"

        if st.button(btn_label, key=f"decision_{i}", use_container_width=True):
            # Log decision
            log_event(event_type="decision", action_key="triage_decision",
                      decision_raw=label, decision_normalized=normalized)

            st.session_state.last_decision = "made" # Flag to trigger transition
            save_session_state()
            st.rerun()

def render_washout(duration_seconds=15):
    """Renders the washout screen with a countdown."""
    placeholder = st.empty()

    # Log start
    log_event(event_type="washout_start")

    for i in range(duration_seconds, 0, -1):
        placeholder.markdown(f"""
        # 🛑 WASHOUT PERIOD

        ### Next scenario starting in {i} seconds...

        *Take a deep breath.*
        """)
        time.sleep(1)

    log_event(event_type="washout_complete")
    placeholder.empty()
