# Studio Pro v3.1 — Compact Context

## Status
- **Backend**: Running on port 7875 (FastAPI + direct ComfyUI REST/WebSocket client)
- **ComfyUI**: Running on port 8188 (venv, v0.25.0)
- **Frontend**: React + Vite, built to `StudioPro-v3/frontend/dist/`
- **GitHub push**: ✅ Up to date at `https://github.com/troycherry-lang/studio-x`
- **Browser UI**: Ready at `http://127.0.0.1:7875` (auto-opened by `studiopro.bat`)

## Environment
- Windows 10
- RTX 5080 (16GB VRAM), PyTorch 2.11.0 + CUDA 12.8
- Python 3.10.6 at `C:\Program Files\Python310\python.exe`
- Node/npm available for frontend builds
- Repo: `troycherry-lang/studio-x` (note: repo name; project folder is `StudioPro-v3`)

## What Works
- ComfyUI setup with Juggernaut XL, IP-Adapter, OpenPoseXL ControlNet, CLIP Vision
- Text-to-image generation with anatomy-aware prompt injection
- 6 tasks implemented: Create, Face, Pose, Wardrobe, Retouch, Refine
- Auto-detects body keywords → injects full-body anti-crop prompts
- Default square ratio (1024×1024) to avoid knee-cropping
- **Real-time progress tracking** via ComfyUI WebSocket (percentage + stage)
- **Human-readable error mapping** (OOM, timeout, connection, model missing)
- **1-click re-run last session** saved to browser localStorage
- **Upload image previews** (thumbnails before generation)
- **Multiple LoRA slots** (up to 3) with per-slot strength
- **Hi-Res Fix / latent upscale** toggle (Off / 1.5x / 2.0x) on all tasks
- **Generation history / gallery** with metadata (saved to `history/`)
- **Body Type Presets**: Default, Glamour, Athletic, Voluptuous, Slender, Petite, Muscular, Natural, Mature
- **Prompt Emphasis** weight slider (0.5x – 2.0x)
- **Flux support** (disabled by default until models are downloaded)

## Active Issues
| Issue | Detail | Action Needed |
|-------|--------|---------------|
| 5 tasks untested | Face/Pose/Wardrobe/Retouch/Refine not verified | Test after user confirms Create works |
| Flux disabled | `FLUX_ENABLED = False` until flux1-dev.safetensors is placed in `ComfyUI\models\unet\` | Download Flux models to enable |

## Folder Layout (only these matter)
```
C:\Users\troyc\Documents\kimi\workspace\
├── ComfyUI\              # AI engine, venv, models, custom nodes
└── StudioPro-v3\         # THIS IS THE APP
    ├── backend\          # FastAPI, direct ComfyUI REST client
    │   ├── main.py
    │   ├── workflows.py
    │   ├── comfy_client.py
    │   └── config.py
    ├── frontend\         # React + Vite
    │   ├── src/
    │   │   └── App.tsx
    │   └── dist/         # Built output (served by backend)
    ├── logs\             # ComfyUI + backend logs
    ├── studiopro.bat     # Console launcher (auto-opens browser)
    ├── studiopro-desktop.bat  # Desktop window launcher (pywebview)
    └── studiopro-open.bat     # Open browser only
```

## Delete These (old builds)
- `StudioPro/` (old v1)
- `studio-x/` (old v2)
- `studio-x-merge/` (merge attempt)
- Any desktop shortcuts pointing to old `.bat` files

## To Test
1. Double-click `StudioPro-v3\studiopro.bat`
2. Wait for the console to show "Studio Pro is ready."
3. Browser opens automatically to `http://127.0.0.1:7875`
4. Enter prompt, pick a **Body Type Preset** (e.g., "Glamour" or "Slender"), click **Generate**
5. Verify image appears in the preview + history gallery

## Key Code Decisions
- **Port 7875** (not 7869) – avoids stuck old process
- **Direct REST + WebSocket client** to ComfyUI – real progress + error capture
- **Backend serves static assets FIRST** (`/assets` mount before SPA catch-all)
- **Anatomy keywords auto-detect**: `full body`, `head to toe`, `nude`, `breasts`, etc. → injects full-body prompts
- **Square ratio default** (1024×1024) – prevents portrait cropping above knees
- **ComfyUI runs inside its own venv** – avoids missing dependencies / silent hangs

## Next Steps (in order)
1. User tests browser UI on port 7875 — verify progress bar, re-run, LoRAs, Hi-Res Fix, history, body presets
2. Verify all 6 tasks work end-to-end
3. Download recommended models (RealVisXL V4.0, Reliberate XL v3) and LoRAs (Detail Tweaker, epiCRealism helper) into ComfyUI folders
4. Optionally enable Flux by downloading flux1-dev.safetensors, t5xxl_fp16.safetensors, ae.safetensors and setting `FLUX_ENABLED = True`
5. Fix any issues found
6. Clean up old folders (`StudioPro/`, `studio-x/`, `studio-x-merge/`)
