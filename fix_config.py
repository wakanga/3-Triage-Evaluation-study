import pandas as pd

filepath = 'config/study_content_pack.xlsx'
sheets = pd.read_excel(filepath, sheet_name=None)

config_df = sheets['Config']

# Reset all Valid_Tools to empty so secondary metrics disappear
config_df['Valid_Tools'] = ""
config_df['SMART_Order'] = pd.NA
config_df['TST_Order'] = pd.NA

# SMART Rules
smart_actions = {
    'walk': 1.0,
    'airway_obs': 2.0,
    'airway_man': 2.5,
    'rr': 3.0,
    'pulse_rate': 4.0,
    'cap_refill': 4.0
}

# TST Rules
tst_actions = {
    'walk': 1.0,
    'hemorrhage': 2.0,
    'hemorrhage_ctrl': 2.5,
    'talking': 3.0,
    'deadly_box': 4.0,
    'airway_obs': 5.0,
    'airway_man': 5.5
}

for idx, row in config_df.iterrows():
    key = row['Action_Key']
    
    valid_list = []
    
    if key in smart_actions:
        valid_list.append("SMART")
        config_df.at[idx, 'SMART_Order'] = smart_actions[key]
        
    if key in tst_actions:
        valid_list.append("TST")
        config_df.at[idx, 'TST_Order'] = tst_actions[key]
        
    if valid_list:
        config_df.at[idx, 'Valid_Tools'] = ",".join(valid_list)

sheets['Config'] = config_df

with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
    for sheet_name, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Updated config/study_content_pack.xlsx Config sheet successfully.")
