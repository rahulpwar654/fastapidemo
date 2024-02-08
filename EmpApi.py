from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Model for Employee
class Employee(BaseModel):
    id: int
    name: str
    department: str
    position: str


# Sample data
employees = [
    Employee(id=1, name="John Doe", department="IT", position="Developer"),
    Employee(id=2, name="Jane Smith", department="HR", position="Manager"),
]


# GET all employees
@app.get("/employees/")
async def get_employees():
    return employees


# GET employee by ID
@app.get("/employees/{employee_id}")
async def get_employee(employee_id: int):
    for employee in employees:
        if employee.id == employee_id:
            return employee
    raise HTTPException(status_code=404, detail="Employee not found")


# POST new employee
@app.post("/employees/")
async def create_employee(employee: Employee):
    employees.append(employee)
    return employee


# PUT/update employee by ID
@app.put("/employees/{employee_id}")
async def update_employee(employee_id: int, employee: Employee):
    for emp in employees:
        if emp.id == employee_id:
            emp.name = employee.name
            emp.department = employee.department
            emp.position = employee.position
            return {"message": "Employee updated successfully"}
    raise HTTPException(status_code=404, detail="Employee not found")


# DELETE employee by ID
@app.delete("/employees/{employee_id}")
async def delete_employee(employee_id: int):
    for i, emp in enumerate(employees):
        if emp.id == employee_id:
            del employees[i]
            return {"message": "Employee deleted successfully"}
    raise HTTPException(status_code=404, detail="Employee not found")
