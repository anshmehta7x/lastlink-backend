from app.dbconnect import initialize_connection
from app.verifytoken import verify_token, auth
from app.services.user_service import UserService

# Initialize services
table = initialize_connection()
user_service = UserService(table, auth)

def get_user_service():
    return user_service
