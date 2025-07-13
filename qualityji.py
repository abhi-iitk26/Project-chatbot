import pandas as pd
import re
from typing import Optional, Dict, List, Tuple
from functools import lru_cache


class TestNameRenamer:
    """Optimized test name renamer with cached patterns and unified processing"""

    def __init__(self):
        # Compile regex patterns once for better performance
        self.patterns = {
            "air_permeability": re.compile(r"AP@([\w\s/]+)\s*\(([^)]+)\)"),
            "abrasion": re.compile(r"Resi[s\.]*\.?([\w\s]+)?/(\d+Kpa)", re.IGNORECASE),
            "abrasion_pressure": re.compile(r"(\d+Kpa)"),
            "abrasion_cycles": re.compile(r"cycles?-?([\d,]+)", re.IGNORECASE),
            "breaking_strength": re.compile(
                r"BS-(Wp|Wt|Yarn)\s*([a-zA-Z/]+)?", re.IGNORECASE
            ),
            "bursting_strength": re.compile(
                r"Burst St\s+([a-zA-Z0-9/²]+)", re.IGNORECASE
            ),
            "colour_fastness": re.compile(r"CF-(.+)"),
            "de_values": re.compile(r"DE Values-(.+)"),
            "thickness": re.compile(r"Thick\s+([^\s()]+)(?:\s+\(([^)]+)\))?"),
            "thread_count": re.compile(
                r"Thrd Count-([Ww][pt])\s*([^\s()]+)?(?:\s+\(([^)]+)\))?"
            ),
            "wicking_minutes": re.compile(r"after(\d+)min", re.IGNORECASE),
            "wp_conditions": re.compile(r"\((.*?)\)"),
            "wp_temp": re.compile(r"(\d+)\s*c", re.IGNORECASE),
            "wp_time": re.compile(r"(\d+)(sec|s|m|h)", re.IGNORECASE),
            "wp_pressure": re.compile(r"(\d*\.?\d+)\s*(bar|pa|mm|cm)", re.IGNORECASE),
        }

        # Colour fastness mapping for better performance
        self.cf_replacements = {
            "Rub-Dry": "Colourfastness to Rubbing (Dry)",
            "Rub-Wet": "Colourfastness to Rubbing (Wet)",
            "Wash-Ch in Shade": "Colourfastness to Washing Change in Shade",
            "Wash-St on": "Colourfastness to Washing Staining on",
            "Water-Ch in Shade": "Colourfastness to Water Change in Shade",
            "Water-St on": "Colourfastness to Water Staining on",
            "Sea Water-Ch in Shade": "Colourfastness to Sea Water Change in Shade",
            "Sea Water-St on": "Colourfastness to Sea Water Staining on",
            "Pers-Acid-Ch in Shade": "Colourfastness to Perspiration (Acid) Change in Shade",
            "Pers-Acid-St on": "Colourfastness to Perspiration (Acid) Staining on",
            "Pers-Alkaline-Ch in Shade": "Colourfastness to Perspiration (Alkaline) Change in Shade",
            "Pers-Alkaline-St on": "Colourfastness to Perspiration (Alkaline) Staining on",
            "Pers-Ch in Shade": "Colourfastness to Perspiration Change in Shade",
            "Pers-St on": "Colourfastness to Perspiration Staining on",
        }

        # Sheet prefix mapping
        self.prefix_map = {
            "Griege": "Grey",
            "Processing": "Processed",
            "Printing": "Printed",
            "Coating": "Coated",
        }

    @lru_cache(maxsize=1000)
    def rename_test_name(self, test_name: str, sheet_name: Optional[str] = None) -> str:
        """Main function to rename test names with caching for performance"""
        if pd.isna(test_name) or test_name == "":
            return test_name

        test_name = str(test_name).strip()
        original_test_name = test_name

        # Route to appropriate parser based on prefix
        result = self._route_to_parser(test_name)

        # Add sheet-based prefix if applicable
        if sheet_name and sheet_name in self.prefix_map:
            prefix = self.prefix_map[sheet_name]
            if not result.startswith("[Unmapped]"):
                result = f"{prefix} {result}"

        return result if not result.startswith("[Unmapped]") else original_test_name

    def _route_to_parser(self, test_name: str) -> str:
        """Route test name to appropriate parser function"""
        test_lower = test_name.lower()

        # Use a mapping for better performance than multiple if-elif chains
        parser_map = [
            ("AP@", self._parse_air_permeability),
            ("%Elong", self._parse_fabric_elongation),
            ("BS-", self._parse_breaking_strength),
            ("Burst St", self._parse_bursting_strength),
            ("CF", self._parse_colour_fastness),
            ("DE Values", self._parse_de_value),
            ("DS", self._parse_ds),
            ("TS-", self._parse_ts),
            ("Thick", self._parse_thickness),
            ("Thrd Count", self._parse_thread_count),
        ]

        # Check simple prefixes first
        for prefix, parser in parser_map:
            if test_name.startswith(prefix):
                return parser(test_name)

        # Check special cases
        if test_lower == "cf to light":
            return "Colour fastness to light"
        elif any(
            test_lower.startswith(x)
            for x in ["abra resi", "abra resis", "abra wool", "abrasion"]
        ):
            return self._parse_abrasion_test(test_name)
        elif "WP" in test_name and ("(" in test_name or "WeldZone" in test_name):
            return self._parse_wp_test(test_name)
        elif "Wicking" in test_name or "WH" in test_name:
            return self._parse_wicking_height(test_name)

        return f"[Unmapped] {test_name}"

    def _parse_air_permeability(self, test_name: str) -> str:
        match = self.patterns["air_permeability"].search(test_name)
        if match:
            pressure = match.group(1).strip()
            unit = match.group(2).strip()
            return f"Air permeability at {pressure} pressure in {unit}"
        return f"[Unmapped] {test_name}"

    def _parse_fabric_elongation(self, test_name: str) -> str:
        description = "Fabric elongation"

        if "-Wp" in test_name:
            description += " in warp direction"
        elif "-Wt" in test_name:
            description += " in weft direction"

        extra = re.sub(r"%Elong[-.]?", "", test_name).strip()
        if extra:
            description += f" ({extra.strip()})"

        return description.strip()

    def _parse_abrasion_test(self, test_name: str) -> str:
        """Optimized abrasion test parsing"""
        abradant_match = self.patterns["abrasion"].search(test_name)
        abradant = (
            abradant_match.group(1).strip()
            if abradant_match and abradant_match.group(1)
            else None
        )
        pressure = abradant_match.group(2) if abradant_match else None

        if not abradant and "wool" in test_name.lower():
            abradant = "Wool"

        if not pressure:
            pressure_match = self.patterns["abrasion_pressure"].search(test_name)
            pressure = (
                pressure_match.group(1) if pressure_match else "unspecified pressure"
            )

        cycle_match = self.patterns["abrasion_cycles"].search(test_name)
        cycles = (
            cycle_match.group(1).replace(",", "").strip()
            if cycle_match
            else ("1" if "cycle" in test_name.lower() else "unspecified number of")
        )

        abradant = abradant or "unspecified abradant"
        return (
            f"Abrasion resistance using {abradant} at {pressure} after {cycles} cycles"
        )

    def _parse_breaking_strength(self, test_name: str) -> str:
        match = self.patterns["breaking_strength"].match(test_name)
        if match:
            direction_map = {"wp": "Warp", "wt": "Weft", "yarn": "Yarn"}
            direction = direction_map.get(match.group(1).lower(), "Unknown")
            unit = match.group(2).strip() if match.group(2) else "unknown unit"
            return f"Breaking strength of {direction} in {unit}"
        return f"[Unmapped] {test_name}"

    def _parse_bursting_strength(self, test_name: str) -> str:
        match = self.patterns["bursting_strength"].match(test_name)
        if match:
            unit = match.group(1).strip().replace("cm2", "cm²")
            return f"Bursting strength in {unit}"
        return f"[Unmapped] {test_name}"

    def _parse_colour_fastness(self, test_name: str) -> str:
        match = self.patterns["colour_fastness"].match(test_name)
        if not match:
            return f"[Unmapped] {test_name}"

        descriptor = match.group(1)

        # Check direct mappings first
        for key, val in self.cf_replacements.items():
            if descriptor.startswith(key):
                material = descriptor.replace(key, "").strip().replace("-", " ")
                return f"{val} {material}".strip()

        # Handle warp/weft cases
        if descriptor in ["Rub-Dry-Wp", "Rub-Dry-Wt", "Rub-Wet-Wp", "Rub-Wet-Wt"]:
            side = "Warp" if "Wp" in descriptor else "Weft"
            condition = "Dry" if "Dry" in descriptor else "Wet"
            return f"Colourfastness to Rubbing ({condition}) on {side}"

        return f"[Unmapped] {test_name}"

    def _parse_de_value(self, test_name: str) -> str:
        if test_name.strip() == "DE Values":
            return "Delta E (ΔE) value"
        match = self.patterns["de_values"].match(test_name)
        return (
            f"Delta E (ΔE) under {match.group(1).strip()}"
            if match
            else f"[Unmapped] {test_name}"
        )

    def _parse_ds(self, test_name: str) -> str:
        """Dimensional stability parsing"""
        if "After" in test_name:
            washes_match = re.search(r"After (.+?) wash", test_name)
            if washes_match:
                washes = washes_match.group(1)
                direction = (
                    "warp"
                    if "-Wp" in test_name
                    else "weft" if "-Wt" in test_name else "unknown"
                )
                return f"Dimensional stability of {direction} after {washes} washes"

        # Water tests
        water_tests = {
            "Cold Water -Wp": "Dimensional stability of warp in cold water",
            "Cold Water -Wt": "Dimensional stability of weft in cold water",
            "Hot Water -Wp": "Dimensional stability of warp in hot water",
            "Hot Water -Wt": "Dimensional stability of weft in hot water",
            "Hot Water -Yarn": "Dimensional stability of yarn in hot water",
        }

        for pattern, description in water_tests.items():
            if pattern in test_name:
                return description

        # Heat tests
        if "to Heat" in test_name:
            heat_match = re.search(r"@ (.+?)-", test_name)
            temp_time = f" at {heat_match.group(1)}" if heat_match else ""

            if "-Wp" in test_name:
                return f"Dimensional stability of warp to heat{temp_time}"
            elif "-Wt" in test_name:
                return f"Dimensional stability of weft to heat{temp_time}"
            elif "-Yarn" in test_name:
                return f"Dimensional stability of yarn to heat{temp_time}"

        return f"[Unmapped] {test_name}"

    def _parse_ts(self, test_name: str) -> str:
        """Tear strength parsing"""
        unit = test_name.split()[-1] if " " in test_name else "Unknown unit"

        if test_name.startswith("TS-Elm-Wp"):
            return f"Tear strength of warp using Elmendorf method in {unit}"
        elif test_name.startswith("TS-Elm-Wt"):
            return f"Tear strength of weft using Elmendorf method in {unit}"
        elif test_name.startswith("TS-Wp"):
            return f"Tear strength of warp in {unit}"
        elif test_name.startswith("TS-Wt"):
            return f"Tear strength of weft in {unit}"

        return f"[Unmapped] {test_name}"

    def _parse_thickness(self, test_name: str) -> str:
        match = self.patterns["thickness"].match(test_name)
        if match:
            unit = match.group(1)
            note = match.group(2)
            return f"Thickness in {unit}" + (f" at {note}" if note else "")
        return f"[Unmapped] {test_name}"

    def _parse_thread_count(self, test_name: str) -> str:
        match = self.patterns["thread_count"].match(test_name)
        if match:
            direction = match.group(1).lower()
            unit = match.group(2) or "unspecified unit"
            extra = match.group(3)

            thread_type = "Ends" if direction == "wp" else "Picks"
            result = f"{thread_type} per {unit}"
            if extra:
                result += f" at {extra}"
            return result
        return f"[Unmapped] {test_name}"

    def _parse_wp_test(self, test_name: str) -> str:
        """Water proofness test parsing"""
        prefix = (
            "Water proofness of weld zone"
            if "WeldZone" in test_name
            else "Water proofness"
        )

        match = self.patterns["wp_conditions"].search(test_name)
        if match:
            inside = match.group(1).lower()

            temp_match = self.patterns["wp_temp"].search(inside)
            time_match = self.patterns["wp_time"].search(inside)
            pressure_match = self.patterns["wp_pressure"].search(inside)
            dynamic = "dynamic" in inside

            result = prefix
            if temp_match:
                result += f" tested at {temp_match.group(1)}°C"
            if time_match:
                unit_map = {
                    "sec": "seconds",
                    "s": "seconds",
                    "m": "minutes",
                    "h": "hour(s)",
                }
                unit = unit_map.get(time_match.group(2), time_match.group(2))
                result += f" for {time_match.group(1)} {unit}"
            elif pressure_match:
                result += f" with minimum pressure of {pressure_match.group(1)} {pressure_match.group(2)}"
            elif dynamic:
                result += " using dynamic method"
            return result
        return prefix

    def _parse_wicking_height(self, test_name: str) -> str:
        """Wicking height parsing"""
        test_clean = test_name.replace(" ", "").replace(".", "")
        method = "5xHL" if "5xHL" in test_clean.lower() else "original"

        direction = (
            "warp"
            if "-Wp" in test_name
            else "weft" if "-Wt" in test_name else "unknown"
        )

        minutes_match = self.patterns["wicking_minutes"].search(test_name)
        duration = f"after {minutes_match.group(1)} minutes" if minutes_match else ""

        return f"Wicking height using {method} method in {direction} direction {duration}".strip()

    def process_excel_file(self, file_path: str) -> None:
        """Process Excel file with optimized memory usage"""
        try:
            print(f"Reading Excel file: {file_path}")

            # Read sheet names without loading data
            with pd.ExcelFile(file_path) as xls:
                sheet_names = xls.sheet_names

            print(f"\nTotal sheets found: {len(sheet_names)}")
            output_path = file_path.replace(".xlsx", "_renamed.xlsx")

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for sheet_name in sheet_names:
                    print(f"Processing sheet: {sheet_name}")

                    # Read individual sheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)

                    # Skip All_Data sheet
                    if sheet_name == "All_Data":
                        print("  >> Skipped (preserved as-is)")
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        continue

                    # Skip if no Test column
                    if "Test" not in df.columns:
                        print("  >> 'Test' column not found, skipping")
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        continue

                    # Apply renaming with vectorized operation
                    original_tests = df["Test"].tolist()
                    df["Test"] = df["Test"].apply(
                        lambda x: self.rename_test_name(x, sheet_name)
                    )

                    # Write to output
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

                    # Show statistics
                    changed_count = sum(
                        1
                        for o, n in zip(original_tests, df["Test"])
                        if str(o) != str(n)
                    )
                    print(
                        f"  >> Renamed: {changed_count}, Unchanged: {len(df) - changed_count}"
                    )

                    # Show sample changes
                    if changed_count > 0:
                        print("  >> Sample changes:")
                        shown = 0
                        for o, n in zip(original_tests, df["Test"]):
                            if str(o) != str(n) and shown < 3:
                                print(f"     - Original: {o}")
                                print(f"     - Renamed : {n}")
                                shown += 1
                    print()

            print(f"✅ Output saved as: {output_path}")

        except Exception as e:
            print(f"❌ Error: {e}")


# Usage
if __name__ == "__main__":
    renamer = TestNameRenamer()
    file_path = "processed_BOM_quality_renamed.xlsx"
    print("Optimized Excel Test Renamer")
    print("=" * 40)
    renamer.process_excel_file(file_path)
