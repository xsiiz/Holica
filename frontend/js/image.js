// Holica AI - Picture Studio Logic
const ImageState = {
  prompt: '',
  negativePrompt: '',
  style: 'photorealistic',
  width: 512,
  height: 512,
  steps: 25,
  cfgScale: 7.0,
  seed: -1,
  initImageBase64: null,
  strength: 0.75,
  isGenerating: false,
  lastGenerated: null
};

function setAspectRatio(ratio) {
  document.querySelectorAll('.aspect-chip').forEach(c => c.classList.remove('active'));
  const target = document.querySelector(`.aspect-chip[data-ratio="${ratio}"]`);
  if (target) target.classList.add('active');

  if (ratio === '1:1') {
    ImageState.width = 512;
    ImageState.height = 512;
  } else if (ratio === '9:16') {
    ImageState.width = 512;
    ImageState.height = 768;
  } else if (ratio === '16:9') {
    ImageState.width = 768;
    ImageState.height = 512;
  }
}

function setStylePreset(style) {
  ImageState.style = style;
  document.querySelectorAll('.style-chip').forEach(c => {
    c.classList.toggle('active', c.dataset.style === style);
  });
}

function randomizeSeed() {
  const seedInput = document.getElementById('image-seed-input');
  const randomVal = Math.floor(Math.random() * 2147483647);
  if (seedInput) {
    seedInput.value = randomVal;
    ImageState.seed = randomVal;
  }
}

async function generatePicture() {
  if (ImageState.isGenerating) return;

  const promptInput = document.getElementById('image-prompt');
  const prompt = promptInput.value.trim();
  if (!prompt) {
    alert('Please enter a prompt to generate an image.');
    promptInput.focus();
    return;
  }

  ImageState.prompt = prompt;
  const negInput = document.getElementById('image-negative-prompt');
  ImageState.negativePrompt = negInput ? negInput.value.trim() : '';

  const seedInput = document.getElementById('image-seed-input');
  ImageState.seed = seedInput && seedInput.value !== '' ? parseInt(seedInput.value) : -1;

  // Show loading
  ImageState.isGenerating = true;
  const genBtn = document.getElementById('btn-generate-image');
  const previewBox = document.getElementById('image-preview-container');
  const actionControls = document.getElementById('image-action-controls');

  if (genBtn) genBtn.disabled = true;
  previewBox.innerHTML = `
    <div style="display:flex; flex-direction:column; align-items:center; gap:1rem;">
      <div class="spinner"></div>
      <p style="color:var(--text-muted); font-size:0.9rem;">Generating Uncensored Diffusion Image...</p>
      <span style="font-size:0.75rem; color:var(--text-dim);">Steps: ${ImageState.steps} | Dimensions: ${ImageState.width}x${ImageState.height}</span>
    </div>
  `;
  if (actionControls) actionControls.style.display = 'none';

  try {
    const res = await fetch(getApiUrl('/api/image/generate'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: ImageState.prompt,
        negative_prompt: ImageState.negativePrompt || undefined,
        style: ImageState.style,
        width: ImageState.width,
        height: ImageState.height,
        steps: ImageState.steps,
        cfg_scale: ImageState.cfgScale,
        seed: ImageState.seed,
        init_image_base64: ImageState.initImageBase64 || undefined,
        strength: ImageState.strength
      })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Server returned ${res.status}`);
    }

    const data = await res.json();
    ImageState.lastGenerated = data;

    // Render image in preview
    const imgSrc = data.base64 || getApiUrl(data.url);
    previewBox.innerHTML = `
      <img id="active-generated-image" src="${imgSrc}" alt="${data.prompt}" style="max-height:100%; border-radius:var(--radius-lg); object-fit:contain;" />
    `;

    // Show action buttons
    if (actionControls) {
      actionControls.style.display = 'flex';
      const statsText = document.getElementById('image-stats-info');
      if (statsText) {
        statsText.textContent = `Seed: ${data.seed} | Render Time: ${data.generation_time_sec}s`;
      }
    }

    // Add to gallery
    addToGallery(data);

  } catch (err) {
    previewBox.innerHTML = `
      <div style="padding:1rem; text-align:center; color:var(--danger)">
        <strong>Generation Failed:</strong><br/>
        <span style="font-size:0.85rem">${err.message}</span>
      </div>
    `;
  } finally {
    ImageState.isGenerating = false;
    if (genBtn) genBtn.disabled = false;
  }
}

function addToGallery(data) {
  const gallery = document.getElementById('image-gallery-grid');
  if (!gallery) return;

  const thumb = document.createElement('div');
  thumb.className = 'gallery-thumbnail';
  thumb.style.cssText = 'width:80px; height:80px; border-radius:6px; overflow:hidden; cursor:pointer; border:1px solid var(--border-color); flex-shrink:0;';
  thumb.innerHTML = `<img src="${data.base64 || getApiUrl(data.url)}" style="width:100%; height:100%; object-fit:cover;" />`;
  
  thumb.addEventListener('click', () => {
    const previewBox = document.getElementById('image-preview-container');
    const imgSrc = data.base64 || getApiUrl(data.url);
    previewBox.innerHTML = `<img src="${imgSrc}" alt="${data.prompt}" style="max-height:100%; border-radius:var(--radius-lg); object-fit:contain;" />`;
    ImageState.lastGenerated = data;
    const actionControls = document.getElementById('image-action-controls');
    if (actionControls) actionControls.style.display = 'flex';
  });

  gallery.prepend(thumb);
}

function downloadCurrentImage() {
  if (!ImageState.lastGenerated) return;
  const a = document.createElement('a');
  a.href = ImageState.lastGenerated.base64 || getApiUrl(ImageState.lastGenerated.url);
  a.download = ImageState.lastGenerated.filename || 'holica_image.png';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function animateCurrentImage() {
  if (!ImageState.lastGenerated) return;
  
  // Switch to Video tab and prepopulate
  switchTab('video');
  if (window.setupVideoFromImage) {
    window.setupVideoFromImage(ImageState.lastGenerated);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Generate button
  const genBtn = document.getElementById('btn-generate-image');
  if (genBtn) genBtn.addEventListener('click', generatePicture);

  // Aspect ratio chips
  document.querySelectorAll('.aspect-chip').forEach(chip => {
    chip.addEventListener('click', () => setAspectRatio(chip.dataset.ratio));
  });

  // Style chips
  document.querySelectorAll('.style-chip').forEach(chip => {
    chip.addEventListener('click', () => setStylePreset(chip.dataset.style));
  });

  // Randomize seed
  const diceBtn = document.getElementById('btn-random-seed');
  if (diceBtn) diceBtn.addEventListener('click', randomizeSeed);

  // Action buttons
  const dlBtn = document.getElementById('btn-download-image');
  if (dlBtn) dlBtn.addEventListener('click', downloadCurrentImage);

  const animBtn = document.getElementById('btn-animate-image');
  if (animBtn) animBtn.addEventListener('click', animateCurrentImage);

  // Steps & CFG Sliders
  const stepsSlider = document.getElementById('image-steps-slider');
  const stepsVal = document.getElementById('image-steps-val');
  if (stepsSlider && stepsVal) {
    stepsSlider.addEventListener('input', (e) => {
      ImageState.steps = parseInt(e.target.value);
      stepsVal.textContent = e.target.value;
    });
  }

  const cfgSlider = document.getElementById('image-cfg-slider');
  const cfgVal = document.getElementById('image-cfg-val');
  if (cfgSlider && cfgVal) {
    cfgSlider.addEventListener('input', (e) => {
      ImageState.cfgScale = parseFloat(e.target.value);
      cfgVal.textContent = e.target.value;
    });
  }
});
