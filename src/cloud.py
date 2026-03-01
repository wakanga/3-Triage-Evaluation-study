import streamlit as st
import gspread
import pandas as pd

@st.cache_resource
def get_gspread_client():
    """Returns a cached gspread client using Streamlit secrets."""
    try:
        creds_dict = st.secrets["gcp_service_account"]
        # gspread supports service_account_from_dict
        client = gspread.service_account_from_dict(creds_dict)
        return client
    except Exception as e:
        st.error(f"Failed to authenticate with Google Sheets: {e}")
        return None

@st.cache_data(ttl=600)
def get_available_sheets():
    """Returns a list of all Google Sheets accessible by the service account."""
    client = get_gspread_client()
    if not client:
        return []
    
    try:
        sheets = client.openall()
        # Filter logic if necessary
        return [sheet.title for sheet in sheets]
    except Exception as e:
        st.error(f"Error fetching sheets: {e}")
        return []

@st.cache_resource(ttl=3600)
def get_spreadsheet(sheet_name):
    """Caches the spreadsheet object to prevent duplicate API discovery calls."""
    client = get_gspread_client()
    if not client:
        return None
    try:
        return client.open(sheet_name)
    except Exception as e:
        st.error(f"Could not open sheet '{sheet_name}'. Error: {e}")
        return None

@st.cache_data(ttl=600)
def fetch_gsheet_data(sheet_name):
    """Fetches Config, Tools, and Patients tabs from a Google Sheet."""
    spreadsheet = get_spreadsheet(sheet_name)
    if not spreadsheet:
        return None

    sheets_data = {}
    required_tabs = ["Config", "Tools", "Patients"]
    
    for tab in required_tabs:
        try:
            worksheet = spreadsheet.worksheet(tab)
            data = worksheet.get_all_records()
            sheets_data[tab] = pd.DataFrame(data)
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Missing required tab '{tab}' in '{sheet_name}'.")
            return None
        except Exception as e:
            st.error(f"Error reading tab '{tab}': {e}")
            return None

    return sheets_data

def append_triage_log(sheet_name, data_row):
    """
    Appends a log row to the 'Triage_Logs' worksheet.
    data_row should be formatted like: [Timestamp, PatientID, TriageCategory, ClinicianNotes]
    """
    spreadsheet = get_spreadsheet(sheet_name)
    if not spreadsheet:
        return

    try:
        worksheet = spreadsheet.worksheet("Triage_Logs")
    except gspread.exceptions.WorksheetNotFound:
        # Create it if it doesn't exist
        try:
            worksheet = spreadsheet.add_worksheet(title="Triage_Logs", rows="1000", cols="3")
            header = ["Timestamp", "PatientID", "TriageCategory"]
            worksheet.append_row(header)
        except Exception as create_err:
            print(f"Failed to create Triage_Logs tab: {create_err}")
            return

    try:
        worksheet.append_row(data_row)
    except Exception as e:
        print(f"Failed to append log row: {e}")
