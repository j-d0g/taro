/**
 * chat.js — Chat panel, messages, tool trace cards, graph viz, typing indicator.
 */

let chatOpen = false;
let threadId = crypto.randomUUID();
let queryCount = 0;
let learnedCount = 0;

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Toggle chat panel ──────────────────────────────────

function toggleChat() {
  chatOpen = !chatOpen;
  document.getElementById('chatPanel').classList.toggle('open', chatOpen);
  document.getElementById('chatBubble').classList.remove('has-unread');
  if (chatOpen) document.getElementById('chatInput').focus();
}

// ── Add message to chat ────────────────────────────────

function addMessage(role, content, toolCalls = [], learnMsg = null, graphIdx = null) {
  const container = document.getElementById('chatMessages');

  const msgDiv = document.createElement('div');
  msgDiv.className = `msg ${role}`;

  // Message bubble
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = formatMarkdown(content);
  msgDiv.appendChild(bubble);

  // Tool trace cards (SurrealDB multi-model visualization)
  if (toolCalls.length > 0) {
    const iconMap = {
      vector:  '&#128269;',
      graph:   '&#128760;',
      bm25:    '&#128196;',
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
        <div class="tool-card-detail">${escapeHtml(tc.args)}</div>
      </div>
    `).join('');
    msgDiv.appendChild(traceDiv);
  }

  // Graph visualization
  if (graphIdx !== null && typeof MOCK_GRAPHS !== 'undefined' && MOCK_GRAPHS[graphIdx]) {
    const graphEl = renderGraphViz(MOCK_GRAPHS[graphIdx]);
    msgDiv.appendChild(graphEl);
  }

  // Self-improvement indicator
  if (learnMsg) {
    const learnDiv = document.createElement('div');
    learnDiv.className = 'self-improve';
    learnDiv.innerHTML = '&#129504; Agent learned: ' + escapeHtml(learnMsg);
    msgDiv.appendChild(learnDiv);
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

// ── Typing indicator ───────────────────────────────────

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

// ── Send message ───────────────────────────────────────

let graphResponseIdx = 0;

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

    // Update stats
    queryCount += (resp.tool_calls || []).length;
    document.getElementById('queryCount').textContent = queryCount;

    if (resp.learn) {
      learnedCount++;
      document.getElementById('learnedCount').textContent = learnedCount;
    }

    // Graph index cycles through MOCK_GRAPHS
    const gIdx = graphResponseIdx % (typeof MOCK_GRAPHS !== 'undefined' ? MOCK_GRAPHS.length : 1);
    graphResponseIdx++;

    addMessage('agent', resp.reply, resp.tool_calls || [], resp.learn, gIdx);

    // Show unread dot if chat is closed
    if (!chatOpen) {
      document.getElementById('chatBubble').classList.add('has-unread');
    }
  } catch (err) {
    removeTyping();
    addMessage('agent', 'Connection error: ' + err.message + '. Is the API running at ' + API_BASE + '?');
  }
}

// ── Markdown-lite formatter ────────────────────────────

function formatMarkdown(text) {
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

// ── Suggestion chips ─────────────────────────────────

function useSuggestion(el) {
  document.getElementById('chatInput').value = el.textContent;
  const suggestions = document.getElementById('chatSuggestions');
  if (suggestions) suggestions.style.display = 'none';
  sendMessage();
}

// ── Keyboard shortcut (Escape to close) ────────────────

function initChatKeyboard() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && chatOpen) toggleChat();
  });
}
