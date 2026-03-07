/**
 * mock-data.js — Mock data matching real CSV schema + SurrealDB edges.
 * IDs are real product_ids from trimmed/products.csv (first 8 chars shown, full 32-char in DB).
 * Replace with real API calls when backend is ready.
 */

const MOCK_PRODUCTS = [
  // Fitness
  {id:"ce5b9184",name:"EXCLUSIVE Clinique Moisture Surge Hydration Skin Heroes Set",vertical:"Fitness",subcategory:"Equipment",price:32.02,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/17696069-9775316280151439.jpg",description:"Clinique Moisture Surge Hydration Skin Heroes Set with four full-sized skincare essentials."},
  {id:"4473f3e5",name:"L'Oreal Men Expert Invincible Sport 96H Roll On Anti-Perspirant Deodorant 50ml",vertical:"Fitness",subcategory:"Tech",price:19.18,avg_rating:4.0,image_url:"https://static.thcdn.com/productimg/original/12183657-1834927998090174.jpg",description:"Sport roll-on anti-perspirant enriched with Magnesia for 96-hour protection."},
  {id:"4fcb3d9a",name:"EXCLUSIVE Clinique Moisture Surge Hydration Skin Heroes Set",vertical:"Fitness",subcategory:"Equipment",price:58.59,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/17696069-9775316280151439.jpg",description:"Clinique Moisture Surge Hydration Skin Heroes Set with four full-sized skincare essentials."},
  {id:"f4f67cca",name:"Resistance Band Set (3 pack) - Blue",vertical:"Fitness",subcategory:"Equipment",price:29.90,avg_rating:4.2,image_url:"",description:"Set of 3 resistance bands with light, medium and heavy resistance levels."},
  {id:"d92239d3",name:"Resistance Band Set (3 pack) - Grey",vertical:"Fitness",subcategory:"Equipment",price:29.90,avg_rating:4.0,image_url:"",description:"Set of 3 resistance bands with light, medium and heavy resistance levels."},
  {id:"774e21c6",name:"Lifting Gloves Size L - Red",vertical:"Fitness",subcategory:"Equipment",price:44.47,avg_rating:4.2,image_url:"",description:"Padded lifting gloves with wrist support for heavy training sessions."},
  // Beauty
  {id:"f9471562",name:"Shark SilkiPro Straight Hair Straightener + Dryer in One Tool",vertical:"Beauty",subcategory:"Tools",price:6.23,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/17726736-3765312733647679.jpg",description:"2-in-1 straightener and dryer with HeatSense Ceramic Plates and rapid-dry technology."},
  {id:"3c883b9d",name:"ESPA Bergamot and Jasmine Bath and Shower Gel 250ml",vertical:"Beauty",subcategory:"Bath & Body",price:48.96,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/12226515-1005188546067853.jpg",description:"Bath and shower gel with pure essential oils of bergamot and jasmine. Soap-free formula."},
  {id:"94634469",name:"Konjac Sponge Natural - Cream",vertical:"Beauty",subcategory:"Bath & Body",price:12.80,avg_rating:4.4,image_url:"",description:"100% natural konjac fibre sponge for gentle daily cleansing."},
  {id:"518ef5de",name:"Silk Pillowcase - Stone",vertical:"Beauty",subcategory:"Bath & Body",price:45.54,avg_rating:4.0,image_url:"",description:"Premium Silk Pillowcase - Stone. Part of our Bath & Body collection."},
  {id:"4b967866",name:"Stylpro Heated LED Electric Gua Sha",vertical:"Beauty",subcategory:"Tools",price:38.50,avg_rating:4.3,image_url:"https://static.thcdn.com/productimg/original/16718539-6375309095782284.jpg",description:"Heated facial massage tool with LED therapy for skin rejuvenation."},
  {id:"ad0a798e",name:"ESPA Bergamot and Jasmine Bath and Shower Gel 250ml",vertical:"Beauty",subcategory:"Bath & Body",price:22.50,avg_rating:4.6,image_url:"https://static.thcdn.com/productimg/original/12226515-1005188546067853.jpg",description:"Aromatic shower gel with bergamot, jasmine and patchouli essential oils."},
  // Wellness
  {id:"8d777214",name:"The INKEY List Starter Retinol Serum 30ml",vertical:"Wellness",subcategory:"Home Wellness",price:19.90,avg_rating:4.5,image_url:"https://static.thcdn.com/productimg/original/14242474-2834942685327564.jpg",description:"Beginner-friendly retinol serum with 0.05% retinol for smoother skin."},
  {id:"728cfef9",name:"The Ordinary The Skin Support Set",vertical:"Wellness",subcategory:"Home Wellness",price:13.80,avg_rating:4.5,image_url:"https://static.thcdn.com/productimg/original/15061739-2215091651791714.jpg",description:"Starter set with cleanser, hyaluronic acid and moisturiser."},
  {id:"3fcd8dfe",name:"Bobbi Brown Vitamin Enriched Face Base 50ml",vertical:"Wellness",subcategory:"Family Health",price:19.84,avg_rating:4.0,image_url:"https://static.thcdn.com/productimg/original/11512195-1075217807350538.jpg",description:"Bestselling hybrid primer and moisturiser enriched with hyaluronic acid, shea butter."},
  {id:"b8960327",name:"Posture Corrector Adjustable - Natural Wood",vertical:"Wellness",subcategory:"Home Wellness",price:35.00,avg_rating:3.8,image_url:"",description:"Adjustable posture corrector made from sustainable natural wood."},
  {id:"cef67bcf",name:"Kids Multivitamin Gummies 60 - Berry",vertical:"Wellness",subcategory:"Family Health",price:24.46,avg_rating:1.0,image_url:"",description:"Natural Kids Multivitamin Gummies 60 - Berry. From our Family Health range."},
  {id:"cf55509e",name:"Gratitude Journal Hardcover - Lavender",vertical:"Wellness",subcategory:"Mindfulness",price:21.32,avg_rating:5.0,image_url:"",description:"Natural Gratitude Journal Hardcover - Lavender. From our Mindfulness range."},
];

// Mock also_bought edges (product -also_bought-> product, derived from co-purchase)
// Real weights from dataset: 4fcb3d9a<->f4f67cca (w=3), 94634469<->ad0a798e (w=2)
const MOCK_ALSO_BOUGHT = {
  "4fcb3d9a": ["f4f67cca"],            // Clinique Set <-> Resistance Band Blue (w=3)
  "f4f67cca": ["4fcb3d9a"],            // reverse
  "94634469": ["ad0a798e", "3c883b9d"],// Konjac Sponge <-> ESPA Shower Gel (w=2)
  "ad0a798e": ["94634469"],            // reverse
  "8d777214": ["728cfef9", "b8960327"],// INKEY Retinol <-> Skin Support Set + Posture Corrector
  "728cfef9": ["8d777214", "d92239d3"],// Skin Support <-> INKEY Retinol + Resistance Band Grey
  "f9471562": ["4b967866"],            // SilkiPro <-> Gua Sha
  "4b967866": ["f9471562"],            // reverse
};

// Mock reviews keyed by order_id (schema: order -has_review-> review)
// Real review_ids and comments from trimmed/reviews.csv
const MOCK_REVIEWS = {
  "73fa93bf": [
    {review_id: "29aeeca2", score: 5, comment: "Amazing product, exceeded my expectations.", sentiment: "positive"},
  ],
  "5ff96c15": [
    {review_id: "f7c4243c", score: 5, comment: "Absolutely love this! Exactly what I needed.", sentiment: "positive"},
  ],
  "dcb36b51": [
    {review_id: "ab3056e4", score: 2, comment: "Had issues from day one. Not worth the money.", sentiment: "negative"},
  ],
  "ab1a70d5": [
    {review_id: "2e889d1c", score: 3, comment: "Decent quality but packaging could be better.", sentiment: "neutral"},
  ],
};

// Mock customer — real data from trimmed/customers.csv + orders.csv
// Schema: customer -placed-> order -contains-> product
const MOCK_CUSTOMER = {
  id: "dfa8a1b5",  // dfa8a1b565b79938d84942f83d88a2f7
  name: "Diego Carvalho",
  city: "forquilhinha",
  state: "SC",
  orders: [
    {order_id: "73fa93bf", price: 104.65, products: ["8d777214", "b8960327", "d92239d3", "728cfef9"]},
  ],
};

// Subcategory map per vertical (derived from products.csv vertical/subcategory columns)
const MOCK_SUBCATEGORIES = {
  "Fitness": ["Equipment", "Tech", "Nutrition", "Accessories", "Drinks"],
  "Beauty": ["Skincare", "Tools", "Bath & Body", "Fragrance", "Body Care", "Grooming"],
  "Wellness": ["Mindfulness", "Family Health", "Home Wellness", "Sleep", "Gifts", "Lifestyle"],
};

// Mock graph traversal data for visualization
// Each response maps to a graph showing which SurrealDB nodes/edges the agent traversed
const MOCK_GRAPHS = [
  // Response 1: hybrid search -> source_id -> also_bought + customer placed->contains
  {
    nodes: [
      {id: "q", label: "Query", type: "query"},
      {id: "d1", label: "doc: Clinique Set", type: "faq"},
      {id: "d2", label: "doc: Skin Support", type: "faq"},
      {id: "p1", label: "product:4fcb3d9a", type: "product"},
      {id: "p2", label: "product:f4f67cca", type: "product"},
      {id: "c1", label: "customer:dfa8a1b5", type: "customer"},
      {id: "o1", label: "order:73fa93bf", type: "order"},
    ],
    edges: [
      {from: "q", to: "d1", label: "hybrid", type: "bm25"},
      {from: "q", to: "d2", label: "hybrid", type: "vector"},
      {from: "d1", to: "p1", label: "source_id", type: "relational"},
      {from: "p1", to: "p2", label: "also_bought", type: "graph"},
      {from: "c1", to: "o1", label: "placed", type: "graph"},
      {from: "o1", to: "p1", label: "contains", type: "graph"},
    ],
  },
  // Response 2: keyword search -> order has_review + contains -> also_bought
  {
    nodes: [
      {id: "q", label: "Query", type: "query"},
      {id: "r1", label: "review:29aeeca2", type: "review"},
      {id: "p1", label: "product:f9471562", type: "product"},
      {id: "p2", label: "product:4b967866", type: "product"},
      {id: "o1", label: "order:73fa93bf", type: "order"},
      {id: "cat", label: "category:beauty__tools", type: "category"},
    ],
    edges: [
      {from: "q", to: "r1", label: "bm25", type: "bm25"},
      {from: "o1", to: "r1", label: "has_review", type: "graph"},
      {from: "o1", to: "p1", label: "contains", type: "graph"},
      {from: "p1", to: "p2", label: "also_bought", type: "graph"},
      {from: "p1", to: "cat", label: "belongs_to", type: "graph"},
    ],
  },
  // Response 3: FAQ semantic search -> learned pattern
  {
    nodes: [
      {id: "q", label: "Query", type: "query"},
      {id: "faq1", label: "doc:faq_12\nReturn Policy", type: "faq"},
      {id: "faq2", label: "doc:faq_15\nShipping FAQ", type: "faq"},
      {id: "lp", label: "learned_pattern:\nsemantic for FAQ", type: "learned"},
    ],
    edges: [
      {from: "q", to: "faq1", label: "vector", type: "vector"},
      {from: "q", to: "faq2", label: "vector", type: "vector"},
      {from: "faq1", to: "lp", label: "pattern", type: "relational"},
    ],
  },
];

// Mock chat responses that showcase SurrealDB multi-model features
const MOCK_RESPONSES = [
  {
    reply: "I found some great options for you! Based on hybrid search (vector + BM25) across our product documents and graph traversal of co-purchase patterns:\n\n1. **Clinique Moisture Surge Set** (\u00a358.59) \u2014 5-star rated, and via `also_bought` edge, customers who bought this also purchased the Resistance Band Set (weight=3)\n2. **The Ordinary Skin Support Set** (\u00a313.80) \u2014 great value starter set",
    tool_calls: [
      {name: "hybrid_search", type: "bm25", args: "documents | vector+BM25 RRF fusion | doc_type='product'"},
      {name: "graph_traverse", type: "graph", args: "product:4fcb3d9a ->also_bought-> product (weight=3)"},
      {name: "get_record", type: "relational", args: "product:728cfef9 | direct lookup by source_id"},
    ],
    learn: "hybrid_search works best for product recommendations"
  },
  {
    reply: "Looking at our Beauty range! Here's what stands out based on ratings and co-purchase patterns:\n\n1. **Shark SilkiPro Straightener** (\u00a36.23) \u2014 5-star, top rated in Tools. Via `also_bought`: frequently bought with the Gua Sha\n2. **ESPA Bergamot Shower Gel** (\u00a348.96) \u2014 5-star, co-purchased with Konjac Sponge (weight=2)\n\nReviews via `order->has_review->review` show overwhelmingly positive sentiment.",
    tool_calls: [
      {name: "keyword_search", type: "bm25", args: "documents | BM25 'beauty tools' | doc_type='product'"},
      {name: "graph_traverse", type: "graph", args: "order:73fa93bf ->has_review-> review | ->contains-> product"},
      {name: "surrealql_query", type: "relational", args: "SELECT * FROM product WHERE vertical='Beauty' ORDER BY avg_rating DESC LIMIT 5"},
    ],
    learn: null
  },
  {
    reply: "Great question! Based on semantic search over our FAQ documents (HNSW cosine similarity):\n\nYou can return any item within 30 days. Items must be unused and in original packaging. You'll get a prepaid returns label via email.\n\nI also found 3 related FAQ entries about shipping costs for returns.",
    tool_calls: [
      {name: "semantic_search", type: "vector", args: "documents | HNSW cosine | doc_type='faq' | query='return policy'"},
      {name: "get_record", type: "relational", args: "learned_pattern:policy_routing | best_tool='semantic_search'"},
    ],
    learn: "semantic_search on faq works best for policy questions"
  }
];
