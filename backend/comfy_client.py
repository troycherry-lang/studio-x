# ComfyUI Direct REST + WebSocket Client
# Tracks real-time generation progress and captures outputs.

import json
import requests
import threading
import time
import urllib.parse
import uuid
from collections import defaultdict

try:
    import websocket
except ImportError:
    websocket = None


class ComfyUIClient:
    def __init__(self, url="http://127.0.0.1:8188"):
        self.url = url
        self.ws_url = url.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
        self.client_id = str(uuid.uuid4())
        self._jobs = defaultdict(lambda: {
            "status": "queued",
            "progress": 0,
            "step": 0,
            "max_steps": 0,
            "executed_nodes": 0,
            "total_nodes": 0,
            "outputs": [],
            "error": None,
        })
        self._ws = None
        self._ws_thread = None
        self._stop_ws = threading.Event()
        self._ensure_ws()

    # ── REST helpers ───────────────────────────────────────────────────
    def is_ready(self):
        try:
            r = requests.get(f"{self.url}/system_stats", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def queue(self, workflow):
        """Submit workflow to ComfyUI. Returns prompt_id."""
        r = requests.post(f"{self.url}/prompt", json={"prompt": workflow}, timeout=60)
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        prompt_id = data["prompt_id"]
        self._jobs[prompt_id].update({
            "status": "queued",
            "total_nodes": len(workflow),
            "progress": 0,
        })
        self._ensure_ws()
        return prompt_id

    def get_history(self, prompt_id):
        """Get execution history for a prompt_id."""
        r = requests.get(f"{self.url}/history/{prompt_id}", timeout=30)
        return r.json()

    def get_image(self, filename, subfolder="", folder_type="output"):
        """Download image by filename."""
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url = f"{self.url}/view?{urllib.parse.urlencode(params)}"
        r = requests.get(url, timeout=30)
        return r.content

    def get_models(self):
        """List available checkpoint models."""
        try:
            r = requests.get(f"{self.url}/object_info/CheckpointLoaderSimple", timeout=10)
            data = r.json()
            return data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
        except Exception:
            return []

    # ── Progress API ───────────────────────────────────────────────────
    def get_progress(self, prompt_id):
        """Return current progress dict for a job."""
        job = self._jobs.get(prompt_id, {
            "status": "queued", "progress": 0, "outputs": [], "error": None
        })

        # If not completed yet, check history for completion/failure
        if job["status"] not in ("completed", "error"):
            try:
                hist = self.get_history(prompt_id)
                if prompt_id in hist:
                    self._finalize_from_history(prompt_id, hist[prompt_id])
            except Exception:
                pass

        return dict(job)

    # ── WebSocket progress tracking ────────────────────────────────────
    def _ensure_ws(self):
        if websocket is None:
            return
        if self._ws_thread is not None and self._ws_thread.is_alive():
            return
        self._stop_ws.clear()
        self._ws_thread = threading.Thread(target=self._ws_run, daemon=True)
        self._ws_thread.start()

    def _ws_run(self):
        while not self._stop_ws.is_set():
            try:
                ws = websocket.WebSocketApp(
                    f"{self.ws_url}?clientId={self.client_id}",
                    on_open=self._on_ws_open,
                    on_message=self._on_ws_message,
                    on_error=self._on_ws_error,
                    on_close=self._on_ws_close,
                )
                self._ws = ws
                ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception:
                pass
            # Back off before reconnecting
            time.sleep(2)

    def _on_ws_open(self, ws):
        pass

    def _on_ws_error(self, ws, error):
        pass

    def _on_ws_close(self, ws, close_status_code, close_msg):
        pass

    def _on_ws_message(self, ws, message):
        try:
            msg = json.loads(message)
        except Exception:
            return

        mtype = msg.get("type")
        data = msg.get("data", {})
        prompt_id = data.get("prompt_id") if isinstance(data, dict) else None
        if not prompt_id:
            return

        job = self._jobs[prompt_id]

        if mtype == "execution_start":
            job["status"] = "running"
            job["progress"] = 5

        elif mtype == "progress":
            # Sampler step progress
            value = data.get("value", 0)
            max_val = data.get("max", 1) or 1
            job["step"] = value
            job["max_steps"] = max_val
            # Map sampler steps to 10%–90% of overall progress
            sampler_pct = (value / max_val) * 80
            job["progress"] = min(90, int(10 + sampler_pct))
            job["status"] = "running"

        elif mtype == "executing":
            node = data.get("node")
            if node is None:
                # execution_finished sentinel
                job["status"] = "completed"
                job["progress"] = 100
                self._finalize_from_history(prompt_id)
            else:
                job["status"] = "running"
                job["executed_nodes"] += 1
                if job["max_steps"] == 0:
                    # No sampler progress yet; estimate from nodes
                    total = max(job["total_nodes"], 1)
                    node_pct = min(job["executed_nodes"] / total, 0.95)
                    job["progress"] = max(job["progress"], int(node_pct * 100))

        elif mtype == "executed":
            output = data.get("output", {})
            for key, val in output.items():
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict) and "filename" in item:
                            job["outputs"].append(item["filename"])

        elif mtype in ("execution_interrupted", "execution_error"):
            job["status"] = "error"
            job["error"] = data.get("error", "Generation was interrupted or failed in ComfyUI.")

    def _finalize_from_history(self, prompt_id, hist_entry=None):
        if hist_entry is None:
            try:
                hist = self.get_history(prompt_id)
                hist_entry = hist.get(prompt_id, {})
            except Exception:
                return

        job = self._jobs[prompt_id]
        status = hist_entry.get("status", {})
        if status.get("status_str") == "error":
            job["status"] = "error"
            job["error"] = status.get("messages", "ComfyUI reported an error.")
        else:
            job["status"] = "completed"
            job["progress"] = 100

        outputs = hist_entry.get("outputs", {})
        files = []
        for node_id, node_out in outputs.items():
            for key, val in node_out.items():
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict) and "filename" in item:
                            files.append(item["filename"])
        if files:
            job["outputs"] = files


# Singleton
comfy = ComfyUIClient()
