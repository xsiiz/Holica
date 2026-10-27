// Holica AI - Global State & App Manager
const AppState = {
  apiUrl: localStorage.getItem('holica_api_url') || window.location.origin,
  isConnected: false,
  activeTab: 'chat',
  vram: null,
  activeModel: 'none'
};

// Auto-determine API URL: if on localhost/127.0.0.1 or file:// without port 7000
if (window.location.protocol === 'file:' || window.location.port === '5500' || window.location.port === '3000') {
  if (!localStorage.getItem('holica_api_url')) {
    AppState.apiUrl = 'http://127.0.0.1:7000';
  }
}

function getApiUrl(endpoint) {
  const base = AppState.apiUrl.replace(/\/+$/, '');
  return `${base}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
}

async function checkConnection() {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  const vramText = document.getElementById('vram-info');

  try {
    const res = await fetch(getApiUrl('/api/status'), { method: 'GET', signal: AbortSignal.timeout(4000) });
    if (!res.ok) throw new Error('Status responded with error');
    
    const data = await res.json();
    AppState.isConnected = true;
    dot.className = 'status-dot online';
    text.textContent = 'Connected';

    if (data.vram && data.vram.gpu_available) {
      vramText.textContent = `VRAM: ${data.vram.reserved_gb} / ${data.vram.total_gb} GB (${data.vram.usage_percent}%)`;
      vramText.style.display = 'inline-block';
    } else {
      vramText.textContent = 'CPU Mode';
      vramText.style.display = 'inline-block';
    }

    if (window.updateSystemMonitor) {
      window.updateSystemMonitor(data);
    }
  } catch (err) {
    AppState.isConnected = false;
    dot.className = 'status-dot offline';
    text.textContent = 'Disconnected';
    vramText.style.display = 'none';
  }
}

function switchTab(tabId) {
  AppState.activeTab = tabId;

  // Update nav buttons
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });

  // Update tab panes
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
  });
}

async function flushVRAM() {
  const btn = document.getElementById('btn-flush-vram');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(getApiUrl('/api/vram/clean'), { method: 'POST' });
    const data = await res.json();
    alert('VRAM cache flushed successfully!');
    checkConnection();
  } catch (err) {
    alert('Failed to flush VRAM: ' + err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Setup API URL input
  const apiInput = document.getElementById('api-url-input');
  if (apiInput) {
    apiInput.value = AppState.apiUrl;
    apiInput.addEventListener('change', (e) => {
      AppState.apiUrl = e.target.value.trim();
      localStorage.setItem('holica_api_url', AppState.apiUrl);
      checkConnection();
    });
  }

  // Setup Tab Navigation
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      switchTab(btn.dataset.tab);
    });
  });

  // Flush VRAM button
  const flushBtn = document.getElementById('btn-flush-vram');
  if (flushBtn) {
    flushBtn.addEventListener('click', flushVRAM);
  }

  // Initial connection check & recurring healthcheck
  checkConnection();
  setInterval(checkConnection, 6000);
});
