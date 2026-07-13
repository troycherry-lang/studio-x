# Studio Pro v3.1 — Configuration
# ComfyUI paths, model defaults, body type presets, Flux support, prompt weights.

import os

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
COMFYUI_DIR = os.path.join(os.path.dirname(BASE_DIR), "ComfyUI")
LORA_DIR = os.path.join(COMFYUI_DIR, "models", "loras")
UNET_DIR = os.path.join(COMFYUI_DIR, "models", "unet")
CLIP_DIR = os.path.join(COMFYUI_DIR, "models", "clip")
VAE_DIR = os.path.join(COMFYUI_DIR, "models", "vae")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Server ───────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 7875
COMFYUI_URL = "http://127.0.0.1:8188"

# ── Defaults ─────────────────────────────────────────────────────────
DEFAULT_MODEL = "juggernautXL_v8Rundiffusion.safetensors"
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024
DEFAULT_STEPS = 25
DEFAULT_CFG = 7.0
DEFAULT_LORA_STRERENGTH = 1.0

# ── Flux ─────────────────────────────────────────────────────────────
# Set FLUX_ENABLED = True when flux1-dev.safetensors is in ComfyUI\models\unet\
FLUX_ENABLED = False
DEFAULT_FLUX_UNET = "flux1-dev.safetensors"
DEFAULT_FLUX_CLIP = "t5xxl_fp16.safetensors"
DEFAULT_FLUX_VAE = "ae.safetensors"
FLUX_DEFAULT_GUIDANCE = 3.5

# ── Prompt Weights ───────────────────────────────────────────────────
# ComfyUI CLIPTextEncode supports (keyword:weight) syntax natively.
# 1.0 = normal, 1.2 = moderate emphasis, 1.3 = strong, 1.5 = very strong
PROMPT_WEIGHTS = {
    "slim": 1.2, "athletic": 1.2, "toned": 1.2, "fit": 1.2, "muscular": 1.3,
    "large_breasts": 1.3, "large_nipples": 1.4, "prominent_nipples": 1.4,
    "visible_areolas": 1.3, "tall": 1.2, "long_legs": 1.2, "narrow_waist": 1.3,
    "wide_hips": 1.2, "curvy": 1.2, "voluptuous": 1.2, "petite": 1.2,
    "pale": 1.1, "tan": 1.1, "oiled": 1.2,
}

# ── Body Type Presets ────────────────────────────────────────────────
# Each preset injects weighted positive keywords and negative suppression.
BODY_PRESETS = {
    "default": {"label": "Default (no bias)", "positive": "", "negative": "", "cfg_boost": 0},
    "athletic": {
        "label": "Athletic / Toned",
        "positive": "(athletic toned body:1.2), (defined abs:1.1), (slim waist:1.2), (toned arms:1.1), (fit physique:1.2), lean muscle, flat stomach",
        "negative": "soft body, average build, undefined waist, plain figure, untoned, weak, housewife",
        "cfg_boost": 0.5,
    },
    "voluptuous": {
        "label": "Curvy / Voluptuous",
        "positive": "(curvy voluptuous body:1.2), (wide hips:1.2), (large natural breasts:1.3), (narrow waist:1.2), (full figure:1.2), (thick thighs:1.1), hourglass proportions",
        "negative": "slim, flat chest, narrow hips, boyish figure, straight body, skinny",
        "cfg_boost": 0.5,
    },
    "slender": {
        "label": "Tall / Slender / Model",
        "positive": "(tall slender body:1.2), (long legs:1.3), (narrow frame:1.1), (elegant proportions:1.2), (lean physique:1.2), runway model body, elongated proportions",
        "negative": "short, stocky, wide hips, average height, compact, squat",
        "cfg_boost": 0.5,
    },
    "petite": {
        "label": "Petite / Small Frame",
        "positive": "(petite frame:1.2), (small delicate body:1.2), (compact proportions:1.1), (slim small build:1.2), short stature, delicate features",
        "negative": "tall, large frame, wide shoulders, big boned, heavyset, towering",
        "cfg_boost": 0.5,
    },
    "muscular": {
        "label": "Muscular / Fit",
        "positive": "(muscular fit body:1.3), (visible abs:1.2), (defined muscles:1.2), (strong physique:1.2), (toned legs:1.1), athletic build, gym body, cut definition",
        "negative": "soft, weak, no muscle, average build, untrained, flabby",
        "cfg_boost": 1.0,
    },
}

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
    "smooth skin, perfect skin, censored, blurred anatomy, "
    "average build, plain figure, housewife, suburban, mom bod"
)

DEFAULT_NEGATIVE = f"{QUALITY_NEGATIVE}, {SAFETY_NEGATIVE}, {NATURAL_NEGATIVE}"

# Auto body-keyword injection — FULL BODY is DEFAULT
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

BODY_POSITIVE = "full body shot, head to toe, entire figure in frame, standing, complete visible anatomy, legs visible, feet visible, whole body shown, not cropped"
BODY_NEGATIVE = "cropped, missing legs, missing feet, cut off, waist up, upper body only, close up, portrait framing, headshot, bust shot, torso only"
