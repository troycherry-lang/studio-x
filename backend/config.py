# Studio Pro v3.1 — Configuration
# ComfyUI paths, model defaults, body type presets, Flux support, prompt weights.

import os

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
HISTORY_DIR = os.path.join(BASE_DIR, "history")
COMFYUI_DIR = os.path.join(os.path.dirname(BASE_DIR), "ComfyUI")
LORA_DIR = os.path.join(COMFYUI_DIR, "models", "loras")
UNET_DIR = os.path.join(COMFYUI_DIR, "models", "unet")
CLIP_DIR = os.path.join(COMFYUI_DIR, "models", "clip")
VAE_DIR = os.path.join(COMFYUI_DIR, "models", "vae")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

# ── Server ───────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 7875
COMFYUI_URL = "http://127.0.0.1:8188"

# ── Defaults ─────────────────────────────────────────────────────────
DEFAULT_MODEL = "juggernautXL_v8Rundiffusion.safetensors"

# Model descriptions shown in the UI dropdown.
# Add entries here as you download new checkpoints into ComfyUI\models\checkpoints\
MODEL_DESCRIPTIONS = {
    "juggernautXL_v8Rundiffusion.safetensors": "General photorealism — good default, mild anatomy",
    "juggernautXL_v9Rundiffusion.safetensors": "General photorealism — newer Juggernaut",
    "realvisxlV40.safetensors": "Realistic portraits, less censored, good skin detail",
    "realvisxlV50.safetensors": "Realistic portraits, less censored, strong prompt adherence",
    "reliberate_v30.safetensors": "NSFW-tuned, explicit anatomy, very prompt-obedient",
    "epicrealismXL_vxa.safetensors": "Cinematic realism, natural skin, decent anatomy",
    "ponyDiffusionV6XL.safetensors": "Anime/2.5D, extremely explicit-capable, tag-based",
    "illustriousXL_v10.safetensors": "Anime/2.5D, uncensored, highly detailed",
    "anythingV5.safetensors": "Anime/hentai-biased, explicit anatomy by default",
    "aom3A1B.safetensors": "Anime, strong NSFW capability",
    "counterfeitV30_v30.safetensors": "Stylized anime, detailed anatomy",
}

DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024
DEFAULT_STEPS = 25
DEFAULT_CFG = 7.0
DEFAULT_LORA_STRENGTH = 1.0

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
    "massive": 1.5, "huge": 1.5,
    "redhead": 1.3, "ginger": 1.3, "auburn_hair": 1.3,
    "freckles": 1.3, "natural_redhead": 1.4,
    "sagging": 1.3, "large_areolas": 1.3, "stretch_marks": 1.2,
    "mature": 1.2, "milf": 1.3, "soft_body": 1.2, "thick": 1.2,
    "glamour": 1.3, "centerfold": 1.4, "pinup": 1.3, "perfect_skin": 1.2,
    "amateur": 1.2, "housewife": 1.2, "natural": 1.1, "candid": 1.1,
    "unposed": 1.1, "everyday": 1.1, "slightly_overweight": 1.2, "chubby": 1.2,
}

# ── Body Type Presets ────────────────────────────────────────────────
# Each preset injects weighted positive keywords and negative suppression.
BODY_PRESETS = {
    "default": {"label": "Default (no bias)", "positive": "", "negative": "", "cfg_boost": 0},
    "glamour": {
        "label": "Idealized / Glamour / Pinup",
        "positive": "(glamour model:1.3), (centerfold beauty:1.4), (perfect proportions:1.3), (pale flawless skin:1.2), (voluptuous hourglass:1.3), (long slender legs:1.3), (narrow waist:1.3), (tall elegant frame:1.2), (perfect skin:1.2), (idealized beauty:1.3), (pinup model:1.3), professional glamour photography, studio lighting",
        "negative": "average, plain, everyday look, housewife, suburban, mom bod, soft body, chubby, slightly overweight, amateur, candid, unposed, realistic imperfections, asymmetrical, sagging, stretch marks, wrinkles, aged",
        "cfg_boost": 1.0,
    },
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
    "natural": {
        "label": "Natural / Amateur / Soft",
        "positive": "(natural amateur woman:1.2), (soft body:1.2), (realistic proportions:1.2), (slightly imperfect:1.1), (natural skin texture:1.2), (candid photography:1.1), (unposed:1.1), (everyday woman:1.2), amateur lighting, home setting, authentic",
        "negative": "glamour, centerfold, perfect, idealized, barbie, doll, mannequin, flawless skin, professional lighting, studio, perfect symmetry, plastic surgery, botox, implants",
        "cfg_boost": 0.5,
    },
    "milf": {
        "label": "Mature / MILF / Soft Body",
        "positive": "(mature woman:1.3), (milf:1.3), (soft mature body:1.3), (large natural breasts:1.3), (natural sagging:1.3), (visible veins:1.2), (stretch marks:1.2), (lived-in body:1.2), (aged soft skin:1.2), (thick thighs:1.2), (wide hips:1.2), (natural imperfections:1.2), mature beauty, experienced",
        "negative": "young, teen, youthful, perfect skin, toned, athletic, slim, flat chest, perky, barbie, doll, idealized",
        "cfg_boost": 0.5,
    },
}

# Hi-Res Fix / latent upscale options
SUPPORTED_UPSCALES = [1.0, 1.5, 2.0]
DEFAULT_UPSCALE = 1.0

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
