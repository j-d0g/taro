/**
 * mock-data.js — Mock product data (from real CSVs) and mock chat responses.
 * Replace with real API calls when backend is ready.
 */

const MOCK_PRODUCTS = [
  {id:"ce5b9184",name:"Clinique Moisture Surge Hydration Set",vertical:"Fitness",subcategory:"Equipment",price:32.02,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/17696069-9775316280151439.jpg",description:"Intensive hydration set with 72-hour moisture surge technology."},
  {id:"4473f3e5",name:"L'Oreal Men Expert Sport Roll-On Deodorant 50ml",vertical:"Fitness",subcategory:"Tech",price:19.18,avg_rating:4.0,image_url:"https://static.thcdn.com/productimg/original/12183657-1834927998090174.jpg",description:"48-hour anti-perspirant designed for active lifestyles."},
  {id:"a1b2c3d4",name:"benefit Hoola Matte Bronzer Mini 2.5g",vertical:"Fitness",subcategory:"Tech",price:15.50,avg_rating:4.5,image_url:"https://static.thcdn.com/productimg/original/13713961-1174915139428614.jpg",description:"Travel-size matte bronzer for a natural sun-kissed glow."},
  {id:"e5f6a7b8",name:"Clinique Take The Day Off Cleansing Balm 125ml",vertical:"Fitness",subcategory:"Nutrition",price:24.99,avg_rating:4.8,image_url:"https://static.thcdn.com/productimg/original/11144730-1515055854992990.jpg",description:"Lightweight balm dissolves tenacious makeup and sunscreen."},
  {id:"f6574524",name:"Wrist Wraps Pair - Teal",vertical:"Fitness",subcategory:"Accessories",price:52.24,avg_rating:1.0,image_url:"",description:"Heavy-duty wrist wraps for powerlifting and Olympic lifts."},
  {id:"5f504b3a",name:"Knee Sleeves Pair - Red",vertical:"Fitness",subcategory:"Accessories",price:44.47,avg_rating:4.2,image_url:"",description:"7mm neoprene knee sleeves for squat support and warmth."},
  {id:"f9471562",name:"Shark SilkiPro Hair Straightener + Dryer",vertical:"Beauty",subcategory:"Tools",price:6.23,avg_rating:5.0,image_url:"https://static.thcdn.com/productimg/original/17726736-3765312733647679.jpg",description:"2-in-1 silk styling tool with ionic ceramic plates."},
  {id:"b3c4d5e6",name:"Stylpro Heated LED Electric Gua Sha",vertical:"Beauty",subcategory:"Tools",price:38.50,avg_rating:4.3,image_url:"https://static.thcdn.com/productimg/original/16718539-6375309095782284.jpg",description:"Heated facial massage tool with LED therapy."},
  {id:"c4d5e6f7",name:"L'Oreal Professionnel Metal Detox Hair Mask",vertical:"Beauty",subcategory:"Skincare",price:28.90,avg_rating:4.7,image_url:"https://static.thcdn.com/productimg/original/13043383-1474897165519900.jpg",description:"Professional-grade mask that neutralises metal particles in hair."},
  {id:"d5e6f7a8",name:"The Ordinary Glucoside Foaming Cleanser 150ml",vertical:"Beauty",subcategory:"Skincare",price:12.80,avg_rating:4.4,image_url:"https://static.thcdn.com/productimg/original/14242474-2834942685327564.jpg",description:"Gentle foaming cleanser with glucoside surfactants."},
  {id:"518ef5de",name:"Silk Pillowcase - Stone",vertical:"Beauty",subcategory:"Bath & Body",price:45.54,avg_rating:4.0,image_url:"",description:"100% mulberry silk pillowcase, reduces hair frizz and skin creases."},
  {id:"adf591c6",name:"Niacinamide 10% Serum 30ml",vertical:"Beauty",subcategory:"Skincare",price:46.77,avg_rating:5.0,image_url:"",description:"High-strength niacinamide for pore reduction and oil control."},
  {id:"3fcd8dfe",name:"Bobbi Brown Vitamin Enriched Face Base 50ml",vertical:"Wellness",subcategory:"Family Health",price:19.84,avg_rating:4.0,image_url:"https://static.thcdn.com/productimg/original/11512195-1075217807350538.jpg",description:"Priming moisturiser packed with vitamins B, C and E."},
  {id:"47969dd9",name:"NEOM Wellbeing Essential Oil Discovery Set",vertical:"Wellness",subcategory:"Mindfulness",price:21.18,avg_rating:3.0,image_url:"https://static.thcdn.com/productimg/original/15463353-1255172214786905.jpg",description:"Four essential oil blends for energy, calm, sleep and happiness."},
  {id:"e6f7a8b9",name:"ESPA Bergamot & Jasmine Shower Gel 250ml",vertical:"Wellness",subcategory:"Mindfulness",price:22.50,avg_rating:4.6,image_url:"https://static.thcdn.com/productimg/original/12226515-1005188546067853.jpg",description:"Aromatic shower gel with bergamot, jasmine and patchouli."},
  {id:"f7a8b9c0",name:"The Ordinary Skin Support Set",vertical:"Wellness",subcategory:"Home Wellness",price:13.80,avg_rating:4.5,image_url:"https://static.thcdn.com/productimg/original/15061739-2215091651791714.jpg",description:"Starter set with cleanser, hyaluronic acid and moisturiser."},
  {id:"cef67bcf",name:"Kids Multivitamin Gummies 60 - Berry",vertical:"Wellness",subcategory:"Family Health",price:24.46,avg_rating:1.0,image_url:"",description:"Berry-flavoured multivitamin gummies for children aged 3+."},
  {id:"cf55509e",name:"Gratitude Journal Hardcover - Lavender",vertical:"Wellness",subcategory:"Mindfulness",price:21.32,avg_rating:5.0,image_url:"",description:"Guided journal with daily gratitude prompts and reflections."},
];

// Mock "also bought" data  (product_id → list of related product_ids)
const MOCK_ALSO_BOUGHT = {
  "ce5b9184": ["3fcd8dfe", "adf591c6"],
  "f9471562": ["b3c4d5e6", "c4d5e6f7"],
  "3fcd8dfe": ["ce5b9184", "47969dd9"],
  "d5e6f7a8": ["adf591c6", "c4d5e6f7"],
  "47969dd9": ["e6f7a8b9", "cf55509e"],
};

// Mock reviews per product
const MOCK_REVIEWS = {
  "ce5b9184": [
    {score: 5, comment: "Amazing hydration, my skin feels incredible after a week!", sentiment: "positive"},
    {score: 4, comment: "Good product but packaging could be better.", sentiment: "positive"},
  ],
  "f9471562": [
    {score: 5, comment: "Best straightener I've ever owned. Heats up in seconds.", sentiment: "positive"},
    {score: 5, comment: "Salon quality at home, absolutely love it.", sentiment: "positive"},
  ],
  "3fcd8dfe": [
    {score: 4, comment: "Great as a primer, keeps makeup on all day.", sentiment: "positive"},
    {score: 3, comment: "A bit pricey for the size but decent quality.", sentiment: "neutral"},
  ],
  "47969dd9": [
    {score: 3, comment: "Nice scents but they don't last very long.", sentiment: "neutral"},
    {score: 2, comment: "Expected more variety in the set.", sentiment: "negative"},
  ],
};

// Mock customer profile (simulates a logged-in user with purchase history via `placed->order->contains->product`)
const MOCK_CUSTOMER = {
  id: "154e666b",
  name: "Charlotte Souza",
  city: "contagem",
  state: "MG",
  purchases: [
    {product_id: "ce5b9184", total_spent: 32.02, order_count: 1},
    {product_id: "f9471562", total_spent: 12.46, order_count: 2},
    {product_id: "47969dd9", total_spent: 21.18, order_count: 1},
    {product_id: "d5e6f7a8", total_spent: 12.80, order_count: 1},
    {product_id: "3fcd8dfe", total_spent: 39.68, order_count: 2},
  ],
};

// Subcategory map per vertical (derived from products.csv vertical/subcategory columns)
const MOCK_SUBCATEGORIES = {
  "Fitness": ["Equipment", "Tech", "Nutrition", "Accessories", "Drinks"],
  "Beauty": ["Skincare", "Tools", "Bath & Body", "Fragrance", "Body Care", "Grooming"],
  "Wellness": ["Mindfulness", "Family Health", "Home Wellness", "Sleep", "Gifts", "Lifestyle"],
};

// Mock graph traversal data for visualization
// Each response maps to a graph that shows which nodes/edges the agent traversed
const MOCK_GRAPHS = [
  {
    nodes: [
      {id: "q", label: "Query", type: "query"},
      {id: "d1", label: "doc: Clinique", type: "faq"},
      {id: "d2", label: "doc: Skin Support", type: "faq"},
      {id: "p1", label: "Clinique Set", type: "product"},
      {id: "p3", label: "Bobbi Brown Base", type: "product"},
      {id: "c1", label: "Charlotte S.", type: "customer"},
    ],
    edges: [
      {from: "q", to: "d1", label: "hybrid", type: "bm25"},
      {from: "q", to: "d2", label: "hybrid", type: "bm25"},
      {from: "d1", to: "p1", label: "source_id", type: "relational"},
      {from: "p1", to: "p3", label: "also_bought", type: "graph"},
      {from: "c1", to: "p1", label: "bought", type: "graph"},
      {from: "c1", to: "p3", label: "bought", type: "graph"},
    ],
  },
  {
    nodes: [
      {id: "q", label: "Query", type: "query"},
      {id: "r1", label: "\"Best ever!\"", type: "review"},
      {id: "r2", label: "\"Salon quality\"", type: "review"},
      {id: "p1", label: "SilkiPro", type: "product"},
      {id: "p2", label: "Hair Mask", type: "product"},
      {id: "o1", label: "Order #7d9a", type: "order"},
    ],
    edges: [
      {from: "q", to: "r1", label: "bm25", type: "bm25"},
      {from: "q", to: "r2", label: "bm25", type: "bm25"},
      {from: "o1", to: "r1", label: "has_review", type: "graph"},
      {from: "o1", to: "p1", label: "contains", type: "graph"},
      {from: "p1", to: "p2", label: "also_bought", type: "graph"},
    ],
  },
  {
    nodes: [
      {id: "q", label: "Query", type: "query"},
      {id: "faq1", label: "Return Policy", type: "faq"},
      {id: "faq2", label: "Shipping FAQ", type: "faq"},
      {id: "lp", label: "Learned: use\nsemantic for FAQ", type: "learned"},
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
    reply: "I found some great options for you! Based on semantic search across our product database and graph traversal of co-purchase patterns, here are my top picks:\n\n1. **Clinique Moisture Surge Set** (\u00a332.02) \u2014 highly rated, customers who bought this also purchased the Bobbi Brown Face Base\n2. **The Ordinary Skin Support Set** (\u00a313.80) \u2014 great value, frequently bought with the Niacinamide Serum",
    tool_calls: [
      {name: "hybrid_search", type: "bm25", args: "documents table | combined vector + BM25 | doc_type='product'"},
      {name: "graph_traverse", type: "graph", args: "product:ce5b9184->also_bought->product WHERE weight > 2"},
      {name: "keyword_search", type: "bm25", args: "documents table | BM25 'return policy' | doc_type='faq'"},
    ],
    learn: "hybrid_search works best for product recommendations"
  },
  {
    reply: "Looking at our Beauty range! Here's what stands out based on ratings and what other customers in your segment bought:\n\n1. **Shark SilkiPro Straightener** (\u00a36.23) \u2014 top rated in Tools\n2. **L'Oreal Metal Detox Hair Mask** (\u00a328.90) \u2014 excellent reviews about repair quality\n\nI also checked customer reviews and the sentiment is overwhelmingly positive for both.",
    tool_calls: [
      {name: "keyword_search", type: "bm25", args: "documents table | BM25 'beauty tools quality'"},
      {name: "graph_traverse", type: "graph", args: "review->has_review<-order->contains->product WHERE sentiment='positive'"},
      {name: "surrealql_query", type: "relational", args: "SELECT * FROM product WHERE vertical='Beauty' ORDER BY avg_rating DESC LIMIT 5"},
    ],
    learn: null
  },
  {
    reply: "Great question! Based on our FAQ knowledge base and past patterns I've learned:\n\nYou can return any item within 30 days. Items must be unused and in original packaging. You'll get a prepaid returns label via email.\n\nI also found 3 related FAQ entries about shipping costs for returns.",
    tool_calls: [
      {name: "semantic_search", type: "vector", args: "documents table | HNSW cosine | doc_type='faq' | query: 'return policy shipping'"},
      {name: "get_record", type: "relational", args: "learned_pattern:policy_routing | best_tool='semantic_search'"},
    ],
    learn: "semantic_search on faq works best for policy questions"
  }
];
