# Studio Pro v3.0 — FastAPI Backend
# Clean REST API. No adapters. No legacy code.

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
import json, os, shutil

from config import HOST, PORT, UPLOAD_DIR, OUTPUT_DIR, COMFYUI_DIR, DEFAULT_MODEL, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_STEPS, DEFAULT_CFG
from comfy_client import comfy
from workflows import build

BASE_DIR = Path(__file__).parent.parent
UPLOAD_PATH = Path(UPLOAD_DIR)
UPLOAD_PATH.mkdir(exist_ok=True)

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(title="Studio Pro", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Serve static assets
assets = BASE_DIR / "frontend" / "dist" / "assets"
if assets.exists():
    app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

# In-memory jobs
jobs = {}

# ── Health ───────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "comfyui": comfy.is_ready()}

# ── Upload ──────────────────────────────────────────────────────────
@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in file.filename)
    name = f"{ts}_{safe}"
    path = UPLOAD_PATH / name
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": name, "size": path.stat().st_size}

# ── Generate ───────────────────────────────────────────────────────
@app.post("/api/generate")
async def generate(
    task: str = Form(...),
    prompt: str = Form(...),
    width: int = Form(DEFAULT_WIDTH),
    height: int = Form(DEFAULT_HEIGHT),
    steps: int = Form(DEFAULT_STEPS),
    cfg: float = Form(DEFAULT_CFG),
    seed: int = Form(-1),
    model: str = Form(DEFAULT_MODEL),
    anatomy: bool = Form(False),
    reference_image: str = Form(None),
    pose_image: str = Form(None),
    mask_image: str = Form(None),
    denoise: float = Form(0.75),
):
    if not comfy.is_ready():
        raise HTTPException(503, "ComfyUI is not running. Start it first.")

    params = {"prompt": prompt, "width": width, "height": height, "steps": steps, "cfg": cfg, "seed": seed, "model": model, "anatomy": anatomy}

    if task == "face":
        if not reference_image: raise HTTPException(400, "Need reference_image")
        params["ref_image"] = str(UPLOAD_PATH / reference_image)
    elif task == "pose":
        if not reference_image or not pose_image: raise HTTPException(400, "Need reference_image and pose_image")
        params["person_img"] = str(UPLOAD_PATH / reference_image)
        params["pose_img"] = str(UPLOAD_PATH / pose_image)
    elif task in ("wardrobe", "retouch"):
        if not reference_image or not mask_image: raise HTTPException(400, "Need reference_image and mask_image")
        params["image"] = str(UPLOAD_PATH / reference_image)
        params["mask"] = str(UPLOAD_PATH / mask_image)
    elif task == "refine":
        if not reference_image: raise HTTPException(400, "Need reference_image")
        params["image"] = str(UPLOAD_PATH / reference_image)
        params["denoise"] = denoise

    try:
        workflow = build(task, params)
    except Exception as e:
        raise HTTPException(500, f"Workflow error: {e}")

    try:
        prompt_id = comfy.queue(workflow)
    except Exception as e:
        raise HTTPException(500, f"ComfyUI error: {e}")

    jobs[prompt_id] = {"task": task, "status": "queued", "outputs": []}
    return {"job_id": prompt_id, "status": "queued"}

# ── Progress ───────────────────────────────────────────────────────
@app.get("/api/progress/{job_id}")
def progress(job_id: str):
    if job_id not in jobs:
        # Check if already completed in ComfyUI history
        try:
            hist = comfy.get_history(job_id)
            if job_id in hist:
                return {"job_id": job_id, "status": "completed", "progress": 100, "outputs": []}
        except: pass
        raise HTTPException(404, "Job not found")

    job = jobs[job_id]
    if job["status"] == "completed":
        return {"job_id": job_id, "status": "completed", "progress": 100, "outputs": job["outputs"]}

    # Check ComfyUI history
    try:
        hist = comfy.get_history(job_id)
        if job_id in hist:
            job["status"] = "completed"
            job["progress"] = 100
            outs = []
            for node_id, node_out in hist[job_id].get("outputs", {}).items():
                for key, val in node_out.items():
                    if isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict) and "filename" in item:
                                outs.append(item["filename"])
            job["outputs"] = outs
            return {"job_id": job_id, "status": "completed", "progress": 100, "outputs": outs}
    except:
        pass

    return {"job_id": job_id, "status": job["status"], "progress": 0, "outputs": []}

# ── Result ──────────────────────────────────────────────────────────
@app.get("/api/result/{job_id}")
def result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    if job["status"] != "completed":
        return {"status": job["status"]}
    if not job["outputs"]:
        return {"status": "completed", "outputs": []}
    filename = job["outputs"][0]
    try:
        data = comfy.get_image(filename)
        return StreamingResponse(iter([data]), media_type="image/png")
    except Exception as e:
        raise HTTPException(500, f"Image error: {e}")

# ── SPA Catch-All ───────────────────────────────────────────────────
@app.get("/{path:path}")
def spa(path: str):
    if path.startswith("api/"):
        raise HTTPException(404, "Not found")
    index = BASE_DIR / "frontend" / "dist" / "index.html"
    if index.exists():
        return FileResponse(str(index))
    raise HTTPException(404, "Frontend not built. Run npm run build in frontend/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
