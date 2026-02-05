import streamlit as st
import os
import pandas as pd
from PIL import Image
import time
from src.engine import log_event

def load_image(filename):
    """Loads an image from assets/img, falling back to default.png."""
    path = os.path.join("assets/img", filename)
    if not os.path.exists(path) or not filename:
        path = "assets/img/default.png"
    return Image.open(path)

def render_patient_card(patient):
    """Renders the patient avatar and visible text."""
    col1, col2 = st.columns([1, 2])

    with col1:
        avatar_file = patient.get("Avatar_File", "default.png")
        # Handle NaN
        if pd.isna(avatar_file):
            avatar_file = "default.png"
        image = load_image(avatar_file)
        st.image(image, use_column_width=True)

    with col2:
        st.subheader(f"Patient ID: {patient['ID']}")
        st.markdown(f"**Scenario:** {patient['Scenario']}")
        st.info(patient['Visible_Text'])

        # Render Fog of War Information
        st.markdown("### Clinical Findings")
        for action in st.session_state.revealed_actions:
            # action is the action_key (e.g., 'walk', 'pulse')
            text_col = f"{action}_Text"
            text = patient.get(text_col)
            if pd.notna(text):
                 st.success(f"**{action.upper()}:** {text}")
            else:
                 st.warning(f"**{action.upper()}:** No response / Indeterminate.")

def render_action_buttons(patient, config_df):
    """Renders the investigation buttons."""
    st.markdown("### Investigation")

    # We want to display buttons in a grid
    cols = st.columns(3)

    # Filter config for actions that have data in the patient row
    # AND are not 'visual' (which is implicit/free/always there?)
    # actually visual text is usually part of visible text or separate?
    # The README says: "Visual (Implicit Visual Scan) Cost 0".
    # Usually this is just given.

    valid_actions = []
    for _, row in config_df.iterrows():
        key = row['Action_Key']
        if key == 'visual':
            continue

        text_col = f"{key}_Text"
        # Only show button if the cell is NOT empty in Excel
        if pd.notna(patient.get(text_col)):
            valid_actions.append(row)

    for i, row in enumerate(valid_actions):
        col = cols[i % 3]
        key = row['Action_Key']
        label = row['Button_Label']
        cost = row['Cost_ms']

        with col:
            # If already revealed, disable or change style?
            # README says: "If new, add to set and add Cost_ms". Idempotent.
            # So we can keep it clickable, just don't add cost again?
            # Or disable it to show it's done. Disabling is clearer.

            disabled = key in st.session_state.revealed_actions
            if st.button(f"{label} (+{cost/1000}s)", key=f"btn_{key}", disabled=disabled):
                st.session_state.revealed_actions.add(key)
                st.session_state.accumulated_cost_ms += cost
                log_event(event_type="reveal", action_key=key)
                st.rerun()

def render_triage_tools(tools_df, tool_id):
    """Renders the triage decision buttons for the selected tool."""
    st.markdown("### Triage Decision")

    # Filter tools by the selected Tool_ID
    my_tools = tools_df[tools_df["Tool_ID"] == tool_id]

    cols = st.columns(2)
    for i, (_, row) in enumerate(my_tools.iterrows()):
        col = cols[i % 2]
        label = row['Button_Label']
        normalized = row['Normalized_Value']

        # Color styling
        color_map = {
            "Red": "primary", # Red is usually primary/destructive
            "Yellow": "secondary",
            "Green": "secondary",
            "Black": "secondary"
        }
        # Streamlit buttons don't support custom colors easily without CSS,
        # but we can use type="primary" for emphasis.
        # Let's just use standard buttons, maybe add emoji?

        emoji_map = {
            "Red": "🔴",
            "Yellow": "🟡",
            "Green": "🟢",
            "Black": "⚫"
        }

        btn_label = f"{emoji_map.get(normalized, '')} {label}"

        with col:
            if st.button(btn_label, key=f"decision_{i}", use_container_width=True):
                # Log decision
                log_event(event_type="decision", action_key="triage_decision",
                          decision_raw=label, decision_normalized=normalized)

                # Move to next patient
                # We handle the logic in app.py or here?
                # Better to set a flag or callback.
                # But standard Streamlit way: update state and rerun.

                st.session_state.last_decision = "made" # Flag to trigger transition
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
