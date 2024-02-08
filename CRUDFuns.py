from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Create a connection and cursor
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# Create table
cursor.execute('''CREATE TABLE IF NOT EXISTS items
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL)''')
conn.commit()


# Item model
class Item(BaseModel):
    name: str
    price: float


# Create item
@app.post("/items/")
async def create_item(item: Item):
    cursor.execute("INSERT INTO items (name, price) VALUES (?, ?)", (item.name, item.price))
    conn.commit()
    return {"name": item.name, "price": item.price}


# Read item
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    cursor.execute("SELECT name, price FROM items WHERE id=?", (item_id,))
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    name, price = result
    return {"name": name, "price": price}


# Update item
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    cursor.execute("UPDATE items SET name=?, price=? WHERE id=?", (item.name, item.price, item_id))
    conn.commit()
    return {"name": item.name, "price": item.price}


# Delete item
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    cursor.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    return {"message": "Item deleted successfully"}
