import pandas as pd

# Read the Excel file
filepath = 'config/study_content_pack.xlsx'
df = pd.read_excel(filepath, 'Tools')

# Fix the invalid Normalized_Value entries
df.loc[df['Button_Label'] == 'Cat 2 (Imminent)', 'Normalized_Value'] = 'Yellow'
df.loc[df['Button_Label'] == 'Cat 4 (Semi-Urgent)', 'Normalized_Value'] = 'Yellow'
df.loc[df['Button_Label'] == 'Cat 5 (Non-Urgent)', 'Normalized_Value'] = 'Green'

# Write back to Excel
with pd.ExcelWriter(filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df.to_excel(writer, sheet_name='Tools', index=False)

print("Fixed! New Tools tab:")
print(df)
