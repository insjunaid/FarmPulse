"""
Scheduler for FarmPulse using APScheduler.
Schedules automatic data refresh every 15 minutes.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# APScheduler imports
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    BackgroundScheduler = None

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[object] = None


def refresh_price_data() -> None:
    """
    Refresh price data from AgMarkNet API.
    This function is called every 15 minutes.
    """
    logger.info("Refreshing price data...")
    
    try:
        from . import agmarknet, signal_generator
    except ImportError:
        import agmarknet, signal_generator
    
    try:
        # Get all crop/mandi combinations
        crops = ["Tomato", "Onion", "Potato", "Cabbage", "Carrot", "Bean", "Chilli"]
        mandis = ["Mysuru", "Chamarajanagar"]
        
        for crop in crops:
            for mandi in mandis:
                # Fetch latest prices
                prices = agmarknet.get_mock_prices(crop, mandi)
                
                if prices:
                    # Generate new signal
                    signal = signal_generator.generate_signal(crop, mandi, prices)
                    
                    logger.info(f"Updated signal: {crop} at {mandi} = {signal.get('signal')}")
        
        logger.info("Price data refresh completed")
        
    except Exception as e:
        logger.error(f"Error refreshing price data: {e}")


def refresh_farmer_signals() -> None:
    """
    Refresh signals for all registered farmers and send SMS.
    This function is called periodically.
    """
    logger.info("Refreshing farmer signals...")
    
    try:
        from .database import SessionLocal
        from . import models, signal_generator, sms_service
    except ImportError:
        from database import SessionLocal
        import models, signal_generator, sms_service
    
    db = SessionLocal()
    
    try:
        # Get all active farmers
        farmers = db.query(models.Farmer).filter(
            models.Farmer.is_active == True
        ).all()
        
        for farmer in farmers:
            try:
                # Get farmer's preferences
                crop = farmer.primary_crop or "Tomato"
                mandi = farmer.preferred_mandi or "Mysuru"
                
                # Generate signal
                signal = signal_generator.generate_signal(crop, mandi)
                
                if signal.get("current_price"):
                    # Send SMS
                    expected_date = signal.get("expected_date", datetime.now().date().isoformat())
                    
                    sms_result = sms_service.send_signal_sms(
                        phone_number=farmer.phone_number,
                        crop=signal.get("crop", crop),
                        mandi=signal.get("mandi", mandi),
                        signal=signal.get("signal", "WATCH"),
                        expected_price=signal.get("expected_price", 0),
                        expected_date=expected_date
                    )
                    
                    logger.info(f"Sent signal to {farmer.phone_number}: {signal.get('signal')}")
                    
            except Exception as e:
                logger.error(f"Error sending signal to farmer {farmer.phone_number}: {e}")
        
        logger.info(f"Farmer signals refresh completed for {len(farmers)} farmers")
        
    except Exception as e:
        logger.error(f"Error refreshing farmer signals: {e}")
    finally:
        db.close()


def start_scheduler() -> bool:
    """
    Start the APScheduler.
    
    Returns:
        True if started successfully, False otherwise
    """
    global scheduler
    
    if not APSCHEDULER_AVAILABLE:
        logger.warning("APScheduler not available")
        return False
    
    try:
        # Create scheduler
        scheduler = BackgroundScheduler()
        
        # Add job: refresh price data every 15 minutes
        scheduler.add_job(
            refresh_price_data,
            'interval',
            minutes=15,
            id='refresh_price_data',
            name='Refresh Price Data',
            replace_existing=True
        )
        
        # Add job: send daily farmer signals at 7:00 AM
        # Why once daily? Farmers don't need hourly updates.
        # They get: 1 morning SMS + on-demand via missed call + manual by FPO
        scheduler.add_job(
            refresh_farmer_signals,
            'cron',
            hour=7,
            minute=0,
            id='refresh_farmer_signals',
            name='Daily Farmer Signal (7 AM)',
            replace_existing=True
        )
        
        # Start scheduler
        scheduler.start()
        
        logger.info("Scheduler started successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return False


def stop_scheduler() -> None:
    """
    Stop the APScheduler.
    """
    global scheduler
    
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def get_scheduler_status() -> Dict[str, Any]:
    """
    Get scheduler status.
    
    Returns:
        Dictionary with scheduler status
    """
    if not scheduler:
        return {
            "running": False,
            "jobs": [],
        }
    
    jobs = []
    
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs,
    }


# Manual trigger functions
def trigger_manual_refresh() -> Dict[str, Any]:
    """
    Manually trigger price data refresh.
    
    Returns:
        Result dictionary
    """
    try:
        refresh_price_data()
        return {
            "success": True,
            "message": "Price data refreshed",
        }
    except Exception as e:
        logger.error(f"Error in manual refresh: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def trigger_manual_farmer_refresh() -> Dict[str, Any]:
    """
    Manually trigger farmer signal refresh.
    
    Returns:
        Result dictionary
    """
    try:
        refresh_farmer_signals()
        return {
            "success": True,
            "message": "Farmer signals refreshed",
        }
    except Exception as e:
        logger.error(f"Error in manual farmer refresh: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Initial data loading
def load_initial_data() -> None:
    """
    Load initial crop and mandi data.
    """
    try:
        from .database import SessionLocal
        from . import models
    except ImportError:
        from database import SessionLocal
        import models
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(models.Crop).count() > 0:
            logger.info("Initial data already exists")
            return
        
        # Add crops
        crops_data = [
            {"name": "Tomato", "name_kannada": "ಟೊಮಾಟೊ", "category": "Vegetable"},
            {"name": "Onion", "name_kannada": "ಈರುಳ್ಳಿ", "category": "Vegetable"},
            {"name": "Potato", "name_kannada": "ಆಲೂಗಡ್ಡೆ", "category": "Vegetable"},
            {"name": "Cabbage", "name_kannada": "ಎಲೆಕೋಸು", "category": "Vegetable"},
            {"name": "Carrot", "name_kannada": "ಕ್ಯಾರೆಟ್", "category": "Vegetable"},
            {"name": "Bean", "name_kannada": "ಬೀನ್ಸ್", "category": "Vegetable"},
            {"name": "Chilli", "name_kannada": "ಮೆಣಸಿನಕಾಯಿ", "category": "Spice"},
            {"name": "Coriander", "name_kannada": "ಕೊತ್ತಂಬರಿ", "category": "Herb"},
            {"name": "Garlic", "name_kannada": "ಬೆಳ್ಳುಳ್ಳಿ", "category": "Spice"},
            {"name": "Ginger", "name_kannada": "ಶುಂಠಿ", "category": "Spice"},
            {"name": "Green Peas", "name_kannada": "ಹಸಿ ಬಟಾಣಿ", "category": "Vegetable"},
            {"name": "Cauliflower", "name_kannada": "ಹೂಕೋಸು", "category": "Vegetable"},
            {"name": "Brinjal", "name_kannada": "ಬದನೆಕಾಯಿ", "category": "Vegetable"},
            {"name": "Pumpkin", "name_kannada": "ಕುಂಬಳಕಾಯಿ", "category": "Vegetable"},
            {"name": "Banana", "name_kannada": "ಬಾಳೆಹಣ್ಣು", "category": "Fruit"},
            {"name": "Mango", "name_kannada": "ಮಾವಿನಹಣ್ಣು", "category": "Fruit"},
            {"name": "Paddy", "name_kannada": "ಭತ್ತ", "category": "Cereal"},
            {"name": "Ragi", "name_kannada": "ರಾಗಿ", "category": "Cereal"},
            {"name": "Jowar", "name_kannada": "ಜೋಳ", "category": "Cereal"},
            {"name": "Bajra", "name_kannada": "ಸಜ್ಜೆ", "category": "Cereal"},
        ]
        
        for crop_data in crops_data:
            crop = models.Crop(**crop_data)
            db.add(crop)
        
        # Add mandis
        mandis_data = [
            {"name": "Mysuru", "district": "Mysuru", "state": "Karnataka", "market_code": "mysuru"},
            {"name": "Chamarajanagar", "district": "Chamarajanagar", "state": "Karnataka", "market_code": "chamarajanagar"},
            {"name": "Bangalore", "district": "Bangalore", "state": "Karnataka", "market_code": "bangalore"},
            {"name": "Mangalore", "district": "Mangalore", "state": "Karnataka", "market_code": "mangalore"},
            {"name": "Hubli-Dharwad", "district": "Dharwad", "state": "Karnataka", "market_code": "hubli-dharwad"},
            {"name": "Belgaum", "district": "Belgaum", "state": "Karnataka", "market_code": "belgaum"},
            {"name": "Bellary", "district": "Bellary", "state": "Karnataka", "market_code": "bellary"},
            {"name": "Tumkur", "district": "Tumkur", "state": "Karnataka", "market_code": "tumkur"},
        ]
        
        for mandi_data in mandis_data:
            mandi = models.Mandi(**mandi_data)
            db.add(mandi)
        
        # Add demo farmer from .env
        import os
        demo_phone = os.getenv("DEMO_FARMER_PHONE", "+919353903818")
        demo_crop = os.getenv("DEMO_FARMER_CROP", "Tomato")
        demo_district = os.getenv("DEMO_FARMER_DISTRICT", "Mysuru")
        
        demo_farmer = models.Farmer(
            name="Demo Farmer",
            phone_number=demo_phone,
            district=demo_district,
            primary_crop=demo_crop,
            preferred_mandi="Mysuru",
            language="kn",
            is_active=True,
        )
        db.add(demo_farmer)
        
        db.commit()
        logger.info("Initial data loaded successfully (including demo farmer)")
        
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")
        db.rollback()
    finally:
        db.close()
