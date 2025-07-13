import streamlit as st
import json
import hashlib
import os
import re
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import traceback

# Try importing required libraries with error handling
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    st.error(
        "❌ sentence-transformers not installed. Run: pip install sentence-transformers"
    )
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import weaviate
    from weaviate import Client as WeaviateClient

    WEAVIATE_AVAILABLE = True
except ImportError:
    st.error("❌ weaviate-client not installed. Run: pip install weaviate-client")
    WEAVIATE_AVAILABLE = False

try:
    from langchain.schema import Document
    from langchain_text_splitters import TokenTextSplitter

    LANGCHAIN_AVAILABLE = True
except ImportError:
    st.error("❌ langchain not installed. Run: pip install langchain")
    LANGCHAIN_AVAILABLE = False

try:
    from langchain_openai import AzureChatOpenAI

    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    st.error("❌ langchain_openai not installed. Run: pip install langchain_openai")
    AZURE_OPENAI_AVAILABLE = False

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WEAVIATE_URL = "http://localhost:8080"
CLASS_NAME = "TextileChunk"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
USERS_FILE = "users.json"
CHAT_HISTORY_DIR = "chat_histories"

# Create directories if they don't exist
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# Process names and parameters (complete definition)
PROCESS_NAMES = [
    "ageing",
    "beaming",
    "calendaring",
    "calendering",
    "coating",
    "curing",
    "direct warping",
    "dry",
    "dry print",
    "drying",
    "dye wash",
    "dyeing and washing",
    "finishing",
    "heat set",
    "pigment",
    "print wash",
    "printing",
    "processing",
    "ptg",
    "scouring",
    "scouring and dyeing",
    "scouring and washing",
    "scouring, drying and washing",
    "sectional warping",
    "sizing",
    "testing after coating",
    "testing after printing",
    "testing after processing",
    "testing after weaving",
    "vdr",
    "warp and weft yarn details",
    "washing",
    "weaving",
]

PROCESS_PARAMETERS = {
    "ageing": [
        "ager",
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "design name",
        "dwell time",
        "dwell time(min)",
        "finishing after printing",
        "finishing details after processing",
        "full article",
        "machine used in processing",
        "steam pressure",
        "steam pressure(pound)",
        "steam pressure(psi)",
        "temp.",
        "temperature",
    ],
    "beaming": [
        "article no",
        "article number",
        "article_no",
        "beaming reed pitch",
        "beaming speed",
        "chamber 1 high",
        "chamber 1 low",
        "chamber 2 high",
        "chamber 2 low",
        "config_id",
        "cylinder 1",
        "cylinder 2",
        "cylinder 3",
        "cylinder 4",
        "cylinder 5",
        "dry tension fast",
        "dry tension slow",
        "full_article",
        "pressure squeeze roll",
        "pressureimmerssion roll",
        "size -",
        "size concentration",
        "size tension fast",
        "size tension slow",
        "sizing m/c speed -",
        "sizing wastsge (kg)",
        "spu %",
        "strech",
        "tension t.s.d (1)",
        "tension take up",
        "total_ends_in_warp",
        "water -",
    ],
    "calendaring": [
        "article no",
        "article number",
        "article_no",
        "bottom 2/ top 2     bowl",
        "bottom 2/top 2 bowl",
        "coating type",
        "design name",
        "finishing after printing",
        "finishing done before coating",
        "full article",
        "full_article",
        "machine used in processing",
        "no of passes",
        "pressure ( tons)",
        "pressure (kg/cm2)",
        "pressure (tons)",
        "pressure(kg)",
        "pressure(tons)",
        "speed mtrs/min",
        "temp",
    ],
    "calendering": [
        "article no",
        "article number",
        "article_no",
        "bottom 2/ top 2     bowl",
        "calendaring details",
        "calendering",
        "calendring",
        "finishing details after processing",
        "full article",
        "machine used in processing",
        "no of passes",
        "pressure ( tons)",
        "speed mtrs/min",
        "temp",
    ],
    "coating": [
        "article no",
        "article number",
        "article_no",
        "bomid",
        "chamber 1 temp ( +/-5)",
        "chamber 2 temp ( +/-5)",
        "chamber 3 temp ( +/-5)",
        "chamber 4 temp ( +/-5)",
        "chamber 5 temp ( +/-5)",
        "chamber 6 temp ( +/-5)",
        "coating chemicals",
        "coating type",
        "finishing done before coating",
        "full_article",
        "shade",
        "shades",
        "speed  ( +/-2)",
        "type of coating",
        "type of finish",
        "viscosity of pu ( +/-10)",
        "weight ( +/-5)",
        "width after",
        "width after coating",
    ],
    "curing": [
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "chamber 1 temp ( +/-5)",
        "chamber 2 temp ( +/-5)",
        "chamber 3 temp ( +/-5)",
        "chamber 4 temp ( +/-5)",
        "chamber 5 temp ( +/-5)",
        "chamber 6 temp ( +/-5)",
        "chamber 7 temp ( +/-5)",
        "chamber 8 temp ( +/-5)",
        "clip / pin",
        "coating type",
        "design name",
        "drying / hs / finishing",
        "dwr curring",
        "finishing after printing",
        "finishing details after processing",
        "finishing done before coating",
        "full article",
        "full_article",
        "machine used in processing",
        "p.h. of solution",
        "speed",
        "speed  mtrs/min",
        "stenter curring",
        "stitch end piece with weft straight",
        "wdith after",
        "width after",
        "with / without bianco",
        "with / without overfeed",
        "without/with mangle[ ]",
        "without/with overflow wash",
    ],
    "direct warping": [
        "article no",
        "article number",
        "article_no",
        "beam winding tension",
        "beaming speed",
        "config_id",
        "creel tension (post position)",
        "density",
        "full article",
        "full_article",
        "jumbo winding tension",
        "lease position",
        "number_of_ends_in_warp",
        "oiling",
        "press roll pressure",
        "s.wrap tension contribution",
        "sizing_details",
        "tension washer",
        "total ends of warp",
        "total no of creel ends",
        "traverse",
        "warping m/c speed",
        "warping multiple",
        "warping reed pitch",
        "wastage",
        "yarn breakage (fluff big)",
        "yarn breakage (fluff small)",
        "yarn breakage (fluff total)",
        "warping speed",
    ],
    "dry": [
        "article no",
        "article number",
        "article_no",
        "chamber 1 temp ( +/-5)",
        "chamber 2 temp ( +/-5)",
        "chamber 3 temp ( +/-5)",
        "chamber 4 temp ( +/-5)",
        "chamber 5 temp ( +/-5)",
        "chamber 6 temp ( +/-5)",
        "clip / pin",
        "coating type",
        "drying / hs / finishing",
        "finishing done before coating",
        "full_article",
        "p.h. of solution",
        "speed  mtrs/min",
        "stitch end piece with weft straight",
        "with / without bianco",
        "with / without overfeed",
        "without/with mangle[ ]",
        "without/with overflow wash",
    ],
    "dry print": [
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "chamber 1 temp ( +/-5)",
        "chamber 2 temp ( +/-5)",
        "chamber 3 temp ( +/-5)",
        "chamber 4 temp ( +/-5)",
        "chamber 5 temp ( +/-5)",
        "chamber 6 temp ( +/-5)",
        "clip / pin",
        "drying / hs / finishing",
        "finishing details after processing",
        "full article",
        "machine used in processing",
        "p.h. of solution",
        "speed",
        "speed  mtrs/min",
        "stenter dry",
        "stitch end piece with weft straight",
        "width after",
        "with / without bianco",
        "with / without overfeed",
        "without/with mangle[ ]",
        "without/with overflow wash",
    ],
    "drying": [
        "after a frame / trolly",
        "article no",
        "article number",
        "article_no",
        "before a frame / trolly",
        "calendaring details",
        "chamber 1 temp ( +/-5)",
        "chamber 2 temp ( +/-5)",
        "chamber 3 temp ( +/-5)",
        "chamber 4 temp ( +/-5)",
        "chamber 5 temp ( +/-5)",
        "chamber 6 temp ( +/-5)",
        "chamber 7 temp ( +/-5)",
        "chamber 8 temp ( +/-5)",
        "clip / pin",
        "design name",
        "drying",
        "drying / hs / finishing",
        "dtenter drying",
        "dwr padding",
        "dwr-dry",
        "finishing after printing",
        "finishing details after processing",
        "full article",
        "gsm",
        "machine used in processing",
        "p.h. of solution",
        "speed",
        "speed  mtrs/min",
        "stenter dring",
        "stenter dry",
        "stenter dwr",
        "stenter dwr drying",
        "stenter dying",
        "stitch end piece with weft straight",
        "vdr",
        "vdr-1",
        "wdith after",
        "width after",
        "with / without bianco",
        "with / without overfeed",
        "with / without under feed",
        "with / without underfeed",
        "without/with mangle[ ]",
        "without/with overflow wash",
    ],
    "dye wash": [
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "cold wash  temp",
        "cold wash end",
        "cold wash ends",
        "cold wash ends-1",
        "cold wash tem-1",
        "cold wash temp",
        "cold wash-1  temp",
        "cold wash-1 ends",
        "cold wash-1 tem",
        "cold wash-2  temp",
        "cold wash-2 ends",
        "dosing ends",
        "dosing temp",
        "dyeing  ends",
        "dyeing  temp",
        "dyeing ends-1",
        "dyeing ends-2",
        "dyeing ends-3",
        "dyeing ends-4",
        "dyeing st ends",
        "dyeing st temp",
        "dyeing st-1 ends",
        "dyeing st-1 temp",
        "dyeing st-2 ends",
        "dyeing st-2 temp",
        "dyeing st-3 ends",
        "dyeing st-3 temp",
        "dyeing st-4 ends",
        "dyeing st-4 temp",
        "dyeing temp-1",
        "dyeing temp-2",
        "dyeing temp-3",
        "dyeing temp-4",
        "finishing details after processing",
        "fixing  ends",
        "fixing  temp",
        "fixing ends",
        "fixing temp",
        "full article",
        "holding time",
        "hot wash ends",
        "hot wash ends 1",
        "hot wash ends 2",
        "hot wash ends-1",
        "hot wash ends-2",
        "hot wash ends-3",
        "hot wash ends-4",
        "hot wash ends-5",
        "hot wash temp",
        "hot wash temp 1",
        "hot wash temp 2",
        "hot wash temp-1",
        "hot wash temp-2",
        "hot wash temp-3",
        "hot wash temp-4",
        "hot wash temp-5",
        "hot wash-1 ends",
        "hot wash-1 temp",
        "hot wash-2 ends",
        "hot wash-2 temp",
        "hot wash-3 ends",
        "hot wash-3 temp",
        "hot wash-4 ends",
        "hot wash-4 temp",
        "jet",
        "machine used in processing",
        "minutes",
        "neutralization ends",
        "neutralization temp",
        "neutralize end",
        "neutralize ends",
        "neutralize temp",
        "neutrialise ends",
        "neutrialise temp",
        "no of ends",
        "p jigger",
        "pressure (kg)",
        "reduction  temp",
        "reduction cleaning ends",
        "reduction cleaning temp",
        "reduction ends",
        "scouring ends",
        "scouring ends-1",
        "scouring temp",
        "scouring temp-1",
        "soaping  temp",
        "soaping ends",
        "soaping temp",
        "speed",
        "speed (rpm)",
        "temp",
        "tension",
        "time",
        "water",
    ],
    "dyeing and washing parameters": [
        "article no",
        "article number",
        "article_no",
        "coating type",
        "cold wash",
        "dosing",
        "drain/fill",
        "drain/fill/add",
        "drain/fill/heat",
        "drain/fill/heat/add",
        "dyeing",
        "fill water lt",
        "finishing done before coating",
        "full_article",
        "hot wash",
        "levelling",
        "loading",
    ],
    "finishing parameters": [
        "after a frame / trolly",
        "article no",
        "article number",
        "article_no",
        "before a frame / trolly",
        "calendaring details",
        "chamber 1 temp ( +/-5)",
        "chamber 2 temp ( +/-5)",
        "chamber 3 temp ( +/-5)",
        "chamber 4 temp ( +/-5)",
        "chamber 5 temp ( +/-5)",
        "chamber 6 temp ( +/-5)",
        "chamber 7 temp ( +/-5)",
        "chamber 8 temp ( +/-5)",
        "clip / pin",
        "coating type",
        "design name",
        "drying / hs / finishing",
        "finishing after printing",
        "finishing details after processing",
        "finishing done before coating",
        "full article",
        "full_article",
        "machine used in processing",
        "nan",
        "p.h. of solution",
        "speed",
        "speed  mtrs/min",
        "stenter finish",
        "stenterfinishing",
        "stitch end piece with weft straight",
        "wdith after",
        "width after",
        "with / without bianco",
        "with / without overfeed",
        "with / without under feed",
        "without/with mangle[ ]",
        "without/with overflow wash",
    ],
    "heat set parameters": [
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "chamber 1 temp ( +/-5)",
        "chamber 2 temp ( +/-5)",
        "chamber 3 temp ( +/-5)",
        "chamber 4 temp ( +/-5)",
        "chamber 5 temp ( +/-5)",
        "chamber 6 temp ( +/-5)",
        "chamber 7 temp ( +/-5)",
        "chamber 8 temp ( +/-5)",
        "clip / pin",
        "coating type",
        "drying / hs / finishing",
        "finishing details after processing",
        "finishing done before coating",
        "full article",
        "full_article",
        "heat setting",
        "machine used in processing",
        "p.h. of solution",
        "speed",
        "speed  mtrs/min",
        "stitch end piece with weft straight",
        "width after",
        "with / without bianco",
        "with / without overfeed",
        "with / without under feed",
        "without/with mangle[ ]",
        "without/with overflow wash",
    ],
    "pigment": [
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "chamber 1 temp ( +/-5)",
        "chamber 2 temp ( +/-5)",
        "chamber 3 temp ( +/-5)",
        "chamber 4 temp ( +/-5)",
        "chamber 5 temp ( +/-5)",
        "chamber 6 temp ( +/-5)",
        "design name",
        "dryer temp. 1",
        "dryer temp. 2",
        "dryer temp. 3",
        "dryer temp. 4",
        "finishing after printing",
        "finishing details after processing",
        "full article",
        "head no. 3",
        "machine used in processing",
        "magnet pressure",
        "screen mesh size",
        "speed",
        "stenter pigment",
        "width after",
        "with / without overfeed",
    ],
    "print wash": [
        "ammonia wash",
        "ammonia wash - no of end",
        "ammonia wash - speed",
        "ammonia wash - temp.",
        "ammonia wash - tension",
        "ammonia wash end",
        "ammonia wash temp",
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "chamber 1 temp",
        "chamber 2 temp",
        "chamber 3 temp",
        "chamber 4 temp",
        "chamber 5 temp",
        "cold wash",
        "cold wash - no of end",
        "cold wash - speed",
        "cold wash - temp.",
        "cold wash - tension",
        "cold wash end",
        "cold wash end-1",
        "cold wash end-2",
        "cold wash ends-2",
        "cold wash temp",
        "cold wash temp-1",
        "cold wash temp-2",
        "design name",
        "drain/fill",
        "drain/fill water",
        "drain/fill water /add",
        "drain/fill water/add",
        "drain/fill water/heat",
        "drain/fill/add",
        "fill water/add",
        "finishing after printing",
        "finishing details after processing",
        "fixing",
        "full article",
        "hot wash",
        "hot wash - no of end",
        "hot wash - speed",
        "hot wash - temp.",
        "hot wash - tension",
        "hot wash ends",
        "hot wash temp",
        "hydro wash - no of end",
        "hydro wash - speed",
        "hydro wash - temp.",
        "hydro wash - tension",
        "loading",
        "loading - speed",
        "loading speed",
        "machine used in processing",
        "neutralization ends",
        "neutralization temp",
        "neutralize",
        "neutralize  - no of end",
        "neutralize  - speed",
        "neutralize  - tension",
        "neutralize - no of end",
        "neutralize - speed",
        "neutralize - temp.",
        "neutralize - tension",
        "no of end",
        "print wash",
        "print wash end",
        "print wash temp",
        "setting",
        "soaping",
        "soaping - no of end",
        "soaping - speed",
        "soaping - temp.",
        "soaping - tension",
        "soaping ends",
        "soaping temp",
        "speed",
        "temp.",
        "tension",
        "wash end",
        "wash temp",
        "water",
    ],
    "printing parameters": [
        "1-dryer temp. 1",
        "1-dryer temp. 2",
        "1-dryer temp. 3",
        "1-dryer temp. 4",
        "1-head no. 2",
        "1-head no. 3",
        "1-head no. 4",
        "1-head no. 5",
        "1-head no. 6",
        "1-magnet pressure head no. 2",
        "1-magnet pressure head no. 3",
        "1-magnet pressure head no. 4",
        "1-magnet pressure head no. 5",
        "1-magnet pressure head no. 6",
        "1-rod size head no. 2",
        "1-rod size head no. 3",
        "1-rod size head no. 4",
        "1-rod size head no. 5",
        "1-rod size head no. 6",
        "1-screen mesh size",
        "1-speed",
        "2-dryer temp. 1",
        "2-dryer temp. 2",
        "2-dryer temp. 3",
        "2-dryer temp. 4",
        "2-head no. 2",
        "2-head no. 3",
        "2-head no. 4",
        "2-head no. 5",
        "2-head no. 6",
        "2-magnet pressure head no. 2",
        "2-magnet pressure head no. 3",
        "2-magnet pressure head no. 4",
        "2-magnet pressure head no. 5",
        "2-magnet pressure head no. 6",
        "2-rod size head no. 2",
        "2-rod size head no. 3",
        "2-rod size head no. 4",
        "2-rod size head no. 5",
        "2-rod size head no. 6",
        "2-screen mesh size",
        "2-speed",
        "article no",
        "article number",
        "article_no",
        "design name",
        "dryer temp. 1",
        "dryer temp. 2",
        "dryer temp. 3",
        "dryer temp. 4",
        "finishing after printing",
        "full article",
        "head no. 2",
        "head no. 3",
        "head no. 4",
        "head no. 5",
        "head no. 6",
        "head no. 7",
        "head no. 8",
        "machine used in processing",
        "magnet pressure",
        "magnet pressure head no. 2",
        "magnet pressure head no. 3",
        "magnet pressure head no. 4",
        "magnet pressure head no. 5",
        "magnet pressure head no. 6",
        "magnet pressure head no. 7",
        "magnet pressure head no. 8",
        "rod size",
        "rod size  head no. 4",
        "rod size  head no. 5",
        "rod size  head no. 6",
        "rod size  head no. 7",
        "rod size head no. 2",
        "rod size head no. 3",
        "rod size head no. 4",
        "rod size head no. 5",
        "rod size head no. 6",
        "rod size head no. 7",
        "rod size head no. 8",
        "screen mesh size",
        "speed",
    ],
    "processing chemicals": [
        "article no",
        "article_no",
        "bomid",
        "calendaring",
        "chemicals used",
        "col_1",
        "full_article",
        "machine used for processing",
        "required shade",
        "type of finish",
        "width in cm",
    ],
    "ptg": [
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "finishing details after processing",
        "full article",
        "machine used in processing",
        "printing",
    ],
    "scouring": [
        "article no",
        "article number",
        "article_no",
        "bleaching-1 ends",
        "bleaching-1 temp",
        "bleaching-2 ends",
        "bleaching-2 temp",
        "boil - off  washer",
        "boil - off washer",
        "calendaring details",
        "chamber 1 temp",
        "chamber 2 temp",
        "chamber 3 temp",
        "chamber 4 temp",
        "chamber 5 temp",
        "chamber 6 temp",
        "chamber 7 temp",
        "chamber 8 temp",
        "chemical recp no",
        "coating type",
        "cold wash end",
        "cold wash ends",
        "cold wash temp",
        "desizing ends",
        "desizing temp",
        "desizing/scouring ends",
        "desizing/scouring temp",
        "finishing details after processing",
        "finishing done before coating",
        "full article",
        "full_article",
        "hot wash ends",
        "hot wash ends-1",
        "hot wash ends-2",
        "hot wash temp",
        "hot wash temp-1",
        "hot wash temp-2",
        "hot wash-1 ends",
        "hot wash-1 temp",
        "jet",
        "machine used in processing",
        "manzel washer 1",
        "megalux",
        "megalux bypass",
        "nan",
        "neutralise ends",
        "neutralise temp",
        "neutralization ends",
        "neutralization temp",
        "no of ends",
        "scouring ends",
        "scouring ends-1",
        "scouring ends-2",
        "scouring temp",
        "scouring temp-1",
        "scouring temp-2",
        "scouring-1 ends",
        "scouring-1 temp",
        "scouring-2 ends",
        "scouring-2 temp",
        "setting",
        "settting",
        "speed",
        "temp",
        "tension",
        "water",
    ],
    "scouring and dyeing": [
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "cold wash ends-1",
        "cold wash tem-1",
        "dyeing st-1 ends",
        "dyeing st-1 temp",
        "dyeing st-2 ends",
        "dyeing st-2 temp",
        "dyeing st-3 ends",
        "dyeing st-3 temp",
        "finishing details after processing",
        "full article",
        "hot wash ends-1",
        "hot wash ends-2",
        "hot wash temp-1",
        "hot wash temp-2",
        "machine used in processing",
        "neutralization ends",
        "neutralization temp",
        "no of ends",
        "scouring ends",
        "scouring temp",
        "speed",
        "temp",
        "tension",
        "water",
    ],
    "scouring and washing": [
        "article no",
        "article number",
        "article_no",
        "bleach end",
        "bleach temp",
        "bleaching end-1",
        "bleaching end-2",
        "bleaching ends",
        "bleaching ends-1",
        "bleaching ends-2",
        "bleaching temp",
        "bleaching temp-1",
        "bleaching temp-2",
        "bleaching-1 ends",
        "bleaching-1 temp",
        "bleaching-2 ends",
        "bleaching-2 temp",
        "calendaring details",
        "chamber 1 temp",
        "chamber 1 temp-1",
        "chamber 2 temp",
        "chamber 2 temp-1",
        "chamber 3 temp",
        "chamber 3 temp-1",
        "chamber 4 temp",
        "chamber 4 temp-1",
        "chamber 5 temp",
        "chamber 5 temp-1",
        "chamber 6 temp",
        "chamber 7 temp",
        "chamber 8 temp",
        "chemical recp no",
        "chemical recp no-1",
        "cold wash end",
        "cold wash end-1",
        "cold wash end-3",
        "cold wash ends",
        "cold wash ends-1",
        "cold wash ends-2",
        "cold wash ends-3",
        "cold wash tem-1",
        "cold wash temp",
        "cold wash temp-1",
        "cold wash temp-2",
        "cold wash temp-3",
        "cold wash-1 ends",
        "cold wash-1 temp",
        "cold wash-2 ends",
        "cold wash-2 temp",
        "desizing ends",
        "desizing temp",
        "finishing details after processing",
        "frn wash ends",
        "frn wash temp",
        "full article",
        "hot  wash ends",
        "hot wash ends",
        "hot wash ends-1",
        "hot wash ends-2",
        "hot wash temp",
        "hot wash temp-1",
        "hot wash temp-2",
        "hot wash-1 ends",
        "hot wash-1 temp",
        "hot wash-2 ends",
        "hot wash-2 temp",
        "jet",
        "machine used in processing",
        "manzel washer 2",
        "megalux",
        "megalux bypass",
        "minutes",
        "nan",
        "neutralise end",
        "neutralise ends",
        "neutralise temp",
        "neutralization ends",
        "neutralization ends-2",
        "neutralization temp",
        "neutralization temp-2",
        "neutrelise ends",
        "neutrelise temp",
        "neutrelization ends",
        "neutrelization temp",
        "no of ends",
        "oxalic wash ends",
        "oxalic wash temp",
        "peroxide process end",
        "peroxide process temp",
        "pressure (kg)",
        "scouring ends",
        "scouring ends-1",
        "scouring ends-2",
        "scouring temp",
        "scouring temp-1",
        "scouring temp-2",
        "scouring-1 ends",
        "scouring-1 temp",
        "scouring-2 ends",
        "scouring-2 temp",
        "scouring-3 ends",
        "scouring-3 temp",
        "scouring/desizing ends",
        "scouring/desizing temp",
        "seting",
        "setting",
        "settting",
        "soaping ends",
        "soaping temp",
        "speed",
        "speed (rpm)",
        "temp",
        "tension",
        "water",
    ],
    "scouring, drying and washing": [
        "article no",
        "article number",
        "article_no",
        "bleaching end-1",
        "bleaching end-2",
        "bleaching ends",
        "bleaching ends 1",
        "bleaching ends 2",
        "bleaching ends-1",
        "bleaching ends-2",
        "bleaching temp",
        "bleaching temp 1",
        "bleaching temp 2",
        "bleaching temp-1",
        "bleaching temp-2",
        "bleaching-1 ends",
        "bleaching-1 temp",
        "bleaching-2 ends",
        "bleaching-2 temp",
        "calendaring details",
        "cold wash  ends",
        "cold wash  ends-2",
        "cold wash end-1",
        "cold wash end-3",
        "cold wash end-4",
        "cold wash end-5",
        "cold wash ends",
        "cold wash ends-1",
        "cold wash ends-2",
        "cold wash ends-3",
        "cold wash tem-1",
        "cold wash temp",
        "cold wash temp-1",
        "cold wash temp-2",
        "cold wash temp-3",
        "cold wash temp-4",
        "cold wash temp-5",
        "cold wash-1 end",
        "cold wash-1 ends",
        "cold wash-1 temp",
        "cold wash-2 end",
        "cold wash-2 ends",
        "cold wash-2 temp",
        "desizing ends",
        "desizing temp",
        "dyeing st-1 ends",
        "dyeing st-1 temp",
        "dyeing st-2 ends",
        "dyeing st-2 temp",
        "dyeing st-3 ends",
        "dyeing st-3 temp",
        "dyeing st-4 ends",
        "dyeing st-4 temp",
        "finishing details after processing",
        "fixing end",
        "fixing ends",
        "fixing ends-2",
        "fixing temp",
        "fixing temp-2",
        "fixing temps",
        "frn wash ends",
        "frn wash temp",
        "full article",
        "hot wash  ends-1",
        "hot wash  ends-2",
        "hot wash ends",
        "hot wash ends-1",
        "hot wash ends-2",
        "hot wash ends-3",
        "hot wash ends-4",
        "hot wash ends-5",
        "hot wash ends-6",
        "hot wash temp",
        "hot wash temp-1",
        "hot wash temp-2",
        "hot wash temp-3",
        "hot wash temp-4",
        "hot wash temp-5",
        "hot wash temp-6",
        "hot wash-1 ends",
        "hot wash-1 temp",
        "hot wash-2  ends",
        "hot wash-2 ends",
        "hot wash-2 temp",
        "hot wash-3 ends",
        "hot wash-3 temp",
        "hot wash-4 ends",
        "hot wash-4 temp",
        "hot wash-5 ends",
        "hot wash-5 temp",
        "jet",
        "machine used in processing",
        "neutralization ends",
        "neutralization ends-1",
        "neutralization ends-2",
        "neutralization temp",
        "neutralization temp-1",
        "neutralization temp-2",
        "neutralize ends",
        "neutralize temp",
        "neutrealise ends",
        "neutrealise temp",
        "neutrelise ends",
        "neutrelise temp",
        "no of ends",
        "reduction cleaning ends",
        "reduction cleaning temp",
        "reduction clear end",
        "reduction clear temp",
        "scouring end",
        "scouring ends",
        "scouring ends-1",
        "scouring ends-2",
        "scouring temp",
        "scouring temp-1",
        "scouring temp-2",
        "scouring-1 ends",
        "scouring-1 temp",
        "scouring-2 ends",
        "scouring-2 temp",
        "soaping ends",
        "soaping temp",
        "soping ends",
        "soping temp",
        "speed",
        "temp",
        "tension",
        "water",
    ],
    "sectional warping": [
        "article no",
        "article number",
        "article_no",
        "beam winding tension",
        "beaming reed pitch",
        "beaming speed",
        "compaction factor",
        "config_id",
        "creel tension (post position)",
        "density",
        "ends / section -",
        "fabric",
        "full article",
        "full_article",
        "lease position",
        "number_of_ends_in_warp",
        "oiling",
        "press roll pressure",
        "s.wrap tension contribution",
        "section width in cms",
        "sizing m/c speed -",
        "sizing_details",
        "tension t.s.d (1)",
        "tension take up",
        "total ends of warp",
        "traverse",
        "warping m/c speed",
        "wastage",
    ],
    "sizing": [
        "article no",
        "article number",
        "article_no",
        "beaming reed pitch",
        "beaming speed",
        "chamber 1 high",
        "chamber 1 low",
        "chamber 2 high",
        "chamber 2 low",
        "config_id",
        "cylinder 1",
        "cylinder 2",
        "cylinder 3",
        "cylinder 4",
        "cylinder 5",
        "dry tension fast",
        "dry tension slow",
        "full_article",
        "pressure squeeze roll",
        "pressureimmerssion roll",
        "size -",
        "size concentration",
        "size tension fast",
        "size tension slow",
        "sizing m/c speed -",
        "sizing wastsge (kg)",
        "spu %",
        "strech",
        "tension t.s.d (1)",
        "tension take up",
        "total ends in warp",
        "water -",
    ],
    "testing after coating": [
        "%bias",
        "%bow",
        "%bow-inch",
        "%skew",
        "%skew-inch",
        "abra emery cycle",
        "abso.of water drop-after washsec",
        "abso.of water drop-before sec",
        "absorption of water drop- sec",
        "add on %",
        "add on(gms)",
        "adhesion to backing (n/cm) 8310se",
        "apcycl@1/2 inch (cfm)",
        "apcycl@1/2 inch (l/m2/s)",
        "appearance after 5x hl",
        "bend lngth-wp mn.cm2",
        "blocking test",
        "breathtest-mg/cm2/h",
        "cf to light",
        "chunk_part",
        "co-eff.frict-wt",
        "co-eff.frict.wp",
        "coated abrasion resistance using p600emery at 9kpa after 150 cycles",
        "coated abrasion resistance using p600emery at 9kpa after 30 cycles",
        "coated abrasion resistance using p600emery at 9kpa after 50 cycles",
        "coated abrasion resistance using unspecified abradant at 9kpa after 10000 cycles",
        "coated abrasion resistance using unspecified abradant at unspecified pressure after unspecified number of cycles",
        "coated abrasion resistance using wool at 12kpa after 100000 cycles",
        "coated abrasion resistance using wool at 12kpa after 75000 cycles",
        "coated abrasion resistance using wool at 9kpa after 15000 cycles",
        "coated abrasion resistance using wool at 9kpa after 50000 cycles",
        "coated abrasion resistance using wool at 9kpa after 60000 cycles",
        "coated abrasion resistance using wool at 9kpa after 90000 cycles",
        "coated abrasion resistance using wool at unspecified pressure after 1 cycles",
        "coated air permeability at 1/2 inch pressure in ft3/ft2/m",
        "coated air permeability at 1/2 inch pressure in l/m2/s",
        "coated air permeability at 10 inch pressure in cm3/cm2/s",
        "coated air permeability at 10 inch pressure in ft3/ft2/m",
        "coated air permeability at 100 pas pressure in cm3/cm2/s",
        "coated air permeability at 100 pas pressure in l/m2/s",
        "coated air permeability at 100 pas pressure in mm/s",
        "coated air permeability at 10mm pressure in cm3/cm2/s",
        "coated air permeability at 200 pas pressure in mm/s",
        "coated air permeability at 25mm pressure in cc/sec/cm2",
        "coated air permeability at 500 pas pressure in l/m2/s",
        "coated breaking strength of warp in dan",
        "coated breaking strength of warp in kgf",
        "coated breaking strength of warp in lbf",
        "coated breaking strength of warp in n",
        "coated breaking strength of weft in dan",
        "coated breaking strength of weft in kgf",
        "coated breaking strength of weft in lbf",
        "coated breaking strength of weft in n",
        "coated bursting strength in kgf/cm²",
        "coated colourfastness to perspiration (acid) change in shade",
        "coated colourfastness to perspiration (acid) staining on acr",
        "coated colourfastness to perspiration (acid) staining on act",
        "coated colourfastness to perspiration (acid) staining on cot",
        "coated colourfastness to perspiration (acid) staining on nyl",
        "coated colourfastness to perspiration (acid) staining on pol",
        "coated colourfastness to perspiration (acid) staining on wol",
        "coated colourfastness to perspiration (alkaline) change in shade",
        "coated colourfastness to perspiration (alkaline) staining on acr",
        "coated colourfastness to perspiration (alkaline) staining on act",
        "coated colourfastness to perspiration (alkaline) staining on cot",
        "coated colourfastness to perspiration (alkaline) staining on nyl",
        "coated colourfastness to perspiration (alkaline) staining on pol",
        "coated colourfastness to perspiration (alkaline) staining on wol",
        "coated colourfastness to rubbing (dry)",
        "coated colourfastness to rubbing (dry)  wp",
        "coated colourfastness to rubbing (dry)  wt",
        "coated colourfastness to rubbing (wet)",
        "coated colourfastness to rubbing (wet)  wp",
        "coated colourfastness to rubbing (wet)  wt",
        "coated colourfastness to sea water change in shade",
        "coated colourfastness to sea water staining on acr",
        "coated colourfastness to sea water staining on act",
        "coated colourfastness to sea water staining on cot",
        "coated colourfastness to sea water staining on nyl",
        "coated colourfastness to sea water staining on pol",
        "coated colourfastness to sea water staining on wol",
        "coated colourfastness to washing change in shade",
        "coated colourfastness to washing staining on acr",
        "coated colourfastness to washing staining on act",
        "coated colourfastness to washing staining on cot",
        "coated colourfastness to washing staining on nyl",
        "coated colourfastness to washing staining on pol",
        "coated colourfastness to washing staining on wol",
        "coated colourfastness to water change in shade",
        "coated colourfastness to water staining on acr",
        "coated colourfastness to water staining on act",
        "coated colourfastness to water staining on cot",
        "coated colourfastness to water staining on nyl",
        "coated colourfastness to water staining on pol",
        "coated colourfastness to water staining on wol",
        "coated delta e (δe) under primary light (f11 10°)",
        "coated delta e (δe) under secondary light (d65 10°)",
        "coated delta e (δe) value",
        "coated dimensional stability of warp after 2 washes",
        "coated dimensional stability of warp after 3 washes",
        "coated dimensional stability of warp after 5 washes",
        "coated dimensional stability of warp after one washes",
        "coated dimensional stability of warp in cold water",
        "coated dimensional stability of warp in hot water",
        "coated dimensional stability of warp to heat",
        "coated dimensional stability of weft after 2 washes",
        "coated dimensional stability of weft after 3 washes",
        "coated dimensional stability of weft after 5 washes",
        "coated dimensional stability of weft after one washes",
        "coated dimensional stability of weft in cold water",
        "coated dimensional stability of weft in hot water",
        "coated dimensional stability of weft to heat",
        "coated ends per 10cms",
        "coated ends per cms",
        "coated ends per dm",
        "coated ends per inch",
        "coated fabric elongation in warp direction (fabric growth after 30mm-wp)",
        "coated fabric elongation in warp direction (wp)",
        "coated fabric elongation in weft direction (fabric growth after 30mm-wt)",
        "coated fabric elongation in weft direction (of fabric stretch-wt(15n))",
        "coated fabric elongation in weft direction (wt)",
        "coated picks per 10cms",
        "coated picks per cms",
        "coated picks per dm",
        "coated picks per inch",
        "coated tear strength of warp in dan",
        "coated tear strength of warp in kgf",
        "coated tear strength of warp in lbf",
        "coated tear strength of warp in n",
        "coated tear strength of warp using elmendorf method in dan",
        "coated tear strength of warp using elmendorf method in kgf",
        "coated tear strength of warp using elmendorf method in lbf",
        "coated tear strength of weft in dan",
        "coated tear strength of weft in kgf",
        "coated tear strength of weft in lbf",
        "coated tear strength of weft in n",
        "coated tear strength of weft using elmendorf method in dan",
        "coated tear strength of weft using elmendorf method in kgf",
        "coated tear strength of weft using elmendorf method in lbf",
        "coated thickness in inch",
        "coated thickness in micron",
        "coated thickness in mil",
        "coated thickness in mm",
        "coated water proofness of weld zone tested at 100°c for 1 hour(s)",
        "coated water proofness tested at 100°c",
        "coated water proofness tested at 100°c for 1 hour(s)",
        "coated water proofness tested at 100°c for 60 minutes",
        "coated water proofness tested at 110°c for 90 seconds",
        "coated water proofness tested at 140°c for 60 seconds",
        "coated water proofness tested at 20°c",
        "coated water proofness tested at 30°c for 30 minutes",
        "coated water proofness tested at 30°c for 60 minutes",
        "coated water proofness tested at 60°c for 30 minutes",
        "coated water proofness tested at 60°c for 60 minutes",
        "coated water proofness tested at 80°c for 60 seconds",
        "coated water proofness tested at 80°c with minimum pressure of 80 cm",
        "coated water proofness using dynamic method",
        "coated water proofness with minimum pressure of 0.4 bar",
        "coating_formulation",
        "crimp test % -wp",
        "crimp test % -wt",
        "deter.of shrink.after1wash @40°c-wp",
        "deter.of shrink.after1wash @40°c-wt",
        "deter.of shrink.after5wash @40°c-wp",
        "deter.of shrink.after5wash @40°c-wt",
        "finish_and_calendaring_details",
        "flex res.-crack",
        "flex res.-flaking",
        "flex res.-wrinkle",
        "fr test (a. flame)",
        "fr test (a. glow)",
        "is_split_chunk",
        "majoraxis-drop spread-afterwashcm",
        "majoraxis-drop spread-beforewashcm",
        "melting point",
        "metamerism f11/d65 mi",
        "nature of coating",
        "nature of dyes",
        "nature of fiber",
        "oil content%",
        "original_stage_name",
        "peel st.-wp gmf",
        "peel st.-wp n",
        "peel st.-wt n",
        "peelrest.after50wash",
        "per.of set %shrink.-wp",
        "per.of set %shrink.-wt",
        "per.of set ap@1/2 inch (ft3/ft2/m)",
        "per.of set thick inch",
        "ph value",
        "ph value-other color",
        "ph value-white to pastel color",
        "pilling (7000 tours)",
        "pilling after (18000 revs.)",
        "pilling resis.martindale(5000 rubs)",
        "relaxation shrinkage- wp",
        "relaxation shrinkage- wt",
        "res. to acc.ageing",
        "res. to low temp.",
        "res. to low temp.(-40°c for 6 hrs.)",
        "res.to acce. ageing(70±1°c/168hrs.)",
        "seal st.-wp n",
        "seal st.-wt n",
        "seam slippage (cm)-wp",
        "seam slippage (cm)-wt",
        "seam slippage of yarn(mm)-wp",
        "seam slippage of yarn(mm)-wt",
        "sp pu film- wp",
        "sp pu film- wt",
        "sp pu film-wp",
        "sp pu film-wt",
        "spreading speed bottom-after 3 wash",
        "ss-wp kgf",
        "ss-wt kgf",
        "type of weave",
        "warp_fibre",
        "water proofness initial (pa)",
        "water repellency",
        "water repellency- after 2 wash",
        "water repellency- after 5 wash",
        "water repellency- before wash",
        "water repellency-after5wash+line",
        "water repellency-after5wash+tumble",
        "water repellency-initial",
        "water resis.(6 kpa/min.)after 5wash",
        "water resistance-after 5 wash-250mm",
        "water resistance-after5wash-10000mm",
        "water resistance-before wash-250mm",
        "water resistance-beforewash-10000mm",
        "water soluble %",
        "water vapor res.re (m2/pa/w)",
        "watervaporresit.",
        "weft_fibre",
        "weight gsm",
        "weight gsm- coated",
        "weight oz/yd2",
        "whiteness ind-cie",
        "wick.height 5xhl after 10min.-wp",
        "wick.height 5xhl after 10min.-wt",
        "wick.height 5xhl after 30min.-wp",
        "wick.height 5xhl after 30min.-wt",
        "wick.height-original after10min.-wp",
        "wick.height-original after10min.-wt",
        "wick.height-original after30min.-wp",
        "wick.height-original after30min.-wt",
        "width cm",
        "width cm (c to c)",
        "width cm (l to l)",
        "width cm (p to p)",
        "width cm (s to s)",
        "width inch",
        "width mm",
        "width",
    ],
    "testing after printing": [
        "%bias",
        "%bow",
        "%skew",
        "abra emery cycle",
        "abso.of water drop-after washsec",
        "abso.of water drop-before sec",
        "absorption of water drop- sec",
        "add on(gms)",
        "blocking test",
        "breathtest-mg/cm2/h",
        "cf to light",
        "chunk_part",
        "deter.of shrink.after1wash @40°c-wp",
        "deter.of shrink.after1wash @40°c-wt",
        "finish",
        "flex res.-crack",
        "flex res.-flaking",
        "flex res.-wrinkle",
        "fr test (a. flame)",
        "fr test (a. glow)",
        "fr test (char length",
        "gloss value (gu)",
        "is_split_chunk",
        "majoraxis-drop spread-afterwashcm",
        "majoraxis-drop spread-beforewashcm",
        "metamerism f11/d65 mi",
        "nature of coating",
        "nature of dyes",
        "nature of fiber",
        "nir reflectance (%)",
        "original_stage_name",
        "peelrest.after50wash",
        "ph value",
        "ph value-other color",
        "ph value-white to pastel color",
        "pilling (7000 tours)",
        "pilling after (18000 revs.)",
        "pilling resis.martindale(5000 rubs)",
        "print_design_name",
        "print_name",
        "printed abrasion resistance using p600emery at 9kpa after 150 cycles",
        "printed abrasion resistance using unspecified abradant at 9kpa after 10000 cycles",
        "printed abrasion resistance using wool at 12kpa after 100000 cycles",
        "printed abrasion resistance using wool at 9kpa after 15000 cycles",
        "printed abrasion resistance using wool at 9kpa after 50000 cycles",
        "printed abrasion resistance using wool at 9kpa after 90000 cycles",
        "printed air permeability at 10 inch pressure in cm3/cm2/s",
        "printed air permeability at 10 inch pressure in ft3/ft2/s",
        "printed air permeability at 100 pas pressure in l/m2/s",
        "printed air permeability at 100 pas pressure in mm/s",
        "printed breaking strength of warp in dan",
        "printed breaking strength of warp in kgf",
        "printed breaking strength of warp in n",
        "printed breaking strength of weft in dan",
        "printed breaking strength of weft in kgf",
        "printed breaking strength of weft in n",
        "printed colourfastness to perspiration (acid) change in shade",
        "printed colourfastness to perspiration (acid) staining on acr",
        "printed colourfastness to perspiration (acid) staining on act",
        "printed colourfastness to perspiration (acid) staining on cot",
        "printed colourfastness to perspiration (acid) staining on nyl",
        "printed colourfastness to perspiration (acid) staining on pol",
        "printed colourfastness to perspiration (acid) staining on wol",
        "printed colourfastness to perspiration (alkaline) change in shade",
        "printed colourfastness to perspiration (alkaline) staining on acr",
        "printed colourfastness to perspiration (alkaline) staining on act",
        "printed colourfastness to perspiration (alkaline) staining on cot",
        "printed colourfastness to perspiration (alkaline) staining on nyl",
        "printed colourfastness to perspiration (alkaline) staining on pol",
        "printed colourfastness to perspiration (alkaline) staining on wol",
        "printed colourfastness to rubbing (dry)",
        "printed colourfastness to rubbing (dry)  wp",
        "printed colourfastness to rubbing (dry)  wt",
        "printed colourfastness to rubbing (wet)",
        "printed colourfastness to rubbing (wet)  wp",
        "printed colourfastness to rubbing (wet)  wt",
        "printed colourfastness to sea water change in shade",
        "printed colourfastness to sea water staining on acr",
        "printed colourfastness to sea water staining on act",
        "printed colourfastness to sea water staining on cot",
        "printed colourfastness to sea water staining on nyl",
        "printed colourfastness to sea water staining on pol",
        "printed colourfastness to sea water staining on wol",
        "printed colourfastness to washing change in shade",
        "printed colourfastness to washing staining on acr",
        "printed colourfastness to washing staining on act",
        "printed colourfastness to washing staining on cot",
        "printed colourfastness to washing staining on nyl",
        "printed colourfastness to washing staining on pol",
        "printed colourfastness to washing staining on wol",
        "printed colourfastness to water change in shade",
        "printed colourfastness to water staining on acr",
        "printed colourfastness to water staining on act",
        "printed colourfastness to water staining on cot",
        "printed colourfastness to water staining on nyl",
        "printed colourfastness to water staining on pol",
        "printed colourfastness to water staining on wol",
        "printed delta e (δe) under primary light (f11 10°)",
        "printed delta e (δe) under secondary light (d65 10°)",
        "printed delta e (δe) value",
        "printed dimensional stability of warp after one washes",
        "printed dimensional stability of warp in hot water",
        "printed dimensional stability of weft after one washes",
        "printed dimensional stability of weft in hot water",
        "printed ends per 10cms",
        "printed ends per cms",
        "printed ends per dm",
        "printed ends per inch",
        "printed fabric elongation in warp direction (fabric growth after 30mm-wp)",
        "printed fabric elongation in warp direction (wp)",
        "printed fabric elongation in weft direction (fabric growth after 30mm-wt)",
        "printed fabric elongation in weft direction (of fabric stretch-wt(15n))",
        "printed fabric elongation in weft direction (wt(15n))",
        "printed fabric elongation in weft direction (wt)",
        "printed picks per 10cms",
        "printed picks per cms",
        "printed picks per dm",
        "printed picks per inch",
        "printed tear strength of warp in dan",
        "printed tear strength of warp in kgf",
        "printed tear strength of warp in lbf",
        "printed tear strength of warp in n",
        "printed tear strength of warp using elmendorf method in dan",
        "printed tear strength of weft in dan",
        "printed tear strength of weft in kgf",
        "printed tear strength of weft in lbf",
        "printed tear strength of weft in n",
        "printed tear strength of weft using elmendorf method in dan",
        "printed thickness in mm",
        "printed water proofness tested at 20°c",
        "printed water proofness tested at 30°c for 30 minutes",
        "printed water proofness tested at 30°c for 60 minutes",
        "printed water proofness using dynamic method",
        "res. to acc.ageing",
        "res. to low temp.",
        "res. to low temp.(-40°c for 6 hrs.)",
        "resistance to flame-wp",
        "resistance to flame-wt",
        "seam slippage of yarn(mm)-wp",
        "seam slippage of yarn(mm)-wt",
        "sp pu film- wp",
        "sp pu film- wt",
        "sp pu film-wp",
        "sp pu film-wt",
        "spreading speed bottom-after 3 wash",
        "ss-wp kgf",
        "ss-wt kgf",
        "type of weave",
        "warp_fibre",
        "water repellency",
        "water repellency- after 5 wash",
        "water repellency- before wash",
        "water repellency-initial",
        "water resis.(6 kpa/min.)after 5wash",
        "water resistance-after 5 wash-250mm",
        "water resistance-after5wash-10000mm",
        "water resistance-before wash-250mm",
        "water resistance-beforewash-10000mm",
        "weft_fibre",
        "weight gsm",
        "width cm",
        "width cm (c to c)",
        "width cm (l to l)",
        "width cm (p to p)",
        "width cm (s to s)",
        "width mm",
        "gsm",
        "weight",
    ],
    "testing after processing": [
        "% fabric distortion",
        "% fabric stability wp",
        "% fabric stability wt",
        "%bias",
        "%bow",
        "%bow-inch",
        "%ch dimen alkali(42%koh24hrs)wp",
        "%ch dimen alkali(42%koh24hrs)wt",
        "%skew",
        "%skew-inch",
        "abcap%(30%koh)-wp",
        "abcap%(30%koh)-wt",
        "abra emery cycle",
        "abso.of water drop-after washsec",
        "abso.of water drop-before sec",
        "absorption of water drop- sec",
        "add on %",
        "add on(gms)",
        "adhesion to backing (n/cm) 8310 x",
        "adhesion to backing (n/cm) 8310se",
        "adhesion to backing (n/cm) 832 mpx",
        "adhesion to backing (n/cm) 837 x",
        "adhesion to backing (n/cm) 839",
        "adhesion to backing (n/cm)-523",
        "adhesion to backing (n/cm)-525",
        "adhesion to backing(n/cm)523(24hrs)",
        "adhesion to backing(n/cm)523/24hrs.",
        "adhesion to backing(n/cm)525(24hrs)",
        "adhesion to backing(n/cm)525/24hrs.",
        "apcycl@1/2 inch (cfm)",
        "apcycl@1/2 inch (l/m2/s)",
        "appearance after 5x hl",
        "bend lngth-wp cms",
        "bend lngth-wp mn.cm2",
        "bend lngth-wt cms",
        "bias/bow%",
        "bleeding",
        "bleeding test--staining on cotton",
        "bleeding test-change in shade",
        "blocking test",
        "bow-mm",
        "breathtest-mg/cm2/h",
        "caact(30%koh)-wp",
        "caact(30%koh)-wt",
        "calendaring_details",
        "cf to light",
        "ch in dimensional",
        "ch in weight",
        "ch phy pro(100°c/2h)",
        "ch phy pro(71°c/30m)",
        "chunk_part",
        "co-eff.frict-wt",
        "co-eff.frict.wp",
        "crimp test % -wp",
        "crimp test % -wt",
        "deter.of shrink.after1wash @40°c-wp",
        "deter.of shrink.after1wash @40°c-wt",
        "deter.of shrink.after5wash @40°c-wp",
        "deter.of shrink.after5wash @40°c-wt",
        "extension at 20lbf (%) wp",
        "extension at 20lbf (%) wt",
        "fabric distortion mm",
        "finish",
        "finish content%",
        "flex res.-crack",
        "flex res.-flaking",
        "flex res.-wrinkle",
        "fr test (a. flame)",
        "fr test (a. glow)",
        "fr test (char length",
        "gloss value (gu)",
        "hydrostatic test cm",
        "is_split_chunk",
        "majoraxis-drop spread-afterwashcm",
        "majoraxis-drop spread-beforewashcm",
        "melting point",
        "metamerism f11/d65 mi",
        "nature of coating",
        "nature of dyes",
        "nature of fiber",
        "nir reflectance (%)",
        "oil content%",
        "oil repellency",
        "original_stage_name",
        "peel st.-wp gmf",
        "peel st.-wt gmf",
        "peelrest.after50wash",
        "per.of set %shrink.-wp",
        "per.of set %shrink.-wt",
        "per.of set ap@1/2 inch (ft3/ft2/m)",
        "per.of set thick inch",
        "petroleum ether extractable%",
        "ph value",
        "ph value-other color",
        "ph value-white to pastel color",
        "pilling (7000 tours)",
        "pilling after (18000 revs.)",
        "pilling resis.martindale(5000 rubs)",
        "pilling resistance",
        "processed abrasion resistance using p600emery at 9kpa after 150 cycles",
        "processed abrasion resistance using p600emery at 9kpa after 30 cycles",
        "processed abrasion resistance using p600emery at 9kpa after 50 cycles",
        "processed abrasion resistance using unspecified abradant at 9kpa after 10000 cycles",
        "processed abrasion resistance using unspecified abradant at unspecified pressure after 20000 cycles",
        "processed abrasion resistance using unspecified abradant at unspecified pressure after unspecified number of cycles",
        "processed abrasion resistance using wool at 12kpa after 100000 cycles",
        "processed abrasion resistance using wool at 9kpa after 15000 cycles",
        "processed abrasion resistance using wool at 9kpa after 30000 cycles",
        "processed abrasion resistance using wool at 9kpa after 50000 cycles",
        "processed abrasion resistance using wool at 9kpa after 60000 cycles",
        "processed abrasion resistance using wool at 9kpa after 90000 cycles",
        "processed air permeability at 1/2 inch pressure in ft3/ft2/m",
        "processed air permeability at 1/2 inch pressure in ft3/ft2/s",
        "processed air permeability at 1/2 inch pressure in l/m2/s",
        "processed air permeability at 10 inch pressure in cm3/cm2/s",
        "processed air permeability at 10 inch pressure in ft3/ft2/m",
        "processed air permeability at 10 inch pressure in ft3/ft2/s",
        "processed air permeability at 100 pas pressure in cm3/cm2/s",
        "processed air permeability at 100 pas pressure in l/m2/s",
        "processed air permeability at 100 pas pressure in mm/s",
        "processed air permeability at 200 pas pressure in mm/s",
        "processed air permeability at 2500 pas pressure in l/m2/s",
        "processed air permeability at 25mm pressure in cc/sec/cm2",
        "processed air permeability at 500 pas pressure in l/m2/s",
        "processed breaking strength of warp in dan",
        "processed breaking strength of warp in kgf",
        "processed breaking strength of warp in lbf",
        "processed breaking strength of warp in n",
        "processed breaking strength of weft in dan",
        "processed breaking strength of weft in kgf",
        "processed breaking strength of weft in lbf",
        "processed breaking strength of weft in n",
        "processed bursting strength in bar",
        "processed bursting strength in kgf/cm²",
        "processed bursting strength in psi",
        "processed colourfastness to perspiration (acid) change in shade",
        "processed colourfastness to perspiration (acid) staining on acr",
        "processed colourfastness to perspiration (acid) staining on act",
        "processed colourfastness to perspiration (acid) staining on cot",
        "processed colourfastness to perspiration (acid) staining on nyl",
        "processed colourfastness to perspiration (acid) staining on pol",
        "processed colourfastness to perspiration (acid) staining on wol",
        "processed colourfastness to perspiration (alkaline) change in shade",
        "processed colourfastness to perspiration (alkaline) staining on acr",
        "processed colourfastness to perspiration (alkaline) staining on act",
        "processed colourfastness to perspiration (alkaline) staining on cot",
        "processed colourfastness to perspiration (alkaline) staining on nyl",
        "processed colourfastness to perspiration (alkaline) staining on pol",
        "processed colourfastness to perspiration (alkaline) staining on wol",
        "processed colourfastness to perspiration change in shade",
        "processed colourfastness to perspiration staining on acr",
        "processed colourfastness to perspiration staining on act",
        "processed colourfastness to perspiration staining on cot",
        "processed colourfastness to perspiration staining on nyl",
        "processed colourfastness to perspiration staining on pol",
        "processed colourfastness to perspiration staining on wol",
        "processed colourfastness to rubbing (dry)",
        "processed colourfastness to rubbing (dry)  wp",
        "processed colourfastness to rubbing (dry)  wt",
        "processed colourfastness to rubbing (wet)",
        "processed colourfastness to rubbing (wet)  wp",
        "processed colourfastness to rubbing (wet)  wt",
        "processed colourfastness to sea water change in shade",
        "processed colourfastness to sea water staining on acr",
        "processed colourfastness to sea water staining on act",
        "processed colourfastness to sea water staining on cot",
        "processed colourfastness to sea water staining on nyl",
        "processed colourfastness to sea water staining on pol",
        "processed colourfastness to sea water staining on wol",
        "processed colourfastness to washing change in shade",
        "processed colourfastness to washing staining on acr",
        "processed colourfastness to washing staining on act",
        "processed colourfastness to washing staining on cot",
        "processed colourfastness to washing staining on nyl",
        "processed colourfastness to washing staining on pol",
        "processed colourfastness to washing staining on wol",
        "processed colourfastness to water change in shade",
        "processed colourfastness to water staining on acr",
        "processed colourfastness to water staining on act",
        "processed colourfastness to water staining on cot",
        "processed colourfastness to water staining on nyl",
        "processed colourfastness to water staining on pol",
        "processed colourfastness to water staining on wol",
        "processed delta e (δe) under primary light (f11 10°)",
        "processed delta e (δe) under secondary light (d65 10°)",
        "processed delta e (δe) value",
        "processed dimensional stability of warp after 2 washes",
        "processed dimensional stability of warp after 3 washes",
        "processed dimensional stability of warp after 5 washes",
        "processed dimensional stability of warp after one washes",
        "processed dimensional stability of warp in cold water",
        "processed dimensional stability of warp in hot water",
        "processed dimensional stability of warp to heat",
        "processed dimensional stability of warp to heat at 150°c/15minutes",
        "processed dimensional stability of weft after 2 washes",
        "processed dimensional stability of weft after 3 washes",
        "processed dimensional stability of weft after 5 washes",
        "processed dimensional stability of weft after one washes",
        "processed dimensional stability of weft in cold water",
        "processed dimensional stability of weft in hot water",
        "processed dimensional stability of weft to heat",
        "processed dimensional stability of weft to heat at 150°c/15minutes",
        "processed ends per 10cms",
        "processed ends per cms",
        "processed ends per dm",
        "processed ends per inch",
        "processed fabric elongation in warp direction (fabric growth after 30mm-wp)",
        "processed fabric elongation in warp direction (wp max.force)",
        "processed fabric elongation in warp direction (wp)",
        "processed fabric elongation in weft direction (fabric growth after 30mm-wt)",
        "processed fabric elongation in weft direction (of fabric stretch-wt(15n))",
        "processed fabric elongation in weft direction (wt max.force)",
        "processed fabric elongation in weft direction (wt(15n))",
        "processed fabric elongation in weft direction (wt(2.7 kgf))",
        "processed fabric elongation in weft direction (wt)",
        "processed picks per 10cms",
        "processed picks per cms",
        "processed picks per dm",
        "processed picks per inch",
        "processed tear strength of warp in dan",
        "processed tear strength of warp in gms",
        "processed tear strength of warp in kgf",
        "processed tear strength of warp in lbf",
        "processed tear strength of warp in mn",
        "processed tear strength of warp in n",
        "processed tear strength of warp using elmendorf method in dan",
        "processed tear strength of warp using elmendorf method in kgf",
        "processed tear strength of warp using elmendorf method in lbf",
        "processed tear strength of warp using elmendorf method in n",
        "processed tear strength of weft in dan",
        "processed tear strength of weft in gms",
        "processed tear strength of weft in kgf",
        "processed tear strength of weft in lbf",
        "processed tear strength of weft in n",
        "processed tear strength of weft using elmendorf method in dan",
        "processed tear strength of weft using elmendorf method in kgf",
        "processed tear strength of weft using elmendorf method in lbf",
        "processed tear strength of weft using elmendorf method in n",
        "processed thickness in inch",
        "processed thickness in micron",
        "processed thickness in mil",
        "processed thickness in mm",
        "processed water proofness tested at 100°c",
        "processed water proofness tested at 20°c",
        "processed water proofness tested at 30°c for 30 minutes",
        "processed water proofness tested at 30°c for 60 minutes",
        "processed water proofness tested at 80°c with minimum pressure of 80 cm",
        "processed water proofness using dynamic method",
        "processed water proofness with minimum pressure of 0.4 bar",
        "relaxation shrinkage- wp",
        "relaxation shrinkage- wt",
        "res. to low temp.",
        "res. to low temp.(-40°c for 6 hrs.)",
        "resistance to flame-wp",
        "resistance to flame-wt",
        "seam slippage (cm)-wp",
        "seam slippage (cm)-wt",
        "seam slippage (mm)-wp",
        "seam slippage (mm)-wt",
        "seam slippage of yarn(mm)-wp",
        "seam slippage of yarn(mm)-wt",
        "selvage req. bs-wp lbf",
        "selvage req. width inch",
        "shade_of_fabric",
        "silicone finish %",
        "size content%",
        "skew-mm",
        "skewing of-wp mm",
        "snagging resistance",
        "sp pu film- wp",
        "sp pu film- wt",
        "sp pu film-wp",
        "sp pu film-wt",
        "spreading speed bottom-after 3 wash",
        "ss-wp kgf",
        "ss-wt kgf",
        "thickmm-micro thick tester classic",
        "type of weave",
        "warp_fibre",
        "water proofness initial (pa)",
        "water repellency",
        "water repellency- after 10 wash",
        "water repellency- after 2 wash",
        "water repellency- after 20 wash",
        "water repellency- after 5 wash",
        "water repellency- back",
        "water repellency- before wash",
        "water repellency- front",
        "water repellency-after5wash+line",
        "water repellency-after5wash+tumble",
        "water repellency-initial",
        "water resis.(6 kpa/min.)after 5wash",
        "water resistance-after 5 wash-250mm",
        "water resistance-after5wash-10000mm",
        "water resistance-before wash-250mm",
        "water resistance-beforewash-10000mm",
        "water soluble %",
        "water vapor res.re (m2/pa/w)",
        "weft_fibre",
        "weight",
        "weight gsm",
        "weight gsm- coated",
        "weight oz/yd",
        "weight oz/yd2",
        "whiteness ind-cie",
        "wick.height 5xhl after 10min.-wp",
        "wick.height 5xhl after 10min.-wt",
        "wick.height 5xhl after 30min.-wp",
        "wick.height 5xhl after 30min.-wt",
        "wick.height-original after10min.-wp",
        "wick.height-original after10min.-wt",
        "wick.height-original after30min.-wp",
        "wick.height-original after30min.-wt",
        "width cm",
        "width cm (c to c)",
        "width cm (l to l)",
        "width cm (p to p)",
        "width cm (s to s)",
        "width inch",
        "width mm",
        "air permeability",
        "ap",
        "gsm",
        "weight",
        "colour fastness",
    ],
    "testing after weaving": [
        "% fabric stability wp",
        "% fabric stability wt",
        "bend lngth-wp cms",
        "bend lngth-wp cms (nozzle)",
        "bend lngth-wp mn.cm2",
        "bend lngth-wt cms",
        "chunk_part",
        "crimp test % -wp",
        "crimp test % -wt",
        "grey air permeability at 1/2 inch pressure in cm3/cm2/s",
        "grey air permeability at 1/2 inch pressure in ft3/ft2/m",
        "grey air permeability at 1/2 inch pressure in l/m2/s",
        "grey air permeability at 10 inch pressure in cm3/cm2/s",
        "grey air permeability at 10 inch pressure in ft3/ft2/m",
        "grey air permeability at 10 inch pressure in ft3/ft2/s",
        "grey air permeability at 100 pas pressure in cm3/cm2/s",
        "grey air permeability at 100 pas pressure in l/m2/s",
        "grey air permeability at 100 pas pressure in mm/s",
        "grey air permeability at 200 pas pressure in l/dm2/m",
        "grey air permeability at 200 pas pressure in l/m2/s",
        "grey air permeability at 200 pas pressure in mm/s",
        "grey air permeability at 2500 pas pressure in l/m2/s",
        "grey air permeability at 500 pas pressure in l/m2/s",
        "grey breaking strength of warp in dan",
        "grey breaking strength of warp in kgf",
        "grey breaking strength of warp in kn/mtr",
        "grey breaking strength of warp in lbf",
        "grey breaking strength of warp in n",
        "grey breaking strength of weft in dan",
        "grey breaking strength of weft in kgf",
        "grey breaking strength of weft in kn/mtr",
        "grey breaking strength of weft in lbf",
        "grey breaking strength of weft in n",
        "grey bursting strength in kgf/cm²",
        "grey delta e (δe) value",
        "grey dimensional stability of warp after one washes",
        "grey dimensional stability of weft after one washes",
        "grey ends per 10cms",
        "grey ends per cms",
        "grey ends per dm",
        "grey ends per inch",
        "grey ends per inch at filler",
        "grey ends per inch at nozzle",
        "grey fabric elongation (wp (nozzle))",
        "grey fabric elongation (wt (nozzle))",
        "grey fabric elongation in warp direction (wp)",
        "grey fabric elongation in weft direction (wt(15n))",
        "grey fabric elongation in weft direction (wt)",
        "grey picks per 10cms",
        "grey picks per cms",
        "grey picks per dm",
        "grey picks per inch",
        "grey picks per inch at nozzle",
        "grey tear strength of warp in dan",
        "grey tear strength of warp in kgf",
        "grey tear strength of warp in lbf",
        "grey tear strength of warp in mn",
        "grey tear strength of warp in n",
        "grey tear strength of warp using elmendorf method in dan",
        "grey tear strength of warp using elmendorf method in kgf",
        "grey tear strength of warp using elmendorf method in n",
        "grey tear strength of weft in dan",
        "grey tear strength of weft in kgf",
        "grey tear strength of weft in lbf",
        "grey tear strength of weft in n",
        "grey tear strength of weft using elmendorf method in dan",
        "grey tear strength of weft using elmendorf method in kgf",
        "grey tear strength of weft using elmendorf method in n",
        "grey thickness in inch",
        "grey thickness in micron",
        "grey thickness in mil",
        "grey thickness in mm",
        "grey thickness in mm at filler",
        "grey thickness in mm at nozzle",
        "index puncture n",
        "is_split_chunk",
        "nature of fiber",
        "original_stage_name",
        "size content%",
        "sizing_details",
        "thickmm-micro thick tester classic",
        "type of weave",
        "type of weave (nozzle)",
        "w permea(l/cm2/s)",
        "warp_fibre",
        "weave",
        "weft_fibre",
        "weight",
        "weight gsm",
        "weight gsm (nozzle)",
        "weight oz/yd2",
        "width cm",
        "width cm (nozzle)",
        "width cm (s to s)",
        "width inch",
        "width mm",
        "air permeability",
        "ap",
        "gsm",
        "weight",
    ],
    "vdr": [
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "finishing details after processing",
        "full article",
        "machine used in processing",
        "vdr",
        "vdr drying",
        "vdr-1",
    ],
    "warp and weft yarn details": [
        "article number",
        "article_no",
        "bomid_warp",
        "bomid_weft",
        "drawing and texturing in warp yarn",
        "drawing and texturing in weft yarn",
        "dullness/brightness of warp",
        "fibre in warp",
        "fibre in weft",
        "filament in warp yarn",
        "filament in weft yarn",
        "full_article",
        "itemid_warp",
        "itemid_weft",
        "number of beams",
        "number of twist in warp yarn",
        "number of twist in weft yarn",
        "ply in warp yarn",
        "ply in weft yarn",
        "quality number",
        "reed space",
        "shade code of warp",
        "shade code of weft",
        "shade of warp yarn",
        "total ends",
        "twist direction in warp yarn",
        "twist direction in weft yarn",
        "type of warping",
        "warp count",
        "warp denier",
        "warp yarn elongation",
        "warp yarn shrinkage",
        "warp yarn tenacity",
        "warp yarn type",
        "warp yarn vendor",
        "weave of fabric",
        "weft count",
        "weft denier",
        "weft yarn brightness",
        "weft yarn elongation",
        "weft yarn shrinkage",
        "weft yarn sizing details",
        "weft yarn tenacity",
        "weft yarn type",
        "weft yarn vendor",
        "width of griege fabric",
    ],
    "washing": [
        "article no",
        "article number",
        "article_no",
        "calendaring details",
        "finishing details after processing",
        "full article",
        "jet",
        "machine used in processing",
        "no of ends",
        "no. of ends",
        "speed",
        "temp",
        "tension",
        "water",
    ],
    "weaving": [
        "article no",
        "article number",
        "article_no",
        "back rest position",
        "beam winding tension",
        "beaming speed",
        "config_id",
        "creel tension (post position)",
        "density",
        "drawing seq body",
        "drawing seq sleavege",
        "full article",
        "full_article",
        "grey width(cms)",
        "height & amound of heald frames",
        "lease position",
        "loom speed rpm",
        "no of heald frames",
        "number_of_ends_in_warp",
        "pick",
        "press roll pressure",
        "pump stroke ( mm )",
        "reed",
        "reed space (inches)",
        "s.wrap tension contribution",
        "shed crossing timing",
        "sizing details",
        "speed",
        "total ends",
        "total ends of warp",
        "traverse",
        "warp beam tension",
        "warping m/c speed",
        "water ltr/kg",
        "water ltr/min",
        "weave",
        "weave_of_fabric",
        "weft arrival timing",
        "weft cutting timing",
    ],
}


# Initialize session state
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "show_chunks" not in st.session_state:
        st.session_state.show_chunks = False
    if "retrieved_chunks" not in st.session_state:
        st.session_state.retrieved_chunks = []
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
    if "system_checks_done" not in st.session_state:
        st.session_state.system_checks_done = False


# Query Analyzer (from your original code)
class QueryAnalyzer:
    def analyze(self, query):
        query_lower = query.lower()
        if any(x in query_lower for x in ["compare", "vs", "difference"]):
            return "comparison"
        if any(x in query_lower for x in ["route", "process", "warping", "sizing"]):
            return "process"
        if any(
            x in query_lower
            for x in ["gsm", "denier", "weight", "coating", "total ends"]
        ):
            return "parameter"
        return "general"


# Prompt Manager (from your original code)
class PromptManager:
    def __init__(self):
        self.templates = {
            "parameter": "You are a textile expert. Use the context to answer parameter-based queries.\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:",
            "process": "Explain the textile process using the context.\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:",
            "comparison": "Compare the items using the below context.\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:",
            "general": "Answer the textile-related question based on context.\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:",
        }

    def get_prompt(self, qtype, context, question):
        return self.templates.get(qtype, self.templates["general"]).format(
            context=context, question=question
        )


# Fixed Weaviate Hybrid Retriever
class WeaviateHybridRetriever:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.use_mock = False

        try:
            if not WEAVIATE_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise Exception("Required libraries not available")

            self.client = WeaviateClient(WEAVIATE_URL)

            # Test connection
            if not self.client.is_ready():
                raise Exception("Weaviate server not ready")

            # Check if class exists
            schema = self.client.schema.get()
            if not any(cls["class"] == CLASS_NAME for cls in schema.get("classes", [])):
                raise Exception(f"Class '{CLASS_NAME}' not found")

            # Initialize embedding model
            self.embedder = SentenceTransformer(MODEL_NAME)
            self.process_names = PROCESS_NAMES
            self.process_parameters = PROCESS_PARAMETERS

            # Test query to ensure everything works
            test_result = (
                self.client.query.get(CLASS_NAME, ["content"]).with_limit(1).do()
            )
            raw_results = test_result.get("data", {}).get("Get", {}).get(CLASS_NAME, [])

            if self.debug_mode:
                st.success(
                    f"✅ Weaviate retriever initialized successfully. Test query returned {len(raw_results)} result(s)"
                )

        except Exception as e:
            if self.debug_mode:
                st.error(f"❌ Weaviate initialization failed: {str(e)}")
                st.warning("🔄 Falling back to mock retriever for demo purposes")

            self.use_mock = True
            self._init_mock_retriever()

    def _init_mock_retriever(self):
        """Initialize mock retriever for when Weaviate is not available"""
        self.mock_documents = [
            {
                "content": "Weaving is a fundamental textile process where yarns are interlaced to form fabric. The warp yarns run lengthwise while weft yarns run crosswise.",
                "metadata": {
                    "article": "demo001",
                    "stage": "weaving",
                    "process": "weaving",
                },
            },
            {
                "content": "Dyeing process involves applying color to textile materials using various chemical processes. Temperature and time are critical parameters.",
                "metadata": {
                    "article": "demo002",
                    "stage": "dyeing",
                    "process": "dyeing",
                },
            },
            {
                "content": "Sizing is applied to warp yarns to improve their strength and reduce breakage during weaving. Common sizing agents include starch and PVA.",
                "metadata": {
                    "article": "demo003",
                    "stage": "sizing",
                    "process": "sizing",
                },
            },
        ]

    def extract_process_and_parameters(self, query: str):
        """Extract processes, parameters, and articles from query"""
        if self.use_mock:
            return [], [], []

        query_lower = query.lower()
        matched_processes = []
        matched_parameters = []

        # Match process names
        for process in self.process_names:
            if process in query_lower:
                matched_processes.append(process)

        # Match parameters
        for param_list in self.process_parameters.values():
            for param in param_list:
                if param.lower() in query_lower:
                    matched_parameters.append(param)

        # Capture article numbers (4-6 digits)
        all_numbers = re.findall(r"\b\d{4,6}\b", query_lower)
        articles = []

        for number in all_numbers:
            # Check if it's preceded by a keyword like "around", "near to", etc.
            keyword_pattern = rf"(around|close to|less than|greater than|near to|more than)\s+{number}"
            is_keyworded = re.search(keyword_pattern, query_lower)

            # Explicit "article 8090" capture
            explicit_pattern = rf"article\s+{number}"
            is_explicit = re.search(explicit_pattern, query_lower)

            if is_explicit or not is_keyworded:
                articles.append(number)

        return matched_processes, matched_parameters, list(set(articles))

    def retrieve(self, query, k=30):
        """Main retrieval method"""
        if self.use_mock:
            return self._mock_retrieve(query, k)

        try:
            if self.debug_mode:
                st.write(f"📡 Sending hybrid query to Weaviate: '{query}'")

            # Generate query vector
            query_vector = self.embedder.encode(
                query, normalize_embeddings=True
            ).tolist()

            # Extract filters
            processes, parameters, articles = self.extract_process_and_parameters(query)

            if self.debug_mode:
                st.write(f"🔍 Matched Processes: {processes}")
                st.write(f"🔍 Matched Parameters: {parameters}")
                st.write(f"🔍 Matched Articles: {articles}")

            # Build filters
            article_filters = [
                {"path": ["article"], "operator": "Equal", "valueText": art}
                for art in articles
            ]
            param_filters = [
                {
                    "path": ["parameter_names"],
                    "operator": "ContainsAny",
                    "valueText": [param.lower()],
                }
                for param in parameters
            ]
            stage_filters = [
                {"path": ["stage"], "operator": "Equal", "valueText": stage.lower()}
                for stage in processes
            ]

            compound_filters = []
            if article_filters:
                compound_filters.append({"operator": "Or", "operands": article_filters})
            if param_filters:
                compound_filters.append({"operator": "Or", "operands": param_filters})
            if stage_filters:
                compound_filters.append({"operator": "Or", "operands": stage_filters})

            where_filter = (
                {"operator": "And", "operands": compound_filters}
                if compound_filters
                else None
            )

            if where_filter and self.debug_mode:
                st.write(f"🔍 Filters Applied: {json.dumps(where_filter, indent=2)}")

            # Query with filters
            query_obj = self.client.query.get(CLASS_NAME, ["content", "metadata"])
            if where_filter:
                query_obj = query_obj.with_where(where_filter)

            response = (
                query_obj.with_hybrid(query=query, vector=query_vector, alpha=0.5)
                .with_limit(k)
                .do()
            )

            raw_hits = response.get("data", {}).get("Get", {}).get(CLASS_NAME)

            # Fallback: No hits with filters
            if not raw_hits and where_filter:
                if self.debug_mode:
                    st.warning(
                        "⚠️ No results with metadata filter. Retrying without filter..."
                    )

                response = (
                    self.client.query.get(CLASS_NAME, ["content", "metadata"])
                    .with_hybrid(query=query, vector=query_vector, alpha=0.5)
                    .with_limit(k)
                    .do()
                )
                raw_hits = response.get("data", {}).get("Get", {}).get(CLASS_NAME)

            if not raw_hits:
                if self.debug_mode:
                    st.warning("⚠️ Still no results after fallback.")
                return []

            # Process results
            results = []
            for hit in raw_hits:
                content = hit.get("content", "")
                meta = hit.get("metadata", {})
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except:
                        meta = {"raw": meta}
                results.append(Document(page_content=content, metadata=meta))

            if self.debug_mode:
                st.write(f"✅ Retrieved {len(results)} documents.")

            return results

        except Exception as e:
            if self.debug_mode:
                st.error(f"❌ Retrieval error: {str(e)}")
            return []

    def _mock_retrieve(self, query, k):
        """Mock retrieval for demo purposes"""
        query_lower = query.lower()
        results = []

        for doc in self.mock_documents:
            content = doc["content"].lower()
            if any(word in content for word in query_lower.split()):
                results.append(
                    Document(page_content=doc["content"], metadata=doc["metadata"])
                )

        # If no matches, return all documents
        if not results:
            results = [
                Document(page_content=doc["content"], metadata=doc["metadata"])
                for doc in self.mock_documents
            ]

        return results[:k]


# System checks
def run_system_checks():
    """Run comprehensive system checks"""
    checks = {}

    # 1. Check Weaviate connection
    if WEAVIATE_AVAILABLE:
        try:
            client = WeaviateClient(WEAVIATE_URL)
            is_ready = client.is_ready()
            if is_ready:
                # Check if class exists
                schema = client.schema.get()
                class_exists = any(
                    cls["class"] == CLASS_NAME for cls in schema.get("classes", [])
                )
                if class_exists:
                    # Count documents
                    try:
                        result = (
                            client.query.aggregate(CLASS_NAME).with_meta_count().do()
                        )
                        count = (
                            result.get("data", {})
                            .get("Aggregate", {})
                            .get(CLASS_NAME, [{}])[0]
                            .get("meta", {})
                            .get("count", 0)
                        )
                        checks["weaviate"] = {
                            "status": "success",
                            "message": f"Connected. Found {count} documents",
                        }
                    except:
                        checks["weaviate"] = {
                            "status": "warning",
                            "message": "Connected but cannot count documents",
                        }
                else:
                    checks["weaviate"] = {
                        "status": "error",
                        "message": f'Class "{CLASS_NAME}" not found',
                    }
            else:
                checks["weaviate"] = {"status": "error", "message": "Server not ready"}
        except Exception as e:
            checks["weaviate"] = {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
            }
    else:
        checks["weaviate"] = {
            "status": "error",
            "message": "Weaviate library not available",
        }

    # 2. Check embedding model
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            model = SentenceTransformer(MODEL_NAME)
            test_embedding = model.encode("test")
            checks["embedding"] = {
                "status": "success",
                "message": f"Model loaded. Dimension: {len(test_embedding)}",
            }
        except Exception as e:
            checks["embedding"] = {
                "status": "error",
                "message": f"Model loading failed: {str(e)}",
            }
    else:
        checks["embedding"] = {
            "status": "error",
            "message": "SentenceTransformers not available",
        }

    # 3. Check Azure OpenAI
    env_vars = ["AZURE_DEPLOYMENT_NAME", "AZURE_API_KEY", "AZURE_ENDPOINT"]
    missing_vars = [var for var in env_vars if not os.getenv(var)]

    if missing_vars:
        checks["azure"] = {
            "status": "warning",
            "message": f"Missing env vars: {missing_vars}",
        }
    elif AZURE_OPENAI_AVAILABLE:
        try:
            # Test configuration without actually calling the API
            checks["azure"] = {"status": "success", "message": "Configuration valid"}
        except Exception as e:
            checks["azure"] = {"status": "error", "message": f"Setup failed: {str(e)}"}
    else:
        checks["azure"] = {
            "status": "error",
            "message": "Azure OpenAI library not available",
        }

    return checks


# User Management Functions
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username, password):
    users = load_users()
    if username in users:
        return users[username]["password"] == hash_password(password)
    return False


def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists"

    users[username] = {
        "password": hash_password(password),
        "created_at": datetime.now().isoformat(),
    }
    save_users(users)
    return True, "User registered successfully"


# Chat History Management
def get_chat_history_file(username):
    return os.path.join(CHAT_HISTORY_DIR, f"{username}_history.json")


def load_chat_history(username):
    history_file = get_chat_history_file(username)
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def save_chat_history(username, history):
    history_file = get_chat_history_file(username)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def clear_chat_history(username):
    history_file = get_chat_history_file(username)
    if os.path.exists(history_file):
        os.remove(history_file)


# Initialize chatbot with proper error handling
@st.cache_resource
def initialize_chatbot(debug_mode=False):
    try:
        retriever = WeaviateHybridRetriever(debug_mode=debug_mode)

        # Try to initialize Azure OpenAI
        llm = None
        if AZURE_OPENAI_AVAILABLE:
            try:
                deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")
                api_key = os.getenv("AZURE_API_KEY")
                endpoint = os.getenv("AZURE_ENDPOINT")

                if all([deployment_name, api_key, endpoint]):
                    llm = AzureChatOpenAI(
                        deployment_name=deployment_name,
                        api_key=api_key,
                        azure_endpoint=endpoint,
                        api_version="2024-04-01-preview",
                        temperature=0.2,
                    )
                    if debug_mode:
                        st.success("✅ Azure OpenAI initialized")
                else:
                    if debug_mode:
                        st.warning("⚠️ Azure OpenAI env vars not set")
            except Exception as e:
                if debug_mode:
                    st.error(f"❌ Azure OpenAI init failed: {str(e)}")

        prompter = PromptManager()
        analyzer = QueryAnalyzer()

        return retriever, llm, prompter, analyzer

    except Exception as e:
        if debug_mode:
            st.error(f"❌ Chatbot initialization failed: {str(e)}")
        return None, None, None, None


# Process query with fallback
def process_query(query, retriever, llm, prompter, analyzer, debug_mode=False):
    try:
        if debug_mode:
            st.write("🔄 Processing query...")

        query_type = analyzer.analyze(query)

        # Retrieve documents
        docs = retriever.retrieve(query, k=60)

        if debug_mode:
            st.write(f"📚 Retrieved {len(docs)} documents")

        # Prepare context
        if docs:
            # Use TokenTextSplitter if available, otherwise simple splitting
            if LANGCHAIN_AVAILABLE:
                token_splitter = TokenTextSplitter(chunk_size=1500, chunk_overlap=0)
                split_docs = []
                for doc in docs[:25]:
                    splits = token_splitter.split_text(doc.page_content)
                    for split in splits:
                        split_docs.append(
                            Document(page_content=split, metadata=doc.metadata)
                        )
                final_chunks = split_docs[:25]
            else:
                final_chunks = docs[:25]

            context = "\n\n".join([f"- {doc.page_content}" for doc in final_chunks])
        else:
            final_chunks = []
            context = ""

        # Generate response
        prompt = prompter.get_prompt(query_type, context, query)

        if llm and context:
            try:
                response = llm.invoke(prompt)
                answer = (
                    response.content if hasattr(response, "content") else str(response)
                )
            except Exception as e:
                if debug_mode:
                    st.error(f"LLM error: {str(e)}")
                answer = generate_fallback_response(query, docs)
        else:
            answer = generate_fallback_response(query, docs)

        # Prepare chunk data
        chunk_data = []
        for i, doc in enumerate(final_chunks, 1):
            meta = doc.metadata
            chunk_data.append(
                {
                    "chunk_id": i,
                    "content": doc.page_content,
                    "article": meta.get("article", "N/A"),
                    "stage": meta.get("stage", "N/A"),
                    "metadata": meta,
                }
            )

        return answer, chunk_data

    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        if debug_mode:
            st.error(error_msg)
            st.error(traceback.format_exc())
        return generate_fallback_response(query, []), []


def generate_fallback_response(query, docs):
    """Generate a fallback response when LLM is not available"""
    if docs:
        return f"""Based on the available documents, here's what I found regarding your query "{query}":

{docs[0].page_content[:500]}...

This information comes from our textile database. For more detailed information, please check the retrieved chunks or refine your query."""
    else:
        return f"""I understand you're asking about "{query}" in the context of textile processes. 

While I don't have specific documents available right now, I can tell you that this might relate to:
- Textile manufacturing processes
- Fabric properties and characteristics  
- Process parameters and optimization

Please try being more specific about the textile process you're interested in (weaving, dyeing, spinning, etc.) or check your Weaviate database connection."""


def show_system_status():
    """Show system status and checks"""
    st.subheader("🔧 System Status")

    if not st.session_state.system_checks_done:
        with st.spinner("Running system checks..."):
            checks = run_system_checks()
            st.session_state.system_checks = checks
            st.session_state.system_checks_done = True

    checks = st.session_state.get("system_checks", {})

    for component, result in checks.items():
        status = result["status"]
        message = result["message"]

        if status == "success":
            st.success(f"✅ {component.title()}: {message}")
        elif status == "warning":
            st.warning(f"⚠️ {component.title()}: {message}")
        else:
            st.error(f"❌ {component.title()}: {message}")

    if st.button("🔄 Refresh Checks"):
        st.session_state.system_checks_done = False
        st.rerun()


def show_auth_interface():
    st.title("🤖 Textile Chatbot - Login")

    # System status
    with st.expander("🔧 System Status", expanded=False):
        show_system_status()

    # Debug mode toggle
    st.session_state.debug_mode = st.checkbox(
        "🔧 Enable Debug Mode", value=st.session_state.debug_mode
    )

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if username and password:
                if authenticate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.chat_history = load_chat_history(username)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")

    with tab2:
        st.subheader("Register")
        new_username = st.text_input("Username", key="register_username")
        new_password = st.text_input(
            "Password", type="password", key="register_password"
        )
        confirm_password = st.text_input(
            "Confirm Password", type="password", key="confirm_password"
        )

        if st.button("Register"):
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    success, message = register_user(new_username, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Passwords do not match")
            else:
                st.warning("Please fill in all fields")


def show_chat_interface():
    st.title("🤖 Textile Industry Chatbot")

    # Initialize chatbot
    retriever, llm, prompter, analyzer = initialize_chatbot(
        debug_mode=st.session_state.debug_mode
    )

    if not retriever:
        st.error("Failed to initialize chatbot. Please check the system status.")
        return

    # Sidebar
    with st.sidebar:
        st.header(f"Welcome, {st.session_state.username}!")

        # Debug toggle
        new_debug_mode = st.checkbox("🔧 Debug Mode", value=st.session_state.debug_mode)
        if new_debug_mode != st.session_state.debug_mode:
            st.session_state.debug_mode = new_debug_mode
            st.rerun()

        # System status in sidebar
        if st.button("📊 System Status"):
            show_system_status()

        # History management
        st.subheader("📝 Chat History")
        history_length = len(st.session_state.chat_history)
        st.write(f"Current history: {history_length} messages")

        max_history = st.slider("Max History Messages", 0, 50, 10)

        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            clear_chat_history(st.session_state.username)
            st.success("Chat history cleared!")
            st.rerun()

        if st.button("🔄 Restart Chat"):
            st.session_state.chat_history = []
            st.session_state.show_chunks = False
            st.session_state.retrieved_chunks = []
            st.success("Chat restarted!")
            st.rerun()

        # Test button
        if st.button("🧪 Test Query"):
            test_query = "What is weaving process?"
            with st.spinner("Testing..."):
                answer, chunks = process_query(
                    test_query, retriever, llm, prompter, analyzer, debug_mode=True
                )
                st.write("**Test Result:**")
                st.write(answer)
                if chunks:
                    st.write(f"Retrieved {len(chunks)} chunks")

        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.chat_history = []
            st.session_state.show_chunks = False
            st.session_state.retrieved_chunks = []
            st.session_state.debug_mode = False
            st.session_state.system_checks_done = False
            st.rerun()

    # Debug panel
    if st.session_state.debug_mode:
        with st.expander("🔧 Debug Information", expanded=False):
            show_system_status()

    # Main chat area
    st.subheader("💬 Chat")

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            else:
                st.write(f"**Bot:** {message['content']}")

                # Add chunks button for bot responses
                if f"chunks_{i}" not in st.session_state:
                    st.session_state[f"chunks_{i}"] = False

                if st.button(f"Show Chunks", key=f"show_chunks_{i}"):
                    st.session_state[f"chunks_{i}"] = not st.session_state[
                        f"chunks_{i}"
                    ]

                if st.session_state[f"chunks_{i}"] and "chunks" in message:
                    with st.expander("📄 Retrieved Chunks", expanded=True):
                        for chunk in message["chunks"]:
                            st.write(
                                f"**Chunk {chunk['chunk_id']}** - Article: {chunk['article']}, Stage: {chunk['stage']}"
                            )
                            st.write(f"Content: {chunk['content'][:200]}...")
                            st.write("---")

    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Enter your message:", height=100)
        col1, col2 = st.columns([1, 4])

        with col1:
            submit_button = st.form_submit_button("Send")

        with col2:
            show_chunks_button = st.form_submit_button("🔍 Show Chunks")

    # Process user input
    if submit_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Limit history based on user preference
        if len(st.session_state.chat_history) > max_history * 2:
            st.session_state.chat_history = st.session_state.chat_history[
                -(max_history * 2) :
            ]

        # Process query
        with st.spinner("Processing your question..."):
            answer, chunks = process_query(
                user_input,
                retriever,
                llm,
                prompter,
                analyzer,
                debug_mode=st.session_state.debug_mode,
            )

            # Add bot response to history
            st.session_state.chat_history.append(
                {
                    "role": "bot",
                    "content": answer,
                    "chunks": chunks,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Save chat history
            save_chat_history(st.session_state.username, st.session_state.chat_history)

            # Store chunks for display
            st.session_state.retrieved_chunks = chunks

        st.rerun()

    # Show chunks separately if requested
    if show_chunks_button and user_input:
        with st.spinner("Retrieving chunks..."):
            _, chunks = process_query(
                user_input,
                retriever,
                llm,
                prompter,
                analyzer,
                debug_mode=st.session_state.debug_mode,
            )
            st.session_state.retrieved_chunks = chunks

        st.subheader("📄 Retrieved Chunks")
        if st.session_state.retrieved_chunks:
            for chunk in st.session_state.retrieved_chunks:
                with st.expander(
                    f"Chunk {chunk['chunk_id']} - Article: {chunk['article']}, Stage: {chunk['stage']}"
                ):
                    st.write(f"**Content:** {chunk['content']}")
                    st.write(f"**Metadata:** {chunk['metadata']}")
        else:
            st.write("No chunks retrieved.")


def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Textile Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    init_session_state()

    # Custom CSS
    st.markdown(
        """
    <style>
    .stTextArea textarea {
        font-size: 16px;
    }
    .stButton > button {
        width: 100%;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
    }
    .bot-message {
        background-color: #f5f5f5;
        text-align: left;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Show appropriate interface
    if not st.session_state.authenticated:
        show_auth_interface()
    else:
        show_chat_interface()


if __name__ == "__main__":
    main()
