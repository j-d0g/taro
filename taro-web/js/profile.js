/**
 * profile.js — Customer profile panel showing purchase history and recommendations.
 * Data comes from real API: /customers/{id}, /customers/{id}/orders, /customers/{id}/recommendations
 * Falls back to mock data if API is unavailable.
 */

let profileOpen = false;
const DEMO_CUSTOMER_ID = 'diego_carvalho';

function toggleProfile() {
  profileOpen = !profileOpen;
  const overlay = document.getElementById('profileOverlay');
  overlay.classList.toggle('open', profileOpen);
  document.body.style.overflow = profileOpen ? 'hidden' : '';

  if (profileOpen) renderProfile();
}

async function renderProfile() {
  // Show loading state
  document.getElementById('profileName').textContent = 'Loading...';
  document.getElementById('profileLocation').textContent = '';
  document.getElementById('profileStats').innerHTML = `
    <div class="profile-stat"><div class="profile-stat-value" style="opacity:0.3">--</div><div class="profile-stat-label">Products</div></div>
    <div class="profile-stat"><div class="profile-stat-value" style="opacity:0.3">--</div><div class="profile-stat-label">Orders</div></div>
    <div class="profile-stat"><div class="profile-stat-value" style="opacity:0.3">--</div><div class="profile-stat-label">Spent</div></div>
  `;
  document.getElementById('profilePurchases').innerHTML = '<div style="color:var(--text-dim);font-size:12px;padding:8px">Loading orders...</div>';
  document.getElementById('profileRecommendations').innerHTML = '<div style="color:var(--text-dim);font-size:12px;padding:8px">Loading recommendations...</div>';

  // Fetch customer data, orders, and recommendations in parallel
  const [customer, orders, recommendations] = await Promise.all([
    fetchCustomer(DEMO_CUSTOMER_ID),
    fetchCustomerOrders(DEMO_CUSTOMER_ID),
    fetchCustomerRecommendations(DEMO_CUSTOMER_ID),
  ]);

  // Header
  const name = customer.name || customer.full_name || 'Customer';
  document.getElementById('profileName').textContent = name;

  const location = customer.city
    ? `${customer.city}${customer.state ? ', ' + customer.state : ''}`
    : '';
  document.getElementById('profileLocation').textContent = location;

  // Update navbar avatar
  const initial = name.charAt(0).toUpperCase();
  const firstName = name.split(' ')[0];
  document.querySelector('.profile-avatar').textContent = initial;
  document.querySelector('.profile-name').textContent = firstName;
  document.querySelector('.profile-header-avatar').textContent = initial;

  // Context/preferences section
  let contextHtml = '';
  if (customer.context) {
    contextHtml += `<div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 12px;margin-bottom:16px;font-size:12px;color:var(--text-secondary);line-height:1.5">${customer.context}</div>`;
  }
  if (customer.preferences) {
    const prefs = customer.preferences;
    const chips = [];
    if (prefs.skin_type) chips.push(prefs.skin_type);
    if (prefs.fitness_goals) chips.push(...(Array.isArray(prefs.fitness_goals) ? prefs.fitness_goals : [prefs.fitness_goals]));
    if (prefs.dietary_restrictions) chips.push(...(Array.isArray(prefs.dietary_restrictions) ? prefs.dietary_restrictions : [prefs.dietary_restrictions]));
    if (chips.length) {
      contextHtml += `<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:16px">${chips.map(c =>
        `<span class="subcategory-chip" style="cursor:default;font-size:10px;padding:3px 8px">${c}</span>`
      ).join('')}</div>`;
    }
  }
  if (customer.memory && customer.memory.length) {
    contextHtml += `<div style="margin-bottom:16px">${customer.memory.map(m =>
      `<div style="font-size:11px;color:var(--text-dim);padding:3px 0">&#128161; ${m}</div>`
    ).join('')}</div>`;
  }

  // Stats
  const orderList = Array.isArray(orders) ? orders : [];
  const allProductIds = orderList.flatMap(o => o.products || []);
  const uniqueProducts = [...new Set(allProductIds.map(p => typeof p === 'object' ? p.id : p))];
  const totalSpent = orderList.reduce((s, o) => s + (o.total || o.price || 0), 0);

  document.getElementById('profileStats').innerHTML = `
    ${contextHtml}
    <div style="display:flex;gap:12px">
      <div class="profile-stat">
        <div class="profile-stat-value">${uniqueProducts.length}</div>
        <div class="profile-stat-label">Products</div>
      </div>
      <div class="profile-stat">
        <div class="profile-stat-value">${orderList.length}</div>
        <div class="profile-stat-label">Orders</div>
      </div>
      <div class="profile-stat">
        <div class="profile-stat-value">\u00a3${totalSpent.toFixed(2)}</div>
        <div class="profile-stat-label">Total Spent</div>
      </div>
    </div>
  `;

  // Purchase history
  const purchasesEl = document.getElementById('profilePurchases');
  if (orderList.length === 0) {
    purchasesEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No purchase history yet</span>';
  } else {
    purchasesEl.innerHTML = orderList.map(order => {
      // Products can be full objects or just IDs
      const products = (order.products || []).map(p => {
        if (typeof p === 'object') return p;
        return MOCK_PRODUCTS.find(mp => mp.id === p) || { id: p, name: p, vertical: '', subcategory: '' };
      });
      if (!products.length) return '';

      const orderPrice = order.total || order.price || 0;
      const priceStr = typeof orderPrice === 'number' ? orderPrice.toFixed(2) : orderPrice;

      return `
        <div class="profile-purchase-card">
          <div class="profile-purchase-info" style="flex:1">
            <div class="profile-purchase-name" style="font-size:11px;color:var(--text-dim)">
              Order ${order.order_id || order.id || ''}
              ${order.date ? `<span style="margin-left:8px;font-size:10px">${order.date}</span>` : ''}
            </div>
            ${products.map(product => `
              <div style="display:flex;align-items:center;gap:8px;margin-top:6px;cursor:pointer" onclick="toggleProfile(); openProductDetail('${product.id}')">
                <div class="profile-purchase-img" style="width:36px;height:36px;min-width:36px">
                  ${product.image_url
                    ? `<img src="${product.image_url}" alt="${product.name}"
                         onerror="this.parentElement.innerHTML='&#128722;'" />`
                    : '&#128722;'}
                </div>
                <div>
                  <div class="profile-purchase-name">${product.name}</div>
                  <div class="profile-purchase-meta">
                    ${product.vertical ? `<span class="vertical-badge-sm ${product.vertical}">${product.vertical}</span>` : ''}
                    ${product.subcategory || ''}
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
          <div class="profile-purchase-right">
            <div class="profile-purchase-price">\u00a3${priceStr}</div>
            <div class="profile-purchase-count">${products.length} item${products.length > 1 ? 's' : ''}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Recommendations
  const recsEl = document.getElementById('profileRecommendations');
  const recs = Array.isArray(recommendations) ? recommendations : [];
  if (recs.length === 0) {
    recsEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No recommendations yet -- purchase more products to build your graph!</span>';
    return;
  }

  recsEl.innerHTML = recs.map(product => {
    const recPrice = typeof product.price === 'number' ? product.price.toFixed(2) : product.price;
    return `
      <div class="profile-rec-card" onclick="toggleProfile(); openProductDetail('${product.id}')">
        <div class="profile-rec-img">
          ${product.image_url
            ? `<img src="${product.image_url}" alt="${product.name}"
                 onerror="this.parentElement.innerHTML='&#128722;'" />`
            : '&#128722;'}
        </div>
        <div class="profile-rec-name">${product.name}</div>
        <div class="profile-rec-price">\u00a3${recPrice}</div>
        <div class="profile-rec-reason">${product.reason || 'via also_bought graph edge'}</div>
      </div>
    `;
  }).join('');
}
