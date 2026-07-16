# Studio Pro v3.1 — FastAPI Backend
# Clean REST API. Body presets, prompt weighting, Flux support, multi-LoRA, Hi-Res Fix.

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
import json, os, shutil, re, random, base64

from config import (
    HOST, PORT, UPLOAD_DIR, OUTPUT_DIR, COMFYUI_DIR, LORA_DIR,
    DEFAULT_MODEL, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_STEPS, DEFAULT_CFG,
    DEFAULT_LORA_STRENGTH, DEFAULT_UPSCALE, SUPPORTED_UPSCALES, HISTORY_DIR,
    BODY_PRESETS, FLUX_ENABLED,
)
from comfy_client import comfy
from workflows import build

BASE_DIR = Path(__file__).parent.parent
UPLOAD_PATH = Path(UPLOAD_DIR)
UPLOAD_PATH.mkdir(exist_ok=True)

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(title="Studio Pro", version="3.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Serve static assets
assets = BASE_DIR / "frontend" / "dist" / "assets"
if assets.exists():
    app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

# In-memory jobs
jobs = {}


def humanize_error(exc):
    """Translate common failures into actionable user messages."""
    text = str(exc).lower()
    if "out of memory" in text or "cuda" in text and "memory" in text or "oom" in text:
        return "GPU ran out of memory. Try a smaller image, fewer steps, or no Hi-Res Fix."
    if "timeout" in text or "timed out" in text:
        return "Generation timed out. ComfyUI may be busy or stuck. Restart and try again."
    if "connection" in text or "refused" in text or "unable to connect" in text:
        return "Cannot reach ComfyUI. Make sure Studio Pro is running and ComfyUI started."
    if "invalid" in text and ("ratio" in text or "aspect" in text):
        return "Invalid image size. Pick a supported aspect ratio."
    if "workflow" in text and "error" in text:
        return f"Workflow error: {exc}"
    if "not found" in text and ("model" in text or "checkpoint" in text):
        return "Selected model was not found in ComfyUI. Check the Models folder."
    if "no module" in text or "import" in text:
        return f"ComfyUI is missing a required node or model: {exc}"
    return f"Generation failed: {exc}"


def _parse_loras(raw):
    """Parse a JSON list of {name, strength} LoRAs from form data."""
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _clamp_upscale(value):
    try:
        f = float(value)
    except Exception:
        return DEFAULT_UPSCALE
    return min(SUPPORTED_UPSCALES, key=lambda x: abs(x - f))


# ── Health ───────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "comfyui": comfy.is_ready(), "version": "3.1.0", "flux_enabled": FLUX_ENABLED}

# ── Config ───────────────────────────────────────────────────────────
@app.get("/api/config")
def get_config():
    """Return app configuration for the frontend."""
    return {
        "body_presets": {k: v["label"] for k, v in BODY_PRESETS.items()},
        "flux_enabled": FLUX_ENABLED,
        "default_cfg": DEFAULT_CFG,
        "default_steps": DEFAULT_STEPS,
    }

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

# ── Models ──────────────────────────────────────────────────────────
@app.get("/api/models")
def list_models():
    """List available checkpoint models from ComfyUI."""
    ckpt_dir = Path(COMFYUI_DIR) / "models" / "checkpoints"
    files = []
    if ckpt_dir.exists():
        for f in ckpt_dir.iterdir():
            if f.suffix.lower() in (".safetensors", ".ckpt", ".pt"):
                files.append(f.name)
    # Also list Flux UNET models
    unet_dir = Path(COMFYUI_DIR) / "models" / "unet"
    if unet_dir.exists():
        for f in unet_dir.iterdir():
            if f.suffix.lower() in (".safetensors", ".pt") and "flux" in f.name.lower():
                files.append(f"flux:{f.name}")
    return sorted(files)

# ── LoRAs ───────────────────────────────────────────────────────────
@app.get("/api/loras")
def list_loras():
    """List available LoRA files from ComfyUI's loras directory."""
    path = Path(LORA_DIR)
    if not path.exists():
        return []
    files = []
    for f in path.iterdir():
        if f.suffix.lower() in (".safetensors", ".ckpt", ".pt"):
            files.append(f.name)
    return sorted(files)

# ── Generate ───────────────────────────────────────────────────────
@app.post("/api/generate")
async def generate(
    task: str = Form(...),
    prompt: str = Form(...),
    negative_prompt: str = Form(None),
    width: int = Form(DEFAULT_WIDTH),
    height: int = Form(DEFAULT_HEIGHT),
    steps: int = Form(DEFAULT_STEPS),
    cfg: float = Form(DEFAULT_CFG),
    seed: int = Form(-1),
    model: str = Form(DEFAULT_MODEL),
    anatomy: bool = Form(False),
    lora: str = Form(None),
    lora_strength: float = Form(DEFAULT_LORA_STRENGTH),
    loras: str = Form("[]"),
    upscale: float = Form(DEFAULT_UPSCALE),
    reference_image: str = Form(None),
    pose_image: str = Form(None),
    mask_image: str = Form(None),
    denoise: float = Form(0.75),
    body_preset: str = Form("default"),
    weight_strength: float = Form(1.0),
    flux: bool = Form(False),
    flux_guidance: float = Form(None),
):
    if not comfy.is_ready():
        raise HTTPException(503, "ComfyUI is not running. Start it first.")

    # Auto-detect Flux model
    is_flux = flux or model.startswith("flux:")
    if is_flux:
        model = model.replace("flux:", "") if model.startswith("flux:") else model

    # Build LoRA list: legacy single lora + new multi-lora list
    lora_list = _parse_loras(loras)
    if lora and lora not in ("None", "", None) and not any(entry.get("name") == lora for entry in lora_list):
        lora_list.insert(0, {"name": lora, "strength": lora_strength})

    # Lock in a real seed so the user can reproduce the result
    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "cfg": cfg,
        "seed": seed,
        "model": model,
        "anatomy": anatomy,
        "lora": lora,
        "lora_strength": lora_strength,
        "loras": lora_list,
        "upscale": _clamp_upscale(upscale),
        "body_preset": body_preset,
        "weight_strength": weight_strength,
        "flux": is_flux,
    }

    if is_flux and flux_guidance:
        params["flux_guidance"] = flux_guidance

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
        raise HTTPException(500, humanize_error(e))

    try:
        prompt_id = comfy.queue(workflow)
    except Exception as e:
        raise HTTPException(503, humanize_error(e))

    jobs[prompt_id] = {
        "task": task, "status": "queued", "outputs": [],
        "meta": {
            "task": task, "prompt": prompt, "negative_prompt": negative_prompt,
            "width": width, "height": height, "steps": steps, "cfg": cfg,
            "seed": seed, "model": model, "anatomy": anatomy,
            "loras": lora_list, "upscale": params["upscale"],
            "body_preset": body_preset, "weight_strength": weight_strength,
            "flux": is_flux,
        }
    }
    return {"job_id": prompt_id, "status": "queued", "seed": seed}

# ── Progress ───────────────────────────────────────────────────────
@app.get("/api/progress/{job_id}")
def progress(job_id: str):
    if job_id not in jobs:
        try:
            hist = comfy.get_history(job_id)
            if job_id in hist:
                return {"job_id": job_id, "status": "completed", "progress": 100, "outputs": []}
        except: pass
        raise HTTPException(404, "Job not found")

    prog = comfy.get_progress(job_id)
    # Sync our in-memory job record
    jobs[job_id]["status"] = prog["status"]
    if prog.get("outputs"):
        jobs[job_id]["outputs"] = prog["outputs"]

    return {
        "job_id": job_id,
        "status": prog["status"],
        "progress": prog["progress"],
        "outputs": jobs[job_id].get("outputs", []),
        "error": prog.get("error"),
    }


def _save_history(job_id: str, image_data: bytes):
    """Persist generated image + metadata to the history folder."""
    job = jobs.get(job_id)
    if not job or "meta" not in job:
        return None
    meta = dict(job["meta"])
    ts = datetime.now()
    day_dir = Path(HISTORY_DIR) / ts.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    file_id = ts.strftime("%H%M%S") + f"_{job_id[:8]}"
    img_path = day_dir / f"{file_id}.png"
    with open(img_path, "wb") as f:
        f.write(image_data)
    meta.update({
        "id": file_id,
        "job_id": job_id,
        "created_at": ts.isoformat(),
        "image": str(img_path.relative_to(Path(HISTORY_DIR))),
    })
    json_path = day_dir / f"{file_id}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)
    return meta


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
        out_path = Path(OUTPUT_DIR) / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(data)
        # Persist to history gallery
        _save_history(job_id, data)
        return StreamingResponse(iter([data]), media_type="image/png")
    except Exception as e:
        raise HTTPException(500, f"Image error: {e}")


# ── History / Gallery ───────────────────────────────────────────────
@app.get("/api/history")
def list_history(limit: int = 20):
    """Return recent generations sorted newest first."""
    entries = []
    hist_path = Path(HISTORY_DIR)
    if not hist_path.exists():
        return {"history": []}
    for day_dir in sorted(hist_path.iterdir(), reverse=True):
        if not day_dir.is_dir():
            continue
        for json_file in sorted(day_dir.glob("*.json"), reverse=True):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                entries.append(meta)
            except Exception:
                continue
            if len(entries) >= limit:
                break
        if len(entries) >= limit:
            break
    return {"history": entries[:limit]}


@app.get("/api/history/{item_id}/image")
def history_image(item_id: str, date: str = ""):
    """Serve a historical image by id and optional date folder."""
    if date:
        img_path = Path(HISTORY_DIR) / date / f"{item_id}.png"
    else:
        # Search recent folders for the id
        img_path = None
        for day_dir in sorted(Path(HISTORY_DIR).iterdir(), reverse=True):
            if not day_dir.is_dir():
                continue
            candidate = day_dir / f"{item_id}.png"
            if candidate.exists():
                img_path = candidate
                break
    if not img_path or not img_path.exists():
        raise HTTPException(404, "Image not found")
    return FileResponse(str(img_path), media_type="image/png")


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
