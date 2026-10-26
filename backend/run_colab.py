import os
import sys
import time
import shutil
import threading
import uvicorn

try:
    import torch
except ImportError:
    torch = None

# Ensure Holica root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import HOST, PORT, ENABLE_TUNNEL
from backend.app.utils.tunnel import CloudflareTunnel

def print_banner(public_url=None):
    gpu_name = torch.cuda.get_device_name(0) if (torch and torch.cuda.is_available()) else "No GPU (CPU Mode)"
    vram_total = (
        torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        if (torch and torch.cuda.is_available())
        else 0
    )

    border = "=" * 70
    print("\n" + border)
    print("           HOLICA AI - UNCENSORED MULTI-STUDIO")
    print("      Chat (LLM) | Image (Diffusion) | Video (AnimateDiff)")
    print(border)
    print(f" [GPU System]   : {gpu_name} ({vram_total:.1f} GB VRAM)")
    print(f" [Local URL]    : http://127.0.0.1:{PORT}")
    if public_url:
        print(f" [PUBLIC WEB URL]: \033[1;32m{public_url}\033[0m")
        print("\n >>> Click or copy the PUBLIC WEB URL above to access the app! <<<")
    else:
        print(" [Cloudflare]   : Tunnel starting or running locally...")
    print(border + "\n")

def start_server():
    uvicorn.run(
        "backend.app.main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        reload=False
    )

def main():
    print("Starting Holica AI Backend...")
    
    # 1. Start Uvicorn in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server a moment to bind port

    public_url = None
    tunnel = None

    # 2. Start Cloudflare Tunnel if enabled
    if ENABLE_TUNNEL:
        tunnel = CloudflareTunnel(port=PORT)
        public_url = tunnel.start()

    print_banner(public_url)

    # 3. Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Holica AI...")
        if tunnel:
            tunnel.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
