import sqlite3
from datetime import datetime, timedelta

import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

app = FastAPI()


# Example ASGI middleware for mTLS authentication
class MutualTLSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get the client certificate from the request
        client_cert = request.scope.get("client_cert", None)

        # Verify client certificate here against a trusted CA
        if not client_cert:
            return Response("Client certificate required", status_code=403)

        # Continue handling the request
        response = await call_next(request)
        return response


# Attach the middleware to the app
app.add_middleware(MutualTLSMiddleware)

# Secret key and algorithm for JWT
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

# Token expiration time
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Database initialization
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Create table
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, full_name TEXT, email TEXT, disabled BOOLEAN)''')
conn.commit()

# Check if admin user already exists
cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
admin_exists = cursor.fetchone()

# If admin user doesn't exist, create it
if not admin_exists:
    cursor.execute("INSERT INTO users (username, password, full_name, email, disabled) VALUES (?, ?, ?, ?, ?)",
                   ("admin", "admin", "Admin User", "admin@example.com", False))
    conn.commit()


# User model
class User(BaseModel):
    id: int
    username: str
    password: str
    full_name: str
    email: str
    disabled: bool


# Function to authenticate user
def authenticate_user(username: str, password: str):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data and user_data[2] == password:
        return {"username": user_data[1], "full_name": user_data[3], "email": user_data[4], "disabled": user_data[5]}
    return None


# Function to create access token
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Function to get current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    user = authenticate_user(username, "")
    if user is None:
        raise credentials_exception
    return user


# Login endpoint
@app.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Create User
@app.post("/users/", response_model=User, dependencies=[Depends(get_current_user)])
def create_user(user: User):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (id, username, password, full_name, email, disabled) VALUES (?, ?, ?, ?, ?, ?)",
                   (user.id, user.username, user.password, user.full_name, user.email, user.disabled))
    conn.commit()
    return user


# Read User
@app.get("/users/{user_id}", response_model=User, dependencies=[Depends(get_current_user)])
def read_user(user_id: int):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user_data = cursor.fetchone()
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = {
        "id": user_data[0],
        "username": user_data[1],
        "password": user_data[2],
        "full_name": user_data[3],
        "email": user_data[4],
        "disabled": user_data[5]
    }
    return user


# Update User
@app.put("/users/{user_id}", dependencies=[Depends(get_current_user)])
def update_user(user_id: int, user: User):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username=?, password=?, full_name=?, email=?, disabled=? WHERE id=?",
                   (user.username, user.password, user.full_name, user.email, user.disabled, user_id))
    conn.commit()
    return {"message": "User updated successfully"}


# Delete User
@app.delete("/users/{user_id}", dependencies=[Depends(get_current_user)])
def delete_user(user_id: int):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    return {"message": "User deleted successfully"}
