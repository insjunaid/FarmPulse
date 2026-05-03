"""
ARIMA Time-Series Forecasting Model for FarmPulse.
Predicts crop prices 3-7 days ahead using ARIMA.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Try to import statsmodels, provide fallback if not available
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available, using simple forecasting")


def prepare_time_series(prices: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert price data to time-series DataFrame.
    
    Args:
        prices: List of price dictionaries with 'date' and 'modal_price'
    
    Returns:
        DataFrame with datetime index
    """
    df = pd.DataFrame(prices)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df = df.set_index('date')
    return df


def check_stationarity(series: pd.Series) -> bool:
    """
    Check if time series is stationary using Augmented Dickey-Fuller test.
    
    Args:
        series: Time series data
    
    Returns:
        True if stationary, False otherwise
    """
    if not STATSMODELS_AVAILABLE:
        # Simple check: variance and mean shouldn't change too much
        return True
    
    try:
        result = adfuller(series.dropna())
        return result[1] < 0.05  # p-value < 0.05 means stationary
    except:
        return True


class PriceForecastModel:
    """
    ARIMA-based price forecasting model.
    """
    
    def __init__(self, order: Tuple[int, int, int] = (5, 1, 2)):
        """
        Initialize the model.
        
        Args:
            order: ARIMA order (p, d, q)
        """
        self.order = order
        self.model = None
        self.fitted_model = None
        self.last_price = None
        
    def fit(self, prices: List[float]) -> bool:
        """
        Fit the ARIMA model to price data.
        
        Args:
            prices: List of historical prices (modal_price)
        
        Returns:
            True if fit successful, False otherwise
        """
        if len(prices) < 10:
            logger.warning("Not enough data points for ARIMA")
            return False
        
        self.last_price = prices[-1]
        
        if not STATSMODELS_AVAILABLE:
            # Use simple moving average for fallback
            self.last_price = np.mean(prices[-7:])
            return True
        
        try:
            # Create time series
            ts = pd.Series(prices)
            
            # Fit ARIMA model
            self.model = ARIMA(ts, order=self.order)
            self.fitted_model = self.model.fit()
            return True
        except Exception as e:
            logger.error(f"ARIMA fitting error: {e}")
            # Fallback to simple model
            self.last_price = np.mean(prices[-7:])
            return False
    
    def forecast(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Generate price forecast for specified number of days.
        
        Args:
            days: Number of days to forecast
        
        Returns:
            List of forecast dictionaries with date, price, lower, upper
        """
        forecasts = []
        today = datetime.now().date()
        
        if not STATSMODELS_AVAILABLE or self.fitted_model is None:
            # Simple forecast using trend + seasonal adjustment
            prices = self._get_simple_forecast(days)
            for i, price in enumerate(prices):
                forecast_date = today + timedelta(days=i+1)
                forecasts.append({
                    "date": forecast_date.isoformat(),
                    "price": round(price, 2),
                    "lower": round(price * 0.85, 2),
                    "upper": round(price * 1.15, 2),
                })
            return forecasts
        
        try:
            # Get ARIMA forecast
            forecast = self.fitted_model.get_forecast(steps=days)
            predictions = forecast.predicted_mean
            conf_int = forecast.conf_int()
            
            for i in range(days):
                forecast_date = today + timedelta(days=i+1)
                price = float(predictions.iloc[i])
                lower = float(conf_int.iloc[i, 0])
                upper = float(conf_int.iloc[i, 1])
                
                # Ensure positive prices
                price = max(price, 1)
                lower = max(lower, 1)
                
                forecasts.append({
                    "date": forecast_date.isoformat(),
                    "price": round(price, 2),
                    "lower": round(lower, 2),
                    "upper": round(upper, 2),
                })
            
            return forecasts
        except Exception as e:
            logger.error(f"Forecast error: {e}")
            return self._get_simple_forecast(days)
    
    def _get_simple_forecast(self, days: int) -> List[float]:
        """
        Simple forecast using moving averages and trend.
        
        Args:
            days: Number of days to forecast
        
        Returns:
            List of forecasted prices
        """
        # Use last 7 days for trend calculation
        base_price = self.last_price if self.last_price else 25
        
        # Small upward trend for demonstration
        trend = 0.02
        
        forecasts = []
        for i in range(days):
            # Add some variation
            variation = np.random.uniform(-0.05, 0.05)
            forecast_price = base_price * (1 + trend * (i+1) + variation)
            forecasts.append(max(forecast_price, 1))
        
        return forecasts
    
    def calculate_confidence(self) -> float:
        """
        Calculate forecast confidence percentage.
        
        Returns:
            Confidence percentage (0-100)
        """
        if self.fitted_model is None:
            return 60.0  # Default confidence for simple model
        
        try:
            # Use AIC as proxy for confidence
            aic = self.fitted_model.aic
            # Convert AIC to confidence (lower AIC = higher confidence)
            # Typical AIC range: 20-100
            confidence = max(50, min(95, 100 - (aic - 20)))
            return round(confidence, 1)
        except:
            return 65.0


def forecast_prices(
    price_history: List[Dict[str, Any]],
    forecast_days: int = 7
) -> Dict[str, Any]:
    """
    Main function to forecast prices.
    
    Args:
        price_history: List of price dictionaries
        forecast_days: Number of days to forecast
    
    Returns:
        Dictionary with forecast data and confidence
    """
    if not price_history:
        return {
            "success": False,
            "error": "No price data available",
            "forecasts": []
        }
    
    # Prepare time series
    df = prepare_time_series(price_history)
    prices = df['modal_price'].tolist()
    
    if len(prices) < 5:
        return {
            "success": False,
            "error": "Insufficient data for forecasting",
            "forecasts": []
        }
    
    # Create and fit model
    model = PriceForecastModel(order=(5, 1, 2))
    fit_success = model.fit(prices)
    
    if not fit_success:
        return {
            "success": False,
            "error": "Model fitting failed",
            "forecasts": []
        }
    
    # Generate forecast
    forecasts = model.forecast(days=forecast_days)
    confidence = model.calculate_confidence()
    
    return {
        "success": True,
        "confidence": confidence,
        "forecast_days": forecast_days,
        "forecasts": forecasts,
        "current_price": prices[-1] if prices else None,
    }


def calculate_price_trend(prices: List[float]) -> str:
    """
    Calculate price trend direction.
    
    Args:
        prices: List of historical prices
    
    Returns:
        Trend string: "rising", "falling", or "stable"
    """
    if len(prices) < 7:
        return "stable"
    
    recent = prices[-7:]
    earlier = prices[-14:-7] if len(prices) >= 14 else prices[:-7]
    
    if not earlier:
        return "stable"
    
    recent_avg = np.mean(recent)
    earlier_avg = np.mean(earlier)
    
    change_pct = (recent_avg - earlier_avg) / earlier_avg * 100
    
    if change_pct > 5:
        return "rising"
    elif change_pct < -5:
        return "falling"
    else:
        return "stable"


def get_optimal_sell_date(
    forecasts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Find optimal date to sell based on forecasts.
    
    Args:
        forecasts: List of forecast dictionaries
    
    Returns:
        Dictionary with optimal date and expected price
    """
    if not forecasts:
        return {
            "optimal_date": None,
            "expected_price": None,
            "reason": "No forecasts available"
        }
    
    # Find day with maximum price
    max_forecast = max(forecasts, key=lambda x: x['price'])
    
    # Find day with best price/lower risk ratio
    best_ratio = None
    best_date = None
    
    for f in forecasts:
        price = f['price']
        upper = f['upper']
        lower = f['lower']
        
        # Risk-adjusted score (higher is better)
        margin = upper - lower
        score = price / (margin + 1)  # Add 1 to avoid division by zero
        
        if best_ratio is None or score > best_ratio:
            best_ratio = score
            best_date = f
    
    return {
        "optimal_date": best_date['date'],
        "expected_price": best_date['price'],
        "confidence_band": {
            "lower": best_date['lower'],
            "upper": best_date['upper'],
        },
        "reason": f"Best risk-adjusted price on {best_date['date']}"
    }


# Mock forecast for development
def get_mock_forecast(crop: str, mandi: str, days: int = 7) -> Dict[str, Any]:
    """
    Generate mock forecast for testing.
    
    Args:
        crop: Crop name
        mandi: Mandi name
        days: Number of days to forecast
    
    Returns:
        Mock forecast dictionary
    """
    try:
        from . import agmarknet
    except ImportError:
        import agmarknet
    
    # Get mock prices
    prices = agmarknet.get_mock_prices(crop, mandi)
    
    if not prices:
        # Generate random prices
        today = datetime.now().date()
        forecasts = []
        base_price = 25
        
        for i in range(days):
            date = today + timedelta(days=i+1)
            price = base_price * (1 + np.random.uniform(-0.1, 0.15) * (i+1))
            lower = price * 0.85
            upper = price * 1.15
            
            forecasts.append({
                "date": date.isoformat(),
                "price": round(price, 2),
                "lower": round(lower, 2),
                "upper": round(upper, 2),
            })
        
        return {
            "success": True,
            "confidence": 78.0,
            "forecast_days": days,
            "forecasts": forecasts,
            "current_price": base_price,
        }
    
    # Use actual prices for forecast
    result = forecast_prices(prices, days)
    
    if result.get("success"):
        return result
    
    # Return mock if real forecast fails
    today = datetime.now().date()
    forecasts = []
    base_price = prices[-1]['modal_price'] if prices else 25
    
    for i in range(days):
        date = today + timedelta(days=i+1)
        price = base_price * (1 + 0.02 * (i+1))
        lower = price * 0.85
        upper = price * 1.15
        
        forecasts.append({
            "date": date.isoformat(),
            "price": round(price, 2),
            "lower": round(lower, 2),
            "upper": round(upper, 2),
        })
    
    return {
        "success": True,
        "confidence": 78.0,
        "forecast_days": days,
        "forecasts": forecasts,
        "current_price": base_price,
    }
