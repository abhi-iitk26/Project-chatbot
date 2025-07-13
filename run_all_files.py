import subprocess

files = [
    "bom.py",
    "bom_warpingsheet.py",
    "bom_processingsheet.py",
    "bom_coatingsheet.py",
    "bom_griege.py",
    "bom_json.py",
    "bom_json1.py",
    "quality_excel.py",
    "quality.py",
    "qualityji.py",
    "quality1.py",
    "route_parser.py",
    "route_beaming.py",
    "route_coating.py",
    "route_griege.py",
    "route_printing.py",
    "route_processing.py",
    "route_warpingd.py",
    "route_warpings.py",
    "chunk_generator_updated.py",
    "core_embedding.py",
]

for file in files:
    print(f"Running {file}...")
    result = subprocess.run(["python", file])
    if result.returncode != 0:
        print(f"{file} failed with exit code {result.returncode}")