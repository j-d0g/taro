-- SurrealDB Schema for Taro.ai Hackathon MVP
-- Run: surreal import --conn http://localhost:8000 --ns hackathon --db chatbot schema/schema.surql

-- ============================================================
-- Unified documents table (searchable content: products, FAQs, articles)
-- Triple-indexed: vector (HNSW) + full-text (BM25) + filter
-- ============================================================
DEFINE TABLE documents SCHEMAFULL;

DEFINE FIELD doc_type ON documents TYPE string;              -- "product", "faq", "article"
DEFINE FIELD title ON documents TYPE string;
DEFINE FIELD content ON documents TYPE string;
DEFINE FIELD source_id ON documents TYPE option<record>;     -- native record link to product/review
DEFINE FIELD metadata ON documents TYPE option<object>;      -- flexible metadata
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
-- Customer
-- ============================================================
DEFINE TABLE customer SCHEMAFULL;

DEFINE FIELD name ON customer TYPE string;
DEFINE FIELD city ON customer TYPE option<string>;
DEFINE FIELD state ON customer TYPE option<string>;

-- ============================================================
-- Product (structured data for graph + direct queries)
-- ============================================================
DEFINE TABLE product SCHEMAFULL;

DEFINE FIELD name ON product TYPE string;
DEFINE FIELD vertical ON product TYPE option<string>;
DEFINE FIELD subcategory ON product TYPE option<string>;
DEFINE FIELD price ON product TYPE option<float>;
DEFINE FIELD avg_rating ON product TYPE option<float>;
DEFINE FIELD description ON product TYPE option<string>;
DEFINE FIELD weight_g ON product TYPE option<float>;
DEFINE FIELD image_url ON product TYPE option<string>;
DEFINE FIELD created_at ON product TYPE datetime DEFAULT time::now();

-- ============================================================
-- Order
-- ============================================================
DEFINE TABLE order SCHEMAFULL;

DEFINE FIELD price ON order TYPE option<float>;
DEFINE FIELD created_at ON order TYPE datetime DEFAULT time::now();

-- ============================================================
-- Payment
-- ============================================================
DEFINE TABLE payment SCHEMAFULL;

DEFINE FIELD payment_type ON payment TYPE string;
DEFINE FIELD installments ON payment TYPE option<int>;
DEFINE FIELD value ON payment TYPE option<float>;

-- ============================================================
-- Review (with vector index for semantic search over comments)
-- ============================================================
DEFINE TABLE review SCHEMAFULL;

DEFINE FIELD score ON review TYPE int;
DEFINE FIELD comment ON review TYPE option<string>;
DEFINE FIELD sentiment ON review TYPE option<string>;
DEFINE FIELD embedding ON review TYPE option<array<float>>;

-- Vector index: "find reviews where people complained about X"
DEFINE INDEX idx_review_embedding ON review FIELDS embedding
    HNSW DIMENSION 1536 DIST COSINE;

-- ============================================================
-- Category (vertical + subcategory hierarchy)
-- ============================================================
DEFINE TABLE category SCHEMAFULL;

DEFINE FIELD name ON category TYPE string;
DEFINE FIELD level ON category TYPE string;                  -- "vertical" or "subcategory"
DEFINE FIELD description ON category TYPE option<string>;

-- ============================================================
-- Graph edges (RELATE)
-- ============================================================

-- Core transactional edges
DEFINE TABLE placed SCHEMAFULL TYPE RELATION IN customer OUT order;

DEFINE TABLE contains SCHEMAFULL TYPE RELATION IN order OUT product;

DEFINE TABLE paid_with SCHEMAFULL TYPE RELATION IN order OUT payment;

DEFINE TABLE has_review SCHEMAFULL TYPE RELATION IN order OUT review;

-- Derived shortcut: customer bought product (aggregated from orders)
DEFINE TABLE bought SCHEMAFULL TYPE RELATION IN customer OUT product;
DEFINE FIELD total_spent ON bought TYPE option<float>;
DEFINE FIELD order_count ON bought TYPE option<int>;

-- Derived co-purchase: products bought by the same customer
DEFINE TABLE also_bought SCHEMAFULL TYPE RELATION IN product OUT product;
DEFINE FIELD weight ON also_bought TYPE int DEFAULT 1;       -- number of customers who bought both
DEFINE FIELD customers ON also_bought TYPE option<array>;    -- sample customer IDs

-- Category hierarchy
DEFINE TABLE belongs_to SCHEMAFULL TYPE RELATION IN product OUT category;
DEFINE TABLE child_of SCHEMAFULL TYPE RELATION IN category OUT category;

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
-- Self-improvement tables
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
