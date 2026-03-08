/**
 * api.js — API abstraction layer.
 * Tries real API first, falls back to mock data with console warning.
 */

const API_BASE = 'http://localhost:8002';

let mockResponseIdx = 0;

// ── Product endpoints ──────────────────────────────────

async function fetchProducts(vertical = null, search = null) {
  try {
    const params = new URLSearchParams();
    if (vertical && vertical !== 'All') params.set('vertical', vertical);
    if (search) params.set('search', search);
    const res = await fetch(`${API_BASE}/products?${params}`);
    if (!res.ok) throw new Error(`API ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('fetchProducts: API unavailable, using mock data:', err.message);
    let products = typeof MOCK_PRODUCTS !== 'undefined' ? [...MOCK_PRODUCTS] : [];
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
}

async function fetchProductDetail(productId) {
  try {
    const res = await fetch(`${API_BASE}/products/${productId}`);
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    if (data.error) {
      console.warn('fetchProductDetail: product not found:', data.error);
      throw new Error(data.error);
    }
    return data;
  } catch (err) {
    console.warn('fetchProductDetail: API unavailable, using mock data:', err.message);
    if (typeof MOCK_PRODUCTS === 'undefined') return null;
    const product = MOCK_PRODUCTS.find(p => p.id === productId);
    if (!product) return null;

    const alsoBoughtIds = (typeof MOCK_ALSO_BOUGHT !== 'undefined' ? MOCK_ALSO_BOUGHT[productId] : null) || [];
    const alsoBought = alsoBoughtIds
      .map(id => MOCK_PRODUCTS.find(p => p.id === id))
      .filter(Boolean);

    const reviews = (typeof MOCK_REVIEWS !== 'undefined' ? MOCK_REVIEWS[productId] : null) || [];

    return { ...product, also_bought: alsoBought, reviews };
  }
}

async function fetchVerticals() {
  try {
    const res = await fetch(`${API_BASE}/verticals`);
    if (!res.ok) throw new Error(`API ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('fetchVerticals: API unavailable, using mock data:', err.message);
    if (typeof MOCK_PRODUCTS === 'undefined') return [];
    const verticals = [...new Set(MOCK_PRODUCTS.map(p => p.vertical))];
    return verticals.sort();
  }
}

async function fetchCategories(vertical = null) {
  try {
    const res = await fetch(`${API_BASE}/categories`);
    if (!res.ok) throw new Error(`API ${res.status}`);
    const verticals = await res.json();
    if (!vertical) return verticals;
    // Find the matching vertical and return its subcategory names
    const match = verticals.find(v => v.name === vertical);
    return match ? (match.subcategories || []).map(s => s.name) : [];
  } catch (err) {
    console.warn('fetchCategories: API unavailable, using mock data:', err.message);
    if (typeof MOCK_SUBCATEGORIES === 'undefined') return [];
    return MOCK_SUBCATEGORIES[vertical] || [];
  }
}

async function fetchCustomerProfile(customerId) {
  try {
    const res = await fetch(`${API_BASE}/customers/${customerId}/profile`);
    if (!res.ok) throw new Error(`API ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('fetchCustomerProfile: API unavailable, using mock data:', err.message);
    return typeof MOCK_CUSTOMER_PROFILE !== 'undefined' ? MOCK_CUSTOMER_PROFILE : null;
  }
}

async function fetchCustomer(customerId) {
  try {
    const res = await fetch(`${API_BASE}/customers/${customerId}`);
    if (!res.ok) throw new Error(`API ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('fetchCustomer: API unavailable, using mock data:', err.message);
    return typeof MOCK_CUSTOMER !== 'undefined' ? MOCK_CUSTOMER : null;
  }
}

async function fetchCustomerOrders(customerId) {
  try {
    const res = await fetch(`${API_BASE}/customers/${customerId}/orders`);
    if (!res.ok) throw new Error(`API ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('fetchCustomerOrders: API unavailable, using mock data:', err.message);
    return typeof MOCK_CUSTOMER !== 'undefined' ? (MOCK_CUSTOMER.orders || []) : [];
  }
}

async function fetchCustomerRecommendations(customerId) {
  try {
    const res = await fetch(`${API_BASE}/customers/${customerId}/recommendations`);
    if (!res.ok) throw new Error(`API ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('fetchCustomerRecommendations: API unavailable, using mock data:', err.message);
    return [];
  }
}

// ── Chat endpoint ──────────────────────────────────────

async function sendChatMessage(message, threadId) {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, thread_id: threadId, user_id: typeof DEMO_CUSTOMER_ID !== 'undefined' ? DEMO_CUSTOMER_ID : null }),
    });
    if (!res.ok) throw new Error(`API ${res.status}`);

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
      products: data.products || [],
      learn: null,
      thread_id: data.thread_id,
    };
  } catch (err) {
    console.warn('sendChatMessage: API unavailable, using mock data:', err.message);
    if (typeof MOCK_RESPONSES === 'undefined') {
      return { reply: 'API is currently unavailable. Please start the backend server.', tool_calls: [], learn: null, thread_id: threadId };
    }

    await new Promise(r => setTimeout(r, 800 + Math.random() * 400));
    const resp = MOCK_RESPONSES[mockResponseIdx % MOCK_RESPONSES.length];
    mockResponseIdx++;
    return {
      reply: resp.reply,
      tool_calls: resp.tool_calls,
      products: resp.products || [],
      learn: resp.learn || null,
      thread_id: threadId,
    };
  }
}

// ── Streaming chat (SSE) ──────────────────────────────

/**
 * Stream chat response via SSE. Calls onEvent(type, data) for each event.
 * Event types: "thinking", "tool_start", "tool_end", "token", "done", "error".
 */
async function sendChatMessageStream(message, threadId, onEvent) {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      thread_id: threadId,
      user_id: typeof DEMO_CUSTOMER_ID !== 'undefined' ? DEMO_CUSTOMER_ID : null,
    }),
  });

  if (!res.ok) throw new Error(`API ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const blocks = buffer.split('\n\n');
    buffer = blocks.pop();

    for (const block of blocks) {
      if (!block.trim()) continue;
      let eventType = null;
      let data = null;

      for (const line of block.split('\n')) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7);
        } else if (line.startsWith('data: ')) {
          try {
            data = JSON.parse(line.slice(6));
          } catch (e) {
            console.warn('SSE parse error:', line);
          }
        }
      }

      if (eventType && data) {
        onEvent(eventType, data);
      }
    }
  }
}

// ── Health check ───────────────────────────────────────

async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
