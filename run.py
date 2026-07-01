# Studio Pro — Simple Runner
# Run this in a command prompt. It shows everything. Press Enter to stop.

import subprocess
import sys
import time
import os
import webbrowser
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
COMFYUI_DIR = os.path.join(os.path.dirname(BASE_DIR), "ComfyUI")
PYTHON = sys.executable

procs = []

def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except:
        return ""

def get_pid(port):
    out = run(f'netstat -ano | findstr ":{port} "')
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and "LISTENING" in line:
            return parts[-1]
    return None

def kill(port, name):
    pid = get_pid(port)
    if pid:
        print(f"  [..] Stopping old {name} (PID {pid})...")
        run(f"taskkill /F /PID {pid} /T")
        time.sleep(2)

def is_ready(port, path="/api/health"):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=2)
        return True
    except:
        return False

def start(cmd, cwd, wait_for, max_wait=60):
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    procs.append(p)
    for i in range(max_wait):
        time.sleep(1)
        if wait_for():
            return True
    return False

print("=" * 50)
print("  Studio Pro v3.0")
print("=" * 50)
print()

# 1. Kill old processes
kill(8188, "ComfyUI")
kill(7875, "backend")

# 2. Start ComfyUI
if not is_ready(8188, "/system_stats"):
    print("  [..] Starting ComfyUI...")
    if start([PYTHON, "main.py", "--listen", "127.0.0.1", "--port", "8188"], COMFYUI_DIR, lambda: is_ready(8188, "/system_stats"), 60):
        print("  [OK] ComfyUI running.")
    else:
        print("  [ERROR] ComfyUI failed to start.")
        sys.exit(1)
else:
    print("  [OK] ComfyUI already running.")

# 3. Start backend
print("  [..] Starting Studio Pro backend...")
if start([PYTHON, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "7875"], BACKEND_DIR, lambda: is_ready(7875), 30):
    print("  [OK] Backend running.")
else:
    print("  [ERROR] Backend failed to start.")
    sys.exit(1)

# 4. Open browser
print("  [..] Opening browser...")
webbrowser.open("http://127.0.0.1:7875")
print()
print("  Studio Pro is ready.")
print("  URL: http://127.0.0.1:7875")
print()

# 5. Wait for user
input("  Press Enter to stop Studio Pro...")
print()

# 6. Shutdown
print("  [..] Stopping...")
for p in procs:
    try:
        p.terminate()
        p.wait(timeout=5)
    except:
        try:
            p.kill()
        except:
            pass
print("  [OK] Goodbye.")
