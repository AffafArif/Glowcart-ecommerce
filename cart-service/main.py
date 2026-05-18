from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth import get_current_user
from cors import setup_cors
import os
import httpx

app = FastAPI(title="GlowCart Cart Service", version="1.1.0")
setup_cors(app)

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002")

class CartItemIn(BaseModel):
    product_id: str
    quantity: int = 1

class QuantityUpdate(BaseModel):
    quantity: int

async def fetch_product(product_id: str):
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
    if resp.status_code == 404:
        raise HTTPException(404, "Product not found")
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"Product Service error: {resp.text}")
    product = resp.json()
    if not product.get("is_active", True):
        raise HTTPException(400, "Product is not active")
    return product

def get_local_user_id(current):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM user_schema.users WHERE supabase_user_id=%s", (current["supabase_user_id"],))
        user = cur.fetchone()
        if not user:
            raise HTTPException(404, "User not synced")
        return user["id"]

def ensure_cart(conn, user_id):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO cart_schema.carts (user_id)
        VALUES (%s)
        ON CONFLICT (user_id)
        DO UPDATE SET updated_at=NOW()
        RETURNING *
        """,
        (user_id,),
    )
    return cur.fetchone()

@app.get("/health")
def health():
    return {"service": "cart-service", "status": "ok", "note": "Product prices are fetched from Product Service, not trusted from frontend."}

@app.get("/cart")
def get_cart(current=Depends(get_current_user)):
    user_id = get_local_user_id(current)
    with get_db() as conn:
        cart = ensure_cart(conn, user_id)
        cur = conn.cursor()
        cur.execute("SELECT * FROM cart_schema.cart_items WHERE cart_id=%s ORDER BY created_at", (cart["id"],))
        items = cur.fetchall()
        total = sum(float(i["price_snapshot"]) * i["quantity"] for i in items)
        return {"cart": cart, "items": items, "total": total}

@app.post("/cart/items")
async def add_item(payload: CartItemIn, current=Depends(get_current_user)):
    if payload.quantity <= 0:
        raise HTTPException(400, "Quantity must be greater than zero")

    product = await fetch_product(payload.product_id)
    if product["stock"] < payload.quantity:
        raise HTTPException(400, "Requested quantity exceeds available stock")

    user_id = get_local_user_id(current)
    with get_db() as conn:
        cart = ensure_cart(conn, user_id)
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM cart_schema.cart_items WHERE cart_id=%s AND product_id=%s", (cart["id"], payload.product_id))
        existing = cur.fetchone()
        new_quantity = payload.quantity + (existing["quantity"] if existing else 0)
        if product["stock"] < new_quantity:
            raise HTTPException(400, "Cart quantity would exceed available stock")

        cur.execute(
            """
            INSERT INTO cart_schema.cart_items
            (cart_id, product_id, product_name, product_image_url, quantity, price_snapshot)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT (cart_id, product_id)
            DO UPDATE SET
                quantity=cart_schema.cart_items.quantity + EXCLUDED.quantity,
                product_name=EXCLUDED.product_name,
                product_image_url=EXCLUDED.product_image_url,
                price_snapshot=EXCLUDED.price_snapshot,
                updated_at=NOW()
            RETURNING *
            """,
            (cart["id"], payload.product_id, product["name"], product.get("image_url"), payload.quantity, product["price"]),
        )
        return cur.fetchone()

@app.patch("/cart/items/{item_id}")
async def update_quantity(item_id: str, payload: QuantityUpdate, current=Depends(get_current_user)):
    if payload.quantity <= 0:
        raise HTTPException(400, "Quantity must be greater than zero")
    user_id = get_local_user_id(current)
    with get_db() as conn:
        cart = ensure_cart(conn, user_id)
        cur = conn.cursor()
        cur.execute("SELECT * FROM cart_schema.cart_items WHERE id=%s AND cart_id=%s", (item_id, cart["id"]))
        item = cur.fetchone()
        if not item:
            raise HTTPException(404, "Cart item not found")

    product = await fetch_product(str(item["product_id"]))
    if product["stock"] < payload.quantity:
        raise HTTPException(400, "Requested quantity exceeds available stock")

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE cart_schema.cart_items
            SET quantity=%s, product_name=%s, product_image_url=%s, price_snapshot=%s, updated_at=NOW()
            WHERE id=%s AND cart_id=%s
            RETURNING *
            """,
            (payload.quantity, product["name"], product.get("image_url"), product["price"], item_id, cart["id"]),
        )
        return cur.fetchone()

@app.delete("/cart/items/{item_id}")
def remove_item(item_id: str, current=Depends(get_current_user)):
    user_id = get_local_user_id(current)
    with get_db() as conn:
        cart = ensure_cart(conn, user_id)
        cur = conn.cursor()
        cur.execute("DELETE FROM cart_schema.cart_items WHERE id=%s AND cart_id=%s RETURNING *", (item_id, cart["id"]))
        item = cur.fetchone()
        if not item:
            raise HTTPException(404, "Cart item not found")
        return {"message": "Removed", "item": item}

@app.delete("/cart/clear")
def clear_cart(current=Depends(get_current_user)):
    user_id = get_local_user_id(current)
    with get_db() as conn:
        cart = ensure_cart(conn, user_id)
        cur = conn.cursor()
        cur.execute("DELETE FROM cart_schema.cart_items WHERE cart_id=%s", (cart["id"],))
        return {"message": "Cart cleared"}
