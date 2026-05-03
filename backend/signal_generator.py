"""
Signal Generator for FarmPulse.
Generates HOLD, WATCH, or SELL NOW signals with confidence percentage.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

try:
    from . import arima_model
except ImportError:
    import arima_model

logger = logging.getLogger(__name__)

# Signal types
SIGNAL_HOLD = "HOLD"
SIGNAL_WATCH = "WATCH"
SIGNAL_SELL_NOW = "SELL NOW"


def calculate_signal(
    current_price: float,
    forecasts: List[Dict[str, Any]],
    confidence: float
) -> Dict[str, Any]:
    """
    Calculate trading signal based on forecasts.
    
    Args:
        current_price: Current market price
        forecasts: List of forecast dictionaries
        confidence: Forecast confidence percentage
    
    Returns:
        Dictionary with signal, expected price, and reasoning
    """
    if not forecasts:
        return {
            "signal": SIGNAL_WATCH,
            "expected_price": current_price,
            "confidence": confidence,
            "reason": "No forecast data available"
        }
    
    # Get the optimal price from forecasts
    optimal = arima_model.get_optimal_sell_date(forecasts)
    
    if not optimal["expected_price"]:
        return {
            "signal": SIGNAL_WATCH,
            "expected_price": current_price,
            "confidence": confidence,
            "reason": "Unable to calculate optimal price"
        }
    
    expected_price = optimal["expected_price"]
    price_change_pct = ((expected_price - current_price) / current_price) * 100
    
    # Calculate signal based on price change
    if price_change_pct >= 15:
        # Price expected to rise by 15% or more - HOLD
        signal = SIGNAL_HOLD
        reason = f"Price expected to rise by {price_change_pct:.1f}% - hold for better returns"
    elif price_change_pct >= 5:
        # Moderate increase - WATCH for confirmation
        signal = SIGNAL_WATCH
        reason = f"Price expected to rise by {price_change_pct:.1f}% - watch for confirmation"
    elif price_change_pct <= -10:
        # Significant decrease - SELL NOW
        signal = SIGNAL_SELL_NOW
        reason = f"Price expected to drop by {abs(price_change_pct):.1f}% - sell now to avoid loss"
    elif price_change_pct <= -5:
        # Moderate decrease - WATCH
        signal = SIGNAL_WATCH
        reason = f"Price expected to drop by {abs(price_change_pct):.1f}% - watch for better opportunity"
    else:
        # Stable - HOLD
        signal = SIGNAL_HOLD
        reason = f"Price expected to remain stable - hold for now"
    
    # Adjust confidence based on forecast quality
    adjusted_confidence = min(confidence * 1.1, 95)
    
    return {
        "signal": signal,
        "expected_price": expected_price,
        "expected_date": optimal.get("optimal_date"),
        "confidence": round(adjusted_confidence, 1),
        "price_change_pct": round(price_change_pct, 1),
        "reason": reason,
    }


def generate_signal(
    crop: str,
    mandi: str,
    price_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate complete signal for crop + mandi combination.
    
    Args:
        crop: Crop name
        mandi: Mandi name
        price_history: Historical price data (optional)
    
    Returns:
        Complete signal dictionary
    """
    try:
        from . import agmarknet
    except ImportError:
        import agmarknet
    
    # Get price data
    if price_history is None:
        # Try to get mock data
        price_history = agmarknet.get_mock_prices(crop, mandi)
    
    if not price_history:
        return {
            "crop": crop,
            "mandi": mandi,
            "signal": SIGNAL_WATCH,
            "expected_price": 0,
            "confidence": 0,
            "reason": "No price data available",
            "current_price": None,
            "forecasts": [],
        }
    
    # Get current price
    current_price = price_history[-1]['modal_price'] if price_history else 0
    
    # Run forecast
    forecast_result = arima_model.forecast_prices(price_history, forecast_days=7)
    
    forecasts = []
    confidence = 60.0  # Default confidence
    
    if forecast_result.get("success"):
        forecasts = forecast_result.get("forecasts", [])
        confidence = forecast_result.get("confidence", 60.0)
    else:
        # Use mock forecast
        mock = arima_model.get_mock_forecast(crop, mandi, days=7)
        forecasts = mock.get("forecasts", [])
        confidence = mock.get("confidence", 60.0)
    
    # Calculate signal
    signal_result = calculate_signal(current_price, forecasts, confidence)
    
    return {
        "crop": crop,
        "mandi": mandi,
        "signal": signal_result["signal"],
        "expected_price": signal_result["expected_price"],
        "expected_date": signal_result.get("expected_date"),
        "confidence": signal_result["confidence"],
        "price_change_pct": signal_result.get("price_change_pct"),
        "reason": signal_result["reason"],
        "current_price": current_price,
        "forecasts": forecasts,
    }


def get_signal_color(signal: str) -> str:
    """
    Get color code for signal.
    
    Args:
        signal: Signal type
    
    Returns:
        Color code: green, amber, or red
    """
    signal = signal.upper()
    
    if signal == SIGNAL_HOLD:
        return "green"
    elif signal == SIGNAL_WATCH:
        return "amber"
    elif signal == SIGNAL_SELL_NOW:
        return "red"
    else:
        return "amber"  # Default to watch


def get_all_signals() -> List[Dict[str, Any]]:
    """
    Generate signals for all crop/mandi combinations.
    
    Returns:
        List of signal dictionaries
    """
    try:
        from . import agmarknet
    except ImportError:
        import agmarknet
    
    crops = ["Tomato", "Onion", "Potato", "Cabbage", "Carrot", "Bean", "Chilli"]
    mandis = ["Mysuru", "Chamarajanagar"]
    
    signals = []
    
    for crop in crops:
        for mandi in mandis:
            signal = generate_signal(crop, mandi)
            signals.append(signal)
    
    return signals


# Kannada translations for signals
KANNADA_SIGNALS = {
    "HOLD": "ತಡೆಹಿಡಿರಿ",  # Tadihidir
    "WATCH": "ನೋಡುತ್ತಿರಿ",   # Noduttiri
    "SELL NOW": "ಈಗಲೇ ಮಾರಿಸಿ",  # Igale marisi
}

# Kannada translations for actions
KANNADA_ACTIONS = {
    "HOLD": "ದರ ಏರಿಕೆ ನಿರೀಕ್ಷೆಯಲ್ಲಿ ನಿಮ್ಮ ಬೆಳೆ ತಡೆಹಿಡಿರಿ",
    "WATCH": "ದರ ಬದಲಾವಣೆಯನ್ನು ನೋಡುತ್ತಿರಿ",
    "SELL NOW": "ದರ ಕುಸಿತದ ಮುನ್ನ ಈಗಲೇ ಮಾರಿಸಿ",
}


def get_kannada_action(signal: str) -> str:
    """
    Get Kannada action text for signal.
    
    Args:
        signal: Signal type
    
    Returns:
        Kannada action text
    """
    return KANNADA_ACTIONS.get(signal.upper(), "ನೋಡುತ್ತಿರಿ")


# Mock signals for development
def get_mock_signals() -> List[Dict[str, Any]]:
    """
    Get mock signals for development and testing.
    
    Returns:
        List of mock signal dictionaries
    """
    crops = ["Tomato", "Onion", "Potato", "Cabbage", "Carrot", "Bean", "Chilli"]
    mandis = ["Mysuru", "Chamarajanagar"]
    
    signals = []
    
    for crop in crops:
        for mandi in mandis:
            signal = generate_signal(crop, mandi)
            signals.append(signal)
    
    return signals
