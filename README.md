# Standardised Triage Evaluation Platform (STEP)

A Streamlit-based research app that simulates mass-casualty triage under "fog of war" conditions. It compares triage systems (e.g., SMART, TST) by capturing decision speed (real time) and information cost (simulated clinical time).

> **See [FEATURES.md](FEATURES.md)** for a detailed exposé of current capabilities and a workspace for planning new features.

## Highlights
- **Fog of War**: Clinical findings are hidden until "purchased" with simulated time.
- **Inline Action Grid**: Categorized assessment actions (A-B-C-D-E) are integrated into a compact, responsive grid.
- **Sticky Sidebar**: Patient information and clinical findings remain visible while scrolling through actions.
- **Excel-Driven Engine**: Fully configurable scenarios, actions, and tools via `study_content_pack.xlsx`.
- **Washout Period**: Enforced 40-second breaks between scenario blocks featuring guided box breathing to reset cognitive load.
- **Session Resume**: Append-only logging with unique session IDs and URL-based resume (`?sid=...`).

## Tech Stack
- Python 3.9+
- Streamlit
- Pandas, OpenPyXL, Pillow

## Repo Layout

```text
app.py                # Main entry point
requirements.txt
assets/
  img/                # Patient avatar images (default.png required)
config/
  study_content_pack.xlsx
data_out/
  logs_{session_id}_{timestamp}.csv
  session_{session_id}.json
src/
  engine.py           # Session state, timing logic, logging, resume
  components.py       # UI elements (Action Grid, Patient Header, Findings)
  utils.py            # Excel ingestion, hashing, validation
```

## Study Content Pack
File: `config/study_content_pack.xlsx`

### Config tab
Defines the available investigation actions.
Columns:
- `Action_Key`: Unique identifier for the action (e.g., `sp02`, `airway`).
- `Button_Label`: Text displayed on the button.
- `Cost_ms`: Simulated time cost in milliseconds.
- `Category`: Grouping for the UI (Must be: `A`, `B`, `C`, `D`, or `E`).
- `Valid_Tools`: Comma-separated list of Tool IDs that allow this action (e.g., `SMART,TST`).

### Tools tab
Defines the triage algorithms/tools available.
Columns:
- `Tool_ID`: Unique ID (e.g., `SMART`, `TST`).
- `Button_Label`: Text for the final decision button (e.g., `P1 - Immediate`).
- `Normalized_Value`: Mapped value for scoring. Allowed: `Red`, `Yellow`, `Green`, `Black`, `White`, `Blue`, `Orange`.

### Patients tab
Defines the scenario sequence and patient data.
Required columns:
- `ID`: Unique patient ID.
- `Scenario`: Name of the scenario block.
- `Is_Practice`: `TRUE` or `FALSE`. Indicates a practice case (not scored/logged).
- `Patient_Name`: Display name.
- `Visible_Text`: Initial text shown (e.g., "Patient is moaning...").

Optional columns:
- `Avatar_File`: Filename in `assets/img` (default: `default.png`).
- `{Action_Key}_Text`: The result text for each action defined in Config.
  - If a cell is empty or contains "not applicable", the button is hidden for that patient.

## Runtime Flow
1. **Onboarding**: Participant enters Role, Experience Band, Fatigue Status, Prior Triage Training, and receives an assigned Triage Tool. Also includes consent and pre-readiness sliders.
2. **Practice**: Practice patients to familiarize the user with the interface (results are not logged).
3. **Scenarios**: Blocks of test patients presented in randomized order.
4. **Washout**: A 40-second mandatory box-breathing break between blocks.
5. **Post-Simulation**: Post-scenario feedback sliders.
6. **Completion**: Generates a unique completion code.

## Data Outputs
- **CSV Log**: `data_out/logs_{session_id}_{timestamp}.csv`
  - Captures every click (reveal, hide, decision) with real time (`t_real_ms`) and simulated time (`t_sim_ms`).
- **Session State**: `data_out/session_{session_id}.json`
  - JSON dump for resuming interrupted sessions.

## Validation
The app runs `src/utils.py` and `verify_logic.py` to ensure:
- All required columns exist in the Excel pack.
- Every `Action_Key` in Config has a corresponding `_Text` column in Patients.
- Valid RGB/Black standard colors are used.

## Developer Docs
See `DEV_INSTRUCTIONS.md` for setup, virtual environment creation, and running the app locally.
