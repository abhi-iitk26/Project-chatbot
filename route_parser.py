import pandas as pd
import os
from pathlib import Path

# 📁 Step 1: Setup paths
data_folder = "Data"
output_folder = "Output"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# 📌 Step 2: Route type mapping (prefix to name)
route_type_map = {
    "RA": "Direct Warping",
    "RP": "Processing", 
    "RB": "Beaming",
    "RE": "Sectional Warping",
    "RG": "Griege",
    "RD": "Printing",
    "RC": "Coating"
}

# 🔑 Columns we want from Route sheets
columns_needed = ["Route Id", "Item Id", "Config ID", "Dim2", "Route Name"]

def process_single_file(input_file_path, file_number):
    """Process a single Excel file through all three steps"""
    
    print(f"\n🔄 Processing file: {input_file_path}")
    
    try:
        # =========================
        # STEP 1: Extract Route and Machine data
        # =========================
        print("  📖 Step 1: Reading Route and Machine sheets...")
        
        # 🔹 Read "Route" sheet
        route_df = pd.read_excel(input_file_path, sheet_name="Route", skiprows=1)

        # 🔹 Try reading "Machine Parameter", fallback to "Route Parameter"
        try:
            machine_df = pd.read_excel(input_file_path, sheet_name="Machine Parameter", skiprows=1)
        except:
            machine_df = pd.read_excel(input_file_path, sheet_name="Route Parameter", skiprows=1)

        # 🔹 Drop unnamed (empty) columns
        route_df = route_df.loc[:, ~route_df.columns.str.contains('^Unnamed')]
        machine_df = machine_df.loc[:, ~machine_df.columns.str.contains('^Unnamed')]

        # 🔹 Optional: Add source file name
        route_df["source_file"] = f"{file_number}.xlsx"
        machine_df["source_file"] = f"{file_number}.xlsx"

        # =========================
        # STEP 2: Split by route type
        # =========================
        print("  🔀 Step 2: Splitting by route types...")
        
        # 🛠 Extract prefix and map to type
        route_df["Route Type"] = route_df["Route Id"].str[:2].map(route_type_map)
        machine_df["Route Type"] = machine_df["Route Id"].str[:2].map(route_type_map)

        # =========================
        # STEP 3: Club route and machine data
        # =========================
        print("  🔗 Step 3: Clubbing Route and Machine data...")
        
        # Create final output file path
        final_output_file = os.path.join(output_folder, f"final_processed_{file_number}.xlsx")
        
        sheets_written = 0
        
        with pd.ExcelWriter(final_output_file) as writer:
            for prefix, type_name in route_type_map.items():
                try:
                    # Filter data by route type
                    route_subset = route_df[route_df["Route Type"] == type_name]
                    machine_subset = machine_df[machine_df["Route Type"] == type_name]
                    
                    if route_subset.empty or machine_subset.empty:
                        continue
                    
                    # ✅ Only keep columns that exist in route data
                    available_cols = [col for col in columns_needed if col in route_subset.columns]
                    
                    # 🛡️ Drop duplicate Route Ids to avoid row explosion
                    route_for_merge = route_subset[available_cols].drop_duplicates(subset="Route Id")
                    
                    # 🔁 Merge on Route Id
                    merged_df = machine_subset.merge(route_for_merge, on="Route Id", how="left")
                    
                    # 💾 Save to output (make sure name <= 31 chars)
                    sheet_name = f"{type_name} Data"[:31]
                    merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    sheets_written += 1
                    print(f"    ✅ Processed: {type_name}")
                    
                except Exception as e:
                    print(f"    ❌ Error processing {type_name}: {e}")
                    continue
            
            # ✨ Write info sheet if none processed
            if sheets_written == 0:
                pd.DataFrame({"Info": [f"No valid data found in file {file_number}.xlsx"]}).to_excel(
                    writer, sheet_name="Info", index=False)
        
        print(f"  🎉 File {file_number}.xlsx processed successfully!")
        print(f"  💾 Output saved: {final_output_file}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error processing file {file_number}.xlsx: {e}")
        return False

def main():
    """Main function to process all files in Data folder"""
    
    print("🚀 Starting batch processing of Excel files...")
    print(f"📂 Looking for files in: {data_folder}")
    
    # Check if Data folder exists
    if not os.path.exists(data_folder):
        print(f"❌ Error: '{data_folder}' folder not found!")
        return
    
    # Dictionary to store all data by route type
    all_data_by_type = {}
    for prefix, type_name in route_type_map.items():
        all_data_by_type[type_name] = []
    
    # Process files 1.xlsx to 28.xlsx
    successful_files = 0
    failed_files = 0
    
    for file_num in range(1, 29):  # 1 to 28
        input_file_path = os.path.join(data_folder, f"{file_num}.xlsx")
        
        # Check if file exists
        if os.path.exists(input_file_path):
            try:
                print(f"\n🔄 Processing file: {input_file_path}")
                
                # Read Route and Machine sheets
                route_df = pd.read_excel(input_file_path, sheet_name="Route", skiprows=1)
                try:
                    machine_df = pd.read_excel(input_file_path, sheet_name="Machine Parameter", skiprows=1)
                except:
                    machine_df = pd.read_excel(input_file_path, sheet_name="Route Parameter", skiprows=1)
                
                # Drop unnamed columns
                route_df = route_df.loc[:, ~route_df.columns.str.contains('^Unnamed')]
                machine_df = machine_df.loc[:, ~machine_df.columns.str.contains('^Unnamed')]
                
                # Add source file
                route_df["source_file"] = f"{file_num}.xlsx"
                machine_df["source_file"] = f"{file_num}.xlsx"
                
                # Add route type
                route_df["Route Type"] = route_df["Route Id"].str[:2].map(route_type_map)
                machine_df["Route Type"] = machine_df["Route Id"].str[:2].map(route_type_map)
                
                # Process each route type
                for prefix, type_name in route_type_map.items():
                    route_subset = route_df[route_df["Route Type"] == type_name]
                    machine_subset = machine_df[machine_df["Route Type"] == type_name]
                    
                    if not route_subset.empty and not machine_subset.empty:
                        # Get available columns
                        available_cols = [col for col in columns_needed if col in route_subset.columns]
                        route_for_merge = route_subset[available_cols].drop_duplicates(subset="Route Id")
                        
                        # Merge data
                        merged_df = machine_subset.merge(route_for_merge, on="Route Id", how="left")
                        all_data_by_type[type_name].append(merged_df)
                
                successful_files += 1
                print(f"  ✅ File {file_num}.xlsx processed successfully!")
                
            except Exception as e:
                print(f"  ❌ Error processing file {file_num}.xlsx: {e}")
                failed_files += 1
        else:
            print(f"⚠️  Warning: File {file_num}.xlsx not found, skipping...")
            failed_files += 1
    
    # Create final combined files
    print(f"\n🔗 Combining all data by route type...")
    for type_name, data_list in all_data_by_type.items():
        if data_list:
            combined_df = pd.concat(data_list, ignore_index=True)
            output_file = os.path.join(output_folder, f"{type_name}_combined.xlsx")
            combined_df.to_excel(output_file, index=False)
            print(f"  ✅ {type_name}: {len(combined_df)} rows saved to {type_name}_combined.xlsx")
    
    # Final summary
    print(f"\n" + "="*50)
    print(f"📊 PROCESSING SUMMARY")
    print(f"="*50)
    print(f"✅ Successfully processed: {successful_files} files")
    print(f"❌ Failed/Missing files: {failed_files} files")
    print(f"📁 Output files saved in: {output_folder}/")
    print(f"🎯 Total files attempted: 28")

if __name__ == "__main__":
    main()