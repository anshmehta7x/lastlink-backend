import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("../serviceaccount.json")
firebase_admin.initialize_app(cred)
print("Firebase initialized")
def delete_user(uid: str):

    print(f"Deleting user with uid: {uid}")
    auth.delete_user(uid)

