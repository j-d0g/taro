/**
 * profile.js — Customer profile panel showing purchase history and recommendations.
 * Data comes from the `bought` and `also_bought` graph edges in SurrealDB.
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

  // Stats
  const totalSpent = customer.purchases.reduce((s, p) => s + p.total_spent, 0);
  const totalOrders = customer.purchases.reduce((s, p) => s + p.order_count, 0);
  document.getElementById('profileStats').innerHTML = `
    <div class="profile-stat">
      <div class="profile-stat-value">${customer.purchases.length}</div>
      <div class="profile-stat-label">Products</div>
    </div>
    <div class="profile-stat">
      <div class="profile-stat-value">${totalOrders}</div>
      <div class="profile-stat-label">Orders</div>
    </div>
    <div class="profile-stat">
      <div class="profile-stat-value">\u00a3${totalSpent.toFixed(2)}</div>
      <div class="profile-stat-label">Total Spent</div>
    </div>
  `;

  // Purchase history
  const purchasesEl = document.getElementById('profilePurchases');
  purchasesEl.innerHTML = customer.purchases.map(purchase => {
    const product = MOCK_PRODUCTS.find(p => p.id === purchase.product_id);
    if (!product) return '';
    return `
      <div class="profile-purchase-card" onclick="toggleProfile(); openProductDetail('${product.id}')">
        <div class="profile-purchase-img">
          ${product.image_url
            ? `<img src="${product.image_url}" alt="${product.name}"
                 onerror="this.parentElement.innerHTML='&#128722;'" />`
            : '&#128722;'}
        </div>
        <div class="profile-purchase-info">
          <div class="profile-purchase-name">${product.name}</div>
          <div class="profile-purchase-meta">
            <span class="vertical-badge-sm ${product.vertical}">${product.vertical}</span>
            ${product.subcategory}
          </div>
        </div>
        <div class="profile-purchase-right">
          <div class="profile-purchase-price">\u00a3${purchase.total_spent.toFixed(2)}</div>
          <div class="profile-purchase-count">${purchase.order_count}x ordered</div>
        </div>
      </div>
    `;
  }).join('');

  // Recommendations: collect also_bought from purchased products, exclude already-bought
  const boughtIds = new Set(customer.purchases.map(p => p.product_id));
  const recIds = new Set();
  customer.purchases.forEach(purchase => {
    const related = MOCK_ALSO_BOUGHT[purchase.product_id] || [];
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
        <div class="profile-rec-reason">Customers who bought similar items also bought this</div>
      </div>
    `;
  }).join('');
}
