from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import sqlite3
from typing import List

app = FastAPI()
DB_NAME = "users.db"

class UserIn(BaseModel):
    username: str
    email: EmailStr

class UserOut(UserIn):
    id: int

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );
        """)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/users", response_model=List[UserOut])
def list_users():
    with get_conn() as conn:
        users = conn.execute("SELECT * FROM users").fetchall()
    return [UserOut(**dict(user)) for user in users]

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    with get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(**dict(user))

@app.post("/create_user", response_model=UserOut)
def create_user(user: UserIn):
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                (user.username, user.email)
            )
            new_id = cur.lastrowid
            new_user = conn.execute("SELECT * FROM users WHERE id = ?", (new_id,)).fetchone()
        return UserOut(**dict(new_user))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
