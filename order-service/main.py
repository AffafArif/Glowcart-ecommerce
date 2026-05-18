from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from database import get_db
from auth import get_current_user
from cors import setup_cors
import os
import httpx

app = FastAPI(title="GlowCart Order Service", version="1.1.0")
setup_cors(app)

PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8005")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8003")

class CheckoutIn(BaseModel):
    shipping_address: str

class StatusUpdate(BaseModel):
    status: str

def get_local_user(current):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_schema.users WHERE supabase_user_id=%s", (current["supabase_user_id"],))
        user = cur.fetchone()
        if not user:
            raise HTTPException(404, "User not synced")
        return user

@app.get("/health")
def health():
    return {"service": "order-service", "status": "ok", "note": "Stock is reduced only after successful payment simulation."}

async def validate_cart_stock(client, items):
    refreshed_items = []
    total = 0.0
    for item in items:
        product_resp = await client.get(f"{PRODUCT_SERVICE_URL}/products/{item['product_id']}")
        if product_resp.status_code != 200:
            raise HTTPException(400, f"Product unavailable: {item['product_name']}")
        product = product_resp.json()
        if not product.get("is_active", True):
            raise HTTPException(400, f"Product disabled: {product['name']}")
        if int(product["stock"]) < int(item["quantity"]):
            raise HTTPException(400, f"Insufficient stock for {product['name']}")
        refreshed = {
            "product_id": item["product_id"],
            "product_name": product["name"],
            "quantity": int(item["quantity"]),
            "price_snapshot": float(product["price"]),
        }
        refreshed_items.append(refreshed)
        total += refreshed["price_snapshot"] * refreshed["quantity"]
    return refreshed_items, total

@app.post("/orders/checkout")
async def checkout(payload: CheckoutIn, authorization: str = Header(None), current=Depends(get_current_user)):
    user = get_local_user(current)
    if not payload.shipping_address.strip():
        raise HTTPException(400, "Shipping address is required")

    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient(timeout=20) as client:
        cart_resp = await client.get(f"{CART_SERVICE_URL}/cart", headers=headers)
        if cart_resp.status_code != 200:
            raise HTTPException(cart_resp.status_code, cart_resp.text)
        cart_data = cart_resp.json()
        items = cart_data.get("items", [])
        if not items:
            raise HTTPException(400, "Cart is empty")

        # Validate current stock and price before payment, but do not reduce stock yet.
        # This avoids reducing inventory for failed payments.
        refreshed_items, total = await validate_cart_stock(client, items)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO order_schema.orders (user_id, total_amount, status, customer_email, shipping_address)
            VALUES (%s,%s,'pending',%s,%s) RETURNING *
            """,
            (user["id"], total, user["email"], payload.shipping_address),
        )
        order = cur.fetchone()
        for item in refreshed_items:
            cur.execute(
                """
                INSERT INTO order_schema.order_items (order_id, product_id, product_name, quantity, price_snapshot)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (order["id"], item["product_id"], item["product_name"], item["quantity"], item["price_snapshot"]),
            )

    payment = None
    final_status = "payment_failed"
    async with httpx.AsyncClient(timeout=20) as client:
        pay_resp = await client.post(
            f"{PAYMENT_SERVICE_URL}/payments/simulate",
            json={"order_id": str(order["id"]), "amount": total},
        )
        if pay_resp.status_code == 200:
            payment = pay_resp.json()
            final_status = "paid" if payment["payment_status"] == "success" else "payment_failed"
        else:
            payment = {"error": pay_resp.text}

        # Critical correction: stock is reserved/reduced only after successful payment.
        if final_status == "paid":
            for item in refreshed_items:
                stock_resp = await client.post(
                    f"{PRODUCT_SERVICE_URL}/products/{item['product_id']}/reserve-stock",
                    json={"quantity": item["quantity"]},
                )
                if stock_resp.status_code != 200:
                    final_status = "cancelled"
                    payment = {
                        "payment_status": "success",
                        "transaction_reference": payment.get("transaction_reference") if isinstance(payment, dict) else None,
                        "warning": f"Payment succeeded but stock reservation failed for {item['product_name']}. Order cancelled for manual review.",
                    }
                    break
            if final_status == "paid":
                await client.delete(f"{CART_SERVICE_URL}/cart/clear", headers=headers)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE order_schema.orders SET status=%s, updated_at=NOW() WHERE id=%s RETURNING *", (final_status, order["id"]))
        updated_order = cur.fetchone()
    return {"order": updated_order, "payment": payment}

@app.get("/orders")
def list_orders(current=Depends(get_current_user)):
    user = get_local_user(current)
    with get_db() as conn:
        cur = conn.cursor()
        if user["role"] == "admin":
            cur.execute("SELECT * FROM order_schema.orders ORDER BY created_at DESC")
        else:
            cur.execute("SELECT * FROM order_schema.orders WHERE user_id=%s ORDER BY created_at DESC", (user["id"],))
        return cur.fetchall()

@app.get("/orders/{order_id}")
def get_order(order_id: str, current=Depends(get_current_user)):
    user = get_local_user(current)
    with get_db() as conn:
        cur = conn.cursor()
        if user["role"] == "admin":
            cur.execute("SELECT * FROM order_schema.orders WHERE id=%s", (order_id,))
        else:
            cur.execute("SELECT * FROM order_schema.orders WHERE id=%s AND user_id=%s", (order_id, user["id"]))
        order = cur.fetchone()
        if not order:
            raise HTTPException(404, "Order not found")
        cur.execute("SELECT * FROM order_schema.order_items WHERE order_id=%s", (order_id,))
        items = cur.fetchall()
        return {"order": order, "items": items}

@app.patch("/orders/{order_id}/status")
def update_status(order_id: str, payload: StatusUpdate, current=Depends(get_current_user)):
    user = get_local_user(current)
    if user["role"] != "admin":
        raise HTTPException(403, "Admin access required")
    allowed = ['pending','paid','payment_failed','cancelled','shipped','delivered']
    if payload.status not in allowed:
        raise HTTPException(400, "Invalid status")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE order_schema.orders SET status=%s, updated_at=NOW() WHERE id=%s RETURNING *", (payload.status, order_id))
        order = cur.fetchone()
        if not order:
            raise HTTPException(404, "Order not found")
        return order
