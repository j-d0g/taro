/**
 * profile.js — Rich customer profile panel with graph-derived insights.
 * Data comes from /customers/{id}/profile (graph traversal) + /customers/{id}/recommendations.
 * Uses async API calls with graceful mock fallback.
 */

const DEMO_CUSTOMER_ID = 'charlotte_gong';
let profileOpen = false;

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
  document.getElementById('profileStats').innerHTML = '';
  document.getElementById('profileBio').innerHTML = '';
  document.getElementById('profileContext').innerHTML = '';
  document.getElementById('profileMemory').innerHTML = '';
  document.getElementById('profileBeauty').innerHTML = '';
  document.getElementById('profileGoals').innerHTML = '';
  document.getElementById('profileCategories').innerHTML = '';
  document.getElementById('profilePurchases').innerHTML =
    '<div class="skeleton" style="width:100%;height:60px"></div>';
  document.getElementById('profileReviewStats').innerHTML = '';
  document.getElementById('profileRecommendations').innerHTML = '';

  // Fetch enriched profile — API first, mock fallback
  const profile = await fetchCustomerProfile(DEMO_CUSTOMER_ID);
  if (!profile || profile.error) {
    document.getElementById('profileName').textContent = 'Customer not found';
    return;
  }

  const orders = profile.orders || [];
  const stats = profile.stats || {};
  const reviewStats = profile.review_stats || {};
  const reviews = profile.reviews || [];
  const goals = profile.inferred_goals || [];
  const topCategories = profile.top_categories || [];

  // ── Header ──────────────────────────────────────────
  document.getElementById('profileName').textContent = profile.name;
  const locationParts = [profile.city, profile.state].filter(Boolean);
  document.getElementById('profileLocation').textContent =
    locationParts.join(', ') + (profile.age ? ` · ${profile.age}y/o` : '');

  // ── Stats ───────────────────────────────────────────
  document.getElementById('profileStats').innerHTML = `
    <div class="profile-stat">
      <div class="profile-stat-value">${stats.unique_products || 0}</div>
      <div class="profile-stat-label">Products</div>
    </div>
    <div class="profile-stat">
      <div class="profile-stat-value">${stats.order_count || 0}</div>
      <div class="profile-stat-label">Orders</div>
    </div>
    <div class="profile-stat">
      <div class="profile-stat-value">\u00a3${(stats.total_spent || 0).toFixed(2)}</div>
      <div class="profile-stat-label">Total Spent</div>
    </div>
  `;

  // ── Bio ─────────────────────────────────────────────
  if (profile.bio) {
    document.getElementById('profileBio').innerHTML = `
      <div class="profile-bio">${profile.bio}</div>
    `;
  }

  // ── Agent Context ─────────────────────────────────
  if (profile.context) {
    document.getElementById('profileContext').innerHTML = `
      <h3 class="profile-section-title">Agent Context</h3>
      <p class="profile-section-subtitle">via <code>POST /distill</code> — evolving memory</p>
      <div class="profile-context">${escapeHtml(profile.context)}</div>`;
  }

  // ── Key Facts ────────────────────────────────────
  if (profile.memory && profile.memory.length > 0) {
    document.getElementById('profileMemory').innerHTML = `
      <h3 class="profile-section-title">Key Facts</h3>
      <p class="profile-section-subtitle">learned from conversations</p>
      <div class="profile-memory"><div class="profile-memory-list">
        ${profile.memory.map(m => `<div class="profile-memory-item">${escapeHtml(m)}</div>`).join('')}
      </div></div>`;
  }

  // ── Beauty Profile ──────────────────────────────────
  const beautyParts = [];

  // Skin & hair type tags
  const typeTags = [];
  if (profile.skin_type) typeTags.push(`<span class="beauty-tag">${profile.skin_type} skin</span>`);
  if (profile.hair_type) typeTags.push(`<span class="beauty-tag">${profile.hair_type} hair</span>`);
  if (profile.experience_level) typeTags.push(`<span class="beauty-tag">${profile.experience_level}</span>`);
  if (typeTags.length) beautyParts.push(`<div class="beauty-tags">${typeTags.join('')}</div>`);

  // Concerns
  if (profile.concerns && profile.concerns.length) {
    beautyParts.push(`
      <div class="beauty-subsection">
        <div class="beauty-subsection-label">Concerns</div>
        <div class="beauty-tags">${profile.concerns.map(c => `<span class="beauty-concern">${c}</span>`).join('')}</div>
      </div>
    `);
  }

  // Allergies
  if (profile.allergies && profile.allergies.length) {
    beautyParts.push(`
      <div class="beauty-subsection">
        <div class="beauty-subsection-label">Allergies & Sensitivities</div>
        <div class="beauty-tags">${profile.allergies.map(a => `<span class="beauty-allergy">${a}</span>`).join('')}</div>
      </div>
    `);
  }

  // Preferred brands
  if (profile.preferred_brands && profile.preferred_brands.length) {
    beautyParts.push(`
      <div class="beauty-subsection">
        <div class="beauty-subsection-label">Preferred Brands</div>
        <div class="beauty-tags">${profile.preferred_brands.map(b => `<span class="profile-brand-tag">${b}</span>`).join('')}</div>
      </div>
    `);
  }

  if (beautyParts.length) {
    document.getElementById('profileBeauty').innerHTML = `
      <h3 class="profile-section-title">Beauty Profile</h3>
      <p class="profile-section-subtitle">via <code>customer</code> rich attributes</p>
      <div class="profile-beauty-card">${beautyParts.join('')}</div>
    `;
  }

  // ── Inferred Goals ──────────────────────────────────
  if (goals.length) {
    document.getElementById('profileGoals').innerHTML = `
      <h3 class="profile-section-title">Inferred Goals</h3>
      <p class="profile-section-subtitle">via <code>product->supports_goal->goal</code> graph traversal</p>
      <div class="beauty-tags" style="margin-bottom:20px">
        ${goals.map(g => `<span class="profile-goal-tag" title="${g.description || ''}">${g.name}</span>`).join('')}
      </div>
    `;
  }

  // ── Top Categories ──────────────────────────────────
  if (topCategories.length) {
    const maxCount = Math.max(...topCategories.map(c => c.count));
    document.getElementById('profileCategories').innerHTML = `
      <h3 class="profile-section-title">Top Categories</h3>
      <p class="profile-section-subtitle">via <code>product->belongs_to->category</code> with counts</p>
      <div class="profile-categories-list">
        ${topCategories.map(c => `
          <div class="profile-cat-row">
            <span class="profile-cat-name">${c.name}</span>
            <div class="profile-cat-bar-bg">
              <div class="profile-cat-bar" style="width:${Math.round((c.count / maxCount) * 100)}%"></div>
            </div>
            <span class="profile-cat-count">${c.count}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  // ── Purchase History ────────────────────────────────
  const purchasesEl = document.getElementById('profilePurchases');
  purchasesEl.innerHTML = orders.map(order => {
    const products = order.products || [];
    return `
      <div class="profile-purchase-card">
        <div class="profile-purchase-info" style="flex:1">
          <div class="profile-purchase-name" style="font-size:11px;color:var(--text-dim)">Order ${order.id || '?'}</div>
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
                  <span class="vertical-badge-sm ${verticalClass(product.vertical)}">${product.vertical || ''}</span>
                  ${product.subcategory || ''}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
        <div class="profile-purchase-right">
          <div class="profile-purchase-price">\u00a3${(order.price || order.total || 0).toFixed(2)}</div>
          <div class="profile-purchase-count">${products.length} item${products.length !== 1 ? 's' : ''}</div>
        </div>
      </div>
    `;
  }).join('');

  // ── Review Activity ─────────────────────────────────
  if (reviewStats.count > 0 || reviews.length > 0) {
    const sentiment = reviewStats.sentiment || {};
    document.getElementById('profileReviewStats').innerHTML = `
      <h3 class="profile-section-title">Review Activity</h3>
      <p class="profile-section-subtitle">via <code>order->has_review->review</code></p>
      <div class="profile-review-summary">
        <div class="profile-review-stat">
          <span class="profile-review-stat-value">${reviewStats.count || 0}</span>
          <span class="profile-review-stat-label">Reviews</span>
        </div>
        <div class="profile-review-stat">
          <span class="profile-review-stat-value">${'&#9733;'.repeat(Math.round(reviewStats.avg_score || 0))} ${(reviewStats.avg_score || 0).toFixed(1)}</span>
          <span class="profile-review-stat-label">Avg Score</span>
        </div>
        <div class="profile-review-stat">
          <span class="profile-review-stat-value" style="color:var(--success)">${sentiment.positive || 0}</span>
          <span class="profile-review-stat-label">Positive</span>
        </div>
        <div class="profile-review-stat">
          <span class="profile-review-stat-value" style="color:var(--warning)">${sentiment.neutral || 0}</span>
          <span class="profile-review-stat-label">Neutral</span>
        </div>
      </div>
      <div class="profile-reviews-list">
        ${reviews.map(r => `
          <div class="profile-review-card">
            <div class="profile-review-card-header">
              <span class="review-stars">${'&#9733;'.repeat(r.score)}${'&#9734;'.repeat(5 - r.score)}</span>
              <span class="review-sentiment ${r.sentiment || 'neutral'}">${r.sentiment || 'neutral'}</span>
            </div>
            <p>${r.comment || ''}</p>
          </div>
        `).join('')}
      </div>
    `;
  }

  // ── Recommendations ─────────────────────────────────
  const recsEl = document.getElementById('profileRecommendations');
  try {
    const recs = await fetchCustomerRecommendations(DEMO_CUSTOMER_ID);
    if (recs && recs.length > 0) {
      recsEl.innerHTML = recs.map(product => `
        <div class="profile-rec-card" onclick="toggleProfile(); openProductDetail('${product.id}')">
          <div class="profile-rec-img">
            ${product.image_url
              ? `<img src="${product.image_url}" alt="${product.name}"
                   onerror="this.parentElement.innerHTML='&#128722;'" />`
              : '&#128722;'}
          </div>
          <div class="profile-rec-name">${product.name}</div>
          <div class="profile-rec-price">\u00a3${(product.price || 0).toFixed(2)}</div>
          <div class="profile-rec-reason">via also_bought graph</div>
        </div>
      `).join('');
    } else {
      recsEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No recommendations yet</span>';
    }
  } catch {
    recsEl.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No recommendations yet</span>';
  }
}
