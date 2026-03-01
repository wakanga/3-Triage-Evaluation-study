# App Features & Roadmap

This document serves as an exposé of the current capabilities of the Standardised Triage Evaluation Platform (STEP).

## Current Features (Exposé)

### Core Simulation Engine
*   **"Fog of War" Mechanics**: Clinical findings are initially hidden and must be "purchased" with simulated clinical time, mimicking the uncertainty and time pressure of real-world triage.
*   **Dynamic Data Sources & Configuration**: The entire study (scenarios, patient data, available actions, and triage tools) is dynamically loaded. The app provides an Admin Toggle to select between three modes:
    *   **Mode A: In App (.xlsx)**: Automatically scans the `config/` folder and provides a dropdown to load any valid `.xlsx` content pack.
    *   **Mode B: Upload (.xlsx)**: Allows users to manually upload a local `.xlsx` content pack.
    *   **Mode C: Cloud Upload**: Dynamically fetch study data from Google Sheets, authenticated securely via Streamlit Secrets.
*   **Dual-Timer System**: The app concurrently tracks action latency with `t_run_ms` (time elapsed since the start of the current scenario block) and simulated clinical time (`t_sim_ms`) for every action taken.

### User Interface & Experience
*   **Inline Action Grid**: A highly compact, responsive grid layout for assessment actions, categorized logically by standard approaches (e.g., A-B-C-D-E). Category labels are integrated directly into the button grid structure for maximum compactness.
*   **Sticky Sidebar / Floating Layout**: Critical patient information and the action summary remain fixed and visible while the user scrolls through the available investigation options, reducing cognitive friction. The layout ensures symmetrical, equal-height display of patient information and triage tool cards.
*   **Dynamic Visuals**: Supports patient avatar images and provides instant text based feedback when actions are selected or deselected. Triage decision buttons are dynamically styled with color-coded outlines.
*   **Washout Periods**: Enforces a mandatory timed break (40 seconds) featuring guided box breathing and a progress bar between scenario blocks to reset the participant's cognitive load before the next set of patients.

### Data Collection & Research Tools
*   **Comprehensive Session Logging**: Append-only CSV logging captures every click, reveal, hide, and final decision alongside associated timestamp data. This includes robust deviation calculations (overtriage/undertriage/correct) matched against predefined `Ref_SMART` and `Ref_Standard_TST` reference standards.
*   **Cloud Feedback Loop (Google Sheets)**: When operating in Mode C, final triage decisions (including optional Clinician Notes) are automatically appended in real-time to a `Triage_Logs` tab within the active Google Sheet.
*   **Explicit Data Source Selection**: Mode dropdowns require an explicit selection by the user to prevent accidental data loading.
*   **Session Resume**: Interrupted sessions can be reliably resumed using URL parameters (`?sid=...`) and JSON-backed session state recovery.
*   **NASA-TLX Integration**: Built-in support for capturing subjective cognitive load assessments from participants.
*   **Automated Validation**: Built-in validation checks structural integrity, missing columns, and logical links across the Excel content pack to warn researchers of config errors before deployment. The validation is flexible to accept alternative spelling variants for common fields.

---

## Current Features – Pilot Phase (SMART vs TST)

### 1. Study Arms
*   **Included:** SMART (Sieve-based) and 10-Second Triage (TST).
*   (ATS/NTS are excluded for this pilot phase).

### 2. Participant Onboarding
*   **Core Demographics:** Role, Experience Band, Prior triage training exposure, Fatigue (On shift Y/N).
*   **Ethics & Training:** Consent checkbox.
*   **Pre-Readiness:** 2 slider questions to gauge confidence and understanding before the simulation.

### 3. Practice Phase
*   **Design:** Configurable practice cases defined by the `Is_Practice` column in the Patient schema.
*   **Execution:** Data is not included in analysis. Counters are reset after practice.
*   **Transition:** Displays a clear statement: *"Practice cases complete. Simulation begins now."*

### 4. Simulation Phase
*   **Mechanics:** Visible description loads, actions revealed incrementally, continuous time tracking.
*   **Constraints:** No back button, no live feedback.
*   **Data Logging per patient:** 
    *   `tool_id`
    *   `decision_raw`, `decision_normalized`
    *   `error_type` (correct / overtriage / undertriage)
    *   `t_run_ms`, `t_sim_ms`
    *   `patient_sequence_order`

### 5. Scene-Level Metrics
*   **Calculations at end of scenario:**
    *   `scene_completion_time`
    *   `total_undertriage_count`, `total_overtriage_count`
    *   `mean_time_per_patient`

### 6. Post-Scenario Questions
*   **Cognitive Load:** 5 modified NASA-TLX sliders.
*   **Perception:** 3 post-perception sliders (improvement in understanding, preparedness, tool effectiveness) logged to a separate file.

### 7. Data Lock & Governance
*   **Validation:** Use a "Consensus-derived reference categorisation" mapping to determine correctness (e.g. `Ref_SMART` & `Ref_Standard_TST`).
*   **Freeze Protocol:** Lock fields, logging schema, tool definitions, and reference answers under a version stamp prior to recruitment.

---

## Data Outputs & Logging Streams

The app maintains several distinct data outputs for comprehensive analysis, separated by the type of event and where they are stored:

### 1. Local CSV Logs (Comprehensive)
Stored under `data_out/` on the local server/machine. These are generated regardless of the data source mode.
*   **`logs_{SESSION_ID}_{TIMESTAMP}.csv`**
    *   **Purpose**: The master event log for the simulation. Absolute "watch time" (`TIMESTAMP`) is anonymized by only existing in the filename.
    *   **Data Captured**: Every discrete action taken by the user (revealing a finding, deciding a triage category) complete with timestamps (`t_run_ms`, `t_sim_ms`), patient ID, scenario name, and deviation calculations (overtriage/undertriage).
*   **`nasa_tlx_logs.csv`**
    *   **Purpose**: Records subjective cognitive load assessments.
    *   **Data Captured**: Raw scores (1-100) across 6 workload domains and an aggregated score, tied to the specific scenario block just completed.
*   **`post_perception_logs.csv`**
    *   **Purpose**: End-of-study feedback.
    *   **Data Captured**: Participant ratings on their perceived improvement in understanding, preparedness, and tool effectiveness.

### 2. Cloud Logs (Google Sheets)
Stored directly in a worksheet named `Triage_Logs` within the currently active Google Sheet. This is **only** generated when the app is in **Mode C (Cloud Upload)**.
*   **`Triage_Logs` Worksheet**
    *   **Purpose**: A real-time, consolidated feedback loop for final decisions.
    *   **Data Captured**: Appends a highly distilled row per patient: `[Timestamp, PatientID, TriageCategory]`.

---

## Planned / Proposed Features

*Use this section as a workspace to describe new features you'd like me (the AI agent) to build. Just add your ideas below as bullet points or detailed descriptions!*

*   *(Example) Add a post-scenario debrief dashboard...*
*   *(Example) Integrate real-time multiplayer coordination...*

---
> **Agent Instruction:** When instructed to add or investigate a new feature, refer to this document to log the plan, requirements, and progress.
