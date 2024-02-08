from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import sqlite3

app = FastAPI()

# Secret key and algorithm for JWT
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

# Token expiration time
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Database initialization
conn = sqlite3.connect('employees.db')
cursor = conn.cursor()

# Employee model
class Employee(BaseModel):
    id: int
    name: str
    department: str
    position: str

# Create table
cursor.execute('''CREATE TABLE IF NOT EXISTS employees
                 (id INTEGER PRIMARY KEY, name TEXT, department TEXT, position TEXT)''')
conn.commit()

# User model
class User(BaseModel):
    username: str
    password: str

# User in database
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$YJmNYEnLlLcwC3SBQqP03O/AALto/Y1aDbZk9bGrZ0QL4w4O6m8Aa",  # Password: secret
        "disabled": False,
    }
}

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to authenticate user
def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

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
        status_code=401,
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

    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# Login endpoint
@app.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Create Employee
@app.post("/employees/", response_model=Employee, dependencies=[Depends(get_current_user)])
async def create_employee(employee: Employee):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO employees (id, name, department, position) VALUES (?, ?, ?, ?)",
                   (employee.id, employee.name, employee.department, employee.position))
    conn.commit()
    return employee

# Read Employee
@app.get("/employees/{employee_id}", response_model=Employee, dependencies=[Depends(get_current_user)])
async def read_employee(employee_id: int):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, department, position FROM employees WHERE id=?", (employee_id,))
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    id, name, department, position = result
    return {"id": id, "name": name, "department": department, "position": position}

# Update Employee
@app.put("/employees/{employee_id}", dependencies=[Depends(get_current_user)])
async def update_employee(employee_id: int, employee: Employee):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET name=?, department=?, position=? WHERE id=?",
                   (employee.name, employee.department, employee.position, employee_id))
    conn.commit()
    return {"message": "Employee updated successfully"}

# Delete Employee
@app.delete("/employees/{employee_id}", dependencies=[Depends(get_current_user)])
async def delete_employee(employee_id: int):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id=?", (employee_id,))
    conn.commit()
    return {"message": "Employee deleted successfully"}
