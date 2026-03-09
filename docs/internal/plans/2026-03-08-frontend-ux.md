# Frontend UX: Swipe Actions, Copilot Mode & Modal Fix

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Tinder-style product swipe actions (cart/keep/remove) to chat product cards, an expandable copilot chat mode, and clean up the debug badge display in the chat.

**Architecture:** Mostly frontend (HTML/CSS/JS) with one new backend endpoint (`POST /preferences`). Three new SurrealDB graph edges (`wants`, `interested_in`, `rejected`). CSS-only layout toggle for copilot mode. No changes to `fs_tools.py` or `graph.py` — those are being modified by another worktree.

**Tech Stack:** Vanilla JS, CSS custom properties, FastAPI, SurrealDB

**Key files to read first:**
- `CLAUDE.md` — project rules, SurrealDB 3.0 gotchas
- `taro-web/index.html` — full page structure
- `taro-web/js/chat.js` — chat rendering, product cards
- `taro-web/js/api.js` — API abstraction layer
- `taro-web/js/products.js` — product modal
- `taro-web/css/style.css` — all styles
- `taro-api/src/main.py` — backend endpoints
- `taro-api/schema/schema.surql` — current graph edge definitions

**Pre-flight:**
```bash
cd taro-api && make verify   # baseline passes
make restart                  # API running
```
Open `http://localhost:3001` in browser and interact with the current chat to understand baseline UX.

---

### Task 1: Add Preference Edge Types to Schema

**Files:**
- Modify: `taro-api/schema/schema.surql` (add 3 edge definitions after line ~163)

**Step 1: Add edge definitions**

Append after the `related_to` edge definition (line ~163) in `schema.surql`:

```sql
-- customer -wants-> product (added to cart)
DEFINE TABLE wants SCHEMAFULL TYPE RELATION IN customer OUT product;
DEFINE FIELD added_at ON wants TYPE datetime DEFAULT time::now();

-- customer -interested_in-> product (saved for later)
DEFINE TABLE interested_in SCHEMAFULL TYPE RELATION IN customer OUT product;
DEFINE FIELD added_at ON interested_in TYPE datetime DEFAULT time::now();

-- customer -rejected-> product (not interested)
DEFINE TABLE rejected SCHEMAFULL TYPE RELATION IN customer OUT product;
DEFINE FIELD reason ON rejected TYPE option<string>;
DEFINE FIELD added_at ON rejected TYPE datetime DEFAULT time::now();
```

**Step 2: Re-seed the database to apply schema**

```bash
cd taro-api && make seed
```

**Step 3: Verify edges exist**

```bash
curl -s -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What tables exist in the database?"}' | python -c "
import sys, json
d = json.load(sys.stdin)
reply = d['reply']
for edge in ['wants', 'interested_in', 'rejected']:
    print(f'{edge}: {\"yes\" if edge in reply else \"check manually\"}')"
```

**Step 4: Commit**

```bash
git add taro-api/schema/schema.surql
git commit -m "schema: add wants, interested_in, rejected edges for product preferences"
```

---

### Task 2: Create POST /preferences Backend Endpoint

**Files:**
- Modify: `taro-api/src/main.py` (add endpoint after the existing customer endpoints, around line ~590)

**Step 1: Write the failing test**

Create `taro-api/tests/test_preferences.py`:

```python
"""Test product preference endpoint."""
import pytest
import httpx

BASE = "http://localhost:8002"


@pytest.mark.asyncio
async def test_preference_cart():
    """POST /preferences with action=cart creates a wants edge."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE}/preferences", json={
            "user_id": "charlotte_gong",
            "product_id": "test_product_001",
            "action": "cart",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "cart"
        assert data["success"] is True


@pytest.mark.asyncio
async def test_preference_reject_with_reason():
    """POST /preferences with action=remove stores reason."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE}/preferences", json={
            "user_id": "charlotte_gong",
            "product_id": "test_product_001",
            "action": "remove",
            "reason": "Too expensive",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "remove"
        assert data["success"] is True


@pytest.mark.asyncio
async def test_preference_invalid_action():
    """POST /preferences with invalid action returns 422."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE}/preferences", json={
            "user_id": "charlotte_gong",
            "product_id": "test_product_001",
            "action": "invalid",
        })
        assert resp.status_code == 422 or resp.json().get("error")
```

**Step 2: Run test to verify it fails**

```bash
cd taro-api/src && python -m pytest ../tests/test_preferences.py -v
```

Expected: FAIL — endpoint doesn't exist yet.

**Step 3: Implement the endpoint**

Add to `taro-api/src/main.py`, after the customer recommendations endpoint (~line 590):

```python
# ── Preference endpoints ──────────────────────────────────


class PreferenceRequest(BaseModel):
    user_id: str
    product_id: str
    action: str  # "cart", "keep", "remove"
    reason: Optional[str] = None


@app.post("/preferences")
async def set_preference(request: PreferenceRequest):
    """Record a user's preference for a product (cart/keep/remove)."""
    edge_map = {
        "cart": "wants",
        "keep": "interested_in",
        "remove": "rejected",
    }
    edge_type = edge_map.get(request.action)
    if not edge_type:
        return {"error": f"Invalid action: {request.action}. Use cart, keep, or remove.", "success": False}

    async with get_db() as db:
        # Remove any existing preference edges for this user-product pair
        for et in edge_map.values():
            await db.query(
                f"DELETE {et} WHERE in = customer:`{request.user_id}` AND out = product:`{request.product_id}`"
            )

        # Create the new edge
        if request.action == "remove" and request.reason:
            await db.query(
                f"RELATE customer:`{request.user_id}`->{edge_type}->product:`{request.product_id}` "
                f"SET reason = $reason, added_at = time::now()",
                {"reason": request.reason},
            )
        else:
            await db.query(
                f"RELATE customer:`{request.user_id}`->{edge_type}->product:`{request.product_id}` "
                f"SET added_at = time::now()"
            )

    logger.info(f"Preference: {request.user_id} -> {request.action} -> {request.product_id}")
    return {"action": request.action, "product_id": request.product_id, "success": True}


@app.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    """Get a user's product preferences (cart, saved, rejected)."""
    async with get_db() as db:
        cart = await db.query(
            f"SELECT ->wants->product.{{id, name, price, image_url}} AS products FROM customer:`{user_id}`"
        )
        saved = await db.query(
            f"SELECT ->interested_in->product.{{id, name, price, image_url}} AS products FROM customer:`{user_id}`"
        )
        rejected = await db.query(
            f"SELECT ->rejected->product.{{id, name, price}} AS products FROM customer:`{user_id}`"
        )

        def extract(result):
            items = result[0].get("products", []) if result else []
            for item in items:
                item["id"] = _str_id(item.get("id", ""))
            return items

        return {
            "cart": extract(cart),
            "saved": extract(saved),
            "rejected": extract(rejected),
        }
```

**Step 4: Restart and run test**

```bash
cd taro-api && make restart
cd src && python -m pytest ../tests/test_preferences.py -v
```

Expected: PASS (note: test_preference_cart and test_preference_reject_with_reason need the API running with a seeded DB).

**Step 5: Run full verification**

```bash
make verify
```

**Step 6: Commit**

```bash
git add taro-api/src/main.py taro-api/tests/test_preferences.py
git commit -m "feat: add POST /preferences endpoint for cart/keep/remove product actions"
```

---

### Task 3: Add Swipe Action Buttons to Chat Product Cards

**Files:**
- Modify: `taro-web/js/chat.js` (renderChatProductCards function, lines ~54-81)
- Modify: `taro-web/js/api.js` (add sendPreference function)
- Modify: `taro-web/css/style.css` (add action button styles)

**Step 1: Add API function for preferences**

Add to `taro-web/js/api.js`, after the `sendChatMessage` function:

```javascript
async function sendPreference(productId, action, reason = null) {
  const userId = typeof DEMO_CUSTOMER_ID !== 'undefined' ? DEMO_CUSTOMER_ID : null;
  if (!userId) {
    console.warn('sendPreference: no user ID');
    return null;
  }
  try {
    const body = { user_id: userId, product_id: productId, action };
    if (reason) body.reason = reason;
    const res = await fetch(`${API_BASE}/preferences`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('sendPreference failed:', err.message);
    return null;
  }
}
```

**Step 2: Update renderChatProductCards with action buttons**

In `taro-web/js/chat.js`, replace the `renderChatProductCards` function:

```javascript
function renderChatProductCards(products) {
  if (!products || products.length === 0) return '';

  const cards = products.map(p => {
    const vc = typeof verticalClass === 'function' ? verticalClass(p.vertical) : (p.vertical || '').toLowerCase();
    const rating = p.avg_rating || 0;
    const stars = '\u2605'.repeat(Math.round(rating)) + '\u2606'.repeat(5 - Math.round(rating));
    return `
      <div class="chat-product-card" id="chat-product-${p.id}" data-product-id="${p.id}">
        <div class="chat-product-main" onclick="openProductDetail('${p.id}')">
          <div class="chat-product-img">
            ${p.image_url
              ? `<img src="${p.image_url}" alt="${escapeHtml(p.name)}"
                   onerror="this.parentElement.innerHTML='&#128722;'" />`
              : '&#128722;'}
          </div>
          <div class="chat-product-info">
            <div class="chat-product-name">${escapeHtml(p.name)}</div>
            <div class="chat-product-meta">
              <span class="chat-product-price">\u00a3${(p.price || 0).toFixed(2)}</span>
              <span class="chat-product-rating"><span style="color:var(--warning)">${stars}</span> ${rating.toFixed(1)}</span>
            </div>
          </div>
        </div>
        <div class="chat-product-actions">
          <button class="pref-btn pref-cart" title="Add to cart" onclick="handlePreference('${p.id}', 'cart', this)">
            &#128722;
          </button>
          <button class="pref-btn pref-keep" title="Save for later" onclick="handlePreference('${p.id}', 'keep', this)">
            &#128278;
          </button>
          <button class="pref-btn pref-remove" title="Not interested" onclick="handlePreference('${p.id}', 'remove', this)">
            &#10005;
          </button>
        </div>
      </div>
    `;
  }).join('');

  return `<div class="chat-product-cards">${cards}</div>`;
}

async function handlePreference(productId, action, btnEl) {
  const card = document.getElementById(`chat-product-${productId}`);
  if (!card) return;

  // Visual feedback immediately
  if (action === 'cart') {
    card.classList.add('pref-carted');
    btnEl.innerHTML = '&#10003;';
  } else if (action === 'keep') {
    card.classList.add('pref-saved');
    btnEl.innerHTML = '&#10003;';
  } else if (action === 'remove') {
    card.classList.add('pref-removed');
    setTimeout(() => card.style.display = 'none', 300);
  }

  // Disable all action buttons on this card
  card.querySelectorAll('.pref-btn').forEach(b => b.disabled = true);

  // Send to backend
  const result = await sendPreference(productId, action);
  if (!result || !result.success) {
    // Revert on failure
    card.className = 'chat-product-card';
    card.style.display = '';
    card.querySelectorAll('.pref-btn').forEach(b => b.disabled = false);
  }
}
```

**Step 3: Add CSS for action buttons**

Add to `taro-web/css/style.css` (after the existing `.chat-product-card` styles):

```css
/* ── Product preference actions ─────────────────────── */
.chat-product-main { cursor: pointer; display: flex; gap: 10px; align-items: center; }

.chat-product-actions {
  display: flex;
  gap: 4px;
  padding: 4px 8px;
  border-top: 1px solid var(--border);
}

.pref-btn {
  flex: 1;
  padding: 6px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  opacity: 0.6;
}

.pref-btn:hover { opacity: 1; }
.pref-btn:disabled { opacity: 0.3; cursor: default; }

.pref-cart:hover { background: rgba(74, 157, 91, 0.1); }
.pref-keep:hover { background: rgba(200, 170, 100, 0.1); }
.pref-remove:hover { background: rgba(200, 80, 80, 0.1); }

.chat-product-card.pref-carted { border-left: 3px solid var(--success); }
.chat-product-card.pref-saved { border-left: 3px solid var(--warning); }
.chat-product-card.pref-removed {
  opacity: 0;
  transform: translateX(20px);
  transition: all 0.3s ease;
}
```

**Step 4: Test in browser**

1. Open `http://localhost:3001`
2. Chat: "recommend a moisturizer"
3. Product cards should now show cart/save/remove buttons below each card
4. Click cart — card gets green left border, button changes to checkmark
5. Click remove — card fades out
6. Check browser console for API calls to `/preferences`

**Step 5: Run verification**

```bash
cd taro-api && make verify
```

**Step 6: Commit**

```bash
git add taro-web/js/chat.js taro-web/js/api.js taro-web/css/style.css
git commit -m "feat: add cart/keep/remove swipe actions to chat product cards"
```

---

### Task 4: Expandable Copilot Chat Mode

**Files:**
- Modify: `taro-web/index.html` (add expand button to chat header, ~line 118)
- Modify: `taro-web/js/chat.js` (add toggle function)
- Modify: `taro-web/css/style.css` (add copilot layout styles)

**Step 1: Add expand button to chat header**

In `taro-web/index.html`, replace the chat header close button area (line ~118):

```html
    <div class="chat-header-controls">
      <button class="chat-expand" id="chatExpand" onclick="toggleCopilot()" title="Expand to copilot mode">&#8644;</button>
      <button class="chat-close" onclick="toggleChat()">&#10005;</button>
    </div>
```

**Step 2: Add copilot toggle function**

Add to `taro-web/js/chat.js`:

```javascript
let copilotMode = localStorage.getItem('copilotMode') === 'true';

function toggleCopilot() {
  copilotMode = !copilotMode;
  document.body.classList.toggle('copilot-active', copilotMode);
  localStorage.setItem('copilotMode', copilotMode);
  document.getElementById('chatExpand').innerHTML = copilotMode ? '&#8646;' : '&#8644;';
}

// Restore on load
if (copilotMode) {
  document.body.classList.add('copilot-active');
}
```

**Step 3: Add copilot CSS**

Add to `taro-web/css/style.css`:

```css
/* ── Copilot mode ───────────────────────────────────── */
.chat-header-controls { display: flex; gap: 4px; align-items: center; }

.chat-expand {
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}
.chat-expand:hover { color: var(--text); background: var(--surface-hover); }

body.copilot-active .chat-panel.open {
  width: 50vw;
  height: 100vh;
  bottom: 0;
  right: 0;
  border-radius: 0;
  box-shadow: -4px 0 20px rgba(0,0,0,0.1);
}

body.copilot-active .main-content {
  margin-right: 50vw;
  transition: margin-right 0.3s ease;
}

body.copilot-active .filter-bar,
body.copilot-active .subcategory-bar {
  margin-right: 50vw;
  transition: margin-right 0.3s ease;
}

@media (max-width: 768px) {
  body.copilot-active .chat-panel.open {
    width: 100vw;
  }
  body.copilot-active .main-content,
  body.copilot-active .filter-bar,
  body.copilot-active .subcategory-bar {
    display: none;
  }
}
```

**Step 4: Test in browser**

1. Open chat, click the expand arrows button (&#8644;)
2. Chat should expand to 50% of viewport, grid shrinks
3. Click again to collapse back
4. Refresh page — preference should persist (localStorage)
5. Test on narrow viewport — should go full-screen

**Step 5: Run verification**

```bash
cd taro-api && make verify
```

**Step 6: Commit**

```bash
git add taro-web/index.html taro-web/js/chat.js taro-web/css/style.css
git commit -m "feat: add expandable copilot chat mode with localStorage persistence"
```

---

### Task 5: Clean Up Tool Trace Debug Badges

**Files:**
- Modify: `taro-web/js/chat.js` (tool trace rendering, lines ~117-138)
- Modify: `taro-web/js/api.js` (tool type classification, lines ~147-153)
- Modify: `taro-web/css/style.css` (tool trace styles)

**Step 1: Improve tool type classification**

In `taro-web/js/api.js`, replace the tool type classification (lines ~147-153):

```javascript
    const toolCalls = (data.tool_calls || []).map(tc => {
      let type = 'relational';
      const name = tc.name || '';
      if (name === 'find') type = 'vector';
      else if (name === 'graph_traverse') type = 'graph';
      else if (name === 'grep') type = 'bm25';
      else if (name === 'web_search') type = 'web';
      else if (name === 'surrealql_query') type = 'relational';
      else if (['ls', 'cat', 'tree', 'explore_schema'].includes(name)) type = 'relational';
      return { name: tc.name, type, args: JSON.stringify(tc.args, null, 2) };
    });
```

**Step 2: Make tool cards collapsible by default, cleaner labels**

In `taro-web/js/chat.js`, replace the tool trace rendering (lines ~117-138):

```javascript
  // Tool trace cards (collapsed by default, click to expand)
  if (toolCalls.length > 0) {
    const iconMap = {
      vector: '&#128269;',
      graph: '&#128760;',
      bm25: '&#128196;',
      relational: '&#9881;',
      web: '&#127760;',
    };
    const labelMap = {
      ls: 'Browse', cat: 'Read', find: 'Semantic search',
      grep: 'Keyword search', tree: 'Hierarchy', explore_schema: 'Schema',
      graph_traverse: 'Graph traversal', surrealql_query: 'SQL query',
      web_search: 'Web search',
    };

    const traceDiv = document.createElement('div');
    traceDiv.className = 'tool-trace';
    const summary = toolCalls.map(tc => labelMap[tc.name] || tc.name).join(', ');
    traceDiv.innerHTML = `
      <div class="tool-trace-summary" onclick="this.parentElement.classList.toggle('expanded')">
        &#9881; ${toolCalls.length} tool${toolCalls.length > 1 ? 's' : ''}: ${summary}
      </div>
      <div class="tool-trace-details">
        ${toolCalls.map(tc => `
          <div class="tool-card">
            <div class="tool-card-header">
              <span class="tool-icon ${tc.type}">${iconMap[tc.type] || '&#9881;'}</span>
              ${labelMap[tc.name] || tc.name}
              <span class="tool-label ${tc.type}">${tc.type}</span>
            </div>
            <div class="tool-card-detail"><pre>${escapeHtml(tc.args)}</pre></div>
          </div>
        `).join('')}
      </div>
    `;
    msgDiv.appendChild(traceDiv);
  }
```

**Step 3: Add collapsed/expanded CSS**

Add to `taro-web/css/style.css`:

```css
/* ── Tool trace (collapsed by default) ────────────── */
.tool-trace-summary {
  cursor: pointer;
  font-size: 11px;
  color: var(--text-dim);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: background 0.2s;
}
.tool-trace-summary:hover { background: var(--surface-hover); }

.tool-trace-details {
  display: none;
  padding: 4px 0;
}
.tool-trace.expanded .tool-trace-details { display: block; }
.tool-trace.expanded .tool-trace-summary { margin-bottom: 4px; }
```

**Step 4: Test in browser**

1. Chat: "recommend a moisturizer"
2. Tool traces should show as a compact one-liner: "3 tools: Semantic search, Read, Read"
3. Click to expand and see individual tool cards with args
4. No more raw "Graph traversal / bm25 / vector / relational" badges

**Step 5: Run verification**

```bash
cd taro-api && make verify
```

**Step 6: Commit**

```bash
git add taro-web/js/chat.js taro-web/js/api.js taro-web/css/style.css
git commit -m "feat: clean up tool trace display with collapsible cards and human-readable labels"
```

---

### Task 6: Final Verification

**Step 1: Full test suite**

```bash
cd taro-api && make verify && make smoke
```

**Step 2: Visual QA in browser**

Open `http://localhost:3001`:
- [ ] Product cards in chat have cart/keep/remove buttons
- [ ] Cart button adds green border, changes to checkmark
- [ ] Remove button fades card out
- [ ] Copilot expand/collapse toggle works
- [ ] Copilot preference persists across page refresh
- [ ] Tool traces are collapsed one-liners, expandable on click
- [ ] Mobile viewport: copilot goes full-screen

**Step 3: Update todo.md**

Mark completed items in `tasks/todo.md`.

**Step 4: Commit**

```bash
git add tasks/todo.md
git commit -m "docs: mark frontend UX tasks complete"
```
