# app/services/user_service.py
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import logging

# Set up proper logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    async def get_user_by_username(self, username):
        try:
            # Note: This should ideally use a GSI on username instead of scan
            response = self.table.scan(
                FilterExpression=Attr("username").eq(username)
            )
            if not response.get('Items'):
                return None
            if len(response['Items']) > 1:
                logger.warning(f"Multiple users found with username {username}")
            return response['Items'][0]
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {str(e)}")
            raise
        
    async def increment_views(self, uid):
        try:
            return self.table.update_item(
                Key={"uid": uid},
                UpdateExpression="SET profileViews = if_not_exists(profileViews, :zero) + :inc",
                ExpressionAttributeValues={
                    ":inc": 1,
                    ":zero": 0
                }
            )
        except Exception as e:
            logger.error(f"Failed to increment views for user {uid}: {str(e)}")
            raise
    
    async def update_last_login(self, uid):
        return self.table.update_item(
            Key={"uid": uid},
            UpdateExpression="SET lastLogin = :time",
            ExpressionAttributeValues={
                ":time": datetime.now().isoformat()
            }
        )
    
    async def update_user_profile(self, uid, update_data):
        try:
            # Build update expression
            update_expression = "SET updatedAt = :updated"
            expression_values = {
                ":updated": datetime.now().isoformat()
            }
            
            # Define protected fields
            protected_fields = {"uid", "email", "provider", "createdAt", "username"}
            
            for key, value in update_data.items():
                if key not in protected_fields:  # Added username to protected fields
                    update_expression += f", #{key} = :{key}"
                    expression_values[f":{key}"] = value
            
            # Add ExpressionAttributeNames to handle reserved words
            expression_names = {f"#{k}": k for k in update_data.keys() if k not in protected_fields}
            
            # Update user
            return self.table.update_item(
                Key={"uid": uid},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names if expression_names else None
            )
        except Exception as e:
            logger.error(f"Failed to update user profile for {uid}: {str(e)}")
            raise
    
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