import pandas as pd
import os

# ------------------ Step 1: Configuration ------------------ #
data_folder = "Data"
reference_file = os.path.join(data_folder, "1.xlsx")
# Automatically detect all Excel files named as digits (e.g., 1.xlsx, 2.xlsx, ...)
input_files = [
    os.path.join(data_folder, f)
    for f in os.listdir(data_folder)
    if f.endswith(".xlsx") and f.split(".")[0].isdigit()
]

# Sort files numerically (important if filenames are not in order)
input_files.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))

final_excel_output = "bom_Grouped_By_Process.xlsx"

sheet_map = {
    "BE": "Warping",
    "BA": "Warping",
    "BG": "Griege",
    "BP": "Processing",
    "BC": "Coating"
}

# ------------------ Step 2: Storage ------------------ #
final_dataframes = {name: [] for name in sheet_map.values()}

# ------------------ Step 3: Process Each File ------------------ #
for file in input_files:
    try:
        try:
            xls = pd.ExcelFile(file)
        except Exception as e:
            print(f"❌ Failed to open {file}: {e}")
            continue

        # Find BOM sheet name (case-insensitive match)
        bom_sheet = next((s for s in xls.sheet_names if s.strip().lower() == "bom"), None)

        if bom_sheet:
            df = pd.read_excel(xls, sheet_name=bom_sheet, header=None)
            df = df.iloc[1:].reset_index(drop=True)        # Remove title row
            df = df.dropna(axis=1, how='all')              # Drop fully empty columns
            df = df.iloc[1:].reset_index(drop=True)
            df.columns = [f"col_{i}" for i in range(len(df.columns))]

            # Rename key columns
            df.rename(columns={
                "col_0": "BOMId",
                "col_2": "ItemId",
                "col_10": "LineItemID",
                "col_15": "BOMQty"
            }, inplace=True)

            # Extract Article number & Process type
            df["Article_No"] = df["ItemId"].astype(str).str[4:]
            df["Process_Type"] = df["BOMId"].astype(str).str[:2]
            df["SheetName"] = df["Process_Type"].map(sheet_map)
            df = df[df["SheetName"].notna()]

            # Group by process and collect
            for sheet_name, group_df in df.groupby("SheetName"):
                final_dataframes[sheet_name].append(group_df)

            print(f"✅ Processed BOM from: {file}")
        else:
            print(f"❌ BOM sheet not found in {file}")
            print(f"   📄 Available sheets: {xls.sheet_names}")

    except Exception as e:
        print(f"⚠️ Error processing {file}: {e}")

# ------------------ Step 4: Save Final Output ------------------ #
with pd.ExcelWriter(final_excel_output) as writer:
    for sheet_name, dfs in final_dataframes.items():
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"\n✅ Final merged output saved as '{final_excel_output}'")
