import streamlit as st
import sys
import os

# Mock session_state
class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value

# Patch streamlit.session_state
st.session_state = MockSessionState()

# Add current dir to path
sys.path.append(os.getcwd())

from src import utils, engine

def run_verification():
    print("Beginning Verification...")
    
    # 1. Config Path
    content_path = "config/study_content_pack.xlsx"
    if not os.path.exists(content_path):
        print(f"FAIL: {content_path} not found.")
        return

    # 2. Hashing
    print("Testing Hashing...")
    try:
        h = utils.calculate_hash(content_path)
        print(f"Hash: {h}")
    except Exception as e:
        print(f"FAIL: Hashing failed - {e}")

    # 3. Loading
    print("Testing Loading...")
    try:
        sheets = utils.load_content_pack(content_path)
        print("Sheets loaded:", list(sheets.keys()))
    except Exception as e:
        print(f"FAIL: Loading failed - {e}")
        return

    # 4. Validation
    print("Testing Validation...")
    # Mock st.error and st.stop to catch them
    original_error = st.error
    original_stop = st.stop
    
    errors = []
    def mock_error(msg):
        print(f"VALIDATION ERROR: {msg}")
        errors.append(msg)
    
    def mock_stop():
        print("VALIDATION STOPPED")
        raise Exception("Streamlit Stopped")
        
    st.error = mock_error
    st.stop = mock_stop
    
    try:
        utils.validate_content_pack(sheets)
        print("Validation Passed.")
    except Exception as e:
        print(f"FAIL: Validation crashed or stopped - {e}")
        
    # Restore
    st.error = original_error
    st.stop = original_stop

    # 5. Engine / Queue Generation
    print("Testing Queue Generation...")
    # Setup session state for engine
    st.session_state.content_pack = sheets
    st.session_state.current_patient_index = 0
    st.session_state.patient_queue = []
    
    try:
        engine.generate_patient_queue()
        queue = st.session_state.patient_queue
        print(f"Queue Generated. Length: {len(queue)}")
        if len(queue) > 0:
            print(f"First Patient ID: {queue[0].get('ID')}")
            print(f"Is Tutorial: {queue[0].get('Is_Tutorial')}")
    except Exception as e:
        print(f"FAIL: Queue generation failed - {e}")

    print("Verification Script Complete.")

if __name__ == "__main__":
    run_verification()
