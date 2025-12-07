"""
SQLAlchemy database models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Admin(Base):
    """Admin account - only one record allowed"""
    __tablename__ = "admin"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Settings(Base):
    """Global settings - only one record"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # API Configuration
    api_base_url = Column(String(500), default="")
    api_key = Column(String(500), default="")
    
    # Test Configuration
    test_interval_minutes = Column(Integer, default=60)
    
    # SMTP Configuration
    smtp_enabled = Column(Boolean, default=False)
    smtp_host = Column(String(255), default="")
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String(255), default="")
    smtp_password = Column(String(255), default="")
    smtp_from = Column(String(255), default="")
    smtp_use_tls = Column(Boolean, default=True)
    admin_email = Column(String(255), default="")
    
    # Webhook Configuration (DingTalk)
    webhook_enabled = Column(Boolean, default=False)
    webhook_url = Column(String(500), default="")
    
    # Display Configuration
    logo_url = Column(String(500), default="")
    site_title = Column(String(100), default="API Health Monitor")
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MonitoredModel(Base):
    """Models to monitor"""
    __tablename__ = "monitored_models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, nullable=False)  # API model identifier
    display_name = Column(String(100), nullable=False)  # Display name for customers
    logo_url = Column(String(500), default="")  # Logo URL for the model
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to test results
    test_results = relationship("TestResult", back_populates="model", cascade="all, delete-orphan")


class TestResult(Base):
    """Test result records"""
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("monitored_models.id"), nullable=False)
    tested_at = Column(DateTime, default=datetime.utcnow, index=True)
    success = Column(Boolean, nullable=False)
    error_code = Column(Integer, nullable=True)  # HTTP status code or custom error code
    error_message = Column(String(500), nullable=True)  # Brief error description
    
    # Relationship
    model = relationship("MonitoredModel", back_populates="test_results")


class DebugLog(Base):
    """Debug logs for admin viewing"""
    __tablename__ = "debug_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR
    source = Column(String(50), nullable=False)  # Module/component name
    message = Column(Text, nullable=False)
