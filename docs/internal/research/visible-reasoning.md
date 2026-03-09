# Visible Agentic Reasoning: Research Findings

## The Problem

When streaming the Taro agent's responses, the user sees:
1. Tool cards spinning (tool_start) then completing (tool_end)
2. Final text response tokens streaming in

**What's missing**: the *why*. Between tool calls, there's no visible reasoning like:
- "Found 3 moisturizers but need to verify prices..."
- "User has eczema-prone skin, filtering out products with essential oils..."
- "First result has no reviews, trying graph traversal for alternatives..."

Claude Code shows this kind of reasoning when searching through a codebase. The Taro agent doesn't.

---

## Root Cause Analysis

### 1. Function-calling models don't produce visible "thoughts"

The `create_react_agent` uses OpenAI/Anthropic/Google function-calling APIs. These models emit **structured `tool_calls` directly** — they do NOT output text reasoning before each tool call.

Classic ReAct (from the paper) generates: `Thought: ... → Action: ... → Observation: ...`
Modern function-calling generates: `[tool_call {name: "find", args: {...}}]` — no "Thought" step.

The reasoning is implicit in the tool selection and arguments, not as visible text.

### 2. The streaming code actively discards intermediate text

In `main.py:368-377`, the current streaming handler:
```python
elif kind == "on_chat_model_stream":
    chunk = data.get("chunk")
    content = getattr(chunk, "content", "")
    tool_chunks = getattr(chunk, "tool_call_chunks", [])

    # Text content = either thinking (intermediate) or final response token
    if content and not tool_chunks:
        yield _sse("token", {"content": content})
```

This means: if a chunk has BOTH text and tool_call_chunks, the text is silently dropped. In practice, function-calling models rarely mix them — but Claude with extended thinking DOES put reasoning in `additional_kwargs["reasoning_content"]`, which this code ignores entirely.

### 3. No distinction between intermediate and final model calls

The agent runs through multiple `on_chat_model_start → stream → end` cycles:
- Cycle 1: Model decides to call `find("moisturizer")` — emits tool_call, no text
- Cycle 2: Model sees find results, decides to call `cat /products/abc` — emits tool_call, no text
- Cycle 3: Model sees product details, generates final answer — emits text tokens

The backend treats ALL `on_chat_model_stream` events identically. There's no way for the frontend to know "this text is intermediate reasoning" vs "this is the final answer."

### 4. `on_chat_model_end` events are completely ignored

After each model call (before a tool call), `on_chat_model_end` fires with the full `AIMessage` including:
- `content` — any text the model wrote
- `tool_calls` — structured tool invocations
- `additional_kwargs` — may contain `reasoning_content` (Claude extended thinking)

This event is never captured in the streaming handler. It's the best place to extract intermediate reasoning.

---

## Event Flow (what actually happens)

```
User: "recommend a moisturizer for dry skin"

1. [on_chat_model_start]   → model begins processing
2. [on_chat_model_stream]  → tool_call_chunks for find("moisturizer dry skin")
                            (NO text content — just structured tool call)
3. [on_chat_model_end]     → AIMessage with tool_calls=[{name:"find", args:{...}}]
                            *** IGNORED — could extract reasoning here ***
4. [on_tool_start]         → find begins       ← user sees spinner
5. [on_tool_end]           → find returns results ← spinner completes
6. [on_chat_model_start]   → model processes results
7. [on_chat_model_stream]  → tool_call_chunks for cat("/products/abc123")
                            (again NO text — just tool call)
8. [on_chat_model_end]     → AIMessage with tool_calls=[{name:"cat", args:{...}}]
                            *** IGNORED ***
9. [on_tool_start]         → cat begins         ← user sees spinner
10. [on_tool_end]          → cat returns product ← spinner completes
11. [on_chat_model_start]  → model generates final answer
12. [on_chat_model_stream] → "Based on your dry skin..." token by token
                            (text content, no tool_call_chunks)
                            ← user sees text streaming
13. [on_chat_model_end]    → final AIMessage
```

The gap: steps 3 and 8 contain the model's decision, but we never surface it.

---

## Solutions (ranked by impact vs effort)

### Option A: Synthetic reasoning from tool context (LOW effort, HIGH impact)

Don't rely on the LLM to produce reasoning text. Instead, generate human-readable descriptions from the tool call itself:

```python
if kind == "on_tool_start":
    # Generate synthetic reasoning from tool name + args
    reasoning = _describe_tool_reasoning(name, tool_input, tool_calls_so_far)
    yield _sse("reasoning", {"content": reasoning})
```

Example `_describe_tool_reasoning`:
```python
def _describe_tool_reasoning(name, args, previous_calls):
    """Generate human-readable reasoning from tool call context."""
    if name == "find":
        query = args.get("query", "")
        doc_type = args.get("doc_type", "")
        return f"Searching for {doc_type or 'products'} matching \"{query}\"..."
    elif name == "cat":
        path = args.get("path", "")
        if previous_calls:
            return f"Verifying details at {path} to confirm recommendation..."
        return f"Reading details from {path}..."
    elif name == "graph_traverse":
        start = args.get("start_id", "")
        pattern = args.get("pattern", "")
        return f"Following {pattern} relationships from {start}..."
    elif name == "grep":
        term = args.get("term", "")
        scope = args.get("scope", "")
        return f"Searching for \"{term}\" in {scope}..."
    elif name == "surrealql_query":
        return "Running a database query for precise filtering..."
    elif name == "web_search":
        return "Nothing found in database, searching the web..."
    elif name == "ls":
        path = args.get("path", "/")
        return f"Browsing {path} to orient..."
    elif name == "tree":
        path = args.get("path", "/")
        return f"Exploring hierarchy at {path}..."
    elif name == "explore_schema":
        return "Checking database structure..."
    return f"Using {name}..."
```

**Pros**: Zero latency, always works, independent of model
**Cons**: Not actual LLM reasoning — just descriptions of what's happening

### Option B: Post-model hook for reasoning extraction (MEDIUM effort, HIGH impact)

Use `create_react_agent`'s `post_model_hook` to inject a lightweight reasoning step after each LLM call but before tool execution:

```python
async def reasoning_hook(state):
    """Extract and surface reasoning from the model's decision."""
    messages = state["messages"]
    last_msg = messages[-1]

    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        # The model decided to call tools — generate a reasoning summary
        tool_names = [tc["name"] for tc in last_msg.tool_calls]
        tool_args = [tc["args"] for tc in last_msg.tool_calls]

        # Add a synthetic reasoning message to state
        reasoning = _describe_tool_reasoning(tool_names[0], tool_args[0], [])
        # Could also ask a fast model to generate richer reasoning here

    return state

agent = create_react_agent(
    model=llm,
    tools=ALL_TOOLS,
    prompt=system_prompt,
    post_model_hook=reasoning_hook,
    checkpointer=checkpointer,
)
```

**Pros**: Runs inside the graph, has full context, can generate richer reasoning
**Cons**: Adds latency per tool call, post_model_hook is v2 only

### Option C: Tool result summaries after each tool_end (MEDIUM effort, HIGH impact)

After each tool completes, generate a brief summary of what was found and whether it's sufficient. This is the "what it found, was it enough" part.

```python
elif kind == "on_tool_end":
    output = data.get("output", "")
    summary = _summarize_tool_result(name, output)
    yield _sse("tool_summary", {"content": summary})
```

Example summaries:
- `find` returns 5 results → "Found 5 matching products. Verifying top picks..."
- `cat` returns product → "Got details: Clinique Moisture Surge, £28.00, 4.5 stars."
- `graph_traverse` returns edges → "Found 3 also-bought products."
- `grep` returns 0 → "No keyword matches. Trying semantic search instead..."

### Option D: Native reasoning models — GPT-5.4 or Claude (MEDIUM effort, HIGHEST impact)

Use models with built-in reasoning/thinking. Both GPT-5.4 and Claude support this natively
via LangChain — the reasoning summaries show the model's actual thought process.

#### GPT-5.4 (RECOMMENDED — already in our model list)

`ChatOpenAI` v1.1.10 already has native `reasoning_effort` and `use_responses_api` params.
GPT-5.4 supports reasoning effort levels: `none` (default), `low`, `medium`, `high`, `xhigh`.

```python
# In graph.py get_llm():
llm = ChatOpenAI(
    model="gpt-5.4",
    temperature=0.3,
    reasoning_effort="low",        # "low" for fast reasoning, "high" for deep
    use_responses_api=True,        # Auto-enabled when reasoning is set
)
```

Reasoning summaries appear in `response.content_blocks`:
```python
for block in response.content_blocks:
    if block["type"] == "reasoning":
        print(block["reasoning"])   # The model's actual thought process
```

In streaming, capture via `on_chat_model_end`:
```python
elif kind == "on_chat_model_end":
    message = data.get("output")
    if message:
        # GPT-5.4: reasoning in content_blocks
        if hasattr(message, "content_blocks"):
            for block in message.content_blocks:
                if isinstance(block, dict) and block.get("type") == "reasoning":
                    yield _sse("thinking", {"content": block["reasoning"]})
        # Claude: reasoning in additional_kwargs
        elif hasattr(message, "additional_kwargs"):
            reasoning = message.additional_kwargs.get("reasoning_content")
            if reasoning:
                yield _sse("thinking", {"content": reasoning})
```

**Key config**: `reasoning_effort="low"` is the sweet spot — adds ~200-500ms per call but
gives genuine 1-2 sentence reasoning summaries like:
- "The user wants hydrating products for dry skin. Searching semantically for moisturizers."
- "Found 5 products. The top result is Clinique Moisture Surge. Verifying price and reviews."

#### Claude (alternative)

```python
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    model_kwargs={"thinking": {"type": "enabled", "budget_tokens": 1024}}
)
```

Claude's reasoning appears in `additional_kwargs["reasoning_content"]`.

**Pros**: REAL reasoning from the model, most interpretable, GPT-5.4 already in model list
**Cons**: Adds latency per model call, `reasoning_effort="low"` ~200-500ms extra; org must be verified for OpenAI reasoning summaries

### Option E: Prompt-engineered visible reasoning (LOW effort, MEDIUM impact)

Add to the system prompt:
```
Before each tool call, briefly state your reasoning in 1 sentence.
Example: "The user wants moisturizers for dry skin, so I'll search semantically."
```

Some models will output a short text before the tool call. This text would appear in `on_chat_model_stream` chunks with content but no tool_call_chunks, and would be captured by the existing code.

**Pros**: Simple prompt change, no code changes
**Cons**: Unreliable — models may ignore it, adds to prompt length, only works with some models

---

## Recommended Implementation

**Phase 1 (ship now)**: Option D with GPT-5.4 `reasoning_effort="low"`
- Real model reasoning with minimal latency (~200-500ms extra per call)
- Already in our model list, `ChatOpenAI` already supports the param natively
- Changes: ~15 lines in `graph.py` + ~10 lines in `main.py` streaming handler
- Frontend: new `thinking` SSE event type rendered as italic text above tool cards

**Phase 2 (polish)**: Option A (synthetic reasoning) + Option C (tool result summaries) as fallback
- For models without reasoning support, or when `reasoning_effort="none"`
- Zero model latency, always works
- Gives: "Searching for X..." → tool spins → "Found 5 results" → next tool

**Phase 3 (multi-model)**: Claude extended thinking as alternative
- Behind model selector — user picks Claude and gets Claude-style thinking
- Different surface format (longer, more detailed reasoning blocks)

---

## Frontend Changes Needed

New SSE event types to handle:
```
event: reasoning
data: {"content": "Searching for moisturizers matching your dry skin concern..."}

event: tool_summary
data: {"content": "Found 5 products. Checking top pick details..."}
```

Frontend rendering:
- `reasoning` → italic text bubble above tool card, fades after tool completes
- `tool_summary` → small text below completed tool card, e.g. "Found 5 results"

---

## Key Insight

Claude Code's visible reasoning works because Claude Code uses a **text-based agentic loop** where the model writes prose reasoning before each action. LangGraph's `create_react_agent` uses **structured function calling** where the model emits tool calls directly without visible text.

To bridge this gap, we either:
1. **Synthesize** reasoning from tool context (fast, reliable, shallow)
2. **Enable extended thinking** to get real reasoning tokens (slow, rich, model-dependent)
3. **Force the model** to output text before tool calls via prompting (unreliable)

The optimal solution is a hybrid: synthetic reasoning for speed + extended thinking behind a toggle for depth.
