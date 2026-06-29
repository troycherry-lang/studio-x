# ComfyUI Direct REST Client
# Simple HTTP. No WebSocket. No async complexity.

import requests
import json
import urllib.parse

class ComfyUIClient:
    def __init__(self, url="http://127.0.0.1:8188"):
        self.url = url

    def is_ready(self):
        try:
            r = requests.get(f"{self.url}/system_stats", timeout=3)
            return r.status_code == 200
        except:
            return False

    def queue(self, workflow):
        """Submit workflow to ComfyUI. Returns prompt_id."""
        r = requests.post(f"{self.url}/prompt", json={"prompt": workflow}, timeout=60)
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        return data["prompt_id"]

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
        except:
            return []

# Singleton
comfy = ComfyUIClient()
