from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

app = FastAPI()

# Define a secret key for JWT encoding and decoding
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mock database user
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$YJmNYEnLlLcwC3SBQqP03O/AALto/Y1aDbZk9bGrZ0QL4w4O6m8Aa",  # Password: secret
        "disabled": False,
    }
}

# User model
class User(BaseModel):
    username: str
    password: str


# Token model
class Token(BaseModel):
    access_token: str
    token_type: str


# Hashing password function
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Authenticate user function
def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user


# Create access token function
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Login endpoint
@app.post("/login", response_model=Token)
async def login_for_access_token(user: User):
    user_data = authenticate_user(user.username, user.password)
    if not user_data:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
