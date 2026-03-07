/**
 * products.js — Product grid rendering, filtering, search, and detail modal.
 */

let currentFilter = 'All';
let currentSubcategory = null;

// ── Render product grid ────────────────────────────────

function renderProducts(filter = 'All', search = '', subcategory = null) {
  const grid = document.getElementById('productGrid');
  let products = [...MOCK_PRODUCTS]; // Will be replaced by fetchProducts() when API is live

  if (filter !== 'All') products = products.filter(p => p.vertical === filter);
  if (subcategory) products = products.filter(p => p.subcategory === subcategory);
  if (search) {
    const q = search.toLowerCase();
    products = products.filter(p =>
      p.name.toLowerCase().includes(q) ||
      p.subcategory.toLowerCase().includes(q) ||
      (p.description && p.description.toLowerCase().includes(q))
    );
  }

  document.getElementById('productCount').textContent = `${products.length} products`;

  let title = 'All products';
  if (filter !== 'All') title = `${filter} products`;
  if (subcategory) title = `${filter} / ${subcategory}`;
  document.getElementById('sectionTitle').textContent = title;

  grid.innerHTML = products.map(p => `
    <div class="product-card" data-id="${p.id}" onclick="openProductDetail('${p.id}')">
      <span class="vertical-badge ${p.vertical}">${p.vertical}</span>
      <div class="product-image">
        ${p.image_url
          ? `<img src="${p.image_url}" alt="${p.name}" loading="lazy"
               onerror="this.parentElement.innerHTML='<div class=placeholder>&#128722;</div>'" />`
          : '<div class="placeholder">&#128722;</div>'
        }
      </div>
      <div class="product-info">
        <div class="product-subcategory">${p.subcategory}</div>
        <div class="product-name">${p.name}</div>
        <div class="product-meta">
          <span class="product-price">\u00a3${p.price.toFixed(2)}</span>
          <span class="product-rating">
            <span class="star">&#9733;</span> ${p.avg_rating.toFixed(1)}
          </span>
        </div>
      </div>
    </div>
  `).join('');
}

// ── Subcategory chips ────────────────────────────────────

function renderSubcategories(vertical) {
  const bar = document.getElementById('subcategoryBar');
  if (!vertical || vertical === 'All') {
    bar.innerHTML = '';
    bar.classList.remove('visible');
    currentSubcategory = null;
    return;
  }

  const subs = MOCK_SUBCATEGORIES[vertical] || [];
  bar.innerHTML = `
    <button class="subcategory-chip ${!currentSubcategory ? 'active' : ''}"
            onclick="selectSubcategory(null)">All ${vertical}</button>
    ${subs.map(s => `
      <button class="subcategory-chip ${currentSubcategory === s ? 'active' : ''}"
              onclick="selectSubcategory('${s}')">${s}</button>
    `).join('')}
  `;
  bar.classList.add('visible');
}

function selectSubcategory(sub) {
  currentSubcategory = sub;
  renderSubcategories(currentFilter);
  renderProducts(currentFilter, document.getElementById('searchInput').value, currentSubcategory);
}

// ── Product detail modal ───────────────────────────────

function openProductDetail(id) {
  const product = MOCK_PRODUCTS.find(p => p.id === id);
  if (!product) return;

  // Fill modal fields
  const imgEl = document.getElementById('modalImage');
  if (product.image_url) {
    imgEl.innerHTML = `<img src="${product.image_url}" alt="${product.name}"
      style="width:100%;height:100%;object-fit:cover;border-radius:12px"
      onerror="this.parentElement.innerHTML='<div class=placeholder style=font-size:80px>&#128722;</div>'" />`;
  } else {
    imgEl.innerHTML = '<div class="placeholder" style="font-size:80px">&#128722;</div>';
  }

  document.getElementById('modalVertical').textContent = product.vertical;
  document.getElementById('modalVertical').className = `modal-vertical ${product.vertical}`;
  document.getElementById('modalName').textContent = product.name;
  document.getElementById('modalDescription').textContent =
    product.description || `${product.subcategory} product in the ${product.vertical} range.`;
  document.getElementById('modalPrice').textContent = `\u00a3${product.price.toFixed(2)}`;

  // Stars
  const stars = '\u2605'.repeat(Math.round(product.avg_rating)) +
                '\u2606'.repeat(5 - Math.round(product.avg_rating));
  document.getElementById('modalRating').innerHTML =
    `<span style="color:var(--warning)">${stars}</span> ${product.avg_rating.toFixed(1)}`;

  // Also bought (graph data)
  const alsoBoughtIds = MOCK_ALSO_BOUGHT[id] || [];
  const alsoBoughtEl = document.getElementById('alsoBought');
  if (alsoBoughtIds.length > 0) {
    alsoBoughtEl.innerHTML = alsoBoughtIds.map(abId => {
      const ab = MOCK_PRODUCTS.find(p => p.id === abId);
      if (!ab) return '';
      return `
        <div class="also-bought-card" onclick="openProductDetail('${ab.id}')">
          <div class="also-bought-img">
            ${ab.image_url
              ? `<img src="${ab.image_url}" alt="${ab.name}" style="width:100%;height:100%;object-fit:cover;border-radius:6px"
                   onerror="this.parentElement.innerHTML='&#128722;'" />`
              : '&#128722;'}
          </div>
          <div class="also-bought-name">${ab.name}</div>
          <div class="also-bought-price">\u00a3${ab.price.toFixed(2)}</div>
        </div>
      `;
    }).join('');
  } else {
    alsoBoughtEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No co-purchase data yet</span>';
  }

  // Reviews
  const reviews = MOCK_REVIEWS[id] || [];
  const reviewsEl = document.getElementById('modalReviews');
  if (reviews.length > 0) {
    reviewsEl.innerHTML = reviews.map(r => {
      const sentimentColor = r.sentiment === 'positive' ? 'var(--success)'
        : r.sentiment === 'negative' ? 'var(--error)' : 'var(--warning)';
      const stars = '\u2605'.repeat(r.score) + '\u2606'.repeat(5 - r.score);
      return `
        <div class="review-card">
          <div class="review-header">
            <span style="color:var(--warning)">${stars}</span>
            <span class="review-sentiment" style="color:${sentimentColor}">${r.sentiment}</span>
          </div>
          <p class="review-comment">${r.comment}</p>
        </div>
      `;
    }).join('');
  } else {
    reviewsEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No reviews yet</span>';
  }

  // Store current product id for chat button
  document.getElementById('modalOverlay').dataset.productId = id;

  // Show modal
  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function askAboutProduct() {
  const id = document.getElementById('modalOverlay').dataset.productId;
  const product = MOCK_PRODUCTS.find(p => p.id === id);
  if (!product) return;

  closeModal();
  if (!chatOpen) toggleChat();
  document.getElementById('chatInput').value = `Tell me about ${product.name}`;
  sendMessage();
}

// ── Filter tab + search event binding ──────────────────

function initFilters() {
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentFilter = tab.dataset.vertical;
      currentSubcategory = null;
      renderSubcategories(currentFilter);
      renderProducts(currentFilter, document.getElementById('searchInput').value, currentSubcategory);
    });
  });

  document.getElementById('searchInput').addEventListener('input', (e) => {
    renderProducts(currentFilter, e.target.value, currentSubcategory);
  });
}
