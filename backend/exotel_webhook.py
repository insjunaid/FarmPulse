"""
Exotel Webhook for FarmPulse.
Handles missed calls from farmers and triggers signal SMS delivery.
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from .database import SessionLocal
    from . import models
    from . import signal_generator
    from . import sms_service
except ImportError:
    from database import SessionLocal
    import models
    import signal_generator
    import sms_service

logger = logging.getLogger(__name__)

# Exotel Configuration
EXOTEL_API_KEY = os.getenv("EXOTEL_API_KEY", "")
EXOTEL_API_SECRET = os.getenv("EXOTEL_API_SECRET", "")
EXOTEL_VIRTUAL_NUMBER = os.getenv("EXOTEL_VIRTUAL_NUMBER", "")


def verify_exotel_request(
    api_key: str,
    api_secret: str
) -> bool:
    """
    Verify Exotel API credentials.
    
    Args:
        api_key: API key from Exotel
        api_secret: API secret from Exotel
    
    Returns:
        True if valid, False otherwise
    """
    if not EXOTEL_API_KEY:
        # No API key configured, allow all requests
        return True
    
    return api_key == EXOTEL_API_KEY and api_secret == EXOTEL_API_SECRET


def handle_missed_call(
    phone_number: str,
    caller_id: Optional[str] = None,
    call_duration: Optional[int] = None
) -> Dict[str, Any]:
    """
    Handle missed call from farmer.
    Triggers signal generation and SMS delivery.
    
    Args:
        phone_number: Farmer's phone number (from missed call)
        caller_id: Caller ID (optional)
        call_duration: Call duration in seconds (optional)
    
    Returns:
        Result dictionary
    """
    logger.info(f"Received missed call from {phone_number}")
    
    db = SessionLocal()
    
    try:
        # Find farmer by phone number
        farmer = db.query(models.Farmer).filter(
            models.Farmer.phone_number == phone_number
        ).first()
        
        if not farmer:
            # Farmer not registered
            logger.warning(f"Farmer not found: {phone_number}")
            return {
                "success": False,
                "error": "Farmer not registered",
                "sms_sent": False,
            }
        
        # Get farmer's preferences
        crop = farmer.primary_crop or "Tomato"
        mandi = farmer.preferred_mandi or "Mysuru"
        
        # Generate signal
        signal = signal_generator.generate_signal(crop, mandi)
        
        if not signal.get("current_price"):
            return {
                "success": False,
                "error": "Unable to generate signal",
                "sms_sent": False,
            }
        
        # Send SMS to farmer
        expected_date = signal.get("expected_date", datetime.now().date().isoformat())
        
        sms_result = sms_service.send_signal_sms(
            phone_number=phone_number,
            crop=signal.get("crop", crop),
            mandi=signal.get("mandi", mandi),
            signal=signal.get("signal", "WATCH"),
            expected_price=signal.get("expected_price", 0),
            expected_date=expected_date
        )
        
        # Log signal in database
        db_signal = models.Signal(
            crop_id=1,  # Would need to lookup actual crop ID
            mandi_id=1,  # Would need to lookup actual mandi ID
            farmer_id=farmer.id,
            signal_type=signal.get("signal", "WATCH"),
            confidence=signal.get("confidence", 0),
            current_price=signal.get("current_price"),
            expected_price=signal.get("expected_price"),
            sms_sent=sms_result.get("success", False),
            sms_sent_at=datetime.utcnow() if sms_result.get("success") else None,
        )
        
        db.add(db_signal)
        db.commit()
        
        return {
            "success": True,
            "farmer": farmer.name,
            "crop": crop,
            "mandi": mandi,
            "signal": signal.get("signal"),
            "sms_sent": sms_result.get("success", False),
            "message_id": sms_result.get("message_id"),
        }
        
    except Exception as e:
        logger.error(f"Error handling missed call: {e}")
        return {
            "success": False,
            "error": str(e),
            "sms_sent": False,
        }
    finally:
        db.close()


def handle_exotel_webhook(
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle incoming Exotel webhook.
    
    Args:
        request_data: Webhook request data
    
    Returns:
        Response dictionary
    """
    # Extract parameters from webhook
    CallFrom = request_data.get("CallFrom", "")
    CallTo = request_data.get("CallTo", "")
    CallType = request_data.get("CallType", "missed")
    DialCallDuration = request_data.get("DialCallDuration", "0")
    
    # Verify API key if configured
    api_key = request_data.get("api_key", "")
    api_secret = request_data.get("api_secret", "")
    
    if not verify_exotel_request(api_key, api_secret):
        logger.warning("Invalid Exotel API credentials")
        return {
            "success": False,
            "error": "Invalid credentials",
        }
    
    # Handle missed call
    if CallType == "missed":
        return handle_missed_call(
            phone_number=CallFrom,
            caller_id=CallTo,
            call_duration=int(DialCallDuration) if DialCallDuration else None
        )
    
    # Other call types not handled
    return {
        "success": False,
        "error": f"Call type {CallType} not supported",
    }


def initiate_callback(
    phone_number: str,
    message: str
) -> Dict[str, Any]:
    """
    Initiate callback to farmer via Exotel.
    
    Args:
        phone_number: Farmer's phone number
        message: Message to play
    
    Returns:
        Result dictionary
    """
    if not EXOTEL_API_KEY:
        logger.warning("Exotel not configured")
        return {
            "success": False,
            "error": "Exotel not configured",
        }
    
    # This would make API call to Exotel to initiate call
    logger.info(f"Initiating callback to {phone_number}")
    
    return {
        "success": True,
        "call_id": f"CALL_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "phone_number": phone_number,
    }


# Webhook endpoint format
def receive_exotel_webhook(CallFrom: str, **kwargs) -> Dict[str, Any]:
    """
    Receive Exotel webhook and process missed call.
    
    Args:
        CallFrom: Phone number of caller
        **kwargs: Additional parameters
    
    Returns:
        Response dictionary
    """
    return handle_missed_call(phone_number=CallFrom)
