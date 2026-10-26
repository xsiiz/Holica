// Holica AI - Video Studio Logic
const VideoState = {
  prompt: '',
  negativePrompt: '',
  initImageBase64: null,
  numFrames: 16,
  fps: 8,
  steps: 20,
  guidanceScale: 7.5,
  seed: -1,
  isGenerating: false,
  lastGenerated: null
};

// Global bridge function called from Image Studio
window.setupVideoFromImage = function(imageData) {
  VideoState.initImageBase64 = imageData.base64 || null;
  const promptInput = document.getElementById('video-prompt');
  if (promptInput) {
    promptInput.value = imageData.prompt || '';
  }

  const sourceBox = document.getElementById('video-source-preview');
  if (sourceBox && (imageData.base64 || imageData.url)) {
    sourceBox.style.display = 'block';
    sourceBox.innerHTML = `
      <div style="display:flex; align-items:center; gap:0.75rem; background:var(--bg-surface); padding:0.5rem; border-radius:var(--radius-md); border:1px solid var(--border-color);">
        <img src="${imageData.base64 || getApiUrl(imageData.url)}" style="width:48px; height:48px; border-radius:4px; object-fit:cover;" />
        <div style="flex:1;">
          <div style="font-size:0.8rem; font-weight:600; color:var(--accent-purple);">Source: Animated from Image</div>
          <div style="font-size:0.7rem; color:var(--text-dim); text-overflow:ellipsis; overflow:hidden; white-space:nowrap; max-width:260px;">${imageData.prompt}</div>
        </div>
        <button id="btn-remove-source-img" class="btn btn-secondary btn-sm" style="padding:0.2rem 0.5rem;">✕</button>
      </div>
    `;

    document.getElementById('btn-remove-source-img')?.addEventListener('click', () => {
      VideoState.initImageBase64 = null;
      sourceBox.style.display = 'none';
      sourceBox.innerHTML = '';
    });
  }
};

async function generateVideo() {
  if (VideoState.isGenerating) return;

  const promptInput = document.getElementById('video-prompt');
  const prompt = promptInput.value.trim();
  if (!prompt && !VideoState.initImageBase64) {
    alert('Please enter a prompt or select an image to animate.');
    promptInput.focus();
    return;
  }

  VideoState.prompt = prompt;
  const negInput = document.getElementById('video-negative-prompt');
  VideoState.negativePrompt = negInput ? negInput.value.trim() : '';

  VideoState.isGenerating = true;
  const genBtn = document.getElementById('btn-generate-video');
  const previewBox = document.getElementById('video-preview-container');
  const actionControls = document.getElementById('video-action-controls');

  if (genBtn) genBtn.disabled = true;
  previewBox.innerHTML = `
    <div style="display:flex; flex-direction:column; align-items:center; gap:1rem;">
      <div class="spinner"></div>
      <p style="color:var(--text-muted); font-size:0.9rem;">Synthesizing Motion Frames with AnimateDiff...</p>
      <span style="font-size:0.75rem; color:var(--text-dim);">${VideoState.numFrames} frames @ ${VideoState.fps} FPS</span>
    </div>
  `;
  if (actionControls) actionControls.style.display = 'none';

  try {
    const res = await fetch(getApiUrl('/api/video/generate'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: VideoState.prompt,
        negative_prompt: VideoState.negativePrompt || undefined,
        init_image_base64: VideoState.initImageBase64 || undefined,
        num_frames: VideoState.numFrames,
        fps: VideoState.fps,
        steps: VideoState.steps,
        guidance_scale: VideoState.guidanceScale,
        seed: VideoState.seed !== -1 ? VideoState.seed : undefined
      })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Server returned ${res.status}`);
    }

    const data = await res.json();
    VideoState.lastGenerated = data;

    const videoUrl = getApiUrl(data.url);
    previewBox.innerHTML = `
      <video id="active-generated-video" src="${videoUrl}" autoplay loop muted playsinline controls style="max-height:100%; max-width:100%; border-radius:var(--radius-lg); object-fit:contain;"></video>
    `;

    if (actionControls) {
      actionControls.style.display = 'flex';
      const stats = document.getElementById('video-stats-info');
      if (stats) {
        stats.textContent = `Frames: ${data.num_frames} | Duration: ${data.duration_sec}s | Render: ${data.generation_time_sec}s`;
      }
    }

  } catch (err) {
    previewBox.innerHTML = `
      <div style="padding:1rem; text-align:center; color:var(--danger)">
        <strong>Video Generation Failed:</strong><br/>
        <span style="font-size:0.85rem">${err.message}</span>
      </div>
    `;
  } finally {
    VideoState.isGenerating = false;
    if (genBtn) genBtn.disabled = false;
  }
}

function downloadCurrentVideo() {
  if (!VideoState.lastGenerated) return;
  const a = document.createElement('a');
  a.href = getApiUrl(VideoState.lastGenerated.url);
  a.download = VideoState.lastGenerated.filename || 'holica_video.mp4';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

document.addEventListener('DOMContentLoaded', () => {
  const genBtn = document.getElementById('btn-generate-video');
  if (genBtn) genBtn.addEventListener('click', generateVideo);

  const dlBtn = document.getElementById('btn-download-video');
  if (dlBtn) dlBtn.addEventListener('click', downloadCurrentVideo);

  // Frame count chips
  document.querySelectorAll('.frame-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.frame-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      VideoState.numFrames = parseInt(chip.dataset.frames);
    });
  });

  // FPS Slider
  const fpsSlider = document.getElementById('video-fps-slider');
  const fpsVal = document.getElementById('video-fps-val');
  if (fpsSlider && fpsVal) {
    fpsSlider.addEventListener('input', (e) => {
      VideoState.fps = parseInt(e.target.value);
      fpsVal.textContent = e.target.value;
    });
  }
});
