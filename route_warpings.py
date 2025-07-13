import pandas as pd
import numpy as np
import json
from pathlib import Path
import re

# ---------- Load Excel ---------- #
file_path = "Output/Sectional Warping_combined.xlsx"
df = pd.read_excel(file_path)

# Drop rows without Route Id
df = df.dropna(subset=["Route Id"])

# Extract article and full_article from Item Id
df["Item Id"] = df["Item Id"].astype(str)
df["full_article"] = df["Item Id"].str[4:]
df["article"] = df["full_article"].str.extract(r"(\d+)")[0]


# ---------- Operation Mapping ---------- #
# Base readable names from Opr Id
def map_opr_id(val):
    if val == "Siz":
        return "Sizing"
    elif val == "Bea":
        return "Beaming"
    else:
        return str(val)


df["operation"] = df["Opr Id"].map(map_opr_id)

# Map Opr Id to broader operation (sectional warping etc.)
operation_map = {
    "Sec War": "sectional warping",
    "Weav": "weaving",
    "War": "direct warping",
}
# Apply operation mapping (fallback to already mapped operation above)
df["operation"] = df["Opr Id"].map(operation_map).fillna(df["operation"])

# ---------- Add other fields ---------- #
df["Config ID"] = df["operation"]
df["Total Ends of Warp"] = df["Dim2"]

# ---------- Grouping ---------- #
grouped = df.groupby(["Route Id", "operation", "article", "full_article"])
output_data = []

for (route_id, operation, article, full_article), group in grouped:
    parameters = {}
    sentence_parts = []

    config_id = (
        group["Config ID"].dropna().iloc[0]
        if not group["Config ID"].dropna().empty
        else ""
    )
    ends_in_warp = (
        group["Total Ends of Warp"].dropna().iloc[0]
        if not group["Total Ends of Warp"].dropna().empty
        else ""
    )

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

    # Final content sentence
    article_mention = (
        f"{full_article} or {article}" if full_article != article else article
    )
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
        "full article": full_article,
        "operation": operation,
        "sheet": "Sectional Warping",
        "config_id": config_id,
        "total ends of warp": ends_in_warp,
        **parameters,
    }

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
output_path = Path("rag_ready_sectional_warping.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False, default=convert)

print(f"✅ Sectional Warping JSON saved to {output_path}")
print(f"📦 Total chunks: {len(output_data)}")
