/**
 * products.js — Product grid rendering, filtering, search, and detail modal.
 */

let currentFilter = 'All';
let currentSubcategory = null;
let _searchDebounce = null;

// ── Loading skeleton ──────────────────────────────────────

function showGridLoading() {
  const grid = document.getElementById('productGrid');
  grid.innerHTML = Array(8).fill(0).map(() => `
    <div class="product-card" style="pointer-events:none">
      <div class="product-image">
        <div class="placeholder" style="opacity:0.15;animation:pulse 1.5s infinite">&#128722;</div>
      </div>
      <div class="product-info">
        <div style="height:12px;width:60%;background:var(--bg-surface);border-radius:4px;margin-bottom:8px"></div>
        <div style="height:14px;width:90%;background:var(--bg-surface);border-radius:4px;margin-bottom:12px"></div>
        <div style="height:16px;width:40%;background:var(--bg-surface);border-radius:4px"></div>
      </div>
    </div>
  `).join('');
}

// ── Render product grid ────────────────────────────────────

async function renderProducts(filter = 'All', search = '', subcategory = null) {
  const grid = document.getElementById('productGrid');

  // Show loading skeleton on initial load (not for filter changes with existing data)
  if (!grid.children.length || grid.querySelector('[style*="pointer-events:none"]')) {
    showGridLoading();
  }

  const vertical = filter !== 'All' ? filter : null;
  let products = [];
  try {
    products = await fetchProducts(vertical, search || null);
  } catch (e) {
    console.error('Failed to fetch products:', e);
    products = [];
  }

  if (subcategory) products = products.filter(p => p.subcategory === subcategory);

  document.getElementById('productCount').textContent = `${products.length} products`;

  let title = 'All products';
  if (filter !== 'All') title = `${filter} products`;
  if (subcategory) title = `${filter} / ${subcategory}`;
  document.getElementById('sectionTitle').textContent = title;

  if (products.length === 0) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:60px 20px;color:var(--text-dim)">
        <div style="font-size:48px;margin-bottom:16px;opacity:0.3">&#128269;</div>
        <div style="font-size:14px">No products found</div>
        <div style="font-size:12px;margin-top:4px">Try a different search or filter</div>
      </div>
    `;
    return;
  }

  grid.innerHTML = products.map(p => {
    const price = typeof p.price === 'number' ? p.price.toFixed(2) : p.price;
    const rating = typeof p.avg_rating === 'number' ? p.avg_rating.toFixed(1) : (p.avg_rating || '0.0');
    const vertical = p.vertical || 'Wellness';
    const subcategory = p.subcategory || '';

    return `
    <div class="product-card" data-id="${p.id}" onclick="openProductDetail('${p.id}')">
      <span class="vertical-badge ${vertical}">${vertical}</span>
      <div class="product-image">
        ${p.image_url
          ? `<img src="${p.image_url}" alt="${p.name}" loading="lazy"
               onerror="this.parentElement.innerHTML='<div class=placeholder>&#128722;</div>'" />`
          : '<div class="placeholder">&#128722;</div>'
        }
      </div>
      <div class="product-info">
        <div class="product-subcategory">${subcategory}</div>
        <div class="product-name">${p.name}</div>
        <div class="product-meta">
          <span class="product-price">\u00a3${price}</span>
          <span class="product-rating">
            <span class="star">&#9733;</span> ${rating}
          </span>
        </div>
      </div>
    </div>
  `;
  }).join('');
}

// ── Subcategory chips ────────────────────────────────────────

async function renderSubcategories(vertical) {
  const bar = document.getElementById('subcategoryBar');
  if (!vertical || vertical === 'All') {
    bar.innerHTML = '';
    bar.classList.remove('visible');
    currentSubcategory = null;
    return;
  }

  // Try real categories API, fall back to deriving from products
  let subs = [];
  try {
    const categories = await fetchCategories();
    subs = categories
      .filter(c => c.vertical === vertical)
      .map(c => c.name)
      .sort();
  } catch (e) {
    // fallback: derive from products
  }

  if (subs.length === 0) {
    const products = await fetchProducts(vertical, null);
    subs = [...new Set(products.map(p => p.subcategory).filter(Boolean))].sort();
  }

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

// ── Product detail modal ───────────────────────────────────

async function openProductDetail(id) {
  // Show modal immediately with loading state
  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  document.getElementById('modalImage').innerHTML = '<div class="placeholder" style="font-size:80px;opacity:0.15;animation:pulse 1.5s infinite">&#128722;</div>';
  document.getElementById('modalName').textContent = 'Loading...';
  document.getElementById('modalDescription').textContent = '';
  document.getElementById('modalPrice').textContent = '';
  document.getElementById('modalRating').textContent = '';
  document.getElementById('alsoBought').innerHTML = '';
  document.getElementById('modalReviews').innerHTML = '';

  const product = await fetchProductDetail(id);
  if (!product || product.error) {
    document.getElementById('modalName').textContent = 'Product not found';
    return;
  }

  // Image
  const imgEl = document.getElementById('modalImage');
  if (product.image_url) {
    imgEl.innerHTML = `<img src="${product.image_url}" alt="${product.name}"
      style="width:100%;height:100%;object-fit:cover;border-radius:12px"
      onerror="this.parentElement.innerHTML='<div class=placeholder style=font-size:80px>&#128722;</div>'" />`;
  } else {
    imgEl.innerHTML = '<div class="placeholder" style="font-size:80px">&#128722;</div>';
  }

  // Basic info
  const vEl = document.getElementById('modalVertical');
  vEl.textContent = product.vertical || '';
  vEl.className = `modal-vertical vertical-badge ${product.vertical || ''}`;

  document.getElementById('modalName').textContent = product.name;

  // Description with extras
  let desc = product.description || `${product.subcategory || ''} product in the ${product.vertical || ''} range.`;
  if (product.brand) desc = `By ${product.brand}. ${desc}`;
  document.getElementById('modalDescription').textContent = desc;

  const price = typeof product.price === 'number' ? product.price.toFixed(2) : product.price;
  document.getElementById('modalPrice').textContent = `\u00a3${price}`;

  // Stars
  const rating = product.avg_rating || 0;
  const stars = '\u2605'.repeat(Math.round(rating)) + '\u2606'.repeat(5 - Math.round(rating));
  document.getElementById('modalRating').innerHTML =
    `<span style="color:var(--warning)">${stars}</span> ${typeof rating === 'number' ? rating.toFixed(1) : rating}`;

  // Tags (ingredients, tags, goals)
  let tagsHtml = '';
  if (product.tags && product.tags.length) {
    tagsHtml += product.tags.map(t => `<span class="subcategory-chip" style="cursor:default;font-size:10px;padding:3px 8px">${t}</span>`).join(' ');
  }
  // Show tags inline with description if any
  if (tagsHtml) {
    document.getElementById('modalDescription').innerHTML =
      desc + `<div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:4px">${tagsHtml}</div>`;
  }

  // Also bought
  const alsoBought = product.also_bought || [];
  const alsoBoughtEl = document.getElementById('alsoBought');
  if (alsoBought.length > 0) {
    alsoBoughtEl.innerHTML = alsoBought.map(ab => {
      const abPrice = typeof ab.price === 'number' ? ab.price.toFixed(2) : ab.price;
      return `
      <div class="also-bought-card" onclick="openProductDetail('${ab.id}')">
        <div class="also-bought-img">
          ${ab.image_url
            ? `<img src="${ab.image_url}" alt="${ab.name}" style="width:100%;height:100%;object-fit:cover;border-radius:6px"
                 onerror="this.parentElement.innerHTML='&#128722;'" />`
            : '&#128722;'}
        </div>
        <div class="also-bought-name">${ab.name}</div>
        <div class="also-bought-price">\u00a3${abPrice}</div>
      </div>
    `;
    }).join('');
  } else {
    alsoBoughtEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No co-purchase data yet</span>';
  }

  // Reviews
  const reviews = product.reviews || [];
  const reviewsEl = document.getElementById('modalReviews');
  if (reviews.length > 0) {
    reviewsEl.innerHTML = reviews.map(r => {
      const sentimentColor = r.sentiment === 'positive' ? 'var(--success)'
        : r.sentiment === 'negative' ? 'var(--error)' : 'var(--warning)';
      const rStars = '\u2605'.repeat(r.score) + '\u2606'.repeat(5 - r.score);
      return `
        <div class="review-card">
          <div class="review-header">
            <span style="color:var(--warning)">${rStars}</span>
            <span class="review-sentiment" style="color:${sentimentColor}">${r.sentiment || ''}</span>
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
  document.getElementById('modalOverlay').dataset.productName = product.name;
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

async function askAboutProduct() {
  const overlay = document.getElementById('modalOverlay');
  const name = overlay.dataset.productName || 'this product';

  closeModal();
  if (!chatOpen) toggleChat();
  document.getElementById('chatInput').value = `Tell me about ${name}`;
  sendMessage();
}

// ── Filter tab + search event binding ──────────────────────

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

  // Debounced search
  document.getElementById('searchInput').addEventListener('input', (e) => {
    clearTimeout(_searchDebounce);
    _searchDebounce = setTimeout(() => {
      renderProducts(currentFilter, e.target.value, currentSubcategory);
    }, 300);
  });
}
