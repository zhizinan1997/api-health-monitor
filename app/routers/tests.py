"""
Test execution and results routes
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import pytz

from app.database import get_db
from app.models import Admin, Settings, MonitoredModel, TestResult
from app.schemas import TestResultResponse, ModelStats, HourlyStatus, ManualTestResult
from app.auth import get_current_admin
from app.api_client import test_model_connectivity
from app.notifier import notify_model_failure
from app.logger import log_debug
from app.scheduler import get_schedule_info

router = APIRouter(prefix="/api/tests", tags=["tests"])

BEIJING_TZ = pytz.timezone("Asia/Shanghai")


def get_settings(db: Session) -> Settings:
    """Get current settings"""
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


async def run_single_test(db: Session, settings: Settings, model: MonitoredModel, send_notification: bool = True) -> ManualTestResult:
    """Run a test for a single model"""
    success, error_code, error_message = await test_model_connectivity(
        api_base_url=settings.api_base_url,
        api_key=settings.api_key,
        model_id=model.model_id
    )
    
    # Save result
    result = TestResult(
        model_id=model.id,
        tested_at=datetime.utcnow(),
        success=success,
        error_code=error_code,
        error_message=error_message
    )
    db.add(result)
    db.commit()
    
    # Send notification on failure (only for scheduled tests)
    if send_notification and not success:
        await notify_model_failure(
            settings=settings,
            model_name=model.display_name,
            model_id=model.model_id,
            error_code=error_code,
            error_message=error_message
        )
    
    return ManualTestResult(
        model_id=model.id,
        model_name=model.display_name,
        success=success,
        error_code=error_code,
        error_message=error_message,
        tested_at=datetime.utcnow()
    )


@router.post("/run-all", response_model=List[ManualTestResult])
async def run_all_tests(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Manually test all enabled models"""
    settings = get_settings(db)
    
    if not settings.api_base_url or not settings.api_key:
        return []
    
    models = db.query(MonitoredModel).filter(MonitoredModel.enabled == True).all()
    results = []
    
    log_debug("INFO", "tests", f"Manual test started for {len(models)} models")
    
    for model in models:
        result = await run_single_test(db, settings, model, send_notification=False)
        results.append(result)
    
    log_debug("INFO", "tests", f"Manual test completed: {sum(1 for r in results if r.success)}/{len(results)} passed")
    return results


@router.post("/run/{model_id}", response_model=ManualTestResult)
async def run_single_model_test(
    model_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Manually test a single model"""
    settings = get_settings(db)
    
    model = db.query(MonitoredModel).filter(MonitoredModel.id == model_id).first()
    if not model:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Model not found")
    
    log_debug("INFO", "tests", f"Manual test started for model: {model.model_id}")
    result = await run_single_test(db, settings, model, send_notification=False)
    
    return result


@router.get("/results", response_model=List[TestResultResponse])
async def get_test_results(
    model_id: Optional[int] = Query(None),
    hours: int = Query(24, ge=1, le=2160),  # Max 90 days
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get test results (public endpoint)"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(TestResult).filter(TestResult.tested_at >= cutoff)
    
    if model_id:
        query = query.filter(TestResult.model_id == model_id)
    
    results = query.order_by(TestResult.tested_at.desc()).limit(limit).all()
    
    # Enhance with model names
    response = []
    for r in results:
        model = db.query(MonitoredModel).filter(MonitoredModel.id == r.model_id).first()
        response.append(TestResultResponse(
            id=r.id,
            model_id=r.model_id,
            model_name=model.display_name if model else "Unknown",
            tested_at=r.tested_at,
            success=r.success,
            error_code=r.error_code,
            error_message=r.error_message
        ))
    
    return response


@router.get("/stats", response_model=List[ModelStats])
async def get_model_stats(db: Session = Depends(get_db)):
    """Get connectivity statistics for all models (public endpoint)"""
    # 按 sort_order 排序确保与管理界面顺序一致
    models = db.query(MonitoredModel).filter(MonitoredModel.enabled == True).order_by(MonitoredModel.sort_order).all()
    stats = []
    
    now = datetime.utcnow()
    
    for model in models:
        # Get last 24 hours of results for hourly status
        hourly_status = _calculate_hourly_status(db, model.id, now)
        
        # Calculate rates for different periods
        rate_1d = _calculate_rate(db, model.id, now, days=1)
        rate_3d = _calculate_rate(db, model.id, now, days=3)
        rate_7d = _calculate_rate(db, model.id, now, days=7)
        rate_30d = _calculate_rate(db, model.id, now, days=30)
        
        # Get last test result (not last error, but most recent test)
        last_test = db.query(TestResult).filter(
            TestResult.model_id == model.id
        ).order_by(TestResult.tested_at.desc()).first()
        
        # Only show error if the most recent test failed
        last_error_code = None
        last_error_message = None
        if last_test and not last_test.success:
            last_error_code = last_test.error_code
            last_error_message = last_test.error_message
        
        stats.append(ModelStats(
            model_id=model.id,
            model_name=model.model_id,
            display_name=model.display_name,
            logo_url=model.logo_url or "",
            hourly_status=hourly_status,
            rate_1d=rate_1d,
            rate_3d=rate_3d,
            rate_7d=rate_7d,
            rate_30d=rate_30d,
            last_error_code=last_error_code,
            last_error_message=last_error_message
        ))
    
    return stats


def _calculate_hourly_status(db: Session, model_id: int, now: datetime) -> List[HourlyStatus]:
    """Calculate hourly status for last 24 hours
    
    每个小时格子的颜色由该小时内最后一次测试结果决定：
    - 最后一次测试成功 → 绿色
    - 最后一次测试失败 → 红色
    - 没有测试 → 灰色
    
    这样管理员手动修复后测试成功，格子会变绿
    """
    # Get Beijing time now
    beijing_now = now.replace(tzinfo=pytz.UTC).astimezone(BEIJING_TZ)
    
    hourly_status = []
    
    for i in range(24):
        # Calculate the hour slot (going back from current hour)
        hour_offset = 23 - i
        slot_start = beijing_now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=hour_offset)
        slot_end = slot_start + timedelta(hours=1)
        
        # Convert to UTC for database query
        slot_start_utc = slot_start.astimezone(pytz.UTC).replace(tzinfo=None)
        slot_end_utc = slot_end.astimezone(pytz.UTC).replace(tzinfo=None)
        
        # Get the LAST test result for this hour (ordered by time)
        last_result = db.query(TestResult).filter(
            TestResult.model_id == model_id,
            TestResult.tested_at >= slot_start_utc,
            TestResult.tested_at < slot_end_utc
        ).order_by(TestResult.tested_at.desc()).first()
        
        if last_result:
            # 最后一次测试结果决定格子颜色
            success = last_result.success
        else:
            success = None  # No test in this hour
        
        hourly_status.append(HourlyStatus(
            hour=slot_start.hour,
            timestamp=slot_start.replace(tzinfo=None),
            success=success
        ))
    
    return hourly_status


def _calculate_rate(db: Session, model_id: int, now: datetime, days: int) -> Optional[float]:
    """Calculate success rate for a period"""
    cutoff = now - timedelta(days=days)
    
    total = db.query(TestResult).filter(
        TestResult.model_id == model_id,
        TestResult.tested_at >= cutoff
    ).count()
    
    if total == 0:
        return None
    
    success = db.query(TestResult).filter(
        TestResult.model_id == model_id,
        TestResult.tested_at >= cutoff,
        TestResult.success == True
    ).count()
    
    return round(success / total * 100, 1)


@router.get("/schedule-info")
async def get_schedule_info_endpoint():
    """获取定时任务的调度信息（上次和下次执行时间）- 公开接口"""
    return get_schedule_info()
