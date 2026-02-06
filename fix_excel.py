import pandas as pd
import sys

filepath = "config/study_content_pack.xlsx"

try:
    print(f"Loading {filepath}...")
    xls = pd.ExcelFile(filepath)
    df_config = pd.read_excel(xls, "Config")
    df_tools = pd.read_excel(xls, "Tools")
    df_patients = pd.read_excel(xls, "Patients")

    if "tourniquet_Text" not in df_patients.columns:
        print("Adding 'tourniquet_Text' column...")
        # Add column with empty values
        df_patients["tourniquet_Text"] = "" 
        # Or None/NaN
        df_patients["tourniquet_Text"] = None
        
        # Save back
        print("Saving file...")
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df_config.to_excel(writer, sheet_name="Config", index=False)
            df_tools.to_excel(writer, sheet_name="Tools", index=False)
            df_patients.to_excel(writer, sheet_name="Patients", index=False)
        print("Success: File updated.")
    else:
        print("Column 'tourniquet_Text' already exists.")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
