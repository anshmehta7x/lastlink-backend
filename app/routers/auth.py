from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from app.models.user import UserCreate, UserLogin, UsernameCheck
from app.deps import get_user_service
from app.verifytoken import verify_token
from datetime import datetime
import logging

# Set up proper logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/login")
async def login_user(login_data: UserLogin = Body(...), token_data: dict = Depends(verify_token)):
    uid = token_data.get("uid")
    email = token_data.get("email")
    provider = login_data.provider
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user_service = get_user_service()
        
        user = await user_service.get_user_by_uid(uid)
        if user:
            await user_service.update_last_login(uid)
            
            return {
                "user": user
            }
        else:
            if provider == "google":
                base_username = login_data.displayName
                username = await user_service.get_modified_username(base_username)
                
                new_user = {
                    "uid": uid,
                    "email": email,
                    "username": username.replace(" ", "").lower(),
                    "name": login_data.displayName or username,
                    "provider": provider,
                    "createdAt": datetime.now().isoformat(),
                    "lastLogin": datetime.now().isoformat(),
                    "photoURL": "https://www.tenforums.com/geek/gars/images/2/types/thumb_15951118880user.png",
                    "profileViews": 0
                }
                
                await user_service.create_user(new_user)
                
                return {
                    "user": new_user
                }
            else:
                raise HTTPException(status_code=404, detail="User does not exist. Please register first.")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@router.post("/register")
async def register_user(
    user: UserCreate, 
    token_data: dict = Depends(verify_token),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Register a new user after they've created an account with Firebase Authentication
    """
    uid = token_data.get("uid")
    email = token_data.get("email")
    username = user.username
    
    if not uid or not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user_service = get_user_service()
        
        # Check if user already exists
        existing_user = await user_service.get_user_by_uid(uid)
        
        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")
        
        # Check if email is already in use
        if await user_service.email_exists(email):
            # Schedule Firebase cleanup in background
            background_tasks.add_task(user_service.delete_firebase_user, uid)
            
            raise HTTPException(status_code=409, detail="Email already in use")
            
        # Check if username is already in use
        if await user_service.username_exists(username):
            # Schedule Firebase cleanup in background
            background_tasks.add_task(user_service.delete_firebase_user, uid)
            
            raise HTTPException(status_code=409, detail="Username already in use")
    
        # Create new user
        new_user = {
            "uid": uid,
            "email": email,
            "username": username.replace(" ", "").lower(),
            "name": "",
            "photoURL": user.photoURL or "https://www.tenforums.com/geek/gars/images/2/types/thumb_15951118880user.png",
            "provider": "email",
            "createdAt": datetime.now().isoformat(),
            "lastLogin": datetime.now().isoformat(),
            "profileViews": 0
        }

        await user_service.create_user(new_user)
        
        return {
            "user": new_user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        
        # Attempt Firebase cleanup on any error
        background_tasks.add_task(user_service.delete_firebase_user, uid)
            
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@router.get("/user")
async def get_user(token_data: dict = Depends(verify_token)):
    """
    Get current user data based on token
    """
    uid = token_data.get("uid")
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user_service = get_user_service()
        user = await user_service.get_user_by_uid(uid)
        
        if user:
            return {
                "user": user
            }
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@router.put("/update")
async def update_user(user_data: dict = Body(...), token_data: dict = Depends(verify_token)):
    """
    Update user profile information
    """
    uid = token_data.get("uid")
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user_service = get_user_service()
        
        # Check if user exists
        user = await user_service.get_user_by_uid(uid)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if updating username and if it's already taken
        if "username" in user_data and user_data["username"] != user.get("username", ""):
            if await user_service.username_exists(user_data["username"]):
                raise HTTPException(status_code=409, detail="Username already taken")
        
        # Update user
        await user_service.update_user_profile(uid, user_data)
        
        # Get updated user
        updated_user = await user_service.get_user_by_uid(uid)
        
        return {
            "user": updated_user
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")

@router.delete("/delete")
async def delete_user_account(
    token_data: dict = Depends(verify_token),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Delete a user account
    """
    uid = token_data.get("uid")
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user_service = get_user_service()
        
        # Check if user exists
        user = await user_service.get_user_by_uid(uid)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user from database
        await user_service.delete_user(uid)
        
        # Schedule Firebase deletion as background task
        background_tasks.add_task(user_service.delete_firebase_user, uid)
        
        return {
            "message": "Account deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")

@router.post("/check-username")
async def check_username(data: UsernameCheck):
    """
    Check if a username is available
    """
    username = data.username
    
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    try:
        user_service = get_user_service()
        is_taken = await user_service.username_exists(username)
        
        if is_taken:
            return {
                "available": False,
                "message": "Username is already taken"
            }
        else:
            return {
                "available": True,
                "message": "Username is available"
            }
    
    except Exception as e:
        logger.error(f"Error checking username: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking username: {str(e)}")