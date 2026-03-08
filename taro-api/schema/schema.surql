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
-- User profiles
-- ============================================================
DEFINE TABLE user SCHEMAFULL;

DEFINE FIELD name ON user TYPE string;
DEFINE FIELD email ON user TYPE option<string>;
DEFINE FIELD profile_type ON user TYPE option<string>;          -- "beauty", "fitness", "wellness", "hybrid"
DEFINE FIELD experience_level ON user TYPE option<string>;      -- "beginner", "intermediate", "advanced"
DEFINE FIELD goals ON user TYPE option<array<string>>;
DEFINE FIELD skin_type ON user TYPE option<string>;
DEFINE FIELD dietary_restrictions ON user TYPE option<array<string>>;
DEFINE FIELD preferences ON user TYPE option<object>;           -- flexible prefs object
DEFINE FIELD context ON user TYPE option<string>;               -- distilled memory from conversations
DEFINE FIELD created_at ON user TYPE datetime DEFAULT time::now();

-- ============================================================
-- Orders
-- ============================================================
DEFINE TABLE order SCHEMAFULL;

DEFINE FIELD order_date ON order TYPE option<datetime>;
DEFINE FIELD total ON order TYPE option<float>;
DEFINE FIELD currency ON order TYPE string DEFAULT "GBP";
DEFINE FIELD status ON order TYPE string DEFAULT "completed";
DEFINE FIELD created_at ON order TYPE datetime DEFAULT time::now();

-- ============================================================
-- Reviews
-- ============================================================
DEFINE TABLE review SCHEMAFULL;

DEFINE FIELD rating ON review TYPE option<int>;
DEFINE FIELD comment ON review TYPE option<string>;
DEFINE FIELD sentiment ON review TYPE option<string>;
DEFINE FIELD created_at ON review TYPE datetime DEFAULT time::now();

-- ============================================================
-- Goals
-- ============================================================
DEFINE TABLE goal SCHEMAFULL;

DEFINE FIELD name ON goal TYPE string;
DEFINE FIELD description ON goal TYPE option<string>;
DEFINE FIELD created_at ON goal TYPE datetime DEFAULT time::now();

-- ============================================================
-- Ingredients
-- ============================================================
DEFINE TABLE ingredient SCHEMAFULL;

DEFINE FIELD name ON ingredient TYPE string;
DEFINE FIELD category ON ingredient TYPE option<string>;
DEFINE FIELD description ON ingredient TYPE option<string>;
DEFINE FIELD created_at ON ingredient TYPE datetime DEFAULT time::now();

-- ============================================================
-- Product extra fields for broader dataset
-- ============================================================
DEFINE FIELD dietary_tags ON product TYPE option<array<string>>;
DEFINE FIELD rating ON product TYPE option<float>;
DEFINE FIELD review_count ON product TYPE option<int>;
DEFINE FIELD vertical ON product TYPE option<string>;
DEFINE FIELD subcategory ON product TYPE option<string>;

-- ============================================================
-- Graph edges (RELATE) - all 9 edge types
-- ============================================================
DEFINE TABLE placed_by SCHEMAFULL TYPE RELATION IN user OUT order;
DEFINE TABLE contains SCHEMAFULL TYPE RELATION IN order OUT product;
DEFINE TABLE has_review SCHEMAFULL TYPE RELATION IN order OUT review;
DEFINE TABLE belongs_to SCHEMAFULL TYPE RELATION IN product OUT category;
DEFINE TABLE child_of SCHEMAFULL TYPE RELATION IN category OUT category;
DEFINE TABLE also_bought SCHEMAFULL TYPE RELATION IN product OUT product;
DEFINE FIELD weight ON also_bought TYPE option<float>;
DEFINE TABLE supports_goal SCHEMAFULL TYPE RELATION IN product OUT goal;
DEFINE TABLE contains_ingredient SCHEMAFULL TYPE RELATION IN product OUT ingredient;
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
