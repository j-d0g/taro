/**
 * products.js — Product grid rendering, filtering, search, and detail modal.
 * Uses async API calls with graceful mock fallback.
 */

let currentFilter = 'All';
let currentSubcategory = null;
let cachedProducts = null;

// ── Render product grid ────────────────────────────────

async function renderProducts(filter = 'All', search = '', subcategory = null) {
  const grid = document.getElementById('productGrid');

  // Show loading skeleton on first load
  if (!cachedProducts) {
    grid.innerHTML = Array(8).fill(`
      <div class="product-card">
        <div class="product-image"><div class="skeleton" style="width:100%;height:100%"></div></div>
        <div class="product-info">
          <div class="skeleton" style="width:60%;height:10px;margin-bottom:8px"></div>
          <div class="skeleton" style="width:90%;height:14px;margin-bottom:12px"></div>
          <div class="skeleton" style="width:40%;height:16px"></div>
        </div>
      </div>
    `).join('');
  }

  const products = await fetchProducts(filter !== 'All' ? filter : null, search || null);
  cachedProducts = products;

  let filtered = [...products];
  if (subcategory) filtered = filtered.filter(p => p.subcategory === subcategory);

  document.getElementById('productCount').textContent = `${filtered.length} products`;

  let title = 'All products';
  if (filter !== 'All') title = `${filter} products`;
  if (subcategory) title = `${filter} / ${subcategory}`;
  document.getElementById('sectionTitle').textContent = title;

  if (filtered.length === 0) {
    grid.innerHTML = '<p style="color:var(--text-dim);text-align:center;padding:40px">No products found</p>';
    return;
  }

  grid.innerHTML = filtered.map(p => `
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
        <div class="product-subcategory">${p.subcategory || ''}</div>
        <div class="product-name">${p.name}</div>
        <div class="product-meta">
          <span class="product-price">\u00a3${(p.price || 0).toFixed(2)}</span>
          <span class="product-rating">
            <span class="star">&#9733;</span> ${(p.avg_rating || 0).toFixed(1)}
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

  const subs = typeof MOCK_SUBCATEGORIES !== 'undefined' ? (MOCK_SUBCATEGORIES[vertical] || []) : [];
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

async function openProductDetail(id) {
  // Show modal immediately with loading state
  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  document.getElementById('modalName').textContent = 'Loading...';
  document.getElementById('modalDescription').textContent = '';
  document.getElementById('modalPrice').textContent = '';
  document.getElementById('modalRating').innerHTML = '';
  document.getElementById('alsoBought').innerHTML = '';
  document.getElementById('modalReviews').innerHTML = '';

  const data = await fetchProductDetail(id);
  if (!data) {
    closeModal();
    return;
  }

  // Fill modal fields
  const imgEl = document.getElementById('modalImage');
  if (data.image_url) {
    imgEl.innerHTML = `<img src="${data.image_url}" alt="${data.name}"
      onerror="this.parentElement.innerHTML='<div class=placeholder style=font-size:80px>&#128722;</div>'" />`;
  } else {
    imgEl.innerHTML = '<div class="placeholder" style="font-size:80px">&#128722;</div>';
  }

  document.getElementById('modalVertical').textContent = data.vertical || '';
  document.getElementById('modalVertical').className = `modal-vertical ${data.vertical || ''}`;
  document.getElementById('modalName').textContent = data.name;
  document.getElementById('modalDescription').textContent =
    data.description || `${data.subcategory || ''} product in the ${data.vertical || ''} range.`;
  document.getElementById('modalPrice').textContent = `\u00a3${(data.price || 0).toFixed(2)}`;

  // Stars
  const rating = data.avg_rating || 0;
  const stars = '\u2605'.repeat(Math.round(rating)) + '\u2606'.repeat(5 - Math.round(rating));
  document.getElementById('modalRating').innerHTML =
    `<span style="color:var(--warning)">${stars}</span> ${rating.toFixed(1)}`;

  // Also bought (from API or mock)
  const alsoBought = data.also_bought || [];
  const alsoBoughtEl = document.getElementById('alsoBought');
  if (alsoBought.length > 0) {
    alsoBoughtEl.innerHTML = alsoBought.map(ab => `
      <div class="also-bought-card" onclick="openProductDetail('${ab.id}')">
        <div class="also-bought-img">
          ${ab.image_url
            ? `<img src="${ab.image_url}" alt="${ab.name}" style="width:100%;height:100%;object-fit:cover;border-radius:6px"
                 onerror="this.parentElement.innerHTML='&#128722;'" />`
            : '&#128722;'}
        </div>
        <div class="also-bought-name">${ab.name}</div>
        <div class="also-bought-price">\u00a3${(ab.price || 0).toFixed(2)}</div>
      </div>
    `).join('');
  } else {
    alsoBoughtEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No co-purchase data yet</span>';
  }

  // Reviews
  const reviews = data.reviews || [];
  const reviewsEl = document.getElementById('modalReviews');
  if (reviews.length > 0) {
    reviewsEl.innerHTML = reviews.map(r => {
      const sentimentClass = r.sentiment || 'neutral';
      const reviewStars = '\u2605'.repeat(r.score || 0) + '\u2606'.repeat(5 - (r.score || 0));
      return `
        <div class="review-card">
          <div class="review-header">
            <span class="review-stars">${reviewStars}</span>
            <span class="review-sentiment ${sentimentClass}">${sentimentClass}</span>
          </div>
          <p class="review-comment">${r.comment || ''}</p>
        </div>
      `;
    }).join('');
  } else {
    reviewsEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No reviews yet</span>';
  }

  // Store current product id for chat button
  document.getElementById('modalOverlay').dataset.productId = id;
  document.getElementById('modalOverlay').dataset.productName = data.name;
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function askAboutProduct() {
  const name = document.getElementById('modalOverlay').dataset.productName;
  if (!name) return;

  closeModal();
  if (!chatOpen) toggleChat();
  document.getElementById('chatInput').value = `Tell me about ${name}`;
  sendMessage();
}

// ── Filter tab + search event binding ──────────────────

let searchDebounceTimer = null;

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
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      renderProducts(currentFilter, e.target.value, currentSubcategory);
    }, 300);
  });
}
