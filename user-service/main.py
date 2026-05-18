from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth import get_current_user
from cors import setup_cors

app = FastAPI(title="GlowCart User Service", version="1.0.0")
setup_cors(app)

class UserUpdate(BaseModel):
    name: str | None = None
    skin_type: str | None = None

@app.get("/health")
def health():
    return {"service": "user-service", "status": "ok"}

@app.post("/users/sync")
def sync_user(current=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_schema.users (supabase_user_id, email, name, avatar_url)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (supabase_user_id)
            DO UPDATE SET email=EXCLUDED.email, name=EXCLUDED.name, avatar_url=EXCLUDED.avatar_url, updated_at=NOW()
            RETURNING *;
        """, (current["supabase_user_id"], current["email"], current["name"], current["avatar_url"]))
        return cur.fetchone()

@app.get("/users/me")
def get_me(current=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_schema.users WHERE supabase_user_id=%s", (current["supabase_user_id"],))
        user = cur.fetchone()
        if not user:
            raise HTTPException(404, "User not synced. Call /users/sync first.")
        return user

@app.patch("/users/me")
def update_me(payload: UserUpdate, current=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_schema.users WHERE supabase_user_id=%s", (current["supabase_user_id"],))
        user = cur.fetchone()
        if not user:
            raise HTTPException(404, "User not found")
        name = payload.name or user["name"]
        skin_type = payload.skin_type or user["skin_type"]
        cur.execute("""
            UPDATE user_schema.users SET name=%s, skin_type=%s, updated_at=NOW()
            WHERE supabase_user_id=%s RETURNING *
        """, (name, skin_type, current["supabase_user_id"]))
        return cur.fetchone()

@app.get("/users/{user_id}")
def get_user(user_id: str, current=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, role, skin_type FROM user_schema.users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(404, "User not found")
        return user
