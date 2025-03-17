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
    await user_service.increment_views(user_info['uid'])
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    return {"userinfo":user_info}


# @router.get("/increment-views/{uid}")
# async def increment_views(uid: str):
#     try:
#         user_service = get_user_service()
#         user = await user_service.get_user_by_uid(uid)
#         if not user:
#             raise HTTPException(
#                 status_code=404, 
#                 detail=f"User with uid {uid} not found"
#             )
            
#         # Increment the views
#         await user_service.increment_views(uid)
        
#         # Return the updated user data
#         updated_user = await user_service.get_user_by_uid(uid)
#         return {
#             "message": "Views incremented successfully",
#             "views": updated_user.get('views', 0)
#         }
#     except Exception as e:
#         logger.error(f"Error incrementing views for user {uid}: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail="Failed to increment views"
#         )

