# Studio Pro v3.0 – Compact Context

## Status
- **Backend**: Running on port 7875 (FastAPI + direct ComfyUI REST client)
- **ComfyUI**: Running on port 8188 (venv, v0.25.0)
- **Frontend**: React + Vite, built to `StudioPro-v3/frontend/dist/`
- **Test result**: ✅ Generated 1.6MB image with user's exact prompt
- **GitHub push**: ❌ Failed – node_modules included, need `.gitignore` + re-push
- **Browser UI**: User has NOT yet tested

## Environment
- Windows 10, Git Bash
- RTX 5080 (16GB VRAM), PyTorch 2.11.0 + CUDA 12.8
- Python 3.10.6 at `C:\Program Files\Python310\python.exe`
- Node/npm v11.9.0 at `C:\Program Files\nodejs\npm.cmd`
- Repo: `troycherry-lang/studio-pro`

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

## Active Issues
| Issue | Detail | Action Needed |
|-------|--------|---------------|
| Git push failed | node_modules committed, rejected by GitHub | Add `.gitignore`, unstage node_modules, re-push |
| Port 7869 stuck | Old `studio-x` backend still occupies 7869 | Kill PID or reboot; using 7875 instead |
| Browser untested | User hasn't opened `http://127.0.0.1:7875` | Ask user to test |
| 5 tasks untested | Face/Pose/Wardrobe/Retouch/Refine not verified | Test after user confirms Create works |

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
    └── studiopro.bat     # One launcher (starts ComfyUI + backend)
```

## Delete These (old builds)
- `StudioPro/` (old v1)
- `studio-x/` (old v2)
- `studio-x-merge/` (merge attempt)
- Any desktop shortcuts pointing to old `.bat` files

## To Test
1. Double-click `StudioPro-v3\studiopro.bat`
2. Wait for "ComfyUI running" + "Studio Pro backend running" messages
3. Open browser to `http://127.0.0.1:7875`
4. Enter prompt, click **Create**
5. Verify image appears in the gallery below

## Key Code Decisions
- **Port 7875** (not 7869) – avoids stuck old process
- **Direct REST client** to ComfyUI – no adapter layers, no drift
- **Backend serves static assets FIRST** (`/assets` mount before SPA catch-all)
- **Anatomy keywords auto-detect**: `full body`, `head to toe`, `nude`, `breasts`, etc. → injects full-body prompts
- **Square ratio default** (1024×1024) – prevents portrait cropping above knees

## Next Steps (in order)
1. Add `.gitignore` to `StudioPro-v3/`, unstage `node_modules/`, push to GitHub
2. User tests browser UI on port 7875 — verify progress bar, re-run, LoRAs, Hi-Res Fix, history
3. Verify all 6 tasks work end-to-end
4. Download recommended models (RealVisXL V4.0, Reliberate XL v3) and LoRAs (Detail Tweaker, epiCRealism helper) into ComfyUI folders
5. Fix any issues found
6. Clean up old folders (`StudioPro/`, `studio-x/`, `studio-x-merge/`)
