"""
Debug logging utility
"""
from datetime import datetime
from typing import Optional
from app.database import SessionLocal
from app.models import DebugLog

# In-memory buffer for logs before DB is ready
_log_buffer = []
_db_ready = False


def set_db_ready():
    """Mark DB as ready and flush buffered logs"""
    global _db_ready
    _db_ready = True
    _flush_buffer()


def _flush_buffer():
    """Flush buffered logs to database"""
    global _log_buffer
    if not _log_buffer:
        return
    
    try:
        db = SessionLocal()
        for level, source, message in _log_buffer:
            log = DebugLog(
                level=level,
                source=source,
                message=message,
                timestamp=datetime.utcnow()
            )
            db.add(log)
        db.commit()
        db.close()
        _log_buffer = []
    except Exception as e:
        print(f"Failed to flush log buffer: {e}")


def log_debug(level: str, source: str, message: str):
    """
    Log a debug message
    
    Args:
        level: INFO, WARNING, or ERROR
        source: Module/component name
        message: Log message
    """
    global _log_buffer
    
    # Always print to console
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] [{source}] {message}")
    
    if not _db_ready:
        _log_buffer.append((level, source, message))
        return
    
    try:
        db = SessionLocal()
        log = DebugLog(
            level=level,
            source=source,
            message=message[:1000],  # Limit message length
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        db.close()
    except Exception as e:
        print(f"Failed to save log: {e}")


def cleanup_old_logs(days: int = 7):
    """Remove logs older than specified days"""
    from datetime import timedelta
    
    try:
        db = SessionLocal()
        cutoff = datetime.utcnow() - timedelta(days=days)
        db.query(DebugLog).filter(DebugLog.timestamp < cutoff).delete()
        db.commit()
        db.close()
        log_debug("INFO", "logger", f"已清理 {days} 天前的日志")
    except Exception as e:
        print(f"Failed to cleanup logs: {e}")
