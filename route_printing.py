import pandas as pd
import numpy as np
import json
import re
from pathlib import Path

# ---------- File Path ---------- #
file_path = "Output/Printing_combined.xlsx"
df = pd.read_excel(file_path).dropna(subset=["Route Id"])

# ---------- Extract Articles ---------- #
df["Item Id"] = df["Item Id"].astype(str)
df["full_article"] = df["Item Id"].str[4:]
df["article"] = df["full_article"].str.extract(r"(\d+)")[0]

# ---------- Other Fields ---------- #
df["design name"] = df["Config ID"]
df["finishing after printing"] = df["Dim2"]
df["machine used in processing"] = (
    df["Route Name"]
    .astype(str)
    .apply(lambda x: re.findall(r"\((.*?)\)", x)[0] if "(" in x and ")" in x else "")
)

# ---------- Stage Mapping ---------- #
stage_map = {
    "PTG": "Printing",
    "AGE": "Ageing",
    "Age": "Ageing",
    "Was PTG": "Print Wash",
    "PTG-1": "Printing",
    "PTG-2": "Printing",
    "Cur": "Curing",
    "Fns": "Finishing",
    "Was PTG ": "Print Wash",
    "Dry": "Drying",
    "AGE": "Ageing",
    "CAL1": "Calendaring",
    "dry ptg": "dry printing",
    "ptg-3": "Printing",
    "was ptg": "Print Wash",
    "Was": "print wash",
    "PTG-3": "Printing",
    "ptg": "Printing",
}
df["Stage"] = df["Opr Id"].map(stage_map).fillna(df["Opr Id"])

# ---------- Grouping ---------- #
grouped = df.groupby(["Route Id", "Stage", "article", "full_article"])
output_data = []

for (route_id, stage, article, full_article), group in grouped:
    design = (
        group["design name"].dropna().iloc[0]
        if not group["design name"].dropna().empty
        else ""
    )
    finish = (
        group["finishing after printing"].dropna().iloc[0]
        if not group["finishing after printing"].dropna().empty
        else ""
    )
    machine = (
        group["machine used in processing"].dropna().iloc[0]
        if not group["machine used in processing"].dropna().empty
        else ""
    )

    parameters = {}
    sentence_parts = []

    for _, row in group.iterrows():
        name = str(row.get("Name", "")).strip()
        min_val = row.get("Standard Min")
        max_val = row.get("Standard Max")
        unit = row.get("Unit")

        if pd.isna(name) or (pd.isna(min_val) and pd.isna(max_val)):
            continue

        if not pd.isna(min_val) and not pd.isna(max_val):
            value = f"{min_val}" if min_val == max_val else f"{min_val} to {max_val}"
        elif not pd.isna(min_val):
            value = f"{min_val}"
        elif not pd.isna(max_val):
            value = f"{max_val}"
        else:
            continue

        if pd.notna(unit) and isinstance(unit, str) and unit.strip():
            if "%" not in value and "%" in unit:
                value += unit
            else:
                value += f" {unit}"

        parameters[name] = value
        sentence_parts.append(f"{name} is set to {value}")

    article_mention = (
        f"{full_article} or {article}" if full_article != article else article
    )
    content = (
        f"Article {article_mention} goes through {stage} with parameters: "
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
        "sheet": "Printing",
        "design name": design,
        "finishing after printing": finish,
        "machine used in processing": machine,
        **parameters,
    }

    output_data.append({"content": content, "metadata": metadata})


# ---------- JSON Fix ---------- #
def convert(obj):
    if isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return str(obj)


# ---------- Save to File ---------- #
output_path = Path("rag_ready_printing.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False, default=convert)

print(f"✅ Printing JSON saved to {output_path}")
print(f"📦 Total chunks: {len(output_data)}")
