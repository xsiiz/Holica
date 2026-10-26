import re
import sys
import time
import shutil
import logging
import subprocess
from typing import Optional

logger = logging.getLogger("holica.tunnel")

class CloudflareTunnel:
    def __init__(self, port: int = 8000):
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None

    def start(self) -> Optional[str]:
        """
        Starts a Cloudflare Quick Tunnel (trycloudflare) pointing to self.port.
        Returns the public HTTPS URL.
        """
        logger.info("Initializing Cloudflare Tunnel on port %d...", self.port)

        # 1. Try pycloudflared if available
        try:
            from pycloudflared import try_cloudflare
            self.public_url = try_cloudflare(port=self.port).tunnel
            if self.public_url:
                logger.info("Cloudflare tunnel active via pycloudflared: %s", self.public_url)
                return self.public_url
        except Exception as e:
            logger.debug("pycloudflared direct call failed: %s, trying binary fallback...", str(e))

        # 2. Check for cloudflared binary
        cmd = "cloudflared"
        if not shutil.which(cmd):
            # If on Linux (Colab), download cloudflared binary
            if sys.platform.startswith("linux"):
                try:
                    logger.info("Downloading cloudflared binary for Linux...")
                    subprocess.run(
                        ["curl", "-L", "--output", "cloudflared", "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"],
                        check=True
                    )
                    subprocess.run(["chmod", "+x", "cloudflared"], check=True)
                    cmd = "./cloudflared"
                except Exception as dl_err:
                    logger.error("Failed to download cloudflared: %s", str(dl_err))
                    return None
            else:
                logger.warning("cloudflared binary not found in PATH on %s.", sys.platform)
                return None

        # 3. Start subprocess and parse URL from stderr
        try:
            self.process = subprocess.Popen(
                [cmd, "tunnel", "--url", f"http://127.0.0.1:{self.port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Wait up to 25 seconds for the URL
            url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
            start_wait = time.time()
            
            while time.time() - start_wait < 25:
                line = self.process.stderr.readline()
                if not line and self.process.poll() is not None:
                    break
                match = url_pattern.search(line)
                if match:
                    self.public_url = match.group(0)
                    logger.info("Cloudflare Tunnel established: %s", self.public_url)
                    return self.public_url
                time.sleep(0.1)

        except Exception as e:
            logger.error("Error starting cloudflared process: %s", str(e))

        return None

    def stop(self):
        """Stops the active tunnel process."""
        if self.process:
            self.process.terminate()
            self.process = None
            logger.info("Cloudflare tunnel terminated.")
