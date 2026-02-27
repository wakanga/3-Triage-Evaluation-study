# App Features & Roadmap

This document serves as an exposé of the current capabilities of the Standardised Triage Evaluation Platform (STEP).

## Current Features (Exposé)

### Core Simulation Engine
*   **"Fog of War" Mechanics**: Clinical findings are initially hidden and must be "purchased" with simulated clinical time, mimicking the uncertainty and time pressure of real-world triage.
*   **Excel-Driven Configuration**: The entire study (scenarios, patient data, available actions, and triage tools) is dynamically loaded from a single, fully configurable `study_content_pack.xlsx` file. This allows researchers to modify the study without altering code. 
There is functionality for the excel to load from a Google Spreadsheet which can be updated in real time and also a functionality of picking different spreadsheets (in .xlsx) from the local machine.
*   **Dual-Timer System**: The app concurrently tracks both real-world time (`t_real_ms`) and simulated clinical time (`t_sim_ms`) for every action taken.

### User Interface & Experience
*   **Inline Action Grid**: A highly compact, responsive grid layout for assessment actions, categorized logically by standard approaches (e.g., A-B-C-D-E).
*   **Sticky Sidebar / Floating Layout**: Critical patient information and the action summary remain fixed and visible while the user scrolls through the available investigation options, reducing cognitive friction.
*   **Dynamic Visuals**: Supports patient avatar images and provides instant text based feedback when actions are selected or deselected.
*   **Washout Periods**: Enforces a mandatory timed break (e.g., 15 seconds) between scenario blocks to reset the participant's cognitive load before the next set of patients.

### Data Collection & Research Tools
*   **Comprehensive Session Logging**: Append-only CSV logging captures every click, reveal, hide, and final decision alongside associated timestamp data.
*   **Session Resume**: Interrupted sessions can be reliably resumed using URL parameters (`?sid=...`) and JSON-backed session state recovery.
*   **NASA-TLX Integration**: Built-in support for capturing subjective cognitive load assessments from participants.
*   **Automated Validation**: Built-in validation checks structural integrity, missing columns, and logical links across the Excel content pack to warn researchers of config errors before deployment.

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
    *   `t_real_ms`, `t_sim_ms`
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
> **Agent Instruction:** When instructed to add or investigate a new feature, refer to this document to log the plan, requirements, and progress.
