/**
 * mock-data.js — Mock data matching real CSV schema + SurrealDB edges.
 * IDs are real product_ids from trimmed/products.csv (first 8 chars shown, full 32-char in DB).
 * Replace with real API calls when backend is ready.
 */

const MOCK_PRODUCTS = [
  // Skincare
  {id:"ce5b9184",name:"EXCLUSIVE Clinique Moisture Surge Hydration Skin Heroes Set",vertical:"Skincare",subcategory:"Moisturisers",price:32.02,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/17696069-9775316280151439.jpg",product_url:"https://www.lookfantastic.com/p/exclusive-clinique-moisture-surge-hydration-skin-heroes-set/17696069/",description:"Clinique Moisture Surge Hydration Skin Heroes Set with four full-sized skincare essentials."},
  {id:"819fc0e9",name:"Clinique Take The Day Off Cleansing Balm 125ml",vertical:"Skincare",subcategory:"Cleansers",price:31.76,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/11144730-1435173069197254.jpg",product_url:"https://www.lookfantastic.com/p/clinique-take-the-day-off-cleansing-balm-125ml/11144730/",description:"Lightweight cleansing balm that dissolves makeup, sunscreen and impurities."},
  {id:"4b967866",name:"Stylpro Heated LED Electric Gua Sha",vertical:"Skincare",subcategory:"Tools",price:38.50,avg_rating:4.3,image_url:"https://static.thcdn.com/productimg/original/16718539-6375309095782284.jpg",product_url:"https://www.lookfantastic.com/p/stylpro-heated-led-electric-gua-sha/16718539/",description:"Heated facial massage tool with LED therapy for skin rejuvenation."},
  {id:"8d777214",name:"The INKEY List Starter Retinol Serum 30ml",vertical:"Skincare",subcategory:"Serums",price:32.48,avg_rating:4.5,image_url:"https://static.thcdn.com/productimg/original/17538813-1504888839476082.jpg",product_url:"https://www.lookfantastic.com/p/the-inkey-list-starter-retinol-serum-30ml/17538813/",description:"Starter retinol serum for improving skin texture and reducing visible signs of ageing."},
  {id:"728cfef9",name:"The Ordinary The Skin Support Set (Worth \u00a313.80)",vertical:"Skincare",subcategory:"Sets",price:28.54,avg_rating:4.5,image_url:"https://static.thcdn.com/productimg/original/15061739-2215091651791714.jpg",product_url:"https://www.lookfantastic.com/p/the-ordinary-the-skin-support-set/15061739/",description:"Skincare set with Hyaluronic Acid 2% + B5 and Niacinamide 10% + Zinc 1%."},
  {id:"35bd74b6",name:"Bobbi Brown Vitamin Enriched Face Base 50ml",vertical:"Skincare",subcategory:"Moisturisers",price:31.16,avg_rating:4.0,image_url:"https://static.thcdn.com/productimg/original/11512195-1075217807350538.jpg",product_url:"https://www.lookfantastic.com/p/bobbi-brown-vitamin-enriched-face-base-50ml/11512195/",description:"Bestselling hybrid primer and moisturiser enriched with hyaluronic acid, shea butter."},
  {id:"dc82d7e8",name:"Weleda Skin Food 75ml",vertical:"Skincare",subcategory:"Moisturisers",price:23.34,avg_rating:4.2,image_url:"https://static.thcdn.com/productimg/original/10540680-1175050072684498.jpg",product_url:"https://www.lookfantastic.com/p/weleda-skin-food-75ml/10540680/",description:"Award-winning intensive moisturizing cream for dry skin with wild pansy and calendula."},
  // Haircare
  {id:"f9471562",name:"Shark SilkiPro Straight Hair Straightener + Dryer in One Tool",vertical:"Haircare",subcategory:"Hair Tools",price:6.23,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/17726736-3765312733647679.jpg",product_url:"https://www.lookfantastic.com/p/shark-silkipro-straight-hair-straightener-dryer-in-one-tool-plum-satin/17726736/",description:"2-in-1 straightener and dryer with HeatSense Ceramic Plates and rapid-dry technology."},
  // Body & Fragrance
  {id:"4473f3e5",name:"L'Oreal Men Expert Invincible Sport 96H Roll On Anti-Perspirant Deodorant 50ml",vertical:"Body & Fragrance",subcategory:"Deodorant",price:19.18,avg_rating:4.0,image_url:"https://static.thcdn.com/productimg/original/12183657-1834927998090174.jpg",product_url:"https://www.lookfantastic.com/p/l-oreal-men-expert-invincible-sport-96h-roll-on-anti-perspirant-deodorant-50ml/12183657/",description:"Sport roll-on anti-perspirant enriched with Magnesia for 96-hour protection."},
  {id:"3c883b9d",name:"ESPA Bergamot and Jasmine Bath and Shower Gel 250ml",vertical:"Body & Fragrance",subcategory:"Bath & Shower",price:48.96,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/12226515-1005188546067853.jpg",product_url:"https://www.lookfantastic.com/p/espa-bergamot-jasmine-bath-shower-gel/12226515/",description:"Bath and shower gel with pure essential oils of bergamot and jasmine. Soap-free formula."},
  {id:"ad0a798e",name:"ESPA Bergamot and Jasmine Body Lotion 200ml",vertical:"Body & Fragrance",subcategory:"Body Moisturisers",price:22.50,avg_rating:4.6,image_url:"https://static.thcdn.com/productimg/original/12226515-1005188546067853.jpg",product_url:"https://www.lookfantastic.com/p/espa-bergamot-jasmine-bath-shower-gel/12226515/",description:"Aromatic body lotion with bergamot, jasmine and patchouli essential oils."},
  {id:"1065dbb6",name:"EXCLUSIVE Clinique Moisture Surge Travel Set",vertical:"Skincare",subcategory:"Sets",price:30.77,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/17696069-9775316280151439.jpg",product_url:"https://www.lookfantastic.com/p/exclusive-clinique-moisture-surge-hydration-skin-heroes-set/17696069/",description:"Clinique Moisture Surge travel-sized essentials for hydration on-the-go."},
];

// Mock also_bought edges (product -also_bought-> product, derived from co-purchase)
// Real pairs from trimmed dataset (all w=1 after trim)
const MOCK_ALSO_BOUGHT = {
  "35bd74b6": ["dc82d7e8"],            // Bobbi Brown Face Base <-> Weleda Skin Food (w=1)
  "dc82d7e8": ["35bd74b6"],            // reverse
  "8d777214": ["728cfef9"],            // INKEY Retinol <-> Skin Support Set (w=1, Diego's order)
  "728cfef9": ["8d777214"],            // reverse
  "f9471562": ["4b967866"],            // SilkiPro <-> Gua Sha (w=1)
  "4b967866": ["f9471562"],            // reverse
};

// Mock reviews keyed by order_id (schema: order -has_review-> review)
// Real review_ids and comments from trimmed/reviews.csv
const MOCK_REVIEWS = {
  "cc2999bc": [
    {review_id: "29aeeca2", score: 5, comment: "Amazing product, exceeded my expectations.", sentiment: "positive"},
  ],
  "200f4d88": [
    {review_id: "f7c4243c", score: 3, comment: "Took ages to arrive. Product itself is fine though.", sentiment: "neutral"},
  ],
};

// Mock customer — real data from trimmed/customers.csv + orders.csv
// Schema: customer -placed-> order -contains-> product
const MOCK_CUSTOMER = {
  id: "dfa8a1b5",  // dfa8a1b565b79938d84942f83d88a2f7
  name: "Diego Carvalho",
  city: "Bristol",
  state: "",
  profile_type: "skincare newcomer",
  experience_level: "beginner",
  goals: ["clear skin", "hydration"],
  dietary_restrictions: [],
  preferred_brands: ["The Ordinary", "CeraVe", "Clinique"],
  skin_type: "oily",
  context: "University student getting into skincare for the first time. Has oily skin prone to breakouts. Looking for affordable, no-fuss products. Prefers science-backed brands. Budget-conscious but willing to invest in a good serum.",
  memory: ["University student on a budget", "Prefers fragrance-free products", "Gets breakouts on forehead and chin", "Likes simple 3-step routines"],
  orders: [
    {order_id: "cc2999bc", price: 59.80, products: ["8d777214", "728cfef9"]},
  ],
};

// Subcategory map per vertical (derived from products.csv vertical/subcategory columns)
const MOCK_SUBCATEGORIES = {
  "Skincare": ["Moisturisers", "Cleansers", "Serums", "Tools", "Sets", "Eye Care", "Sun Care"],
  "Haircare": ["Shampoo", "Conditioner", "Hair Treatments", "Styling", "Hair Tools"],
  "Body & Fragrance": ["Bath & Shower", "Body Moisturisers", "Fragrance", "Deodorant", "Hand & Nail"],
};

// Mock graph traversal data for visualization
// Each response maps to a graph showing which SurrealDB nodes/edges the agent traversed
const MOCK_GRAPHS = [
  // Response 1: hybrid search -> source_id -> also_bought + customer placed->contains
  {
    nodes: [
      {id: "q", label: "Query", type: "query"},
      {id: "d1", label: "doc: Retinol Serum", type: "faq"},
      {id: "d2", label: "doc: Skin Support", type: "faq"},
      {id: "p1", label: "product:8d777214", type: "product"},
      {id: "p2", label: "product:728cfef9", type: "product"},
      {id: "c1", label: "customer:dfa8a1b5", type: "customer"},
      {id: "o1", label: "order:cc2999bc", type: "order"},
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
      {id: "o1", label: "order:cc2999bc", type: "order"},
      {id: "cat", label: "category:haircare__tools", type: "category"},
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
    reply: "I found some great options for you! Based on hybrid search (vector + BM25) across our product documents and graph traversal of co-purchase patterns:\n\n1. **The INKEY List Starter Retinol Serum** (\u00a332.48) \u2014 via `also_bought` edge, customers who bought this also purchased The Ordinary Skin Support Set\n2. **The Ordinary Skin Support Set** (\u00a328.54) \u2014 great value starter set with Hyaluronic Acid + Niacinamide",
    tool_calls: [
      {name: "hybrid_search", type: "bm25", args: "documents | vector+BM25 RRF fusion | doc_type='product'"},
      {name: "graph_traverse", type: "graph", args: "product:8d777214 ->also_bought-> product:728cfef9"},
      {name: "get_record", type: "relational", args: "product:728cfef9 | direct lookup by source_id"},
    ],
    products: [
      {id:"8d777214",name:"The INKEY List Starter Retinol Serum 30ml",price:32.48,avg_rating:4.5,image_url:"https://static.thcdn.com/productimg/original/17538813-1504888839476082.jpg",vertical:"Skincare",subcategory:"Serums"},
      {id:"728cfef9",name:"The Ordinary The Skin Support Set (Worth \u00a313.80)",price:28.54,avg_rating:4.5,image_url:"https://static.thcdn.com/productimg/original/15061739-2215091651791714.jpg",vertical:"Skincare",subcategory:"Sets"},
    ],
    learn: "hybrid_search works best for product recommendations"
  },
  {
    reply: "Looking at our Haircare and Skincare range! Here's what stands out based on ratings and co-purchase patterns:\n\n1. **Shark SilkiPro Straightener** (\u00a36.23) \u2014 5-star, top rated in Hair Tools. Via `also_bought`: frequently bought with the Gua Sha\n2. **ESPA Bergamot Shower Gel** (\u00a348.96) \u2014 5-star in Bath & Shower\n\nReviews via `order->has_review->review` show overwhelmingly positive sentiment.",
    tool_calls: [
      {name: "keyword_search", type: "bm25", args: "documents | BM25 'haircare tools' | doc_type='product'"},
      {name: "graph_traverse", type: "graph", args: "order:cc2999bc ->has_review-> review | ->contains-> product"},
      {name: "surrealql_query", type: "relational", args: "SELECT * FROM product WHERE vertical='Haircare' ORDER BY avg_rating DESC LIMIT 5"},
    ],
    products: [
      {id:"f9471562",name:"Shark SilkiPro Straight Hair Straightener + Dryer in One Tool",price:6.23,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/17726736-3765312733647679.jpg",vertical:"Haircare",subcategory:"Hair Tools"},
      {id:"3c883b9d",name:"ESPA Bergamot and Jasmine Bath and Shower Gel 250ml",price:48.96,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/12226515-1005188546067853.jpg",vertical:"Body & Fragrance",subcategory:"Bath & Shower"},
    ],
    learn: null
  },
  {
    reply: "Great question! Based on semantic search over our FAQ documents (HNSW cosine similarity):\n\nYou can return any item within 30 days. Items must be unused and in original packaging. You'll get a prepaid returns label via email.\n\nI also found 3 related FAQ entries about shipping costs for returns.",
    tool_calls: [
      {name: "semantic_search", type: "vector", args: "documents | HNSW cosine | doc_type='faq' | query='return policy'"},
      {name: "get_record", type: "relational", args: "learned_pattern:policy_routing | best_tool='semantic_search'"},
    ],
    products: [],
    learn: "semantic_search on faq works best for policy questions"
  }
];
