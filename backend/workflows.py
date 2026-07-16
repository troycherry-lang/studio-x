# Workflow Builder
# Builds ComfyUI JSON node graphs for each task.
# v3.1: Prompt weighting, Flux workflow, body presets, multi-LoRA, Hi-Res Fix.

import random
from config import (
    DEFAULT_MODEL, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_STEPS, DEFAULT_CFG,
    DEFAULT_LORA_STRENGTH, DEFAULT_UPSCALE, DEFAULT_NEGATIVE,
    PORTRAIT_KEYWORDS, BODY_KEYWORDS, BODY_POSITIVE, BODY_NEGATIVE,
    BODY_PRESETS, PROMPT_WEIGHTS,
    DEFAULT_FLUX_UNET, DEFAULT_FLUX_CLIP, DEFAULT_FLUX_VAE, FLUX_DEFAULT_GUIDANCE,
)


class Builder:
    def __init__(self):
        self.nodes = {}
        self.id_counter = 0

    def _id(self):
        self.id_counter += 1
        return str(self.id_counter)

    def _node(self, class_type, inputs):
        nid = self._id()
        self.nodes[nid] = {"class_type": class_type, "inputs": inputs}
        return nid

    # ── Prompt Building with Weighting ─────────────────────────────────

    def _weight(self, text, weight):
        """Wrap text in ComfyUI CLIP weight syntax: (text:weight)."""
        if not text or weight == 1.0:
            return text
        return f"({text}:{weight})"

    def _apply_weights(self, prompt_text):
        """Auto-detect keywords and apply emphasis weights."""
        result = prompt_text
        for keyword, weight in PROMPT_WEIGHTS.items():
            if keyword in result.lower() and f"({keyword}:" not in result.lower():
                result = result.replace(keyword, self._weight(keyword.replace("_", " "), weight))
        return result

    def _prompt(self, task, user_text, anatomy=False, body_preset="default", weight_strength=1.0):
        """Build positive prompt with body preset + weighting + anatomy."""
        user_lower = user_text.lower()
        is_portrait = any(kw in user_lower for kw in PORTRAIT_KEYWORDS)

        parts = []

        # 1. Body preset (highest priority, first in prompt = highest CLIP weight)
        preset = BODY_PRESETS.get(body_preset, BODY_PRESETS["default"])
        if preset["positive"]:
            parts.append(preset["positive"])

        # 2. Full body framing (unless portrait explicitly requested)
        if not is_portrait:
            parts.append(BODY_POSITIVE)

        # 3. Base quality
        parts.append("professional photograph, high quality, detailed, realistic lighting")

        # 4. User prompt with auto-weighting applied
        weighted_user = self._apply_weights(user_text)
        if weight_strength != 1.0:
            weighted_user = self._weight(weighted_user, weight_strength)
        parts.append(weighted_user)

        # 5. Anatomy mode
        if anatomy:
            parts.append("natural skin texture, visible pores, soft natural lighting, subsurface scattering, imperfect skin, candid")

        return ", ".join(parts)

    def _negative(self, user_text, anatomy=False, custom_negative=None, body_preset="default"):
        """Build negative prompt with preset negatives + quality safety."""
        user_lower = user_text.lower()
        is_portrait = any(kw in user_lower for kw in PORTRAIT_KEYWORDS)

        parts = [DEFAULT_NEGATIVE]

        if not is_portrait:
            parts.append(BODY_NEGATIVE)

        if anatomy:
            parts.append("smooth skin, barbie, doll, mannequin, plastic, censored, airbrushed, perfect skin")

        # Body preset negative
        preset = BODY_PRESETS.get(body_preset, BODY_PRESETS["default"])
        if preset["negative"]:
            parts.append(preset["negative"])

        if custom_negative:
            parts.append(custom_negative)

        return ", ".join(parts)

    # ── Checkpoint / Model Loading ─────────────────────────────────────

    def _checkpoint(self, model, loras=None, flux=False):
        """Load checkpoint (SDXL) or Flux UNet + CLIP + VAE, optionally stack LoRAs."""
        if flux:
            return self._flux_checkpoint(loras)

        ckpt = self._node("CheckpointLoaderSimple", {"ckpt_name": model})
        current = ckpt
        loras = loras or []
        for entry in loras:
            name = entry.get("name") if isinstance(entry, dict) else entry
            strength = entry.get("strength", DEFAULT_LORA_STRENGTH) if isinstance(entry, dict) else DEFAULT_LORA_STRENGTH
            if not name or name in ("None", "", None):
                continue
            lora_node = self._node("LoraLoader", {
                "model": [current, 0],
                "clip": [current, 1],
                "lora_name": name,
                "strength_model": strength,
                "strength_clip": strength,
            })
            current = lora_node
        return ckpt, current

    def _latent(self, width, height, upscale=DEFAULT_UPSCALE):
        """Create empty latent at target size, optionally upscaled."""
        latent = self._node("EmptyLatentImage", {"width": width, "height": height, "batch_size": 1})
        if upscale and upscale > 1.0:
            latent = self._node("LatentUpscale", {
                "samples": [latent, 0],
                "upscale_method": "nearest-exact",
                "width": int(width * upscale),
                "height": int(height * upscale),
                "crop": "disabled",
            })
        return latent

    def _flux_checkpoint(self, loras=None):
        """Load Flux: UNET + DualCLIP + VAE separately, optionally apply LoRAs."""
        unet = self._node("UNETLoader", {"unet_name": DEFAULT_FLUX_UNET, "weight_dtype": "default"})
        clip = self._node("DualCLIPLoader", {
            "clip_name1": DEFAULT_FLUX_CLIP,
            "clip_name2": "clip_l.safetensors",
            "type": "flux",
            "device": "default",
        })
        vae = self._node("VAELoader", {"vae_name": DEFAULT_FLUX_VAE})

        # Model sampling for Flux
        model = self._node("ModelSamplingFlux", {
            "model": [unet, 0],
            "max_shift": 1.15,
            "base_shift": 0.5,
        })

        current = model
        current_clip = clip
        loras = loras or []
        for entry in loras:
            name = entry.get("name") if isinstance(entry, dict) else entry
            strength = entry.get("strength", DEFAULT_LORA_STRENGTH) if isinstance(entry, dict) else DEFAULT_LORA_STRENGTH
            if not name or name in ("None", "", None):
                continue
            lora_node = self._node("LoraLoader", {
                "model": [current, 0],
                "clip": [current_clip, 0],
                "lora_name": name,
                "strength_model": strength,
                "strength_clip": strength,
            })
            current = lora_node

        return vae, current, current_clip

    # ── Task: Create (text-to-image) ─────────────────────────────────
    def create(self, prompt, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, steps=DEFAULT_STEPS,
               cfg=DEFAULT_CFG, seed=-1, model=DEFAULT_MODEL, anatomy=False,
               lora=None, lora_strength=DEFAULT_LORA_STRENGTH, loras=None,
               negative_prompt=None, body_preset="default", weight_strength=1.0,
               flux=False, flux_guidance=None, upscale=DEFAULT_UPSCALE):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        # Build LoRA list: legacy single lora + new multi-lora list
        lora_list = list(loras or [])
        if lora and lora not in ("None", "", None) and not any(entry.get("name") == lora for entry in lora_list):
            lora_list.insert(0, {"name": lora, "strength": lora_strength})

        if flux:
            return self._flux_create(prompt, width, height, steps, seed, anatomy, lora_list,
                                     negative_prompt, body_preset, weight_strength, flux_guidance)

        ckpt, mdl = self._checkpoint(model, lora_list)
        pos = self._node("CLIPTextEncode", {
            "text": self._prompt("create", prompt, anatomy, body_preset, weight_strength),
            "clip": [mdl, 1],
        })
        neg = self._node("CLIPTextEncode", {
            "text": self._negative(prompt, anatomy, negative_prompt, body_preset),
            "clip": [mdl, 1],
        })
        latent = self._latent(width, height, upscale)
        sampler = self._node("KSampler", {
            "model": [mdl, 0], "positive": [pos, 0], "negative": [neg, 0], "latent_image": [latent, 0],
            "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0
        })
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": "studiopro"})
        return self.nodes

    def _flux_create(self, prompt, width, height, steps, seed, anatomy, loras,
                     negative_prompt, body_preset, weight_strength, flux_guidance):
        """Flux text-to-image workflow."""
        vae, mdl, clip = self._flux_checkpoint(loras)

        pos = self._node("CLIPTextEncode", {
            "text": self._prompt("create", prompt, anatomy, body_preset, weight_strength),
            "clip": [clip, 0],
        })
        neg = self._node("CLIPTextEncode", {
            "text": self._negative(prompt, anatomy, negative_prompt, body_preset),
            "clip": [clip, 0],
        })
        latent = self._node("EmptySD3LatentImage", {"width": width, "height": height, "batch_size": 1})

        guidance = flux_guidance or FLUX_DEFAULT_GUIDANCE
        sampler = self._node("KSampler", {
            "model": [mdl, 0],
            "positive": [pos, 0],
            "negative": [neg, 0],
            "latent_image": [latent, 0],
            "seed": seed,
            "steps": steps,
            "cfg": 1.0,  # Flux uses guidance node instead
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
        })

        # Flux requires a CFG/guidance node after sampling
        guided = self._node("CFGNoise", {"model": [sampler, 0], "cfg": guidance})
        decoded = self._node("VAEDecode", {"samples": [guided, 0], "vae": [vae, 0]})
        self._node("SaveImage", {"images": [decoded, 0], "filename_prefix": "studiopro_flux"})
        return self.nodes

    # ── Task: Face (IP-Adapter portrait) ────────────────────────────
    def face(self, prompt, ref_image, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
             steps=DEFAULT_STEPS, cfg=DEFAULT_CFG, seed=-1, model=DEFAULT_MODEL,
             anatomy=False, lora=None, lora_strength=DEFAULT_LORA_STRENGTH, loras=None,
             negative_prompt=None, body_preset="default", weight_strength=1.0, upscale=DEFAULT_UPSCALE):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        lora_list = list(loras or [])
        if lora and lora not in ("None", "", None) and not any(entry.get("name") == lora for entry in lora_list):
            lora_list.insert(0, {"name": lora, "strength": lora_strength})

        ckpt, mdl = self._checkpoint(model, lora_list)
        img = self._node("LoadImage", {"image": ref_image})
        ip = self._node("IPAdapterUnifiedLoader", {"model": [mdl, 0], "preset": "PLUS FACE (portraits)"})
        ipa = self._node("IPAdapter", {
            "model": [ip, 0], "ipadapter": [ip, 1], "image": [img, 0],
            "weight": 0.8, "start_at": 0.0, "end_at": 1.0, "weight_type": "standard",
        })

        pos = self._node("CLIPTextEncode", {
            "text": self._prompt("face", prompt, anatomy, body_preset, weight_strength),
            "clip": [mdl, 1],
        })
        neg = self._node("CLIPTextEncode", {
            "text": self._negative(prompt, anatomy, negative_prompt, body_preset),
            "clip": [mdl, 1],
        })
        latent = self._latent(width, height, upscale)
        sampler = self._node("KSampler", {
            "model": [ipa, 0], "positive": [pos, 0], "negative": [neg, 0],
            "latent_image": [latent, 0], "seed": seed, "steps": steps,
            "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0
        })
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": "studiopro_face"})
        return self.nodes

    # ── Task: Pose (OpenPose + IP-Adapter) ───────────────────────────
    def pose(self, prompt, person_img, pose_img, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
             steps=DEFAULT_STEPS, cfg=DEFAULT_CFG, seed=-1, model=DEFAULT_MODEL,
             anatomy=False, lora=None, lora_strength=DEFAULT_LORA_STRENGTH, loras=None,
             negative_prompt=None, body_preset="default", weight_strength=1.0, upscale=DEFAULT_UPSCALE):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        lora_list = list(loras or [])
        if lora and lora not in ("None", "", None) and not any(entry.get("name") == lora for entry in lora_list):
            lora_list.insert(0, {"name": lora, "strength": lora_strength})

        ckpt, mdl = self._checkpoint(model, lora_list)
        person = self._node("LoadImage", {"image": person_img})
        pose = self._node("LoadImage", {"image": pose_img})

        ip = self._node("IPAdapterUnifiedLoader", {"model": [mdl, 0], "preset": "PLUS (high strength)"})
        ipa = self._node("IPAdapter", {
            "model": [ip, 0], "ipadapter": [ip, 1], "image": [person, 0],
            "weight": 0.8, "start_at": 0.0, "end_at": 1.0, "weight_type": "standard",
        })

        pre = self._node("OpenposePreprocessor", {
            "image": [pose, 0], "detect_hand": "enable", "detect_body": "enable",
            "detect_face": "disable", "resolution": min(width, height),
        })
        cn = self._node("ControlNetLoader", {"control_net_name": "OpenPoseXL2.safetensors"})
        cna = self._node("ControlNetApply", {
            "conditioning": None, "control_net": [cn, 0],
            "image": [pre, 0], "strength": 1.0,
        })

        pos = self._node("CLIPTextEncode", {
            "text": self._prompt("pose", prompt, anatomy, body_preset, weight_strength),
            "clip": [mdl, 1],
        })
        neg = self._node("CLIPTextEncode", {
            "text": self._negative(prompt, anatomy, negative_prompt, body_preset),
            "clip": [mdl, 1],
        })
        self.nodes[cna]["inputs"]["conditioning"] = [pos, 0]

        latent = self._latent(width, height, upscale)
        sampler = self._node("KSampler", {
            "model": [ipa, 0], "positive": [cna, 0], "negative": [neg, 0],
            "latent_image": [latent, 0], "seed": seed, "steps": steps,
            "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0
        })
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": "studiopro_pose"})
        return self.nodes

    # ── Task: Inpaint (Wardrobe / Retouch) ───────────────────────────
    def inpaint(self, prompt, image, mask, task="wardrobe", width=DEFAULT_WIDTH,
                height=DEFAULT_HEIGHT, steps=DEFAULT_STEPS, cfg=DEFAULT_CFG,
                seed=-1, model=DEFAULT_MODEL, denoise=0.75, anatomy=False,
                lora=None, lora_strength=DEFAULT_LORA_STRENGTH, loras=None,
                negative_prompt=None, body_preset="default", weight_strength=1.0):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        lora_list = list(loras or [])
        if lora and lora not in ("None", "", None) and not any(entry.get("name") == lora for entry in lora_list):
            lora_list.insert(0, {"name": lora, "strength": lora_strength})

        ckpt, mdl = self._checkpoint(model, lora_list)
        img = self._node("LoadImage", {"image": image})
        msk = self._node("LoadImage", {"image": mask})

        vae_in = self._node("VAEEncodeForInpaint", {
            "pixels": [img, 0], "mask": [msk, 1],
            "vae": [ckpt, 2], "grow_mask_by": 6,
        })

        pos = self._node("CLIPTextEncode", {
            "text": self._prompt(task, prompt, anatomy, body_preset, weight_strength),
            "clip": [mdl, 1],
        })
        neg = self._node("CLIPTextEncode", {
            "text": self._negative(prompt, anatomy, negative_prompt, body_preset),
            "clip": [mdl, 1],
        })

        sampler = self._node("KSampler", {
            "model": [mdl, 0], "positive": [pos, 0], "negative": [neg, 0],
            "latent_image": [vae_in, 0], "seed": seed, "steps": steps,
            "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal",
            "denoise": denoise,
        })
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": f"studiopro_{task}"})
        return self.nodes

    # ── Task: Refine (img2img / upscale) ────────────────────────────
    def refine(self, image, prompt="", denoise=0.5, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
               steps=DEFAULT_STEPS, cfg=DEFAULT_CFG, seed=-1, model=DEFAULT_MODEL,
               lora=None, lora_strength=DEFAULT_LORA_STRENGTH, loras=None,
               negative_prompt=None, body_preset="default", weight_strength=1.0,
               upscale=DEFAULT_UPSCALE):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        lora_list = list(loras or [])
        if lora and lora not in ("None", "", None) and not any(entry.get("name") == lora for entry in lora_list):
            lora_list.insert(0, {"name": lora, "strength": lora_strength})

        ckpt, mdl = self._checkpoint(model, lora_list)
        img = self._node("LoadImage", {"image": image})

        vae_in = self._node("VAEEncode", {"pixels": [img, 0], "vae": [ckpt, 2]})
        latent = [vae_in, 0]

        if upscale and upscale > 1.0:
            up = self._node("LatentUpscale", {
                "samples": latent, "upscale_method": "nearest-exact",
                "width": int(width * upscale), "height": int(height * upscale),
                "crop": "disabled",
            })
            latent = [up, 0]

        pos_text = self._prompt("refine", prompt, False, body_preset, weight_strength) if prompt else "high quality, detailed"
        pos = self._node("CLIPTextEncode", {"text": pos_text, "clip": [mdl, 1]})

        neg_text = DEFAULT_NEGATIVE
        if negative_prompt:
            neg_text += ", " + negative_prompt
        neg = self._node("CLIPTextEncode", {"text": neg_text, "clip": [mdl, 1]})

        sampler = self._node("KSampler", {
            "model": [mdl, 0], "positive": [pos, 0], "negative": [neg, 0],
            "latent_image": latent, "seed": seed, "steps": steps,
            "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal",
            "denoise": denoise,
        })
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": "studiopro_refine"})
        return self.nodes


# Dispatcher

def build(task, params):
    b = Builder()
    if task == "create":
        return b.create(**params)
    if task == "face":
        return b.face(**params)
    if task == "pose":
        return b.pose(**params)
    if task == "wardrobe":
        return b.inpaint(task="wardrobe", **params)
    if task == "retouch":
        return b.inpaint(task="retouch", **params)
    if task == "refine":
        return b.refine(**params)
    raise ValueError(f"Unknown task: {task}")
