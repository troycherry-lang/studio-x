# Studio Pro Desktop Launcher
# One window. No browser. No ports visible to user. Close window = everything stops.
# Automatically kills old processes on startup.

import subprocess
import sys
import time
import os
import webview

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
COMFYUI_DIR = os.path.join(os.path.dirname(BASE_DIR), "ComfyUI")

PYTHON = sys.executable
processes = []

def run_cmd(cmd):
    """Run a shell command and return stdout."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception:
        return ""

def get_pid_on_port(port):
    """Find the PID using a specific port on Windows."""
    output = run_cmd(f'netstat -ano | findstr ":{port} "')
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 5 and "LISTENING" in line:
            return parts[-1]
    return None

def kill_pid(pid):
    """Kill a process by PID."""
    if pid:
        run_cmd(f'taskkill /F /PID {pid} /T')
        time.sleep(1)

def is_port_ready(port):
    """Check if something is responding on a port."""
    try:
        import urllib.request
        urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2)
        return True
    except:
        return False

def is_comfyui_ready():
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=2)
        return True
    except:
        return False

def ensure_port_free(port, name):
    """Kill any process using a port, then verify it's free."""
    pid = get_pid_on_port(port)
    if pid:
        print(f"[..] Killing old {name} process (PID {pid})...")
        kill_pid(pid)
    # Double-check port is free
    for i in range(5):
        if not get_pid_on_port(port):
            return True
        time.sleep(1)
    return False

def start_comfyui():
    if is_comfyui_ready():
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
    for i in range(60):
        time.sleep(1)
        if is_comfyui_ready():
            print("[OK] ComfyUI ready.")
            return p
    print("[ERROR] ComfyUI did not start.")
    return p

def start_backend():
    ensure_port_free(7875, "backend")
    print("[..] Starting Studio Pro backend...")
    p = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "7875", "--log-level", "warning"],
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(p)
    for i in range(30):
        time.sleep(1)
        if is_port_ready(7875):
            print("[OK] Studio Pro backend ready.")
            return p
    print("[ERROR] Backend did not start.")
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
