/**
 * chat.js — Chat panel, messages, tool trace cards, graph viz, product cards, typing indicator.
 */

let chatOpen = false;
let threadId = localStorage.getItem('taro_thread_id') || crypto.randomUUID();
localStorage.setItem('taro_thread_id', threadId);
let queryCount = 0;
let learnedCount = 0;
let copilotMode = localStorage.getItem('copilotMode') === 'true';

function toggleCopilot() {
  copilotMode = !copilotMode;
  document.body.classList.toggle('copilot-active', copilotMode);
  localStorage.setItem('copilotMode', copilotMode);
  document.getElementById('chatExpand').innerHTML = copilotMode ? '&#8646;' : '&#8644;';
  if (copilotMode) {
    // Auto-open panel when entering copilot mode (bubble is hidden)
    chatOpen = true;
    document.getElementById('chatPanel').classList.add('open');
  }
}

if (copilotMode) {
  document.body.classList.add('copilot-active');
  // Auto-open chat panel in copilot mode (bubble is hidden)
  chatOpen = true;
  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('chatPanel').classList.add('open');
  });
}

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

// ── Product reference extraction ───────────────────────

function extractProductReferences(text) {
  // Match **Product Name** (£XX.XX) or just **Product Name**
  const refs = [];
  const regex = /\*\*([^*]+)\*\*(?:\s*\([\u00a3$]?([\d.]+)\))?/g;
  let match;
  while ((match = regex.exec(text)) !== null) {
    refs.push({ name: match[1].trim(), price: match[2] ? parseFloat(match[2]) : null });
  }
  return refs;
}

function findProductByName(name) {
  if (!cachedProducts || !cachedProducts.length) return null;
  const lower = name.toLowerCase();
  // Exact match
  let found = cachedProducts.find(p => p.name.toLowerCase() === lower);
  if (found) return found;
  // Fuzzy: product name starts with or contains the reference
  found = cachedProducts.find(p => p.name.toLowerCase().startsWith(lower));
  if (found) return found;
  found = cachedProducts.find(p => p.name.toLowerCase().includes(lower));
  if (found) return found;
  // Reverse: reference contains product name
  found = cachedProducts.find(p => lower.includes(p.name.toLowerCase()));
  return found || null;
}

function renderChatProductCards(products) {
  if (!products || products.length === 0) return '';

  const cards = products.map(p => {
    const vc = typeof verticalClass === 'function' ? verticalClass(p.vertical) : (p.vertical || '').toLowerCase();
    const rating = p.avg_rating || 0;
    const stars = '\u2605'.repeat(Math.round(rating)) + '\u2606'.repeat(5 - Math.round(rating));
    return `
      <div class="chat-product-card" id="chat-product-${p.id}" data-product-id="${p.id}">
        <div class="chat-product-main" onclick="openProductDetail('${p.id}')">
          <div class="chat-product-img">
            ${p.image_url
              ? `<img src="${p.image_url}" alt="${escapeHtml(p.name)}"
                   onerror="this.parentElement.innerHTML='&#128722;'" />`
              : '&#128722;'}
          </div>
          <div class="chat-product-info">
            <div class="chat-product-name">${escapeHtml(p.name)}</div>
            <div class="chat-product-meta">
              <span class="chat-product-price">\u00a3${(p.price || 0).toFixed(2)}</span>
              <span class="chat-product-rating"><span style="color:var(--warning)">${stars}</span> ${rating.toFixed(1)}</span>
            </div>
          </div>
        </div>
        <div class="chat-product-actions">
          <button class="pref-btn pref-cart" title="Add to cart" onclick="handlePreference('${p.id}', 'cart', this)">
            &#128722;
          </button>
          <button class="pref-btn pref-keep" title="Save for later" onclick="handlePreference('${p.id}', 'keep', this)">
            &#128278;
          </button>
          <button class="pref-btn pref-remove" title="Not interested" onclick="handlePreference('${p.id}', 'remove', this)">
            &#10005;
          </button>
        </div>
      </div>
    `;
  }).join('');

  return `<div class="chat-product-cards">${cards}</div>`;
}

async function handlePreference(productId, action, btnEl) {
  const card = document.getElementById(`chat-product-${productId}`);
  if (!card) return;

  // Visual feedback immediately
  if (action === 'cart') {
    card.classList.add('pref-carted');
    btnEl.innerHTML = '&#10003;';
  } else if (action === 'keep') {
    card.classList.add('pref-saved');
    btnEl.innerHTML = '&#10003;';
  } else if (action === 'remove') {
    card.classList.add('pref-removed');
    setTimeout(() => card.style.display = 'none', 300);
  }

  // Disable all action buttons on this card
  card.querySelectorAll('.pref-btn').forEach(b => b.disabled = true);

  // Send to backend
  const result = await sendPreference(productId, action);
  if (!result || !result.success) {
    // Revert on failure
    card.className = 'chat-product-card';
    card.style.display = '';
    card.querySelectorAll('.pref-btn').forEach(b => b.disabled = false);
  }
}

// ── Add message to chat ────────────────────────────────

function addMessage(role, content, toolCalls = [], learnMsg = null, graphIdx = null, products = []) {
  const container = document.getElementById('chatMessages');

  const msgDiv = document.createElement('div');
  msgDiv.className = `msg ${role}`;

  // Message bubble
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = formatMarkdown(content);
  msgDiv.appendChild(bubble);

  // Product cards for agent messages
  if (role === 'agent') {
    let matchedProducts = products || [];

    // If no structured products provided, try text extraction
    if (matchedProducts.length === 0) {
      const refs = extractProductReferences(content);
      matchedProducts = refs
        .map(ref => findProductByName(ref.name))
        .filter(Boolean);
    }

    if (matchedProducts.length > 0) {
      const cardsDiv = document.createElement('div');
      cardsDiv.innerHTML = renderChatProductCards(matchedProducts);
      msgDiv.appendChild(cardsDiv.firstElementChild);
    }
  }

  // Tool trace cards (collapsed by default, click to expand)
  if (toolCalls.length > 0) {
    const iconMap = {
      vector: '&#128269;',
      graph: '&#128760;',
      bm25: '&#128196;',
      relational: '&#9881;',
      web: '&#127760;',
    };
    const labelMap = {
      ls: 'Browse', cat: 'Read', find: 'Semantic search',
      grep: 'Keyword search', tree: 'Hierarchy', explore_schema: 'Schema',
      graph_traverse: 'Graph traversal', surrealql_query: 'SQL query',
      web_search: 'Web search',
    };

    const traceDiv = document.createElement('div');
    traceDiv.className = 'tool-trace';
    const summary = toolCalls.map(tc => labelMap[tc.name] || tc.name).join(', ');
    traceDiv.innerHTML = `
      <div class="tool-trace-summary" onclick="this.parentElement.classList.toggle('expanded')">
        &#9881; ${toolCalls.length} tool${toolCalls.length > 1 ? 's' : ''}: ${summary}
      </div>
      <div class="tool-trace-details">
        ${toolCalls.map(tc => `
          <div class="tool-card">
            <div class="tool-card-header">
              <span class="tool-icon ${tc.type}">${iconMap[tc.type] || '&#9881;'}</span>
              ${labelMap[tc.name] || tc.name}
              <span class="tool-label ${tc.type}">${tc.type}</span>
            </div>
            <div class="tool-card-detail"><pre>${escapeHtml(tc.args)}</pre></div>
          </div>
        `).join('')}
      </div>
    `;
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

// ── Streaming message renderer ────────────────────────

function createStreamingMessage() {
  const container = document.getElementById('chatMessages');

  const msgDiv = document.createElement('div');
  msgDiv.className = 'msg agent';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble streaming';
  msgDiv.appendChild(bubble);

  const traceDiv = document.createElement('div');
  traceDiv.className = 'tool-trace';
  traceDiv.style.display = 'none';
  msgDiv.insertBefore(traceDiv, bubble);

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;

  let textBuffer = '';
  const toolCards = {};

  return {
    appendToken(content) {
      textBuffer += content;
      bubble.innerHTML = formatMarkdown(textBuffer);
      container.scrollTop = container.scrollHeight;
    },

    addToolStart(id, name, args) {
      traceDiv.style.display = '';
      const iconMap = {
        vector: '&#128269;', graph: '&#128760;',
        bm25: '&#128196;', relational: '&#9881;',
      };
      let type = 'relational';
      if (name.includes('find') || name.includes('semantic')) type = 'vector';
      else if (name.includes('graph') || name.includes('traverse')) type = 'graph';
      else if (name.includes('grep') || name.includes('keyword')) type = 'bm25';

      const card = document.createElement('div');
      card.className = 'tool-card streaming-tool';
      card.onclick = () => card.classList.toggle('expanded');
      card.innerHTML = `
        <div class="tool-card-header">
          <span class="tool-icon ${type}">${iconMap[type] || '&#9881;'}</span>
          ${name}
          <span class="tool-label ${type}">${type}</span>
          <span class="tool-spinner"></span>
        </div>
        <div class="tool-card-detail">${escapeHtml(JSON.stringify(args, null, 2))}</div>
      `;
      traceDiv.appendChild(card);
      toolCards[id] = card;
      container.scrollTop = container.scrollHeight;
    },

    completeToolEnd(id, durationMs) {
      const card = toolCards[id];
      if (!card) return;
      card.classList.remove('streaming-tool');
      card.classList.add('completed-tool');
      const spinner = card.querySelector('.tool-spinner');
      if (spinner) spinner.outerHTML = `<span class="tool-duration">${durationMs}ms</span>`;
    },

    addThinking(content) {
      const el = document.createElement('div');
      el.className = 'agent-thinking';
      el.innerHTML = '&#129504; <em>' + escapeHtml(content) + '</em>';
      traceDiv.style.display = '';
      traceDiv.appendChild(el);
      container.scrollTop = container.scrollHeight;
    },

    addProducts(products) {
      if (!products || products.length === 0) return;
      const cardsHtml = renderChatProductCards(products);
      if (cardsHtml) {
        const div = document.createElement('div');
        div.innerHTML = cardsHtml;
        msgDiv.appendChild(div.firstElementChild);
      }
    },

    showLearn(insight) {
      const learnDiv = document.createElement('div');
      learnDiv.className = 'self-improve';
      learnDiv.innerHTML = '&#129504; ' + escapeHtml(insight);
      msgDiv.appendChild(learnDiv);
      container.scrollTop = container.scrollHeight;
      learnedCount++;
      document.getElementById('learnedCount').textContent = learnedCount;
    },

    finalize() {
      bubble.classList.remove('streaming');
    },
  };
}

// ── Send message ───────────────────────────────────────

let graphResponseIdx = 0;

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  addMessage('user', text);

  try {
    const stream = createStreamingMessage();
    let streamWorked = false;

    try {
      await sendChatMessageStream(text, threadId, (eventType, data) => {
        streamWorked = true;
        switch (eventType) {
          case 'token':
            stream.appendToken(data.content || '');
            break;
          case 'tool_start':
            stream.addToolStart(data.id, data.name, data.args || {});
            break;
          case 'tool_end':
            stream.completeToolEnd(data.id, data.duration_ms || 0);
            break;
          case 'thinking':
            stream.addThinking(data.content || '');
            break;
          case 'learn':
            stream.showLearn(data.insight || 'Pattern captured');
            break;
          case 'done':
            queryCount += (data.tool_calls || []).length;
            document.getElementById('queryCount').textContent = queryCount;
            stream.addProducts(data.products || []);
            stream.finalize();
            break;
          case 'error':
            stream.appendToken('\n\n_Error: ' + (data.message || 'Unknown error') + '_');
            break;
        }
      });
    } catch (streamErr) {
      if (!streamWorked) {
        const container = document.getElementById('chatMessages');
        container.lastChild.remove();

        showTyping();
        const resp = await sendChatMessage(text, threadId);
        removeTyping();
        queryCount += (resp.tool_calls || []).length;
        document.getElementById('queryCount').textContent = queryCount;
        if (resp.learn) {
          learnedCount++;
          document.getElementById('learnedCount').textContent = learnedCount;
        }
        const gIdx = graphResponseIdx % (typeof MOCK_GRAPHS !== 'undefined' ? MOCK_GRAPHS.length : 1);
        graphResponseIdx++;
        addMessage('agent', resp.reply, resp.tool_calls || [], resp.learn, gIdx, resp.products || []);
      } else {
        stream.appendToken('\n\n_Connection lost during streaming._');
        stream.finalize();
      }
    }

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

// ── Streaming send message ─────────────────────────────

async function sendMessageStreaming() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  addMessage('user', text);

  // Create a streaming message container
  const container = document.getElementById('chatMessages');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'msg agent';
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = '<span class="stream-cursor">|</span>';
  msgDiv.appendChild(bubble);
  container.appendChild(msgDiv);

  let fullText = '';
  const toolCalls = [];

  try {
    await sendChatMessageStream(text, threadId, (event) => {
      switch (event.type) {
        case 'reasoning':
          bubble.innerHTML = `<em style="color:var(--text-dim)">${escapeHtml(event.content)}</em><span class="stream-cursor">|</span>`;
          break;
        case 'tool_call':
          toolCalls.push({ name: event.name, type: 'relational', args: JSON.stringify(event.args) });
          bubble.innerHTML += `<br><span style="color:var(--text-dim);font-size:11px">&#9881; ${escapeHtml(event.name)}</span>`;
          break;
        case 'token':
          fullText += event.content;
          bubble.innerHTML = formatMarkdown(fullText) + '<span class="stream-cursor">|</span>';
          break;
        case 'done':
          bubble.innerHTML = formatMarkdown(fullText);
          // Add tool trace cards
          if (toolCalls.length > 0) {
            const traceDiv = document.createElement('div');
            traceDiv.className = 'tool-trace';
            traceDiv.innerHTML = toolCalls.map(tc => `
              <div class="tool-card" onclick="this.classList.toggle('expanded')">
                <div class="tool-card-header">
                  <span class="tool-icon ${tc.type}">&#9881;</span>
                  ${tc.name}
                  <span class="tool-label ${tc.type}">${tc.type}</span>
                </div>
                <div class="tool-card-detail">${escapeHtml(tc.args)}</div>
              </div>
            `).join('');
            msgDiv.appendChild(traceDiv);
          }
          queryCount += toolCalls.length;
          document.getElementById('queryCount').textContent = queryCount;
          break;
        case 'error':
          bubble.innerHTML = `<span style="color:var(--error)">Error: ${escapeHtml(event.content)}</span>`;
          break;
      }
      container.scrollTop = container.scrollHeight;
    });
  } catch (err) {
    bubble.innerHTML = 'Connection error: ' + escapeHtml(err.message);
  }
}

// ── New Chat ───────────────────────────────────────────

function newChat() {
  threadId = crypto.randomUUID();
  localStorage.setItem('taro_thread_id', threadId);
  document.getElementById('chatMessages').innerHTML = `
    <div class="msg agent">
      <div class="msg-bubble">
        Hi! I'm your shopping assistant powered by SurrealDB's multi-model
        engine. What are you looking for?
      </div>
    </div>
    <div class="chat-suggestions" id="chatSuggestions">
      <button class="suggestion-chip" onclick="useSuggestion(this)">Best sellers under &pound;30</button>
      <button class="suggestion-chip" onclick="useSuggestion(this)">Skincare routine for dry skin</button>
      <button class="suggestion-chip" onclick="useSuggestion(this)">Compare retinol serums</button>
    </div>
  `;
  queryCount = 0;
  learnedCount = 0;
  document.getElementById('queryCount').textContent = '0';
  document.getElementById('learnedCount').textContent = '0';
}

// ── Keyboard shortcut (Escape to close) ────────────────

function initChatKeyboard() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && chatOpen) toggleChat();
  });
}
