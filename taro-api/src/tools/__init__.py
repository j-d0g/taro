"""SurrealDB Agentic Search Harness - 9 tools organized by GATHER -> ACT -> VERIFY.

The filesystem metaphor (ls, cat, find, grep, tree) maps SurrealDB's multi-model
graph onto familiar bash patterns that LLMs already understand.

  GATHER: ls, cat, tree, explore_schema  (orient in the data graph)
  ACT:    find, grep, graph_traverse, surrealql_query, web_search  (execute queries)
  VERIFY: cat + graph_traverse double as verification tools
"""

from tools.fs_tools import ls, cat, grep, find, tree
from tools.graph_traverse import graph_traverse
from tools.explore_schema import explore_schema
from tools.web_search import web_search
from tools.raw_query import surrealql_query

ALL_TOOLS = [
    # GATHER phase: orient in the data graph
    ls,                 # Browse entities at a path (like bash ls)
    cat,                # Read full record details (like bash cat)
    tree,               # Recursive hierarchy view (like bash tree)
    explore_schema,     # Schema introspection (fields, indexes)
    # ACT phase: execute informed queries
    find,               # Hybrid RRF search: semantic + keyword (primary search)
    grep,               # BM25 keyword search within a scope (like bash grep)
    graph_traverse,     # Follow relationship edges (9 edge types)
    surrealql_query,    # Raw read-only SurrealQL for aggregations
    web_search,         # Tavily web fallback with SurrealDB caching
]

__all__ = ["ALL_TOOLS"]
