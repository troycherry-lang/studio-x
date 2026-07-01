# Studio Pro v3.0 — Configuration
# Everything in one place. No external dependencies.

import os

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
COMFYUI_DIR = os.path.join(os.path.dirname(BASE_DIR), "ComfyUI")
LORA_DIR = os.path.join(COMFYUI_DIR, "models", "loras")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Server ───────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 7875  # Fresh port, no conflicts
COMFYUI_URL = "http://127.0.0.1:8188"

# ── Defaults ─────────────────────────────────────────────────────────
DEFAULT_MODEL = "juggernautXL_v8Rundiffusion.safetensors"
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024
DEFAULT_STEPS = 25
DEFAULT_CFG = 7.0
DEFAULT_LORA_STRENGTH = 1.0

# ── Prompts ──────────────────────────────────────────────────────────
SAFETY_NEGATIVE = (
    "child, children, kid, minor, underage, baby, toddler, loli, shota, "
    "bestiality, non-consensual, violent, gore"
)

QUALITY_NEGATIVE = (
    "deformed, bad anatomy, extra fingers, missing fingers, blurry, "
    "cartoon, anime, watermark, signature, text, worst quality, low quality"
)

NATURAL_NEGATIVE = (
    "barbie, doll, mannequin, featureless, plastic, silicone, "
    "smooth skin, perfect skin, censored, blurred anatomy"
)

DEFAULT_NEGATIVE = f"{QUALITY_NEGATIVE}, {SAFETY_NEGATIVE}, {NATURAL_NEGATIVE}"

# Auto body-keyword injection — FULL BODY is DEFAULT
# Only skip full-body if user explicitly asks for a close-up/portrait
PORTRAIT_KEYWORDS = [
    "close up", "close-up", "portrait", "headshot", "face only",
    "upper body", "bust", "torso", "waist up", "chest up",
    "shoulders up", "head and shoulders", "profile", "selfie",
]

BODY_KEYWORDS = [
    "full body", "head to toe", "feet", "legs", "nude", "naked",
    "topless", "breasts", "nipples", "vagina", "pussy", "genitals",
    "shaved", "trimmed", "pubic hair", "dildo", "masturbating",
]

# Always inject full body by default
BODY_POSITIVE = "full body, head to toe, standing, complete anatomy, entire figure visible, natural proportions, feet visible, legs visible"
BODY_NEGATIVE = "cropped, missing legs, missing feet, cut off, waist up, upper body only, close up, portrait framing, headshot"
