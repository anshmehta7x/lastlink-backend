from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from app.models.user import UserCreate, UserLogin, UsernameCheck
from app.deps import get_user_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/get/{username}")
async def get_profile(username: str):
    user_service = get_user_service()
    user_info =await user_service.get_user_by_username(username)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    return {"userinfo":user_info}
