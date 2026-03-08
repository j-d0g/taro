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
-- User (customer / shopper profile)
-- ============================================================
DEFINE TABLE user SCHEMAFULL;

DEFINE FIELD name ON user TYPE string;
DEFINE FIELD email ON user TYPE option<string>;
DEFINE FIELD city ON user TYPE option<string>;
DEFINE FIELD age ON user TYPE option<int>;
DEFINE FIELD profile_type ON user TYPE option<string>;       -- "skincare enthusiast", "fitness beginner", etc.
DEFINE FIELD experience_level ON user TYPE option<string>;   -- "beginner", "intermediate", "advanced"
DEFINE FIELD goals ON user TYPE option<array<string>>;       -- ["clear skin", "muscle gain"]
DEFINE FIELD dietary_restrictions ON user TYPE option<array<string>>; -- ["vegan", "gluten-free"]
DEFINE FIELD preferred_brands ON user TYPE option<array<string>>;
DEFINE FIELD skin_type ON user TYPE option<string>;          -- "dry", "oily", "combination", "sensitive"
DEFINE FIELD context ON user TYPE option<string>;            -- LLM-readable summary
DEFINE FIELD memory ON user TYPE option<array<string>>;      -- key facts for personalisation

-- ============================================================
-- Customer (from CSV dataset)
-- ============================================================
DEFINE TABLE customer SCHEMAFULL;

DEFINE FIELD name ON customer TYPE option<string>;
DEFINE FIELD city ON customer TYPE option<string>;
DEFINE FIELD state ON customer TYPE option<string>;
DEFINE FIELD skin_type ON customer TYPE option<string>;
DEFINE FIELD hair_type ON customer TYPE option<string>;
DEFINE FIELD concerns ON customer TYPE option<array<string>>;
DEFINE FIELD preferences ON customer TYPE option<array<string>>;
DEFINE FIELD allergies ON customer TYPE option<array<string>>;
DEFINE FIELD age ON customer TYPE option<int>;
DEFINE FIELD bio ON customer TYPE option<string>;
DEFINE FIELD profile_type ON customer TYPE option<string>;
DEFINE FIELD experience_level ON customer TYPE option<string>;
DEFINE FIELD preferred_brands ON customer TYPE option<array<string>>;

-- ============================================================
-- Product (structured data for graph + direct queries)
-- ============================================================
DEFINE TABLE product SCHEMAFULL;

DEFINE FIELD name ON product TYPE string;
DEFINE FIELD vertical ON product TYPE option<string>;
DEFINE FIELD subcategory ON product TYPE option<string>;
DEFINE FIELD category ON product TYPE option<string>;        -- alias for subcategory (used in fs_tools)
DEFINE FIELD price ON product TYPE option<float>;
DEFINE FIELD avg_rating ON product TYPE option<float>;
DEFINE FIELD description ON product TYPE option<string>;
DEFINE FIELD brand ON product TYPE option<string>;
DEFINE FIELD ingredients ON product TYPE option<array<string>>;
DEFINE FIELD tags ON product TYPE option<array<string>>;     -- "vegan", "bestseller", "new", etc.
DEFINE FIELD dietary_tags ON product TYPE option<array<string>>; -- "vegan", "gluten-free", "organic"
DEFINE FIELD weight_g ON product TYPE option<float>;
DEFINE FIELD image_url ON product TYPE option<string>;
DEFINE FIELD product_url ON product TYPE option<string>;
DEFINE FIELD created_at ON product TYPE datetime DEFAULT time::now();

-- ============================================================
-- Order
-- ============================================================
DEFINE TABLE order SCHEMAFULL;

DEFINE FIELD total ON order TYPE option<float>;
DEFINE FIELD price ON order TYPE option<float>;
DEFINE FIELD currency ON order TYPE option<string> DEFAULT 'GBP';
DEFINE FIELD status ON order TYPE option<string>;            -- "delivered", "shipped", "processing"
DEFINE FIELD order_date ON order TYPE option<datetime>;
DEFINE FIELD created_at ON order TYPE datetime DEFAULT time::now();

-- ============================================================
-- Review (with vector index for semantic search over comments)
-- ============================================================
DEFINE TABLE review SCHEMAFULL;

DEFINE FIELD score ON review TYPE int;
DEFINE FIELD comment ON review TYPE option<string>;
DEFINE FIELD sentiment ON review TYPE option<string>;
DEFINE FIELD embedding ON review TYPE option<array<float>>;

DEFINE INDEX idx_review_embedding ON review FIELDS embedding
    HNSW DIMENSION 1536 DIST COSINE;

-- ============================================================
-- Category (3 verticals: Skincare, Haircare, Body & Fragrance; 9 subcategories)
-- ============================================================
DEFINE TABLE category SCHEMAFULL;

DEFINE FIELD name ON category TYPE string;
DEFINE FIELD level ON category TYPE string;                  -- "vertical" or "subcategory"
DEFINE FIELD description ON category TYPE option<string>;

-- ============================================================
-- Goal (fitness / wellness / beauty goals)
-- ============================================================
DEFINE TABLE goal SCHEMAFULL;

DEFINE FIELD name ON goal TYPE string;
DEFINE FIELD description ON goal TYPE option<string>;
DEFINE FIELD vertical ON goal TYPE option<string>;           -- which vertical this goal relates to

-- ============================================================
-- Ingredient (key active ingredients across products)
-- ============================================================
DEFINE TABLE ingredient SCHEMAFULL;

DEFINE FIELD name ON ingredient TYPE string;
DEFINE FIELD role ON ingredient TYPE option<string>;         -- "hydration", "anti-aging", "exfoliation"
DEFINE FIELD category ON ingredient TYPE option<string>;     -- "skincare", "nutrition", "wellness"
DEFINE FIELD description ON ingredient TYPE option<string>;
DEFINE FIELD common_in ON ingredient TYPE option<array<string>>; -- product types it appears in

-- ============================================================
-- Graph edges (9 total)
-- ============================================================

-- customer -placed-> order
DEFINE TABLE placed SCHEMAFULL TYPE RELATION IN customer OUT order;

-- order -contains-> product
DEFINE TABLE contains SCHEMAFULL TYPE RELATION IN order OUT product;

-- order -has_review-> review
DEFINE TABLE has_review SCHEMAFULL TYPE RELATION IN order OUT review;

-- product -also_bought-> product (derived: co-purchased by same user)
DEFINE TABLE also_bought SCHEMAFULL TYPE RELATION IN product OUT product;
DEFINE FIELD weight ON also_bought TYPE int DEFAULT 1;

-- product -belongs_to-> category
DEFINE TABLE belongs_to SCHEMAFULL TYPE RELATION IN product OUT category;

-- category -child_of-> category (subcategory -> vertical)
DEFINE TABLE child_of SCHEMAFULL TYPE RELATION IN category OUT category;

-- product -supports_goal-> goal
DEFINE TABLE supports_goal SCHEMAFULL TYPE RELATION IN product OUT goal;

-- product -contains_ingredient-> ingredient
DEFINE TABLE contains_ingredient SCHEMAFULL TYPE RELATION IN product OUT ingredient;
DEFINE FIELD concentration ON contains_ingredient TYPE option<string>; -- "active", "trace"

-- product -related_to-> product (cross-reference: similar/complementary)
DEFINE TABLE related_to SCHEMAFULL TYPE RELATION IN product OUT product;
DEFINE FIELD reason ON related_to TYPE option<string>;       -- "same category", "complementary", "alternative"

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
