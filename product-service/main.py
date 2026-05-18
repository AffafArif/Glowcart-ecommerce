from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from database import get_db
from auth import get_current_user
from cors import setup_cors

app = FastAPI(title="GlowCart Product Service", version="1.0.0")
setup_cors(app)

class ProductIn(BaseModel):
    name: str
    brand: str = "GlowCart"
    category: str
    skin_concern: str
    skin_type: str = "all"
    description: str
    ingredients: str
    price: float
    stock: int
    image_url: str | None = None
    is_active: bool = True

class StockUpdate(BaseModel):
    quantity: int

async def require_admin(current=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT role FROM user_schema.users WHERE supabase_user_id=%s", (current["supabase_user_id"],))
        user = cur.fetchone()
        if not user or user["role"] != "admin":
            raise HTTPException(403, "Admin access required")
        return current

@app.get("/health")
def health():
    return {"service": "product-service", "status": "ok"}

@app.get("/products")
def list_products(search: str | None = None, category: str | None = None, skin_type: str | None = None, active_only: bool = True):
    clauses = []
    params = []
    if active_only:
        clauses.append("is_active = TRUE")
    if search:
        clauses.append("(LOWER(name) LIKE %s OR LOWER(description) LIKE %s OR LOWER(ingredients) LIKE %s)")
        s = f"%{search.lower()}%"
        params.extend([s, s, s])
    if category:
        clauses.append("LOWER(category) = %s")
        params.append(category.lower())
    if skin_type:
        clauses.append("(LOWER(skin_type) = %s OR LOWER(skin_type) = 'all')")
        params.append(skin_type.lower())
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM product_schema.products {where} ORDER BY created_at DESC", tuple(params))
        return cur.fetchall()

@app.get("/products/{product_id}")
def get_product(product_id: str):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM product_schema.products WHERE id=%s", (product_id,))
        product = cur.fetchone()
        if not product:
            raise HTTPException(404, "Product not found")
        return product

@app.post("/products")
def create_product(payload: ProductIn, admin=Depends(require_admin)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO product_schema.products
            (name, brand, category, skin_concern, skin_type, description, ingredients, price, stock, image_url, is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
        """, (payload.name, payload.brand, payload.category, payload.skin_concern, payload.skin_type, payload.description, payload.ingredients, payload.price, payload.stock, payload.image_url, payload.is_active))
        return cur.fetchone()

@app.patch("/products/{product_id}")
def update_product(product_id: str, payload: ProductIn, admin=Depends(require_admin)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE product_schema.products SET
            name=%s, brand=%s, category=%s, skin_concern=%s, skin_type=%s, description=%s, ingredients=%s,
            price=%s, stock=%s, image_url=%s, is_active=%s, updated_at=NOW()
            WHERE id=%s RETURNING *
        """, (payload.name, payload.brand, payload.category, payload.skin_concern, payload.skin_type, payload.description, payload.ingredients, payload.price, payload.stock, payload.image_url, payload.is_active, product_id))
        product = cur.fetchone()
        if not product:
            raise HTTPException(404, "Product not found")
        return product

@app.delete("/products/{product_id}")
def delete_product(product_id: str, admin=Depends(require_admin)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE product_schema.products SET is_active=FALSE, updated_at=NOW() WHERE id=%s RETURNING *", (product_id,))
        product = cur.fetchone()
        if not product:
            raise HTTPException(404, "Product not found")
        return {"message": "Product disabled", "product": product}

@app.post("/products/{product_id}/reserve-stock")
def reserve_stock(product_id: str, payload: StockUpdate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT stock FROM product_schema.products WHERE id=%s AND is_active=TRUE FOR UPDATE", (product_id,))
        product = cur.fetchone()
        if not product:
            raise HTTPException(404, "Product not found")
        if product["stock"] < payload.quantity:
            raise HTTPException(400, "Insufficient stock")
        cur.execute("UPDATE product_schema.products SET stock=stock-%s, updated_at=NOW() WHERE id=%s RETURNING *", (payload.quantity, product_id))
        return cur.fetchone()
