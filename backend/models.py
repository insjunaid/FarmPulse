"""
SQLAlchemy database models for FarmPulse.
Tables: crops, mandis, prices, signals, farmers
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from .database import Base
except ImportError:
    from database import Base


class Crop(Base):
    """Crop Master Table"""
    __tablename__ = "crops"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    name_kannada = Column(String(100), nullable=True)  # Kannada name
    category = Column(String(50), nullable=True)      # Vegetable, Fruit, Grain, etc.
    
    # Relationships
    prices = relationship("Price", back_populates="crop")
    signals = relationship("Signal", back_populates="crop")


class Mandi(Base):
    """Mandi (Market) Master Table"""
    __tablename__ = "mandis"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(50), default="Karnataka")
    market_code = Column(String(20), unique=True, nullable=False)  # AgMarkNet market code
    
    # Relationships
    prices = relationship("Price", back_populates="mandi")
    signals = relationship("Signal", back_populates="mandi")


class Price(Base):
    """Daily Price Data Table"""
    __tablename__ = "prices"
    
    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    mandi_id = Column(Integer, ForeignKey("mandis.id"), nullable=False)
    date = Column(Date, nullable=False)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    modal_price = Column(Float, nullable=False)  # Most common price
    arrival_quantity = Column(Float, nullable=True)  # In quintals
    
    # Relationships
    crop = relationship("Crop", back_populates="prices")
    mandi = relationship("Mandi", back_populates="prices")


class Farmer(Base):
    """Farmer Registration Table"""
    __tablename__ = "farmers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(15), unique=True, nullable=False)
    district = Column(String(100), nullable=False)
    primary_crop = Column(String(100), nullable=True)
    preferred_mandi = Column(String(100), nullable=True)
    language = Column(String(10), default="kn")  # kn = Kannada
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    signals = relationship("Signal", back_populates="farmer")


class Signal(Base):
    """Signal Generation Table"""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    mandi_id = Column(Integer, ForeignKey("mandis.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)
    
    signal_type = Column(String(20), nullable=False)  # HOLD, WATCH, SELL NOW
    confidence = Column(Float, nullable=False)  # 0-100 percentage
    
    current_price = Column(Float, nullable=True)
    expected_price = Column(Float, nullable=True)
    price_date = Column(Date, nullable=True)  # Date for expected price
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    
    sms_sent = Column(Boolean, default=False)
    sms_sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    crop = relationship("Crop", back_populates="signals")
    mandi = relationship("Mandi", back_populates="signals")
    farmer = relationship("Farmer", back_populates="signals")
