import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.app.config import (
    STATIC_DIR,
    OUTPUTS_DIR,
    DEFAULT_IMAGE_STEPS,
    DEFAULT_IMAGE_CFG,
    DEFAULT_VIDEO_FRAMES,
    DEFAULT_VIDEO_FPS
)
from backend.app.core.vram_manager import vram_manager
from backend.app.services.chat_service import chat_service, PERSONAS
from backend.app.services.image_service import image_service, STYLE_PRESETS
from backend.app.services.video_service import video_service

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("holica.api")

app = FastAPI(
    title="Holica AI - Uncensored Studio API",
    description="High-performance, unrestricted AI Chat, Image and Video generation backend powered by Google Colab GPU.",
    version="1.0.0"
)

# Enable CORS for all domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount outputs directory for generated assets
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Mount frontend assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    if (STATIC_DIR / "css").exists():
        app.mount("/css", StaticFiles(directory=str(STATIC_DIR / "css")), name="css")
    if (STATIC_DIR / "js").exists():
        app.mount("/js", StaticFiles(directory=str(STATIC_DIR / "js")), name="js")


# Pydantic Request Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    persona: str = Field(default="uncensored", description="Persona identifier: uncensored, storyteller, waifu, coder")
    temperature: float = Field(default=0.7, ge=0.0, le=1.5)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, ge=64, le=4096)

class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    style: str = Field(default="photorealistic", description="photorealistic, anime, cinematic, raw")
    width: int = Field(default=512, ge=256, le=1024)
    height: int = Field(default=512, ge=256, le=1024)
    steps: int = Field(default=DEFAULT_IMAGE_STEPS, ge=10, le=75)
    cfg_scale: float = Field(default=DEFAULT_IMAGE_CFG, ge=1.0, le=20.0)
    seed: Optional[int] = None
    init_image_base64: Optional[str] = None
    strength: float = Field(default=0.75, ge=0.1, le=1.0)

class VideoRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    init_image_base64: Optional[str] = None
    num_frames: int = Field(default=DEFAULT_VIDEO_FRAMES, ge=8, le=24)
    fps: int = Field(default=DEFAULT_VIDEO_FPS, ge=4, le=16)
    steps: int = Field(default=20, ge=10, le=40)
    guidance_scale: float = Field(default=7.5, ge=1.0, le=15.0)
    seed: Optional[int] = None

class PreloadRequest(BaseModel):
    model_type: str = Field(..., description="'chat', 'image', or 'video'")


# Routes
@app.get("/")
async def root():
    """Serves the web UI index.html if present, else API overview."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "app": "Holica AI - Uncensored Studio",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
        "vram": vram_manager.get_vram_status()
    }

@app.get("/api/status")
async def get_system_status():
    """Provides real-time GPU VRAM, active mode, and model readiness status."""
    return {
        "status": "online",
        "vram": vram_manager.get_vram_status(),
        "models": {
            "chat_ready": chat_service.is_ready(),
            "image_ready": image_service.is_ready(),
            "video_ready": video_service.is_ready()
        },
        "presets": {
            "personas": PERSONAS,
            "image_styles": STYLE_PRESETS
        }
    }

@app.post("/api/vram/clean")
async def clean_vram():
    """Forces garbage collection and clears CUDA cache."""
    vram_manager.clean_cache()
    return {
        "message": "CUDA cache flushed successfully.",
        "vram": vram_manager.get_vram_status()
    }

@app.post("/api/models/preload")
async def preload_model(req: PreloadRequest, background_tasks: BackgroundTasks):
    """Triggers background preloading of a specific AI model."""
    target = req.model_type.lower()
    if target == "chat":
        background_tasks.add_task(chat_service.load_model)
    elif target == "image":
        background_tasks.add_task(image_service.load_model)
    elif target == "video":
        background_tasks.add_task(video_service.load_model)
    else:
        raise HTTPException(status_code=400, detail="Invalid model_type. Choose 'chat', 'image', or 'video'.")

    return {"message": f"Preloading '{target}' model in background...", "target": target}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Uncensored Chat Streaming Endpoint using Server-Sent Events (SSE).
    """
    try:
        if not chat_service.is_ready():
            chat_service.load_model()

        dict_messages = [{"role": m.role, "content": m.content} for m in req.messages]
        
        return StreamingResponse(
            chat_service.stream_chat(
                messages=dict_messages,
                persona=req.persona,
                temperature=req.temperature,
                top_p=req.top_p,
                max_tokens=req.max_tokens
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error("Error during chat generation: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")

@app.post("/api/image/generate")
async def generate_image_endpoint(req: ImageRequest):
    """
    Uncensored Image Generation Endpoint (Txt2Img / Img2Img).
    """
    try:
        if not image_service.is_ready():
            image_service.load_model()

        result = image_service.generate(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            style=req.style,
            width=req.width,
            height=req.height,
            steps=req.steps,
            cfg_scale=req.cfg_scale,
            seed=req.seed,
            init_image_base64=req.init_image_base64,
            strength=req.strength
        )
        return result
    except Exception as e:
        logger.error("Error during image generation: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@app.post("/api/video/generate")
async def generate_video_endpoint(req: VideoRequest):
    """
    Uncensored Short Video Generation Endpoint (Txt2Vid / Img2Vid).
    """
    try:
        if not video_service.is_ready():
            video_service.load_model()

        result = video_service.generate(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            init_image_base64=req.init_image_base64,
            num_frames=req.num_frames,
            fps=req.fps,
            steps=req.steps,
            guidance_scale=req.guidance_scale,
            seed=req.seed
        )
        return result
    except Exception as e:
        logger.error("Error during video generation: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
