# File: vector_mapper.py

import os
import yaml
import numpy as np
from dotenv import load_dotenv
from pymongo import MongoClient
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean

from logger import progress

# ─── Setup ────────────────────────────────────────────────────────
load_dotenv()

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

mongo_uri = os.getenv("MONGO_URI", config.get("mongo_uri"))
client = MongoClient(mongo_uri)
db = client["industry_mapping"]

esic_col = db[config["collections"]["esic"]]
isic_col = db[config["collections"]["isic"]]


K_TOP = int(os.getenv("MATCH_K_TOP", config["search"].get("k_top", 3)))
SIM_MODE = os.getenv("MATCH_MODE", config["embedding"].get("normalization_mode", "cosine"))

# ─── Scoring Algorithm ────────────────────────────────────────────
def compute_score(vec1, vec2, mode=SIM_MODE):
    if not vec1 or not vec2:
        return 0.0
    try:
        if mode == "cosine":
            return float(cosine_similarity([vec1], [vec2])[0][0])
        elif mode == "dotProduct":
            return float(np.dot(vec1, vec2))
        elif mode == "distance":
            dist = euclidean(vec1, vec2)
            return 1.0 / (1.0 + dist)
        else:
            print(f"⚠️ Unknown match mode: {mode}")
            return 0.0
    except Exception as e:
        print(f"❌ Score computation failed: {e}")
        return 0.0

# ─── Matching Logic ───────────────────────────────────────────────
def find_best_matches(esic_vec, k=K_TOP, match_mode=SIM_MODE, model=None, full_text=False, isic_level=None, section=None):
    isic_key = {
        "cosine": f"embedding_cosine_{model}{'_full' if full_text else ''}",
        "dotProduct": f"embedding_dot_{model}{'_full' if full_text else ''}",
        "distance": f"embedding_raw_{model}{'_full' if full_text else ''}",
    }.get(match_mode, f"embedding_cosine_{model}{'_full' if full_text else ''}")


     # ── Add Level Filter Here ──
    query_filter = {"level": isic_level or 4}
    if section != None:
        query_filter["section_label"] = section

    projection_fields = {
        isic_key: 1,
        "code": 1,
        "full_code": 1,
        "description": 1,
        "section_label": 1,
        "division_label": 1,
        "group_label": 1,
        "class": 1,
        "level":1
    }

    # print("f1")
    # print(isic_col.find_one())
    # print("f1 str")
    # print(isic_col.find_one({"level": {"$type": "string"}}))
    # print("f1 l5")
    # print(isic_col.find_one({"level": "5"}))



    scored = []
    for isic in isic_col.find(query_filter, projection_fields):
        vec2 = isic.get(isic_key)
        if vec2:
            score = compute_score(esic_vec, vec2, match_mode)
           
            scored.append({
                            "code": isic.get("code"),
                            "full_code": isic.get("full_code"),
                            "description": isic.get("description"),
                            "section_label": isic.get("section_label"),
                            "division_label": isic.get("division_label"),
                            "group_label": isic.get("group_label"),
                            "class": isic.get("class"),
                            "level": isic.get("level"),
                            "score": round(score, 3)
                        })

    return sorted(scored, key=lambda x: x["score"], reverse=True)[:k]

# ─── Batch Mapping ────────────────────────────────────────────────
def map_esic_to_isic(store=True, verbose=False, match_mode=SIM_MODE, model=None, k_top=None, full_text=False):
    esic_key  = {
        "cosine": f"embedding_cosine_{model}{'_full' if full_text else ''}",
        "dotProduct": f"embedding_dot_{model}{'_full' if full_text else ''}",
        "distance": f"embedding_raw_{model}{'_full' if full_text else ''}",
    }.get(match_mode, f"embedding_cosine_{model}{'_full' if full_text else ''}")


    total = esic_col.count_documents({})

    result_col = db[config["collections"].get(f"results{esic_key}", f"mapping_results{esic_key}")]
    if store:
        
        result_col.delete_many({})
        print("🧹 Cleared previous mapping results.")

    for idx, esic in enumerate(esic_col.find({}, {"code": 1, "title": 1, esic_key: 1}), 1):
        esic_vec = esic.get(esic_key)
        if not esic_vec:
            continue

        matches = find_best_matches(esic_vec, match_mode=match_mode, model=model, k=k_top)
        record = {
            "esic_code": esic["code"],
            "title": esic.get("title", ""),
            "matches": matches,
            "match_mode": match_mode
        }

        

        if store:
            
            result_col.insert_one(record)

        if verbose and idx <= 5:
            print(f"\n🔹 ESIC {record['esic_code']}: {record['title']}")
            for i, m in enumerate(matches, 1):
                print(f"   Match {i}: ISIC {m['code']} — {m['description']} (score: {m['score']})")

        if total >= 100 and idx % 10 == 0:
            # print(f"   ▶ Mapped {idx}/{total}")
            progress(idx, total, prefix="▶ Mapped")
        elif total >= 25 and idx % 5 == 0:
            # print(f"   ▶ Mapped {idx}/{total}")
            progress(idx, total, prefix="▶ Mapped")

    print(f"\n✅ Completed mapping {total} ESIC entries using mode: {match_mode}")
