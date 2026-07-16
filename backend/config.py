# Studio Pro v3.0 — Configuration
# Everything in one place. No external dependencies.

import os

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
HISTORY_DIR = os.path.join(BASE_DIR, "history")
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

# Hi-Res Fix / latent upscale options
SUPPORTED_UPSCALES = [1.0, 1.5, 2.0]
DEFAULT_UPSCALE = 1.0

# ── Prompt Weights ───────────────────────────────────────────────────
# Used by the weight engine to boost descriptive keywords.
PROMPT_WEIGHTS = {
    "massive": 1.5, "huge": 1.5,
    "redhead": 1.3, "ginger": 1.3, "auburn_hair": 1.3, "pale": 1.1,
    "freckles": 1.3, "natural_redhead": 1.4,
    "sagging": 1.3, "large_areolas": 1.3, "stretch_marks": 1.2,
    "mature": 1.2, "milf": 1.3, "soft_body": 1.2, "thick": 1.2,
    "glamour": 1.3, "centerfold": 1.4, "pinup": 1.3, "perfect_skin": 1.2,
    "amateur": 1.2, "housewife": 1.2, "natural": 1.1, "candid": 1.1,
    "unposed": 1.1, "everyday": 1.1, "slightly_overweight": 1.2, "chubby": 1.2,
}

# ── Body Presets ─────────────────────────────────────────────────────
# One-click body/personality presets. Applied by workflows.py based on user selection.
BODY_PRESETS = {
    "anime_model": {
        "label": "Idealized / Glamour / Anime Model",
        "positive": "(glamour model:1.3), (centerfold beauty:1.4), (perfect proportions:1.3), (pale flawless skin:1.2), (massive breasts:1.5), (voluptuous hourglass:1.3), (long slender legs:1.3), (narrow waist:1.3), (tall elegant frame:1.2), (perfect skin:1.2), (idealized beauty:1.3), (pinup model:1.3), (striking features:1.2), (redhead:1.3), (natural redhead:1.4), (pale:1.1), (freckles:1.3), professional glamour photography, studio lighting",
        "negative": "average, plain, everyday look, housewife, suburban, mom bod, soft body, chubby, slightly overweight, amateur, candid, unposed, realistic imperfections, asymmetrical, sagging, stretch marks, wrinkles, aged",
        "cfg_boost": 1.0,
    },
    "natural_amateur": {
        "label": "Natural / Amateur / Soft",
        "positive": "(natural amateur woman:1.2), (soft body:1.2), (realistic proportions:1.2), (slightly imperfect:1.1), (natural skin texture:1.2), (candid photography:1.1), (unposed:1.1), (everyday woman:1.2), (large natural breasts:1.3), (soft mature body:1.2), (natural sagging:1.2), (lived-in body:1.1), amateur lighting, home setting, authentic",
        "negative": "glamour, centerfold, perfect, idealized, barbie, doll, mannequin, flawless skin, professional lighting, studio, perfect symmetry, toned, athletic, fit, muscular, plastic surgery, botox, implants",
        "cfg_boost": 0.5,
    },
    "milf": {
        "label": "Mature / MILF / Soft Body",
        "positive": "(mature woman:1.3), (milf:1.3), (soft mature body:1.3), (large natural breasts:1.3), (natural sagging:1.3), (visible veins:1.2), (stretch marks:1.2), (lived-in body:1.2), (aged soft skin:1.2), (thick thighs:1.2), (wide hips:1.2), (natural imperfections:1.2), mature beauty, experienced",
        "negative": "young, teen, youthful, perfect skin, toned, athletic, slim, flat chest, perky, barbie, doll, idealized",
        "cfg_boost": 0.5,
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

# Always inject full body by default — place at START of prompt for maximum CLIP weight
BODY_POSITIVE = "full body shot, head to toe, entire figure in frame, standing, complete visible anatomy, legs visible, feet visible, whole body shown, not cropped"
BODY_NEGATIVE = "cropped, missing legs, missing feet, cut off, waist up, upper body only, close up, portrait framing, headshot, bust shot, torso only"

# ── Keyword Categories for Weight Engine ─────────────────────────────
# Used by workflows.py _apply_weights() to boost descriptive words
BODY_SHAPE_KEYWORDS = [
    "slim", "athletic", "toned", "fit", "muscular", "curvy", "voluptuous",
    "petite", "tall", "thick", "chubby", "soft body", "wide hips", "narrow waist",
]

BREAST_KEYWORDS = [
    "large_breasts", "massive breasts", "huge breasts", "large natural breasts",
    "large_areolas", "large nipples", "prominent_nipples", "sagging", "natural sagging",
    "visible_areolas", "visible_veins",
]

HAIR_KEYWORDS = [
    "redhead", "ginger", "auburn_hair", "natural_redhead", "pale", "freckles",
    "blonde", "brunette", "black hair",
]

STYLE_KEYWORDS = [
    "glamour", "centerfold", "pinup", "amateur", "candid", "natural",
    "unposed", "everyday", "housewife", "professional", "studio",
]

MATURITY_KEYWORDS = [
    "mature", "milf", "aged", "young", "teen",
]
