from fastapi import FastAPI
from app.dbconnect import initialize_connection
app = FastAPI()

table = initialize_connection()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/users")
def create_user(user: dict):
    table.put_item(Item=user)
    return {"message": "User created successfully", "user": user}
