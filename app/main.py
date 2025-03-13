from fastapi import FastAPI, Depends, HTTPException, Request, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.dbconnect import initialize_connection
from app.verifytoken import verify_token, auth
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import json
import logging

# Set up proper logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define models
class UserCreate(BaseModel):
    username: str
    displayName: str = None
    photoURL: str = None

class UserLogin(BaseModel):
    uid: str = None
    email: str = None
    provider: str = None
    displayName: str = None

# Create a service layer for user operations
class UserService:
    def __init__(self, table, auth_client):
        self.table = table
        self.auth = auth_client
    
    async def delete_firebase_user(self, uid):
        try:
            logger.info(f"Deleting Firebase user with uid: {uid}")
            self.auth.delete_user(uid)
            return True
        except Exception as e:
            logger.error(f"Failed to delete Firebase user {uid}: {str(e)}")
            return False
    
    async def username_exists(self, username):
        response = self.table.scan(
            FilterExpression=Attr("username").eq(username)
        )
        return response.get('Items') and len(response['Items']) > 0
    
    async def email_exists(self, email):
        response = self.table.scan(
            FilterExpression=Attr("email").eq(email)
        )
        return response.get('Items') and len(response['Items']) > 0
    
    async def create_user(self, user_data):
        return self.table.put_item(Item=user_data)
    
    async def get_user_by_uid(self, uid):
        response = self.table.query(
            KeyConditionExpression=Key("uid").eq(uid)
        )
        return response.get('Items')[0] if response.get('Items') and len(response.get('Items')) > 0 else None
        
    async def update_last_login(self, uid):
        return self.table.update_item(
            Key={"uid": uid},
            UpdateExpression="SET lastLogin = :time",
            ExpressionAttributeValues={
                ":time": datetime.now().isoformat()
            }
        )
    
    async def update_user_profile(self, uid, update_data):
        # Build update expression
        update_expression = "SET updatedAt = :updated"
        expression_values = {
            ":updated": datetime.now().isoformat()
        }
        
        for key, value in update_data.items():
            if key not in ["uid", "email", "provider", "createdAt"]:  # Prevent updating critical fields
                update_expression += f", {key} = :{key}"
                expression_values[f":{key}"] = value
        
        # Update user
        return self.table.update_item(
            Key={"uid": uid},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
    
    async def delete_user(self, uid):
        return self.table.delete_item(
            Key={"uid": uid}
        )
    
    async def get_all_users(self):
        response = self.table.scan()
        return response.get('Items', [])
    
    async def get_modified_username(self, base_username, max_attempts=10):
        count = 0
        username = base_username
        
        while count < max_attempts:
            if not await self.username_exists(username):
                return username
            count += 1
            username = f"{base_username}{count}"
        
        # If we exhausted attempts, generate a truly unique name with timestamp
        return f"{base_username}{int(datetime.now().timestamp())}"

# Initialize the app
app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
table = initialize_connection()
user_service = UserService(table, auth)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/auth/login")
async def login_user(login_data: UserLogin = Body(...), token_data: dict = Depends(verify_token)):
    """
    Handle user login from any provider (email/password or Google)
    """
    uid = token_data.get("uid")
    email = token_data.get("email")
    provider = login_data.provider
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Check if user exists
        user = await user_service.get_user_by_uid(uid)
        
        # User exists - return user data
        if user:
            # Update last login time
            await user_service.update_last_login(uid)
            
            return {
                "success": True,
                "message": "Login successful",
                "user": user
            }
        else:
            # Handle auto-creation for Google login
            if provider == "google":
                # Create a new user with email as username initially
                base_username = login_data.displayName
                
                # Get unique username
                username = await user_service.get_modified_username(base_username)
                
                # Create new user
                new_user = {
                    "uid": uid,
                    "email": email,
                    "username": username,
                    "displayName": login_data.displayName or username,
                    "provider": provider,
                    "createdAt": datetime.now().isoformat(),
                    "lastLogin": datetime.now().isoformat(),
                }
                
                await user_service.create_user(new_user)
                
                return {
                    "success": True,
                    "message": "Account created automatically with Google login",
                    "user": new_user
                }
            else:
                return {
                    "success": False,
                    "message": "User does not exist. Please register first."
                }
                
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/auth/register")
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
        # Check if user already exists
        existing_user = await user_service.get_user_by_uid(uid)
        
        if existing_user:
            return {
                "success": False,
                "message": "User already exists",
                "firebaseCleanupNeeded": False  # User exists in both Firebase and database
            }
        
        # Check if email is already in use
        if await user_service.email_exists(email):
            # Schedule Firebase cleanup in background
            background_tasks.add_task(user_service.delete_firebase_user, uid)
            
            return {
                "success": False,
                "message": "Email already in use",
                "firebaseCleanupNeeded": False  # Will be handled in background
            }
            
        # Check if username is already in use
        if await user_service.username_exists(username):
            # Schedule Firebase cleanup in background
            background_tasks.add_task(user_service.delete_firebase_user, uid)
            
            return {
                "success": False,
                "message": "Username already in use",
                "firebaseCleanupNeeded": False  # Will be handled in background
            }
    
        # Create new user
        new_user = {
            "uid": uid,
            "email": email,
            "username": username,
            "displayName": user.displayName or username,
            "photoURL": user.photoURL or "",
            "provider": "email",
            "createdAt": datetime.now().isoformat(),
            "lastLogin": datetime.now().isoformat(),
        }

        await user_service.create_user(new_user)
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user": new_user
        }
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        
        # Attempt Firebase cleanup on any error
        background_tasks.add_task(user_service.delete_firebase_user, uid)
            
        return {
            "success": False,
            "message": f"Registration error: {str(e)}",
            "firebaseCleanupNeeded": False  # Will be handled in background
        }

@app.get("/auth/user")
async def get_user(token_data: dict = Depends(verify_token)):
    """
    Get current user data based on token
    """
    uid = token_data.get("uid")
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user = await user_service.get_user_by_uid(uid)
        
        if user:
            return {
                "success": True,
                "user": user
            }
        else:
            return {
                "success": False,
                "message": "User not found"
            }
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@app.put("/auth/update")
async def update_user(user_data: dict = Body(...), token_data: dict = Depends(verify_token)):
    """
    Update user profile information
    """
    uid = token_data.get("uid")
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Check if user exists
        user = await user_service.get_user_by_uid(uid)
        
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Check if updating username and if it's already taken
        if "username" in user_data and user_data["username"] != user.get("username", ""):
            if await user_service.username_exists(user_data["username"]):
                return {
                    "success": False,
                    "message": "Username already taken"
                }
        
        # Update user
        await user_service.update_user_profile(uid, user_data)
        
        # Get updated user
        updated_user = await user_service.get_user_by_uid(uid)
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": updated_user
        }
    
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")

@app.delete("/auth/delete")
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
        # Check if user exists
        user = await user_service.get_user_by_uid(uid)
        
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Delete user from database
        await user_service.delete_user(uid)
        
        # Schedule Firebase deletion as background task
        background_tasks.add_task(user_service.delete_firebase_user, uid)
        
        return {
            "success": True,
            "message": "Account deleted successfully"
        }
    
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")

@app.post("/auth/check-username")
async def check_username(data: dict = Body(...)):
    """
    Check if a username is available
    """
    username = data.get("username")
    
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    try:
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

@app.get("/users")
async def get_users(token_data: dict = Depends(verify_token)):
    """
    Get all users (admin only)
    """
    uid = token_data.get("uid")
    
    # Check if admin (in a real app, you'd have an admin flag in the user record)
    try:
        user = await user_service.get_user_by_uid(uid)
        
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Here you would check if user is admin
        # if not user.get("isAdmin", False):
        #     raise HTTPException(status_code=403, detail="Forbidden")
        
        users = await user_service.get_all_users()
        return {
            "success": True,
            "users": users
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")