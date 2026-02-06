import pandas as pd

filepath = "config/study_content_pack.xlsx"
try:
    xls = pd.ExcelFile(filepath)
    df_config = pd.read_excel(xls, "Config")
    df_patients = pd.read_excel(xls, "Patients")

    print("Config Action Keys:", df_config["Action_Key"].tolist())
    print("Patients Columns:", df_patients.columns.tolist())

    keys = df_config["Action_Key"].tolist()
    cols = df_patients.columns.tolist()

    for key in keys:
        if key == "visual": continue
        text_col = f"{key}_Text"
        if text_col not in cols:
            print(f"MISSING: {text_col}")
        else:
            print(f"FOUND: {text_col}")

except Exception as e:
    print(e)
