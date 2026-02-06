# Developer Instructions

## Prerequisites
- Python 3.9+
- pip

## Setup
From the repo root `c:\Users\warou\Code\3-Triage-Evaluation-study`.

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run The App
```powershell
streamlit run app.py
```

Alternate (Windows):
```powershell
.\run_app.bat
```

The app will open at `http://localhost:8501`.

## Resume A Session
- The app sets a URL query parameter `sid` when it starts.
- Refreshing the page should keep `sid` and resume the session automatically.
- To resume from another browser or machine, open the app URL with `?sid=<session_id>`.
- Session checkpoints are stored in `data_out/session_{session_id}.json`.

## Common Commands
Validate content pack and queue generation:
```powershell
python verify_logic.py
```

Check for required column `Patient_Name`:
```powershell
python check_col.py
```

List action keys and missing `{Action_Key}_Text` columns:
```powershell
python debug_excel.py
```

Add a missing `tourniquet_Text` column to the Patients sheet:
```powershell
python fix_excel.py
```

List logs and sessions:
```powershell
Get-ChildItem data_out
```

## Notes
- Logs are appended to `data_out/logs_{session_id}_{timestamp}.csv`.
- Deleting a session requires deleting both the CSV log and the JSON session file.
