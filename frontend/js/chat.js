// Holica AI - Chat Studio Logic
const ChatState = {
  messages: [],
  persona: 'uncensored',
  temperature: 0.7,
  maxTokens: 1024,
  isGenerating: false
};

function formatMarkdown(text) {
  if (!text) return '';
  let escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks ```code```
  escaped = escaped.replace(/```([a-zA-Z]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code class="language-${lang}">${code}</code></pre>`;
  });

  // Inline code `code`
  escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold **text**
  escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italic *text*
  escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Line breaks
  escaped = escaped.replace(/\n/g, '<br/>');

  return escaped;
}

function appendMessage(role, content = '') {
  const container = document.getElementById('chat-messages');
  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${role}`;
  bubble.innerHTML = formatMarkdown(content);
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
  return bubble;
}

async function sendChatMessage() {
  if (ChatState.isGenerating) return;

  const input = document.getElementById('chat-input');
  const userText = input.value.trim();
  if (!userText) return;

  // Clear input
  input.value = '';

  // Append User message
  ChatState.messages.push({ role: 'user', content: userText });
  appendMessage('user', userText);

  // Setup Assistant bubble
  ChatState.isGenerating = true;
  const sendBtn = document.getElementById('btn-chat-send');
  if (sendBtn) sendBtn.disabled = true;

  const assistantBubble = appendMessage('assistant', '');
  assistantBubble.classList.add('blinking-cursor');

  let accumulatedResponse = '';

  try {
    const res = await fetch(getApiUrl('/api/chat'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: ChatState.messages,
        persona: ChatState.persona,
        temperature: ChatState.temperature,
        max_tokens: ChatState.maxTokens
      })
    });

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}: ${res.statusText}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep last incomplete line

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6));
            if (data.token) {
              accumulatedResponse += data.token;
              assistantBubble.innerHTML = formatMarkdown(accumulatedResponse);
              const container = document.getElementById('chat-messages');
              container.scrollTop = container.scrollHeight;
            }
          } catch (e) {
            // ignore non-json chunk
          }
        }
      }
    }

    ChatState.messages.push({ role: 'assistant', content: accumulatedResponse });
  } catch (err) {
    assistantBubble.innerHTML = `<span style="color:var(--danger)">[Chat Error: ${err.message}]</span>`;
  } finally {
    assistantBubble.classList.remove('blinking-cursor');
    ChatState.isGenerating = false;
    if (sendBtn) sendBtn.disabled = false;
  }
}

function clearChat() {
  if (confirm('Clear entire conversation history?')) {
    ChatState.messages = [];
    const container = document.getElementById('chat-messages');
    container.innerHTML = `
      <div class="message-bubble assistant">
        <strong>Holica Uncensored AI</strong> is initialized and ready. All safety filters are disabled. Ask me anything, request roleplay, or generate mature creative fiction.
      </div>
    `;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Send Button & Enter Key
  const sendBtn = document.getElementById('btn-chat-send');
  const chatInput = document.getElementById('chat-input');
  
  if (sendBtn) sendBtn.addEventListener('click', sendChatMessage);
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }

  // Persona Selector
  const personaSelect = document.getElementById('chat-persona-select');
  if (personaSelect) {
    personaSelect.addEventListener('change', (e) => {
      ChatState.persona = e.target.value;
    });
  }

  // Temperature Slider
  const tempSlider = document.getElementById('chat-temp-slider');
  const tempVal = document.getElementById('chat-temp-val');
  if (tempSlider && tempVal) {
    tempSlider.addEventListener('input', (e) => {
      ChatState.temperature = parseFloat(e.target.value);
      tempVal.textContent = e.target.value;
    });
  }

  // Clear Button
  const clearBtn = document.getElementById('btn-chat-clear');
  if (clearBtn) clearBtn.addEventListener('click', clearChat);

  // Quick Prompt Chips
  document.querySelectorAll('.quick-prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      if (chatInput) {
        chatInput.value = chip.dataset.prompt;
        chatInput.focus();
      }
    });
  });
});
