# File: web_ui.py

from generative_mapper import recommend_best_match
import streamlit as st
import os
import yaml
from dotenv import load_dotenv
from pymongo import MongoClient
from embedding_utils import get_embedding
from mapper import find_best_matches

# ─── Environment + Config ───────────────────────────────
load_dotenv()
with open("config.yaml") as f:
    config = yaml.safe_load(f)

mongo_uri = os.getenv("MONGO_URI", config.get("mongo_uri"))
client = MongoClient(mongo_uri)
db = client["industry_mapping"]
isic_col = db[config["collections"]["isic"]]

# ─── Streamlit UI Settings ──────────────────────────────
st.set_page_config(page_title="ESIC to ISIC Mapper", layout="centered")
st.title("🔍 ESIC-to-ISIC Semantic Mapper")
st.caption("Match ESIC English titles to ISIC codes using configurable vector search.")

# ─── Sidebar: Parameters ────────────────────────────────
st.sidebar.header("⚙️ Advanced Options")
selected_model = st.sidebar.selectbox(
    "Embedding AI Model",
    options=[
             "mxbai-embed-large", 
            # "nomic-embed-text", 
             
            #  "bge-m3"
             ],
    index=0
)

selected_gen_model = st.sidebar.selectbox(
    "Generative AI Model",
    options=[None, "deepseek-coder-v2:latest", "gemma3:27b-it-qat", "qwen3:14b"],
    index=0
)

similarity_mode = st.sidebar.selectbox(
    "Similarity Metric",
    options=["cosine", "dotProduct", "distance"],
    index=0
)

full_text_mode = st.sidebar.selectbox(
    "Text Span",
    options=["Description only", "Description only with notes", ],
    index=0
)

selected_level = st.sidebar.selectbox(
    "ISIC Level",
    options=[ 4, 3, 2, 1],
    index=0
)
selected_section = st.sidebar.selectbox(
    "ISIC Section",
    options=[ None, 'Agriculture, forestry and fishing',	'Mining and quarrying',	'Manufacturing',	'Electricity, gas, steam and air conditioning supply',	'Water supply; sewerage, waste management and remediation activities',	'Construction',	'Wholesale and retail trade',	'Transportation and storage',	'Accommodation and food service activities',	'Publishing, broadcasting, and content production and distribution activities',	'Telecommunications, computer programming, consultancy, computing infrastructure, and other information service activities',	'Financial and insurance activities',	'Real estate activities',	'Professional, scientific and technical activities',	'Administrative and support service activities',	'Public administration and defence; compulsory social security',	'Education',	'Human health and social work activities',	'Arts, sports and recreation',	'Other service activities',	'Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use',	'Activities of extraterritorial organizations and bodies ',],
    index=0
)

top_k = st.sidebar.slider("🔢 Number of Matches", min_value=1, max_value=25, value=config["search"].get("k_top", 3))

# ─── Main Input ─────────────────────────────────────────
title_input = st.text_input("📝 Enter ESIC Title of Category:")

# ─── Session State Init ─────────────────────────────────
if "matches" not in st.session_state:
    st.session_state.matches = []
if "recommendation" not in st.session_state:
    st.session_state.recommendation = None
if "esic_vec" not in st.session_state:
    st.session_state.esic_vec = None
if "ready_for_reasoning" not in st.session_state:
    st.session_state.ready_for_reasoning = False

# ── Button: Vector Search ──────────────────────────────
if st.button("Find Matches"):
    if not title_input.strip():
        st.warning("Please enter a valid title of category.")
    else:
        with st.spinner("🔄 Generating embedding and finding matches..."):
            st.session_state.esic_vec = get_embedding(
                text=title_input,
                model=selected_model,
                normalize_mode=similarity_mode
            )
            st.session_state.matches = find_best_matches(
                st.session_state.esic_vec,
                k=top_k,
                match_mode=similarity_mode,
                model=selected_model,
                full_text=full_text_mode == "Description only with notes",
                isic_level= selected_level,
                section=selected_section
            )
        st.session_state.recommendation = None
        st.session_state.ready_for_reasoning = False


# ── Display Match Results First ────────────────────────
if st.session_state.matches:
    st.success(f"Top `{top_k}` ISIC matches for `{title_input}` using `{selected_model}` AI embedding model.")

    for i, match in enumerate(st.session_state.matches, start=1):
        color = (
            "🟢" if match["score"] >= 0.85 else
            "🟡" if match["score"] >= 0.75 else
            "🔴"
        )
        with st.expander(f"{i} : {color} ISIC Level {match['level']} Code: `{match['full_code']}`  Score: `{match['score']}`", expanded=True):
            st.write(f"**Description:** {match['description']}")
            st.write(f"**Section:** `{match['section_label']}`")
            st.write(f"**Division:** `{match['division_label']}`")
            st.write(f"**Group:** `{match['group_label']}`")
            st.progress(match["score"])

# ── Trigger Reasoning Separately ───────────────────────
if st.session_state.matches and selected_gen_model:
    if st.button("💡 Generate AI Reasoning"):
        st.session_state.recommendation = None
        st.session_state.ready_for_reasoning = True

    if st.session_state.ready_for_reasoning and st.session_state.recommendation is None:
        with st.spinner("🧠 AI reasoning in progress..."):
            try:
                st.session_state.recommendation = recommend_best_match(
                    esic_title=title_input,
                    matches=st.session_state.matches,
                    embedding_model=selected_model,
                    gen_model=selected_gen_model,
                    similarity_mode=similarity_mode,
                    top_k=top_k
                )
            except Exception as gen_error:
                st.session_state.recommendation = f"⚠️ Recommendation failed: {gen_error}"

# ── Show Recommendation Above Matches ───────────────────
if st.session_state.recommendation:
    st.subheader("🧠 Suggested Best Match by AI Reasoning")
    st.info(st.session_state.recommendation)