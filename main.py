# File: main.py

import os
import sys
import subprocess
from dotenv import load_dotenv
from pipeline import (
    load_esic,
    load_isic,
    map_esic_to_isic,
    export_results_to_excel,
    reset_db,
    test_embedding
)
from logger import banner

load_dotenv()

# ─── Launch Streamlit UI ──────────────────────────────
def serve_web_ui():
    banner("🚀 Launching ESIC Semantic Mapper Web UI...")
    subprocess.run([
        "streamlit", "run", "web_ui.py",
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])

# ─── CLI Dispatcher ───────────────────────────────────
def run_cli(command):
    cmd = command.lower()
    banner(f"⏳ Executing command: {cmd}")
    if cmd == "load":
        load_esic()
    elif cmd == "loadisic":
        load_isic()
    elif cmd == "map":
        map_esic_to_isic(store=True, verbose=True)
    elif cmd == "export":
        export_results_to_excel()
    elif cmd == "loadmap":
        load_esic()
        load_isic()
        map_esic_to_isic(store=True, verbose=True)
    elif cmd == "load":
        load_esic()
        load_isic()
    elif cmd == "reset":
        reset_db()
    elif cmd == "test":
        test_embedding()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

# ─── Help Message ─────────────────────────────────────
def show_help():
    print("""
🧪 Usage: python main.py [command]

Available commands:
  load       → Load ESIC data with raw + normalized embeddings
  loadisic   → Load ISIC data with full embeddings
  map        → Perform ESIC-to-ISIC semantic mapping
  export     → Save mapping results to Excel
  loadmap    → Run load + loadisic + map
  test       → Test embedding endpoint with sample input
  reset      → Clear all MongoDB collections
(no command) → Launch Web UI at http://localhost:8501
""")

# ─── Entry Point ──────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli(sys.argv[1])
    else:
        serve_web_ui()
