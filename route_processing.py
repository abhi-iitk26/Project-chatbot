import pandas as pd
import numpy as np
import json
import re
from pathlib import Path

# ---------- Load Excel ---------- #
file_path = "Output/Processing_combined.xlsx"
df = pd.read_excel(file_path)
df = df.dropna(subset=["Route Id"])

# Extract article from Item Id
df["Item Id"] = df["Item Id"].astype(str)
df["full_article"] = df["Item Id"].str[4:]
df["article"] = df["full_article"].str.extract(r"(\d+)")[0]

# Rename for metadata
df["calendaring_details"] = df["Config ID"]
df["finishing_details_after_processing"] = df["Dim2"]

# Extract machine name from Route Name (inside parentheses)
df["machine_used_in_processing"] = (
    df["Route Name"]
    .astype(str)
    .apply(lambda x: re.findall(r"\((.*?)\)", x)[0] if "(" in x and ")" in x else "")
)

# ---------- Stage Mapping ---------- #
stage_map = {
    "Sco,Was": "scouring and washing",
    "AGE": "Ageing",
    "Age": "Ageing",
    "SC,DY,WH": "scouring, drying and washing",
    "CAL1": "calendering",
    "CAL2": "calendering",
    "CAL3": "calendering",
    "Cal1": "calendering",
    "Cal2": "calendering",
    "Cal3": "calendering",
    "Cur": "Curing",
    "Fns": "Finishing",
    "Dy,Was": "dye wash",
    "Dry": "Drying",
    "AGE": "Ageing",
    "Scou": "scouring",
    "Was PTG": "print wash",
    "ptg": "printing",
    "sc,dy,wh": "scouring, drying and washing",
    "Sc,Dy,Wh": "scouring, drying and washing",
    "sco,dye": "scouring and dyeing",
    "Dry PTG": "dry print",
    "scou-bo": "scouring",
    "was": "washing",
    "Was": "washing",
    "was ptg": "washing print",
    "dy,was": "dye wash",
    "Dy,Was": "dye wash",
    "dry ptg": "dry print",
    "dy,was": "dye wash",
    "Sco,Dye": "scouring and dyeing",
    "Scou-BO": "scouring",
}
df["Stage"] = df["Opr Id"].map(stage_map).fillna(df["Opr Id"])

""
# Set preferred types
preferred_types = {
    t.strip().lower()
    for t in [
        "Manzel Washer",
        "Menzel Washer",
        "Stenter Drying",
        "STENTER HEAT SET",
        "Jigger",
        "STENTER FINISHING",
        "CALENDARING",
        "STenter Curing",
    ]
}

# ---------- Group by Route Id and Opr Id ---------- #

# ---------- Group by Route Id, Opr Id, Stage, article, full_article ---------- #
grouped = df.groupby(["Route Id", "Opr Id", "Stage", "article", "full_article"])
output_data = []

for (route_id, opr_id, stage, article, full_article), group in grouped:
    calendar = (
        group["calendaring_details"].dropna().iloc[0]
        if not group["calendaring_details"].dropna().empty
        else ""
    )
    finish_detail = (
        group["finishing_details_after_processing"].dropna().iloc[0]
        if not group["finishing_details_after_processing"].dropna().empty
        else ""
    )
    machine = (
        group["machine_used_in_processing"].dropna().iloc[0]
        if not group["machine_used_in_processing"].dropna().empty
        else ""
    )

    parameters = {}
    sentence_parts = []

    for _, row in group.iterrows():
        param_type = str(row.get("Parameter Type", "")).strip()
        name = str(row.get("Name", "")).strip()
        min_val = row.get("Standard Min")
        max_val = row.get("Standard Max")
        unit = row.get("Unit")

        if pd.isna(min_val) and pd.isna(max_val):
            continue

        # Build value string
        if not pd.isna(min_val) and not pd.isna(max_val):
            value = (
                f"{min_val}"
                if str(min_val) == str(max_val)
                else f"{min_val} to {max_val}"
            )
        elif not pd.isna(min_val):
            value = f"{min_val}"
        elif not pd.isna(max_val):
            value = f"{max_val}"
        else:
            continue

        # Add unit if valid
        if pd.notna(unit) and isinstance(unit, str) and unit.strip():
            if "%" not in value and "%" in unit:
                value += unit
            else:
                value += f" {unit}"

        # Choose key
        if param_type.lower() in preferred_types and name:
            key = name
        else:
            key = param_type

        if key:
            parameters[key] = value
            sentence_parts.append(f"{key} is set to {value}")

    # Final content
    article_mention = (
        f"{full_article} or {article}" if full_article != article else article
    )
    content = (
        f"Article {article_mention} goes through stage {stage} with parameters: "
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
        "stage": stage,
        "sheet": "Processing",
        "calendaring details": calendar,
        "finishing details after processing": finish_detail,
        "machine used in processing": machine,
        **parameters,
    }

    output_data.append({"content": content, "metadata": metadata})


# ---------- JSON Serialization Fix ---------- #
def convert(obj):
    if isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return str(obj)


# ---------- Save Output ---------- #
output_path = Path("rag_ready_processing.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False, default=convert)

print(f"✅ Processing JSON saved to {output_path}")
print(f"📦 Total Chunks: {len(output_data)}")
