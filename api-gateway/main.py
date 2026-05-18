from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from cors import setup_cors
import os
import httpx
import time

app = FastAPI(title="GlowCart API Gateway", version="1.0.0")
setup_cors(app)

SERVICE_MAP = {
    "users": os.getenv("USER_SERVICE_URL", "http://user-service:8001"),
    "products": os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002"),
    "cart": os.getenv("CART_SERVICE_URL", "http://cart-service:8003"),
    "orders": os.getenv("ORDER_SERVICE_URL", "http://order-service:8004"),
    "payments": os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8005"),
}

_product_cache = {"time": 0, "data": None, "query": None}
CACHE_SECONDS = 60

@app.get("/health")
def health():
    return {"service": "api-gateway", "status": "ok", "routes": SERVICE_MAP}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request):
    first = path.split("/", 1)[0]
    base = SERVICE_MAP.get(first)
    if not base:
        return JSONResponse(status_code=404, content={"detail": "Unknown service route"})

    method = request.method
    query = str(request.url.query)

    # Simple product-list cache for sustainability/performance discussion.
    # Mutating product requests clear this cache so admin edits show quickly.
    if first == "products" and method in {"POST", "PATCH", "DELETE", "PUT"}:
        _product_cache.update({"time": 0, "data": None, "query": None})

    if method == "GET" and path == "products":
        now = time.time()
        if _product_cache["data"] is not None and _product_cache["query"] == query and now - _product_cache["time"] < CACHE_SECONDS:
            return JSONResponse(content=_product_cache["data"], headers={"X-GlowCart-Cache": "HIT"})

    url = f"{base}/{path}"
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, params=request.query_params, content=body, headers=headers)

    content_type = resp.headers.get("content-type", "application/json")
    if method == "GET" and path == "products" and resp.status_code == 200:
        try:
            _product_cache.update({"time": time.time(), "data": resp.json(), "query": query})
        except Exception:
            pass
    return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)
