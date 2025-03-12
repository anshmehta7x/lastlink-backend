from fastapi import FastAPI, Depends, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.dbconnect import initialize_connection
from app.verifytoken import verify_token
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

table = initialize_connection()

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

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/auth/login")
async def login_user(login_data: UserLogin = Body(...), token_data: dict = Depends(verify_token)):
    """
    Handle user login from any provider (email/password or Google)
    """
    print(login_data)
    uid = token_data.get("uid")
    email = token_data.get("email")
    provider = login_data.provider
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Check if user exists
        user_response = table.query(
            KeyConditionExpression=Key("uid").eq(uid)
        )
        
        # User exists - return user data
        if user_response.get('Items') and len(user_response['Items']) > 0:
            user = user_response['Items'][0]
            
            # Update last login time
            table.update_item(
                Key={"uid": uid},
                UpdateExpression="SET lastLogin = :time",
                ExpressionAttributeValues={
                    ":time": datetime.now().isoformat()
                }
            )
            
            return {
                "success": True,
                "message": "Login successful",
                "user": user
            }
        else:

            if provider == "google":
                # Create a new user with email as username initially
                username = login_data.displayName
                # Check if username exists and modify if needed
                username_exists = True
                count = 0
                base_username = username
                
                while username_exists and count < 10:
                    response = table.scan(
                        FilterExpression=Attr("username").eq(username)
                    )
                    
                    if response.get('Items') and len(response['Items']) > 0:
                        count += 1
                        username = f"{base_username}{count}"
                    else:
                        username_exists = False
                
                # Create new user
                new_user = {
                    "uid": uid,
                    "email": email,
                    "username": username,
                    "provider": provider,
                    "createdAt": datetime.now().isoformat(),
                    "lastLogin": datetime.now().isoformat(),
                }
                
                table.put_item(Item=new_user)
                
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
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/auth/register")
async def register_user(user: UserCreate, token_data: dict = Depends(verify_token)):
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
        existing_user = table.query(
            KeyConditionExpression=Key("uid").eq(uid)
        )
        
        if existing_user.get('Items') and len(existing_user['Items']) > 0:
            return {
                "success": False,
                "message": "User already exists",
                "firebaseCleanupNeeded": True
            }
        
        # Check if email or username is already in use
        username = user.username
        
        if email or username:
            filter_expression = None
            if email and username:
                filter_expression = Attr("email").eq(email) | Attr("username").eq(username)
            elif email:
                filter_expression = Attr("email").eq(email)
            elif username:
                filter_expression = Attr("username").eq(username)
                
            if filter_expression:
                response = table.scan(
                    FilterExpression=filter_expression
                )
                
                if response.get('Items') and len(response['Items']) > 0:
                    for item in response['Items']:
                        if item.get('email') == email:
                            return {
                                "success": False,
                                "message": "Email already in use",
                                "firebaseCleanupNeeded": True
                            }
                        if item.get('username') == username:
                            import app.admin as admin
                            admin.delete_user(uid)
                            return {
                                "success": False,
                                "message": "Username already in use",
                                "firebaseCleanupNeeded": True
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

        table.put_item(Item=new_user)
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user": new_user
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Registration error: {str(e)}",
            "firebaseCleanupNeeded": True
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
        user_response = table.query(
            KeyConditionExpression=Key("uid").eq(uid)
        )
        
        if user_response.get('Items') and len(user_response['Items']) > 0:
            return {
                "success": True,
                "user": user_response['Items'][0]
            }
        else:
            return {
                "success": False,
                "message": "User not found"
            }
    except Exception as e:
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
        user_response = table.query(
            KeyConditionExpression=Key("uid").eq(uid)
        )
        
        if not user_response.get('Items') or len(user_response['Items']) == 0:
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Check if updating username and if it's already taken
        if "username" in user_data and user_data["username"] != user_response['Items'][0].get("username", ""):
            username_response = table.scan(
                FilterExpression=Attr("username").eq(user_data["username"])
            )
            
            if username_response.get('Items') and len(username_response['Items']) > 0:
                return {
                    "success": False,
                    "message": "Username already taken"
                }
        
        # Build update expression
        update_expression = "SET updatedAt = :updated"
        expression_values = {
            ":updated": datetime.now().isoformat()
        }
        
        for key, value in user_data.items():
            if key not in ["uid", "email", "provider", "createdAt"]:  # Prevent updating critical fields
                update_expression += f", {key} = :{key}"
                expression_values[f":{key}"] = value
        
        # Update user
        table.update_item(
            Key={"uid": uid},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        # Get updated user
        updated_user = table.query(
            KeyConditionExpression=Key("uid").eq(uid)
        )
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": updated_user['Items'][0] if updated_user.get('Items') else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")

@app.delete("/auth/delete")
async def delete_user(token_data: dict = Depends(verify_token)):
    """
    Delete a user account
    """
    uid = token_data.get("uid")
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Check if user exists
        user_response = table.query(
            KeyConditionExpression=Key("uid").eq(uid)
        )
        
        if not user_response.get('Items') or len(user_response['Items']) == 0:
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Delete user
        table.delete_item(
            Key={"uid": uid}
        )
        
        return {
            "success": True,
            "message": "Account deleted successfully"
        }
    
    except Exception as e:
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
        response = table.scan(
            FilterExpression=Attr("username").eq(username)
        )
        
        if response.get('Items') and len(response['Items']) > 0:
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
        raise HTTPException(status_code=500, detail=f"Error checking username: {str(e)}")

@app.get("/users")
async def get_users(token_data: dict = Depends(verify_token)):
    """
    Get all users (admin only)
    """
    uid = token_data.get("uid")
    
    # Check if admin (in a real app, you'd have an admin flag in the user record)
    try:
        user_response = table.query(
            KeyConditionExpression=Key("uid").eq(uid)
        )
        
        if not user_response.get('Items') or len(user_response['Items']) == 0:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Here you would check if user is admin
        # if not user_response['Items'][0].get("isAdmin", False):
        #     raise HTTPException(status_code=403, detail="Forbidden")
        
        users = table.scan()
        return {
            "success": True,
            "users": users["Items"]
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")