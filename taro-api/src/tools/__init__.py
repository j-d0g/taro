"""SurrealDB Agentic Search Harness - 8 tools for the ReAct agent."""

from tools.semantic_search import semantic_search
from tools.keyword_search import keyword_search
from tools.graph_traverse import graph_traverse
from tools.hybrid_search import hybrid_search
from tools.get_record import get_record
from tools.explore_schema import explore_schema
from tools.web_search import web_search
from tools.raw_query import surrealql_query

ALL_TOOLS = [
    hybrid_search,      # Default: combined vector + BM25 (most powerful)
    semantic_search,    # Vector similarity for conceptual queries
    keyword_search,     # BM25 for exact terms and names
    graph_traverse,     # Graph relationships (categories, related products)
    get_record,         # Direct lookup by ID
    explore_schema,     # Schema introspection
    web_search,         # Tavily fallback with caching
    surrealql_query,    # Raw read-only SurrealQL for advanced queries
]

__all__ = ["ALL_TOOLS"]
