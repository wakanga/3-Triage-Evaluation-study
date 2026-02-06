import streamlit as st
import os
import pandas as pd
from PIL import Image
import time
from src.engine import log_event, save_session_state, get_investigation_result, log_nasa_tlx

def load_image(filename):
    """Loads an image from assets/img, falling back to default.png."""
    path = os.path.join("assets/img", filename)
    if not os.path.exists(path) or not filename:
        path = "assets/img/default.png"
    return Image.open(path)

def inject_custom_css():
    """Injects core CSS for the application, handling basic visual polish."""
    
    css_content = """
        <style>
        /* ===== Visual Polish ===== */

        /* Rounded Avatars in Header */
        /* Target the avatar image specific container if possible, or just general images in top block */
        /* Since we removed the specific ID, we'll assume general styling or target via layout context if needed. */
        /* For now, let's just make sure ALL images in the app have a slight radius for consistency, or target broadly. */
        img {
            border-radius: 8px;
        }

        /* Common Button Styling for Triage Tools */
        div[data-testid="column"] button {
             width: 100%;
             border-radius: 6px;
             font-weight: 600;
        }
        
        /* NASA-TLX Slider Styling */
        div[data-testid="stSlider"] label {
            font-weight: 600 !important;
            font-size: 1rem !important;
        }
        </style>
    """
    
    st.markdown(css_content, unsafe_allow_html=True)

def render_patient_info(patient):
    """Renders just the text info for the patient (Name, Scenario, Info)."""
    # 1. Name (Top, Large)
    st.markdown(f"## {patient.get('Patient_Name', 'Unknown')}")
    
    # 2. Scenario (Bottom) - Removed ID
    st.markdown(f"**Scenario:** {patient['Scenario']}")
    
    visible_text = patient.get("Visible_Text")
    if pd.isna(visible_text) or visible_text is None:
        visible_text = "No visible findings recorded."
    st.info(visible_text)

def render_patient_avatar(patient):
    """Renders just the patient avatar image."""
    avatar_file = patient.get("Avatar_File", "default.png")
    if pd.isna(avatar_file):
        avatar_file = "default.png"
    image = load_image(avatar_file)
    st.image(image, use_container_width=True)

# render_patient_header was refactored into render_patient_info and render_patient_avatar



def render_action_buttons(patient, config_df):
    """Renders the investigation buttons in a 2-column grid with inline findings."""
    
    # 1. Component-Specific CSS
    st.markdown("""
        <style>
        /* Tighten vertical spacing */
        div[data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
        
        /* Category Header Base */
        .category-header {
            font-weight: 800;
            font-size: 1.1rem;
            color: #2c3e50;
            background-color: #f8f9fa;
            padding: 8px 12px;
            border-radius: 6px;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            border-left: 6px solid #ccc; /* Default */
        }
        
        /* Color Accents */
        .cat-header-A { border-left-color: #3498db !important; background-color: #ebf5fb !important; } /* Blue */
        .cat-header-B { border-left-color: #00bcd4 !important; background-color: #e0f7fa !important; } /* Cyan */
        .cat-header-C { border-left-color: #e74c3c !important; background-color: #fdedec !important; } /* Red */
        .cat-header-D { border-left-color: #e67e22 !important; background-color: #fdf2e9 !important; } /* Orange */
        .cat-header-E { border-left-color: #f1c40f !important; background-color: #fef9e7 !important; } /* Yellow */

        /* First header in a column shouldn't have huge top margin */
        div[data-testid="column"] > div > div:first-child .category-header {
            margin-top: 0rem;
        }

        /* Button Spacing */
        div.row-widget.stButton {
            margin-bottom: 0.2rem !important;
            padding-bottom: 0.0rem !important;
        }
        
        /* Inline Finding Box */
        .inline-finding {
            background-color: #f8f9fa;
            padding: 8px 12px;
            border-radius: 4px;
            border-left: 5px solid #2ecc71; /* Green success */
            margin-bottom: 0.4rem;
            font-size: 0.95rem;
            color: #1f1f1f;
            line-height: 1.3;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)

    # Get current tool to filter actions
    tool_id = st.session_state.get("tool_id", "ATS")
    valid_actions = config_df[config_df['Valid_Tools'].str.contains(tool_id, na=False)]

    labels = {
        'A': 'Airway', 
        'B': 'Breathing', 
        'C': 'Circulation', 
        'D': 'Disability', 
        'E': 'Exposure & History'
    }

    # Consolidated Container for the Grid
    with st.container():
        # Split into 3 columns
        col1, col2, col3 = st.columns(3, gap="small")
        
        # Define Cat -> Col mapping
        # Col 1: A, B
        # Col 2: C
        # Col 3: D, E
        col_map = {
            'A': col1, 'B': col1,
            'C': col2, 
            'D': col3, 'E': col3
        }
        
        for cat in ['A', 'B', 'C', 'D', 'E']:
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

            # Render in the assigned column
            with col_map[cat]:
                # Apply specific class based on category
                st.markdown(f"<div class='category-header cat-header-{cat}'>{labels[cat]}</div>", unsafe_allow_html=True)
                for _, row in pd.DataFrame(visible_buttons).iterrows():
                    _render_inline_action(row, patient)

def _render_inline_action(row, patient):
    """Renders button OR inline text if revealed."""
    key = row['Action_Key']
    label = row['Button_Label']
    cost = row['Cost_ms']
    
    # Label cleanup
    for prefix in ["Airway:", "Breathing:", "Circulation:", "Disability:"]:
        if label.startswith(prefix):
            label = label[len(prefix):].strip()
    label = label.strip()
    
    is_revealed = key in st.session_state.revealed_actions
    
    if is_revealed:
        # Render Text Result IN PLACE
        text = get_investigation_result(patient, key)
        st.markdown(f"<div class='inline-finding'><strong>{label}:</strong> {text}</div>", unsafe_allow_html=True)
    else:
        # Render Button
        if st.button(label, key=f"btn_{key}", use_container_width=True):
            st.session_state.revealed_actions.add(key)
            st.session_state.accumulated_cost_ms += cost
            log_event(event_type="reveal", action_key=key)
            save_session_state()
            st.rerun()

def render_triage_tools(tools_df, tool_id):
    """Renders the triage decision buttons in a compact grid."""
    st.markdown("#### Decision")

    # Filter tools by the selected Tool_ID
    my_tools = tools_df[tools_df["Tool_ID"] == tool_id]

    # Grid Layout (2 cols)
    cols = st.columns(2, gap="small")

    for i, (_, row) in enumerate(my_tools.iterrows()):
        label = row['Button_Label']
        normalized = row['Normalized_Value']
        
        emoji_map = {
            "Red": "🔴", "Yellow": "🟡", "Green": "🟢",
            "Black": "⚫", "White": "⚪", "Blue": "🔵", "Orange": "🟠"
        }
        btn_label = f"{emoji_map.get(normalized, '')} {label}"
        
        # Alternate columns
        with cols[i % 2]:
            if st.button(btn_label, key=f"decision_{i}", use_container_width=True):
                # Log decision
                log_event(event_type="decision", action_key="triage_decision",
                          decision_raw=label, decision_normalized=normalized)

                st.session_state.last_decision = "made"
                save_session_state()
                st.rerun()

def render_washout(duration_seconds=15):
    """Renders the washout screen with a countdown."""
    placeholder = st.empty()

    # Log start
    log_event(event_type="washout_start")
    
    # Scroll to Top Hack
    st.components.v1.html(
        "<script>window.parent.document.querySelector('section.main').scrollTo(0, 0);</script>",
        height=0
    )

    # CSS for Pale Blue Background and Large Text
    st.markdown("""
        <style>
        .washout-container {
            background-color: #e6f3ff;
            padding: 50px;
            border-radius: 10px;
            text-align: center;
            height: 80vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .washout-title {
            color: #2c3e50;
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .washout-timer {
            color: #e74c3c;
            font-size: 5rem;
            font-weight: 800;
        }
        .washout-text {
            color: #34495e;
            font-size: 2rem;
            margin-top: 30px;
        }
        </style>
    """, unsafe_allow_html=True)

    for i in range(duration_seconds, 0, -1):
        placeholder.markdown(f"""
        <div class="washout-container">
            <div class="washout-title">🛑 WASHOUT PERIOD</div>
            <div class="washout-timer">{i}</div>
            <div class="washout-text">Take a deep breath...</div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1)

    log_event(event_type="washout_complete")
    placeholder.empty()

def render_nasa_tlx():
    """Renders the NASA-TLX survey form."""
    st.title("🧠 NASA-TLX: Workload Assessment")
    st.markdown("### Please rate your experience during the previous scenario.")
    
    with st.form("nasa_tlx_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Mental Demand")
            m_demand = st.slider("How mentally demanding was the task?", 0, 100, 50, key="nasa_m")
            
            st.markdown("#### Physical Demand")
            p_demand = st.slider("How physically demanding was the task?", 0, 100, 50, key="nasa_p")
            
            st.markdown("#### Temporal Demand")
            t_demand = st.slider("How hurried or rushed was the pace??", 0, 100, 50, key="nasa_t")

        with col2:
            st.markdown("#### Performance")
            # Note: Standard NASA-TLX Performance is usually "How SUCCESSFUL were you?" (0=Perfect, 100=Failure) OR (0=Failure, 100=Perfect).
            # The user specified: "0 — Perfect performance, 100 — Very poor performance (Note: this scale is intentionally reversed)"
            perf = st.slider("How successful do you think you were? (0=Perfect, 100=Poor)", 0, 100, 50, key="nasa_perf")
            
            st.markdown("#### Effort")
            effort = st.slider("How hard did you have to work?", 0, 100, 50, key="nasa_eff")
            
            st.markdown("#### Frustration")
            frust = st.slider("How insecure, discouraged, irritated, stressed, and annoyed were you?", 0, 100, 50, key="nasa_frust")
            
        st.divider()
        st.markdown("#### Comments")
        comments = st.text_area("Was there anything specific that made the task easier or harder?", key="nasa_comments")
        
        submitted = st.form_submit_button("Submit Assessment", type="primary")
        
        if submitted:
            # Calculate Raw Score (Mean)
            raw_score = sum([m_demand, p_demand, t_demand, perf, effort, frust]) / 6.0
            
            data = {
                "nasa_mental": m_demand,
                "nasa_physical": p_demand,
                "nasa_temporal": t_demand,
                "nasa_performance": perf, 
                "nasa_effort": effort,
                "nasa_frustration": frust,
                "nasa_raw_score": round(raw_score, 2),
                "comments": comments
            }
            
            log_nasa_tlx(data)
            
            st.session_state.nasa_tlx_active = False
            # Transition to Washout logic is handled in app.py after this flag clears
            save_session_state()
            st.rerun()
