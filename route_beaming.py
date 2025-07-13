import pandas as pd
import numpy as np
import json
from pathlib import Path

# ---------- Load Excel ---------- #
file_path = "Output/Beaming_combined.xlsx"
df = pd.read_excel(file_path)

# Drop rows without Route Id
df = df.dropna(subset=["Route Id"])

# ✅ Derive Full Article from Item Id (characters after first 4)
df["Item Id"] = df["Item Id"].astype(str)
df["Full Article"] = df["Item Id"].str[4:]   # e.g., BWPP8228FT → 8228FT

# ✅ Extract Article Number (numeric part only)
df["Article Number"] = df["Full Article"].str.extract(r'(\d+)')[0]

# Map Opr Id to readable operation
def map_opr_id(val):
    if val == "Siz":
        return "Sizing"
    elif val == "Bea":
        return "Beaming"
    else:
        return str(val)

df["operation"] = df["Opr Id"].map(map_opr_id)
df["Config ID"] = df["operation"]
df["Total Ends in Warp"] = df["Dim2"]

# ---------- Grouping ---------- #
grouped = df.groupby(["Route Id", "operation", "Article Number", "Full Article"])
output_data = []

for (route_id, operation, article, full_article), group in grouped:
    parameters = {}
    sentence_parts = []

    config_id = group["Config ID"].dropna().iloc[0] if not group["Config ID"].dropna().empty else ""
    ends_in_warp = group["Total Ends in Warp"].dropna().iloc[0] if not group["Total Ends in Warp"].dropna().empty else ""

    for _, row in group.iterrows():
        name = row.get("Name")
        min_val = row.get("Standard Min")
        max_val = row.get("Standard Max")
        unit = row.get("Unit")

        if pd.isna(name):
            continue

        value_str = ""
        if not pd.isna(min_val) and not pd.isna(max_val):
            if str(min_val).strip() == str(max_val).strip():
                value_str = f"{min_val}"
            else:
                value_str = f"{min_val} to {max_val}"
        elif not pd.isna(min_val):
            value_str = f"{min_val}"
        elif not pd.isna(max_val):
            value_str = f"{max_val}"
        else:
            continue

        if pd.notna(unit):
            value_str += f"{unit}" if "%" not in str(value_str) and "%" in str(unit) else ""

        parameters[name] = value_str
        sentence_parts.append(f"{name} is set to {value_str}")

    # Article reference logic
    article_mention = f"{full_article} or {article}" if full_article != article else article

    content_sentence = (
        f"Article {article_mention} uses {operation} operation with the following parameters: "
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
        "operation": operation,
        "sheet": "Beaming",
        "config_id": config_id,
        "total_ends_in_warp": ends_in_warp,
        **parameters
    }

    output_data.append({
        "content": content_sentence,
        "metadata": metadata
    })

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
output_path = Path("rag_ready_beaming.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False, default=convert)

print(f"✅ JSON with correct full_article saved to {output_path}")
print(f"📊 Total Chunks: {len(output_data)}")
