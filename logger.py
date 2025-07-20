# logger.py
import sys
import datetime

def banner(message):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now} 🔹 {message}")

def progress(current, total, prefix="Progress"):
    msg = f"{prefix}: {current}/{total}"
    print(f"\r{msg}", end="")
    sys.stdout.flush()

def done(message):
    print(f"✅  {message} \n")
