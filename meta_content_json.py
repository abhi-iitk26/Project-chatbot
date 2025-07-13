import json
from collections import defaultdict

CHUNK_FILE = "all_combined_chunks.json"
OUTPUT_FILE = "process_config.py"  # ✅ Output file path

with open(CHUNK_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

process_params = defaultdict(set)
all_metadata_keys = set()

for chunk in chunks:
    meta = chunk.get("metadata", {})
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            continue

    # ✅ Fetch process name from 'stage' or 'operation'
    stage = meta.get("stage") or meta.get("operation")
    if not stage:
        continue
    stage = stage.lower().strip()

    for key in meta.keys():
        # ✅ Ignore general or non-parameter keys
        if key.lower() in [
            "article",
            "design_name",
            "item id",
            "item_id",
            "route name",
            "stage",
            "operation",
        ]:
            continue

        all_metadata_keys.add(key)
        process_params[stage].add(key.strip().lower())

# ✅ Write to Python file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    # Write process names
    f.write("PROCESS_NAMES = [\n")
    for stage in sorted(process_params):
        f.write(f'    "{stage}",\n')
    f.write("]\n\n")

    # Write process parameters
    f.write("PROCESS_PARAMETERS = {\n")
    for stage in sorted(process_params):
        params = sorted(process_params[stage])
        params_str = ", ".join(f'"{p}"' for p in params)
        f.write(f'    "{stage}": [{params_str}],\n')
    f.write("}\n")

print(f"✅ Output written to: {OUTPUT_FILE}")
