/**
 * api.js — API abstraction layer.
 * Always tries real API first; falls back to mock data on failure.
 */

const API_BASE = 'http://localhost:8002';

let mockResponseIdx = 0;

// ── Helpers ─────────────────────────────────────────────────

async function apiFetch(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

// ── Product endpoints ──────────────────────────────────────

async function fetchProducts(vertical = null, search = null) {
  try {
    const params = new URLSearchParams();
    if (vertical && vertical !== 'All') params.set('vertical', vertical);
    if (search) params.set('search', search);
    const qs = params.toString();
    return await apiFetch(`/products${qs ? '?' + qs : ''}`);
  } catch (e) {
    console.warn('fetchProducts fallback to mock:', e.message);
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
}

async function fetchProductDetail(productId) {
  try {
    return await apiFetch(`/products/${productId}`);
  } catch (e) {
    console.warn('fetchProductDetail fallback to mock:', e.message);
    const product = MOCK_PRODUCTS.find(p => p.id === productId);
    if (!product) return null;
    const alsoBoughtIds = MOCK_ALSO_BOUGHT[productId] || [];
    const alsoBought = alsoBoughtIds
      .map(id => MOCK_PRODUCTS.find(p => p.id === id))
      .filter(Boolean);
    const reviews = MOCK_REVIEWS[productId] || [];
    return { ...product, also_bought: alsoBought, reviews };
  }
}

async function fetchVerticals() {
  try {
    return await apiFetch('/verticals');
  } catch (e) {
    console.warn('fetchVerticals fallback to mock:', e.message);
    return [...new Set(MOCK_PRODUCTS.map(p => p.vertical))].sort();
  }
}

// ── Category endpoints ─────────────────────────────────────

async function fetchCategories() {
  try {
    const verticals = await apiFetch('/categories');
    // Flatten nested verticals into [{name, vertical}, ...] for subcategory chips
    return verticals.flatMap(v =>
      (v.subcategories || []).map(s => ({ id: s.id, name: s.name, vertical: v.name }))
    );
  } catch (e) {
    console.warn('fetchCategories fallback to mock:', e.message);
    return Object.entries(MOCK_SUBCATEGORIES).flatMap(([vertical, subs]) =>
      subs.map(s => ({ id: s.toLowerCase().replace(/\s+/g, '_'), name: s, vertical }))
    );
  }
}

async function fetchCategory(categoryId) {
  try {
    return await apiFetch(`/categories/${categoryId}`);
  } catch (e) {
    console.warn('fetchCategory fallback to mock:', e.message);
    return { id: categoryId, name: categoryId, products: [] };
  }
}

// ── Customer endpoints ─────────────────────────────────────

async function fetchCustomer(id) {
  try {
    return await apiFetch(`/customers/${id}`);
  } catch (e) {
    console.warn('fetchCustomer fallback to mock:', e.message);
    return MOCK_CUSTOMER;
  }
}

async function fetchCustomerOrders(id) {
  try {
    return await apiFetch(`/customers/${id}/orders`);
  } catch (e) {
    console.warn('fetchCustomerOrders fallback to mock:', e.message);
    return MOCK_CUSTOMER.orders || [];
  }
}

async function fetchCustomerRecommendations(id) {
  try {
    return await apiFetch(`/customers/${id}/recommendations`);
  } catch (e) {
    console.warn('fetchCustomerRecommendations fallback to mock:', e.message);
    // Derive from mock also_bought
    const boughtIds = new Set((MOCK_CUSTOMER.orders || []).flatMap(o => o.products));
    const recs = [];
    boughtIds.forEach(pid => {
      (MOCK_ALSO_BOUGHT[pid] || []).forEach(rid => {
        if (!boughtIds.has(rid)) {
          const p = MOCK_PRODUCTS.find(pr => pr.id === rid);
          if (p) recs.push({ ...p, reason: 'co-purchase pattern' });
        }
      });
    });
    return recs;
  }
}

// ── Goal endpoints ─────────────────────────────────────────

async function fetchGoals() {
  try {
    return await apiFetch('/goals');
  } catch (e) {
    console.warn('fetchGoals fallback to mock:', e.message);
    return [];
  }
}

async function fetchGoal(goalId) {
  try {
    return await apiFetch(`/goals/${goalId}`);
  } catch (e) {
    console.warn('fetchGoal fallback to mock:', e.message);
    return { id: goalId, name: goalId, products: [] };
  }
}

// ── Chat endpoint ──────────────────────────────────────────

async function sendChatMessage(message, threadId) {
  try {
    const data = await apiFetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, thread_id: threadId }),
    });

    // Normalise tool_calls to display format
    const toolCalls = (data.tool_calls || []).map(tc => {
      let type = 'relational';
      const name = tc.name || '';
      if (name.includes('semantic') || name.includes('vector')) type = 'vector';
      else if (name.includes('graph') || name.includes('traverse')) type = 'graph';
      else if (name.includes('keyword') || name.includes('hybrid')) type = 'bm25';
      else if (name.includes('ls') || name.includes('cat') || name.includes('find') || name.includes('grep') || name.includes('tree')) type = 'relational';
      else if (name.includes('web')) type = 'bm25';
      return { name, type, args: JSON.stringify(tc.args, null, 2) };
    });

    return {
      reply: data.reply,
      tool_calls: toolCalls,
      learn: null,
      thread_id: data.thread_id,
    };
  } catch (e) {
    console.warn('sendChatMessage fallback to mock:', e.message);
    // Simulate network delay
    await new Promise(r => setTimeout(r, 800 + Math.random() * 400));
    const resp = MOCK_RESPONSES[mockResponseIdx % MOCK_RESPONSES.length];
    mockResponseIdx++;
    return {
      reply: resp.reply,
      tool_calls: resp.tool_calls,
      learn: resp.learn || null,
      thread_id: threadId,
    };
  }
}

// ── Health check ───────────────────────────────────────────

async function checkApiHealth() {
  try {
    const data = await apiFetch('/health');
    return data.status === 'ok';
  } catch {
    return false;
  }
}
