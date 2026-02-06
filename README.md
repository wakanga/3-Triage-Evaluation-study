# Cognitive Load Triage Evaluation Platform

A Streamlit-based research app that simulates mass-casualty triage under "fog of war" conditions. It compares ATS, SMART, and 10-Second Triage by capturing decision speed (real time) and information cost (simulated clinical time).

## Highlights
- Excel-driven content pack for actions, tools, and patients.
- Fog-of-war reveal mechanics with time penalties.
- Washout period enforcement between scenario blocks.
- Append-only CSV logging with content-pack hashing.
- Session resume after refresh via a URL `sid` query parameter.

## Tech Stack
- Python 3.9+
- Streamlit
- Pandas, OpenPyXL, Pillow

## Repo Layout

```text
app.py
requirements.txt
assets/
  img/                # Patient avatar images (default.png required)
config/
  study_content_pack.xlsx
data_out/
  logs_{session_id}_{timestamp}.csv
  session_{session_id}.json
src/
  engine.py           # Session, timing, logging, resume
  components.py       # UI elements
  utils.py            # Excel load, hashing, validation
```

## Study Content Pack
File: `config/study_content_pack.xlsx`

### Config tab
Columns: `Action_Key`, `Button_Label`, `Cost_ms`
- `visual` is implicit and should have cost `0`.
- Each `Action_Key` (except `visual`) must have a matching `{Action_Key}_Text` column in Patients.

### Tools tab
Columns: `Tool_ID`, `Button_Label`, `Normalized_Value`
- `Normalized_Value` must be one of `Red`, `Yellow`, `Green`, `Black`.
- Each `Tool_ID` defines the decision buttons shown to the participant.

### Patients tab
Required columns:
- `ID`, `Scenario`, `Is_Tutorial`, `Visible_Text`, `Gold_Standard_Normalized`, `Patient_Name`
Optional columns:
- `Avatar_File` (filename in `assets/img`; missing values fall back to `default.png`)
- `{Action_Key}_Text` for each action in Config (except `visual`)

Rendering rules:
- Action buttons only render when the matching `{Action_Key}_Text` cell is not empty.
- `Gold_Standard_Normalized` must be one of `Red`, `Yellow`, `Green`, `Black`.

## Runtime Flow
1. Onboarding collects role, experience, fatigue, and assigned tool.
2. Tutorial patients run first.
3. Scenario blocks run in randomized order with a strict 15-second washout between blocks.
4. Completion shows a unique completion code.
5. Withdraw deletes the CSV log and session checkpoint.

## Data Outputs
- CSV log: `data_out/logs_{session_id}_{timestamp}.csv`
- Session checkpoint: `data_out/session_{session_id}.json`

Log columns:
- `timestamp_utc` (currently local system time, no timezone)
- `app_version`
- `content_pack_hash`
- `session_id`
- `participant_role`
- `tool_id`
- `scenario_type`
- `patient_id`
- `event_type` (`card_start`, `reveal`, `decision`, `washout_start`, `washout_complete`)
- `action_key`
- `decision_raw`
- `decision_normalized`
- `t_real_ms`
- `t_sim_ms`
- `gold_standard`
- `is_critical_fail`
- `is_over_triage`

## Session Resume
The app sets a URL query parameter `sid` on first load. Refreshing the page preserves `sid` and reloads the session from `data_out/session_{session_id}.json`. If the content pack hash changes, the app starts a new session.

## Validation Rules
The app validates the content pack on startup:
- All required sheets and columns exist.
- `_Text` columns exist for each `Action_Key` (except `visual`).
- `Normalized_Value` and `Gold_Standard_Normalized` values are only `Red`, `Yellow`, `Green`, `Black`.
- `assets/img/default.png` exists.

## Developer Docs
See `DEV_INSTRUCTIONS.md` for setup, running the app, and common terminal commands.
