/**
 * profile.js — Customer profile panel showing purchase history and recommendations.
 * Data comes from `placed->order->contains->product` and `also_bought` graph edges in SurrealDB.
 */

let profileOpen = false;

function toggleProfile() {
  profileOpen = !profileOpen;
  const overlay = document.getElementById('profileOverlay');
  overlay.classList.toggle('open', profileOpen);
  document.body.style.overflow = profileOpen ? 'hidden' : '';

  if (profileOpen) renderProfile();
}

function renderProfile() {
  const customer = MOCK_CUSTOMER;

  // Header
  document.getElementById('profileName').textContent = customer.name;
  document.getElementById('profileLocation').textContent =
    `${customer.city}, ${customer.state}`;

  // Stats — derived from orders (placed->order->contains->product)
  const allProductIds = customer.orders.flatMap(o => o.products);
  const uniqueProductIds = [...new Set(allProductIds)];
  const totalSpent = customer.orders.reduce((s, o) => s + o.price, 0);
  document.getElementById('profileStats').innerHTML = `
    <div class="profile-stat">
      <div class="profile-stat-value">${uniqueProductIds.length}</div>
      <div class="profile-stat-label">Products</div>
    </div>
    <div class="profile-stat">
      <div class="profile-stat-value">${customer.orders.length}</div>
      <div class="profile-stat-label">Orders</div>
    </div>
    <div class="profile-stat">
      <div class="profile-stat-value">\u00a3${totalSpent.toFixed(2)}</div>
      <div class="profile-stat-label">Total Spent</div>
    </div>
  `;

  // Purchase history — models placed->order->contains->product
  const purchasesEl = document.getElementById('profilePurchases');
  purchasesEl.innerHTML = customer.orders.map(order => {
    const products = order.products.map(pid => MOCK_PRODUCTS.find(p => p.id === pid)).filter(Boolean);
    if (!products.length) return '';
    return `
      <div class="profile-purchase-card">
        <div class="profile-purchase-info" style="flex:1">
          <div class="profile-purchase-name" style="font-size:11px;color:var(--text-dim)">Order ${order.order_id}</div>
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
                  <span class="vertical-badge-sm ${product.vertical}">${product.vertical}</span>
                  ${product.subcategory}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
        <div class="profile-purchase-right">
          <div class="profile-purchase-price">\u00a3${order.price.toFixed(2)}</div>
          <div class="profile-purchase-count">${order.products.length} item${order.products.length > 1 ? 's' : ''}</div>
        </div>
      </div>
    `;
  }).join('');

  // Recommendations: placed->order->contains->product, then product->also_bought->product
  const boughtIds = new Set(customer.orders.flatMap(o => o.products));
  const recIds = new Set();
  boughtIds.forEach(pid => {
    const related = MOCK_ALSO_BOUGHT[pid] || [];
    related.forEach(rid => {
      if (!boughtIds.has(rid)) recIds.add(rid);
    });
  });

  const recsEl = document.getElementById('profileRecommendations');
  if (recIds.size === 0) {
    recsEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No recommendations yet — purchase more products to build your graph!</span>';
    return;
  }

  recsEl.innerHTML = [...recIds].map(rid => {
    const product = MOCK_PRODUCTS.find(p => p.id === rid);
    if (!product) return '';
    return `
      <div class="profile-rec-card" onclick="toggleProfile(); openProductDetail('${product.id}')">
        <div class="profile-rec-img">
          ${product.image_url
            ? `<img src="${product.image_url}" alt="${product.name}"
                 onerror="this.parentElement.innerHTML='&#128722;'" />`
            : '&#128722;'}
        </div>
        <div class="profile-rec-name">${product.name}</div>
        <div class="profile-rec-price">\u00a3${product.price.toFixed(2)}</div>
        <div class="profile-rec-reason">via also_bought graph edge (co-purchase pattern)</div>
      </div>
    `;
  }).join('');
}
