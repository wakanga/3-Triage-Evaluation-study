
# PROJECT BLUEPRINT: The "Cognitive Load" Triage Evaluation Platform (Platinum Master)

## 1. Project Vision

**Objective:** To generate a policy paper evaluating the safety and efficiency of three triage systems (ATS, SMART, 10-Second Triage) in Mass Casualty Incidents.
**Core Mechanic:** A "Fog of War" card simulation measuring *Real Time* (decision speed) vs. *Simulated Clinical Time* (information cost).

## 2. Technical Stack & Architecture

* **Language:** Python 3.9+
* **Framework:** Streamlit (v1.28+)
* **Data Engine:** Pandas (ingests Excel "Study Content Pack").
* **Persistence:** Local Session State & Append-Only CSV logging.

### Folder Structure

```text
/triage_study_app
│
├── app.py                 # Main application entry point
├── requirements.txt       # streamlit, pandas, openpyxl, Pillow
│
├── assets/
│   └── img/               # Patient avatar images (ensure 'default.png' exists)
│
├── config/
│   └── study_content_pack.xlsx  # THE BRAIN: Patients, Rules, Costs, and Tool Definitions
│
├── data_out/              # Session logs
│   └── logs_{session_id}_{timestamp}.csv
│
└── src/
    ├── engine.py          # Time logic & State Persistence
    ├── components.py      # UI elements
    └── utils.py           # Excel loader, Hashing, & Validation

```

## 3. The "Study Content Pack" (Excel Architecture)

**File:** `config/study_content_pack.xlsx`

### **Tab 1: `Config` (The Rules)**

*Note: Costs are integer milliseconds.*
*Columns:* `Action_Key`, `Button_Label`, `Cost_ms`

| Action_Key | Button_Label | Cost_ms |
| --- | --- | --- |
| `visual` | (Implicit Visual Scan) | 0 |
| `walk` | Ask: "Can you walk?" | 2000 |
| `voice` | Ask: "Can you hear me?" | 2000 |
| `pulse` | Check Radial Pulse | 5000 |
| `rr` | Count Respiration | 8000 |
| `airway` | Jaw Thrust / Maneuver | 5000 |
| `tourniquet` | Apply Tourniquet | 15000 |

### **Tab 2: `Tools` (Explicit Mappings)**

*Defines exactly what buttons appear for each tool and how they map to analysis colors.*
*Columns:* `Tool_ID`, `Button_Label`, `Normalized_Value`

| Tool_ID | Button_Label | Normalized_Value |
| --- | --- | --- |
| ATS | Cat 1 (Immediate) | Red |
| ATS | Cat 2 (Imminent) | Red |
| ATS | Cat 3 (Urgent) | Yellow |
| ATS | Cat 4 (Semi-Urgent) | Green |
| ATS | Cat 5 (Non-Urgent) | Green |
| ATS | Dead | Black |
| SMART | Priority 1 (Red) | Red |
| SMART | Priority 2 (Yellow) | Yellow |
| ... | ... | ... |

### **Tab 3: `Patients` (The Content)**

*Columns:*

* **Metadata:** `ID`, `Scenario` (Entrapment/Violence), `Is_Tutorial` (TRUE/FALSE), `Avatar_File` (filename in assets/img).
* **Fog of War Data:** `Visible_Text`, `walk_Text`, `voice_Text`, `pulse_Text`, `rr_Text`, `airway_Text`.
* *Rule:* If the cell is empty (NaN), the button **must not render**. column names must match `{Action_Key}_Text`.


* **The Answer Key:** `Gold_Standard_Normalized` (Red/Yellow/Green/Black), `Hidden_ISS`, `Critical_Failure_Type`.

---

## 4. User Flow & Mechanics

### **Phase 1: Onboarding & Resilience**

* **Inputs:** Role, Years Exp, Fatigue Status ("On Shift?").
* **Session Resume:** The app must verify if a valid session exists in `st.session_state`. If a browser refresh occurs, reload the previous state (current patient index, shuffled lists) instead of restarting.
* **Hashing:** On startup, calculate an SHA-256 hash of `study_content_pack.xlsx`. This ensures every log file can be traced back to the exact version of the study logic used.

### **Phase 2: The Tutorial**

* Loads patients where `Is_Tutorial == TRUE`.
* Logs marked `is_practice = True`.

### **Phase 3: The Scenarios**

* **Behavior:**
* User clicks "Check Pulse".
* **Logic:** Check `revealed_actions`. If new, add to set and add `Cost_ms` to accumulator. (Idempotent).


* **Triage Decision:**
* User sees buttons defined in the **Tools** Excel tab for their assigned tool.
* **Log Event:** `decision_raw` (e.g., "Cat 1") and `decision_normalized` (e.g., "Red").
* **Move Next:** No back button.



### **Phase 4: Washout (Robust)**

* **Trigger:** Between Scenario A and B.
* **UI:** Blank screen with "Break - Next scenario in X seconds".
* **Logic:** Uses a `time.time()` loop with `st.empty()` to enforce the 15-second break even if the user tries to interact. Log `washout_start` and `washout_complete`.

### **Phase 5: Completion & Ethics**

* **Withdraw Button:** A small footer link "Withdraw & Delete Session". If clicked, abort execution and delete the session log file.
* **Completion Code:** Generate unique code `f"{session_id[-6:]}_{timestamp[-4:]}"`.

---

## 5. Data Logging Schema (The Output)

**Filename:** `data_out/logs_{session_id}_{timestamp}.csv` (Append-only).

| Column | Description |
| --- | --- |
| `timestamp_utc` | Exact time. |
| `app_version` | v1.0.0. |
| `content_pack_hash` | Hash of the Excel file (Audit Trail). |
| `session_id` | Unique UUID. |
| `participant_role` | e.g., "Paramedic". |
| `tool_id` | "ATS", "SMART", or "10S". |
| `scenario_type` | "Entrapment". |
| `patient_id` | "entrap_01". |
| `event_type` | `card_start`, `reveal`, `decision`, `washout_start`, `washout_complete`. |
| `action_key` | e.g., "pulse" or "triage_decision". |
| `decision_raw` | e.g., "Cat 1". |
| `decision_normalized` | Red/Yellow/Green/Black. |
| `t_real_ms` | `int((now - start).total_seconds() * 1000)` |
| `t_sim_ms` | `t_real_ms` + Accumulated Penalties. |
| `gold_standard` | Red/Yellow/Green/Black. |
| `is_critical_fail` | Boolean (True if Gold=Red and Decision!=Red). |
| `is_over_triage` | Boolean (True if Gold!=Red and Decision=Red). |

---

## 6. INSTRUCTION SET FOR THE AI CODER

*Copy/Paste this block to your agent.*

---

**ROLE:** Senior Python Developer (Streamlit Specialist).

**TASK:** Build a robust, research-grade Streamlit app for a triage study using an Excel-driven content engine.

**CRITICAL IMPLEMENTATION DETAILS:**

1. **Timing Math (CRITICAL):**
* Calculate real time as: `t_real_ms = int((datetime.now() - st.session_state.card_start_time).total_seconds() * 1000)`
* Do NOT use `.microseconds`.


2. **Excel Ingestion & Validation (The "Validator"):**
* Load `config/study_content_pack.xlsx`. Calculate its SHA-256 hash immediately for logging.
* **Validator Routine:** On startup, run a check:
* Are all required columns present?
* Do `_Text` columns in "Patients" match keys in "Config"?
* If validation fails, stop app and show error.


* **Tools Tab:** Load the specific button labels for each Tool ID (ATS, SMART, 10S) and their mapping to Normalized colors.


3. **Session Resilience:**
* Use `st.session_state` to store `patient_order`, `current_index`, and `shuffled_lists`.
* If the browser refreshes, the app must **Resume** from the current state, not restart.
* **Withdraw:** Add a footer button "Withdraw Study". If clicked, `os.remove` the current log file and show a "Session Cancelled" message.


4. **Logging Logic:**
* **Header:** Include `app_version` and `content_pack_hash` in every row.
* **Auto-Grading:** Log `is_critical_fail` (Under-triage of Red) and `is_over_triage` (Over-triage of non-Red) booleans.
* **Safety:** Use `open(filepath, 'a', newline='')`. Check `os.path.exists` to write header only once. Flush after every write.


5. **User Interface:**
* **Fog of War:** Only render action buttons if the corresponding cell in Excel is NOT empty/NaN.
* **Washout:** Enforce a strict 15-second timer between scenarios using `time.sleep` logic loop (or `st.empty` replacement) to prevent skipping.



**DELIVERABLE:** Generate `app.py`, `utils.py` (including the validator & hashing logic), `engine.py`, and the code to generate the `study_content_pack.xlsx` with the new **Tools** tab structure.

---
