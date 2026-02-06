import pandas as pd

filepath = "config/study_content_pack.xlsx"
try:
    xls = pd.ExcelFile(filepath)
    df_patients = pd.read_excel(xls, "Patients")
    
    if "Patient_Name" in df_patients.columns:
        print("FOUND: Patient_Name")
    else:
        print("MISSING: Patient_Name")
        
except Exception as e:
    print(e)
