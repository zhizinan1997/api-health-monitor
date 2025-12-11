"""
Scheduled task runner for model health checks
"""
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Settings, MonitoredModel, TestResult
from app.api_client import test_model_connectivity
from app.notifier import notify_model_failure
from app.logger import log_debug

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
_current_interval = None
_last_run_time = None  # 记录上次执行时间（上海时区）


def get_settings(db: Session) -> Settings:
    """Get current settings from database"""
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


async def run_scheduled_tests():
    """Run connectivity tests for all enabled models with retest redundancy.
    
    Two-phase approach to prevent false positives from network glitches:
    1. First phase: Test all models, record failures (no notifications)
    2. Wait 3 minutes
    3. Second phase: Retest only failed models
    4. Send notifications only for models that fail both tests
    """
    import asyncio
    import pytz
    
    global _last_run_time
    # 记录本次执行时间（上海时区）
    shanghai_tz = pytz.timezone("Asia/Shanghai")
    _last_run_time = datetime.now(shanghai_tz)
    
    log_debug("INFO", "scheduler", "Starting scheduled model tests (Phase 1)")
    
    db = SessionLocal()
    try:
        settings = get_settings(db)
        
        if not settings.api_base_url or not settings.api_key:
            log_debug("WARNING", "scheduler", "API not configured, skipping tests")
            return
        
        models = db.query(MonitoredModel).filter(MonitoredModel.enabled == True).all()
        
        if not models:
            log_debug("INFO", "scheduler", "No models to test")
            return
        
        log_debug("INFO", "scheduler", f"Phase 1: Testing {len(models)} models")
        
        # Phase 1: Test all models, collect failures
        failed_models = []
        
        for model in models:
            success, error_code, error_message = await test_model_connectivity(
                api_base_url=settings.api_base_url,
                api_key=settings.api_key,
                model_id=model.model_id
            )
            
            # Save test result
            result = TestResult(
                model_id=model.id,
                tested_at=datetime.utcnow(),
                success=success,
                error_code=error_code,
                error_message=error_message
            )
            db.add(result)
            
            # Track failures for retest (don't notify yet)
            if not success:
                failed_models.append({
                    'model': model,
                    'error_code': error_code,
                    'error_message': error_message
                })
        
        db.commit()
        
        # If no failures, we're done
        if not failed_models:
            log_debug("INFO", "scheduler", f"Phase 1 completed: All {len(models)} models passed")
            return
        
        log_debug("INFO", "scheduler", f"Phase 1: {len(failed_models)} models failed, waiting 3 minutes for retest")
        
        # Wait 3 minutes before retest
        await asyncio.sleep(180)
        
        # Phase 2: Retest only failed models
        log_debug("INFO", "scheduler", f"Phase 2: Retesting {len(failed_models)} failed models")
        
        confirmed_failures = 0
        
        for failed_info in failed_models:
            model = failed_info['model']
            
            success, error_code, error_message = await test_model_connectivity(
                api_base_url=settings.api_base_url,
                api_key=settings.api_key,
                model_id=model.model_id
            )
            
            # Save retest result
            retest_result = TestResult(
                model_id=model.id,
                tested_at=datetime.utcnow(),
                success=success,
                error_code=error_code,
                error_message=error_message
            )
            db.add(retest_result)
            
            # Only notify if retest also fails
            if not success:
                confirmed_failures += 1
                log_debug("WARNING", "scheduler", f"Model {model.display_name} failed retest, sending notification")
                await notify_model_failure(
                    settings=settings,
                    model_name=model.display_name,
                    model_id=model.model_id,
                    error_code=error_code,
                    error_message=error_message
                )
            else:
                log_debug("INFO", "scheduler", f"Model {model.display_name} passed retest (network glitch resolved)")
        
        db.commit()
        log_debug("INFO", "scheduler", f"Phase 2 completed: {confirmed_failures}/{len(failed_models)} confirmed failures, {len(failed_models) - confirmed_failures} recovered")
        
    except Exception as e:
        log_debug("ERROR", "scheduler", f"Error during scheduled tests: {e}")
        db.rollback()
    finally:
        db.close()


def update_scheduler_settings(interval_minutes: int, start_hour: int = 0, start_minute: int = 0):
    """Update the scheduler with new interval and start time settings
    
    Args:
        interval_minutes: 测试间隔（分钟）
        start_hour: 测试起始小时（0-23）
        start_minute: 测试起始分钟（0-59）
    """
    global _current_interval
    import pytz
    
    # Remove existing job if any
    try:
        scheduler.remove_job("model_health_check")
    except:
        pass
    
    # 计算下次执行时间：从今天的起始时间开始，找到下一个合适的执行点
    shanghai_tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(shanghai_tz)
    
    # 构建今天的起始时间点
    today_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    
    # 计算从今天起始时间到现在经过了多少个间隔
    if now < today_start:
        # 还没到今天的起始时间，下次执行就是今天的起始时间
        next_run = today_start
    else:
        # 已过今天起始时间，计算下一个执行点
        elapsed_minutes = (now - today_start).total_seconds() / 60
        intervals_passed = int(elapsed_minutes // interval_minutes) + 1
        next_run = today_start + timedelta(minutes=intervals_passed * interval_minutes)
    
    # Add new job with calculated start time
    scheduler.add_job(
        run_scheduled_tests,
        trigger=IntervalTrigger(minutes=interval_minutes, start_date=next_run),
        id="model_health_check",
        name="Model Health Check",
        replace_existing=True
    )
    
    _current_interval = interval_minutes
    log_debug("INFO", "scheduler", f"Scheduler updated: interval={interval_minutes}min, start={start_hour:02d}:{start_minute:02d}, next_run={next_run.strftime('%Y-%m-%d %H:%M:%S')}")


# 保持旧函数名兼容性
def update_scheduler_interval(interval_minutes: int):
    """Update the scheduler interval (backward compatible wrapper)"""
    db = SessionLocal()
    try:
        settings = get_settings(db)
        update_scheduler_settings(
            interval_minutes=interval_minutes,
            start_hour=settings.test_start_hour or 0,
            start_minute=settings.test_start_minute or 0
        )
    finally:
        db.close()


def start_scheduler():
    """Start the scheduler with initial settings"""
    db = SessionLocal()
    try:
        settings = get_settings(db)
        interval = settings.test_interval_minutes or 60
        start_hour = settings.test_start_hour or 0
        start_minute = settings.test_start_minute or 0
        
        update_scheduler_settings(
            interval_minutes=interval,
            start_hour=start_hour,
            start_minute=start_minute
        )
        
        global _current_interval
        _current_interval = interval
        
        scheduler.start()
        log_debug("INFO", "scheduler", f"Scheduler started with {interval} minute interval, start time {start_hour:02d}:{start_minute:02d}")
        
    except Exception as e:
        log_debug("ERROR", "scheduler", f"Failed to start scheduler: {e}")
    finally:
        db.close()


def cleanup_old_results(days: int = 90):
    """Remove test results older than specified days"""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(TestResult).filter(TestResult.tested_at < cutoff).delete()
        db.commit()
        if deleted > 0:
            log_debug("INFO", "scheduler", f"Cleaned up {deleted} test results older than {days} days")
    except Exception as e:
        log_debug("ERROR", "scheduler", f"Failed to cleanup old results: {e}")
        db.rollback()
    finally:
        db.close()


def get_schedule_info():
    """获取调度器信息：上次执行时间和下次执行时间"""
    import pytz
    
    shanghai_tz = pytz.timezone("Asia/Shanghai")
    
    # 上次执行时间
    last_run = None
    if _last_run_time:
        last_run = _last_run_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 下次执行时间
    next_run = None
    try:
        job = scheduler.get_job("model_health_check")
        if job and job.next_run_time:
            # 转换为上海时区
            next_run_shanghai = job.next_run_time.astimezone(shanghai_tz)
            next_run = next_run_shanghai.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    
    return {
        "last_run_time": last_run,
        "next_run_time": next_run
    }

