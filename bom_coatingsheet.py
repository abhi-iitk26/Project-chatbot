import pandas as pd
import re
# ---------- CONFIG ---------- #
file_path = "bom_Grouped_By_Process.xlsx"

# ---------- STEP 1: Load Coating Sheet ---------- #
df = pd.read_excel(file_path, sheet_name="Coating")
df.columns = [col.strip() for col in df.columns]

# ---------- STEP 2: Extract Article Number ---------- #
#df["Article_No"] = df["N"].astype(str).str.extract(r'(\d{4})')
#df["Article_No"] = df["Article_No"].astype(str).str.replace(r"\.0$", "", regex=True)
#df.drop(columns=["col_1"], inplace=True)

# ---------- STEP 3: Rename Columns ---------- #
df.rename(columns={
    "col_3": "Type of Coating",
    "col_4": "Shade",
    "col_5": "Type of Finish",
    "col_6": "Width After Coating",
    "LineItemID": "Coating Chemical",
    "col_12": "Coating Chemical Vendors"
}, inplace=True)

# ---------- STEP 4: Apply Value Mappings to Type of Coating ---------- #
def map_coating_type(val):
    val = str(val).strip().upper()

    if val == "PU":
        return "Polyurethane Coating"
    elif val.startswith("PUS"):
        return "Polyurethane Solvent"
    elif val == "AC" or val.startswith("AC"):
        return "Acrylic Coating"
    elif "AC+SLC" in val:
        return "Acrylic"
    elif val.startswith("BRPU"):
        return "Breathable Polyurethane"
    elif val.startswith("DSPVC"):
        return "Breathable Polyvinyle Chloride Coating"
    elif val.startswith("FRLAM"):
        return "Flame Retardent Lamination"
    elif re.match(r"^HB\d+WLAM$", val):
        micron = re.findall(r"\d+", val)[0]
        return f"High breathable white lamination of {micron} micron"
    elif re.match(r"^HB\d+TLAM$", val):
        micron = re.findall(r"\d+", val)[0]
        return f"High breathable transparent lamination of {micron} micron"
    elif re.match(r"^HB\d+\s*LAM$", val):
        micron = re.findall(r"\d+", val)[0]
        return f"High breathable lamination of {micron} micron"
    elif val.startswith("SIPU"):
        return "Silicon and Polyurethane"
    elif val.startswith("SLPU"):
        return "Sealable Polyurethane"
    else:
        return val  # leave unchanged if not matched

df["Type of Coating"] = df["Type of Coating"].apply(map_coating_type)


# ---------- STEP 4a: Map Type of Finish Logic ---------- #
def map_finish(val):
    val = str(val).strip().upper()
    if val.startswith("FFDWR"):
        return "Fluorine Free Durable Water Repellent (C Zero)"
    elif val.startswith("FRDWR"):
        return "Flame Retardant and Durable Water Repellent"
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
columns_to_drop = ["col_9", "col_7", "col_8", "col_11", "col_13", "col_16"]
df.drop(columns=columns_to_drop, inplace=True, errors="ignore")

# ---------- STEP 6: Filter Out 'PW' Chemicals ---------- #
df = df[~df['Coating Chemical'].astype(str).str.match(r'^(PW|DW)', na=False)]


# ---------- STEP 7: Group Static Fields by BOMId ---------- #
grouped_info = df.groupby('BOMId').agg({
    'Type of Coating': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Shade': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Type of Finish': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Width After Coating': lambda x: ', '.join(sorted(set(x.dropna().astype(str)))),
    'Article_No': lambda x: ', '.join(sorted(set(x.dropna().astype(str))))
})

# ---------- STEP 8: Combine Chemical, Vendor, Usage ---------- #
# ---------- STEP 8: Combine Chemical, Vendor, Usage + Quantity ---------- #
chemicals_data = []
for bom_id, group in df.groupby('BOMId'):
    chemical_rows = []
    for _, row in group.iterrows():
        chem = str(row['Coating Chemical']).strip()
        vendor = str(row['Coating Chemical Vendors']).strip()
        usage = str(row.get('col_14', '')).strip()
        qty = str(row.get('BOMQty', '')).strip()

        if chem and chem.lower() != 'nan':
            parts = [f"{chem}"]
            if vendor or usage:
                parts.append(f"({vendor} - {usage})")
            if qty:
                parts.append(f"and chemical quantity is {qty}")
            chemical_rows.append(" ".join(parts))

    chemicals_data.append({
        'BOMId': bom_id,
        'Coating Chemicals': "; ".join(chemical_rows)
    })


chemicals_df = pd.DataFrame(chemicals_data).set_index('BOMId')

# ---------- STEP 9: Merge and Save Final Data ---------- #
final_df = grouped_info.join(chemicals_df).reset_index()

with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    final_df.to_excel(writer, sheet_name="Cleaned_Coating", index=False)

print("✅ Cleaned_Coating sheet created with proper chemical + vendor + usage details.")
