# Taro Testing Guide — Step by Step

Run these from the repo root or from `taro-api` as noted. Ensure SurrealDB and (where required) the API are running.

---

## Prerequisites (once per session)

1. **Start SurrealDB** (if not already running):
   ```bash
   cd taro-api && surreal start --user root --pass root memory
   ```
   Or: `make surrealdb` from repo root (runs the same).

2. **Set API key** (for any test that calls the LLM):
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```
   Or have it in `taro-api/config/.env` and source that before commands.

3. **Optional: activate venv** (if you use one):
   ```bash
   cd taro-api && source .venv/bin/activate
   ```

---

## 1. Unit tests (no API needed)

**Goal:** Run pytest (~89 tests) without starting the API.

**Steps:**

1. From repo root:
   ```bash
   cd taro-api
   ```
2. Run tests:
   ```bash
   .venv/bin/python -m pytest tests/ -v
   ```
   (If `make verify` fails with an xcode-select error, use this command instead.)

3. Optional: run a specific test file or test name:
   ```bash
   .venv/bin/python -m pytest tests/test_fs_tools.py -v
   .venv/bin/python -m pytest tests/ -k "preferences" -v
   ```

---

## 2. Health check

**Goal:** Confirm the API is up.

**Steps:**

1. Start the API if needed (in another terminal):
   ```bash
   cd taro-api && .venv/bin/python main.py
   ```
   Or from repo root: `cd taro-api && make serve`.

2. In your working terminal:
   ```bash
   make health
   ```
   Or: `curl -s http://localhost:8002/health | python -m json.tool`

3. You should see JSON with a healthy status.

---

## 3. Smoke test (3 queries, ~1 min)

**Goal:** Quick sanity check: product search, graph traversal, schema awareness.

**Steps:**

1. Ensure API is running (see 2.1) and SurrealDB is up.
2. From repo root:
   ```bash
   make smoke
   ```
3. Watch the output; each of the 3 steps should print `Pass: True` (or equivalent).

---

## 4. Distillation test (`make test-distill`)

**Goal:** Test memory distillation: send a chat as `diego_carvalho`, then call `/distill` to extract context.

**Steps:**

1. Ensure API is running on port 8002 and SurrealDB is up.
2. From repo root:
   ```bash
   make test-distill
   ```
3. You should see:
   - **Step 1:** A reply to “I want vegan protein for muscle building” for user `diego_carvalho`.
   - **Step 2:** Output from `/distill` with `context` (extracted insights) and `updated` (whether customer record was updated).

**What it runs under the hood:**

- `POST /chat` with `message`, `user_id: diego_carvalho`, `thread_id: make-test-distill`.
- `POST /distill` with `thread_id: make-test-distill`, `user_id: diego_carvalho`.

---

## 5. Eval basic (`make eval-basic`)

**Goal:** Run the evaluation suite with basic assertions (~5 min).

**Steps:**

1. Ensure API is running (and SurrealDB).
2. From repo root:
   ```bash
   make eval-basic
   ```
3. Wait for the run to finish; check the script output for pass/fail.

---

## 6. Stress test (`make stress`)

**Goal:** Restart the API and run 43 adversarial queries (~20 min). Good for tool selection and edge cases.

**Steps:**

1. From repo root:
   ```bash
   make stress
   ```
   This will:
   - Kill any process on port 8002 and start the API in the background.
   - Run `tests/stress_test_harness.py` (43 queries).

2. If you hit OpenAI rate limits, add a delay (e.g. 2+ seconds) between LLM calls in `tests/stress_test_harness.py`, then run again.

3. Check the final summary (e.g. X/43 passed). Rate-limit failures are not counted as harness failures.

---

## 7. Manual checks

### 7.1 Conversation history

**Goal:** Confirm the agent uses prior turns in the thread.

**Steps:**

1. Open the frontend (e.g. serve `taro-web` and open in browser):
   ```bash
   cd taro-web && python3 -m http.server 8080
   ```
   Open http://localhost:8080/index.html (or the port you use).

2. Start a thread: send 2–3 messages (e.g. “What categories do you have?”, “Tell me about skincare”, “What’s good for dry skin?”).

3. Ask: “What did we discuss?” or “Summarise our conversation.”

4. Check that the reply refers to earlier topics (categories, skincare, dry skin). If it does, conversation history is being used.

---

### 7.2 Product modal

**Goal:** Confirm clicking a product in a reply shows correct details from `/products/{id}`.

**Steps:**

1. In the frontend, send a message that returns product recommendations (e.g. “Recommend a moisturiser” or “What’s in the skincare category?”).

2. Click a product name/link in the assistant’s reply.

3. A modal should open with product details (name, price, description, etc.). Confirm they match the product and that nothing is missing or wrong.

---

### 7.3 Learn counter / Learn event

**Goal:** Confirm that after a Learn event, the UI or backend shows that a pattern was stored.

**Steps:**

1. Trigger a Learn event (e.g. complete a flow that creates a “learned” pattern — see your prompts or docs for how learning is triggered).

2. Check either:
   - **Backend:** Query or list learned patterns (e.g. `ls /system/patterns` or your admin endpoint), or
   - **UI:** Any “Learn” or “Patterns” indicator that increments or lists new patterns.

3. Confirm the new pattern appears. If the UI doesn’t show a “Learn counter” yet, this step is “confirm in backend only.”

---

### 7.4 Sanity check after preferences change

**Goal:** Quickly verify preferences (cart / not interested) are used.

**Steps:**

1. **Health:** From repo root run `make health`; ensure API is up.

2. **Smoke:** Run `make smoke`; all three checks should pass.

3. **Frontend as charlotte_gong:**
   - Open the chat UI.
   - If there’s a user selector, choose `charlotte_gong` (or set `user_id` to `charlotte_gong` in the request).
   - Ask: “What’s in my cart?” or “What have I said I’m not interested in?”

4. The reply should mention the LANEIGE product (cart) and CeraVe (not interested), or whatever is currently in the seed data for that user. That confirms preferences are wired correctly.

---

## Quick reference

| What              | Command / action                                      |
|-------------------|--------------------------------------------------------|
| Unit tests        | `cd taro-api && .venv/bin/python -m pytest tests/ -v`  |
| Health            | `make health` (API must be running)                    |
| Smoke             | `make smoke`                                           |
| Distillation      | `make test-distill`                                    |
| Eval basic        | `make eval-basic`                                      |
| Stress            | `make stress`                                          |
| Conversation      | Manual: multi-turn chat then “What did we discuss?”   |
| Product modal     | Manual: click product in reply, check modal            |
| Learn             | Manual: trigger Learn, check backend or UI            |
| Preferences check | `make health` → `make smoke` → chat as charlotte_gong  |
| Product Swipe Actions | Manual: cart badge/drawer, Keep bookmark, Remove + reason prompt |

### 7.5 Product Swipe Actions (Cart / Keep / Remove)

**Goal:** Confirm cart UI, bookmark state, and remove-with-reason flow work end-to-end.

**Steps:**

1. Open the frontend with API running and a logged-in user (e.g. `DEMO_CUSTOMER_ID` = `charlotte_gong` in profile.js).
2. **Cart:** In chat, get a product recommendation. Click the cart icon on a product card. The floating cart badge (above the chat bubble, same size) should show count ≥ 1; click the badge to open the drawer. The drawer shows each item with thumbnail, name, price, and a "View product" link (opens the product modal). Refresh the page — badge and drawer should still show the same (persisted via API).
3. **Keep:** Click the bookmark icon on a product card. The card should show a “✓ Saved” style and the button a checkmark; card stays visible.
4. **Remove:** Click the X on a product card. An optional “What didn’t you like?” prompt appears; enter text or click Skip. The card should fade out and disappear. The next agent reply should take the preference into account (e.g. avoid similar items).
5. **In-session adapt:** After adding to cart or removing a product, send another message (e.g. “What else do you recommend?”). The agent should see the preference update in conversation context and adapt (backend appends preference context when `thread_id` is sent with `POST /preferences`).
