import sys
import os
import yaml
import openpyxl
import xlsxwriter
from dotenv import load_dotenv
from pymongo import MongoClient
from embedding_utils import get_all_embeddings, get_embedding
from esic_loader import load_esic
from isic_loader import load_isic
from mapper import map_esic_to_isic
from logger import banner, progress, done

# ─── Load Config ────────────────────────────────────────
load_dotenv()
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

mongo_uri = os.getenv("MONGO_URI", config.get("mongo_uri"))
client = MongoClient(mongo_uri)
db = client["industry_mapping"]

esic_col = db[config["collections"]["esic"]]
isic_col = db[config["collections"]["isic"]]




# ─── Export to Excel ────────────────────────────────────
def export_results_to_excel(filename="mapping_results.xlsx", model=None, full_text=False, match_mode=None):
    esic_key  = {
        "cosine": f"embedding_cosine_{model}{'_full' if full_text else ''}",
        "dotProduct": f"embedding_dot_{model}{'_full' if full_text else ''}",
        "distance": f"embedding_raw_{model}{'_full' if full_text else ''}",
    }.get(match_mode, f"embedding_cosine_{model}{'_full' if full_text else ''}")

    result_col = db[config["collections"].get(f"results{esic_key}", f"mapping_results{esic_key}")]
    results = list(result_col.find())
    banner(f"📤 Exporting {len(results)} mappings to {esic_key}_{filename}")
    wb = xlsxwriter.Workbook(f"output/{esic_key}_{filename}")
    ws = wb.add_worksheet("ESIC-ISIC Mapping")

    sample_k = len(results[0]["matches"]) if results else 0

    # Build match header blocks in correct logical sequence
    full_headers = ["ESIC Code", "Title of Category"]
    for i in range(sample_k):
        full_headers += [
            f"Match {i+1} ISIC Code",
            f"Match {i+1} ISIC Description",
            f"Match {i+1} Score"
        ]

    # Write headers
    for col, header in enumerate(full_headers):
        ws.write(0, col, header)

    # Write each row based on header alignment
    for idx, record in enumerate(results, start=1):
        ws.write(idx, 0, record.get("esic_code", ""))
        ws.write(idx, 1, record.get("title", ""))

        for i, match in enumerate(record.get("matches", [])):
            col_offset = 2 + i * 3
            ws.write(idx, col_offset,     match.get("full_code", ""))
            ws.write(idx, col_offset + 1, match.get("description", ""))
            ws.write(idx, col_offset + 2, match.get("score", 0.0))

        progress(idx, len(results), prefix="▶ Excel Export")

    wb.close()
    done(f"Exported {len(results)} rows to {esic_key}_{filename}")


# ─── Test Embedding ─────────────────────────────────────
def test_embedding():
    sample = "Growing of cereals including maize and teff"
    vector = get_embedding(sample)
    done(f"Vector length: {len(vector)}")
    print(f"First 5 dimensions: {vector[:5]}")

# ─── Reset MongoDB ──────────────────────────────────────
def reset_db():
    esic_col.delete_many({})
    isic_col.delete_many({})

    models = [
                            # "nomic-embed-text", 
                            "mxbai-embed-large", 
                            # "bge-m3"
        ]
    match_modes = ["cosine", "distance", "dotProduct"]
    for model in models:
        for match_mode in match_modes:
            for full_text in [True, False]:
                esic_key  = {
                    "cosine": f"embedding_cosine_{model}{'_full' if full_text else ''}",
                    "dotProduct": f"embedding_dot_{model}{'_full' if full_text else ''}",
                    "distance": f"embedding_raw_{model}{'_full' if full_text else ''}",
                }.get(match_mode, f"embedding_cosine_{model}{'_full' if full_text else ''}")

                result_col = db[config["collections"].get(f"results{esic_key}", f"mapping_results{esic_key}")]
                
                result_col.delete_many({})
    print("🧹 Cleared esic_codes, isic, and mapping_results collections.")

# ─── CLI Dispatcher ─────────────────────────────────────
def show_help():
    print("""
🧪 Usage: python pipeline.py <command>

Commands:
  loadesic   → Load ESIC data with full embeddings
  loadisic   → Load ISIC Rev. 4 data with full embeddings
  load       → Load ISIC and ESIC
  map        → Perform ESIC-to-ISIC semantic mapping
  export     → Export results to Excel
  loadmap    → Run load + loadisic + map
  test       → Test embedding endpoint
  reset      → Clear MongoDB collections
""")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ["--help", "-h"]:
        show_help()
    else:
        cmd = args[0].lower()
        if cmd == "loadesic": load_esic()
        elif cmd == "loadisic": load_isic()
        elif cmd == "map": map_esic_to_isic(store=True, verbose=True, k_top=5, model="mxbai-embed-large")
        elif cmd == "export": export_results_to_excel(model="mxbai-embed-large", match_mode="cosine", full_text=False)
        elif cmd == "loadmap":
            load_esic()
            load_isic()
            map_esic_to_isic(store=True, verbose=True, k_top=5, model="mxbai-embed-large")
        elif cmd == "load":
            load_esic()
            load_isic()
        elif cmd == "test": test_embedding()
        elif cmd == "reset": reset_db()
        else:
            print(f"❌ Unknown command: {cmd}")
            show_help()
