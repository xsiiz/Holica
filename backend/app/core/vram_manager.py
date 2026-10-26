import gc
import logging
import threading
from typing import Dict, Any, Optional

try:
    import torch
except ImportError:
    torch = None

logger = logging.getLogger("holica.vram")

class VRAMManager:
    """
    Manages GPU memory allocation and model caching for Google Colab environments.
    Designed specifically for NVIDIA T4 (15.3 GB VRAM) and similar GPUs.
    """
    _instance: Optional["VRAMManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.active_models: Dict[str, Any] = {}
        self.current_mode: str = "idle"
        self.inference_lock = threading.Lock()

    def get_vram_status(self) -> Dict[str, Any]:
        """Returns GPU VRAM statistics in Gigabytes."""
        if not torch or not torch.cuda.is_available():
            return {
                "gpu_available": False,
                "gpu_name": "CPU (No GPU detected)",
                "allocated_gb": 0.0,
                "reserved_gb": 0.0,
                "total_gb": 0.0,
                "free_gb": 0.0,
                "usage_percent": 0.0,
                "active_mode": self.current_mode,
                "loaded_models": list(self.active_models.keys())
            }

        device = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(device)
        total = props.total_memory / (1024 ** 3)
        allocated = torch.cuda.memory_allocated(device) / (1024 ** 3)
        reserved = torch.cuda.memory_reserved(device) / (1024 ** 3)
        free = total - reserved

        return {
            "gpu_available": True,
            "gpu_name": props.name,
            "allocated_gb": round(allocated, 2),
            "reserved_gb": round(reserved, 2),
            "total_gb": round(total, 2),
            "free_gb": round(free, 2),
            "usage_percent": round((reserved / total) * 100, 1),
            "active_mode": self.current_mode,
            "loaded_models": list(self.active_models.keys())
        }

    def clean_cache(self):
        """Forces garbage collection and clears CUDA cache."""
        gc.collect()
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            logger.info("CUDA cache cleared. Allocated: %.2f GB", 
                        torch.cuda.memory_allocated() / (1024 ** 3))

    def register_model(self, name: str, model_obj: Any):
        """Registers a loaded model object."""
        self.active_models[name] = model_obj
        logger.info("Registered model: %s", name)

    def unload_model(self, name: str):
        """Unloads a model from memory and clears CUDA cache."""
        if name in self.active_models:
            del self.active_models[name]
            self.clean_cache()
            logger.info("Unloaded model: %s", name)

    def prepare_for(self, target_service: str):
        """
        Coordinates memory before running an inference pipeline.
        - 'chat': Needs ~4.5 GB. Can coexist with 'image'.
        - 'image': Needs ~3.5 GB. Can coexist with 'chat'.
        - 'video': Needs ~7.5 GB. If VRAM is tight, unloads video or image cache.
        """
        self.current_mode = target_service

        if target_service == "video":
            # AnimateDiff needs substantial VRAM. If image pipeline is also loaded,
            # clear intermediate cache
            self.clean_cache()
            if torch and torch.cuda.is_available():
                free_gb = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_reserved(0)) / (1024 ** 3)
                if free_gb < 6.0 and "image" in self.active_models:
                    logger.warning("Low VRAM for video. Unloading image model to prevent OOM...")
                    self.unload_model("image")

        elif target_service == "image":
            # If video was active, unload it to give space to image
            if "video" in self.active_models:
                logger.info("Unloading video pipeline to free VRAM for image generation...")
                self.unload_model("video")
            self.clean_cache()

vram_manager = VRAMManager()
