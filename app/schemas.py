"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ Admin Schemas ============

class AdminSetup(BaseModel):
    """First-time admin account setup"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class AdminLogin(BaseModel):
    """Admin login request"""
    username: str
    password: str


class AdminPasswordChange(BaseModel):
    """Change admin password"""
    current_password: str
    new_password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class AdminStatus(BaseModel):
    """Admin initialization status"""
    initialized: bool
    username: Optional[str] = None


# ============ Settings Schemas ============

class SettingsUpdate(BaseModel):
    """Update settings"""
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    test_interval_minutes: Optional[int] = Field(None, ge=5, le=1440)
    
    smtp_enabled: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    admin_email: Optional[str] = None
    
    webhook_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    
    logo_url: Optional[str] = None
    site_title: Optional[str] = None


class SettingsResponse(BaseModel):
    """Settings response (hide sensitive data for display)"""
    api_base_url: str
    api_key_masked: str  # Show only last 4 chars
    test_interval_minutes: int
    
    smtp_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password_set: bool  # Just indicate if password is set
    smtp_from: str
    smtp_use_tls: bool
    admin_email: str
    
    webhook_enabled: bool
    webhook_url: str
    
    logo_url: str
    site_title: str

    class Config:
        from_attributes = True


# ============ Model Schemas ============

class ModelCreate(BaseModel):
    """Add model to monitoring"""
    model_id: str
    display_name: str
    logo_url: Optional[str] = ""


class ModelUpdate(BaseModel):
    """Update model"""
    display_name: Optional[str] = None
    logo_url: Optional[str] = None
    enabled: Optional[bool] = None


class ModelResponse(BaseModel):
    """Model response"""
    id: int
    model_id: str
    display_name: str
    logo_url: str = ""
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AvailableModel(BaseModel):
    """Model from upstream API"""
    id: str
    owned_by: Optional[str] = None


# ============ Test Result Schemas ============

class TestResultResponse(BaseModel):
    """Individual test result"""
    id: int
    model_id: int
    model_name: str
    tested_at: datetime
    success: bool
    error_code: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class HourlyStatus(BaseModel):
    """Hourly status for progress bar"""
    hour: int  # 0-23
    timestamp: datetime
    success: Optional[bool] = None  # None means no test in that hour


class ModelStats(BaseModel):
    """Model connectivity statistics"""
    model_id: int
    model_name: str
    display_name: str
    logo_url: str = ""
    hourly_status: List[HourlyStatus]  # Last 24 hours
    rate_1d: Optional[float] = None
    rate_3d: Optional[float] = None
    rate_7d: Optional[float] = None
    rate_30d: Optional[float] = None
    last_error_code: Optional[int] = None
    last_error_message: Optional[str] = None


class ManualTestResult(BaseModel):
    """Result of manual test"""
    model_id: int
    model_name: str
    success: bool
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    tested_at: datetime


# ============ Log Schemas ============

class DebugLogResponse(BaseModel):
    """Debug log entry"""
    id: int
    timestamp: datetime
    level: str
    source: str
    message: str

    class Config:
        from_attributes = True


class LogsPage(BaseModel):
    """Paginated logs response"""
    logs: List[DebugLogResponse]
    total: int
    page: int
    page_size: int


# ============ Customer Page Schemas ============

class CustomerPageData(BaseModel):
    """Data for customer page"""
    logo_url: str
    site_title: str
    models: List[ModelStats]
    last_updated: datetime
