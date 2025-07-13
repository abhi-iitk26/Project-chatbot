import pandas as pd
import json
import re
import tiktoken

tokenizer = tiktoken.get_encoding("cl100k_base")


input_file = "processed_BOM_quality_renamed.xlsx"
output_json = "all_quality_chunks.json"


# ------------ Token Counting Function ------------ #
def count_tokens(text):
    """Accurate token count using tiktoken (same as OpenAI models)"""
    if not text:
        return 0
    return len(tokenizer.encode(text))


def extract_numeric_article(article):
    """Extract only numeric part from article number"""
    import re

    # Remove all non-numeric characters and return only digits
    numeric_only = re.sub(r"[^0-9]", "", str(article))
    return numeric_only if numeric_only else str(article)


def extract_metadata_from_content(content, original_metadata):
    """Extract only the metadata parameters that are actually mentioned in the content"""
    filtered_metadata = {}

    # Always keep basic structure metadata
    basic_fields = [
        "article",
        "stage",
        "original_stage_name",
        "chunk_part",
        "is_split_chunk",
    ]
    for field in basic_fields:
        if field in original_metadata:
            filtered_metadata[field] = original_metadata[field]

    # Check for fiber information in content
    if "warp" in content.lower() and original_metadata.get("warp_fibre"):
        filtered_metadata["warp_fibre"] = original_metadata["warp_fibre"]
    if "weft" in content.lower() and original_metadata.get("weft_fibre"):
        filtered_metadata["weft_fibre"] = original_metadata["weft_fibre"]

    # Check for stage-specific parameters in content
    content_lower = content.lower()

    # Testing After Weaving specific
    if "sizing" in content_lower and original_metadata.get("sizing_details"):
        filtered_metadata["sizing_details"] = original_metadata["sizing_details"]
    if "weave" in content_lower and original_metadata.get("weave"):
        filtered_metadata["weave"] = original_metadata["weave"]

    # Testing After Processing specific
    if "calendaring" in content_lower and original_metadata.get("calendaring_details"):
        filtered_metadata["calendaring_details"] = original_metadata[
            "calendaring_details"
        ]
    if "shade" in content_lower and original_metadata.get("shade_of_fabric"):
        filtered_metadata["shade_of_fabric"] = original_metadata["shade_of_fabric"]
    if "finish" in content_lower and original_metadata.get("finish"):
        filtered_metadata["finish"] = original_metadata["finish"]

    # Testing After Coating specific
    if "coating" in content_lower and original_metadata.get("coating_formulation"):
        filtered_metadata["coating_formulation"] = original_metadata[
            "coating_formulation"
        ]
    if (
        "finish" in content_lower or "calendaring" in content_lower
    ) and original_metadata.get("finish_and_calendaring_details"):
        filtered_metadata["finish_and_calendaring_details"] = original_metadata[
            "finish_and_calendaring_details"
        ]

    # Testing After Printing specific
    if "print design" in content_lower and original_metadata.get("print_design_name"):
        filtered_metadata["print_design_name"] = original_metadata["print_design_name"]
    if "print name" in content_lower and original_metadata.get("print_name"):
        filtered_metadata["print_name"] = original_metadata["print_name"]

    # Check for test parameters mentioned in content
    for test_key, test_value in original_metadata.items():
        if test_key not in filtered_metadata and test_key not in basic_fields:
            # Check if this test parameter is mentioned in content
            test_keywords = [
                test_key.lower(),
                test_key.replace("_", " ").lower(),
                test_key.replace(" ", "").lower(),
            ]

            # Also check reverse mapping keys (short names)
            for short_name, full_name in REVERSE_TEST_MAPPING.items():
                if full_name.lower() == test_key.lower():
                    test_keywords.extend(
                        [
                            short_name.lower(),
                            short_name.replace("-", " ").lower(),
                            short_name.replace(" ", "").lower(),
                        ]
                    )

            # Check if any keyword is in content
            for keyword in test_keywords:
                if keyword in content_lower:
                    filtered_metadata[test_key] = test_value
                    break

    return filtered_metadata


def split_content_by_tokens(
    content, metadata, article, stage, original_article, max_tokens=550
):
    """Split content into chunks of max_tokens size while preserving sentence structure"""
    chunks = []

    # If content is already within limit, return as is
    if count_tokens(content) <= max_tokens:
        return [
            {
                "article": article,
                "stage": stage,
                "content": content,
                "metadata": metadata,
            }
        ]

    # Split content into sentences
    sentences = re.split(r"(?<=[.!?])\s+", content)

    current_chunk = ""
    chunk_counter = 1

    for sentence in sentences:
        # Check if adding this sentence would exceed the limit
        test_chunk = current_chunk + (" " if current_chunk else "") + sentence

        if count_tokens(test_chunk) <= max_tokens:
            current_chunk = test_chunk
        else:
            # Save current chunk if it has content
            if current_chunk:
                # Ensure article name is in chunk content
                if f"Article {original_article}" not in current_chunk:
                    current_chunk = (
                        f"Article {original_article} belongs to {stage} stage. "
                        + current_chunk
                    )

                # Create base metadata for split chunk
                base_metadata = {
                    "article": article,
                    "stage": stage,
                    "original_stage_name": metadata.get("original_stage_name"),
                    "chunk_part": chunk_counter,
                    "is_split_chunk": True,
                }

                # Extract only relevant metadata based on content
                chunk_metadata = extract_metadata_from_content(
                    current_chunk, {**metadata, **base_metadata}
                )

                chunks.append(
                    {
                        "article": article,
                        "stage": stage,
                        "content": current_chunk,
                        "metadata": chunk_metadata,
                    }
                )
                chunk_counter += 1

            # Start new chunk with current sentence
            current_chunk = sentence

            # Handle very long sentences that exceed max_tokens
            if count_tokens(current_chunk) > max_tokens:
                # Split by words if sentence is too long
                words = current_chunk.split()
                temp_chunk = ""

                for word in words:
                    test_temp = temp_chunk + (" " if temp_chunk else "") + word
                    if count_tokens(test_temp) <= max_tokens:
                        temp_chunk = test_temp
                    else:
                        if temp_chunk:
                            # Ensure article name is in chunk content
                            if f"Article {original_article}" not in temp_chunk:
                                temp_chunk = (
                                    f"Article {original_article} belongs to {stage} stage. "
                                    + temp_chunk
                                )

                            # Create base metadata for split chunk
                            base_metadata = {
                                "article": article,
                                "stage": stage,
                                "original_stage_name": metadata.get(
                                    "original_stage_name"
                                ),
                                "chunk_part": chunk_counter,
                                "is_split_chunk": True,
                            }

                            # Extract only relevant metadata based on content
                            chunk_metadata = extract_metadata_from_content(
                                temp_chunk, {**metadata, **base_metadata}
                            )

                            chunks.append(
                                {
                                    "article": article,
                                    "stage": stage,
                                    "content": temp_chunk,
                                    "metadata": chunk_metadata,
                                }
                            )
                            chunk_counter += 1
                        temp_chunk = word

                current_chunk = temp_chunk

    # Add the last chunk if it has content
    if current_chunk:
        # Ensure article name is in chunk content
        if f"Article {original_article}" not in current_chunk:
            current_chunk = (
                f"Article {original_article} belongs to {stage} stage. " + current_chunk
            )

        # Create base metadata for split chunk
        base_metadata = {
            "article": article,
            "stage": stage,
            "original_stage_name": metadata.get("original_stage_name"),
            "chunk_part": chunk_counter,
            "is_split_chunk": True,
        }

        # Extract only relevant metadata based on content
        chunk_metadata = extract_metadata_from_content(
            current_chunk, {**metadata, **base_metadata}
        )

        chunks.append(
            {
                "article": article,
                "stage": stage,
                "content": current_chunk,
                "metadata": chunk_metadata,
            }
        )

    return chunks


# ------------ Mapping Dictionaries ------------ #
stage_mapping = {
    "Griege": "Testing After Weaving",
    "Processing": "Testing After Processing",
    "Coating": "Testing After Coating",
    "Printing": "Testing After Printing",
}

FIBRE_MAP = {
    "M": "Nylon 6",
    "N": "Nylon 66",
    "L": "Poly Propylene",
    "P": "Polyester",
    "E": "Spun Polyester",
    "V": "Viscose Rayon",
    "T": "Polyester Cotton",
    "R": "Para Aramid",
    "A": "Meta Aramid",
    "C": "Cotton",
    "B": "Dimetrol",
    "D": "Nylon Cotton",
    "Z": "Nylon Spandex",
    "G": "Polyester Viscose",
    "H": "Spun Poly Propylene",
    "S": "Polyester Spandex",
    "U": "Spun Viscose Rayon",
    "Y": "Spun Acrylic",
    "F": "Recycled Polyester Spandex",
    "I": "PTT",
    "J": "PTT stretch",
    "X": "Aromatic Polyester (ARP - Vectran)",
    "K": "Nylon 06 Spandex",
    "Q": "Glass Fibre",
}

weave_map = {
    "DB": "Dobby",
    "RS": "Ripstop",
    "HB": "Herringbone Twill",
    "KT": "Knitted",
    "KN": "Knitted",
    "LN": "Leno",
    "ST": "Satin",
    "PL": "Plain",
}


def get_weave(value):
    if isinstance(value, str) and len(value) >= 2:
        return weave_map.get(value[:2].upper(), "Unknown")
    return "Unknown"


# Mapping of raw test names to metadata keys
REVERSE_TEST_MAPPING = {}


# ------------ Helpers ------------ #
def safe_str(value):
    if pd.isna(value) or value is None:
        return "Not specified"
    return str(value).strip()


def standardize_tests(group, metadata):
    seen = set()
    summaries = []
    for _, row in group.iterrows():
        if pd.isna(row.get("Test")) or str(row.get("Test")).strip() == "":
            continue

        test_name = safe_str(row.get("Test"))  # Short name for content
        full_test_name = REVERSE_TEST_MAPPING.get(
            test_name, test_name
        )  # Full name for metadata

        unit = safe_str(row.get("Unit"))
        method = safe_str(row.get("Test method"))
        standard = safe_str(row.get("Standard"))
        max_val = safe_str(row.get("Max"))
        min_val = safe_str(row.get("Min"))

        key = (test_name, unit, method, standard, max_val, min_val)
        if key in seen:
            continue
        seen.add(key)

        if min_val != "Not specified" and max_val != "Not specified":
            metadata[full_test_name] = f"{min_val}–{max_val}"

        summary = f"{test_name}"
        if unit != "Not specified":
            summary += f" ({unit})"
        if method != "Not specified":
            summary += f" tested using '{method}'"
        if standard != "Not specified":
            summary += f" standard '{standard}'"
        if min_val != "Not specified" or max_val != "Not specified":
            summary += f" with expected range {min_val}–{max_val}"
        summary += "."
        summaries.append(summary)

    return summaries


# ------------ Main Processing ------------ #
xls = pd.ExcelFile(input_file)
sheet_names = [
    s
    for s in xls.sheet_names
    if not s.lower().startswith("yarn")
    and not s.lower().startswith("unknown")
    and s.lower() != "all_data"
]

all_chunks = []
token_stats = {"original_chunks": 0, "split_chunks": 0, "oversized_chunks": 0}

for sheet in sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)
    df.columns = df.columns.str.strip()
    if df.empty or "article Number" not in df.columns or "stage name" not in df.columns:
        continue

    for (article, stage_name), article_stage_group in df.groupby(
        ["article Number", "stage name"]
    ):
        if str(stage_name).strip().lower() in ["yarn article", "unknown"]:
            continue

        # Extract numeric article for metadata and chunk structure
        numeric_article = extract_numeric_article(article)
        original_article = str(article)  # Keep original for content

        mapped_stage = stage_mapping.get(stage_name, f"Testing After {stage_name}")
        grouping_columns = []
        if "Configuration" in df.columns:
            grouping_columns.append("Configuration")
        if "Dimension 2" in df.columns:
            grouping_columns.append("Dimension 2")

        groups_to_process = (
            article_stage_group.groupby(grouping_columns)
            if grouping_columns
            else [("N/A", article_stage_group)]
        )

        for group_key, group in groups_to_process:
            config = group_key[0] if isinstance(group_key, tuple) else str(group_key)
            dim2 = (
                group_key[1]
                if isinstance(group_key, tuple) and len(group_key) > 1
                else "N/A"
            )
            valid_tests = group.dropna(subset=["Test"])
            if valid_tests.empty:
                continue

            warp_fibre = (
                safe_str(group["warp fibre"].iloc[0])
                if "warp fibre" in group.columns
                else "Not specified"
            )
            weft_fibre = (
                safe_str(group["weft fibre"].iloc[0])
                if "weft fibre" in group.columns
                else "Not specified"
            )

            metadata = {
                "article": numeric_article,  # Use numeric version
                "stage": mapped_stage,
                "original_stage_name": stage_name,
                "warp_fibre": warp_fibre,
                "weft_fibre": weft_fibre,
            }

            content_intro = f"Article {original_article} belongs to {mapped_stage} stage. "  # Use original article name
            if warp_fibre != "Not specified" and weft_fibre != "Not specified":
                content_intro += (
                    f"It uses {warp_fibre} for warp and {weft_fibre} for weft. "
                )

            # Stage-specific metadata
            if mapped_stage == "Testing After Weaving":
                metadata["sizing_details"] = safe_str(config)
                metadata["weave"] = get_weave(dim2)
                content_intro += f"It has sizing details '{metadata['sizing_details']}' and weave type '{metadata['weave']}'. "
            elif mapped_stage == "Testing After Processing":
                metadata["calendaring_details"] = safe_str(config)
                metadata["shade_of_fabric"] = safe_str(
                    group.get("Dimension 1", pd.Series([None])).iloc[0]
                )
                metadata["finish"] = safe_str(dim2)
                content_intro += f"It has fabric shade '{metadata['shade_of_fabric']}', calendaring details '{metadata['calendaring_details']}', and finish '{metadata['finish']}'. "
            elif mapped_stage == "Testing After Coating":
                metadata["coating_formulation"] = safe_str(config)
                metadata["finish_and_calendaring_details"] = safe_str(dim2)
                content_intro += f"It has coating formulation '{metadata['coating_formulation']}' and finish & calendaring details '{metadata['finish_and_calendaring_details']}'. "
            elif mapped_stage == "Testing After Printing":
                metadata["print_design_name"] = safe_str(config)
                metadata["print_name"] = safe_str(
                    group.get("Dimension 1", pd.Series([None])).iloc[0]
                )
                metadata["finish"] = safe_str(dim2)
                content_intro += f"It has print design '{metadata['print_design_name']}', print name '{metadata['print_name']}', and finish '{metadata['finish']}'. "

            summaries = standardize_tests(valid_tests, metadata)
            content = content_intro + " ".join(summaries)

            # Check token count and split if necessary
            token_count = count_tokens(content)
            token_stats["original_chunks"] += 1

            if token_count > 550:
                token_stats["oversized_chunks"] += 1
                # Split the content into multiple chunks
                split_chunks = split_content_by_tokens(
                    content,
                    metadata,
                    numeric_article,
                    mapped_stage,
                    original_article,  # Pass original_article
                )
                all_chunks.extend(split_chunks)
                token_stats["split_chunks"] += len(split_chunks)
                print(
                    f"🔄 Split article {original_article} ({mapped_stage}) - {token_count} tokens → {len(split_chunks)} chunks"  # Use original for display
                )
            else:
                all_chunks.append(
                    {
                        "article": numeric_article,  # Use numeric version
                        "stage": mapped_stage,
                        "content": content,
                        "metadata": metadata,
                    }
                )

try:
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\n✅ All Quality Chunks saved to {output_json}")
    print(f"📊 Total chunks created: {len(all_chunks)}")

    # 🔍 Token Statistics
    print(f"\n📈 Token Management Summary:")
    print("=" * 60)
    print(f"Original chunks processed: {token_stats['original_chunks']}")
    print(f"Chunks that exceeded 550 tokens: {token_stats['oversized_chunks']}")
    print(f"Total chunks after splitting: {len(all_chunks)}")
    print(f"Split chunks created: {token_stats['split_chunks']}")
    print("=" * 60)

    # 🔍 Summary by Stage
    stage_counts = {}
    for chunk in all_chunks:
        stage = chunk["metadata"]["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    print(f"\n📈 Summary by Stage:")
    print("=" * 60)
    for stage, count in stage_counts.items():
        print(f"{stage:35} | {count:6} chunks")
    print("=" * 60)
    print(f"{'TOTAL':35} | {len(all_chunks):6} chunks")

    articles = set(chunk["article"] for chunk in all_chunks)
    print(f"\n📋 Unique Articles: {len(articles)}")
    print(f"📊 Average chunks per article: {len(all_chunks)/len(articles):.1f}")

    # Show token distribution
    token_counts = [count_tokens(chunk["content"]) for chunk in all_chunks]
    print(f"\n📊 Token Distribution:")
    print(f"Average tokens per chunk: {sum(token_counts)/len(token_counts):.1f}")
    print(f"Max tokens in any chunk: {max(token_counts)}")
    print(f"Min tokens in any chunk: {min(token_counts)}")
    print(f"Chunks over 550 tokens: {sum(1 for tc in token_counts if tc > 550)}")

except Exception as e:
    print(f"❌ Error saving JSON: {e}")
    import traceback

    traceback.print_exc()

print(f"\n🏁 JSON Generation completed!")
