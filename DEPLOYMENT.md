# Deployment Guide

## Supabase

1. Create project.
2. Run `supabase/schema.sql` in SQL Editor.
3. Enable Google provider in Authentication > Providers.
4. Add redirect URLs:
   - `http://localhost:5173`
   - `https://your-frontend.vercel.app`

## Render backend deployment

Create six Render Web Services:

1. api-gateway
2. user-service
3. product-service
4. cart-service
5. order-service
6. payment-service

Use Docker environment for each service.

Set environment variables:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL
CORS_ORIGINS
```

For API Gateway also set:

```text
USER_SERVICE_URL
PRODUCT_SERVICE_URL
CART_SERVICE_URL
ORDER_SERVICE_URL
PAYMENT_SERVICE_URL
```

For Order Service also set:

```text
PAYMENT_SERVICE_URL
PRODUCT_SERVICE_URL
CART_SERVICE_URL
```

## Vercel frontend deployment

Deploy `frontend/`.

Set:

```text
VITE_API_GATEWAY_URL
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
```

## Admin role

After first Google login:

```sql
UPDATE user_schema.users SET role='admin' WHERE email='your_email@gmail.com';
```
