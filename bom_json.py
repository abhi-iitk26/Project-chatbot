import pandas as pd
import json
import re

# ---------- CONFIGURATION ---------- #
file_path = "bom_Grouped_By_Process.xlsx"
output_path = "structured_bom_data.json"

# ---------- LOAD SHEETS ---------- #
xls = pd.ExcelFile(file_path)
sheet_names = [s for s in xls.sheet_names if s.startswith("Cleaned_")]
warp_df = pd.read_excel(xls, sheet_name="Cleaned_Warping")
griege_df = pd.read_excel(xls, sheet_name="Cleaned_Griege")

warp_df.columns = warp_df.columns.str.strip()
griege_df.columns = griege_df.columns.str.strip()
for df in (warp_df, griege_df):
    df["Article_No"] = df["Article_No"].astype(str).str.strip()

# ---------- ONE-TO-ONE MERGE ---------- #
warp_df_grouped = warp_df.groupby("Article_No").first().reset_index()
griege_df_grouped = griege_df.groupby("Article_No").first().reset_index()

merged = pd.merge(
    warp_df_grouped,
    griege_df_grouped,
    on=["Article_No"],
    how="inner",
    suffixes=("_warp", "_weft")
)
print(f"✅ One-to-one merged Warp-Griege records: {len(merged)}")

# ---------- CREATE MERGED CHUNKS ---------- #
merged_chunks = []
for i, row in merged.iterrows():
    full_art = str(row["Article_No"])
    art_match = re.match(r"\d{4}", full_art)
    art = art_match.group(0) if art_match else full_art
    cid = f"Warping_Griege_{full_art}"

    wd = row.get("Warp Denier", "unknown")
    wefd = row.get("Weft Denier", "unknown")
    wt = row.get("Number of twist in Warp yarn", "unknown")
    wet = row.get("Number of twist in Weft yarn", "unknown")

    intro = (
        f"For article {full_art}, the warp yarn denier is {wd} and weft yarn denier is {wefd}; "
        f"the warp yarn twist is {wt} and the weft yarn twist is {wet}."
    )

    kv_lines = []
    for col in merged.columns:
        val = row[col]
        if pd.notna(val) and str(val).strip():
            col_name = col.replace("_warp", "").replace("_weft", "").strip()
            val_str = str(val).strip()
            kv_lines.append(f"{col_name} is {val_str}")
    kv_block = "; ".join(kv_lines) + "."
    content = intro + " Additional parameters recorded are: " + kv_block

    metadata = {
        col: str(row[col]).strip()
        for col in merged.columns
        if pd.notna(row[col]) and str(row[col]).strip()
    }

    # 🔁 Add normalized and full article mapping
    metadata["full_article"] = full_art
    for k in ["article", "article_no", "article number", "quality number", "fabric"]:
        metadata[k] = art

    merged_chunks.append({
        "chunk_id": cid,
        "sheet": "Warp and Weft Yarn details",
        "article": art,
        "content": content,
        "metadata": metadata
    })

# ---------- PROCESS OTHER SHEETS (AS-IS) ---------- #
def row_to_chunk(row, sheet, idx):
    meta = {}
    parts = []
    for c, v in row.items():
        if pd.notna(v) and str(v).strip():
            vs = str(v).strip()
            meta[c.strip()] = vs
            parts.append(f"{c.strip()} is {vs}")
    full_art = meta.get("Article_No", f"UNKNOWN_{idx}")
    art_match = re.match(r"\d{4}", full_art)
    art = art_match.group(0) if art_match else full_art

    meta["full_article"] = full_art
    for k in ["article", "article no", "article_no", "fabric"]:
        meta[k] = art

    return {
        "chunk_id": f"{sheet}_{full_art}_{idx}",
        "sheet": sheet,
        "article": art,
        "content": f"In the {sheet} process of article {full_art}, the following parameters were recorded: " + "; ".join(parts) + ".",
        "metadata": meta
    }

other_chunks = []
for s in sheet_names:
    if s not in ("Cleaned_Warping", "Cleaned_Griege"):
        df = pd.read_excel(xls, sheet_name=s)
        df.columns = df.columns.str.strip()
        sheet_key = s.replace("Cleaned_", "")
        for idx, row in df.iterrows():
            other_chunks.append(row_to_chunk(row, sheet_key, idx + 1))

# ---------- SAVE FINAL JSON ---------- #
all_chunks = merged_chunks + other_chunks
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, indent=2, ensure_ascii=False)

print(f"✅ Final total chunks: {len(all_chunks)} saved to '{output_path}'")
