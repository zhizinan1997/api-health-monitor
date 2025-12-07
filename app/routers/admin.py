"""
Admin authentication and account management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Admin
from app.schemas import AdminSetup, AdminLogin, AdminPasswordChange, TokenResponse, AdminStatus
from app.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_admin,
    is_admin_initialized
)
from app.logger import log_debug

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/status", response_model=AdminStatus)
async def get_admin_status(db: Session = Depends(get_db)):
    """Check if admin account has been initialized"""
    admin = db.query(Admin).first()
    if admin:
        return AdminStatus(initialized=True, username=admin.username)
    return AdminStatus(initialized=False)


@router.post("/setup", response_model=TokenResponse)
async def setup_admin(data: AdminSetup, db: Session = Depends(get_db)):
    """First-time admin account setup"""
    # Check if already initialized
    if is_admin_initialized(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin account already exists"
        )
    
    # Create admin account
    admin = Admin(
        username=data.username,
        password_hash=get_password_hash(data.password)
    )
    db.add(admin)
    db.commit()
    
    log_debug("INFO", "admin", f"Admin account created: {data.username}")
    
    # Return token for immediate login
    access_token = create_access_token(data={"sub": admin.username})
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(data: AdminLogin, db: Session = Depends(get_db)):
    """Admin login"""
    admin = db.query(Admin).filter(Admin.username == data.username).first()
    
    if not admin or not verify_password(data.password, admin.password_hash):
        log_debug("WARNING", "admin", f"Failed login attempt for user: {data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token = create_access_token(data={"sub": admin.username})
    log_debug("INFO", "admin", f"Admin logged in: {admin.username}")
    return TokenResponse(access_token=access_token)


@router.put("/password")
async def change_password(
    data: AdminPasswordChange,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Change admin password"""
    if not verify_password(data.current_password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    admin.password_hash = get_password_hash(data.new_password)
    db.commit()
    
    log_debug("INFO", "admin", "Admin password changed")
    return {"message": "Password updated successfully"}
