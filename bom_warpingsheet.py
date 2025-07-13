import pandas as pd
import re

# ---------- CONFIG ---------- #
file_path = "bom_Grouped_By_Process.xlsx"
valid_sheets = ["Sectional Warping", "Direct Warping", "Warping"]  # any one might exist

# ---------- STEP 1: Load matching Warping sheet ---------- #
excel_file = pd.ExcelFile(file_path)
available_sheets = excel_file.sheet_names

# Find first matching sheet
sheet_to_use = next((s for s in available_sheets if s.strip().lower() in [v.lower() for v in valid_sheets]), None)

if not sheet_to_use:
    raise ValueError(f"No Warping sheet found in file. Available sheets: {available_sheets}")

df = pd.read_excel(file_path, sheet_name=sheet_to_use)
df.columns = [col.strip() for col in df.columns]
print(f"✅ Loaded sheet: '{sheet_to_use}' with columns: {df.columns.tolist()}")

# ---------- STEP 2: Drop unwanted columns ---------- #
df.drop(columns=["col_3", "col_7", "col_8", "col_9", "col_1"], inplace=True, errors="ignore")

# ---------- STEP 3: Rename useful columns ---------- #
df.rename(columns={
    "col_4": "Shade of Warp Yarn",
    "col_5": "Total Ends",
    "col_6": "Reed space",
    "col_12": "Warp yarn vendor"
}, inplace=True)

# ---------- STEP 4: Parse LineItemID (Warp Info) ---------- #
def parse_lineitemid(val):
    val = str(val).strip()
    if len(val) != 19:
        return pd.Series([None] * 7)
    return pd.Series([
        val[0],        # Warp Yarn Type
        val[1:6],      # Warp Denier
        val[6:10],     # Filament in Warp yarn
        val[10:13],    # Fibre in Warp
        val[13:16],    # Number of twist in Warp yarn
        val[16],       # Twist direction in warp yarn
        val[17:19]     # Ply in warp yarn
    ])

df[[
    "Warp Yarn Type", "Warp Denier", "Filament in Warp yarn", "Fibre in Warp",
    "Number of twist in Warp yarn", "Twist direction in warp yarn", "Ply in warp yarn"
]] = df["LineItemID"].apply(parse_lineitemid)

# ---------- STEP 5: Merge Yarn Type Codes into Drawing and Texturing Column ---------- #
df["Drawing and texturing in Warp Yarn"] = df["col_11"].astype(str).apply(lambda val: f"{val[:3]} / {val[-3:]}")
df.drop(columns=["col_11"], inplace=True)

# ---------- STEP 6: Parse Shade Code + Dullness ---------- #
df[["Shade code of warp", "Dullness/Brightness of warp"]] = df["col_13"].astype(str).apply(lambda val: pd.Series([val[:2], val[2:4]]))
df.drop(columns=["col_13"], inplace=True)

# ---------- STEP 7: Parse Shrinkage, Elongation, Tenacity ---------- #
df[["Warp Yarn Shrinkage", "Warp Yarn Elongation", "warp Yarn Tenacity"]] = df["col_14"].astype(str).apply(lambda val: pd.Series([val[:2], val[2:4], val[4:6]]))
df.drop(columns=["col_14"], inplace=True)

# ---------- STEP 8: Replace Codes with Full Forms ---------- #
yarn_code_map = {
    "FDY": "Fully Drawn Yarn", "DTY": "Drawn Textured Yarn", "TWI": "Twisted",
    "SIM": "Semi Intermingle", "HIM": "Highly Intermingle", "FLT": "Flat"
}
yarn_type_symbol = { "X": "Twisted", "Y": "Flat", "A": "Air Textured" }
dullness_map = { "FD": "Fully Dull", "SD": "Semi Dull", "BR": "Bright" }
shrinkage_map = { "NS": "Normal Shrinkage", "LS": "Low Shrinkage" }
elongation_map = { "NE": "Normal Elongation", "HE": "High Elongation" }
tenacity_map = { "NT": "Normal Tenacity", "LT": "Low Tenacity", "HT": "High Tenacity" }

df["Drawing and texturing in Warp Yarn"] = df["Drawing and texturing in Warp Yarn"].replace(yarn_code_map)
df["Warp Yarn Type"] = df["Warp Yarn Type"].replace(yarn_type_symbol)
df["Dullness/Brightness of warp"] = df["Dullness/Brightness of warp"].replace(dullness_map)
df["Warp Yarn Shrinkage"] = df["Warp Yarn Shrinkage"].replace(shrinkage_map)
df["Warp Yarn Elongation"] = df["Warp Yarn Elongation"].replace(elongation_map)
df["warp Yarn Tenacity"] = df["warp Yarn Tenacity"].replace(tenacity_map)

# ---------- STEP 9: Type of Warping using ItemId (Updated Logic) ---------- #
df['ItemId'] = df['ItemId'].astype(str).str.strip()

df['Type of Warping'] = df['ItemId'].apply(lambda val: (
    "Sectional warping" if val.startswith("E") else
    "Direct warping" if val.startswith("A") else val
))

# ---------- STEP 9A: Remove rows with invalid ItemId prefixes ---------- #
df = df[df['ItemId'].str.startswith(('E', 'A'))]


# ---------- STEP 11: Replace Composition Short Codes ---------- #
composition_map = {
    'N06': 'Nylon 6', 'N66': 'Nylon 66', 'PES': 'Polyester', 'PPL': 'Polypropylene',
    'SPE': 'Spun Polyester', 'CTN': 'Cotton', 'PCT': 'Polyester-Cotton', 'VSR': 'Viscose Rayon',
    'PEV': 'Polyester Viscose', 'PSP': 'Polyester Spandex', 'PBT': 'Polybutylene Terephthalate',
    'SAC': 'Spun Acrylic', 'PRE': 'Recycled Polyester', 'MRE': 'Recycled Nylon 06',
    'NRE': 'Recycled Nylon 66', 'MAR': 'Meta Aramid', 'PAR': 'Para Aramid',
    'PTT': 'Polytrimethylene Teraphthalate (PTT) FDY Sorona',
    'PTS': 'PTT Bico Sorona Stretch', 'PRS': 'Recycled PET Spandex',
    'APR': 'Aromatic Polyester (Vectran)', 'MSP': 'Nylon 06 Spandex',
    'APE': 'Antistatic Nylon and Polyester Yarn', 'ANY': 'Antistatic Nylon Yarn',
    'MCL': 'NYLON6+COTTON+LYCRA', 'MCT': 'NYLON6+COTTON',
    'SPP': 'Spun Polyester steel + Continuous filament polyester'
}

def replace_composition(value):
    if pd.isna(value):
        return value
    for short, full in composition_map.items():
        if short in str(value):
            value = value.replace(short, full)
    return value

df['Fibre in Warp'] = df['Fibre in Warp'].apply(replace_composition)

# ---------- STEP 12: Handle Warp Denier with Ply ---------- #
def clarify_warp_denier(value):
    if isinstance(value, str) and '/' in value:
        return f"{value} (Plyed Count Yarn, not Denier)"
    return value

df['Warp Denier'] = df['Warp Denier'].apply(clarify_warp_denier)

def split_reed_space(value):
    value = str(value).strip()
    try:
        # Extract numeric value only for comparison
        numeric_value = float(re.findall(r"[\d.]+", value)[0]) if re.search(r"[\d.]+", value) else 0
        if "'" in value or '"' in value or numeric_value > 20:
            return value, ""
        else:
            return "", value
    except:
        return value, ""

df[["Reed space", "Number of Beams"]] = df["Reed space"].apply(split_reed_space).apply(pd.Series)


def split_and_convert_warp_denier(val):
    val = str(val).strip()

    # If brackets are present, remove value from Warp Denier and extract Warp Count
    if '(' in val and ')' in val:
        # Get the part before the bracket
        val_no_bracket = val.split('(')[0].strip()
        if '/' in val_no_bracket:
            parts = val_no_bracket.split('/')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                ply = int(parts[0])
                count = int(parts[1])
                return "", f"{count} Ne of {ply} ply"
        return "", ""  # fallback if parsing fails

    # If no bracket, keep as is
    return val, ""

df[["Warp Denier", "Warp Count"]] = df["Warp Denier"].apply(split_and_convert_warp_denier).apply(pd.Series)


# ---------- STEP 12A: Clean Warp Denier further (keep only valid integers) ---------- #
def clean_warp_denier_postprocess(val):
    val = str(val).strip()

    # If decimal (e.g., 840.0)
    if re.fullmatch(r"\d+\.\d+", val):
        return ""

    # If not fully digits (e.g., abc, 12a)
    if not val.isdigit():
        return ""

    # If valid integer → remove leading zeros
    return str(int(val))

df["Warp Denier"] = df["Warp Denier"].apply(clean_warp_denier_postprocess)

# ---------- STEP 12B: Clean Number of twist and Filament columns ---------- #
def clean_number_of_twist(val):
    val = str(val).strip()
    return "0" if val == "000" else val.lstrip("0")

def clean_filament(val):
    val = str(val).strip()
    return "0" if val == "0000" else val.lstrip("0")

df["Number of twist in Warp yarn"] = df["Number of twist in Warp yarn"].apply(clean_number_of_twist)
df["Filament in Warp yarn"] = df["Filament in Warp yarn"].apply(clean_filament)





# ---------- STEP 13: Final Cleanup ---------- #
df.drop(columns=[
    'Process_Type', 'SheetName', 'LineItemID', 'BOMQty',
    'col_16', 'col_17', 'col_18'
], inplace=True, errors='ignore')



# ---------- STEP 14: Save Final Output ---------- #
with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df.to_excel(writer, sheet_name="Cleaned_Warping", index=False)

print(f"✅ Cleaned_Warping created from: '{sheet_to_use}'")
