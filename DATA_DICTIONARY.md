# Data Dictionary & Excel Schema Hub (Pilot Phase)

This document defines the exact expected structure, sheets, and columns for the `study_content_pack.xlsx` file. It has been streamlined specifically for the SMART vs. TST feasibility pilot.

---

## 1. Sheet: `Config`
Defines the clinical actions available to the user and their associated time costs.
*(Note: As per previous structure, this actually acts as the Actions list).*

| Column Name | Description |
| :--- | :--- |
| `Action_Key` | Unique code for the action (e.g., `airway_obs`). Must match the dynamic columns in the `Patients` sheet. |
| `Button_Label` | The text displayed on the UI button. |
| `Category` | Groups the actions in the UI (e.g., `A`, `B`, `C`, `D`, `E`). |
| `Cost_ms` | Simulated time penalty in milliseconds for clicking this action. |
| `Valid_Tools` | Comma-separated list of tools that allow this action (`SMART,TST`). |

---

## 2. Sheet: `Tools`
Defines the standard triage categories shown to the user based on their assigned tool.

| Column Name | Description |
| :--- | :--- |
| `Tool_ID` | Identifies the tool (`SMART` or `TST`). |
| `Button_Label` | The raw text shown on the button (e.g., `P1 - Immediate`). |
| `Normalized_Value` | Standardized category for analytics (`Red`, `Yellow`, `Green`, `Dead`). |

---

## 3. Sheet: `Patients`
The master list of distinct simulated patients and their clinical findings. Over-engineered hospital-level metrics have been removed to keep the pilot out-of-hospital focused.

### Core Tracking & Metadata
| Column Name | Description |
| :--- | :--- |
| `ID` | Unique patient identifier (e.g., `ent_01`). |
| `Patient_Name` | UI Display Name. |
| `Scenario` | Overarching event (e.g., `Entrapment`). Groups patients together. |
| `Is_Practice` | Flags cases as practice (e.g. `TRUE`). Excludes them from scoring/analysis. |
| `Visible_Text` | The initial vignette shown to the user automatically. |
| `Avatar_File` | Image filename in `assets/img`. |

### Reference Standards (Consensus)
| Column Name | Description |
| :--- | :--- |
| `Ref_SMART` | The consensus-derived category for SMART. (`Red`/`Yellow`/`Green`/`Dead`). |
| `Ref_Standard_TST` | The consensus-derived category for TST. (`Red`/`Yellow`/`Green`/`Dead`). |

### Action Results (Dynamic Columns matching `Action_Key`)
*These exist so that when a user clicks `Action_Key`, the app looks up the corresponding `[Action_Key]_Text` column to reveal.*

| Column Name | Description |
| :--- | :--- |
| `airway_obs_Text` | Essential for SMART/TST. |
| `airway_man_Text` | Essential for SMART/TST. |
| `rr_Text` | Essential for SMART (Resp Rate). |
| `pulse_rad_Text` | Essential for SMART. |
| `pulse_rate_Text` | Important context. |
| `cap_refill_Text` | Essential for SMART. |
| `hemorrhage_Text` | Key intervention/feature in TST/SMART. |
| `avpu_Text` | Base neurological assessment. |
| `walk_Text` | The very first step of TST. Essential. |
