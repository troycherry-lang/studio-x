# Workflow Builder
# Builds ComfyUI JSON node graphs for each task.

import random
from config import DEFAULT_MODEL, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_STEPS, DEFAULT_CFG, DEFAULT_NEGATIVE, BODY_KEYWORDS, BODY_POSITIVE, BODY_NEGATIVE

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

    def _prompt(self, task, user_text, anatomy=False):
        parts = ["professional photograph, high quality, detailed, realistic lighting"]
        user_lower = user_text.lower()
        if any(kw in user_lower for kw in BODY_KEYWORDS):
            parts.append(BODY_POSITIVE)
        parts.append(user_text)
        if anatomy:
            parts.append("natural skin texture, visible pores, soft natural lighting, subsurface scattering")
        return ", ".join(parts)

    def _negative(self, user_text, anatomy=False):
        parts = [DEFAULT_NEGATIVE]
        user_lower = user_text.lower()
        if any(kw in user_lower for kw in BODY_KEYWORDS):
            parts.append(BODY_NEGATIVE)
        if anatomy:
            parts.append("smooth skin, barbie, doll, mannequin, plastic, censored")
        return ", ".join(parts)

    # ── Task: Create (text-to-image) ─────────────────────────────────
    def create(self, prompt, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, steps=DEFAULT_STEPS, cfg=DEFAULT_CFG, seed=-1, model=DEFAULT_MODEL, anatomy=False):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1: seed = random.randint(0, 2**32 - 1)

        ckpt = self._node("CheckpointLoaderSimple", {"ckpt_name": model})
        pos = self._node("CLIPTextEncode", {"text": self._prompt("create", prompt, anatomy), "clip": [ckpt, 1]})
        neg = self._node("CLIPTextEncode", {"text": self._negative(prompt, anatomy), "clip": [ckpt, 1]})
        latent = self._node("EmptyLatentImage", {"width": width, "height": height, "batch_size": 1})
        sampler = self._node("KSampler", {
            "model": [ckpt, 0], "positive": [pos, 0], "negative": [neg, 0], "latent_image": [latent, 0],
            "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0
        })
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": "studiopro"})
        return self.nodes

    # ── Task: Face (IP-Adapter portrait) ────────────────────────────
    def face(self, prompt, ref_image, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, steps=DEFAULT_STEPS, cfg=DEFAULT_CFG, seed=-1, model=DEFAULT_MODEL, anatomy=False):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1: seed = random.randint(0, 2**32 - 1)

        ckpt = self._node("CheckpointLoaderSimple", {"ckpt_name": model})
        img = self._node("LoadImage", {"image": ref_image})
        ip = self._node("IPAdapterUnifiedLoader", {"model": [ckpt, 0], "preset": "PLUS FACE (portraits)"})
        ipa = self._node("IPAdapter", {"model": [ip, 0], "ipadapter": [ip, 1], "image": [img, 0], "weight": 0.8, "start_at": 0.0, "end_at": 1.0, "weight_type": "standard"})

        pos = self._node("CLIPTextEncode", {"text": self._prompt("face", prompt, anatomy), "clip": [ckpt, 1]})
        neg = self._node("CLIPTextEncode", {"text": self._negative(prompt, anatomy), "clip": [ckpt, 1]})
        latent = self._node("EmptyLatentImage", {"width": width, "height": height, "batch_size": 1})
        sampler = self._node("KSampler", {"model": [ipa, 0], "positive": [pos, 0], "negative": [neg, 0], "latent_image": [latent, 0], "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0})
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": "studiopro_face"})
        return self.nodes

    # ── Task: Pose (OpenPose + IP-Adapter) ───────────────────────────
    def pose(self, prompt, person_img, pose_img, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, steps=DEFAULT_STEPS, cfg=DEFAULT_CFG, seed=-1, model=DEFAULT_MODEL, anatomy=False):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1: seed = random.randint(0, 2**32 - 1)

        ckpt = self._node("CheckpointLoaderSimple", {"ckpt_name": model})
        person = self._node("LoadImage", {"image": person_img})
        pose = self._node("LoadImage", {"image": pose_img})

        ip = self._node("IPAdapterUnifiedLoader", {"model": [ckpt, 0], "preset": "PLUS (high strength)"})
        ipa = self._node("IPAdapter", {"model": [ip, 0], "ipadapter": [ip, 1], "image": [person, 0], "weight": 0.8, "start_at": 0.0, "end_at": 1.0, "weight_type": "standard"})

        pre = self._node("OpenposePreprocessor", {"image": [pose, 0], "detect_hand": "enable", "detect_body": "enable", "detect_face": "disable", "resolution": min(width, height)})
        cn = self._node("ControlNetLoader", {"control_net_name": "OpenPoseXL2.safetensors"})
        cna = self._node("ControlNetApply", {"conditioning": None, "control_net": [cn, 0], "image": [pre, 0], "strength": 1.0})

        pos = self._node("CLIPTextEncode", {"text": self._prompt("pose", prompt, anatomy), "clip": [ckpt, 1]})
        neg = self._node("CLIPTextEncode", {"text": self._negative(prompt, anatomy), "clip": [ckpt, 1]})
        self.nodes[cna]["inputs"]["conditioning"] = [pos, 0]

        latent = self._node("EmptyLatentImage", {"width": width, "height": height, "batch_size": 1})
        sampler = self._node("KSampler", {"model": [ipa, 0], "positive": [cna, 0], "negative": [neg, 0], "latent_image": [latent, 0], "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0})
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": "studiopro_pose"})
        return self.nodes

    # ── Task: Inpaint (Wardrobe / Retouch) ───────────────────────────
    def inpaint(self, prompt, image, mask, task="wardrobe", width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, steps=DEFAULT_STEPS, cfg=DEFAULT_CFG, seed=-1, model=DEFAULT_MODEL, denoise=0.75, anatomy=False):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1: seed = random.randint(0, 2**32 - 1)

        ckpt = self._node("CheckpointLoaderSimple", {"ckpt_name": model})
        img = self._node("LoadImage", {"image": image})
        msk = self._node("LoadImage", {"image": mask})

        vae_in = self._node("VAEEncodeForInpaint", {"pixels": [img, 0], "mask": [msk, 1], "vae": [ckpt, 2], "grow_mask_by": 6})

        pos = self._node("CLIPTextEncode", {"text": self._prompt(task, prompt, anatomy), "clip": [ckpt, 1]})
        neg = self._node("CLIPTextEncode", {"text": self._negative(prompt, anatomy), "clip": [ckpt, 1]})

        sampler = self._node("KSampler", {"model": [ckpt, 0], "positive": [pos, 0], "negative": [neg, 0], "latent_image": [vae_in, 0], "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": denoise})
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": f"studiopro_{task}"})
        return self.nodes

    # ── Task: Refine (img2img / upscale) ────────────────────────────
    def refine(self, image, prompt="", denoise=0.5, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, steps=DEFAULT_STEPS, cfg=DEFAULT_CFG, seed=-1, model=DEFAULT_MODEL, upscale=None):
        self.nodes = {}
        self.id_counter = 0
        if seed == -1: seed = random.randint(0, 2**32 - 1)

        ckpt = self._node("CheckpointLoaderSimple", {"ckpt_name": model})
        img = self._node("LoadImage", {"image": image})

        vae_in = self._node("VAEEncode", {"pixels": [img, 0], "vae": [ckpt, 2]})
        latent = [vae_in, 0]

        if upscale and upscale > 1.0:
            up = self._node("LatentUpscale", {"samples": latent, "upscale_method": "nearest-exact", "width": int(width * upscale), "height": int(height * upscale), "crop": "disabled"})
            latent = [up, 0]

        pos = self._node("CLIPTextEncode", {"text": prompt or "high quality, detailed", "clip": [ckpt, 1]})
        neg = self._node("CLIPTextEncode", {"text": DEFAULT_NEGATIVE, "clip": [ckpt, 1]})

        sampler = self._node("KSampler", {"model": [ckpt, 0], "positive": [pos, 0], "negative": [neg, 0], "latent_image": latent, "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": denoise})
        vae = self._node("VAEDecode", {"samples": [sampler, 0], "vae": [ckpt, 2]})
        self._node("SaveImage", {"images": [vae, 0], "filename_prefix": "studiopro_refine"})
        return self.nodes

# Dispatcher
def build(task, params):
    b = Builder()
    if task == "create": return b.create(**params)
    if task == "face": return b.face(**params)
    if task == "pose": return b.pose(**params)
    if task == "wardrobe": return b.inpaint(task="wardrobe", **params)
    if task == "retouch": return b.inpaint(task="retouch", **params)
    if task == "refine": return b.refine(**params)
    raise ValueError(f"Unknown task: {task}")
