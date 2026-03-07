-- SurrealDB Schema for Taro.ai Hackathon MVP
-- Run: surreal import --conn http://localhost:8000 --ns hackathon --db chatbot schema/schema.surql

-- ============================================================
-- Unified documents table (searchable content: products, FAQs, articles)
-- ============================================================
DEFINE TABLE documents SCHEMAFULL;

DEFINE FIELD doc_type ON documents TYPE string;          -- "product", "faq", "article"
DEFINE FIELD title ON documents TYPE string;
DEFINE FIELD content ON documents TYPE string;
DEFINE FIELD source_id ON documents TYPE option<string>;  -- link to source record (e.g. "product:impact_whey")
DEFINE FIELD metadata ON documents TYPE option<object>;   -- flexible metadata
DEFINE FIELD embedding ON documents TYPE option<array<float>>;
DEFINE FIELD created_at ON documents TYPE datetime DEFAULT time::now();

-- HNSW vector index for semantic search
DEFINE INDEX idx_documents_embedding ON documents FIELDS embedding
    HNSW DIMENSION 1536 DIST COSINE;

-- BM25 full-text index for keyword search
DEFINE ANALYZER doc_analyzer TOKENIZERS blank, class FILTERS lowercase, snowball(english);
DEFINE INDEX idx_documents_content ON documents FIELDS content
    SEARCH ANALYZER doc_analyzer BM25;
DEFINE INDEX idx_documents_title ON documents FIELDS title
    SEARCH ANALYZER doc_analyzer BM25;

-- Filter index
DEFINE INDEX idx_documents_doc_type ON documents FIELDS doc_type;

-- ============================================================
-- Structured product table (for graph relations + structured queries)
-- ============================================================
DEFINE TABLE product SCHEMAFULL;

DEFINE FIELD name ON product TYPE string;
DEFINE FIELD brand ON product TYPE string DEFAULT "Myprotein";
DEFINE FIELD description ON product TYPE string;
DEFINE FIELD price ON product TYPE option<float>;
DEFINE FIELD currency ON product TYPE string DEFAULT "GBP";
DEFINE FIELD category ON product TYPE option<string>;
DEFINE FIELD flavours ON product TYPE option<array<string>>;
DEFINE FIELD key_benefits ON product TYPE option<array<string>>;
DEFINE FIELD url ON product TYPE option<string>;
DEFINE FIELD created_at ON product TYPE datetime DEFAULT time::now();

-- ============================================================
-- Category hierarchy
-- ============================================================
DEFINE TABLE category SCHEMAFULL;

DEFINE FIELD name ON category TYPE string;
DEFINE FIELD description ON category TYPE option<string>;
DEFINE FIELD parent ON category TYPE option<string>;

-- ============================================================
-- Graph edges (RELATE)
-- ============================================================
DEFINE TABLE belongs_to SCHEMAFULL TYPE RELATION IN product OUT category;
DEFINE TABLE child_of SCHEMAFULL TYPE RELATION IN category OUT category;
DEFINE TABLE related_to SCHEMAFULL TYPE RELATION IN product OUT product;
DEFINE FIELD reason ON related_to TYPE option<string>;

-- ============================================================
-- Web cache (for Tavily results)
-- ============================================================
DEFINE TABLE web_cache SCHEMAFULL;

DEFINE FIELD query ON web_cache TYPE string;
DEFINE FIELD results ON web_cache TYPE array;
DEFINE FIELD cached_at ON web_cache TYPE datetime DEFAULT time::now();
DEFINE FIELD ttl_hours ON web_cache TYPE int DEFAULT 24;

DEFINE INDEX idx_web_cache_query ON web_cache FIELDS query UNIQUE;

-- ============================================================
-- Self-improvement tables (Phase 6 stretch)
-- ============================================================
DEFINE TABLE learned_pattern SCHEMAFULL;

DEFINE FIELD pattern_type ON learned_pattern TYPE string;
DEFINE FIELD query_pattern ON learned_pattern TYPE string;
DEFINE FIELD best_tool ON learned_pattern TYPE string;
DEFINE FIELD success_count ON learned_pattern TYPE int DEFAULT 0;
DEFINE FIELD created_at ON learned_pattern TYPE datetime DEFAULT time::now();

DEFINE TABLE failure_record SCHEMAFULL;

DEFINE FIELD query ON failure_record TYPE string;
DEFINE FIELD tool_used ON failure_record TYPE string;
DEFINE FIELD error ON failure_record TYPE string;
DEFINE FIELD created_at ON failure_record TYPE datetime DEFAULT time::now();
