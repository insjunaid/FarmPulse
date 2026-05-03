"""
AgMarkNet API Integration for fetching historical mandi prices.
Connects to AgMarkNet (Agricultural Marketing Network) API.
"""
import os
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# AgMarkNet API Configuration
AGMARKNET_BASE_URL = "https://api.agmarknet.gov.in"
AGMARKNET_API_KEY = os.getenv("AGMARKNET_API_KEY", "")

# Known Mandi Market Codes for Karnataka
MANDI_MARKET_CODES = {
    "Mysuru": "mysuru",
    "Chamarajanagar": "chamarajanagar",
    "Bangalore": "bangalore",
    "Mangalore": "mangalore",
    "Hubli-Dharwad": "hubli-dharwad",
    "Belgaum": "belgaum",
    "Bellary": "bellary",
    "Tumkur": "tumkur",
}

# Known Crops in Karnataka
CROPS = {
    "Tomato": {"id": "tomato", "commodity_id": 46},
    "Onion": {"id": "onion", "commodity_id": 23},
    "Potato": {"id": "potato", "commodity_id": 43},
    "Cabbage": {"id": "cabbage", "commodity_id": 12},
    "Carrot": {"id": "carrot", "commodity_id": 16},
    "Bean": {"id": "bean", "commodity_id": 18},
    "Chilli": {"id": "chilli", "commodity_id": 69},
    "Coriander": {"id": "coriander", "commodity_id": 24},
    "Garlic": {"id": "garlic", "commodity_id": 31},
    "Ginger": {"id": "ginger", "commodity_id": 32},
    "Green Peas": {"id": "green_peas", "commodity_id": 36},
    "Cauliflower": {"id": "cauliflower", "commodity_id": 14},
    "Brinjal": {"id": "brinjal", "commodity_id": 10},
    "Pumpkin": {"id": "pumpkin", "commodity_id": 45},
    "Banana": {"id": "banana", "commodity_id": 186},
    "Mango": {"id": "mango", "commodity_id": 131},
    "Paddy": {"id": "paddy", "commodity_id": 158},
    "Ragi": {"id": "ragi", "commodity_id": 163},
    "Jowar": {"id": "jowar", "commodity_id": 170},
    "Bajra": {"id": "bajra", "commodity_id": 171},
}


def get_state_id(state: str = "Karnataka") -> str:
    """Get state ID from AgMarkNet"""
    state_mapping = {
        "Karnataka": "KA",
        "Andhra Pradesh": "AP",
        "Tamil Nadu": "TN",
        "Maharashtra": "MH",
    }
    return state_mapping.get(state, "KA")


def fetch_daily_prices(
    commodity_id: int,
    market_code: str,
    state_code: str = "KA",
    date: Optional[datetime] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch daily prices for a specific commodity and market.
    
    Args:
        commodity_id: AgMarkNet commodity ID
        market_code: Market code (e.g., 'mysuru')
        state_code: State code (default: KA for Karnataka)
        date: Date for which to fetch prices (default: today)
    
    Returns:
        Dictionary with price data or None if failed
    """
    if date is None:
        date = datetime.now()
    
    # Format date as DD/MM/YYYY
    date_str = date.strftime("%d/%m/%Y")
    
    # Build API URL
    url = f"{AGMARKNET_BASE_URL}/service-1/price-data/daily"
    
    params = {
        "state": state_code,
        "market": market_code,
        "commodity": commodity_id,
        "date": date_str,
    }
    
    headers = {}
    if AGMARKNET_API_KEY:
        headers["X-API-Key"] = AGMARKNET_API_KEY
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success") and data.get("data"):
            return data["data"][0]
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching prices: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def fetch_price_history(
    commodity_id: int,
    market_code: str,
    state_code: str = "KA",
    days: int = 30
) -> List[Dict[str, Any]]:
    """
    Fetch price history for specified number of days.
    
    Args:
        commodity_id: AgMarkNet commodity ID
        market_code: Market code
        state_code: State code
        days: Number of days to fetch
    
    Returns:
        List of price data dictionaries
    """
    prices = []
    current_date = datetime.now()
    
    for i in range(days):
        date = current_date - timedelta(days=i)
        price_data = fetch_daily_prices(
            commodity_id=commodity_id,
            market_code=market_code,
            state_code=state_code,
            date=date
        )
        if price_data:
            prices.append(price_data)
    
    return prices


def parse_agmarknet_price(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse AgMarkNet API response to standardized format.
    
    Args:
        data: Raw price data from API
    
    Returns:
        Parsed price data dictionary
    """
    return {
        "min_price": float(data.get("min_price", 0) or 0),
        "max_price": float(data.get("max_price", 0) or 0),
        "modal_price": float(data.get("modal_price", 0) or 0),
        "arrival_quantity": float(data.get("arrival_qty", 0) or 0),
        "date": datetime.strptime(data.get("arrival_date", ""), "%d-%m-%Y").date() if data.get("arrival_date") else None,
    }


# Mock data for development and testing
MOCK_PRICE_DATA = {
    "Tomato": {
        "Mysuru": [
            {"date": "2025-04-28", "min_price": 15, "max_price": 25, "modal_price": 20, "arrival": 50},
            {"date": "2025-04-27", "min_price": 18, "max_price": 28, "modal_price": 24, "arrival": 45},
            {"date": "2025-04-26", "min_price": 20, "max_price": 32, "modal_price": 28, "arrival": 40},
            {"date": "2025-04-25", "min_price": 22, "max_price": 35, "modal_price": 30, "arrival": 38},
            {"date": "2025-04-24", "min_price": 18, "max_price": 30, "modal_price": 25, "arrival": 42},
            {"date": "2025-04-23", "min_price": 15, "max_price": 25, "modal_price": 20, "arrival": 55},
            {"date": "2025-04-22", "min_price": 12, "max_price": 20, "modal_price": 16, "arrival": 60},
            {"date": "2025-04-21", "min_price": 10, "max_price": 18, "modal_price": 14, "arrival": 65},
            {"date": "2025-04-20", "min_price": 8, "max_price": 15, "modal_price": 12, "arrival": 70},
            {"date": "2025-04-19", "min_price": 35, "max_price": 50, "modal_price": 42, "arrival": 25},
            {"date": "2025-04-18", "min_price": 30, "max_price": 45, "modal_price": 38, "arrival": 30},
            {"date": "2025-04-17", "min_price": 25, "max_price": 40, "modal_price": 32, "arrival": 35},
            {"date": "2025-04-16", "min_price": 20, "max_price": 35, "modal_price": 28, "arrival": 40},
            {"date": "2025-04-15", "min_price": 18, "max_price": 30, "modal_price": 25, "arrival": 45},
        ],
        "Chamarajanagar": [
            {"date": "2025-04-28", "min_price": 10, "max_price": 18, "modal_price": 14, "arrival": 30},
            {"date": "2025-04-27", "min_price": 12, "max_price": 20, "modal_price": 16, "arrival": 28},
            {"date": "2025-04-26", "min_price": 15, "max_price": 22, "modal_price": 18, "arrival": 25},
            {"date": "2025-04-25", "min_price": 18, "max_price": 26, "modal_price": 22, "arrival": 22},
            {"date": "2025-04-24", "min_price": 14, "max_price": 22, "modal_price": 18, "arrival": 26},
            {"date": "2025-04-23", "min_price": 10, "max_price": 18, "modal_price": 14, "arrival": 32},
            {"date": "2025-04-22", "min_price": 8, "max_price": 14, "modal_price": 11, "arrival": 35},
            {"date": "2025-04-21", "min_price": 6, "max_price": 12, "modal_price": 9, "arrival": 38},
            {"date": "2025-04-20", "min_price": 5, "max_price": 10, "modal_price": 7, "arrival": 40},
            {"date": "2025-04-19", "min_price": 25, "max_price": 38, "modal_price": 32, "arrival": 15},
            {"date": "2025-04-18", "min_price": 22, "max_price": 35, "modal_price": 28, "arrival": 18},
            {"date": "2025-04-17", "min_price": 18, "max_price": 30, "modal_price": 24, "arrival": 20},
            {"date": "2025-04-16", "min_price": 15, "max_price": 25, "modal_price": 20, "arrival": 22},
            {"date": "2025-04-15", "min_price": 12, "max_price": 20, "modal_price": 16, "arrival": 25},
        ],
    },
    "Onion": {
        "Mysuru": [
            {"date": "2025-04-28", "min_price": 20, "max_price": 30, "modal_price": 25, "arrival": 100},
            {"date": "2025-04-27", "min_price": 18, "max_price": 28, "modal_price": 23, "arrival": 95},
            {"date": "2025-04-26", "min_price": 22, "max_price": 32, "modal_price": 27, "arrival": 90},
            {"date": "2025-04-25", "min_price": 25, "max_price": 35, "modal_price": 30, "arrival": 85},
            {"date": "2025-04-24", "min_price": 28, "max_price": 38, "modal_price": 33, "arrival": 80},
        ],
        "Chamarajanagar": [
            {"date": "2025-04-28", "min_price": 15, "max_price": 25, "modal_price": 20, "arrival": 60},
            {"date": "2025-04-27", "min_price": 14, "max_price": 24, "modal_price": 19, "arrival": 55},
            {"date": "2025-04-26", "min_price": 18, "max_price": 28, "modal_price": 23, "arrival": 50},
            {"date": "2025-04-25", "min_price": 20, "max_price": 30, "modal_price": 25, "arrival": 48},
            {"date": "2025-04-24", "min_price": 22, "max_price": 32, "modal_price": 27, "arrival": 45},
        ],
    },
}


def get_mock_prices(crop: str, mandi: str) -> List[Dict[str, Any]]:
    """
    Get mock price data for testing.
    
    Args:
        crop: Crop name
        mandi: Mandi name
    
    Returns:
        List of price data
    """
    return MOCK_PRICE_DATA.get(crop, {}).get(mandi, [])
