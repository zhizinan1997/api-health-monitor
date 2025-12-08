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


def update_scheduler_interval(interval_minutes: int):
    """Update the scheduler interval"""
    global _current_interval
    
    if _current_interval == interval_minutes:
        return  # No change needed
    
    # Remove existing job if any
    try:
        scheduler.remove_job("model_health_check")
    except:
        pass
    
    # Add new job with updated interval
    scheduler.add_job(
        run_scheduled_tests,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="model_health_check",
        name="Model Health Check",
        replace_existing=True
    )
    
    _current_interval = interval_minutes
    log_debug("INFO", "scheduler", f"Scheduler interval updated to {interval_minutes} minutes")


def start_scheduler():
    """Start the scheduler with initial settings"""
    db = SessionLocal()
    try:
        settings = get_settings(db)
        interval = settings.test_interval_minutes or 60
        
        # Add the scheduled job
        scheduler.add_job(
            run_scheduled_tests,
            trigger=IntervalTrigger(minutes=interval),
            id="model_health_check",
            name="Model Health Check",
            replace_existing=True
        )
        
        global _current_interval
        _current_interval = interval
        
        scheduler.start()
        log_debug("INFO", "scheduler", f"Scheduler started with {interval} minute interval")
        
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
