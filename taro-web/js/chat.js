/**
 * chat.js — Chat panel, messages, tool trace cards, graph viz, typing indicator.
 */

let chatOpen = false;
let threadId = crypto.randomUUID();
let queryCount = 0;
let learnedCount = 0;

// ── Toggle chat panel ──────────────────────────────────────

function toggleChat() {
  chatOpen = !chatOpen;
  document.getElementById('chatPanel').classList.toggle('open', chatOpen);
  document.getElementById('chatBubble').classList.remove('has-unread');
  if (chatOpen) document.getElementById('chatInput').focus();
}

// ── Add message to chat ────────────────────────────────────

function addMessage(role, content, toolCalls = [], learnMsg = null, graphData = null) {
  const container = document.getElementById('chatMessages');

  const msgDiv = document.createElement('div');
  msgDiv.className = `msg ${role}`;

  // Message bubble
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = content;
  msgDiv.appendChild(bubble);

  // Tool trace cards (SurrealDB multi-model visualization)
  if (toolCalls.length > 0) {
    const iconMap = {
      vector:     '&#128269;',
      graph:      '&#128760;',
      bm25:       '&#128196;',
      relational: '&#9881;',
    };

    const traceDiv = document.createElement('div');
    traceDiv.className = 'tool-trace';
    traceDiv.innerHTML = toolCalls.map(tc => `
      <div class="tool-card" onclick="this.classList.toggle('expanded')">
        <div class="tool-card-header">
          <span class="tool-icon ${tc.type}">${iconMap[tc.type] || '&#9881;'}</span>
          ${tc.name}
          <span class="tool-label ${tc.type}">${tc.type}</span>
        </div>
        <div class="tool-card-detail">${tc.args || ''}</div>
      </div>
    `).join('');
    msgDiv.appendChild(traceDiv);
  }

  // Graph visualization (only when graph data is explicitly provided)
  if (graphData) {
    const graphEl = renderGraphViz(graphData);
    msgDiv.appendChild(graphEl);
  }

  // Self-improvement indicator
  if (learnMsg) {
    const learnDiv = document.createElement('div');
    learnDiv.className = 'self-improve';
    learnDiv.innerHTML = `&#129504; Agent learned: ${learnMsg}`;
    msgDiv.appendChild(learnDiv);
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

// ── Typing indicator ───────────────────────────────────────

function showTyping() {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'msg agent';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

// ── Send message ───────────────────────────────────────────

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  addMessage('user', text);
  showTyping();

  try {
    const resp = await sendChatMessage(text, threadId);
    removeTyping();

    if (resp.thread_id) threadId = resp.thread_id;

    // Update stats
    const tcCount = (resp.tool_calls || []).length;
    queryCount += tcCount;
    document.getElementById('queryCount').textContent = queryCount;

    if (resp.learn) {
      learnedCount++;
      document.getElementById('learnedCount').textContent = learnedCount;
    }

    // Only show graph for graph-traverse tool calls
    const hasGraphCall = (resp.tool_calls || []).some(tc =>
      tc.type === 'graph' || (tc.name && tc.name.includes('graph'))
    );
    let graphData = null;
    if (hasGraphCall && typeof MOCK_GRAPHS !== 'undefined' && MOCK_GRAPHS.length > 0) {
      graphData = MOCK_GRAPHS[queryCount % MOCK_GRAPHS.length];
    }

    addMessage('agent', formatMarkdown(resp.reply), resp.tool_calls || [], resp.learn, graphData);

    // Show unread dot if chat is closed
    if (!chatOpen) {
      document.getElementById('chatBubble').classList.add('has-unread');
    }
  } catch (err) {
    removeTyping();
    addMessage('agent', `Connection error: ${err.message}. Is the API running at ${API_BASE}?`);
  }
}

// ── Markdown-lite formatter ────────────────────────────────

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code style="background:var(--bg-surface);padding:1px 4px;border-radius:3px;font-size:11px">$1</code>')
    .replace(/\n/g, '<br>');
}

// ── Keyboard shortcut (Escape to close) ────────────────────

function initChatKeyboard() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && chatOpen) toggleChat();
  });
}
