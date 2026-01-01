"""
Database of Real Israeli Stores and Objects for Dynamic Replanning Simulation
All locations are real places in Israel that LLMs can recognize and analyze
"""

STORES_DATABASE = {
    # 🍶 חנויות שמוכרות אבל לא לחלב (2)
    "starbucks_tel_aviv": {
        "type": "coffee_shop",
        "sells_milk": False,
        "category": "beverages",
        "description": "Starbucks coffee shop at Tel Aviv Central Station",
        "address": "HaMasa Street, Tel Aviv",
        "city": "Tel Aviv",
        "price_estimate": 0,
        "color": "purple",
        "real_info": "Popular coffee chain, serves coffee and pastries, no groceries"
    },

    "moshe_butcher_rehovot": {
        "type": "butcher_shop",
        "sells_milk": False,
        "category": "food",
        "description": "Moshe's butcher shop in Rehovot, famous for fresh meat",
        "address": "Herzl Street, Rehovot",
        "city": "Rehovot",
        "price_estimate": 0,
        "color": "red",
        "real_info": "Traditional butcher shop, specializes in kosher meat products"
    },

    # 🛒 רשתות סופר (3)
    "rami_levy_jerusalem": {
        "type": "supermarket",
        "sells_milk": True,
        "category": "supermarket",
        "description": "Rami Levy supermarket in Jerusalem city center",
        "address": "King David Street, Jerusalem",
        "city": "Jerusalem",
        "price_estimate": 2.5,
        "color": "red",
        "real_info": "Discount supermarket chain, known for low prices on basic groceries"
    },

    "victory_tel_aviv": {
        "type": "supermarket",
        "sells_milk": True,
        "category": "supermarket",
        "description": "Victory supermarket at Tel Aviv central bus station",
        "address": "Levinsky Street, Tel Aviv",
        "city": "Tel Aviv",
        "price_estimate": 4.0,
        "color": "blue",
        "real_info": "Standard supermarket chain with good selection of products"
    },

    "mega_bulldog_tlv": {
        "type": "supermarket",
        "sells_milk": True,
        "category": "supermarket",
        "description": "Mega Bulldog supermarket in Tel Aviv",
        "address": "Ibn Gabirol Street, Tel Aviv",
        "city": "Tel Aviv",
        "price_estimate": 3.5,
        "color": "green",
        "real_info": "Mid-range supermarket with focus on fresh products and organic options"
    },

    # 👕 בגדים ומסעדות (5)
    "zara_tel_aviv": {
        "type": "clothing_store",
        "sells_milk": False,
        "category": "fashion",
        "description": "Zara fashion store at Azrieli Mall, Tel Aviv",
        "address": "Azrieli Center, Tel Aviv",
        "city": "Tel Aviv",
        "price_estimate": 0,
        "color": "purple",
        "real_info": "Spanish fast fashion retailer, clothing and accessories"
    },

    "mango_jerusalem": {
        "type": "clothing_store",
        "sells_milk": False,
        "category": "fashion",
        "description": "Mango clothing store in Jerusalem",
        "address": "Jaffa Street, Jerusalem",
        "city": "Jerusalem",
        "price_estimate": 0,
        "color": "yellow",
        "real_info": "Spanish fashion brand specializing in women's and men's clothing"
    },

    "burger_ranch_hod_hasharon": {
        "type": "fast_food",
        "sells_milk": False,
        "category": "restaurant",
        "description": "Burger Ranch in Hod Hasharon",
        "address": "Begin Boulevard, Hod Hasharon",
        "city": "Hod Hasharon",
        "price_estimate": 0,
        "color": "red",
        "real_info": "Popular Israeli fast food chain, known for burgers and fries"
    },

    "aroma_tlv": {
        "type": "coffee_shop",
        "sells_milk": False,
        "category": "beverages",
        "description": "Aroma coffee shop in Tel Aviv",
        "address": "Dizengoff Street, Tel Aviv",
        "city": "Tel Aviv",
        "price_estimate": 0,
        "color": "yellow",
        "real_info": "Israeli coffee chain, serves coffee, sandwiches, and light meals"
    },

    "castro_haifa": {
        "type": "clothing_store",
        "sells_milk": False,
        "category": "fashion",
        "description": "Castro fashion store in Haifa",
        "address": "Horev Center, Haifa",
        "city": "Haifa",
        "price_estimate": 0,
        "color": "purple",
        "real_info": "Israeli fashion retailer, clothing for all ages and styles"
    },

    # 🌳 אובייקטים לא מסחריים (3)
    "old_tree_jerusalem_forest": {
        "type": "nature",
        "sells_milk": False,
        "category": "nature",
        "description": "Ancient olive tree in Jerusalem forest",
        "address": "Jerusalem Forest",
        "city": "Jerusalem",
        "price_estimate": 0,
        "color": "green",
        "real_info": "Historic tree in the Jerusalem forest nature reserve"
    },

    "gan_safranim_tel_aviv": {
        "type": "park",
        "sells_milk": False,
        "category": "recreation",
        "description": "Gan Safranim playground in Tel Aviv",
        "address": "Safranim Street, Tel Aviv",
        "city": "Tel Aviv",
        "price_estimate": 0,
        "color": "blue",
        "real_info": "Popular children's playground in Tel Aviv with slides and swings"
    },

    "public_phone_booth_dizengoff": {
        "type": "infrastructure",
        "sells_milk": False,
        "category": "public_service",
        "description": "Public telephone booth on Dizengoff Street, Tel Aviv",
        "address": "Dizengoff Street, Tel Aviv",
        "city": "Tel Aviv",
        "price_estimate": 0,
        "color": "grey",
        "real_info": "Vintage public telephone booth, part of Tel Aviv's street furniture"
    },

    # חנויות נוספות מגוונות (למקרה שנצטרך יותר)
    "hummus_john_rehovot": {
        "type": "restaurant",
        "sells_milk": False,
        "category": "food",
        "description": "Hummus John in Rehovot",
        "address": "Herzl Street, Rehovot",
        "city": "Rehovot",
        "price_estimate": 0,
        "color": "yellow",
        "real_info": "Popular hummus restaurant chain in Israel"
    },

    "fox_home_tlv": {
        "type": "home_goods",
        "sells_milk": False,
        "category": "household",
        "description": "Fox Home store in Tel Aviv",
        "address": "Rothschild Boulevard, Tel Aviv",
        "city": "Tel Aviv",
        "price_estimate": 0,
        "color": "red",
        "real_info": "Home improvement and furniture store chain"
    },

    "be_tlv": {
        "type": "clothing_store",
        "sells_milk": False,
        "category": "fashion",
        "description": "BE fashion store in Tel Aviv",
        "address": "Dizengoff Street, Tel Aviv",
        "city": "Tel Aviv",
        "price_estimate": 0,
        "color": "blue",
        "real_info": "Israeli fashion brand for young adults"
    }
}

def get_random_stores(count=13, seed=None):
    """
    Get random stores from the database

    Args:
        count: Number of stores to return
        seed: Random seed for reproducibility

    Returns:
        List of store dictionaries
    """
    if seed is not None:
        import random
        random.seed(seed)

    import random
    stores_list = list(STORES_DATABASE.values())
    return random.sample(stores_list, min(count, len(stores_list)))

def get_store_by_name(name):
    """Get store information by name"""
    return STORES_DATABASE.get(name)

def get_stores_by_category(category):
    """Get all stores in a specific category"""
    return {name: data for name, data in STORES_DATABASE.items()
            if data['category'] == category}

def get_stores_by_city(city):
    """Get all stores in a specific city"""
    return {name: data for name, data in STORES_DATABASE.items()
            if data['city'] == city}
