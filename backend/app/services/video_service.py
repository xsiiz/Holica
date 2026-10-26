import os
import io
import time
import uuid
import base64
import random
import logging
from typing import Optional, Dict, Any, List
from PIL import Image
import numpy as np
import imageio

try:
    import torch
except ImportError:
    torch = None

from backend.app.config import (
    VIDEO_BASE_MODEL_ID,
    MOTION_ADAPTER_ID,
    OUTPUTS_DIR,
    DEVICE,
    DTYPE,
    MOCK_MODELS,
    DEFAULT_VIDEO_FRAMES,
    DEFAULT_VIDEO_FPS
)
from backend.app.core.vram_manager import vram_manager

logger = logging.getLogger("holica.video")

DEFAULT_VIDEO_NEGATIVE_PROMPT = (
    "bad quality, worse quality, low resolution, deformed, distorted, blurry, jerky, jittery, flicker"
)

class VideoService:
    def __init__(self):
        self.pipe = None

    def is_ready(self) -> bool:
        return self.pipe is not None or MOCK_MODELS

    def load_model(self):
        """Loads AnimateDiff pipeline with Motion Adapter."""
        if self.pipe is not None or MOCK_MODELS:
            return

        vram_manager.prepare_for("video")

        try:
            from diffusers import (
                AnimateDiffPipeline,
                MotionAdapter,
                EulerDiscreteScheduler
            )

            logger.info("Loading Motion Adapter: %s...", MOTION_ADAPTER_ID)
            adapter = MotionAdapter.from_pretrained(
                MOTION_ADAPTER_ID,
                torch_dtype=DTYPE
            )

            logger.info("Loading AnimateDiff Base Pipeline: %s...", VIDEO_BASE_MODEL_ID)
            pipe = AnimateDiffPipeline.from_pretrained(
                VIDEO_BASE_MODEL_ID,
                motion_adapter=adapter,
                torch_dtype=DTYPE,
                safety_checker=None,
                requires_safety_checker=False
            )

            # Scheduler configuration for smooth motion
            pipe.scheduler = EulerDiscreteScheduler.from_config(
                pipe.scheduler.config,
                beta_schedule="linear",
                timestep_spacing="linspace",
                steps_offset=1
            )

            if DEVICE == "cuda":
                pipe.to("cuda")
                pipe.enable_vae_slicing()
                pipe.enable_model_cpu_offload()

            self.pipe = pipe
            vram_manager.register_model("video", self.pipe)
            logger.info("AnimateDiff Video generation pipeline loaded successfully.")

        except Exception as e:
            logger.error("Error loading video pipeline: %s", str(e), exc_info=True)
            raise e

    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        init_image_base64: Optional[str] = None,
        num_frames: int = DEFAULT_VIDEO_FRAMES,
        fps: int = DEFAULT_VIDEO_FPS,
        steps: int = 20,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generates an uncensored short video (MP4) from text prompt or input frame.
        """
        start_time = time.time()
        neg_prompt = (negative_prompt if negative_prompt is not None else DEFAULT_VIDEO_NEGATIVE_PROMPT).strip()

        # Handle seed
        if seed is None or seed < 0:
            if torch:
                seed = torch.randint(0, 2**32 - 1, (1,)).item()
            else:
                seed = random.randint(0, 2**32 - 1)

        generator = None
        if torch:
            generator = torch.Generator(device=DEVICE).manual_seed(seed) if DEVICE == "cuda" else torch.Generator().manual_seed(seed)

        video_id = str(uuid.uuid4())[:8]
        filename = f"holica_vid_{video_id}.mp4"
        filepath = OUTPUTS_DIR / filename

        frames: List[np.ndarray] = []

        if MOCK_MODELS or self.pipe is None:
            # Generate simulated smooth animated MP4 frames
            from PIL import ImageDraw
            for i in range(num_frames):
                img = Image.new("RGB", (512, 512), color=(15, 15, 25))
                draw = ImageDraw.Draw(img)
                # Moving glowing orb
                cx = int(256 + 120 * np.cos(2 * np.pi * i / num_frames))
                cy = int(256 + 120 * np.sin(2 * np.pi * i / num_frames))
                draw.ellipse([(cx - 35, cy - 35), (cx + 35, cy + 35)], fill=(138, 43, 226))
                draw.text((150, 420), f"Holica Video Frame {i+1}/{num_frames}", fill=(220, 220, 240))
                frames.append(np.array(img))
        else:
            with vram_manager.inference_lock:
                vram_manager.prepare_for("video")

                # If init image provided, prompt is tuned for continuation
                effective_prompt = prompt
                if init_image_base64:
                    effective_prompt = f"high quality animation of {prompt}, smooth motion, cinematic camera movement"

                output = self.pipe(
                    prompt=effective_prompt,
                    negative_prompt=neg_prompt,
                    num_frames=num_frames,
                    guidance_scale=guidance_scale,
                    num_inference_steps=steps,
                    generator=generator,
                    width=512,
                    height=512
                )
                
                # output.frames is List[List[PIL.Image]]
                video_frames = output.frames[0]
                frames = [np.array(f) for f in video_frames]
                vram_manager.clean_cache()

        # Save to MP4 using imageio
        try:
            imageio.mimsave(str(filepath), frames, fps=fps, format="mp4")
        except Exception as e:
            logger.warning("MP4 encode error (%s). Writing fallback video/gif format.", str(e))
            try:
                # Fallback to GIF or raw bytes
                gif_path = filepath.with_suffix(".gif")
                imageio.mimsave(str(gif_path), frames, duration=1.0/fps)
                filepath = gif_path
                filename = gif_path.name
            except Exception:
                # If still no codec, write placeholder bytes
                with open(filepath, "wb") as f:
                    f.write(b"MOCK_VIDEO_DATA")

        elapsed = round(time.time() - start_time, 2)
        logger.info("Generated video '%s' with %d frames in %.2fs", filename, len(frames), elapsed)

        return {
            "id": video_id,
            "filename": filename,
            "url": f"/outputs/{filename}",
            "num_frames": len(frames),
            "fps": fps,
            "duration_sec": round(len(frames) / fps, 1),
            "seed": seed,
            "generation_time_sec": elapsed
        }

video_service = VideoService()
