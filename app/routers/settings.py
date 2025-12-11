"""
Settings management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Admin, Settings
from app.schemas import SettingsUpdate, SettingsResponse
from app.auth import get_current_admin
from app.notifier import send_email_notification, send_dingtalk_webhook, send_test_failure_notification
from app.scheduler import update_scheduler_interval
from app.logger import log_debug

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_or_create_settings(db: Session) -> Settings:
    """Get settings or create default if not exists"""
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/public")
async def get_public_settings(db: Session = Depends(get_db)):
    """Get public settings (site title, logo) - no authentication required"""
    settings = get_or_create_settings(db)
    return {
        "site_title": settings.site_title or "API Health Monitor",
        "logo_url": settings.logo_url or ""
    }


@router.get("", response_model=SettingsResponse)
async def get_settings(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get current settings"""
    settings = get_or_create_settings(db)
    
    # Mask API key for display
    api_key_masked = ""
    if settings.api_key:
        if len(settings.api_key) > 8:
            api_key_masked = "*" * (len(settings.api_key) - 4) + settings.api_key[-4:]
        else:
            api_key_masked = "*" * len(settings.api_key)
    
    return SettingsResponse(
        api_base_url=settings.api_base_url or "",
        api_key_masked=api_key_masked,
        test_interval_minutes=settings.test_interval_minutes,
        test_start_hour=settings.test_start_hour,
        test_start_minute=settings.test_start_minute,
        smtp_enabled=settings.smtp_enabled,
        smtp_host=settings.smtp_host or "",
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username or "",
        smtp_password_set=bool(settings.smtp_password),
        smtp_from=settings.smtp_from or "",
        smtp_use_tls=settings.smtp_use_tls,
        admin_email=settings.admin_email or "",
        webhook_enabled=settings.webhook_enabled,
        webhook_url=settings.webhook_url or "",
        custom_notification_text=settings.custom_notification_text or "",
        logo_url=settings.logo_url or "",
        site_title=settings.site_title or "API Health Monitor"
    )


@router.put("")
async def update_settings(
    data: SettingsUpdate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update settings"""
    settings = get_or_create_settings(db)
    
    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(settings, field):
            setattr(settings, field, value)
    
    db.commit()
    
    # 当任何调度相关设置改变时，重新配置调度器
    if (data.test_interval_minutes is not None or 
        data.test_start_hour is not None or 
        data.test_start_minute is not None):
        # 获取最新的设置值
        db.refresh(settings)
        from app.scheduler import update_scheduler_settings
        update_scheduler_settings(
            interval_minutes=settings.test_interval_minutes or 60,
            start_hour=settings.test_start_hour or 0,
            start_minute=settings.test_start_minute or 0
        )
    
    log_debug("INFO", "settings", "设置已更新")
    return {"message": "设置保存成功"}


@router.post("/test-email")
async def test_email(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Send a test email"""
    settings = get_or_create_settings(db)
    
    if not settings.smtp_enabled:
        raise HTTPException(status_code=400, detail="邮件通知未启用，请先保存设置")
    
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.admin_email]):
        raise HTTPException(status_code=400, detail="SMTP 配置不完整")
    
    success, error = await send_email_notification(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        smtp_from=settings.smtp_from or settings.smtp_username,
        smtp_use_tls=settings.smtp_use_tls,
        admin_email=settings.admin_email,
        subject="[测试] API 健康监控 - 邮件测试",
        body="这是一封来自 API 健康监控的测试邮件。\n\n如果您收到此邮件，说明邮件配置正确。",
        is_test=True
    )
    
    if success:
        return {"message": "测试邮件发送成功"}
    else:
        raise HTTPException(status_code=500, detail=f"邮件发送失败: {error}")


@router.post("/test-webhook")
async def test_webhook(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Send a test webhook notification"""
    settings = get_or_create_settings(db)
    
    if not settings.webhook_enabled:
        raise HTTPException(status_code=400, detail="Webhook 通知未启用，请先保存设置")
    
    if not settings.webhook_url:
        raise HTTPException(status_code=400, detail="Webhook URL 未配置")
    
    success, error = await send_dingtalk_webhook(
        webhook_url=settings.webhook_url,
        title="🔔 测试通知",
        content="这是一条来自 **API 健康监控** 的测试消息。\n\n如果您收到此通知，说明 Webhook 配置正确。",
        is_test=True
    )
    
    if success:
        return {"message": "测试消息发送成功"}
    else:
        raise HTTPException(status_code=500, detail=f"Webhook 发送失败: {error}")


@router.post("/test-notification")
async def test_notification(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Send a test failure notification (email + webhook)"""
    settings = get_or_create_settings(db)
    
    if not settings.smtp_enabled and not settings.webhook_enabled:
        raise HTTPException(status_code=400, detail="未启用任何通知渠道，请先启用邮件或 Webhook 并保存设置")
    
    success, error = await send_test_failure_notification(settings)
    
    if success:
        return {"message": "模型故障告警测试发送成功"}
    else:
        raise HTTPException(status_code=500, detail=f"发送失败: {error}")
