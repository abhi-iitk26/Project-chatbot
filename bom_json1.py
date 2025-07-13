import json
from pathlib import Path

# ---------- CONFIG ---------- #
input_path = Path("structured_bom_data.json")  # Input file
output_path = Path("structured_bom_data_final.json")  # Output file

# ---------- STEP 1: Load JSON ---------- #
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- STEP 2: Process Each Chunk ---------- #
for chunk in data:
    # Clean article number (remove .0)
    article_raw = str(chunk.get("article", "")).strip()
    article_clean = (
        article_raw.replace(".0", "") if article_raw.endswith(".0") else article_raw
    )
    chunk["article"] = article_clean

    # Clean chunk_id
    if "chunk_id" in chunk:
        chunk["chunk_id"] = chunk["chunk_id"].replace(".0", "")

    # Clean metadata article-related keys
    if "metadata" in chunk:
        article_keys = [
            "Article_No",
            "article",
            "article no",
            "article number",
            "article_no",
            "article_no.",
            "article_number",
            "quality_number",
            "quality no",
            "fabric",
            "operation",
        ]
        for key in article_keys:
            if key in chunk["metadata"]:
                val = str(chunk["metadata"][key]).strip()
                chunk["metadata"][key] = (
                    val.replace(".0", "") if val.endswith(".0") else val
                )

        # ✅ Add or update "operation" equal to sheet value
        sheet_val = chunk.get("sheet", "").strip()
        chunk["metadata"]["operation"] = sheet_val

    # Clean content field (article number in sentence)
    if "content" in chunk:
        chunk["content"] = chunk["content"].replace(f"{article_clean}.0", article_clean)

    # Rename Griege sheet and chunk_id to Weft
    if chunk.get("sheet", "").lower() == "griege" or chunk.get(
        "chunk_id", ""
    ).lower().startswith("griege"):
        chunk["chunk_id"] = (
            chunk["chunk_id"].replace("Griege", "Weft").replace("griege", "Weft")
        )
        chunk["sheet"] = "Weft"
        if "metadata" in chunk:
            chunk["metadata"]["process"] = "Weft"
            chunk["metadata"][
                "operation"
            ] = "Weft"  # ✅ Also update operation after renaming

# ---------- STEP 3: Save Updated JSON ---------- #
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Updated JSON saved to: {output_path}")
