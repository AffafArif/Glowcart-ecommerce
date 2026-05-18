# GlowCart — Distributed Skincare E-Commerce Platform

GlowCart is a distributed skincare e-commerce prototype built for CS-432 Distributed Computing.
It uses a React frontend, FastAPI microservices, an API Gateway, Supabase PostgreSQL, Supabase Google Auth/JWT, Docker, and cloud-ready deployment configuration.

## Architecture

```text
React Frontend
      ↓ HTTP REST + JWT
API Gateway
      ↓ HTTP REST + JWT forwarding
User Service
Product Service
Cart Service
Order Service → Payment Service
      ↓
Supabase PostgreSQL logical schemas
```

## Services

| Service | Local Port | Purpose |
|---|---:|---|
| API Gateway | 8000 | Single frontend entry point and request routing |
| User Service | 8001 | User sync/profile/role management |
| Product Service | 8002 | Skincare product catalog and admin CRUD |
| Cart Service | 8003 | Per-user cart management |
| Order Service | 8004 | Checkout, order history, order status |
| Payment Service | 8005 | Payment simulation and payment records |

## Why this fulfills the assignment

- **Network communication:** frontend communicates with API Gateway using REST; Gateway communicates with services using HTTP; Order Service communicates with Payment Service using HTTP.
- **No monolithic single-process system:** each backend domain runs as a separate FastAPI service/container.
- **Minimum 3 distributed components:** project contains 6 backend distributed components plus frontend and Supabase.
- **Separate databases/logical separation:** Supabase PostgreSQL uses separate schemas: `user_schema`, `product_schema`, `cart_schema`, `order_schema`, `payment_schema`.
- **Sustainability:** lightweight services, logical DB separation, independent service scaling, product caching in Gateway, and cloud-hosted managed DB reduce unnecessary local resource usage.

## Local setup

### 1. Supabase

1. Create a Supabase project.
2. Enable Google provider in Authentication.
3. Open SQL Editor and run:

```sql
-- copy contents of supabase/schema.sql
```

4. Copy your Supabase values:
   - Project URL
   - Anon Key
   - Service Role Key
   - PostgreSQL connection string

### 2. Environment variables

Copy `.env.example` to `.env` in root and fill values.

```bash
cp .env.example .env
```

Copy `frontend/.env.example` to `frontend/.env`.

```bash
cp frontend/.env.example frontend/.env
```

### 3. Run backend with Docker

```bash
docker compose up --build
```

Swagger docs:

- http://localhost:8000/docs
- http://localhost:8001/docs
- http://localhost:8002/docs
- http://localhost:8003/docs
- http://localhost:8004/docs
- http://localhost:8005/docs

### 4. Run frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Demo flow

1. User logs in with Google.
2. User syncs profile through User Service.
3. User browses products from Product Service.
4. User adds products to cart through Cart Service.
5. User checks out through Order Service.
6. Order Service calls Payment Service using HTTP.
7. Payment record is saved and order status becomes `paid` or `payment_failed`.
8. User views order history.
9. Admin opens Admin Dashboard and adds/updates products using the edit form.
10. Admin opens Orders and updates order status using status buttons.

## Important implementation corrections included

- Admin product edit form supports PATCH updates to Product Service.
- Admin order page supports status updates: pending, paid, payment_failed, cancelled, shipped, delivered.
- Checkout validates stock before payment, but reduces product stock only after Payment Service returns success.
- Cart Service no longer trusts frontend price/name/image. It receives only product_id and quantity, then fetches authoritative product data from Product Service.
- Product Details page is included with ingredients, skin concern, stock, and add-to-cart quantity.
- API Gateway clears product-list cache when products are added, edited, or disabled.

## Cloud deployment suggestion

- Frontend: Vercel
- Backend services: Render Web Services, one service per backend folder
- Database/Auth: Supabase

For Render, deploy each backend folder separately with Docker. Set all environment variables for each service.

For Vercel, deploy the `frontend` folder and set:

```text
VITE_API_GATEWAY_URL=https://your-api-gateway.onrender.com
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Admin access

After logging in once with Google, manually set your user role in Supabase SQL Editor:

```sql
UPDATE user_schema.users
SET role = 'admin'
WHERE email = 'your_email@gmail.com';
```

Then refresh the app.
