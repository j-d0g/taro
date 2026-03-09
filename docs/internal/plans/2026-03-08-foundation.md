# Foundation: User Data Pipeline & Context Injection

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the broken user data pipeline so the agent can find customers, show product details from chat cards, and inject user context at chat start.

**Architecture:** Three bugs/features in dependency order: (1) verify user/customer table alignment, (2) fix chat product card modal, (3) enrich user context injection with graph traversal. All changes are in the backend (`main.py`, `fs_tools.py`) and frontend (`api.js`).

**Tech Stack:** Python/FastAPI, SurrealDB 3.0, vanilla JS frontend

**Key files to read first:**
- `CLAUDE.md` — project rules, SurrealDB 3.0 gotchas
- `tasks/lessons.md` — 12 failure patterns with prevention rules
- `tasks/harness-engineering.md` — verification approach
- `taro-api/src/main.py` — FastAPI endpoints + chat + distill
- `taro-api/src/tools/fs_tools.py` — SurrealFS tool handlers
- `taro-api/schema/schema.surql` — DB schema (table definitions)
- `taro-api/schema/seed.py` — data seeding script
- `taro-web/js/api.js` — frontend API layer
- `taro-web/js/chat.js` — chat product card rendering
- `taro-web/js/products.js` — product modal (`openProductDetail`)

**Pre-flight (do this before ANY code changes):**
```bash
cd taro-api && make verify  # must pass — baseline
make restart                # ensure API is running
make smoke                  # baseline — note pass/fail
```

---

### Task 1: Verify User/Customer Table Mismatch (may already be fixed)

**Files:**
- Read: `taro-api/src/tools/fs_tools.py:121-228` (user handlers)
- Read: `taro-api/src/main.py:122-163` (chat context injection)
- Read: `taro-api/src/main.py:270-296` (distill endpoint)
- Read: `taro-api/schema/schema.surql:33-54` (customer table def)
- Read: `taro-api/schema/seed.py` (where customers are created)

**Step 1: Check if the code already queries `customer` table**

Grep all occurrences of `FROM user` and `FROM customer` in `fs_tools.py` and `main.py`:

```bash
cd taro-api && grep -n "FROM user\|FROM customer" src/tools/fs_tools.py src/main.py
```

Expected: If ALL queries already use `FROM customer`, this bug is already fixed. If any still say `FROM user`, those need updating.

**Step 2: Test live**

```bash
# Ensure DB is seeded
make seed

# Test ls /users/ via API
curl -s -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"ls /users/"}' | python -c "import sys,json; d=json.load(sys.stdin); print(d['reply'][:500])"
```

Expected: Should list Charlotte Gong and other seeded customers. If it says "No users found", the table mismatch still exists.

**Step 3: Test user context injection**

```bash
curl -s -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What do you know about me?", "user_id":"charlotte_gong"}' | python -c "import sys,json; d=json.load(sys.stdin); print(d['reply'][:500])"
```

Expected: Reply should reference Charlotte's profile data. If generic "I don't know anything about you", context injection is broken.

**Step 4: Test distill endpoint**

```bash
curl -s -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"I love retinol products", "user_id":"charlotte_gong", "thread_id":"test-distill-1"}' > /dev/null

curl -s -X POST http://localhost:8002/distill \
  -H 'Content-Type: application/json' \
  -d '{"thread_id":"test-distill-1", "user_id":"charlotte_gong"}' | python -c "import sys,json; d=json.load(sys.stdin); print(f'Updated: {d[\"updated\"]}'); print(f'Context: {d[\"context\"][:200]}')"
```

Expected: `updated: True` with a distilled context string.

**Step 5: Fix any remaining mismatches**

If Step 1 found `FROM user` queries, update them to `FROM customer`. The schema defines `customer` (schema.surql:35), seed.py creates `customer` records, so all queries must match.

In `fs_tools.py`, check these handlers query `customer`:
- `_handle_list_users` (line ~122): `SELECT ... FROM customer`
- `_handle_show_user` (line ~137): `SELECT * FROM customer:{user_id}`
- `_handle_list_user_orders` (line ~202): `FROM customer:{user_id}`

In `main.py`, check:
- Chat context (line ~129): `SELECT * FROM customer:{request.user_id}`
- Distill (line ~273): `SELECT context FROM customer:{request.user_id}`
- Distill update (line ~294): `UPDATE customer:{request.user_id}`

**Step 6: Re-run verification**

```bash
make verify && make smoke
```

Expected: All pass.

**Step 7: Commit (only if changes were made)**

```bash
git add -A && git commit -m "fix: unify user/customer table queries across codebase"
```

If no changes needed (already fixed), document this in the task output and move on.

---

### Task 2: Fix Chat Product Card Modal Showing Empty Data

**Files:**
- Read: `taro-api/src/main.py:184-206` (product extraction from tool messages)
- Read: `taro-api/src/main.py:354-385` (GET /products/{id} endpoint)
- Read: `taro-web/js/chat.js:54-81` (renderChatProductCards)
- Read: `taro-web/js/api.js:38-58` (fetchProductDetail)
- Read: `taro-web/js/products.js:141-225` (openProductDetail)

**Step 1: Reproduce the bug**

```bash
# Get a product recommendation from the chat
curl -s -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"recommend a moisturizer under 30"}' | python -c "
import sys, json
d = json.load(sys.stdin)
products = d.get('products', [])
print(f'Products returned: {len(products)}')
for p in products[:3]:
    print(f'  id={p.get(\"id\")}, name={p.get(\"name\")}, price={p.get(\"price\")}')
    # Now test if this ID resolves via the product detail endpoint
    pid = p.get('id', '')
    print(f'  -> Will call GET /products/{pid}')
"
```

**Step 2: Test product detail lookup with the extracted ID**

```bash
# Use a product ID from Step 1 output (replace PRODUCT_ID)
curl -s http://localhost:8002/products/PRODUCT_ID | python -c "
import sys, json
d = json.load(sys.stdin)
if 'error' in d:
    print(f'BUG CONFIRMED: {d[\"error\"]}')
else:
    print(f'OK: {d.get(\"name\")} - £{d.get(\"price\")}')
"
```

If the product ID returns an error, the bug is confirmed — the ID from tool results doesn't match the product table.

**Step 3: Diagnose the ID mismatch**

The `find` tool returns results from the `documents` table (which has hashed IDs). The `id` field in tool results is a `documents` table ID, not a `product` table ID. The product table uses different IDs.

Check what IDs the products actually have:

```bash
curl -s 'http://localhost:8002/products?limit=3' | python -c "
import sys, json
products = json.load(sys.stdin)
for p in products[:3]:
    print(f'id={p[\"id\"]}, name={p[\"name\"]}')
"
```

Compare with the IDs returned from chat. If they differ, the extraction in `main.py:184-206` needs to use `source_id` (which bridges documents -> product) instead of `id`.

**Step 4: Fix product extraction in main.py**

In `taro-api/src/main.py`, around line 184-206, the product extraction parses tool message JSON. The issue is that `find`/`grep` tools return `documents` table records with a `source_id` field pointing to the actual product. Update the extraction to prefer `source_id` over `id`:

```python
# In the product extraction loop (main.py ~line 197)
# Change:
"id": _str_id(item.get("id", "")),
# To:
"id": _str_id(item.get("source_id", "") or item.get("id", "")),
```

This way, if a `source_id` exists (pointing to the product table), we use it. Otherwise fall back to `id`.

**Step 5: Fix fetchProductDetail error handling in api.js**

In `taro-web/js/api.js:38-58`, add error checking:

```javascript
async function fetchProductDetail(productId) {
  try {
    const res = await fetch(`${API_BASE}/products/${productId}`);
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    // Check for API-level error (product not found)
    if (data.error) {
      console.warn('fetchProductDetail: product not found:', data.error);
      return null;
    }
    return data;
  } catch (err) {
    // ... existing mock fallback ...
  }
}
```

**Step 6: Test the fix**

```bash
# Restart API to pick up changes
cd taro-api && make restart

# Re-run the same chat query
curl -s -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"recommend a moisturizer under 30"}' | python -c "
import sys, json, urllib.request
d = json.load(sys.stdin)
for p in d.get('products', [])[:3]:
    pid = p.get('id', '')
    resp = json.loads(urllib.request.urlopen(f'http://localhost:8002/products/{pid}').read())
    if 'error' in resp:
        print(f'STILL BROKEN: {pid} -> {resp[\"error\"]}')
    else:
        print(f'FIXED: {pid} -> {resp[\"name\"]} £{resp[\"price\"]}')
"
```

Expected: All product IDs resolve to actual products with names and prices.

**Step 7: Run verification**

```bash
make verify && make smoke
```

**Step 8: Commit**

```bash
git add taro-api/src/main.py taro-web/js/api.js
git commit -m "fix: use source_id for chat product cards, add error handling in fetchProductDetail"
```

---

### Task 3: Enrich User Context Injection with Graph Data

**Files:**
- Modify: `taro-api/src/main.py:122-163` (chat context injection)
- Test via: `make smoke` and manual curl

**Step 1: Write a test script to verify current context injection**

Create `taro-api/tests/test_context_injection.sh`:

```bash
#!/bin/bash
# Test that user context injection includes profile + purchase history
echo "Testing context injection for charlotte_gong..."
RESPONSE=$(curl -s -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What do you know about me? What have I bought before?", "user_id":"charlotte_gong"}')

REPLY=$(echo "$RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin)['reply'])")
echo "Reply: $REPLY"

# Check if the response mentions Charlotte or purchase history
echo "$REPLY" | grep -qi "charlotte" && echo "PASS: Knows user name" || echo "FAIL: Doesn't know user name"
echo "$REPLY" | grep -qiE "order|bought|purchase|product" && echo "PASS: References purchase history" || echo "FAIL: No purchase history"
```

Run: `bash taro-api/tests/test_context_injection.sh`

**Step 2: Enhance context injection in main.py**

Replace the context injection block in `main.py:122-163` with richer graph traversal:

```python
        # Inject user context if user_id provided
        user_context = ""
        if request.user_id:
            try:
                async with get_db() as db:
                    # 1. Customer profile
                    user_result = await db.query(
                        f"SELECT * FROM customer:`{request.user_id}`"
                    )
                    if user_result and isinstance(user_result[0], dict) and "name" in user_result[0]:
                        user = user_result[0]
                        name = user.get("name", request.user_id)
                        parts = [f"\n[User: {name} — customer:{request.user_id}]"]

                        # Profile fields
                        for field, label in [
                            ("bio", "Bio"), ("skin_type", "Skin type"),
                            ("hair_type", "Hair type"), ("context", "Previous context"),
                        ]:
                            if user.get(field):
                                parts.append(f"{label}: {user[field]}")
                        for field, label in [
                            ("concerns", "Concerns"), ("allergies", "Allergies"),
                            ("goals", "Goals"), ("preferences", "Preferences"),
                            ("preferred_brands", "Preferred brands"),
                            ("dietary_restrictions", "Dietary"), ("memory", "Key facts"),
                        ]:
                            if user.get(field):
                                parts.append(f"{label}: {', '.join(user[field])}")

                        # 2. Recent purchases via graph
                        order_result = await db.query(
                            f"SELECT ->placed->order->contains->product.{{name, price, subcategory}} "
                            f"AS products FROM customer:`{request.user_id}`"
                        )
                        bought = order_result[0].get("products", []) if order_result else []
                        if bought:
                            product_names = [p.get("name", "?") for p in bought[:10]]
                            parts.append(f"Recent purchases: {', '.join(product_names)}")

                        # 3. Graph entry hint
                        parts.append(
                            f"Graph entry: start from customer:{request.user_id}. "
                            f"Traverse: ->placed->order, ->placed->order->contains->product, "
                            f"->placed->order->has_review->review"
                        )

                        user_context = " | ".join(parts)
            except Exception as ue:
                logger.warning(f"Failed to load user context: {ue}")
```

**Step 3: Test the enriched context**

```bash
cd taro-api && make restart

curl -s -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What have I bought recently?", "user_id":"charlotte_gong"}' | python -c "
import sys, json
d = json.load(sys.stdin)
print(d['reply'][:600])
tools = [tc['name'] for tc in d.get('tool_calls', [])]
print(f'Tools used: {tools}')
"
```

Expected: Agent should reference Charlotte's purchase history from the injected context, potentially without needing to call `ls /users/` first (since the data is already in the system message).

**Step 4: Run full verification**

```bash
make verify && make smoke
```

**Step 5: Commit**

```bash
git add taro-api/src/main.py
git commit -m "feat: enrich user context injection with purchase history via graph traversal"
```

---

### Task 4: Final Verification & Cleanup

**Step 1: Run full test suite**

```bash
cd taro-api && make verify
```

Expected: All tests pass.

**Step 2: Run smoke test**

```bash
make smoke
```

Expected: All 3 queries pass.

**Step 3: Manual integration test**

Open `http://localhost:3001` in browser:
1. Click the chat bubble
2. Ask "recommend a moisturizer under 30"
3. Click on a product card in the chat response
4. Verify the modal shows: product name, price, rating, description, also-bought, reviews

**Step 4: Update todo.md**

Mark completed tasks with `[x]` in `tasks/todo.md`.

**Step 5: Add lessons learned**

If any unexpected issues were found during this plan, append to `tasks/lessons.md`.

**Step 6: Final commit**

```bash
git add tasks/todo.md tasks/lessons.md
git commit -m "docs: mark foundation tasks complete, add lessons learned"
```
