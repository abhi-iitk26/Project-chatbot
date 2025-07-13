import pandas as pd
import os

# ------------------ Step 1: Configuration ------------------ #
data_folder = "Data"
reference_file = os.path.join(data_folder, "1.xlsx")
input_files = [os.path.join(data_folder, f"{i}.xlsx") for i in range(1, 29)]
output_file = "merged_BOM_quality.xlsx"

# ------------------ Step 2: Get Reference Columns ------------------ #
ref_df = pd.read_excel(reference_file, sheet_name="Quality")
ref_columns = ref_df.columns[:14].tolist()  # Columns A to N

# ------------------ Step 3: Fibre Code Mapping ------------------ #
fibre_map = {
    'M': "Nylon 6", 'N': "Nylon 66", 'L': "Poly Propylene", 'P': "Polyester",
    'E': "Spun Polyester", 'V': "Viscose Rayon", 'T': "Polyester Cotton", 'R': "Para Aramid",
    'A': "Meta Aramid", 'C': "Cotton", 'B': "Dimetrol", 'D': "Nylon Cotton",
    'Z': "Nylon Spandex", 'G': "Polyester Viscose", 'H': "Spun Poly Propylene",
    'S': "Polyester Spandex", 'U': "Spun Viscose Rayon", 'Y': "Spun Acrylic",
    'F': "Recycled Polyester Spandex", 'I': "PTT", 'J': "PTT stretch",
    'X': "Aromatic Polyester (ARP - Vectran)", 'K': "Nylon 06 Spandex", 'Q': "Glass Fibre"
}

# ------------------ Step 4: Helper Functions ------------------ #
def extract_article_stage(item):
    if not isinstance(item, str) or len(item) < 5:
        return "", "Unknown"
    first_char = item[0].upper()
    stage_map = {'G': 'Griege', 'P': 'Processing', 'C': 'Coating'}
    stage_name = stage_map.get(first_char, f"Unknown ({first_char})")
    article_no = item[4:]
    return article_no, stage_name

def extract_fibres(item):
    if not isinstance(item, str) or len(item) < 4:
        return "", ""
    warp_code = item[2].upper()
    weft_code = item[3].upper()
    return fibre_map.get(warp_code, f"Unknown ({warp_code})"), fibre_map.get(weft_code, f"Unknown ({weft_code})")

# ------------------ Step 5: Create Combined DataFrame ------------------ #
combined_df = pd.DataFrame(columns=ref_columns)

# ------------------ Step 6: Processing Each File ------------------ #
for file in input_files:
    try:
        # First read only A1 to decide
        preview = pd.read_excel(file, sheet_name="Quality", nrows=1, usecols="A")
        a1_value = str(preview.iloc[0, 0]).strip().upper()

        if a1_value.startswith("Q"):
            print(f"⚠️ Skipped {file} due to A1='{a1_value}'")
            continue

        df = pd.read_excel(file, sheet_name="Quality")
        df.columns = df.columns.str.strip()

        for col in ref_columns:
            if col not in df.columns:
                df[col] = ""

        df = df[ref_columns]

        # ➕ Add derived columns
        df["article_no"], df["stage_name"] = zip(*df["Item number"].apply(extract_article_stage))
        df["warp_fibre"], df["weft_fibre"] = zip(*df["Item number"].apply(extract_fibres))

        # ➕ Append to final DataFrame
        combined_df = pd.concat([combined_df, df], ignore_index=True)
        print(f"✅ Processed: {file}")

    except Exception as e:
        print(f"❌ Error processing {file}: {e}")

# ------------------ Step 7: Save Final Output ------------------ #
combined_df.to_excel(output_file, index=False, sheet_name="Merged_Quality")
print(f"\n✅ Final Merged File Saved as: {output_file}")
