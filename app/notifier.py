"""
Notification services - Email (SMTP) and Webhook (DingTalk)
"""
import asyncio
from datetime import datetime
from typing import Optional
import pytz
import httpx
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.logger import log_debug


# Beijing timezone for quiet hours
BEIJING_TZ = pytz.timezone("Asia/Shanghai")


def is_quiet_hours() -> bool:
    """
    Check if current time is within quiet hours (23:00 - 08:00 Beijing time)
    During quiet hours, notifications should not be sent.
    """
    now = datetime.now(BEIJING_TZ)
    hour = now.hour
    return hour >= 23 or hour < 8


async def send_email_notification(
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    smtp_from: str,
    smtp_use_tls: bool,
    admin_email: str,
    subject: str,
    body: str,
    is_test: bool = False
) -> tuple[bool, Optional[str]]:
    """
    Send email notification via SMTP
    
    Args:
        is_test: If True, ignore quiet hours check
        
    Returns:
        Tuple of (success, error_message)
    """
    # Check quiet hours (skip for test emails)
    if not is_test and is_quiet_hours():
        log_debug("INFO", "notifier", "邮件通知跳过 - 免打扰时段")
        return True, "跳过（免打扰时段）"
    
    if not all([smtp_host, smtp_username, smtp_password, admin_email]):
        return False, "SMTP 配置不完整"
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from or smtp_username
        msg["To"] = admin_email
        
        # HTML body for better formatting
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #d32f2f;">⚠️ API 健康监控警报</h2>
            <div style="background: #fff3e0; padding: 15px; border-radius: 8px; border-left: 4px solid #ff9800;">
                {body.replace(chr(10), '<br>')}
            </div>
            <p style="color: #666; font-size: 12px; margin-top: 20px;">
                此消息由 API 健康监控系统自动发送。<br>
                发送时间：{datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}（北京时间）
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        if smtp_use_tls:
            await aiosmtplib.send(
                msg,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_username,
                password=smtp_password,
                start_tls=True
            )
        else:
            await aiosmtplib.send(
                msg,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_username,
                password=smtp_password,
                use_tls=False
            )
        
        log_debug("INFO", "notifier", f"邮件已发送至 {admin_email}")
        return True, None
        
    except Exception as e:
        error_msg = str(e)[:200]
        log_debug("ERROR", "notifier", f"邮件发送失败: {error_msg}")
        return False, error_msg


async def send_dingtalk_webhook(
    webhook_url: str,
    title: str,
    content: str,
    is_test: bool = False
) -> tuple[bool, Optional[str]]:
    """
    Send notification to DingTalk group via webhook
    
    Args:
        is_test: If True, ignore quiet hours check
        
    Returns:
        Tuple of (success, error_message)
    """
    # Check quiet hours (skip for test notifications)
    if not is_test and is_quiet_hours():
        log_debug("INFO", "notifier", "Webhook 通知跳过 - 免打扰时段")
        return True, "跳过（免打扰时段）"
    
    if not webhook_url:
        return False, "Webhook URL 未配置"
    
    # DingTalk markdown message format
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": f"## {title}\n\n{content}\n\n---\n*{datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}（北京时间）*"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("errcode") == 0:
                    log_debug("INFO", "notifier", "钉钉 Webhook 发送成功")
                    return True, None
                else:
                    error_msg = data.get("errmsg", "未知错误")
                    log_debug("ERROR", "notifier", f"钉钉返回错误: {error_msg}")
                    return False, error_msg
            else:
                error_msg = f"HTTP {response.status_code}"
                log_debug("ERROR", "notifier", f"钉钉 Webhook 请求失败: {error_msg}")
                return False, error_msg
                
    except Exception as e:
        error_msg = str(e)[:200]
        log_debug("ERROR", "notifier", f"钉钉 Webhook 错误: {error_msg}")
        return False, error_msg


async def notify_model_failure(
    settings,
    model_name: str,
    model_id: str,
    error_code: Optional[int],
    error_message: Optional[str]
):
    """
    Send notifications for model failure
    Checks if notifications are enabled before sending
    """
    # Build notification content in Chinese
    title = f"🔴 模型离线告警：{model_name}"
    
    content = f"""
**模型名称**：{model_name}
**模型ID**：`{model_id}`
**状态**：❌ 连接失败
**错误代码**：{error_code or '无'}
**错误信息**：{error_message or '未知错误'}
    """.strip()
    
    email_body = f"""
模型名称：{model_name}
模型ID：{model_id}
状态：连接失败
错误代码：{error_code or '无'}
错误信息：{error_message or '未知错误'}
    """.strip()
    
    tasks = []
    
    # Send email if enabled
    if settings.smtp_enabled:
        tasks.append(send_email_notification(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            smtp_from=settings.smtp_from,
            smtp_use_tls=settings.smtp_use_tls,
            admin_email=settings.admin_email,
            subject=f"[警报] {title}",
            body=email_body
        ))
    
    # Send webhook if enabled
    if settings.webhook_enabled:
        tasks.append(send_dingtalk_webhook(
            webhook_url=settings.webhook_url,
            title=title,
            content=content
        ))
    
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def send_test_failure_notification(settings) -> tuple[bool, Optional[str]]:
    """
    Send a test failure notification for testing purposes
    """
    title = "🔴 模型离线告警：测试模型"
    
    content = """
**模型名称**：测试模型
**模型ID**：`test-model-001`
**状态**：❌ 连接失败
**错误代码**：503
**错误信息**：这是一条测试告警消息，用于验证通知功能是否正常工作。

> 如果您收到此消息，说明通知功能配置正确。
    """.strip()
    
    email_body = """
模型名称：测试模型
模型ID：test-model-001
状态：连接失败
错误代码：503
错误信息：这是一条测试告警消息，用于验证通知功能是否正常工作。

如果您收到此邮件，说明邮件通知功能配置正确。
    """.strip()
    
    results = []
    
    # Send email if enabled
    if settings.smtp_enabled:
        success, error = await send_email_notification(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            smtp_from=settings.smtp_from,
            smtp_use_tls=settings.smtp_use_tls,
            admin_email=settings.admin_email,
            subject=f"[测试警报] {title}",
            body=email_body,
            is_test=True
        )
        results.append(("邮件", success, error))
    
    # Send webhook if enabled
    if settings.webhook_enabled:
        success, error = await send_dingtalk_webhook(
            webhook_url=settings.webhook_url,
            title=title,
            content=content,
            is_test=True
        )
        results.append(("Webhook", success, error))
    
    if not results:
        return False, "未启用任何通知渠道"
    
    failures = [f"{name}: {error}" for name, success, error in results if not success]
    if failures:
        return False, "; ".join(failures)
    
    return True, None

