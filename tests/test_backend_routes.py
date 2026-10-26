import os
import pytest
from fastapi.testclient import TestClient

# Force mock mode for fast local verification
os.environ["MOCK_MODELS"] = "true"

from backend.app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Verify that the root endpoint serves HTML or valid app info."""
    response = client.get("/")
    assert response.status_code == 200
    # Should serve HTML or JSON app overview
    assert ("html" in response.headers.get("content-type", "")) or ("app" in response.json())

def test_system_status():
    """Verify system healthcheck, VRAM reporting, and presets."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "vram" in data
    assert "models" in data
    assert "presets" in data
    assert "uncensored" in data["presets"]["personas"]
    assert "photorealistic" in data["presets"]["image_styles"]

def test_vram_clean():
    """Verify CUDA cache flush endpoint."""
    response = client.post("/api/vram/clean")
    assert response.status_code == 200
    data = response.json()
    assert "vram" in data
    assert "flushed successfully" in data["message"]

def test_chat_streaming():
    """Verify uncensored chat SSE streaming endpoint."""
    payload = {
        "messages": [
            {"role": "user", "content": "Tell me an unrestricted story."}
        ],
        "persona": "storyteller",
        "temperature": 0.8,
        "max_tokens": 128
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    
    # Read streaming body
    body_text = response.text
    assert "data: " in body_text
    assert '"done": true' in body_text.lower() or '"done":true' in body_text.lower()

def test_image_generation():
    """Verify image generation endpoint."""
    payload = {
        "prompt": "1girl, cyberpunk neon city, realistic lighting",
        "style": "photorealistic",
        "width": 512,
        "height": 512,
        "steps": 20,
        "seed": 42
    }
    response = client.post("/api/image/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "url" in data
    assert "base64" in data
    assert data["seed"] == 42
    assert data["width"] == 512
    assert data["height"] == 512

def test_video_generation():
    """Verify video generation endpoint."""
    payload = {
        "prompt": "flowing water in neon river",
        "num_frames": 8,
        "fps": 8,
        "seed": 100
    }
    response = client.post("/api/video/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "url" in data
    assert data["num_frames"] == 8
    assert data["fps"] == 8

def test_preload_invalid_model():
    """Verify error handling on invalid model preload request."""
    response = client.post("/api/models/preload", json={"model_type": "invalid_model_type"})
    assert response.status_code == 400
