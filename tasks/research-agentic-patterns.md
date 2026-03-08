# Research: Agentic Tool-Calling Patterns for SurrealDB Graph Exploration

## 1. Claude Code Tool Selection: How It Chains Tools Naturally

**How it works**: Claude Code uses a simple agentic loop -- read context, decide tool, observe result, repeat. Tool chaining emerges from the model's pretraining on bash workflows (glob -> read -> grep is natural because developers do this every day).

**Key insight from Anthropic's "Effective Context Engineering" blog**:
- Tools should be "self-contained, robust to error, and extremely clear with respect to their intended use"
- "If human engineers cannot definitively identify which tool applies to a situation, agents will struggle similarly"
- Use **progressive disclosure**: let agents "incrementally discover relevant context through exploration. Each interaction yields context that informs the next decision"
- Maintain **lightweight identifiers** (file paths, IDs) that let the agent dynamically load data at runtime

**What makes chaining natural**: Each tool returns breadcrumbs pointing to the next tool. `ls` returns paths you can `cat`. `find` returns `source_id` you can `graph_traverse`. The output IS the input for the next step.

**Recommendation for Taro**: Our `find` results already return `source_id` -- this is correct. But we should ensure EVERY tool output includes "next step hints" (e.g., `cat` output should mention available edge types, `graph_traverse` output should suggest deeper traversals or `cat` for details).

---

## 2. ReAct Pattern Optimizations: Preventing Tool Bias

**The core problem**: Agents default to the most "general purpose" tool. In our case, `find` handles everything, so the agent rarely uses `grep`, `graph_traverse`, or `surrealql_query`.

**Research findings**:
- **Keep toolsets small** (< 10 tools) with well-defined, non-overlapping purposes. We have 9 -- good, but some overlap (find vs grep, ls vs cat vs tree).
- **Tool descriptions should include "when NOT to use"**: "Use find for semantic/conceptual queries. For exact name matches, use grep instead."
- **Structured reasoning templates** outperform free-form chain-of-thought for tool selection. Our GATHER->ACT->VERIFY harness is already this pattern.
- **System prompt routing tables** (the decision flow in our default.md) are the right approach. Paragon's research found that while better descriptions had "negligible" effect on simple cases, they had "positive impact on complex test cases that needed multiple tools and chaining."

**Key optimization from LangGraph patterns**:
- **Dynamic tool loading**: Only expose tools relevant to the current phase. During GATHER, hide ACT tools. During ACT, expose the full set. This reduces decision paralysis.
- **ToolSelector pattern**: Instead of letting the LLM pick freely, add a routing step that narrows the candidate set.

**Recommendation for Taro**:
1. Add negative examples to tool descriptions: "Do NOT use find when the user provides an exact product name -- use grep."
2. Consider adding "trigger words" to descriptions: graph_traverse should mention "also bought", "related", "similar", "together", "alongside", "co-purchased".
3. The decision flow table in the system prompt is our strongest lever -- expand it with more specific routing rules.

---

## 3. Graph Exploration Patterns for LLMs

**Academic state of the art**:
- **Paths-over-Graph (PoG)**: Three-phase dynamic multi-hop path exploration. The LLM proposes candidate paths on a KG, evaluates them, and selects the best. Achieved 18.9% accuracy improvement over Think-on-Graph.
- **Think-on-Graph**: Treats the LLM as an agent doing beam search on a KG -- iteratively discovering and evaluating reasoning paths.
- **AGENTiGraph**: Multi-agent architecture where different agents handle intent interpretation, task management, and knowledge integration.
- **NeoConverse (Neo4j)**: Combines GraphRAG with agentic architecture, enabling multi-hop queries and graph algorithms.

**What makes graph traversal feel natural to LLMs**:
1. **Frame it as navigation, not queries**: "Follow the `also_bought` path from this product" vs "Execute a graph traversal query." The filesystem metaphor already does this.
2. **Show the graph in tool outputs**: When `cat` returns a product, list its edges: "Connected: 3 also_bought, 2 reviews, 1 goal." This creates curiosity.
3. **Worked examples in the prompt**: The #1 way to teach multi-hop is showing it done. Our prompt has Example 2 (also_bought) but needs more variety:
   - Multi-hop: "Find ingredients in products that Diego bought" (customer -> order -> product -> ingredient)
   - Cross-entity: "What goals do products in the Skincare category support?" (category <- belongs_to <- product -> supports_goal -> goal)
4. **Return "explore further" suggestions**: After a 1-hop traversal, suggest: "Try depth=2 for transitive connections, or combine with other edge types."

**Critical insight**: The overhead of graph traversal (extra tool calls) is what discourages LLMs. They optimize for fewer steps. To counter this, make graph results feel MORE valuable than flat search results -- include relationship metadata, co-purchase counts, review sentiments.

**Recommendation for Taro**:
1. `cat` output should explicitly list available edge types with counts: "Edges: also_bought (4), supports_goal (2), belongs_to (1), contains_ingredient (8)"
2. Add multi-hop worked examples to the system prompt (2-3 hop chains)
3. `graph_traverse` output should suggest next steps: "Tip: Try `cat /products/{id}` on any result, or `graph_traverse('{id}', 'contains_ingredient')` to see ingredients."
4. Consider a compound tool `explore` that does 1-hop on ALL edge types from a record simultaneously

---

## 4. Tool Description Engineering

**Best practices from 2025 research**:

1. **Name = verb + noun** that matches the user's mental model. Our bash names (ls, cat, find, grep) are excellent because of pretraining familiarity.

2. **Description structure** (most effective pattern):
   - Line 1: What the tool does (one sentence)
   - Line 2: When to use it (concrete triggers)
   - Line 3: When NOT to use it (disambiguation from similar tools)
   - Parameters: Each with type, description, and example value

3. **Trigger-word alignment**: Include the exact phrases users would say that should route to this tool:
   - `graph_traverse`: "also bought", "related products", "similar items", "what else", "people who bought", "ingredients in", "products for goal"
   - `grep`: exact names, "search for CeraVe", "find products called..."
   - `find`: conceptual queries, "best moisturizer for", "something for dry skin"

4. **Parameter examples in descriptions**: "start_id: e.g. 'product:cerave_cleanser' (from find/grep source_id)" -- this teaches the agent how to chain from previous results.

5. **Keep descriptions concise**: Tool definitions consume tokens on EVERY call. Each unnecessary line costs latency and money. Our `graph_traverse` description is well-sized; don't bloat it.

**Key finding from Paragon's evaluation**: LLM model choice mattered more than prompt engineering for simple cases. But for complex multi-tool chaining, description quality was the deciding factor.

**Recommendation for Taro**:
1. Add "When NOT to use" lines to `find` and `grep` descriptions
2. Add user-language trigger words to `graph_traverse` description
3. Ensure every tool description includes example parameter values from realistic scenarios
4. Keep the total token footprint of all 9 tool descriptions under ~2000 tokens

---

## 5. SurrealDB Graph Patterns for Agents

**Key SurrealQL patterns**:

```surql
-- Basic traversal (what we use now)
SELECT * FROM product:xyz->also_bought->?

-- Recursive traversal (SurrealDB 2.1+)
person:ceo.{..}.{ id, title, manages: ->manages->person.@ }

-- Depth-ranged traversal
person:paz.{1..3}.{ from: id, recipients: ->messaged.out }

-- Shortest path
SELECT @.{..+shortest=person:ceo}<-manages<-person AS path_to_ceo FROM person

-- Bidirectional (edges work both ways by default)
product:xyz<-also_bought<-?  -- "who also-bought leads TO this product"
```

**SurrealDB's official Knowledge Graph RAG patterns**:
1. **Concept-based retrieval**: Vector search on concepts -> traverse backward to chunks via `<-MENTIONS_CONCEPT<-chunk`. Concepts serve as explainable intermediaries.
2. **Direct chunk retrieval with document context**: Vector search on chunks directly, then enrich with graph context via traversal.

**Key SurrealDB advantage**: Edges are real tables with metadata. Our `related_to` edge has a `reason` field, `has_review` connects to reviews with `sentiment`. This metadata is what makes graph results richer than flat search.

**Recommendation for Taro**:
1. Expose recursive traversal (`{1..3}` syntax) for multi-hop in one query instead of multiple tool calls
2. Consider adding a "reverse traversal" example to the prompt: `graph_traverse("product:xyz", "also_bought", direction="in")` to find "products that lead to this one"
3. The edge metadata (reason, sentiment, weight) should be prominently displayed in graph_traverse output -- it IS already, which is good
4. For the hackathon: demonstrate SurrealDB's recursive syntax as a differentiator

---

## 6. Cross-Cutting: Encoding "Curiosity" in System Prompts

**The fundamental challenge**: LLMs are trained to be efficient (minimize tool calls). Exploration requires being deliberately "inefficient."

**Patterns that work**:

1. **Mandate minimum tool calls**: "You MUST use at least 2 different tools before answering." Forces exploration.
2. **Reward depth in examples**: Show 3-tool chains as the "gold standard" response in worked examples.
3. **"Did you check?" gates**: "Before recommending, ask yourself: Did I check related products? Did I check what else the customer bought? Did I check ingredients?"
4. **Graph-aware VERIFY phase**: Instead of just `cat` to verify, require: "Use `graph_traverse` to verify at least one relationship is relevant to the answer."
5. **Anthropic's progressive disclosure**: Design tool outputs to surface "curiosity hooks" -- metadata that implies there's more to discover: "This product has 4 co-purchase connections and supports 2 goals."

**Anti-patterns that kill exploration**:
- "Use the fewest tools possible" (our current prompt says this!) -- directly discourages graph traversal
- Overly simple examples that resolve in 1-2 tool calls
- No penalty for shallow answers

**Recommendation for Taro**:
1. REMOVE "Use the fewest tools possible" from the GATHER phase guidance
2. REPLACE with: "Use the RIGHT tools, not the fewest. A 3-tool chain that includes graph relationships produces better answers than a single search."
3. Add a "richness check" to VERIFY: "Did you explore at least one graph relationship?"
4. Ensure `cat` output includes edge counts to trigger curiosity
5. Add at least 2 multi-hop examples to the prompt (currently only Example 2 uses graph_traverse)

---

## Summary: Actionable Changes for Taro

### HIGH IMPACT (do first)
1. **Remove "fewest tools possible" language** -- replace with "use the RIGHT tools"
2. **Add edge counts to `cat` output** -- "Connected: also_bought(4), contains_ingredient(8), supports_goal(2)"
3. **Add "next step" hints to graph_traverse output** -- suggest follow-up tools
4. **Add 2-3 multi-hop worked examples** to the system prompt (chains of 3+ tools using graph_traverse)
5. **Add trigger words to graph_traverse description** -- "also bought", "related", "similar", "together", "ingredients in"

### MEDIUM IMPACT (do second)
6. **Add "when NOT to use" to find/grep descriptions** -- reduce ambiguity
7. **Add negative examples to prompt** -- show cases where flat search misses but graph finds the answer
8. **Make VERIFY phase graph-aware** -- "verify at least one relationship"
9. **Include reverse traversal examples** -- `direction="in"` use cases

### LOWER IMPACT (nice to have)
10. **Compound `explore` tool** -- 1-hop on ALL edge types simultaneously
11. **Recursive traversal support** -- use SurrealDB `{1..3}` syntax for multi-hop in single query
12. **Dynamic tool exposure per phase** -- GATHER tools only during orient, then expand

---

## Sources

- [How Claude Code Works](https://code.claude.com/docs/en/how-claude-code-works)
- [Effective Context Engineering for AI Agents - Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Agent Interfaces in 2026: Filesystem vs API vs Database - Arize](https://arize.com/blog/agent-interfaces-in-2026-filesystem-vs-api-vs-database-what-actually-works/)
- [Paths-over-Graph: KG Empowered LLM Reasoning](https://arxiv.org/abs/2410.14211)
- [AGENTiGraph: Interactive KG Platform for LLM Chatbots](https://arxiv.org/html/2410.11531v1)
- [GraphRAG and Agentic Architecture - Neo4j](https://neo4j.com/blog/developer/graphrag-and-agentic-architecture-with-neoconverse/)
- [Knowledge Graph RAG: Two Query Patterns - SurrealDB](https://surrealdb.com/blog/knowledge-graph-rag-two-query-patterns-for-smarter-ai-agents)
- [SurrealDB Graph Traversal, Recursion, and Shortest Path](https://surrealdb.com/blog/data-analysis-using-graph-traversal-recursion-and-shortest-path)
- [SurrealDB Graph Data Model](https://surrealdb.com/docs/surrealdb/models/graph)
- [SurrealDB RELATE Statement](https://surrealdb.com/docs/surrealql/statements/relate)
- [Function Calling in LLM Agents - Symflower](https://symflower.com/en/company/blog/2025/function-calling-llm-agents/)
- [Advanced Tool Calling in LLM Agents - SparkCo](https://sparkco.ai/blog/advanced-tool-calling-in-llm-agents-a-deep-dive)
- [LangChain ReAct Agent Guide](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langchain-setup-tools-agents-memory/langchain-react-agent-complete-implementation-guide-working-examples-2025)
- [From Commands to Prompts: LLM-based Semantic File System](https://arxiv.org/abs/2410.11843)
- [Advanced Tool Use - Anthropic](https://www.anthropic.com/engineering/advanced-tool-use)
