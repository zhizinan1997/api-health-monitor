"""
Debug logs routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Admin, DebugLog
from app.schemas import DebugLogResponse, LogsPage
from app.auth import get_current_admin

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=LogsPage)
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
    level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get debug logs (admin only)"""
    query = db.query(DebugLog)
    
    if level:
        query = query.filter(DebugLog.level == level.upper())
    
    if source:
        query = query.filter(DebugLog.source.contains(source))
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    logs = query.order_by(DebugLog.timestamp.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return LogsPage(
        logs=[DebugLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("")
async def clear_logs(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Clear all debug logs (admin only)"""
    deleted = db.query(DebugLog).delete()
    db.commit()
    
    from app.logger import log_debug
    log_debug("INFO", "logs", f"已清空 {deleted} 条日志记录")
    
    return {"message": f"已清空 {deleted} 条日志记录"}
