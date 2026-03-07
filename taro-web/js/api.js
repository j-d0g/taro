/**
 * api.js — API abstraction layer with USE_MOCK toggle.
 * Flip USE_MOCK to false when the FastAPI backend is running.
 */

const API_BASE = 'http://localhost:8000';
const USE_MOCK = true;

let mockResponseIdx = 0;

// ── Product endpoints ──────────────────────────────────

async function fetchProducts(vertical = null, search = null) {
  if (USE_MOCK) {
    let products = [...MOCK_PRODUCTS];
    if (vertical && vertical !== 'All') {
      products = products.filter(p => p.vertical === vertical);
    }
    if (search) {
      const q = search.toLowerCase();
      products = products.filter(p =>
        p.name.toLowerCase().includes(q) ||
        p.subcategory.toLowerCase().includes(q) ||
        (p.description && p.description.toLowerCase().includes(q))
      );
    }
    return products;
  }

  // Real API
  const params = new URLSearchParams();
  if (vertical && vertical !== 'All') params.set('vertical', vertical);
  if (search) params.set('search', search);
  const res = await fetch(`${API_BASE}/products?${params}`);
  return res.json();
}

async function fetchProductDetail(productId) {
  if (USE_MOCK) {
    const product = MOCK_PRODUCTS.find(p => p.id === productId);
    if (!product) return null;

    const alsoBoughtIds = MOCK_ALSO_BOUGHT[productId] || [];
    const alsoBought = alsoBoughtIds
      .map(id => MOCK_PRODUCTS.find(p => p.id === id))
      .filter(Boolean);

    const reviews = MOCK_REVIEWS[productId] || [];

    return { ...product, also_bought: alsoBought, reviews };
  }

  // Real API
  const res = await fetch(`${API_BASE}/products/${productId}`);
  return res.json();
}

async function fetchVerticals() {
  if (USE_MOCK) {
    const verticals = [...new Set(MOCK_PRODUCTS.map(p => p.vertical))];
    return verticals.sort();
  }

  const res = await fetch(`${API_BASE}/verticals`);
  return res.json();
}

// ── Chat endpoint ──────────────────────────────────────

async function sendChatMessage(message, threadId) {
  if (USE_MOCK) {
    // Simulate network delay
    await new Promise(r => setTimeout(r, 1200 + Math.random() * 800));

    const resp = MOCK_RESPONSES[mockResponseIdx % MOCK_RESPONSES.length];
    mockResponseIdx++;

    return {
      reply: resp.reply,
      tool_calls: resp.tool_calls,
      learn: resp.learn || null,
      thread_id: threadId,
    };
  }

  // Real API
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  });

  const data = await res.json();

  // Normalise tool_calls to display format
  const toolCalls = (data.tool_calls || []).map(tc => {
    let type = 'relational';
    if (tc.name.includes('semantic') || tc.name.includes('vector')) type = 'vector';
    else if (tc.name.includes('graph') || tc.name.includes('traverse')) type = 'graph';
    else if (tc.name.includes('keyword') || tc.name.includes('hybrid')) type = 'bm25';
    return { name: tc.name, type, args: JSON.stringify(tc.args, null, 2) };
  });

  return {
    reply: data.reply,
    tool_calls: toolCalls,
    learn: null,
    thread_id: data.thread_id,
  };
}
