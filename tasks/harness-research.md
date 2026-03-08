# Harness Engineering Research

## 1. OpenAI's Harness Engineering

Source: [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/), [InfoQ summary](https://www.infoq.com/news/2026/02/openai-harness-engineering-codex/), [Martin Fowler analysis](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)

### Core Definition

Harness engineering shifts human engineers from writing code to **designing environments, specifying intent, and providing structured feedback**. The agent operates within a constrained sandbox with rich verification methods.

### Key Principles

1. **Context Gathering First**: Before acting, Codex injects sandbox rules, environment context, and project guidance (32KiB scan cap). Machine-readable artifacts serve as the single source of truth.
2. **Architectural Constraints**: Dependencies must follow enforced sequences (Types -> Config -> Repo -> Service -> Runtime -> UI). Structural tests validate compliance.
3. **Verification & Feedback Loops**: Agents provide verifiable evidence through citations of terminal logs and test outputs. Every step is traceable.
4. **Sandbox Execution**: Shell/file tools execute in isolated containers. Internet disabled during task execution. Tools participate under a consistent policy model.
5. **Entropy Management**: Periodic agents identify inconsistencies and architectural violations, actively combating system decay.

### Agent Loop Pattern

1. Gather context (read docs, scan codebase, check git history)
2. Act on one feature at a time (incremental, not full implementation)
3. Verify through tests, linters, type checkers
4. Commit clean state with descriptive messages
5. Repeat

---

## 2. Claude Code's Harness Approach

Source: [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works), [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### The Core Feedback Loop

Claude Code operates in: **gather context -> take action -> verify work -> repeat**

### Harness Structure

1. **Initializer-Coding Agent Pattern**: Two distinct roles -- an initializer sets up the environment on first run, a coding agent makes incremental progress in subsequent sessions.
2. **Environment Scaffolding**: Set up progress files, git commits as checkpoints, structured JSON tracking passing/failing features.
3. **Feature-Based Decomposition**: Work on one feature at a time with clear pass/fail markers.
4. **Incremental Verification Checkpoints**: Sessions begin by reading progress, checking git history, running tests.
5. **Clean State Commits**: Leave code appropriate for merging -- no major bugs, well-documented.

### Tool Scoping

Tools make Claude Code agentic: read code, edit files, run commands, search the web. Settings scoped from org-wide policies down to personal preferences. The harness provides tools, context management, and execution environment.

---

## 3. SurrealDB Capabilities for Harness

Source: Schema at `taro-api/schema/schema.surql`, [SurrealDB features](https://surrealdb.com/features)

### Graph Traversal

```surql
-- Forward traversal
SELECT ->belongs_to->category FROM product:whey
-- Reverse traversal
SELECT <-contains<-order FROM product:whey
-- Multi-hop
SELECT ->placed->order->contains->product FROM customer:abc
-- Projected fields
SELECT ->related_to->product.{id, name, price} AS related FROM product:whey
```

### Vector Search (HNSW)

```surql
SELECT *, vector::similarity::cosine(embedding, $vec) AS score
FROM documents
WHERE embedding <|5|> $vec
ORDER BY score DESC
```

### Full-Text Search (BM25)

```surql
SELECT *, search::score(1) AS score
FROM documents
WHERE content @1@ $query
ORDER BY score DESC
```

### Graph Edges (6 types)

| Edge | From | To | Purpose |
|------|------|----|---------|
| `placed` | customer | order | Purchase history |
| `contains` | order | product | Order contents |
| `has_review` | order | review | Review linkage |
| `belongs_to` | product | category | Categorization |
| `child_of` | category | category | Hierarchy |
| `also_bought` | product | product | Co-purchase signal |

### Record Functions

- `record::id()`, `record::table()` for record introspection
- `math::mean()`, `math::sum()`, `count()` for aggregation
- `time::now()`, `string::lowercase()` for utilities
- `vector::similarity::cosine()` for similarity scoring

---

## 4. Tool-Phase Mapping

### The 3-Phase Harness Loop: GATHER -> ACT -> VERIFY

| Phase | Purpose | Tools |
|-------|---------|-------|
| **GATHER** | Build context, understand the data landscape | `ls`, `tree`, `explore_schema`, `cat` |
| **ACT** | Execute targeted queries based on gathered context | `find`, `hybrid_search`, `semantic_search`, `keyword_search`, `grep`, `graph_traverse`, `surrealql_query` |
| **VERIFY** | Ground-truth check against actual records | `get_record`, `cat`, `graph_traverse` (confirmation), `web_search` (fallback) |

### Phase Details

**GATHER Phase** -- Orient yourself in the data graph:
- `ls /` to see top-level entities (users, products, categories, goals, ingredients)
- `tree /categories` to understand the category hierarchy
- `explore_schema` to discover table fields and indexes
- `cat /products/{id}` to deeply understand a specific record

**ACT Phase** -- Execute informed queries:
- `find "vegan protein for muscle"` for conceptual hybrid search
- `hybrid_search` for general product queries
- `grep "creatine" /products` for exact keyword matching
- `graph_traverse` to follow relationships from known records
- `surrealql_query` for aggregations and complex filters

**VERIFY Phase** -- Confirm before responding:
- `get_record` on recommended product IDs to verify details
- `cat /products/{id}` to see full record with relationships
- `graph_traverse` to confirm category/relationship claims
- `web_search` only as last resort for info not in the database

---

## 5. Key Design Principles for Our Harness

1. **Graph as filesystem**: SurrealDB's graph IS the filesystem. `ls`, `cat`, `tree` make it navigable.
2. **Orient before search**: GATHER phase prevents blind queries. Understanding the data landscape improves search quality.
3. **Search surfaces, graph connects**: Vector/BM25 find entry points. Graph traversal discovers context.
4. **Verify with source records**: Never recommend without having seen the actual product record.
5. **Constrain outputs, not process**: Tell the agent WHAT to verify, not HOW to search.
6. **Make failure loud**: Tool results include scores, counts, and explicit "no results" messages.
