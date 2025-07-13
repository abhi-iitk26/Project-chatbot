import pandas as pd
import numpy as np
import json
from pathlib import Path

# ---------- Load Excel ---------- #
file_path = "Output/Coating_combined.xlsx"
df = pd.read_excel(file_path)

# Drop rows without Route Id
df = df.dropna(subset=["Route Id"])

# ✅ Derive Full Article from Item Id (characters after first 4)
df["Item Id"] = df["Item Id"].astype(str)
df["full_article"] = df["Item Id"].str[4:]  # e.g., BWPP8228FT → 8228FT

# ✅ Extract only numeric part as article
df["article"] = df["full_article"].str.extract(r"(\d+)")[0]


# Map Opr Id to readable Stage
def map_stage(val):
    mapping = {
        "CAL": "Calendaring",
        "Fns": "Finishing",
        "Cur": "Curing",
        "Scou": "Scouring",
        "Dy": "Dyeing and Washing",
        "Was": "Dyeing and Washing",
        "Coat": "Coating",
        "cal1": "Calendaring",
        "coat1": "Coating",
        "dy,was": "Dyeing and Washing",
        "Dy,Was": "Dyeing and Washing",
        "Coat1": "Coating",
        "CAL1": "Calendaring",
    }
    return mapping.get(str(val).strip(), str(val))


df["Stage"] = df["Opr Id"].map(map_stage)

# Rename Config ID and Dim2
df["Coating type"] = df["Config ID"]
df["Finishing done before coating"] = df["Dim2"]

# Grouping
grouped = df.groupby(["Route Id", "Stage", "article", "full_article"])
output_data = []

for (route_id, stage, article, full_article), group in grouped:
    parameters = {}
    sentence_parts = []

    coating_type = (
        group["Coating type"].dropna().iloc[0]
        if not group["Coating type"].dropna().empty
        else ""
    )
    finish_before = (
        group["Finishing done before coating"].dropna().iloc[0]
        if not group["Finishing done before coating"].dropna().empty
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
            value_str += (
                f"{unit}" if "%" not in str(value_str) and "%" in str(unit) else ""
            )

        parameters[name] = value_str
        sentence_parts.append(f"{name} is set to {value_str}")

    # Article reference sentence
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
        "operation": stage,
        "sheet": "Coating",
        "coating type": coating_type,
        "finishing done before coating": finish_before,
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
output_path = Path("rag_ready_coating.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False, default=convert)

print(f"✅ Coating RAG JSON saved to {output_path}")
print(f"📊 Total Chunks: {len(output_data)}")
