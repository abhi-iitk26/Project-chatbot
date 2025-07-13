import pandas as pd
import re

# ---------- CONFIG ---------- #
file_path = "bom_Grouped_By_Process.xlsx"
df = pd.read_excel(file_path, sheet_name="Griege")
df.columns = [col.strip() for col in df.columns]

# ---------- STEP 1: Remove rows where LineItemID has BW or EW ---------- #
df = df[~df['LineItemID'].astype(str).str.contains("BW|EW", na=False)]

# ---------- STEP 2: Drop unwanted columns ---------- #
drop_cols = ['col_7','col_4', 'col_9', 'col_8', 'BOMQty', 'col_18', 'col_16', 'col_17', 'Process_Type', 'SheetName']
df.drop(columns=[col for col in drop_cols if col in df.columns], inplace=True)

# ---------- STEP 3: Rename relevant columns ---------- #
df.rename(columns={
    'col_3': 'Weft Yarn Sizing details',
    'col_6': 'Width of griege fabric',
    'col_12': 'Weft yarn vendor'
}, inplace=True)

# ---------- STEP 4: Extract weave type from col_4 ---------- #
def map_weave(code):
    prefix = str(code).strip()[:2].upper()
    mapping = {
        'DB': 'Dobby', 'RS': 'Ripstop', 'HB': 'Herringbone Twill',
        'KT': 'Knitted', 'KN': 'Knitted', 'LN': 'Leno',
        'ST': 'Satin', 'PL': 'Plain'
    }
    return mapping.get(prefix, prefix)

df['Weave of fabric'] = df['col_5'].apply(map_weave)
df.drop(columns=['col_5'], inplace=True)

# ---------- STEP 5: Parse LineItemID (19-char logic) ---------- #
def parse_lineitemid(val):
    val = str(val).strip()
    if len(val) != 19:
        return pd.Series([None] * 7)
    return pd.Series([
        val[0],        # Yarn Type
        val[1:6],      # Denier
        val[6:10],     # Filament
        val[10:13],    # Composition
        val[13:16],    # Twist Number
        val[16],       # Twist Direction
        val[17:19]     # Ply
    ])

df[[
    "Weft Yarn Type", "Weft Denier", "Filament in Weft Yarn", "Fibre in Weft",
     "Number of twist in Weft yarn", "Twist direction in Weft yarn", "Ply in Weft yarn"
]] = df["LineItemID"].apply(parse_lineitemid)
df.drop(columns=["LineItemID"], inplace=True)

# ---------- STEP 6: Replace symbols and composition ---------- #
composition_map = {
    'N06': 'Nylon 6', 'N66': 'Nylon 66', 'PES': 'Polyester', 'PPL': 'Polypropylene',
    'SPE': 'Spun Polyester', 'CTN': 'Cotton', 'PCT': 'Polyester-Cotton',
    'VSR': 'Viscose Rayon', 'PEV': 'Polyester Viscose', 'PSP': 'Polyester Spandex',
    'PBT': 'Polybutylene Terephthalate', 'SAC': 'Spun Acrylic', 'PRE': 'Recycled Polyester',
    'MRE': 'Recycled Nylon 06', 'NRE': 'Recycled Nylon 66', 'MAR': 'Meta Aramid',
    'PAR': 'Para Aramid', 'PTT': 'Polytrimethylene Teraphthalate (PTT) FDY Sorona',
    'PTS': 'PTT Bico Sorona Stretch', 'PRS': 'Recycled PET Spandex',
    'APR': 'Aromatic Polyester (Vectran)', 'MSP': 'Nylon 06 Spandex',
    'APE': 'Antistatic Nylon and Polyester Yarn', 'ANY': 'Antistatic Nylon Yarn',
    'MCL': 'NYLON6+COTTON+LYCRA', 'MCT': 'NYLON6+COTTON',
    'SPP': 'Spun Polyester steel + Continuous filament polyester'
}
df["Fibre in Weft"] = df["Fibre in Weft"].replace(composition_map)

yarn_type_symbol = {"X": "Twisted", "Y": "Flat", "A": "Air Textured"}
df["Weft Yarn Type"] = df["Weft Yarn Type"].replace(yarn_type_symbol)

df["Twist direction in Weft yarn"] = df["Twist direction in Weft yarn"].replace({
    "0": "No Twist", "S": "S Twist", "Z": "Z Twist"
})

# ---------- STEP 7: col_10 → Yarn textured ---------- #
def map_texture(val):
    val = str(val).strip().upper()[:3]
    return {
        'FDY': 'Fully Drawn Yarn', 'DTY': 'Drawn and Textured Yarn',
        'TWI': 'Twisted', 'ATY': 'Air Textured Yarn'
    }.get(val, val)

df['Drawing and texturing in Weft Yarn'] = df['col_11'].apply(map_texture)
df.drop(columns=['col_11'], inplace=True)

# ---------- STEP 8: col_12 → Yarn Shade and Brightness ---------- #
df['Shade Code of Weft'] = df['col_13'].astype(str).str[:2]
df['Weft Yarn Brightness'] = df['col_13'].astype(str).str[2:4].map({
    'FD': 'Fully Dull', 'SD': 'Semi Dull', 'BR': 'Bright'
})
df.drop(columns=['col_13'], inplace=True)

# ---------- STEP 9: col_13 → Shrinkage, Elongation, Tenacity ---------- #
df['Weft Yarn Shrinkage'] = df['col_14'].astype(str).str[:2].map({
    'NS': 'Normal Shrinkage', 'LS': 'Low Shrinkage'
})
df['Weft Yarn Elongation'] = df['col_14'].astype(str).str[2:4].map({
    'NE': 'Normal Elongation', 'HE': 'High Elongation'
})
df['Weft Yarn Tenacity'] = df['col_14'].astype(str).str[4:6].map({
    'NT': 'Normal Tenacity', 'LT': 'Low Tenacity', 'HT': 'High Tenacity'
})
df.drop(columns=['col_14'], inplace=True)


# ---------- STEP 9A: Clean Weft Denier and extract Count ---------- #
def clean_weft_denier(val):
    val = str(val).strip()

    # Case: Plyed Count format like 02/24 or 12/30
    if '/' in val:
        parts = val.split('/')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            ply = int(parts[0])
            count = int(parts[1])
            return "", f"{count} Ne of {ply} ply"

    # Case: Only digits (may have leading zeros)
    if val.isdigit():
        return str(int(val)), ""

    # Case: Non-numeric or weird text — return empty
    return "", ""

df[["Weft Denier", "Weft Count"]] = df["Weft Denier"].apply(clean_weft_denier).apply(pd.Series)


# ---------- STEP 12A: Clean Weft Denier further (keep only valid integers) ---------- #
def clean_weft_denier_postprocess(val):
    val = str(val).strip()

    # If decimal (e.g., 840.0)
    if re.fullmatch(r"\d+\.\d+", val):
        return ""

    # If not fully digits (e.g., abc, 12a)
    if not val.isdigit():
        return ""

    # If valid integer → remove leading zeros
    return str(int(val))

df["Weft Denier"] = df["Weft Denier"].apply(clean_weft_denier_postprocess)

# ---------- STEP 12B: Clean Number of twist and Filament columns ---------- #
def clean_number_of_twist(val):
    val = str(val).strip()
    return "0" if val == "000" else val.lstrip("0")

def clean_filament(val):
    val = str(val).strip()
    return "0" if val == "0000" else val.lstrip("0")

df["Number of twist in Weft yarn"] = df["Number of twist in Weft yarn"].apply(clean_number_of_twist)
df["Filament in Weft Yarn"] = df["Filament in Weft Yarn"].apply(clean_filament)



# ---------- STEP 10: Keep only 1 row per BOMId ---------- #
df = df.groupby('BOMId', as_index=False).first()

# ---------- STEP 11: Save Final Sheet ---------- #
with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df.to_excel(writer, sheet_name="Cleaned_Griege", index=False)

print("✅ Cleaned_Griege sheet created successfully with structured weft yarn info.")
