# File: gen_utils.py

import os
import yaml
import requests
import json
import time
from dotenv import load_dotenv

# ─── Load Environment & Config ───────────────────────────
load_dotenv()
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", config.get("ollama_host", "http://localhost:11434"))
VERBOSE = os.getenv("GEN_VERBOSE", "false").lower() == "true"
TIMEOUT = int(os.getenv("GEN_TIMEOUT", "300"))  # Adjustable

# ─── Endpoint Resolver ───────────────────────────────────
def resolve_endpoint(model_name: str):
    if model_name.endswith("-chat") or model_name.startswith(("gemma", "qwen")):
        return f"{OLLAMA_HOST}/api/chat", "chat"
    return f"{OLLAMA_HOST}/api/generate", "generate"

# ─── Host Check (Optional) ───────────────────────────────
def is_host_reachable(host_url):
    try:
        return requests.get(host_url, timeout=5).status_code < 400
    except:
        return False

# ─── Unified Query Interface ─────────────────────────────
def query_gen_model(prompt: str, model_name: str, retries: int = 0, delay: int = 2):
    endpoint, mode = resolve_endpoint(model_name)

    payload = {
        "model": model_name,
        "temperature": 0.3,
        "max_tokens": 1024,
        "stop": ["\n"]
    }

    if mode == "chat":
        payload["messages"] = [{"role": "user", "content": prompt.strip()}]
    else:
        payload.update({
            "prompt": prompt.strip(),
            "stream": False
        })

    for attempt in range(retries + 1):
        try:
            start = time.time()
            response = requests.post(endpoint, json=payload, timeout=TIMEOUT)
            response.raise_for_status()

            # ─── Chat-style ───────────────────────────
            if mode == "chat":
                data = response.json()
                if VERBOSE: print(f"📥 Chat response: {data}")
                return data.get("message", {}).get("content", "⚠️ No chat output.")

            # ─── Generate-style ────────────────────────
            data = response.json()
            final = data.get("response", "") or data.get("output", "")
            if VERBOSE: print(f"📥 Generate response in {time.time() - start:.2f}s: {final[:100]}...")
            return final.strip() or "⚠️ Empty generate output."

        except Exception as ex:
            print(f"⚠️ Attempt {attempt+1} failed: {ex}")
            if attempt < retries:
                time.sleep(delay)

    return "❌ Generation failed after retries. Model may be overloaded or misrouted."


# # File: gen_utils.py

# import os
# import yaml
# import requests
# import json
# import time
# from dotenv import load_dotenv

# # ─── Load Environment ────────────────────────────────────
# load_dotenv()

# with open("config.yaml", "r") as f:
#     config = yaml.safe_load(f)

# OLLAMA_HOST = os.getenv("OLLAMA_HOST", config.get("ollama_host", "http://localhost:11434"))
# VERBOSE = os.getenv("GEN_VERBOSE", "false").lower() == "true"

# # ─── Endpoint Resolver ───────────────────────────────────
# def resolve_endpoint(model_name: str):
#     if model_name.endswith("-chat") or model_name.startswith(("gemma", "qwen")):
#         return f"{OLLAMA_HOST}/api/chat", "chat"
#     return f"{OLLAMA_HOST}/api/generate", "generate"

# # ─── Reachability Check ──────────────────────────────────
# def is_host_reachable(host_url):
#     try:
#         probe = requests.get(host_url, timeout=5)
#         reachable = probe.status_code < 400
#         if VERBOSE:
#             print(f"✅ Host reachable: {host_url}")
#         return reachable
#     except Exception as e:
#         print(f"❌ Host unreachable: {e}")
#         return False

# # ─── Model Query with Fallbacks ──────────────────────────
# def query_gen_model(prompt: str, model_name: str, retries: int = 0, delay: int = 2):
#     # if not is_host_reachable(OLLAMA_HOST):
#     #     return "⚠️ Host unreachable. Check Docker/network settings."

#     endpoint, mode = resolve_endpoint(model_name)

#     payload = {
#         "model": model_name,
#         "temperature": 0.3,
#         # "max_tokens": 150,
#         "max_tokens": 250,
#         "stop": ["\n"],
       
#     }

#     if mode == "chat":
#         payload["messages"] = [{"role": "user", "content": prompt.strip()}]
#     else:
#         payload["prompt"] = prompt.strip()
#         payload["stream"] = False

#     for attempt in range(retries + 1):
#         try:
#             with requests.post(endpoint, 
#                                json=payload, 
#                                timeout=120, 
#                             #    stream=(mode == "generate")
#                                ) as response:
#                 response.raise_for_status()

#                 if mode == "chat":
#                     try:
#                         data = response.json()
#                         return data.get("message", {}).get("content", "⚠️ No response.")
#                     except Exception as decode_error:
#                         return f"⚠️ Chat parse failed: {decode_error}"

#                 output = []
#                 for line in response.iter_lines():
#                     if line:
#                         try:
#                             token = json.loads(line.decode("utf-8")).get("response", "")
#                             output.append(token)
#                         except Exception as stream_err:
#                             if VERBOSE:
#                                 print(f"⚠️ Stream decode error: {stream_err}")
#                 return "".join(output).strip() or "⚠️ Empty response."

#         except Exception as ex:
#             print(f"⚠️ Attempt {attempt+1} failed: {ex}")
#             if attempt < retries:
#                 time.sleep(delay)

#     return "❌ Generation failed. Model may be overloaded or misconfigured."
