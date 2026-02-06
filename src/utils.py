import pandas as pd
import hashlib
import os
import streamlit as st

def calculate_hash(filepath):
    """Calculates SHA-256 hash of the file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read and update hash string in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_content_pack(filepath):
    """Loads the Excel content pack into a dictionary of DataFrames."""
    if not os.path.exists(filepath):
        st.error(f"Content pack not found at {filepath}")
        st.stop()

    xls = pd.ExcelFile(filepath)
    sheets = {}
    for sheet_name in ["Config", "Tools", "Patients"]:
        if sheet_name not in xls.sheet_names:
            st.error(f"Missing sheet: {sheet_name} in content pack.")
            st.stop()
        sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)

    return sheets

def validate_content_pack(sheets):
    """Validates the content pack structure and data."""
    # 1. Validate Config Tab
    required_config_cols = {"Action_Key", "Button_Label", "Cost_ms"}
    if not required_config_cols.issubset(sheets["Config"].columns):
        st.error(f"Config tab missing columns. Required: {required_config_cols}")
        st.stop()

    # 2. Validate Tools Tab
    required_tools_cols = {"Tool_ID", "Button_Label", "Normalized_Value"}
    if not required_tools_cols.issubset(sheets["Tools"].columns):
        st.error(f"Tools tab missing columns. Required: {required_tools_cols}")
        st.stop()
    allowed_colors = {"Red", "Yellow", "Green", "Black", "White", "Blue", "Orange"}
    tool_colors = set(sheets["Tools"]["Normalized_Value"].dropna().unique())
    invalid_colors = tool_colors - allowed_colors
    if invalid_colors:
        st.error(f"Tools tab has invalid Normalized_Value entries: {invalid_colors}. Allowed: {allowed_colors}")
        st.stop()

    # 3. Validate Patients Tab
    # 3. Validate Patients Tab
    required_patient_cols = {"ID", "Scenario", "Is_Tutorial", "Patient_Name"}
    if not required_patient_cols.issubset(sheets["Patients"].columns):
        st.error(f"Patients tab missing columns. Required: {required_patient_cols}")
        st.stop()
    return True
