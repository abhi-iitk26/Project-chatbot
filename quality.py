import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

# ------------------ Configuration ------------------ #
INPUT_FILE = "merged_BOM_quality.xlsx"
OUTPUT_FILE = "processed_BOM_quality.xlsx"

print("🚀 Starting Simple BOM Quality Processor...")

# Check if input exists
if not os.path.exists(INPUT_FILE):
    print(f"❌ File not found: {INPUT_FILE}")
    exit()

# ------------------ Constants ------------------ #
FIBRE_MAP = {
    'M': "Nylon 6", 'N': "Nylon 66", 'L': "Poly Propylene", 'P': "Polyester",
    'E': "Spun Polyester", 'V': "Viscose Rayon", 'T': "Polyester Cotton", 'R': "Para Aramid",
    'A': "Meta Aramid", 'C': "Cotton", 'B': "Dimetrol", 'D': "Nylon Cotton",
    'Z': "Nylon Spandex", 'G': "Polyester Viscose", 'H': "Spun Poly Propylene",
    'S': "Polyester Spandex", 'U': "Spun Viscose Rayon", 'Y': "Spun Acrylic",
    'F': "Recycled Polyester Spandex", 'I': "PTT", 'J': "PTT stretch",
    'X': "Aromatic Polyester (ARP - Vectran)", 'K': "Nylon 06 Spandex", 'Q': "Glass Fibre"
}

STAGE_MAP = {
    'G': 'Griege', 'P': 'Processing', 'C': 'Coating', 'D': 'Printing'
}

# ------------------ Simple Extract Function ------------------ #
def extract_info(item):
    """Simple extraction function"""
    try:
        if pd.isna(item):
            return "", "Unknown", "Unknown", "Unknown"
        
        item = str(item).strip()
        if len(item) < 4:
            return item, "Unknown", "Unknown", "Unknown"
        
        # Article & Stage
        if item[0].isdigit():
            article, stage = item, "Yarn Article"
        else:
            stage = STAGE_MAP.get(item[0].upper(), "Unknown")
            article = item[4:] if len(item) > 4 else item
        
        # Fibres
        warp = FIBRE_MAP.get(item[2].upper(), "Unknown") if len(item) >= 3 else "Unknown"
        weft = FIBRE_MAP.get(item[3].upper(), "Unknown") if len(item) >= 4 else "Unknown"
        
        return article, stage, warp, weft
    except:
        return str(item), "Unknown", "Unknown", "Unknown"

# ------------------ Main Processing ------------------ #
print("📖 Reading input file...")

try:
    # Read all sheets at once
    all_sheets = pd.read_excel(INPUT_FILE, sheet_name=None, engine='openpyxl')
    print(f"✅ Found {len(all_sheets)} sheets")
    
    # Combine all sheets
    all_data = []
    for sheet_name, df in all_sheets.items():
        if len(df) > 0 and 'Item number' in df.columns:
            df['source_sheet'] = sheet_name
            all_data.append(df)
            print(f"   📋 {sheet_name}: {len(df)} rows")
    
    if not all_data:
        print("❌ No valid data found!")
        exit()
    
    # Combine everything
    print("\n🔗 Combining all data...")
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"✅ Total rows: {len(combined_df)}")
    
    # Process Item numbers (vectorized for speed)
    print("\n🔄 Processing items...")
    items = combined_df['Item number'].fillna('')
    
    # Extract info for all items at once
    extracted = [extract_info(item) for item in items]
    articles, stages, warps, wefts = zip(*extracted)
    
    # Add new columns
    combined_df['article Number'] = articles
    combined_df['stage name'] = stages
    combined_df['warp fibre'] = warps
    combined_df['weft fibre'] = wefts
    
    print(f"✅ Processing completed!")
    
    # ------------------ Save Results ------------------ #
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        # Save all data
        combined_df.to_excel(writer, index=False, sheet_name="All_Data")
        
        # Save by stages (only valid ones)
        valid_stages = [s for s in combined_df['stage name'].unique() 
                       if s not in ['Yarn Article', 'Unknown'] and 'Unknown' not in s]
        
        saved_count = 0
        for stage in valid_stages:
            stage_df = combined_df[combined_df['stage name'] == stage]
            if len(stage_df) > 0:
                sheet_name = stage.replace(' ', '_')[:31]
                stage_df.to_excel(writer, index=False, sheet_name=sheet_name)
                saved_count += len(stage_df)
                print(f"   📋 {sheet_name}: {len(stage_df)} records")
    
    # ------------------ Summary ------------------ #
    print(f"\n🎉 SUCCESS!")
    print(f"📊 Summary:")
    print(f"   Total Records: {len(combined_df)}")
    print(f"   Valid Stage Records: {saved_count}")
    print(f"   Output File: {OUTPUT_FILE}")
    
    # Show stage breakdown
    stage_counts = combined_df['stage name'].value_counts()
    print(f"\n📈 Stage Breakdown:")
    for stage, count in stage_counts.head(10).items():
        print(f"   {stage}: {count}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Done!")