# 1. Ten Second Triage (TST) Logic Flow
*Focus: Observable, binary decisions for rapid clearance.*

| Node | Human Decision / Input | Outcome: YES | Outcome: NO |
| :--- | :--- | :--- | :--- |
| **1. Mobility** | Is the patient walking? | **P3 (Green)** $\rightarrow$ END | Proceed to Node 2 |
| **2. Hemorrhage** | Is there major external bleeding? | **P1 (Red)** $\rightarrow$ END | Proceed to Node 3 |
| **3. Perfusion** | Is the patient talking? | Proceed to Node 3a | Proceed to Node 4 |
| **3a. Anatomy** | Penetrating injury to "Deadly Box"? | **P1 (Red)** $\rightarrow$ END | **P2 (Yellow)** $\rightarrow$ END |
| **4. Airway** | Breathing after airway maneuver? | **P1 (Red)** $\rightarrow$ END | **Dead (Black)** $\rightarrow$ END |

---

## 2. SMART Triage (Sieve) Logic Flow
*Focus: Physiological thresholds and measured clinical signs.*

| Node | Human Decision / Input | Outcome: YES | Outcome: NO |
| :--- | :--- | :--- | :--- |
| **1. Mobility** | Is the patient walking? | **P3 (Green)** $\rightarrow$ END | Proceed to Node 2 |
| **2. Airway** | Is the patient breathing? | Proceed to Node 3 | **Perform Manoeuvre** $\rightarrow$ Node 2a |
| **2a. Reassess** | Breathing after airway maneuver? | Proceed to Node 3 | **Dead (Black)** $\rightarrow$ END |
| **3. Resp Rate** | Is RR $< 10$ or $> 30$? | **P1 (Red)** $\rightarrow$ END | Proceed to Node 4 |
| **4. Circulation** | Cap Refill $> 2$s OR HR $> 120$? | **P1 (Red)** $\rightarrow$ END | **P2 (Yellow)** $\rightarrow$ END |

---

## 3. Step-by-Step Comparison: Similarities & Differences

### Key Similarities
* **The "First Filter":** Both algorithms use **Walking** as the immediate exit to P3 (Green) to clear the scene of the least injured.
* **The "Finality":** Both require a manual **Airway Maneuver** by the human before the app/simulation allows a "Dead (Black)" disposition.
* **Output Uniformity:** Both result in the same four standardized priority colors (Red, Yellow, Green, Black).

### Key Differences in Steps

| Feature | Ten Second Triage (TST) | SMART (Sieve) |
| :--- | :--- | :--- |
| **Step 2 Priority** | **Bleeding:** Immediate stop for hemorrhage. | **Breathing:** Immediate check for apnea. |
| **Decision Logic** | **Binary:** "Are they talking?" (Yes/No). | **Quantitative:** "What is the RR?" (Numerical). |
| **Injury Context** | **Anatomical:** Checks for "Deadly Box" wounds. | **Physiological:** Ignores wound site, looks at vitals. |
| **App Complexity** | **Low:** 4-5 taps, no typing/scrolling. | **Moderate:** Requires numeric input or range selection. |
| **Clinical Effort** | **Minimal:** Can be done from 2 meters away. | **High:** Requires touching patient (Pulse/Cap Refill). |

---

## 4. Final Disposition & "Action" Options
In your simulation, when the human reaches an **"END"** node, the app should offer these disposition/action tags for data capture:

* **P1 (Red):** Immediate Intervention (Tourniquet, Airway, Needle Decompression).
* **P2 (Yellow):** Urgent Transfer (Secondary survey, monitored holding).
* **P3 (Green):** Delayed Care (Self-treatment, redirection to holding area).
* **Dead (Black):** Recovery (Move to temporary mortuary).
