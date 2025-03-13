from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    displayName: str = None
    photoURL: str = None

class UserLogin(BaseModel):
    uid: str = None
    email: str = None
    provider: str = None
    displayName: str = None

class UsernameCheck(BaseModel):
    username: str
