import pandas as pd
import re

# ---------- CONFIG ---------- #
file_path = "bom_Grouped_By_Process.xlsx"

# ---------- STEP 1: Load Processing Sheet ---------- #
df = pd.read_excel(file_path, sheet_name="Processing")
df.columns = [col.strip() for col in df.columns]

# ---------- STEP 2: Rename Required Columns ---------- #
df.rename(columns={
    "col_3": "Calendaring",
    "col_4": "Required Shade",
    "col_5": "Type of Finish",
    "col_6": "Width in cm",
    "LineItemID": "Chemical Used",
    "col_12": "Chemicals Vendor",
    "col_13": "Phase of Chemical",
    "col_18": "Unit of Measurement"
}, inplace=True)

# ---------- STEP 3: Map Calendaring Logic ---------- #
df["Calendaring"] = df["Calendaring"].apply(
    lambda x: "No calendar" if str(x).strip().upper() == "NIL" 
    else "Calendared Fabric" if str(x).strip().upper().startswith("CL") 
    else x
)

# ---------- STEP 4: Map Type of Finish Logic ---------- #
def map_finish(val):
    val = str(val).strip().upper()
    if val.startswith("FFDWR"):
        return "Fluorine Free Durable Water Repellent"
    elif val.startswith("DWR"):
        return "Durable Water Repellent"
    elif val.startswith("WR"):
        return "Water Repellent Finish"
    elif val.startswith("SI"):
        return "Silicon Finish"
    elif val.startswith("ST"):
        return "Stiff Finish"
    elif val.startswith("MMT"):
        return "Moisture Management Finish"
    elif val.startswith("AB"):
        return "AntiBacterial Finish"
    elif val.startswith("CB") or val.startswith("PR"):
        return "Prime Finish"
    elif val.startswith("FR"):
        return "Flame Retardent Finish"
    elif val.startswith("LPE"):
        return "Levofin PE Finish"
    elif val == "NIL":
        return "No Finish"
    return val
df["Type of Finish"] = df["Type of Finish"].apply(map_finish)


# ---------- STEP 5: Drop Unwanted Columns ---------- #
columns_to_drop = [ "col_7", "col_8", "col_9", "col_14", "col_16", "col_17"]
df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

# ---------- STEP 6: Remove 'GW' Chemicals ---------- #
df = df[~df['Chemical Used'].astype(str).str.startswith('GW', na=False)]

# ---------- STEP 7: Extract Machine Info from 'Name' ---------- #
def extract_machine(name):
    match = re.search(r'\((.*?)\)', str(name))
    return match.group(1).strip() if match else ''

def clean_name(name):
    return re.sub(r'\s*\(.*?\)', '', str(name)).strip()

df['Machine used for processing'] = df['col_1'].apply(extract_machine)
df['col_1'] = df['col_1'].apply(clean_name)

# ---------- STEP 8: Group Information Per BOM ---------- #
# ---------- STEP 8: Group Information Per BOM ---------- #
df["Article_No"] = df["Article_No"].astype(str).str.replace(r"\.0$", "", regex=True)

grouped_info = df.groupby('BOMId').agg({
    'col_1': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Machine used for processing': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Calendaring': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Required Shade': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Type of Finish': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Width in cm': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Article_No': lambda x: ', '.join(sorted(set(x.dropna().astype(str))))
})


# ---------- STEP 9: Create Chemical Summary ---------- #
chem_data = []
for bom_id, group in df.groupby('BOMId'):
    chem_list = []
    for _, row in group.iterrows():
        chem = str(row['Chemical Used']).strip()
        vendor = str(row['Chemicals Vendor']).strip()
        qty = str(row.get('BOMQty', '')).strip()
        if chem and chem.lower() != 'nan':
            chem_list.append(f"{chem} ({vendor} - {qty} Gpl)")
    chem_data.append({'BOMId': bom_id, 'Chemicals Used': '; '.join(chem_list)})

chem_df = pd.DataFrame(chem_data).set_index('BOMId')

# ---------- STEP 10: Merge Grouped Info and Save ---------- #
final_df = grouped_info.join(chem_df).reset_index()

with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    final_df.to_excel(writer, sheet_name="Cleaned_Processing", index=False)

print("✅ Cleaned_Processing sheet saved successfully with machine info, finish mapping, and chemical details.")
