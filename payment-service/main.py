from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_db
from cors import setup_cors
import random
import uuid

app = FastAPI(title="GlowCart Payment Simulation Service", version="1.0.0")
setup_cors(app)

class PaymentIn(BaseModel):
    order_id: str
    amount: float
    force_status: str | None = None

@app.get("/health")
def health():
    return {"service": "payment-service", "status": "ok"}

@app.post("/payments/simulate")
def simulate_payment(payload: PaymentIn):
    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be greater than zero")
    status = payload.force_status if payload.force_status in ["success", "failed"] else ("success" if random.random() > 0.15 else "failed")
    reference = f"TXN-{uuid.uuid4().hex[:10].upper()}"
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO payment_schema.payments (order_id, amount, payment_status, transaction_reference)
            VALUES (%s,%s,%s,%s) RETURNING *
        """, (payload.order_id, payload.amount, status, reference))
        return cur.fetchone()

@app.get("/payments/{order_id}")
def get_payment(order_id: str):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM payment_schema.payments WHERE order_id=%s ORDER BY created_at DESC", (order_id,))
        payments = cur.fetchall()
        return payments
