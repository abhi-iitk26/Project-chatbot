import pandas as pd
import numpy as np
import json
from pathlib import Path
import re

# ----------- File Selection ----------- #
file_path = "Output/Direct Warping_combined.xlsx"  # 🔁 Change as needed
sheet_name = Path(file_path).stem.split("_")[0]  # e.g., "Direct Warping" or "Griege"

df = pd.read_excel(file_path)
df = df.dropna(subset=["Route Id"])

# Extract article & full_article
df["Item Id"] = df["Item Id"].astype(str)
df["full_article"] = df["Item Id"].str[4:]
df["article"] = df["full_article"].str.extract(r"(\d+)")[0]

# Set stage and metadata fields
if sheet_name == "Direct Warping":
    df["Stage"] = df["Opr Id"].apply(
        lambda x: "Warping" if str(x).strip() == "War" else str(x)
    )
    df["sizing_details"] = df["Config ID"]
    df["number_of_ends_in_warp"] = df["Dim2"]
elif sheet_name == "Griege":
    df["Stage"] = "Weaving"
    df["sizing_details"] = df["Config ID"]
    df["weave_of_fabric"] = df["Dim2"].astype(str).str[:2]
else:
    raise ValueError("❌ Invalid sheet. Use only for Direct Warping or Griege.")

# ---------- Stage to Operation Mapping ---------- #
operation_map = {
    "Sec War": "sectional warping",
    "Weav": "weaving",
    "War": "direct warping",  # Add this for Direct Warping
}
df["operation_mapped"] = df["Opr Id"].map(operation_map).fillna(df["Stage"])

# ---------- Grouping ---------- #
grouped = df.groupby(["Route Id", "Stage", "article", "full_article"])
output_data = []

for (route_id, stage, article, full_article), group in grouped:
    parameters = {}
    sentence_parts = []

    # Extract shared metadata
    sizing_details = (
        group["sizing_details"].dropna().iloc[0]
        if not group["sizing_details"].dropna().empty
        else ""
    )
    ends_in_warp = (
        group["number_of_ends_in_warp"].dropna().iloc[0]
        if "number_of_ends_in_warp" in group
        and not group["number_of_ends_in_warp"].dropna().empty
        else ""
    )
    weave_of_fabric = (
        group["weave_of_fabric"].dropna().iloc[0]
        if "weave_of_fabric" in group and not group["weave_of_fabric"].dropna().empty
        else ""
    )
    operation_value = group["operation_mapped"].dropna().iloc[0]

    for _, row in group.iterrows():
        name = row.get("Name")
        min_val = row.get("Standard Min")
        max_val = row.get("Standard Max")
        unit = row.get("Unit")

        if pd.isna(name):
            continue

        value_str = ""
        if not pd.isna(min_val) and not pd.isna(max_val):
            value_str = (
                f"{min_val}"
                if str(min_val).strip() == str(max_val).strip()
                else f"{min_val} to {max_val}"
            )
        elif not pd.isna(min_val):
            value_str = f"{min_val}"
        elif not pd.isna(max_val):
            value_str = f"{max_val}"
        else:
            continue

        if pd.notna(unit):
            value_str += (
                f"{unit}" if "%" not in str(value_str) and "%" in str(unit) else ""
            )

        parameters[name] = value_str
        sentence_parts.append(f"{name} is set to {value_str}")

    # Build content sentence
    article_mention = (
        f"{full_article} or {article}" if full_article != article else article
    )
    content_sentence = (
        f"Article {article_mention} uses {stage} operation with the following parameters: "
        + ", ".join(sentence_parts)
        + "."
    )

    metadata = {
        "article": article,
        "article_no": article,
        "article no": article,
        "article number": article,
        "fabric": article,
        "full_article": full_article,
        "operation": operation_value,  # ✅ use mapped operation here
        "sheet": sheet_name,
        **parameters,
    }

    if sheet_name == "Direct Warping":
        metadata["sizing_details"] = sizing_details
        metadata["number_of_ends_in_warp"] = ends_in_warp
    elif sheet_name == "Griege":
        metadata["sizing_details"] = sizing_details
        metadata["weave_of_fabric"] = weave_of_fabric

    output_data.append({"content": content_sentence, "metadata": metadata})


# ---------- JSON Serialization Fix ---------- #
def convert(obj):
    if isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return str(obj)


# ---------- Save JSON ---------- #
output_file = f"rag_ready_{sheet_name.replace(' ', '_').lower()}.json"
output_path = Path(output_file)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False, default=convert)

print(f"✅ JSON saved to {output_path}")
print(f"📦 Total Chunks: {len(output_data)}")
