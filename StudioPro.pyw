# Studio Pro Desktop Launcher
# One window. No browser. No ports visible to user. Close window = everything stops.

import subprocess
import sys
import time
import os
import signal
import webview
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
COMFYUI_DIR = os.path.join(os.path.dirname(BASE_DIR), "ComfyUI")

PYTHON = sys.executable

processes = []

def is_comfyui_running():
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=2)
        return True
    except:
        return False

def start_comfyui():
    if is_comfyui_running():
        print("[OK] ComfyUI already running.")
        return None
    print("[..] Starting ComfyUI...")
    p = subprocess.Popen(
        [PYTHON, "main.py", "--listen", "127.0.0.1", "--port", "8188"],
        cwd=COMFYUI_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(p)
    # Wait for ComfyUI to be ready
    for i in range(60):
        time.sleep(1)
        if is_comfyui_running():
            print("[OK] ComfyUI ready.")
            return p
    print("[ERROR] ComfyUI did not start within 60 seconds.")
    return p

def is_backend_running():
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:7875/api/health", timeout=2)
        return True
    except:
        return False

def start_backend():
    if is_backend_running():
        print("[OK] Studio Pro backend already running.")
        return None
    print("[..] Starting Studio Pro backend...")
    p = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "7875", "--log-level", "warning"],
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(p)
    # Wait for backend to be ready
    for i in range(30):
        time.sleep(1)
        if is_backend_running():
            print("[OK] Studio Pro backend ready.")
            return p
    print("[ERROR] Backend did not start within 30 seconds.")
    return p

def on_closing():
    print("[..] Shutting down...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except:
            try:
                p.kill()
            except:
                pass
    print("[OK] Goodbye.")

def main():
    print("=" * 50)
    print("  Studio Pro v3.0 — Desktop Edition")
    print("=" * 50)
    print()
    
    start_comfyui()
    start_backend()
    
    print("[..] Opening window...")
    
    window = webview.create_window(
        "Studio Pro",
        "http://127.0.0.1:7875",
        width=1400,
        height=900,
        min_size=(1000, 700),
    )
    
    webview.start(on_closing)

if __name__ == "__main__":
    main()
