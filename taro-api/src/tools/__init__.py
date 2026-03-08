"""SurrealDB Agentic Search Harness - 13 tools for the ReAct agent.

Tools are organized by harness phase:
  GATHER: ls, cat, tree, explore_schema (orient in the data graph)
  ACT:    find, hybrid_search, semantic_search, keyword_search, grep,
          graph_traverse, surrealql_query, web_search (execute queries)
  VERIFY: get_record (ground-truth check; cat + graph_traverse also serve verification)
"""

from tools.semantic_search import semantic_search
from tools.keyword_search import keyword_search
from tools.graph_traverse import graph_traverse
from tools.hybrid_search import hybrid_search
from tools.get_record import get_record
from tools.explore_schema import explore_schema
from tools.web_search import web_search
from tools.raw_query import surrealql_query
from tools.fs_tools import ls, cat, grep, find, tree

ALL_TOOLS = [
    # GATHER phase: orient in the data graph
    ls,                 # Browse entities at a path (like bash ls)
    cat,                # Read full record details (like bash cat)
    tree,               # Recursive hierarchy view (like bash tree)
    explore_schema,     # Schema introspection (fields, indexes)
    # ACT phase: execute informed queries
    find,               # Hybrid RRF search in data graph (semantic + keyword)
    hybrid_search,      # Combined vector + BM25 on documents table
    semantic_search,    # Vector similarity for conceptual queries
    keyword_search,     # BM25 for exact terms and names
    grep,               # Keyword search within a scope (like bash grep)
    graph_traverse,     # Graph relationships (categories, related products)
    surrealql_query,    # Raw read-only SurrealQL for advanced queries
    web_search,         # Tavily fallback with caching
    # VERIFY phase: ground-truth check
    get_record,         # Direct lookup by ID to confirm details
]

__all__ = ["ALL_TOOLS"]
