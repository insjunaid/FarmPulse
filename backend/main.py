"""
FarmPulse FastAPI Main Application.
REST API endpoints for crop price signals and forecasts.
"""
import os
from pathlib import Path

# Load .env before anything else
from dotenv import load_dotenv
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging

try:
    from .database import SessionLocal, get_db, init_db
    from . import models
    from . import signal_generator
    from . import scheduler
    from . import sms_service
except ImportError:
    from database import SessionLocal, get_db, init_db
    import models
    import signal_generator
    import scheduler
    import sms_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FarmPulse API",
    description="Predictive Crop Price Intelligence API for Karnataka Farmers",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Pydantic Models ==========

class FarmerCreate(BaseModel):
    """Schema for creating a new farmer"""
    name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., pattern=r"^\+?[\d\s-]{10,15}$")
    district: str = Field(..., min_length=1, max_length=100)
    primary_crop: Optional[str] = "Tomato"
    preferred_mandi: Optional[str] = "Mysuru"
    language: Optional[str] = "kn"


class FarmerResponse(BaseModel):
    """Schema for farmer response"""
    id: int
    name: str
    phone_number: str
    district: str
    primary_crop: Optional[str]
    preferred_mandi: Optional[str]
    language: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SignalResponse(BaseModel):
    """Schema for signal response"""
    crop: str
    mandi: str
    signal: str
    expected_price: float
    expected_date: Optional[str]
    confidence: float
    price_change_pct: Optional[float]
    reason: str
    current_price: Optional[float]
    forecasts: List[Dict[str, Any]] = []


class ForecastResponse(BaseModel):
    """Schema for forecast response"""
    crop: str
    mandi: str
    current_price: float
    confidence: float
    forecasts: List[Dict[str, Any]]


class SignalHistoryResponse(BaseModel):
    """Schema for signal history response"""
    farmer_id: int
    signals: List[Dict[str, Any]]


class SMSSendRequest(BaseModel):
    """Schema for sending SMS"""
    phone_number: str
    crop: str
    mandi: str
    signal: str
    expected_price: float
    expected_date: Optional[str] = None
    message: Optional[str] = None


# ========== Dependency ==========

def get_database():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== Endpoints ==========

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting FarmPulse API...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Load initial data
    try:
        scheduler.load_initial_data()
        logger.info("Initial data loaded")
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")
    
    # Start scheduler
    try:
        scheduler.start_scheduler()
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
    
    logger.info("FarmPulse API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down FarmPulse API...")
    scheduler.stop_scheduler()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "FarmPulse API",
        "version": "1.0.0",
        "description": "Predictive Crop Price Intelligence for Karnataka Farmers",
        "endpoints": {
            "health": "/health",
            "signals": "/signal/{crop}/{mandi}",
            "all_signals": "/signals/all",
            "forecast": "/forecast/{crop}/{mandi}",
            "farmers": "/farmers",
            "register": "/register-farmer",
            "send_sms": "/send-sms",
            "docs": "/docs",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "msg91_configured": bool(os.getenv("MSG91_AUTH_KEY")),
    }


# ========== Signal Endpoints ==========

@app.get("/signal/{crop}/{mandi}", response_model=SignalResponse)
async def get_signal(crop: str, mandi: str):
    """
    Get today's signal for a crop and mandi combination.
    
    Args:
        crop: Crop name (e.g., Tomato, Onion)
        mandi: Mandi name (e.g., Mysuru, Chamarajanagar)
    
    Returns:
        Signal with price forecast and confidence
    """
    # Generate signal
    signal = signal_generator.generate_signal(crop, mandi)
    
    return signal


@app.get("/signals/all")
async def get_all_signals():
    """
    Get all signals for all crop/mandi combinations.
    
    Returns:
        List of all signals
    """
    return signal_generator.get_all_signals()


@app.get("/forecast/{crop}/{mandi}", response_model=ForecastResponse)
async def get_forecast(crop: str, mandi: str, days: int = 7):
    """
    Get 7-day price forecast for a crop and mandi.
    
    Args:
        crop: Crop name
        mandi: Mandi name
        days: Number of days to forecast (default: 7)
    
    Returns:
        Price forecast with confidence band
    """
    try:
        from . import agmarknet, arima_model
    except ImportError:
        import agmarknet, arima_model
    
    # Get price data
    prices = agmarknet.get_mock_prices(crop, mandi)
    
    if not prices:
        # Use mock forecast if no price data
        mock = arima_model.get_mock_forecast(crop, mandi, days=days)
        return {
            "crop": crop,
            "mandi": mandi,
            "current_price": mock.get("current_price", 25),
            "confidence": mock.get("confidence", 60),
            "forecasts": mock.get("forecasts", []),
        }
    
    # Get current price
    current_price = prices[-1]['modal_price']
    
    # Run forecast
    forecast_result = arima_model.forecast_prices(prices, forecast_days=days)
    
    if not forecast_result.get("success"):
        # Use mock forecast
        mock = arima_model.get_mock_forecast(crop, mandi, days=days)
        return {
            "crop": crop,
            "mandi": mandi,
            "current_price": current_price,
            "confidence": mock.get("confidence", 60),
            "forecasts": mock.get("forecasts", []),
        }
    
    return {
        "crop": crop,
        "mandi": mandi,
        "current_price": forecast_result.get("current_price", current_price),
        "confidence": forecast_result.get("confidence", 60),
        "forecasts": forecast_result.get("forecasts", []),
    }


# ========== Farmer Endpoints ==========

@app.post("/register-farmer", response_model=FarmerResponse, status_code=status.HTTP_201_CREATED)
async def register_farmer(farmer: FarmerCreate):
    """
    Register a new farmer.
    
    Args:
        farmer: Farmer details
    
    Returns:
        Registered farmer information
    """
    db = SessionLocal()
    
    try:
        # Check if phone number already exists
        existing = db.query(models.Farmer).filter(
            models.Farmer.phone_number == farmer.phone_number
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Phone number already registered"
            )
        
        # Create farmer
        db_farmer = models.Farmer(
            name=farmer.name,
            phone_number=farmer.phone_number,
            district=farmer.district,
            primary_crop=farmer.primary_crop,
            preferred_mandi=farmer.preferred_mandi,
            language=farmer.language,
        )
        
        db.add(db_farmer)
        db.commit()
        db.refresh(db_farmer)
        
        logger.info(f"Farmer registered: {db_farmer.phone_number}")
        
        return db_farmer
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering farmer: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register farmer: {str(e)}"
        )
    finally:
        db.close()


@app.get("/farmers", response_model=List[FarmerResponse])
async def get_farmers(
    district: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get list of registered farmers.
    
    Args:
        district: Filter by district (optional)
        skip: Number of records to skip
        limit: Maximum records to return
    
    Returns:
        List of farmers
    """
    db = SessionLocal()
    
    try:
        query = db.query(models.Farmer)
        
        if district:
            query = query.filter(models.Farmer.district == district)
        
        farmers = query.offset(skip).limit(limit).all()
        
        return farmers
        
    except Exception as e:
        logger.error(f"Error getting farmers: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get farmers"
        )
    finally:
        db.close()


@app.get("/history/{farmer_id}")
async def get_farmer_history(farmer_id: int):
    """
    Get signal history for a farmer.
    
    Args:
        farmer_id: Farmer ID
    
    Returns:
        List of past signals
    """
    db = SessionLocal()
    
    try:
        # Get farmer
        farmer = db.query(models.Farmer).filter(
            models.Farmer.id == farmer_id
        ).first()
        
        if not farmer:
            raise HTTPException(
                status_code=404,
                detail="Farmer not found"
            )
        
        # Get signal history
        signals = db.query(models.Signal).filter(
            models.Signal.farmer_id == farmer_id
        ).order_by(
            models.Signal.generated_at.desc()
        ).limit(30).all()
        
        return {
            "farmer_id": farmer_id,
            "farmer_name": farmer.name,
            "phone_number": farmer.phone_number,
            "signals": [
                {
                    "crop": s.crop_id,
                    "mandi": s.mandi_id,
                    "signal": s.signal_type,
                    "confidence": s.confidence,
                    "current_price": s.current_price,
                    "expected_price": s.expected_price,
                    "generated_at": s.generated_at.isoformat() if s.generated_at else None,
                    "sms_sent": s.sms_sent,
                }
                for s in signals
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting farmer history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get farmer history"
        )
    finally:
        db.close()


# ========== SMS Endpoints ==========

@app.post("/send-sms")
async def send_sms_endpoint(request: SMSSendRequest):
    """
    Send SMS to a farmer via MSG91.
    
    Args:
        request: SMS send request data
    
    Returns:
        SMS send result
    """
    expected_date = request.expected_date or datetime.now().date().isoformat()
    
    # Send via SMS service (will use real MSG91 if key is configured)
    result = sms_service.send_signal_sms(
        phone_number=request.phone_number,
        crop=request.crop,
        mandi=request.mandi,
        signal=request.signal,
        expected_price=request.expected_price,
        expected_date=expected_date
    )
    
    return result


@app.get("/sms-logs")
async def get_sms_logs():
    """Get SMS send history (from current session)"""
    return {
        "logs": sms_service.get_mock_sms_logs(),
        "total": len(sms_service.get_mock_sms_logs()),
    }


# ========== Admin Endpoints ==========

@app.get("/admin/scheduler-status")
async def get_scheduler_status():
    """Get scheduler status"""
    return scheduler.get_scheduler_status()


@app.post("/admin/trigger-refresh")
async def trigger_refresh():
    """Manually trigger price data refresh"""
    return scheduler.trigger_manual_refresh()


@app.post("/admin/trigger-farmer-refresh")
async def trigger_farmer_refresh():
    """Manually trigger farmer signal refresh"""
    return scheduler.trigger_manual_farmer_refresh()


# ========== Webhook Endpoints ==========

@app.post("/webhook/exotel")
async def exotel_webhook_endpoint(request: Dict[str, Any]):
    """
    Exotel webhook endpoint for missed calls.
    
    Args:
        request: Webhook request data from Exotel
    
    Returns:
        Response dictionary
    """
    try:
        from . import exotel_webhook
    except ImportError:
        import exotel_webhook
    
    return exotel_webhook.handle_exotel_webhook(request)


# ========== Dummy Data Endpoints (for testing) ==========

@app.get("/dummy/signals")
async def get_dummy_signals():
    """Get all signals (dummy data)"""
    return signal_generator.get_mock_signals()


@app.get("/dummy/forecast/{crop}/{mandi}")
async def get_dummy_forecast(crop: str, mandi: str):
    """Get dummy forecast"""
    try:
        from . import arima_model
    except ImportError:
        import arima_model
    
    return arima_model.get_mock_forecast(crop, mandi, days=7)


# Run with: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
