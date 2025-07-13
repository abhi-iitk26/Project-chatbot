import os
import json
import re
from typing import List, Dict, Any

# ------------ File Paths ------------ #
ROUTE_FILES = [
    "rag_ready_beaming.json",
    "rag_ready_coating.json",
    "rag_ready_direct_warping.json",
    "rag_ready_griege.json",
    "rag_ready_printing.json",
    "rag_ready_processing.json",
    "rag_ready_sectional_warping_complete.json",
]

BOM_FILE = "structured_bom_data_final.json"
QUALITY_FILE = "all_quality_chunks.json"
OUTPUT_FILE = "all_combined_chunks.json"

# ------------ Dictionary for Mapping ------------ #
short_to_full = {
    "AB": "Anti Bacterial",
    "MMT": "Moisture Management",
    "SI": "Silicon",
    "KT": "Knitted",
    "RS": "Rib Stop",
    "": "NA",
    "LN": "Leno",
    "HB": "Hucka Back",
    "CH": "Chain Weave",
    "WHCTNIL": "WHCTNIL",
    "RB": "Rib Stop",
    "OT": "OT",
    "MT": "Matt Weave",
    "FDYFLT": "FDYFLT",
    "K-": "Printing Screen",
    "ACS": "Acrylic Solvent Based",
    "ATYATY": "ATY",
    "O-": "O",
    "NBBKLAM": "Non Breathable Black Thermoplastic Polyurethane Lamination",
    "FBLAM": "Lamination",
    "RFL": "RFL",
    "LAM": "Lamination",
    "HBWLAM": "High Breathable White Polyurethane Lamination",
    "INAM": "INAM",
    "SIEL": "SIEL",
    "KU-/C": "KU-/C",
    "PVC": "PVC",
    "Layer Lam": "Layer Lamination",
    "FDYTWI": "FDYTWI",
    "TWITWI": "TWITWI",
    "AC+SLC": "Acrlyic",
    "DTYNIM": "DTYNIM",
    "DTYHIM": "DTYHIM",
    "HBTLAM": "High Breathable Thermoplastic Polyurethane Lamination",
    "LLAM": "Layer Lamination",
    "Blotch": "Blotch",
    "LWLAM": "Lamination",
    "WHFDNIL": "Shade Full Dull Nil",
    "MTM": "Moisture Management",
    "PR": "Prime Finish",
    "EL": "EL 40 Finish",
    "DSCPU": "Polyurethane",
    "NILL": "Nil",
    "EL-": "EL 40 Finish",
    "LPE": "Levofin PE",
    "AC": "Acrylic Coating",
    "PUS": "Polyurethane Solvent",
    "PU": "Polyurethane",
    "PUPVC": "Polyurethane PVC",
    "DSPU": "Polyurethane",
    "TPULAM": "Thermoplastic Polyurethane Lamination",
    "HMPU": "Hot Melt Polyurethane",
    "BRPUW": "Breathable Polyurethane",
    "BRPU": "Breathable Polyurethane",
    "PRPU": "Prime Polyurethane",
    "LAMNBTPU": "Non Breathable Thermoplastic Polyurethane Lamination",
    "SIPU": "Silicon Polyurethane",
    "PU+SLC": "Polyurethane",
    "WBPU": "Water Based Polyurethane",
    "SLPU": "Sealable Polyurethane",
    "NLBRNIL": "Shade Bright Nil",
    "BKBRNIL": "Shade Bright Nil",
    "YGBRNIL": "Shade Bright Nil",
    "JBKSDNIL": "Shade Semi Dull Nil",
    "YLBRNIL": "Shade Bright Nil",
    "GNBRNIL": "Shade Bright Nil",
    "WHSDNIL": "Shade Semi Dull Nil",
    "BRBRNIL": "Shade Bright Nil",
    "ORBRNIL": "Shade Bright Nil",
    "NIL": "Nil",
    "WR": "Water Repellent",
    "PL": "Plain",
    "TW": "Twill",
    "WRWP": "Water Repellent Water Proofness",
    "WRCL": "Water Repellent Calendar",
    "DB": "Dobby",
    "WHBRNIL": "Shade Bright Nil",
    "SIWROR": "Silicon Water Repellent Oil Repellent",
    "WRSI": "Water Repellent Silicon",
    "WRST": "Water Repellent Stiff",
    "FRWRCL": "Flame Retardant Water Repellent Calendar",
    "ST": "Stiff",
    "WROR": "Water Repellent Oil Repellent",
    "FRWR": "Flame Retardant Water Repellent",
    "FR": "Flame Retardant",
    "WRFR": "Flame Retardant Water Repellent",
    "WRAMB": "Water Repellent Anti Microbial",
    "DWR": "Durable Water Repellent",
    "DWRCL": "Durable Water Repellent Calendar",
    "IRRDWR": "Durable Water Repellent",
    "WR/NIL": "Water Repellent",
    "CL": "Calendar",
    "ACL": "Calendar",
    "SICL": "Silicon Calendar",
    "WR+": "Water Repellent",
    "CLDWR": "Durable Water Repellent Calendar",
    "WRAS": "Water Repellent Anti Static",
    "DWRDCL": "Durable Water Repellent Calendar",
    "OWR": "Water Repellent Oil Repellent",
    "AMWR": "Water Repellent Anti Microbial",
    "WRORST": "Water Repellent Oil Repellent Stiff",
    "OWRST": "Water Repellent Oil Repellent Stiff",
    "Non Sized": "Non Sized",
    "WLD CL": "Calendar",
    "FRPUAB": "Flame Retardant Poly Urethane Anti Microbial",
    "Sized": "Sized",
    "Acrylic Sized": "Acrylic Sized",
    "Acrylic Sized KANANI": "Acrylic Sized",
    "FRPU": "Flame Retardant Poly Urethane",
    "DW Acrylic Sized": "Acrylic Sized",
    "DCL": "Calendar",
    "Unsized": "Non Sized",
    "Polyester Sized": "Polyester Sized",
    "NONSIZE": "Non Sized",
    "Acrylic Sized Draw Kanani": "Acrylic Sized",
    "Acrylic Sized/DW": "Acrylic Sized",
}


# ------------ Text Replacer ------------ #
def replace_short_forms_in_text(text: str, mapping: Dict[str, str]) -> str:
    for short, full in mapping.items():
        if short:
            pattern = r"\b" + re.escape(short) + r"\b"
            text = re.sub(pattern, full, text)
    return text


# ------------ Helper Functions ------------ #
def load_json_file(filepath: str, source_tag: str) -> List[Dict[str, Any]]:
    with open(filepath, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

        if isinstance(raw_data, dict) and "chunks" in raw_data:
            raw_data = raw_data["chunks"]

        cleaned = []
        for d in raw_data:
            if isinstance(d, dict):
                if "metadata" not in d:
                    d["metadata"] = {}
                d["metadata"]["source"] = source_tag

                # Replace short forms in content
                if "content" in d and isinstance(d["content"], str):
                    d["content"] = replace_short_forms_in_text(
                        d["content"], short_to_full
                    )

                # Replace short forms in metadata values
                for key, value in d["metadata"].items():
                    if isinstance(value, str):
                        d["metadata"][key] = replace_short_forms_in_text(
                            value, short_to_full
                        )

                # ✅ Add "same" field to metadata
                article = d["metadata"].get("Article_No") or d["metadata"].get(
                    "article"
                )
                if article:
                    d["metadata"]["same"] = f"of article {article}"

                cleaned.append(d)
            else:
                print(f"⚠️ Skipped invalid item in {filepath}: {type(d)}")
        return cleaned


def load_all_chunks() -> List[Dict[str, Any]]:
    all_chunks = []
    print("🔍 Loading chunks from Route, BOM, and Quality JSONs...")
    for route_file in ROUTE_FILES:
        chunks = load_json_file(route_file, source_tag="Route")
        all_chunks.extend(chunks)
        print(f"📄 Loaded {len(chunks)} from {route_file}")

    bom_chunks = load_json_file(BOM_FILE, source_tag="BOM")
    all_chunks.extend(bom_chunks)
    print(f"📄 Loaded from BOM")

    quality_chunks = load_json_file(QUALITY_FILE, source_tag="Quality")
    all_chunks.extend(quality_chunks)
    print(f"📄 Loaded from Quality")

    return all_chunks


# ------------ Main Execution ------------ #
if __name__ == "__main__":
    all_chunks = load_all_chunks()
    print(f"✅ Total combined chunks: {len(all_chunks)}")

    unique_articles = set()
    for chunk in all_chunks:
        article_no = chunk.get("metadata", {}).get("Article_No") or chunk.get(
            "metadata", {}
        ).get("article")
        if article_no:
            unique_articles.add(article_no)
    print(f"🔢 Total unique articles: {len(unique_articles)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"💾 Combined chunks saved to: {OUTPUT_FILE}")
