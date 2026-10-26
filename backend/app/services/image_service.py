import os
import io
import time
import uuid
import base64
import random
import logging
from typing import Optional, Dict, Any
from PIL import Image

try:
    import torch
except ImportError:
    torch = None

from backend.app.config import (
    IMAGE_MODEL_ID,
    OUTPUTS_DIR,
    DEVICE,
    DTYPE,
    MOCK_MODELS,
    DEFAULT_IMAGE_STEPS,
    DEFAULT_IMAGE_CFG
)
from backend.app.core.vram_manager import vram_manager

logger = logging.getLogger("holica.image")

DEFAULT_NEGATIVE_PROMPT = (
    "worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, "
    "missing fingers, extra digit, fewer digits, cropped, signature, watermark, username, blurry, artist name"
)

STYLE_PRESETS = {
    "photorealistic": {
        "name": "Ultra Photorealistic",
        "prefix": "masterpiece, 8k, raw photo, highly detailed, realistic skin texture, 35mm photograph, soft lighting, ",
        "suffix": ", photorealistic, lifelike, bokeh, hyperdetailed"
    },
    "anime": {
        "name": "Anime & Illustration",
        "prefix": "masterpiece, top quality, anime aesthetic, vibrant colors, detailed lineart, ",
        "suffix": ", beautiful composition, highly detailed digital painting"
    },
    "cinematic": {
        "name": "Cinematic Film",
        "prefix": "cinematic still, 35mm film, dramatic lighting, depth of field, anamorphic lens, ",
        "suffix": ", volumetric lighting, 8k resolution, award winning film look"
    },
    "raw": {
        "name": "Raw Unfiltered",
        "prefix": "",
        "suffix": ""
    }
}

class ImageService:
    def __init__(self):
        self.pipe = None
        self.img2img_pipe = None

    def is_ready(self) -> bool:
        return self.pipe is not None or MOCK_MODELS

    def load_model(self):
        """Loads Stable Diffusion pipeline with Safety Filter permanently disabled."""
        if self.pipe is not None or MOCK_MODELS:
            return

        vram_manager.prepare_for("image")

        try:
            from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

            logger.info("Loading uncensored diffusion model: %s...", IMAGE_MODEL_ID)
            
            # Disable safety checker explicitly
            pipe = StableDiffusionPipeline.from_pretrained(
                IMAGE_MODEL_ID,
                torch_dtype=DTYPE,
                safety_checker=None,
                requires_safety_checker=False,
                use_safetensors=True
            )
            
            # High-speed scheduler (DPMSolver++)
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                pipe.scheduler.config,
                use_karras_sigmas=True
            )

            if DEVICE == "cuda":
                pipe.to("cuda")
                pipe.enable_attention_slicing()
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    pass

            self.pipe = pipe
            vram_manager.register_model("image", self.pipe)
            logger.info("Uncensored image generation pipeline loaded successfully.")

        except Exception as e:
            logger.error("Error loading image model: %s", str(e), exc_info=True)
            raise e

    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        style: str = "photorealistic",
        width: int = 512,
        height: int = 512,
        steps: int = DEFAULT_IMAGE_STEPS,
        cfg_scale: float = DEFAULT_IMAGE_CFG,
        seed: Optional[int] = None,
        init_image_base64: Optional[str] = None,
        strength: float = 0.75
    ) -> Dict[str, Any]:
        """
        Generates an uncensored image (Text-to-Image or Image-to-Image).
        """
        start_time = time.time()
        
        # Apply style preset
        style_info = STYLE_PRESETS.get(style, STYLE_PRESETS["raw"])
        full_prompt = f"{style_info['prefix']}{prompt}{style_info['suffix']}".strip()
        neg_prompt = (negative_prompt if negative_prompt is not None else DEFAULT_NEGATIVE_PROMPT).strip()

        # Handle seed
        if seed is None or seed < 0:
            if torch:
                seed = torch.randint(0, 2**32 - 1, (1,)).item()
            else:
                seed = random.randint(0, 2**32 - 1)
        
        generator = None
        if torch:
            generator = torch.Generator(device=DEVICE).manual_seed(seed) if DEVICE == "cuda" else torch.Generator().manual_seed(seed)

        # File names
        img_id = str(uuid.uuid4())[:8]
        filename = f"holica_img_{img_id}.png"
        filepath = OUTPUTS_DIR / filename

        if MOCK_MODELS or self.pipe is None:
            # Generate a stylish placeholder image for mock/testing
            img = Image.new("RGB", (width, height), color=(18, 18, 28))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(120, 90, 255), width=3)
            draw.text((width // 4, height // 2 - 20), "Holica AI - Image Ready", fill=(255, 255, 255))
            draw.text((width // 4, height // 2 + 10), f"Seed: {seed} | Steps: {steps}", fill=(180, 180, 200))
            img.save(filepath, format="PNG")
        else:
            with vram_manager.inference_lock:
                vram_manager.prepare_for("image")

                if init_image_base64:
                    # Img2Img workflow
                    from diffusers import StableDiffusionImg2ImgPipeline
                    if self.img2img_pipe is None:
                        self.img2img_pipe = StableDiffusionImg2ImgPipeline(
                            vae=self.pipe.vae,
                            text_encoder=self.pipe.text_encoder,
                            tokenizer=self.pipe.tokenizer,
                            unet=self.pipe.unet,
                            scheduler=self.pipe.scheduler,
                            safety_checker=None,
                            feature_extractor=None,
                            requires_safety_checker=False
                        ).to(DEVICE)

                    raw_bytes = base64.b64decode(init_image_base64.split(",")[-1])
                    init_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB").resize((width, height))
                    
                    result = self.img2img_pipe(
                        prompt=full_prompt,
                        negative_prompt=neg_prompt,
                        image=init_img,
                        strength=strength,
                        num_inference_steps=steps,
                        guidance_scale=cfg_scale,
                        generator=generator
                    )
                else:
                    # Txt2Img workflow
                    result = self.pipe(
                        prompt=full_prompt,
                        negative_prompt=neg_prompt,
                        width=width,
                        height=height,
                        num_inference_steps=steps,
                        guidance_scale=cfg_scale,
                        generator=generator
                    )

                img = result.images[0]
                img.save(filepath, format="PNG")
                vram_manager.clean_cache()

        # Convert to base64 for fast frontend display
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        b64_str = f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"

        elapsed = round(time.time() - start_time, 2)
        logger.info("Generated image '%s' in %.2fs", filename, elapsed)

        return {
            "id": img_id,
            "filename": filename,
            "url": f"/outputs/{filename}",
            "base64": b64_str,
            "prompt": full_prompt,
            "seed": seed,
            "width": width,
            "height": height,
            "steps": steps,
            "generation_time_sec": elapsed
        }

image_service = ImageService()
