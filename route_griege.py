import pandas as pd
import numpy as np
import json
from pathlib import Path

# ---------- File Setup ---------- #
file_path = "Output/Griege_combined.xlsx"
sheet_name = "Griege"
df = pd.read_excel(file_path)

# Drop rows without Route Id
df = df.dropna(subset=["Route Id"])

# ✅ Extract full and numeric article
df["Item Id"] = df["Item Id"].astype(str)
df["full_article"] = df["Item Id"].str[4:]
df["article"] = df["full_article"].str.extract(r"(\d+)")[0]

df["Stage"] = "Weaving"
df["sizing_details"] = df["Config ID"]
df["weave_of_fabric"] = df["Dim2"].astype(str).str[:2]

# ---------- Grouping ---------- #
grouped = df.groupby(["Route Id", "Stage", "article", "full_article"])
output_data = []

for (route_id, stage, article, full_article), group in grouped:
    parameters = {}
    sentence_parts = []

    sizing_details = group["sizing_details"].dropna().iloc[0] if not group["sizing_details"].dropna().empty else ""
    weave_of_fabric = group["weave_of_fabric"].dropna().iloc[0] if not group["weave_of_fabric"].dropna().empty else ""

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

    article_mention = f"{full_article} or {article}" if full_article != article else article

    content_sentence = (
        f"Article {article_mention} uses Weaving operation with the following parameters: "
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
        "operation": stage,
        "sheet": "Griege",
        "sizing_details": sizing_details,
        "weave_of_fabric": weave_of_fabric,
        **parameters
    }

    output_data.append({
        "content": content_sentence,
        "metadata": metadata
    })

# ---------- JSON Conversion Fix ---------- #
def convert(obj):
    if isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return str(obj)

# ---------- Save JSON ---------- #
output_path = Path("rag_ready_griege.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False, default=convert)

print(f"✅ Griege JSON saved to {output_path}")
print(f"📊 Total Chunks: {len(output_data)}")
