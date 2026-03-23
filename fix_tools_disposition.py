import pandas as pd
import os

filepath = 'config/study_content_pack.xlsx'

# Read all sheets
sheets = pd.read_excel(filepath, sheet_name=None)

# New tools data
tools_data = [
    {"Tool_ID": "SMART", "Button_Label": "P1 (Red): Immediate Intervention (Tourniquet, Airway, Needle Decon)", "Normalized_Value": "Red"},
    {"Tool_ID": "SMART", "Button_Label": "P2 (Yellow): Urgent Transfer (Secondary survey, monitored holding)", "Normalized_Value": "Yellow"},
    {"Tool_ID": "SMART", "Button_Label": "P3 (Green): Delayed Care (Self-treatment, redirection to holding)", "Normalized_Value": "Green"},
    {"Tool_ID": "SMART", "Button_Label": "Dead (Black): Recovery (Move to temporary mortuary)", "Normalized_Value": "Black"},
    
    {"Tool_ID": "TST", "Button_Label": "P1 (Red): Immediate Intervention (Tourniquet, Airway, Needle Decon)", "Normalized_Value": "Red"},
    {"Tool_ID": "TST", "Button_Label": "P2 (Yellow): Urgent Transfer (Secondary survey, monitored holding)", "Normalized_Value": "Yellow"},
    {"Tool_ID": "TST", "Button_Label": "P3 (Green): Delayed Care (Self-treatment, redirection to holding)", "Normalized_Value": "Green"},
    {"Tool_ID": "TST", "Button_Label": "Dead (White): Recovery (Move to temporary mortuary)", "Normalized_Value": "White"},
]

# Update the Tools sheet
sheets['Tools'] = pd.DataFrame(tools_data)

# Write all sheets back
with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
    for sheet_name, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Updated config/study_content_pack.xlsx Tools sheet successfully.")
