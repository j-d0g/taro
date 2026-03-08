"""Mock dataset for Taro.ai hackathon demo.

LookFantastic-style products across Beauty, Fitness, Wellness verticals.
Rich user profiles with preferences, context, and memory.
Coherent orders/reviews that tell demo-friendly stories.
"""

# ── Goals ────────────────────────────────────────────────────

GOALS = [
    {"id": "clear_skin", "name": "Clear Skin", "description": "Achieve a clear, blemish-free complexion through targeted skincare", "vertical": "Beauty"},
    {"id": "anti_aging", "name": "Anti-Aging", "description": "Reduce fine lines and wrinkles, maintain youthful skin", "vertical": "Beauty"},
    {"id": "hydration", "name": "Hydration", "description": "Deep moisture for skin, hair, and body wellness", "vertical": "Beauty"},
    {"id": "muscle_building", "name": "Muscle Building", "description": "Build lean muscle mass through nutrition and training support", "vertical": "Fitness"},
    {"id": "weight_loss", "name": "Weight Loss", "description": "Healthy weight management through nutrition and exercise", "vertical": "Fitness"},
    {"id": "endurance", "name": "Endurance", "description": "Improve cardiovascular fitness and stamina", "vertical": "Fitness"},
    {"id": "better_sleep", "name": "Better Sleep", "description": "Improve sleep quality and establish healthy sleep patterns", "vertical": "Wellness"},
    {"id": "relaxation", "name": "Relaxation", "description": "Reduce stress and promote mental calm through self-care", "vertical": "Wellness"},
    {"id": "hair_growth", "name": "Hair Growth", "description": "Support healthy hair growth and reduce thinning", "vertical": "Beauty"},
]

# ── Ingredients ──────────────────────────────────────────────

INGREDIENTS = [
    {"id": "hyaluronic_acid", "name": "Hyaluronic Acid", "role": "hydration", "category": "skincare", "description": "Moisture-binding molecule that holds 1000x its weight in water", "common_in": ["serums", "moisturisers", "masks"]},
    {"id": "retinol", "name": "Retinol", "role": "anti-aging", "category": "skincare", "description": "Vitamin A derivative that boosts cell turnover and collagen production", "common_in": ["serums", "night creams"]},
    {"id": "niacinamide", "name": "Niacinamide", "role": "pore control", "category": "skincare", "description": "Vitamin B3 that minimises pores and evens skin tone", "common_in": ["serums", "moisturisers", "toners"]},
    {"id": "salicylic_acid", "name": "Salicylic Acid", "role": "exfoliation", "category": "skincare", "description": "BHA that penetrates pores to clear breakouts", "common_in": ["cleansers", "toners", "spot treatments"]},
    {"id": "vitamin_c", "name": "Vitamin C", "role": "brightening", "category": "skincare", "description": "Antioxidant that brightens skin and fades dark spots", "common_in": ["serums", "moisturisers"]},
    {"id": "glycolic_acid", "name": "Glycolic Acid", "role": "exfoliation", "category": "skincare", "description": "AHA that resurfaces skin for a smoother texture", "common_in": ["toners", "peeling solutions", "masks"]},
    {"id": "ceramides", "name": "Ceramides", "role": "barrier repair", "category": "skincare", "description": "Lipids that strengthen the skin barrier and lock in moisture", "common_in": ["moisturisers", "cleansers"]},
    {"id": "squalane", "name": "Squalane", "role": "hydration", "category": "skincare", "description": "Lightweight oil that mimics skin's natural sebum", "common_in": ["oils", "moisturisers"]},
    {"id": "spf", "name": "SPF Filters", "role": "sun protection", "category": "skincare", "description": "UV filters that protect skin from sun damage", "common_in": ["sunscreens", "moisturisers", "primers"]},
    {"id": "peptides", "name": "Peptides", "role": "anti-aging", "category": "skincare", "description": "Short chains of amino acids that signal collagen production", "common_in": ["serums", "eye creams"]},
    {"id": "creatine", "name": "Creatine Monohydrate", "role": "muscle performance", "category": "nutrition", "description": "Increases phosphocreatine stores for explosive strength", "common_in": ["pre-workouts", "supplements"]},
    {"id": "whey_protein", "name": "Whey Protein", "role": "muscle recovery", "category": "nutrition", "description": "Fast-absorbing complete protein for post-workout recovery", "common_in": ["protein powders", "bars"]},
    {"id": "caffeine", "name": "Caffeine", "role": "energy", "category": "nutrition", "description": "Stimulant that improves focus and exercise performance", "common_in": ["pre-workouts", "energy drinks", "eye creams"]},
    {"id": "bcaa", "name": "BCAAs", "role": "recovery", "category": "nutrition", "description": "Branched-chain amino acids that reduce muscle soreness", "common_in": ["supplements", "drinks"]},
    {"id": "collagen", "name": "Collagen", "role": "skin and joint health", "category": "wellness", "description": "Structural protein supporting skin elasticity and joint mobility", "common_in": ["supplements", "drinks", "creams"]},
    {"id": "melatonin", "name": "Melatonin", "role": "sleep support", "category": "wellness", "description": "Hormone that regulates the sleep-wake cycle", "common_in": ["sleep supplements", "sprays"]},
    {"id": "magnesium", "name": "Magnesium", "role": "relaxation", "category": "wellness", "description": "Mineral that supports muscle relaxation and sleep quality", "common_in": ["supplements", "bath salts", "sprays"]},
    {"id": "lavender", "name": "Lavender Oil", "role": "calming", "category": "wellness", "description": "Essential oil with calming and sleep-promoting properties", "common_in": ["pillow sprays", "bath products", "candles"]},
    {"id": "biotin", "name": "Biotin", "role": "hair and nail growth", "category": "wellness", "description": "B-vitamin that supports keratin production for healthy hair and nails", "common_in": ["supplements", "hair treatments"]},
    {"id": "zinc", "name": "Zinc", "role": "immune support", "category": "wellness", "description": "Essential mineral for immune function and skin health", "common_in": ["supplements", "skincare"]},
]

# ── Products ─────────────────────────────────────────────────

PRODUCTS = [
    # ─── Beauty > Skincare (10) ───
    {"id": "ordinary_niacinamide", "name": "The Ordinary Niacinamide 10% + Zinc 1%", "brand": "The Ordinary", "vertical": "Beauty", "subcategory": "Skincare", "price": 5.90, "avg_rating": 4.7, "description": "Concentrated serum that targets blemishes, enlarged pores and uneven skin tone. A cult-favourite with 10% pure niacinamide.", "weight_g": 30, "ingredients": ["Niacinamide", "Zinc"], "tags": ["bestseller", "vegan", "cruelty-free"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "cerave_moisturiser", "name": "CeraVe Moisturising Cream", "brand": "CeraVe", "vertical": "Beauty", "subcategory": "Skincare", "price": 12.50, "avg_rating": 4.8, "description": "Rich, non-greasy moisturiser with 3 essential ceramides and hyaluronic acid. Restores and maintains the skin barrier.", "weight_g": 340, "ingredients": ["Ceramides", "Hyaluronic Acid"], "tags": ["bestseller", "fragrance-free", "dermatologist-recommended"], "dietary_tags": [], "image_url": ""},
    {"id": "ordinary_peeling", "name": "The Ordinary AHA 30% + BHA 2% Peeling Solution", "brand": "The Ordinary", "vertical": "Beauty", "subcategory": "Skincare", "price": 7.35, "avg_rating": 4.6, "description": "10-minute exfoliating facial with glycolic, salicylic, and lactic acids. Reveals brighter, smoother skin.", "weight_g": 30, "ingredients": ["Glycolic Acid", "Salicylic Acid"], "tags": ["bestseller", "vegan", "cruelty-free"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "elemis_cleansing_balm", "name": "ELEMIS Pro-Collagen Cleansing Balm", "brand": "ELEMIS", "vertical": "Beauty", "subcategory": "Skincare", "price": 46.00, "avg_rating": 4.9, "description": "Award-winning 3-in-1 cleansing balm that melts away makeup and impurities. Infused with elderberry, starflower and rose.", "weight_g": 100, "ingredients": ["Collagen", "Squalane"], "tags": ["luxury", "award-winning", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "la_roche_posay_spf", "name": "La Roche-Posay Anthelios UVMune 400 SPF50+", "brand": "La Roche-Posay", "vertical": "Beauty", "subcategory": "Skincare", "price": 18.00, "avg_rating": 4.7, "description": "Ultra-protection sunscreen with Mexoryl 400 filter. Lightweight, non-greasy formula suitable for sensitive skin.", "weight_g": 50, "ingredients": ["SPF Filters"], "tags": ["dermatologist-recommended", "fragrance-free"], "dietary_tags": [], "image_url": ""},
    {"id": "ordinary_retinol", "name": "The Ordinary Retinol 0.5% in Squalane", "brand": "The Ordinary", "vertical": "Beauty", "subcategory": "Skincare", "price": 5.80, "avg_rating": 4.3, "description": "Water-free retinol solution in squalane for anti-aging benefits. Targets fine lines, wrinkles and uneven tone.", "weight_g": 30, "ingredients": ["Retinol", "Squalane"], "tags": ["vegan", "cruelty-free", "anti-aging"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "clinique_moisture_surge", "name": "Clinique Moisture Surge 100H Auto-Replenishing Hydrator", "brand": "Clinique", "vertical": "Beauty", "subcategory": "Skincare", "price": 32.00, "avg_rating": 4.6, "description": "Cloud-like cream-gel that provides 100 hours of hydration. Oil-free and suitable for all skin types.", "weight_g": 50, "ingredients": ["Hyaluronic Acid", "Squalane"], "tags": ["fragrance-free", "allergy-tested"], "dietary_tags": [], "image_url": ""},
    {"id": "drunk_elephant_vc", "name": "Drunk Elephant C-Firma Fresh Day Serum", "brand": "Drunk Elephant", "vertical": "Beauty", "subcategory": "Skincare", "price": 62.00, "avg_rating": 4.4, "description": "Potent 15% L-ascorbic acid vitamin C serum packed with antioxidants. Firms, brightens, and improves signs of photoaging.", "weight_g": 30, "ingredients": ["Vitamin C", "Peptides"], "tags": ["luxury", "clean-beauty"], "dietary_tags": [], "image_url": ""},
    {"id": "inkey_list_ha", "name": "The INKEY List Hyaluronic Acid Serum", "brand": "The INKEY List", "vertical": "Beauty", "subcategory": "Skincare", "price": 6.99, "avg_rating": 4.5, "description": "Lightweight hydrating serum with 2% hyaluronic acid complex. Instantly plumps skin and locks in moisture.", "weight_g": 30, "ingredients": ["Hyaluronic Acid"], "tags": ["budget-friendly", "vegan", "cruelty-free"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "cerave_cleanser", "name": "CeraVe Hydrating Facial Cleanser", "brand": "CeraVe", "vertical": "Beauty", "subcategory": "Skincare", "price": 11.50, "avg_rating": 4.7, "description": "Non-foaming cleanser with ceramides and hyaluronic acid. Removes dirt without stripping the skin barrier.", "weight_g": 236, "ingredients": ["Ceramides", "Hyaluronic Acid"], "tags": ["fragrance-free", "dermatologist-recommended"], "dietary_tags": [], "image_url": ""},

    # ─── Beauty > Bath & Body (8) ───
    {"id": "sanctuary_bath_soak", "name": "Sanctuary Spa Wellness De-Stress Bath Soak", "brand": "Sanctuary Spa", "vertical": "Beauty", "subcategory": "Bath & Body", "price": 8.00, "avg_rating": 4.5, "description": "Calming bath soak with lavender and chamomile. Transforms bath water into a de-stressing spa experience.", "weight_g": 500, "ingredients": ["Lavender Oil", "Magnesium"], "tags": ["relaxing", "vegan"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "rituals_body_cream", "name": "Rituals The Ritual of Sakura Body Cream", "brand": "Rituals", "vertical": "Beauty", "subcategory": "Bath & Body", "price": 19.90, "avg_rating": 4.6, "description": "Nourishing body cream with cherry blossom and rice milk. Leaves skin silky smooth with a delicate scent.", "weight_g": 220, "ingredients": ["Squalane"], "tags": ["luxury"], "dietary_tags": [], "image_url": ""},
    {"id": "sol_janeiro_bum_bum", "name": "Sol de Janeiro Brazilian Bum Bum Cream", "brand": "Sol de Janeiro", "vertical": "Beauty", "subcategory": "Bath & Body", "price": 44.00, "avg_rating": 4.7, "description": "Iconic fast-absorbing body cream with cupuacu butter and caffeine. Tightens, smooths and adds addictive caramel scent.", "weight_g": 240, "ingredients": ["Caffeine", "Collagen"], "tags": ["bestseller", "cult-favourite"], "dietary_tags": [], "image_url": ""},
    {"id": "bioderma_shower_oil", "name": "Bioderma Atoderm Shower Oil", "brand": "Bioderma", "vertical": "Beauty", "subcategory": "Bath & Body", "price": 11.50, "avg_rating": 4.4, "description": "Ultra-nourishing shower oil that cleanses without drying. Perfect for very dry and sensitive skin.", "weight_g": 1000, "ingredients": ["Squalane", "Ceramides"], "tags": ["dermatologist-recommended", "fragrance-free"], "dietary_tags": [], "image_url": ""},
    {"id": "lush_sleepy_lotion", "name": "Lush Sleepy Body Lotion", "brand": "Lush", "vertical": "Beauty", "subcategory": "Bath & Body", "price": 16.50, "avg_rating": 4.8, "description": "Calming body lotion with lavender and tonka bean. Apply before bed for a soothing, restful night's sleep.", "weight_g": 215, "ingredients": ["Lavender Oil"], "tags": ["vegan", "handmade", "bestseller"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "dove_body_wash", "name": "Dove Deeply Nourishing Body Wash", "brand": "Dove", "vertical": "Beauty", "subcategory": "Bath & Body", "price": 4.50, "avg_rating": 4.3, "description": "Microbiome-gentle body wash with NutriumMoisture technology. Delivers softer, smoother skin from day one.", "weight_g": 450, "ingredients": ["Ceramides"], "tags": ["budget-friendly"], "dietary_tags": [], "image_url": ""},
    {"id": "molton_brown_wash", "name": "Molton Brown Re-Charge Black Pepper Bath & Shower Gel", "brand": "Molton Brown", "vertical": "Beauty", "subcategory": "Bath & Body", "price": 25.00, "avg_rating": 4.5, "description": "Invigorating shower gel with Madagascan black pepper, coriander and basil. A warm, spicy wake-up call.", "weight_g": 300, "ingredients": [], "tags": ["luxury", "gift-worthy"], "dietary_tags": [], "image_url": ""},
    {"id": "aveeno_lotion", "name": "Aveeno Daily Moisturising Lotion", "brand": "Aveeno", "vertical": "Beauty", "subcategory": "Bath & Body", "price": 7.99, "avg_rating": 4.5, "description": "Fragrance-free lotion with colloidal oatmeal. Clinically proven to moisturise for 24 hours.", "weight_g": 300, "ingredients": ["Ceramides"], "tags": ["fragrance-free", "dermatologist-recommended"], "dietary_tags": [], "image_url": ""},

    # ─── Beauty > Fragrance (6) ───
    {"id": "jo_malone_lime", "name": "Jo Malone London Lime Basil & Mandarin Cologne", "brand": "Jo Malone", "vertical": "Beauty", "subcategory": "Fragrance", "price": 55.00, "avg_rating": 4.8, "description": "Crisp, peppery cologne inspired by a Caribbean breeze. Lime, basil and white thyme in perfect balance.", "weight_g": 30, "ingredients": [], "tags": ["luxury", "gift-worthy", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "ysl_libre", "name": "YSL Libre Eau de Parfum", "brand": "YSL", "vertical": "Beauty", "subcategory": "Fragrance", "price": 72.00, "avg_rating": 4.6, "description": "Bold floral fragrance with French lavender and Moroccan orange blossom. The scent of freedom.", "weight_g": 50, "ingredients": ["Lavender Oil"], "tags": ["luxury", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "ariana_cloud", "name": "Ariana Grande Cloud Eau de Parfum", "brand": "Ariana Grande", "vertical": "Beauty", "subcategory": "Fragrance", "price": 35.00, "avg_rating": 4.5, "description": "Dreamy, cloud-like fragrance with lavender, coconut and musks. Sweet, airy and universally loved.", "weight_g": 100, "ingredients": ["Lavender Oil"], "tags": ["bestseller", "value"], "dietary_tags": [], "image_url": ""},
    {"id": "dior_sauvage", "name": "Dior Sauvage Eau de Toilette", "brand": "Dior", "vertical": "Beauty", "subcategory": "Fragrance", "price": 68.00, "avg_rating": 4.7, "description": "Raw, noble masculinity with Calabrian bergamot and Ambroxan. The world's most popular men's fragrance.", "weight_g": 60, "ingredients": [], "tags": ["luxury", "bestseller", "iconic"], "dietary_tags": [], "image_url": ""},
    {"id": "sol_janeiro_mist", "name": "Sol de Janeiro Brazilian Bum Bum Body Mist", "brand": "Sol de Janeiro", "vertical": "Beauty", "subcategory": "Fragrance", "price": 22.00, "avg_rating": 4.6, "description": "All-over body mist with the iconic Brazilian Bum Bum scent. Caramel, pistachio and salted vanilla.", "weight_g": 240, "ingredients": [], "tags": ["cult-favourite", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "acqua_di_parma", "name": "Acqua di Parma Colonia Eau de Cologne", "brand": "Acqua di Parma", "vertical": "Beauty", "subcategory": "Fragrance", "price": 85.00, "avg_rating": 4.7, "description": "Italian elegance in a bottle. Sicilian citrus, lavender and rosemary in a timeless cologne.", "weight_g": 100, "ingredients": ["Lavender Oil"], "tags": ["luxury", "gift-worthy"], "dietary_tags": [], "image_url": ""},

    # ─── Beauty > Tools (6) ───
    {"id": "ghd_platinum", "name": "ghd Platinum+ Styler", "brand": "ghd", "vertical": "Beauty", "subcategory": "Tools", "price": 199.00, "avg_rating": 4.8, "description": "Ultra-zone predictive technology styler that recognises hair needs. 185°C optimum styling temperature.", "weight_g": 500, "ingredients": [], "tags": ["luxury", "award-winning", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "dyson_airwrap", "name": "Dyson Airwrap Multi-Styler Complete Long", "brand": "Dyson", "vertical": "Beauty", "subcategory": "Tools", "price": 479.99, "avg_rating": 4.7, "description": "Revolutionary multi-styler that uses air, not extreme heat. Curl, wave, smooth and dry with one tool.", "weight_g": 700, "ingredients": [], "tags": ["luxury", "innovation"], "dietary_tags": [], "image_url": ""},
    {"id": "beautyblender_og", "name": "beautyblender Original", "brand": "beautyblender", "vertical": "Beauty", "subcategory": "Tools", "price": 17.00, "avg_rating": 4.6, "description": "The original edgeless makeup sponge. Bounce for a flawless, airbrushed finish with any foundation.", "weight_g": 20, "ingredients": [], "tags": ["bestseller", "cult-favourite"], "dietary_tags": [], "image_url": ""},
    {"id": "foreo_luna", "name": "FOREO LUNA 4 Facial Cleansing Device", "brand": "FOREO", "vertical": "Beauty", "subcategory": "Tools", "price": 199.00, "avg_rating": 4.5, "description": "Medical-grade silicone cleansing device with 16 intensities. Removes 99% of dirt and oil.", "weight_g": 120, "ingredients": [], "tags": ["innovation", "smart-tech"], "dietary_tags": [], "image_url": ""},
    {"id": "tangle_teezer", "name": "Tangle Teezer The Original Detangling Hairbrush", "brand": "Tangle Teezer", "vertical": "Beauty", "subcategory": "Tools", "price": 12.00, "avg_rating": 4.7, "description": "Patented two-tiered teeth flex through knots painlessly. Reduces breakage and leaves hair smooth.", "weight_g": 80, "ingredients": [], "tags": ["award-winning", "bestseller", "value"], "dietary_tags": [], "image_url": ""},
    {"id": "jade_roller", "name": "Mount Lai The De-Puffing Jade Roller", "brand": "Mount Lai", "vertical": "Beauty", "subcategory": "Tools", "price": 28.00, "avg_rating": 4.3, "description": "Genuine jade facial roller that cools and de-puffs. Use with serum for enhanced absorption.", "weight_g": 150, "ingredients": [], "tags": ["natural", "self-care"], "dietary_tags": [], "image_url": ""},

    # ─── Beauty > Grooming (6) ───
    {"id": "bulldog_moisturiser", "name": "Bulldog Original Moisturiser", "brand": "Bulldog", "vertical": "Beauty", "subcategory": "Grooming", "price": 6.00, "avg_rating": 4.4, "description": "Lightweight moisturiser designed for men's skin. With aloe vera, camelina oil and green tea.", "weight_g": 100, "ingredients": ["Squalane"], "tags": ["vegan", "cruelty-free", "value"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "harry_razor", "name": "Harry's Winston Razor Set", "brand": "Harry's", "vertical": "Beauty", "subcategory": "Grooming", "price": 15.00, "avg_rating": 4.3, "description": "Precision-engineered 5-blade razor with weighted handle. Includes 2 blade cartridges and travel cover.", "weight_g": 120, "ingredients": [], "tags": ["value", "starter-kit"], "dietary_tags": [], "image_url": ""},
    {"id": "clinique_for_men", "name": "Clinique For Men Maximum Hydrator", "brand": "Clinique", "vertical": "Beauty", "subcategory": "Grooming", "price": 30.00, "avg_rating": 4.5, "description": "72-hour hydrating gel cream with caffeine and hyaluronic acid. Oil-free, mattifying formula.", "weight_g": 50, "ingredients": ["Hyaluronic Acid", "Caffeine"], "tags": ["fragrance-free"], "dietary_tags": [], "image_url": ""},
    {"id": "lab_series_cleanser", "name": "Lab Series Multi-Action Face Wash", "brand": "Lab Series", "vertical": "Beauty", "subcategory": "Grooming", "price": 22.00, "avg_rating": 4.2, "description": "3-in-1 cleanser, exfoliator and toner for men. Removes excess oil and unclogs pores.", "weight_g": 100, "ingredients": ["Salicylic Acid"], "tags": ["multi-function"], "dietary_tags": [], "image_url": ""},
    {"id": "aesop_post_shave", "name": "Aesop In Two Minds Facial Hydrator", "brand": "Aesop", "vertical": "Beauty", "subcategory": "Grooming", "price": 45.00, "avg_rating": 4.6, "description": "Lightweight gel-cream for combination skin. Niacinamide, sage leaf and bisabolol balance and hydrate.", "weight_g": 60, "ingredients": ["Niacinamide"], "tags": ["luxury", "clean-beauty"], "dietary_tags": [], "image_url": ""},
    {"id": "king_c_gillette_oil", "name": "King C. Gillette Beard Oil", "brand": "King C. Gillette", "vertical": "Beauty", "subcategory": "Grooming", "price": 9.99, "avg_rating": 4.4, "description": "Premium beard oil with argan and jojoba oils. Softens, conditions and tames facial hair.", "weight_g": 30, "ingredients": ["Squalane"], "tags": ["value", "bestseller"], "dietary_tags": [], "image_url": ""},

    # ─── Beauty > Body Care (6) ───
    {"id": "palmers_cocoa", "name": "Palmer's Cocoa Butter Formula Body Lotion", "brand": "Palmer's", "vertical": "Beauty", "subcategory": "Body Care", "price": 5.49, "avg_rating": 4.5, "description": "Rich cocoa butter lotion that heals and softens rough, dry skin. With vitamin E for added nourishment.", "weight_g": 400, "ingredients": ["Vitamin C"], "tags": ["budget-friendly", "classic"], "dietary_tags": [], "image_url": ""},
    {"id": "nuxe_dry_oil", "name": "NUXE Huile Prodigieuse Multi-Purpose Dry Oil", "brand": "NUXE", "vertical": "Beauty", "subcategory": "Body Care", "price": 26.50, "avg_rating": 4.7, "description": "Cult-favourite dry oil for face, body and hair. Nourishes, repairs and adds satin glow.", "weight_g": 100, "ingredients": ["Squalane"], "tags": ["cult-favourite", "multi-use"], "dietary_tags": [], "image_url": ""},
    {"id": "bio_oil", "name": "Bio-Oil Skincare Oil", "brand": "Bio-Oil", "vertical": "Beauty", "subcategory": "Body Care", "price": 13.50, "avg_rating": 4.4, "description": "Specialist skincare oil for scars, stretch marks and uneven skin tone. With PurCellin Oil technology.", "weight_g": 125, "ingredients": ["Retinol", "Vitamin C"], "tags": ["bestseller", "dermatologist-recommended"], "dietary_tags": [], "image_url": ""},
    {"id": "first_aid_beauty_kp", "name": "First Aid Beauty KP Bump Eraser Body Scrub", "brand": "First Aid Beauty", "vertical": "Beauty", "subcategory": "Body Care", "price": 24.00, "avg_rating": 4.5, "description": "Chemical + physical exfoliant with 10% AHA and pumice. Smooths keratosis pilaris and rough bumps.", "weight_g": 283, "ingredients": ["Glycolic Acid"], "tags": ["dermatologist-recommended", "clean-beauty"], "dietary_tags": [], "image_url": ""},
    {"id": "neutrogena_hand", "name": "Neutrogena Norwegian Formula Hand Cream", "brand": "Neutrogena", "vertical": "Beauty", "subcategory": "Body Care", "price": 4.29, "avg_rating": 4.6, "description": "Concentrated glycerine formula that provides immediate and lasting relief for extremely dry hands.", "weight_g": 75, "ingredients": ["Ceramides"], "tags": ["budget-friendly", "classic", "dermatologist-recommended"], "dietary_tags": [], "image_url": ""},
    {"id": "ameliorate_lotion", "name": "Ameliorate Transforming Body Lotion", "brand": "Ameliorate", "vertical": "Beauty", "subcategory": "Body Care", "price": 27.00, "avg_rating": 4.6, "description": "Clinically proven lotion with lactic acid that smooths rough, bumpy skin. Visible results in 6 days.", "weight_g": 200, "ingredients": ["Glycolic Acid", "Ceramides"], "tags": ["dermatologist-recommended", "award-winning"], "dietary_tags": [], "image_url": ""},

    # ─── Beauty > Accessories (6) ───
    {"id": "slip_pillowcase", "name": "Slip Pure Silk Pillowcase", "brand": "Slip", "vertical": "Beauty", "subcategory": "Accessories", "price": 85.00, "avg_rating": 4.8, "description": "Grade 6A mulberry silk pillowcase that reduces friction. Prevents hair breakage and sleep creases.", "weight_g": 100, "ingredients": [], "tags": ["luxury", "bestseller", "sleep"], "dietary_tags": [], "image_url": ""},
    {"id": "kitsch_hair_ties", "name": "Kitsch Recycled Satin Scrunchies", "brand": "Kitsch", "vertical": "Beauty", "subcategory": "Accessories", "price": 8.00, "avg_rating": 4.4, "description": "Pack of 5 satin scrunchies made from recycled materials. Gentle on hair, no pulling or snagging.", "weight_g": 50, "ingredients": [], "tags": ["sustainable", "value", "vegan"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "elemis_headband", "name": "ELEMIS Spa Headband", "brand": "ELEMIS", "vertical": "Beauty", "subcategory": "Accessories", "price": 14.00, "avg_rating": 4.3, "description": "Plush terry cloth headband to keep hair back during skincare routines. Adjustable and machine washable.", "weight_g": 60, "ingredients": [], "tags": ["spa", "self-care"], "dietary_tags": [], "image_url": ""},
    {"id": "makeup_bag_ted", "name": "Ted Baker Floral Print Makeup Bag", "brand": "Ted Baker", "vertical": "Beauty", "subcategory": "Accessories", "price": 25.00, "avg_rating": 4.5, "description": "Beautiful floral-print PVC makeup bag with wipe-clean interior. Spacious enough for daily essentials.", "weight_g": 150, "ingredients": [], "tags": ["gift-worthy"], "dietary_tags": [], "image_url": ""},
    {"id": "ecotools_set", "name": "EcoTools Start The Day Beautifully Brush Set", "brand": "EcoTools", "vertical": "Beauty", "subcategory": "Accessories", "price": 12.99, "avg_rating": 4.4, "description": "5-piece brush set with recycled aluminium handles. Includes powder, blush, eye shadow, lip and concealer brushes.", "weight_g": 120, "ingredients": [], "tags": ["sustainable", "cruelty-free", "value"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "mirror_compact", "name": "Fancii LED Compact Mirror", "brand": "Fancii", "vertical": "Beauty", "subcategory": "Accessories", "price": 18.99, "avg_rating": 4.3, "description": "Lighted compact mirror with 1x/10x magnification. Natural daylight LED for precise makeup application.", "weight_g": 130, "ingredients": [], "tags": ["travel-friendly"], "dietary_tags": [], "image_url": ""},

    # ─── Fitness > Equipment (8) ───
    {"id": "resistance_bands_set", "name": "Fit Simplify Resistance Loop Bands Set", "brand": "Fit Simplify", "vertical": "Fitness", "subcategory": "Equipment", "price": 12.99, "avg_rating": 4.5, "description": "Set of 5 latex resistance bands in progressive strengths. Perfect for glutes, legs and physiotherapy.", "weight_g": 200, "ingredients": [], "tags": ["bestseller", "home-gym", "value"], "dietary_tags": [], "image_url": ""},
    {"id": "yoga_mat_manduka", "name": "Manduka PRO Yoga Mat", "brand": "Manduka", "vertical": "Fitness", "subcategory": "Equipment", "price": 95.00, "avg_rating": 4.8, "description": "Dense 6mm cushion with closed-cell surface. Lifetime guarantee. The gold standard for serious yogis.", "weight_g": 3400, "ingredients": [], "tags": ["premium", "lifetime-guarantee", "eco-friendly"], "dietary_tags": [], "image_url": ""},
    {"id": "foam_roller", "name": "TriggerPoint GRID Foam Roller", "brand": "TriggerPoint", "vertical": "Fitness", "subcategory": "Equipment", "price": 34.99, "avg_rating": 4.6, "description": "Patented multi-density foam roller that mimics a therapist's hand. For warm-up, recovery and pain relief.", "weight_g": 600, "ingredients": [], "tags": ["recovery", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "kettlebell_12kg", "name": "Wolverson Fitness Competition Kettlebell 12kg", "brand": "Wolverson", "vertical": "Fitness", "subcategory": "Equipment", "price": 42.00, "avg_rating": 4.7, "description": "Steel competition kettlebell with consistent handle diameter. Colour-coded by weight for quick identification.", "weight_g": 12000, "ingredients": [], "tags": ["home-gym", "competition-grade"], "dietary_tags": [], "image_url": ""},
    {"id": "pull_up_bar", "name": "Iron Gym Total Upper Body Workout Bar", "brand": "Iron Gym", "vertical": "Fitness", "subcategory": "Equipment", "price": 24.99, "avg_rating": 4.3, "description": "Doorframe-mounted pull-up bar with multiple grip positions. No screws needed—leveraged mounting.", "weight_g": 2800, "ingredients": [], "tags": ["home-gym", "value"], "dietary_tags": [], "image_url": ""},
    {"id": "skipping_rope", "name": "Beast Gear Speed Skipping Rope", "brand": "Beast Gear", "vertical": "Fitness", "subcategory": "Equipment", "price": 8.97, "avg_rating": 4.5, "description": "Adjustable speed rope with smooth ball bearing mechanism. Perfect for double-unders and HIIT.", "weight_g": 180, "ingredients": [], "tags": ["value", "cardio", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "dumbbells_hex", "name": "Mirafit Hex Dumbbells 10kg Pair", "brand": "Mirafit", "vertical": "Fitness", "subcategory": "Equipment", "price": 29.95, "avg_rating": 4.6, "description": "Rubber-coated hex dumbbells with ergonomic chrome handles. Non-roll design for floor safety.", "weight_g": 20000, "ingredients": [], "tags": ["home-gym", "essentials"], "dietary_tags": [], "image_url": ""},
    {"id": "ab_roller", "name": "Perfect Fitness Ab Carver Pro Roller", "brand": "Perfect Fitness", "vertical": "Fitness", "subcategory": "Equipment", "price": 19.99, "avg_rating": 4.4, "description": "Carbon steel spring-loaded ab roller. Internal resistance assists on the roll-out and adds challenge on return.", "weight_g": 1300, "ingredients": [], "tags": ["core", "home-gym"], "dietary_tags": [], "image_url": ""},

    # ─── Fitness > Nutrition (8) ───
    {"id": "mp_impact_whey", "name": "Myprotein Impact Whey Protein", "brand": "Myprotein", "vertical": "Fitness", "subcategory": "Nutrition", "price": 22.99, "avg_rating": 4.6, "description": "High-quality whey protein with 21g protein per serving. Available in 40+ flavours. UK's #1 protein brand.", "weight_g": 1000, "ingredients": ["Whey Protein"], "tags": ["bestseller", "value"], "dietary_tags": ["gluten-free"], "image_url": ""},
    {"id": "optimum_gold", "name": "Optimum Nutrition Gold Standard 100% Whey", "brand": "Optimum Nutrition", "vertical": "Fitness", "subcategory": "Nutrition", "price": 38.99, "avg_rating": 4.7, "description": "The world's best-selling whey protein. 24g protein, 5.5g BCAAs per serving. Double Rich Chocolate.", "weight_g": 908, "ingredients": ["Whey Protein", "BCAAs"], "tags": ["premium", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "mp_creatine", "name": "Myprotein Creatine Monohydrate Powder", "brand": "Myprotein", "vertical": "Fitness", "subcategory": "Nutrition", "price": 9.99, "avg_rating": 4.7, "description": "Pure creatine monohydrate, one of the most researched supplements. 5g per serving for strength and power.", "weight_g": 250, "ingredients": ["Creatine Monohydrate"], "tags": ["bestseller", "essentials", "vegan"], "dietary_tags": ["vegan", "gluten-free"], "image_url": ""},
    {"id": "protein_bar_grenade", "name": "Grenade Carb Killa Protein Bar", "brand": "Grenade", "vertical": "Fitness", "subcategory": "Nutrition", "price": 2.50, "avg_rating": 4.5, "description": "20g protein, low-sugar bar in White Chocolate Cookie flavour. Triple-layered for satisfying texture.", "weight_g": 60, "ingredients": ["Whey Protein"], "tags": ["on-the-go", "low-sugar", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "vegan_protein_huel", "name": "Huel Complete Protein", "brand": "Huel", "vertical": "Fitness", "subcategory": "Nutrition", "price": 27.00, "avg_rating": 4.3, "description": "Plant-based protein blend with all essential amino acids. 20g protein from pea, rice, hemp and faba bean.", "weight_g": 780, "ingredients": [], "tags": ["vegan", "sustainable"], "dietary_tags": ["vegan", "gluten-free"], "image_url": ""},
    {"id": "peanut_butter_pip", "name": "Pip & Nut Smooth Peanut Butter", "brand": "Pip & Nut", "vertical": "Fitness", "subcategory": "Nutrition", "price": 3.50, "avg_rating": 4.6, "description": "100% natural peanut butter with no palm oil, no added sugar. Just peanuts and a pinch of sea salt.", "weight_g": 300, "ingredients": [], "tags": ["natural", "vegan", "value"], "dietary_tags": ["vegan", "gluten-free"], "image_url": ""},
    {"id": "bcaa_powder", "name": "Applied Nutrition BCAA Amino Hydrate", "brand": "Applied Nutrition", "vertical": "Fitness", "subcategory": "Nutrition", "price": 14.99, "avg_rating": 4.4, "description": "6g BCAAs + electrolytes in a refreshing drink. Reduces muscle soreness and supports hydration.", "weight_g": 450, "ingredients": ["BCAAs", "Magnesium"], "tags": ["recovery", "hydration"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "omega_3", "name": "Myprotein Omega 3 Fish Oil Capsules", "brand": "Myprotein", "vertical": "Fitness", "subcategory": "Nutrition", "price": 7.99, "avg_rating": 4.3, "description": "High-strength omega-3 with EPA and DHA. Supports heart health, brain function and joint mobility.", "weight_g": 200, "ingredients": ["Zinc"], "tags": ["essentials"], "dietary_tags": [], "image_url": ""},

    # ─── Fitness > Tech (6) ───
    {"id": "garmin_forerunner", "name": "Garmin Forerunner 265 GPS Running Watch", "brand": "Garmin", "vertical": "Fitness", "subcategory": "Tech", "price": 349.99, "avg_rating": 4.8, "description": "AMOLED display GPS running watch with training readiness and morning report. 13-day battery life.", "weight_g": 47, "ingredients": [], "tags": ["premium", "smart-tech", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "whoop_band", "name": "WHOOP 4.0 Fitness Tracker", "brand": "WHOOP", "vertical": "Fitness", "subcategory": "Tech", "price": 0.00, "avg_rating": 4.5, "description": "Screen-free wearable tracking strain, recovery and sleep. Free device with membership subscription.", "weight_g": 27, "ingredients": [], "tags": ["innovation", "pro-athlete"], "dietary_tags": [], "image_url": ""},
    {"id": "theragun_mini", "name": "Theragun Mini 2.0 Massage Gun", "brand": "Therabody", "vertical": "Fitness", "subcategory": "Tech", "price": 149.00, "avg_rating": 4.6, "description": "Pocket-sized percussive therapy device. 3 speeds, QuietForce Technology. Perfect for on-the-go recovery.", "weight_g": 500, "ingredients": [], "tags": ["recovery", "travel-friendly", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "fitbit_charge", "name": "Fitbit Charge 6 Activity Tracker", "brand": "Fitbit", "vertical": "Fitness", "subcategory": "Tech", "price": 139.99, "avg_rating": 4.4, "description": "Advanced health tracker with Google integration. ECG, SpO2, stress management and 40+ exercise modes.", "weight_g": 37, "ingredients": [], "tags": ["smart-tech", "value"], "dietary_tags": [], "image_url": ""},
    {"id": "hydration_bottle", "name": "HidrateSpark PRO Smart Water Bottle", "brand": "HidrateSpark", "vertical": "Fitness", "subcategory": "Tech", "price": 44.99, "avg_rating": 4.2, "description": "LED-glowing smart bottle that tracks water intake via Bluetooth. Reminds you to stay hydrated.", "weight_g": 350, "ingredients": [], "tags": ["smart-tech", "hydration"], "dietary_tags": [], "image_url": ""},
    {"id": "mp_shaker", "name": "Myprotein Smartshake Original Shaker", "brand": "Myprotein", "vertical": "Fitness", "subcategory": "Tech", "price": 7.99, "avg_rating": 4.3, "description": "600ml leakproof shaker with wire mixing ball. Twist-on storage compartment for supplements.", "weight_g": 200, "ingredients": [], "tags": ["essentials", "value"], "dietary_tags": [], "image_url": ""},

    # ─── Fitness > Drinks (6) ───
    {"id": "nocco_bcaa", "name": "NOCCO BCAA+ Sport Drink", "brand": "NOCCO", "vertical": "Fitness", "subcategory": "Drinks", "price": 2.00, "avg_rating": 4.3, "description": "Zero-sugar BCAA drink with caffeine and vitamins. Refreshing Tropical flavour for pre or post workout.", "weight_g": 330, "ingredients": ["BCAAs", "Caffeine"], "tags": ["zero-sugar", "on-the-go"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "grenade_shake", "name": "Grenade High Protein Shake", "brand": "Grenade", "vertical": "Fitness", "subcategory": "Drinks", "price": 2.99, "avg_rating": 4.4, "description": "Ready-to-drink 25g protein shake in Fudge Brownie flavour. Low-sugar, high-protein convenience.", "weight_g": 330, "ingredients": ["Whey Protein"], "tags": ["on-the-go", "low-sugar"], "dietary_tags": [], "image_url": ""},
    {"id": "mp_clear_whey", "name": "Myprotein Clear Whey Isolate", "brand": "Myprotein", "vertical": "Fitness", "subcategory": "Drinks", "price": 24.99, "avg_rating": 4.5, "description": "Light, refreshing, juice-like protein drink. 20g protein per serving. Peach Tea flavour.", "weight_g": 500, "ingredients": ["Whey Protein"], "tags": ["innovation", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "prime_hydration", "name": "PRIME Hydration Drink", "brand": "PRIME", "vertical": "Fitness", "subcategory": "Drinks", "price": 2.50, "avg_rating": 4.1, "description": "Electrolyte-infused hydration drink with BCAAs. 10% coconut water, zero sugar. Ice Pop flavour.", "weight_g": 500, "ingredients": ["BCAAs"], "tags": ["trending"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "bulk_pre_workout", "name": "Bulk Complete Pre-Workout", "brand": "Bulk", "vertical": "Fitness", "subcategory": "Drinks", "price": 16.99, "avg_rating": 4.4, "description": "Comprehensive pre-workout with caffeine, creatine and beta-alanine. 150mg caffeine per serving.", "weight_g": 500, "ingredients": ["Creatine Monohydrate", "Caffeine"], "tags": ["performance", "value"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "science_energy_gel", "name": "Science in Sport GO Isotonic Energy Gel", "brand": "SiS", "vertical": "Fitness", "subcategory": "Drinks", "price": 1.25, "avg_rating": 4.2, "description": "Easy-to-take isotonic gel requiring no water. 22g fast-acting carbohydrates for endurance performance.", "weight_g": 60, "ingredients": [], "tags": ["endurance", "on-the-go"], "dietary_tags": ["vegan"], "image_url": ""},

    # ─── Fitness > Accessories (6) ───
    {"id": "lifting_gloves", "name": "RDX Weight Lifting Gloves", "brand": "RDX", "vertical": "Fitness", "subcategory": "Accessories", "price": 14.99, "avg_rating": 4.4, "description": "Authentic leather gym gloves with integrated wrist support. Padded palms prevent calluses.", "weight_g": 150, "ingredients": [], "tags": ["essentials"], "dietary_tags": [], "image_url": ""},
    {"id": "gym_bag_under_armour", "name": "Under Armour Undeniable 5.0 Duffle", "brand": "Under Armour", "vertical": "Fitness", "subcategory": "Accessories", "price": 30.00, "avg_rating": 4.6, "description": "Water-repellent duffle bag with UA Storm technology. Ventilated shoe pocket and adjustable strap.", "weight_g": 680, "ingredients": [], "tags": ["essentials", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "knee_sleeves", "name": "SBD Knee Sleeves", "brand": "SBD", "vertical": "Fitness", "subcategory": "Accessories", "price": 70.00, "avg_rating": 4.8, "description": "Competition-approved 7mm neoprene knee sleeves. IPF and IWF approved. The powerlifter's choice.", "weight_g": 400, "ingredients": [], "tags": ["competition-grade", "premium"], "dietary_tags": [], "image_url": ""},
    {"id": "shaker_bottle", "name": "BlenderBottle Classic V2 Shaker", "brand": "BlenderBottle", "vertical": "Fitness", "subcategory": "Accessories", "price": 9.99, "avg_rating": 4.5, "description": "28oz shaker with patented BlenderBall wire whisk. Leak-proof, dishwasher safe. 100+ colours.", "weight_g": 180, "ingredients": [], "tags": ["essentials", "value", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "wrist_wraps", "name": "Gymshark Wrist Wraps", "brand": "Gymshark", "vertical": "Fitness", "subcategory": "Accessories", "price": 12.00, "avg_rating": 4.3, "description": "Stiff cotton wrist wraps with thumb loop. Provides joint stability during heavy pressing movements.", "weight_g": 80, "ingredients": [], "tags": ["essentials"], "dietary_tags": [], "image_url": ""},
    {"id": "headband_nike", "name": "Nike Swoosh Sport Headband", "brand": "Nike", "vertical": "Fitness", "subcategory": "Accessories", "price": 8.95, "avg_rating": 4.4, "description": "Dri-FIT moisture-wicking headband. Keeps sweat out of your eyes during intense workouts.", "weight_g": 30, "ingredients": [], "tags": ["essentials", "value"], "dietary_tags": [], "image_url": ""},

    # ─── Wellness > Sleep (8) ───
    {"id": "neom_sleep_mist", "name": "NEOM Perfect Night's Sleep Pillow Mist", "brand": "NEOM", "vertical": "Wellness", "subcategory": "Sleep", "price": 20.00, "avg_rating": 4.7, "description": "Award-winning pillow spray with lavender, chamomile and patchouli. 97% said it helped them sleep better.", "weight_g": 30, "ingredients": ["Lavender Oil"], "tags": ["award-winning", "bestseller", "natural"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "this_works_sleep", "name": "This Works Deep Sleep Pillow Spray", "brand": "This Works", "vertical": "Wellness", "subcategory": "Sleep", "price": 19.50, "avg_rating": 4.6, "description": "The original sleep spray, clinically proven to help you fall asleep faster. Lavender, vetivert and camomile.", "weight_g": 75, "ingredients": ["Lavender Oil"], "tags": ["bestseller", "clinically-proven"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "weighted_blanket", "name": "Silentnight Wellbeing Weighted Blanket", "brand": "Silentnight", "vertical": "Wellness", "subcategory": "Sleep", "price": 40.00, "avg_rating": 4.4, "description": "6.8kg weighted blanket with glass bead filling. Reduces anxiety and promotes deeper, calmer sleep.", "weight_g": 6800, "ingredients": [], "tags": ["anxiety-relief", "value"], "dietary_tags": [], "image_url": ""},
    {"id": "sleep_supplement", "name": "Holland & Barrett Magnesium + Sleep Support", "brand": "Holland & Barrett", "vertical": "Wellness", "subcategory": "Sleep", "price": 12.99, "avg_rating": 4.3, "description": "Night-time supplement with magnesium, 5-HTP and lemon balm. Supports natural melatonin production.", "weight_g": 80, "ingredients": ["Magnesium", "Melatonin"], "tags": ["natural"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "sleep_mask_manta", "name": "Manta Sleep Mask", "brand": "Manta", "vertical": "Wellness", "subcategory": "Sleep", "price": 35.00, "avg_rating": 4.7, "description": "100% blackout sleep mask with adjustable eye cups. Zero eye pressure, infinitely adjustable fit.", "weight_g": 60, "ingredients": [], "tags": ["premium", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "calm_app_subscription", "name": "Calm Sleep Stories Collection", "brand": "Calm", "vertical": "Wellness", "subcategory": "Sleep", "price": 14.99, "avg_rating": 4.5, "description": "Digital collection of guided sleep meditations and bedtime stories narrated by soothing voices.", "weight_g": 0, "ingredients": [], "tags": ["digital", "mindfulness"], "dietary_tags": [], "image_url": ""},
    {"id": "sleep_tea_pukka", "name": "Pukka Night Time Organic Tea", "brand": "Pukka", "vertical": "Wellness", "subcategory": "Sleep", "price": 3.29, "avg_rating": 4.5, "description": "Organic herbal tea with oat flower, lavender and limeflower. A warming, soothing pre-bed ritual.", "weight_g": 36, "ingredients": ["Lavender Oil"], "tags": ["organic", "vegan", "value"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "lumie_bodyclock", "name": "Lumie Bodyclock Shine 300 Wake-Up Light", "brand": "Lumie", "vertical": "Wellness", "subcategory": "Sleep", "price": 99.00, "avg_rating": 4.6, "description": "Sunrise alarm clock that wakes you gradually with light. Clinically proven to improve energy and mood.", "weight_g": 500, "ingredients": [], "tags": ["clinically-proven", "smart-tech"], "dietary_tags": [], "image_url": ""},

    # ─── Wellness > Mindfulness (6) ───
    {"id": "meditation_cushion", "name": "Lotuscrafts Meditation Cushion Zafu", "brand": "Lotuscrafts", "vertical": "Wellness", "subcategory": "Mindfulness", "price": 32.00, "avg_rating": 4.5, "description": "Organic cotton buckwheat-filled meditation cushion. Supports correct spinal alignment during practice.", "weight_g": 2000, "ingredients": [], "tags": ["organic", "eco-friendly"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "singing_bowl", "name": "Ohm Store Tibetan Singing Bowl Set", "brand": "Ohm Store", "vertical": "Wellness", "subcategory": "Mindfulness", "price": 22.99, "avg_rating": 4.4, "description": "Handcrafted singing bowl with mallet and cushion. Rich, resonant tone for meditation and sound healing.", "weight_g": 600, "ingredients": [], "tags": ["handcrafted", "gift-worthy"], "dietary_tags": [], "image_url": ""},
    {"id": "gratitude_journal", "name": "The Five Minute Journal", "brand": "Intelligent Change", "vertical": "Wellness", "subcategory": "Mindfulness", "price": 23.95, "avg_rating": 4.6, "description": "Guided gratitude journal with morning and evening prompts. Backed by positive psychology research.", "weight_g": 350, "ingredients": [], "tags": ["bestseller", "self-improvement"], "dietary_tags": [], "image_url": ""},
    {"id": "acupressure_mat", "name": "Bed of Nails ECO Acupressure Mat", "brand": "Bed of Nails", "vertical": "Wellness", "subcategory": "Mindfulness", "price": 45.00, "avg_rating": 4.3, "description": "Swedish-designed acupressure mat with 8,820 non-toxic spikes. Releases tension and promotes relaxation.", "weight_g": 1200, "ingredients": [], "tags": ["eco-friendly", "swedish-design"], "dietary_tags": [], "image_url": ""},
    {"id": "essential_oil_set", "name": "Neal's Yard Remedies Organic Aromatherapy Trio", "brand": "Neal's Yard", "vertical": "Wellness", "subcategory": "Mindfulness", "price": 24.00, "avg_rating": 4.5, "description": "Trio of organic essential oils: Lavender, Frankincense and Geranium. For diffusing, baths and massage.", "weight_g": 90, "ingredients": ["Lavender Oil"], "tags": ["organic", "gift-worthy", "natural"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "diffuser_neom", "name": "NEOM Wellbeing Pod Essential Oil Diffuser", "brand": "NEOM", "vertical": "Wellness", "subcategory": "Mindfulness", "price": 35.00, "avg_rating": 4.4, "description": "Sleek ultrasonic diffuser that creates a fine scented mist. Covers up to 100 sq metres.", "weight_g": 400, "ingredients": [], "tags": ["smart-tech", "home-spa"], "dietary_tags": [], "image_url": ""},

    # ─── Wellness > Home Wellness (6) ───
    {"id": "neom_candle", "name": "NEOM Organics Real Luxury Scented Candle", "brand": "NEOM", "vertical": "Wellness", "subcategory": "Home Wellness", "price": 36.00, "avg_rating": 4.7, "description": "Natural wax candle with 24 pure essential oils including lavender, jasmine and Brazilian rosewood.", "weight_g": 420, "ingredients": ["Lavender Oil"], "tags": ["luxury", "natural", "gift-worthy"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "bath_salts_westlab", "name": "Westlab Mindful Bathing Salts", "brand": "Westlab", "vertical": "Wellness", "subcategory": "Home Wellness", "price": 7.99, "avg_rating": 4.4, "description": "Pure Dead Sea and Himalayan bath salts with CBD and frankincense. Transforms bath into a mindful ritual.", "weight_g": 1000, "ingredients": ["Magnesium"], "tags": ["natural", "value", "mindfulness"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "air_purifier", "name": "Levoit Core 300S Smart Air Purifier", "brand": "Levoit", "vertical": "Wellness", "subcategory": "Home Wellness", "price": 119.99, "avg_rating": 4.5, "description": "3-stage HEPA filtration for rooms up to 40 sqm. App-controlled with air quality monitoring.", "weight_g": 3500, "ingredients": [], "tags": ["smart-tech", "bestseller"], "dietary_tags": [], "image_url": ""},
    {"id": "humidifier", "name": "Pro Breeze Ultrasonic Humidifier", "brand": "Pro Breeze", "vertical": "Wellness", "subcategory": "Home Wellness", "price": 29.99, "avg_rating": 4.3, "description": "3.5L ultrasonic cool mist humidifier. Auto shut-off and 360° nozzle. Relieves dry skin and congestion.", "weight_g": 1800, "ingredients": [], "tags": ["value", "winter-essential"], "dietary_tags": [], "image_url": ""},
    {"id": "himalayan_lamp", "name": "Levoit Kana Himalayan Salt Lamp", "brand": "Levoit", "vertical": "Wellness", "subcategory": "Home Wellness", "price": 18.99, "avg_rating": 4.4, "description": "Hand-carved pink Himalayan salt lamp with dimmer switch. Emits a warm, calming amber glow.", "weight_g": 3200, "ingredients": [], "tags": ["natural", "ambience"], "dietary_tags": [], "image_url": ""},
    {"id": "aroma_roller", "name": "Scentered Sleep Well Aromatherapy Balm", "brand": "Scentered", "vertical": "Wellness", "subcategory": "Home Wellness", "price": 16.50, "avg_rating": 4.3, "description": "Portable aromatherapy balm stick with palmarosa, lavender and ylang ylang. Apply to pulse points.", "weight_g": 5, "ingredients": ["Lavender Oil"], "tags": ["travel-friendly", "natural"], "dietary_tags": ["vegan"], "image_url": ""},

    # ─── Wellness > Lifestyle (6) ───
    {"id": "collagen_supplement", "name": "Vital Proteins Collagen Peptides", "brand": "Vital Proteins", "vertical": "Wellness", "subcategory": "Lifestyle", "price": 34.00, "avg_rating": 4.5, "description": "Bovine collagen peptides powder. 20g collagen per serving for skin, hair, nails and joint support.", "weight_g": 284, "ingredients": ["Collagen", "Vitamin C"], "tags": ["bestseller", "clean-label"], "dietary_tags": ["gluten-free"], "image_url": ""},
    {"id": "multivitamin", "name": "Centrum Advance Multivitamin", "brand": "Centrum", "vertical": "Wellness", "subcategory": "Lifestyle", "price": 9.50, "avg_rating": 4.3, "description": "Complete A-Z multivitamin with 24 key nutrients. Supports immunity, energy and overall wellbeing.", "weight_g": 100, "ingredients": ["Zinc", "Biotin", "Vitamin C"], "tags": ["essentials", "value"], "dietary_tags": [], "image_url": ""},
    {"id": "turmeric_supplement", "name": "Holland & Barrett Turmeric + Black Pepper", "brand": "Holland & Barrett", "vertical": "Wellness", "subcategory": "Lifestyle", "price": 17.99, "avg_rating": 4.4, "description": "High-strength turmeric extract with piperine for enhanced absorption. Anti-inflammatory support.", "weight_g": 80, "ingredients": [], "tags": ["natural", "bestseller"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "vitamin_d", "name": "BetterYou DLux 3000 Vitamin D Oral Spray", "brand": "BetterYou", "vertical": "Wellness", "subcategory": "Lifestyle", "price": 8.95, "avg_rating": 4.6, "description": "Convenient oral spray delivering 3000 IU vitamin D3. Optimised absorption through the buccal tissue.", "weight_g": 15, "ingredients": [], "tags": ["innovation", "winter-essential"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "probiotics", "name": "Symprove Daily Probiotic", "brand": "Symprove", "vertical": "Wellness", "subcategory": "Lifestyle", "price": 21.95, "avg_rating": 4.2, "description": "Water-based liquid probiotic with 4 unique strains. Arrives alive in the gut for maximum efficacy.", "weight_g": 500, "ingredients": [], "tags": ["clinically-proven", "gut-health"], "dietary_tags": ["vegan", "gluten-free"], "image_url": ""},
    {"id": "hair_supplement", "name": "Viviscal Hair Growth Supplements", "brand": "Viviscal", "vertical": "Wellness", "subcategory": "Lifestyle", "price": 29.99, "avg_rating": 4.1, "description": "Clinically proven supplement with AminoMar, biotin and zinc. Promotes existing hair growth from within.", "weight_g": 60, "ingredients": ["Biotin", "Zinc"], "tags": ["clinically-proven"], "dietary_tags": [], "image_url": ""},

    # ─── Wellness > Gifts (6) ───
    {"id": "gift_set_neom", "name": "NEOM Wellbeing Discovery Collection", "brand": "NEOM", "vertical": "Wellness", "subcategory": "Gifts", "price": 30.00, "avg_rating": 4.6, "description": "Mini collection of 4 scented candles: Real Luxury, Happiness, Complete Bliss and Tranquillity.", "weight_g": 280, "ingredients": ["Lavender Oil"], "tags": ["gift-worthy", "bestseller"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "gift_set_rituals", "name": "Rituals The Ritual of Sakura Gift Set", "brand": "Rituals", "vertical": "Wellness", "subcategory": "Gifts", "price": 29.50, "avg_rating": 4.5, "description": "4-piece cherry blossom set: shower foam, body scrub, body cream and hand wash. Beautiful gift box.", "weight_g": 700, "ingredients": [], "tags": ["gift-worthy", "luxury"], "dietary_tags": [], "image_url": ""},
    {"id": "pamper_set_sanctuary", "name": "Sanctuary Spa My Moment of Calm Gift", "brand": "Sanctuary Spa", "vertical": "Wellness", "subcategory": "Gifts", "price": 15.00, "avg_rating": 4.4, "description": "Relaxation gift set with body wash, body butter, bath soak and sleep mist. Everything for a spa night in.", "weight_g": 500, "ingredients": ["Lavender Oil", "Magnesium"], "tags": ["gift-worthy", "value"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "eye_mask_heated", "name": "Spacemasks Self-Heating Eye Mask", "brand": "Spacemasks", "vertical": "Wellness", "subcategory": "Gifts", "price": 15.00, "avg_rating": 4.5, "description": "Box of 5 self-heating jasmine-scented eye masks. Gently warm to 40°C for 15 minutes of bliss.", "weight_g": 150, "ingredients": [], "tags": ["self-care", "stocking-filler", "bestseller"], "dietary_tags": ["vegan"], "image_url": ""},
    {"id": "care_package", "name": "The Letterbox Relaxation Gift Box", "brand": "Letterbox Gifts", "vertical": "Wellness", "subcategory": "Gifts", "price": 19.99, "avg_rating": 4.3, "description": "Letterbox-friendly gift with dark chocolate, bath bomb, candle and relaxation tea. Fits through the door.", "weight_g": 400, "ingredients": [], "tags": ["letterbox-friendly", "gift-worthy"], "dietary_tags": [], "image_url": ""},
    {"id": "bath_bomb_set", "name": "Lush Best Sellers Bath Bomb Set", "brand": "Lush", "vertical": "Wellness", "subcategory": "Gifts", "price": 32.50, "avg_rating": 4.7, "description": "Collection of 6 best-selling bath bombs including Intergalactic, Dragon's Egg and Sex Bomb.", "weight_g": 900, "ingredients": ["Lavender Oil"], "tags": ["gift-worthy", "vegan", "handmade"], "dietary_tags": ["vegan"], "image_url": ""},

    # ─── Wellness > Family Health (6) ───
    {"id": "kids_vitamins", "name": "Haliborange Kids Multivitamin Softies", "brand": "Haliborange", "vertical": "Wellness", "subcategory": "Family Health", "price": 5.99, "avg_rating": 4.4, "description": "Strawberry-flavoured chewable multivitamins for kids 3-12. With vitamins A, C, D, E and zinc.", "weight_g": 100, "ingredients": ["Zinc", "Vitamin C"], "tags": ["kids", "tasty"], "dietary_tags": [], "image_url": ""},
    {"id": "baby_bath", "name": "Childs Farm Baby Moisturiser", "brand": "Childs Farm", "vertical": "Wellness", "subcategory": "Family Health", "price": 4.75, "avg_rating": 4.6, "description": "Gentle, unfragranced moisturiser suitable from newborn. Dermatologist and paediatrician approved.", "weight_g": 250, "ingredients": ["Ceramides"], "tags": ["baby", "dermatologist-recommended", "value"], "dietary_tags": [], "image_url": ""},
    {"id": "prenatal_vitamin", "name": "Pregnacare Max Pregnancy Supplement", "brand": "Pregnacare", "vertical": "Wellness", "subcategory": "Family Health", "price": 16.50, "avg_rating": 4.3, "description": "Comprehensive pregnancy supplement with folic acid, vitamin D, omega-3 DHA and iron.", "weight_g": 100, "ingredients": ["Biotin", "Zinc"], "tags": ["pregnancy", "doctor-recommended"], "dietary_tags": [], "image_url": ""},
    {"id": "first_aid_kit", "name": "St John Ambulance Home First Aid Kit", "brand": "St John Ambulance", "vertical": "Wellness", "subcategory": "Family Health", "price": 17.99, "avg_rating": 4.5, "description": "Comprehensive 100-piece first aid kit in durable bag. Plasters, bandages, antiseptic wipes and more.", "weight_g": 450, "ingredients": [], "tags": ["essentials", "family"], "dietary_tags": [], "image_url": ""},
    {"id": "thermometer", "name": "Braun ThermoScan 7 Ear Thermometer", "brand": "Braun", "vertical": "Wellness", "subcategory": "Family Health", "price": 39.99, "avg_rating": 4.6, "description": "Professional-accuracy ear thermometer with age-precision technology. Colour-coded fever alert.", "weight_g": 200, "ingredients": [], "tags": ["medical-grade", "family"], "dietary_tags": [], "image_url": ""},
    {"id": "hand_sanitiser", "name": "Touchland Power Mist Hand Sanitiser", "brand": "Touchland", "vertical": "Wellness", "subcategory": "Family Health", "price": 9.99, "avg_rating": 4.4, "description": "Hydrating mist sanitiser with aloe vera and essential oils. 500 sprays per bottle. Rainwater scent.", "weight_g": 38, "ingredients": [], "tags": ["on-the-go", "design-led"], "dietary_tags": ["vegan"], "image_url": ""},
]

# ── Users ────────────────────────────────────────────────────

USERS = [
    {
        "id": "emma_chen", "name": "Emma Chen", "email": "emma.chen@gmail.com",
        "city": "London", "age": 28,
        "profile_type": "skincare enthusiast", "experience_level": "advanced",
        "goals": ["clear skin", "anti-aging", "hydration"],
        "dietary_restrictions": ["vegan"],
        "preferred_brands": ["The Ordinary", "CeraVe", "Drunk Elephant"],
        "skin_type": "combination",
        "context": "Dedicated skincare enthusiast who follows a multi-step routine. Prefers science-backed, vegan products. Has combination skin that gets oily in the T-zone. Interested in anti-aging prevention. Budget-conscious but splurges on serums.",
        "memory": ["Uses 10-step skincare routine", "Allergic to fragrance", "Prefers pump bottles", "Birthday in September"],
    },
    {
        "id": "james_wilson", "name": "James Wilson", "email": "jwilson@outlook.com",
        "city": "Manchester", "age": 32,
        "profile_type": "gym regular", "experience_level": "intermediate",
        "goals": ["muscle building", "weight loss"],
        "dietary_restrictions": ["gluten-free"],
        "preferred_brands": ["Myprotein", "Optimum Nutrition", "Grenade"],
        "skin_type": None,
        "context": "Regular gym-goer training 4x per week. Focused on body recomposition — building muscle while losing fat. Prefers gluten-free supplements. Currently on a caloric deficit with high protein intake.",
        "memory": ["Trains push/pull/legs split", "Lactose intolerant — prefers isolate protein", "Competes in amateur powerlifting"],
    },
    {
        "id": "sarah_patel", "name": "Sarah Patel", "email": "sarah.p@yahoo.co.uk",
        "city": "Birmingham", "age": 45,
        "profile_type": "wellness seeker", "experience_level": "beginner",
        "goals": ["better sleep", "relaxation", "anti-aging"],
        "dietary_restrictions": [],
        "preferred_brands": ["NEOM", "This Works", "ELEMIS"],
        "skin_type": "dry",
        "context": "Busy professional and mother of two struggling with sleep quality and stress. Has dry, mature skin showing signs of aging. Looking for a simplified self-care routine that actually works. Values luxury but needs convenience.",
        "memory": ["Works from home", "Prefers evening routines", "Sensitive to strong scents", "Has two children under 10"],
    },
    {
        "id": "diego_carvalho", "name": "Diego Carvalho", "email": "diego.c@gmail.com",
        "city": "Bristol", "age": 26,
        "profile_type": "fitness beginner", "experience_level": "beginner",
        "goals": ["muscle building", "endurance"],
        "dietary_restrictions": ["vegan"],
        "preferred_brands": ["Myprotein", "Huel", "Bulk"],
        "skin_type": None,
        "context": "Recently started going to the gym and looking to build a supplement stack. Vegan, so needs plant-based options. Into running as well as strength training. On a student budget.",
        "memory": ["University student", "Runs 5K twice a week", "Vegan for 3 years", "Budget is tight"],
    },
    {
        "id": "olivia_thompson", "name": "Olivia Thompson", "email": "olivia.t@icloud.com",
        "city": "Edinburgh", "age": 35,
        "profile_type": "beauty enthusiast", "experience_level": "advanced",
        "goals": ["clear skin", "hydration", "hair growth"],
        "dietary_restrictions": [],
        "preferred_brands": ["ELEMIS", "Clinique", "The INKEY List"],
        "skin_type": "sensitive",
        "context": "Beauty journalist who tests products professionally. Extremely sensitive skin — reacts to many actives. Experiencing post-partum hair thinning. Prefers fragrance-free, dermatologist-tested products.",
        "memory": ["Beauty journalist at Cosmopolitan", "Had baby 6 months ago", "Cannot use retinol — causes irritation", "Prefers fragrance-free only"],
    },
    {
        "id": "marcus_wright", "name": "Marcus Wright", "email": "marcus.w@gmail.com",
        "city": "Leeds", "age": 41,
        "profile_type": "marathon runner", "experience_level": "advanced",
        "goals": ["endurance", "weight loss", "better sleep"],
        "dietary_restrictions": [],
        "preferred_brands": ["Garmin", "SiS", "Therabody"],
        "skin_type": None,
        "context": "Competitive marathon runner training for London Marathon. Needs performance nutrition and recovery tools. Tracks everything with Garmin. Struggles with sleep before race days. Looking for tech-forward solutions.",
        "memory": ["Marathon PB: 3:12", "Runs 60km/week", "Uses Garmin Forerunner", "Race day is April 2026"],
    },
    {
        "id": "aisha_khan", "name": "Aisha Khan", "email": "aisha.k@hotmail.com",
        "city": "Leicester", "age": 23,
        "profile_type": "budget beauty", "experience_level": "beginner",
        "goals": ["clear skin", "hydration"],
        "dietary_restrictions": [],
        "preferred_brands": ["The Ordinary", "CeraVe", "The INKEY List"],
        "skin_type": "oily",
        "context": "University student on a tight budget looking for affordable, effective skincare. Has oily, acne-prone skin. Wants a simple routine that won't break the bank. Follows SkinTok for recommendations.",
        "memory": ["Student at University of Leicester", "Has acne on chin and forehead", "Max budget: £15 per product", "Follows Hyram on YouTube"],
    },
    {
        "id": "tom_reynolds", "name": "Tom Reynolds", "email": "tom.r@proton.me",
        "city": "Cardiff", "age": 38,
        "profile_type": "home gym enthusiast", "experience_level": "intermediate",
        "goals": ["muscle building"],
        "dietary_restrictions": [],
        "preferred_brands": ["Mirafit", "Wolverson", "Myprotein"],
        "skin_type": None,
        "context": "Built a home gym during lockdown and never went back. Focuses on compound lifts and functional fitness. Looking for quality equipment that lasts. Buys protein in bulk to save money.",
        "memory": ["Has garage gym", "Squats 140kg", "Prefers unflavoured protein", "Orders in bulk quarterly"],
    },
    {
        "id": "priya_sharma", "name": "Priya Sharma", "email": "priya.s@gmail.com",
        "city": "Oxford", "age": 52,
        "profile_type": "holistic wellness", "experience_level": "advanced",
        "goals": ["relaxation", "anti-aging", "better sleep"],
        "dietary_restrictions": ["vegan"],
        "preferred_brands": ["Neal's Yard", "NEOM", "Pukka"],
        "skin_type": "dry",
        "context": "Yoga teacher who practices holistic wellness. Prefers organic, natural products. Vegan lifestyle. Interested in aromatherapy and Ayurvedic approaches. Dry, mature skin needing intensive hydration.",
        "memory": ["Teaches yoga 5x/week", "Meditates daily", "Prefers organic certification", "Interested in Ayurveda"],
    },
    {
        "id": "ryan_murphy", "name": "Ryan Murphy", "email": "ryan.m@gmail.com",
        "city": "Glasgow", "age": 29,
        "profile_type": "grooming minimalist", "experience_level": "beginner",
        "goals": ["clear skin"],
        "dietary_restrictions": [],
        "preferred_brands": ["Bulldog", "Harry's", "Clinique"],
        "skin_type": "oily",
        "context": "Wants a simple, no-fuss grooming routine. Oily skin, prone to razor bumps. Just wants the basics that work. Doesn't want to spend too much time or money.",
        "memory": ["Shaves every other day", "Gets razor bumps on neck", "Wants max 3-step routine"],
    },
    {
        "id": "lucy_baker", "name": "Lucy Baker", "email": "lucy.b@gmail.com",
        "city": "Brighton", "age": 31,
        "profile_type": "new mum", "experience_level": "intermediate",
        "goals": ["better sleep", "relaxation", "hydration"],
        "dietary_restrictions": [],
        "preferred_brands": ["Lush", "Sanctuary Spa", "Childs Farm"],
        "skin_type": "dry",
        "context": "New mum of 6-month-old. Sleep-deprived and looking for quick self-care wins. Needs products safe for use around babies. Loves bath products as her main form of relaxation.",
        "memory": ["Baby is 6 months old", "Breastfeeding — avoids retinol", "Bath time is her self-care moment", "Partner is allergic to strong scents"],
    },
    {
        "id": "alex_johnson", "name": "Alex Johnson", "email": "alex.j@gmail.com",
        "city": "Liverpool", "age": 34,
        "profile_type": "gifter", "experience_level": "beginner",
        "goals": ["relaxation"],
        "dietary_restrictions": [],
        "preferred_brands": ["Rituals", "Jo Malone", "Lush"],
        "skin_type": None,
        "context": "Regularly buys gifts for partner, family and friends. Doesn't use many products personally but knows what others like. Tends to buy gift sets around birthdays and holidays.",
        "memory": ["Partner loves Jo Malone", "Mum's birthday in March", "Sister is vegan", "Prefers gift sets with nice packaging"],
    },
    {
        "id": "fatima_al_rashid", "name": "Fatima Al-Rashid", "email": "fatima.r@gmail.com",
        "city": "London", "age": 40,
        "profile_type": "luxury skincare", "experience_level": "advanced",
        "goals": ["anti-aging", "hydration"],
        "dietary_restrictions": [],
        "preferred_brands": ["ELEMIS", "La Roche-Posay", "Drunk Elephant"],
        "skin_type": "dry",
        "context": "Willing to invest in premium skincare that delivers results. Dry, mature skin with fine lines around eyes. Follows dermatologist recommendations. Interested in clinical-grade products.",
        "memory": ["Uses SPF daily", "Gets professional facials monthly", "Prefers clinical brands", "Has rosacea on cheeks"],
    },
    {
        "id": "ben_taylor", "name": "Ben Taylor", "email": "ben.t@gmail.com",
        "city": "Nottingham", "age": 21,
        "profile_type": "student athlete", "experience_level": "beginner",
        "goals": ["muscle building", "endurance"],
        "dietary_restrictions": [],
        "preferred_brands": ["Myprotein", "Nike", "Applied Nutrition"],
        "skin_type": None,
        "context": "University rugby player who needs to bulk up. Very high protein requirement. Shops mainly based on price per serving. Interested in pre-workouts for early morning training.",
        "memory": ["Plays university rugby", "Trains 6x/week", "Needs 180g protein daily", "Wakes at 5:30am for training"],
    },
    {
        "id": "helen_cross", "name": "Helen Cross", "email": "helen.c@gmail.com",
        "city": "Bath", "age": 58,
        "profile_type": "mature beauty", "experience_level": "intermediate",
        "goals": ["anti-aging", "hydration", "hair growth"],
        "dietary_restrictions": [],
        "preferred_brands": ["ELEMIS", "Clinique", "Vital Proteins"],
        "skin_type": "dry",
        "context": "Menopausal, experiencing changes in skin and hair. Looking for products that address mature skin concerns. Interested in collagen supplements. Values quality over price.",
        "memory": ["Going through menopause", "Hair has become thinner", "Prefers rich, nourishing textures", "Takes HRT"],
    },
]

# ── Orders (coherent purchase stories) ───────────────────────

ORDERS = [
    # Emma — skincare routine builder
    {"id": "ord_001", "user_id": "emma_chen", "products": ["ordinary_niacinamide", "cerave_moisturiser", "ordinary_peeling"], "total": 25.75, "status": "delivered", "order_date": "2025-10-15"},
    {"id": "ord_002", "user_id": "emma_chen", "products": ["drunk_elephant_vc", "inkey_list_ha", "la_roche_posay_spf"], "total": 86.99, "status": "delivered", "order_date": "2025-12-02"},
    {"id": "ord_003", "user_id": "emma_chen", "products": ["ordinary_retinol", "cerave_cleanser"], "total": 17.30, "status": "delivered", "order_date": "2026-02-10"},
    # James — gym supplements
    {"id": "ord_004", "user_id": "james_wilson", "products": ["mp_impact_whey", "mp_creatine", "protein_bar_grenade"], "total": 35.48, "status": "delivered", "order_date": "2025-09-20"},
    {"id": "ord_005", "user_id": "james_wilson", "products": ["optimum_gold", "bcaa_powder", "shaker_bottle"], "total": 63.97, "status": "delivered", "order_date": "2025-11-15"},
    {"id": "ord_006", "user_id": "james_wilson", "products": ["lifting_gloves", "knee_sleeves", "wrist_wraps"], "total": 96.99, "status": "delivered", "order_date": "2026-01-08"},
    # Sarah — wellness & sleep seeker
    {"id": "ord_007", "user_id": "sarah_patel", "products": ["neom_sleep_mist", "this_works_sleep", "weighted_blanket"], "total": 79.50, "status": "delivered", "order_date": "2025-10-01"},
    {"id": "ord_008", "user_id": "sarah_patel", "products": ["elemis_cleansing_balm", "clinique_moisture_surge"], "total": 78.00, "status": "delivered", "order_date": "2025-12-20"},
    {"id": "ord_009", "user_id": "sarah_patel", "products": ["neom_candle", "sleep_tea_pukka", "sleep_supplement"], "total": 52.28, "status": "shipped", "order_date": "2026-02-28"},
    # Diego — beginner vegan fitness
    {"id": "ord_010", "user_id": "diego_carvalho", "products": ["vegan_protein_huel", "resistance_bands_set", "skipping_rope"], "total": 48.96, "status": "delivered", "order_date": "2025-11-01"},
    {"id": "ord_011", "user_id": "diego_carvalho", "products": ["bulk_pre_workout", "nocco_bcaa", "peanut_butter_pip"], "total": 22.49, "status": "delivered", "order_date": "2026-01-15"},
    # Olivia — sensitive skin beauty
    {"id": "ord_012", "user_id": "olivia_thompson", "products": ["cerave_moisturiser", "cerave_cleanser", "inkey_list_ha"], "total": 30.99, "status": "delivered", "order_date": "2025-10-05"},
    {"id": "ord_013", "user_id": "olivia_thompson", "products": ["hair_supplement", "clinique_moisture_surge", "slip_pillowcase"], "total": 146.99, "status": "delivered", "order_date": "2026-01-22"},
    # Marcus — marathon runner
    {"id": "ord_014", "user_id": "marcus_wright", "products": ["garmin_forerunner", "theragun_mini", "foam_roller"], "total": 533.98, "status": "delivered", "order_date": "2025-09-10"},
    {"id": "ord_015", "user_id": "marcus_wright", "products": ["science_energy_gel", "nocco_bcaa", "gym_bag_under_armour"], "total": 35.25, "status": "delivered", "order_date": "2025-12-01"},
    {"id": "ord_016", "user_id": "marcus_wright", "products": ["neom_sleep_mist", "sleep_mask_manta", "magnesium_supplement"], "total": 67.99, "status": "delivered", "order_date": "2026-02-15"},
    # Aisha — budget skincare
    {"id": "ord_017", "user_id": "aisha_khan", "products": ["ordinary_niacinamide", "cerave_cleanser", "ordinary_peeling"], "total": 24.75, "status": "delivered", "order_date": "2025-11-10"},
    {"id": "ord_018", "user_id": "aisha_khan", "products": ["inkey_list_ha", "la_roche_posay_spf"], "total": 24.99, "status": "delivered", "order_date": "2026-01-05"},
    # Tom — home gym bulk buyer
    {"id": "ord_019", "user_id": "tom_reynolds", "products": ["kettlebell_12kg", "dumbbells_hex", "pull_up_bar"], "total": 96.94, "status": "delivered", "order_date": "2025-10-15"},
    {"id": "ord_020", "user_id": "tom_reynolds", "products": ["mp_impact_whey", "mp_creatine", "mp_shaker"], "total": 40.97, "status": "delivered", "order_date": "2025-12-10"},
    # Priya — holistic wellness
    {"id": "ord_021", "user_id": "priya_sharma", "products": ["essential_oil_set", "meditation_cushion", "neom_candle"], "total": 92.00, "status": "delivered", "order_date": "2025-09-25"},
    {"id": "ord_022", "user_id": "priya_sharma", "products": ["sleep_tea_pukka", "acupressure_mat", "diffuser_neom"], "total": 83.29, "status": "delivered", "order_date": "2025-12-15"},
    {"id": "ord_023", "user_id": "priya_sharma", "products": ["bath_salts_westlab", "aroma_roller"], "total": 24.49, "status": "shipped", "order_date": "2026-03-01"},
    # Ryan — simple grooming
    {"id": "ord_024", "user_id": "ryan_murphy", "products": ["bulldog_moisturiser", "harry_razor", "lab_series_cleanser"], "total": 43.00, "status": "delivered", "order_date": "2025-11-20"},
    {"id": "ord_025", "user_id": "ryan_murphy", "products": ["clinique_for_men", "king_c_gillette_oil"], "total": 39.99, "status": "delivered", "order_date": "2026-02-05"},
    # Lucy — new mum self-care
    {"id": "ord_026", "user_id": "lucy_baker", "products": ["lush_sleepy_lotion", "sanctuary_bath_soak", "baby_bath"], "total": 29.25, "status": "delivered", "order_date": "2025-10-20"},
    {"id": "ord_027", "user_id": "lucy_baker", "products": ["this_works_sleep", "weighted_blanket", "sleep_mask_manta"], "total": 94.50, "status": "delivered", "order_date": "2026-01-10"},
    # Alex — gift buyer
    {"id": "ord_028", "user_id": "alex_johnson", "products": ["jo_malone_lime", "gift_set_rituals"], "total": 84.50, "status": "delivered", "order_date": "2025-12-15"},
    {"id": "ord_029", "user_id": "alex_johnson", "products": ["gift_set_neom", "bath_bomb_set", "eye_mask_heated"], "total": 77.50, "status": "delivered", "order_date": "2026-02-20"},
    # Fatima — luxury skincare
    {"id": "ord_030", "user_id": "fatima_al_rashid", "products": ["elemis_cleansing_balm", "drunk_elephant_vc", "la_roche_posay_spf"], "total": 126.00, "status": "delivered", "order_date": "2025-10-10"},
    {"id": "ord_031", "user_id": "fatima_al_rashid", "products": ["clinique_moisture_surge", "ordinary_retinol", "slip_pillowcase"], "total": 122.80, "status": "delivered", "order_date": "2025-12-30"},
    {"id": "ord_032", "user_id": "fatima_al_rashid", "products": ["collagen_supplement", "hair_supplement"], "total": 63.99, "status": "shipped", "order_date": "2026-02-25"},
    # Ben — student athlete
    {"id": "ord_033", "user_id": "ben_taylor", "products": ["mp_impact_whey", "mp_creatine", "bulk_pre_workout"], "total": 49.97, "status": "delivered", "order_date": "2025-10-01"},
    {"id": "ord_034", "user_id": "ben_taylor", "products": ["protein_bar_grenade", "prime_hydration", "headband_nike"], "total": 13.95, "status": "delivered", "order_date": "2025-12-05"},
    {"id": "ord_035", "user_id": "ben_taylor", "products": ["bcaa_powder", "skipping_rope"], "total": 23.96, "status": "delivered", "order_date": "2026-02-01"},
    # Helen — mature beauty
    {"id": "ord_036", "user_id": "helen_cross", "products": ["elemis_cleansing_balm", "clinique_moisture_surge"], "total": 78.00, "status": "delivered", "order_date": "2025-09-15"},
    {"id": "ord_037", "user_id": "helen_cross", "products": ["collagen_supplement", "hair_supplement", "multivitamin"], "total": 73.49, "status": "delivered", "order_date": "2025-11-20"},
    {"id": "ord_038", "user_id": "helen_cross", "products": ["nuxe_dry_oil", "ameliorate_lotion"], "total": 53.50, "status": "delivered", "order_date": "2026-01-30"},
]

# ── Reviews ──────────────────────────────────────────────────

REVIEWS = [
    # Skincare
    {"id": "rev_001", "order_id": "ord_001", "score": 5, "comment": "The Ordinary Niacinamide is genuinely life-changing for my skin. Pores are visibly smaller within a week. Incredible value for money.", "sentiment": "positive"},
    {"id": "rev_002", "order_id": "ord_001", "score": 5, "comment": "CeraVe Moisturiser is the only thing that keeps my skin hydrated without breaking me out. Holy grail product.", "sentiment": "positive"},
    {"id": "rev_003", "order_id": "ord_002", "score": 4, "comment": "Drunk Elephant Vitamin C serum is brilliant but I wish the packaging was more stable — it oxidises quickly.", "sentiment": "positive"},
    {"id": "rev_004", "order_id": "ord_003", "score": 4, "comment": "Started with 0.5% retinol and my skin is adjusting well. Some initial dryness but results are showing.", "sentiment": "positive"},
    {"id": "rev_005", "order_id": "ord_008", "score": 5, "comment": "ELEMIS Cleansing Balm is pure luxury. Melts away everything and leaves skin so soft. Worth every penny.", "sentiment": "positive"},
    {"id": "rev_006", "order_id": "ord_012", "score": 5, "comment": "Perfect gentle cleanser for my sensitive skin. No irritation, no stripping. CeraVe has become my go-to brand.", "sentiment": "positive"},
    {"id": "rev_007", "order_id": "ord_017", "score": 5, "comment": "The Ordinary AHA BHA peeling solution gave me the smoothest skin ever! Use it twice a week max though.", "sentiment": "positive"},
    {"id": "rev_008", "order_id": "ord_018", "score": 4, "comment": "INKEY List HA serum is great for the price. Does exactly what it says. Not as luxurious as expensive brands but equally effective.", "sentiment": "positive"},
    # Fitness
    {"id": "rev_009", "order_id": "ord_004", "score": 5, "comment": "Myprotein Impact Whey in Salted Caramel — delicious and mixes perfectly. 21g protein is solid for the price.", "sentiment": "positive"},
    {"id": "rev_010", "order_id": "ord_004", "score": 5, "comment": "Creatine monohydrate from Myprotein. No frills, no flavour, just results. Strength went up within 2 weeks.", "sentiment": "positive"},
    {"id": "rev_011", "order_id": "ord_005", "score": 4, "comment": "ON Gold Standard is the benchmark for a reason. Smooth, tasty, mixes well. Pricier than Myprotein but worth it.", "sentiment": "positive"},
    {"id": "rev_012", "order_id": "ord_006", "score": 5, "comment": "SBD Knee Sleeves are incredible. Tight but supportive. Made a huge difference to my squat confidence.", "sentiment": "positive"},
    {"id": "rev_013", "order_id": "ord_010", "score": 4, "comment": "Huel Complete Protein tastes decent for plant-based. Not as smooth as whey but the macros are good.", "sentiment": "positive"},
    {"id": "rev_014", "order_id": "ord_014", "score": 5, "comment": "Garmin Forerunner 265 is a game-changer. AMOLED screen, insane battery life, training readiness score is addictive.", "sentiment": "positive"},
    {"id": "rev_015", "order_id": "ord_014", "score": 5, "comment": "Theragun Mini is worth every penny for recovery. Use it every day after runs. Fits in my gym bag perfectly.", "sentiment": "positive"},
    {"id": "rev_016", "order_id": "ord_019", "score": 4, "comment": "Wolverson kettlebells are solid quality. The handle diameter is consistent which matters for technique.", "sentiment": "positive"},
    {"id": "rev_017", "order_id": "ord_033", "score": 4, "comment": "Bulk pre-workout hits hard at 5:30am training. Good energy without the crash. The beta-alanine tingle is intense though!", "sentiment": "positive"},
    # Wellness & Sleep
    {"id": "rev_018", "order_id": "ord_007", "score": 5, "comment": "NEOM Sleep Mist genuinely helps me drift off faster. The lavender scent is calming without being overpowering.", "sentiment": "positive"},
    {"id": "rev_019", "order_id": "ord_007", "score": 4, "comment": "This Works sleep spray is decent but I prefer the NEOM one. Still, it does help create a bedtime ritual.", "sentiment": "positive"},
    {"id": "rev_020", "order_id": "ord_007", "score": 3, "comment": "Weighted blanket is nice but heavier than expected. Took a few nights to adjust. Now I sleep better though.", "sentiment": "neutral"},
    {"id": "rev_021", "order_id": "ord_021", "score": 5, "comment": "Neal's Yard essential oils are beautiful quality. The frankincense is my favourite for meditation sessions.", "sentiment": "positive"},
    {"id": "rev_022", "order_id": "ord_021", "score": 5, "comment": "NEOM candle fills the whole room with the most gorgeous scent. Burns evenly and lasts ages. Perfect for yoga.", "sentiment": "positive"},
    {"id": "rev_023", "order_id": "ord_026", "score": 5, "comment": "Lush Sleepy lotion is amazing! The lavender scent is so soothing. My baby and I both sleep better.", "sentiment": "positive"},
    {"id": "rev_024", "order_id": "ord_027", "score": 5, "comment": "Manta Sleep Mask is a revelation. Total blackout, no pressure on eyes. Best purchase I've made as a new mum.", "sentiment": "positive"},
    # Gifts & Luxury
    {"id": "rev_025", "order_id": "ord_028", "score": 5, "comment": "Jo Malone Lime Basil — my partner absolutely loves it. Beautiful bottle, long-lasting scent. The perfect gift.", "sentiment": "positive"},
    {"id": "rev_026", "order_id": "ord_029", "score": 4, "comment": "NEOM discovery set is great for trying different scents. Nice packaging too. Perfect birthday gift for my mum.", "sentiment": "positive"},
    {"id": "rev_027", "order_id": "ord_030", "score": 5, "comment": "La Roche-Posay SPF50 is the best sunscreen I've ever used. Lightweight, no white cast, perfect under makeup.", "sentiment": "positive"},
    {"id": "rev_028", "order_id": "ord_031", "score": 5, "comment": "Slip silk pillowcase is pure luxury. My hair has less breakage and my skin looks better in the morning. Never going back to cotton.", "sentiment": "positive"},
    # Grooming
    {"id": "rev_029", "order_id": "ord_024", "score": 4, "comment": "Bulldog moisturiser is simple and effective. No frills, just works. Good for guys who want the basics.", "sentiment": "positive"},
    {"id": "rev_030", "order_id": "ord_024", "score": 3, "comment": "Harry's razor is okay for the price but I still get some razor bumps on my neck. Might try a safety razor next.", "sentiment": "neutral"},
    {"id": "rev_031", "order_id": "ord_025", "score": 4, "comment": "Clinique For Men hydrator absorbs quickly and doesn't feel greasy. Good for oily skin. Fragrance-free is a plus.", "sentiment": "positive"},
    # Body Care
    {"id": "rev_032", "order_id": "ord_013", "score": 4, "comment": "Viviscal supplements — been taking for 3 months and I think I see some baby hairs growing. Fingers crossed.", "sentiment": "positive"},
    {"id": "rev_033", "order_id": "ord_038", "score": 5, "comment": "NUXE dry oil is incredible. Use it on everything — face, body, hair. Absorbs instantly and smells divine.", "sentiment": "positive"},
    {"id": "rev_034", "order_id": "ord_038", "score": 5, "comment": "Ameliorate body lotion smoothed out my KP within a week. Actual miracle product. Now a permanent staple.", "sentiment": "positive"},
    # Negative / Mixed
    {"id": "rev_035", "order_id": "ord_011", "score": 2, "comment": "NOCCO BCAA drink is too sweet and artificial-tasting for me. The caffeine kick is okay but won't repurchase.", "sentiment": "negative"},
    {"id": "rev_036", "order_id": "ord_034", "score": 2, "comment": "PRIME hydration is overhyped. Tastes fine but nothing special for the price. Marketing over substance.", "sentiment": "negative"},
    {"id": "rev_037", "order_id": "ord_016", "score": 3, "comment": "Magnesium supplement might be helping with sleep but it's hard to tell. Placebo? Will keep trying for another month.", "sentiment": "neutral"},
    {"id": "rev_038", "order_id": "ord_020", "score": 4, "comment": "Myprotein shaker works fine but the lid feels cheap compared to BlenderBottle. Does the job though.", "sentiment": "positive"},
]

# Note: ord_016 references "magnesium_supplement" which doesn't exist in PRODUCTS.
# Fix: we map it to sleep_supplement which contains magnesium
ORDER_PRODUCT_FIXUPS = {
    "magnesium_supplement": "sleep_supplement",
}

# ── Product-to-Goal mappings ─────────────────────────────────

PRODUCT_GOAL_EDGES = [
    # Clear Skin
    ("ordinary_niacinamide", "clear_skin"),
    ("cerave_cleanser", "clear_skin"),
    ("ordinary_peeling", "clear_skin"),
    ("la_roche_posay_spf", "clear_skin"),
    ("lab_series_cleanser", "clear_skin"),
    ("bulldog_moisturiser", "clear_skin"),
    # Anti-Aging
    ("ordinary_retinol", "anti_aging"),
    ("drunk_elephant_vc", "anti_aging"),
    ("elemis_cleansing_balm", "anti_aging"),
    ("collagen_supplement", "anti_aging"),
    ("bio_oil", "anti_aging"),
    # Hydration
    ("cerave_moisturiser", "hydration"),
    ("clinique_moisture_surge", "hydration"),
    ("inkey_list_ha", "hydration"),
    ("lush_sleepy_lotion", "hydration"),
    ("aveeno_lotion", "hydration"),
    # Muscle Building
    ("mp_impact_whey", "muscle_building"),
    ("optimum_gold", "muscle_building"),
    ("mp_creatine", "muscle_building"),
    ("protein_bar_grenade", "muscle_building"),
    ("bcaa_powder", "muscle_building"),
    ("vegan_protein_huel", "muscle_building"),
    # Weight Loss
    ("mp_clear_whey", "weight_loss"),
    ("science_energy_gel", "weight_loss"),
    ("skipping_rope", "weight_loss"),
    # Endurance
    ("garmin_forerunner", "endurance"),
    ("science_energy_gel", "endurance"),
    ("nocco_bcaa", "endurance"),
    ("bulk_pre_workout", "endurance"),
    ("foam_roller", "endurance"),
    # Better Sleep
    ("neom_sleep_mist", "better_sleep"),
    ("this_works_sleep", "better_sleep"),
    ("weighted_blanket", "better_sleep"),
    ("sleep_supplement", "better_sleep"),
    ("sleep_mask_manta", "better_sleep"),
    ("lush_sleepy_lotion", "better_sleep"),
    ("sleep_tea_pukka", "better_sleep"),
    ("lumie_bodyclock", "better_sleep"),
    # Relaxation
    ("neom_candle", "relaxation"),
    ("sanctuary_bath_soak", "relaxation"),
    ("essential_oil_set", "relaxation"),
    ("acupressure_mat", "relaxation"),
    ("meditation_cushion", "relaxation"),
    ("bath_bomb_set", "relaxation"),
    ("diffuser_neom", "relaxation"),
    # Hair Growth
    ("hair_supplement", "hair_growth"),
    ("collagen_supplement", "hair_growth"),
]

# ── Product-to-Ingredient mappings ───────────────────────────

PRODUCT_INGREDIENT_EDGES = [
    # Skincare actives
    ("ordinary_niacinamide", "niacinamide", "active"),
    ("ordinary_niacinamide", "zinc", "active"),
    ("cerave_moisturiser", "ceramides", "active"),
    ("cerave_moisturiser", "hyaluronic_acid", "active"),
    ("ordinary_peeling", "glycolic_acid", "active"),
    ("ordinary_peeling", "salicylic_acid", "active"),
    ("elemis_cleansing_balm", "collagen", "active"),
    ("elemis_cleansing_balm", "squalane", "trace"),
    ("la_roche_posay_spf", "spf", "active"),
    ("ordinary_retinol", "retinol", "active"),
    ("ordinary_retinol", "squalane", "active"),
    ("clinique_moisture_surge", "hyaluronic_acid", "active"),
    ("clinique_moisture_surge", "squalane", "trace"),
    ("drunk_elephant_vc", "vitamin_c", "active"),
    ("drunk_elephant_vc", "peptides", "active"),
    ("inkey_list_ha", "hyaluronic_acid", "active"),
    ("cerave_cleanser", "ceramides", "active"),
    ("cerave_cleanser", "hyaluronic_acid", "active"),
    # Grooming
    ("clinique_for_men", "hyaluronic_acid", "active"),
    ("clinique_for_men", "caffeine", "active"),
    ("aesop_post_shave", "niacinamide", "active"),
    ("lab_series_cleanser", "salicylic_acid", "active"),
    # Body care
    ("ameliorate_lotion", "glycolic_acid", "active"),
    ("ameliorate_lotion", "ceramides", "trace"),
    ("bio_oil", "retinol", "trace"),
    ("bio_oil", "vitamin_c", "trace"),
    # Fitness nutrition
    ("mp_impact_whey", "whey_protein", "active"),
    ("optimum_gold", "whey_protein", "active"),
    ("optimum_gold", "bcaa", "active"),
    ("mp_creatine", "creatine", "active"),
    ("bcaa_powder", "bcaa", "active"),
    ("bcaa_powder", "magnesium", "trace"),
    ("bulk_pre_workout", "creatine", "active"),
    ("bulk_pre_workout", "caffeine", "active"),
    ("nocco_bcaa", "bcaa", "active"),
    ("nocco_bcaa", "caffeine", "active"),
    ("grenade_shake", "whey_protein", "active"),
    ("mp_clear_whey", "whey_protein", "active"),
    # Wellness
    ("collagen_supplement", "collagen", "active"),
    ("collagen_supplement", "vitamin_c", "active"),
    ("sleep_supplement", "magnesium", "active"),
    ("sleep_supplement", "melatonin", "active"),
    ("hair_supplement", "biotin", "active"),
    ("hair_supplement", "zinc", "active"),
    ("multivitamin", "zinc", "active"),
    ("multivitamin", "biotin", "active"),
    ("multivitamin", "vitamin_c", "active"),
    # Sleep / Wellness
    ("neom_sleep_mist", "lavender", "active"),
    ("this_works_sleep", "lavender", "active"),
    ("sanctuary_bath_soak", "lavender", "active"),
    ("sanctuary_bath_soak", "magnesium", "active"),
    ("neom_candle", "lavender", "active"),
    ("bath_salts_westlab", "magnesium", "active"),
    ("essential_oil_set", "lavender", "active"),
]

# ── Related products (cross-references) ─────────────────────

RELATED_PRODUCTS = [
    ("ordinary_niacinamide", "cerave_moisturiser", "complementary"),
    ("ordinary_niacinamide", "ordinary_peeling", "same brand"),
    ("ordinary_niacinamide", "inkey_list_ha", "alternative"),
    ("cerave_moisturiser", "cerave_cleanser", "same brand"),
    ("ordinary_retinol", "drunk_elephant_vc", "complementary"),
    ("la_roche_posay_spf", "cerave_moisturiser", "complementary"),
    ("elemis_cleansing_balm", "clinique_moisture_surge", "complementary"),
    ("mp_impact_whey", "mp_creatine", "complementary"),
    ("mp_impact_whey", "optimum_gold", "alternative"),
    ("mp_impact_whey", "vegan_protein_huel", "alternative"),
    ("mp_creatine", "bcaa_powder", "complementary"),
    ("optimum_gold", "protein_bar_grenade", "complementary"),
    ("neom_sleep_mist", "this_works_sleep", "alternative"),
    ("neom_sleep_mist", "weighted_blanket", "complementary"),
    ("neom_sleep_mist", "sleep_tea_pukka", "complementary"),
    ("neom_candle", "essential_oil_set", "complementary"),
    ("neom_candle", "diffuser_neom", "complementary"),
    ("garmin_forerunner", "theragun_mini", "complementary"),
    ("foam_roller", "theragun_mini", "alternative"),
    ("collagen_supplement", "hair_supplement", "complementary"),
    ("bulldog_moisturiser", "harry_razor", "complementary"),
    ("clinique_for_men", "lab_series_cleanser", "complementary"),
    ("sanctuary_bath_soak", "bath_salts_westlab", "alternative"),
    ("lush_sleepy_lotion", "neom_sleep_mist", "complementary"),
    ("gift_set_neom", "neom_candle", "same brand"),
    ("gift_set_rituals", "rituals_body_cream", "same brand"),
    ("jo_malone_lime", "dior_sauvage", "alternative"),
    ("slip_pillowcase", "sleep_mask_manta", "complementary"),
]
