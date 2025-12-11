"""
Model management routes
"""
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Admin, Settings, MonitoredModel
from app.schemas import ModelCreate, ModelUpdate, ModelResponse, AvailableModel
from app.auth import get_current_admin
from app.api_client import get_available_models
from app.logger import log_debug
from app.logo_mapper import get_logo_url

router = APIRouter(prefix="/api/models", tags=["models"])


def get_settings(db: Session) -> Settings:
    """Get current settings"""
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/available", response_model=List[AvailableModel])
async def fetch_available_models(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Fetch available models from upstream API"""
    settings = get_settings(db)
    
    if not settings.api_base_url or not settings.api_key:
        raise HTTPException(status_code=400, detail="API configuration is incomplete")
    
    success, models, error = await get_available_models(
        api_base_url=settings.api_base_url,
        api_key=settings.api_key
    )
    
    if not success:
        raise HTTPException(status_code=502, detail=f"Failed to fetch models: {error}")
    
    return [AvailableModel(id=m.get("id", ""), owned_by=m.get("owned_by")) for m in models]


@router.get("", response_model=List[ModelResponse])
async def list_monitored_models(db: Session = Depends(get_db)):
    """Get list of monitored models (public endpoint)"""
    models = db.query(MonitoredModel).order_by(MonitoredModel.sort_order).all()
    return models


@router.post("", response_model=ModelResponse)
async def add_model(
    data: ModelCreate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Add a model to monitoring"""
    # Check if already exists
    existing = db.query(MonitoredModel).filter(MonitoredModel.model_id == data.model_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Model is already being monitored")
    
    # Auto-assign logo if not provided
    logo_url = data.logo_url if data.logo_url else get_logo_url(data.model_id, data.display_name)
    
    # Get max sort_order for new model
    max_order = db.query(MonitoredModel).count()
    
    model = MonitoredModel(
        model_id=data.model_id,
        display_name=data.display_name,
        logo_url=logo_url,
        enabled=True,
        sort_order=max_order
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    
    log_debug("INFO", "models", f"添加模型监控: {data.model_id}, logo: {logo_url}")
    return model


# ==========================================
# 重要：/reorder 路由必须在 /{model_id} 之前
# 否则 "reorder" 会被误当作 model_id 参数
# ==========================================

@router.put("/reorder")
async def reorder_models(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update model display order"""
    # 直接读取 JSON body
    order = await request.json()
    
    if not isinstance(order, list):
        raise HTTPException(status_code=400, detail="Expected a list of model IDs")
    
    log_debug("INFO", "models", f"Received reorder request: {order}")
    
    for index, model_id in enumerate(order):
        model = db.query(MonitoredModel).filter(MonitoredModel.id == int(model_id)).first()
        if model:
            model.sort_order = index
            log_debug("DEBUG", "models", f"Set model {model_id} sort_order to {index}")
    
    db.commit()
    log_debug("INFO", "models", f"Successfully updated model order: {order}")
    
    # Return updated list
    models = db.query(MonitoredModel).order_by(MonitoredModel.sort_order).all()
    return models


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    data: ModelUpdate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a monitored model"""
    model = db.query(MonitoredModel).filter(MonitoredModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(model, field):
            setattr(model, field, value)
    
    db.commit()
    db.refresh(model)
    
    log_debug("INFO", "models", f"更新模型: {model.model_id}")
    return model


@router.delete("/{model_id}")
async def remove_model(
    model_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Remove a model from monitoring"""
    model = db.query(MonitoredModel).filter(MonitoredModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_name = model.model_id
    db.delete(model)
    db.commit()
    
    log_debug("INFO", "models", f"Removed model from monitoring: {model_name}")
    return {"message": "Model removed from monitoring"}


@router.put("/{model_id}/toggle")
async def toggle_model(
    model_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Toggle model enabled/disabled status"""
    model = db.query(MonitoredModel).filter(MonitoredModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model.enabled = not model.enabled
    db.commit()
    
    status = "enabled" if model.enabled else "disabled"
    log_debug("INFO", "models", f"Model {model.model_id} {status}")
    return {"message": f"Model {status}", "enabled": model.enabled}
