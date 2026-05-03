"""
SMS Service for FarmPulse using MSG91 API.
Sends Kannada Unicode SMS to farmers in real-time.
"""
import os
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# MSG91 Configuration - loaded from environment
MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY", "")
MSG91_SENDER_ID = os.getenv("MSG91_SENDER_ID", "FARMPL")
MSG91_ROUTE = os.getenv("MSG91_ROUTE", "4")  # Transactional route
MSG91_COUNTRY = os.getenv("MSG91_COUNTRY", "91")  # India

# MSG91 API v5 base URL
MSG91_SEND_URL = "https://control.msg91.com/api/v5/flow/"
MSG91_SEND_SMS_URL = "https://api.msg91.com/api/v2/sendsms"


def send_sms(
    phone_number: str,
    message: str,
    sender_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send SMS via MSG91 API.
    
    Args:
        phone_number: Recipient phone number (with country code)
        message: Message content
        sender_id: Sender ID (optional)
    
    Returns:
        Dictionary with success status and message ID
    """
    if not MSG91_AUTH_KEY:
        logger.warning("MSG91_AUTH_KEY not set, returning mock response")
        return {
            "success": True,
            "message_id": f"MOCK_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "phone_number": phone_number,
            "message": "Mock SMS sent (API key not configured)",
            "sms_text": message,
        }
    
    # Format phone number - remove + and spaces
    phone = phone_number.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        phone = phone[1:]
    if not phone.startswith("91"):
        phone = f"91{phone}"
    
    # Use MSG91 SendSMS API v2 (more straightforward for single SMS)
    url = "https://api.msg91.com/api/v2/sendsms"
    
    payload = {
        "sender": sender_id or MSG91_SENDER_ID,
        "route": MSG91_ROUTE,
        "country": MSG91_COUNTRY,
        "sms": [
            {
                "message": message,
                "to": [phone]
            }
        ]
    }
    
    headers = {
        "authkey": MSG91_AUTH_KEY,
        "Content-Type": "application/json",
    }
    
    try:
        logger.info(f"Sending SMS to {phone} via MSG91...")
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            timeout=30
        )
        
        logger.info(f"MSG91 response status: {response.status_code}")
        logger.info(f"MSG91 response body: {response.text}")
        
        result = {}
        try:
            result = response.json()
        except:
            result = {"message": response.text}
        
        # MSG91 returns "success" type on success
        is_success = (
            response.status_code == 200 or 
            result.get("type") == "success" or
            "success" in str(result.get("message", "")).lower()
        )
        
        return {
            "success": is_success,
            "message_id": result.get("request_id", result.get("message", f"MSG91_{datetime.now().strftime('%Y%m%d%H%M%S')}")),
            "phone_number": phone_number,
            "response": result,
            "sms_text": message,
            "api_status": response.status_code,
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"SMS API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "phone_number": phone_number,
            "sms_text": message,
        }
    except Exception as e:
        logger.error(f"Unexpected SMS error: {e}")
        return {
            "success": False,
            "error": str(e),
            "phone_number": phone_number,
            "sms_text": message,
        }


def format_signal_sms(
    crop: str,
    mandi: str,
    signal: str,
    expected_price: float,
    expected_date: str,
    kannada_action: str
) -> str:
    """
    Format SMS message for signal.
    
    Args:
        crop: Crop name
        mandi: Mandi name
        signal: Signal type (HOLD/WATCH/SELL NOW)
        expected_price: Expected price per kg
        expected_date: Expected date for price
        kannada_action: Kannada action text
    
    Returns:
        Formatted SMS message
    """
    # Format date nicely
    try:
        date_obj = datetime.fromisoformat(expected_date)
        date_str = date_obj.strftime("%d %b")
    except:
        date_str = expected_date
    
    message = f"FarmPulse Alert | Crop: {crop} | Mandi: {mandi} | Signal: {signal} | Expected: Rs.{expected_price:.0f}/kg by {date_str} | {kannada_action}"
    
    return message


def send_signal_sms(
    phone_number: str,
    crop: str,
    mandi: str,
    signal: str,
    expected_price: float,
    expected_date: str
) -> Dict[str, Any]:
    """
    Send signal SMS to farmer.
    
    Args:
        phone_number: Farmer's phone number
        crop: Crop name
        mandi: Mandi name
        signal: Signal type
        expected_price: Expected price
        expected_date: Expected date
    
    Returns:
        Result dictionary
    """
    # Get Kannada action
    try:
        from . import signal_generator
    except ImportError:
        import signal_generator
    
    kannada_action = signal_generator.get_kannada_action(signal)
    
    # Format message
    message = format_signal_sms(
        crop=crop,
        mandi=mandi,
        signal=signal,
        expected_price=expected_price,
        expected_date=expected_date,
        kannada_action=kannada_action
    )
    
    # Send SMS
    result = send_sms(phone_number, message)
    
    # Save to mock log
    save_mock_sms(phone_number, message, crop, mandi, signal)
    
    # Log the result
    logger.info(f"SMS sent to {phone_number}: {signal} for {crop} at {mandi} - Success: {result.get('success')}")
    
    return result


def send_bulk_sms(
    phone_numbers: List[str],
    message: str
) -> Dict[str, Any]:
    """
    Send SMS to multiple recipients.
    
    Args:
        phone_numbers: List of phone numbers
        message: Message content
    
    Returns:
        Result dictionary
    """
    results = {
        "success": True,
        "total": len(phone_numbers),
        "sent": 0,
        "failed": 0,
        "messages": [],
    }
    
    for phone in phone_numbers:
        result = send_sms(phone, message)
        results["messages"].append(result)
        
        if result.get("success"):
            results["sent"] += 1
        else:
            results["failed"] += 1
            results["success"] = False
    
    return results


# Mock SMS for development
MOCK_SMS_SENT = []


def get_mock_sms_logs() -> List[Dict[str, Any]]:
    """
    Get logs of sent mock SMS.
    
    Returns:
        List of sent SMS logs
    """
    return MOCK_SMS_SENT


def save_mock_sms(
    phone_number: str,
    message: str,
    crop: str,
    mandi: str,
    signal: str
) -> None:
    """
    Save mock SMS to log.
    
    Args:
        phone_number: Phone number
        message: Message content
        crop: Crop name
        mandi: Mandi name
        signal: Signal type
    """
    MOCK_SMS_SENT.append({
        "phone_number": phone_number,
        "message": message,
        "crop": crop,
        "mandi": mandi,
        "signal": signal,
        "sent_at": datetime.now().isoformat(),
    })


# SMS templates in Kannada
SMS_TEMPLATE_KANNADA = {
    "Tomato": {
        "HOLD": "FarmPulse | ಟೊಮಾಟೊ: ದರ ಏರಿಕೆ ನಿರೀಕ್ಷೆ | ತಡೆಹಿಡಿರಿ",
        "WATCH": "FarmPulse | ಟೊಮಾಟೊ: ದರ ಬದಲಾವಣೆ ನೋಡಿ | ನೋಡುತ್ತಿರಿ",
        "SELL NOW": "FarmPulse | ಟೊಮಾಟೊ: ದರ ಈಗ ಮಾರಿಸಿ | ಮಾರಿಸಿ",
    },
    "Onion": {
        "HOLD": "FarmPulse | ಈರುಳ್ಳಿ: ದರ ಏರಿಕೆ ನಿರೀಕ್ಷೆ | ತಡೆಹಿಡಿರಿ",
        "WATCH": "FarmPulse | ಈರುಳ್ಳಿ: ದರ ಬದಲಾವಣೆ ನೋಡಿ | ನೋಡುತ್ತಿರಿ",
        "SELL NOW": "FarmPulse | ಈರುಳ್ಳಿ: ದರ ಕುಸಿತ | ಈಗಲೇ ಮಾರಿಸಿ",
    },
}
