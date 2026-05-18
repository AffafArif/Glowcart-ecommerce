CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS user_schema;
CREATE SCHEMA IF NOT EXISTS product_schema;
CREATE SCHEMA IF NOT EXISTS cart_schema;
CREATE SCHEMA IF NOT EXISTS order_schema;
CREATE SCHEMA IF NOT EXISTS payment_schema;

CREATE TABLE IF NOT EXISTS user_schema.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supabase_user_id UUID UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    avatar_url TEXT,
    role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'admin')),
    skin_type TEXT DEFAULT 'normal',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_schema.products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    brand TEXT NOT NULL DEFAULT 'GlowCart',
    category TEXT NOT NULL,
    skin_concern TEXT NOT NULL,
    skin_type TEXT NOT NULL DEFAULT 'all',
    description TEXT NOT NULL,
    ingredients TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_schema.carts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS cart_schema.cart_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id UUID NOT NULL REFERENCES cart_schema.carts(id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    product_name TEXT NOT NULL,
    product_image_url TEXT,
    quantity INT NOT NULL CHECK (quantity > 0),
    price_snapshot NUMERIC(10,2) NOT NULL CHECK (price_snapshot >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(cart_id, product_id)
);

CREATE TABLE IF NOT EXISTS order_schema.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL CHECK (total_amount >= 0),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','paid','payment_failed','cancelled','shipped','delivered')),
    customer_email TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_schema.order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES order_schema.orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    product_name TEXT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price_snapshot NUMERIC(10,2) NOT NULL CHECK (price_snapshot >= 0)
);

CREATE TABLE IF NOT EXISTS payment_schema.payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL,
    amount NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    payment_status TEXT NOT NULL CHECK (payment_status IN ('success','failed')),
    transaction_reference TEXT UNIQUE NOT NULL,
    provider TEXT NOT NULL DEFAULT 'GlowPay Simulation',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO product_schema.products (name, brand, category, skin_concern, skin_type, description, ingredients, price, stock, image_url)
VALUES
('Niacinamide 10% Serum', 'GlowCart', 'Serum', 'Oil Control', 'oily', 'A lightweight serum for oily and blemish-prone skin.', 'Niacinamide, Zinc PCA, Hyaluronic Acid', 3200, 40, 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be'),
('Hydrating Hyaluronic Acid', 'GlowCart', 'Serum', 'Hydration', 'dry', 'A daily hydration booster for plump-looking skin.', 'Hyaluronic Acid, Panthenol, Glycerin', 2800, 35, 'https://images.unsplash.com/photo-1608248597279-f99d160bfcbc'),
('Barrier Repair Moisturizer', 'GlowCart', 'Moisturizer', 'Barrier Repair', 'all', 'A ceramide-rich moisturizer for daily barrier support.', 'Ceramides, Cholesterol, Fatty Acids', 3600, 30, 'https://images.unsplash.com/photo-1556228720-195a672e8a03'),
('Daily Mineral Sunscreen SPF 50', 'GlowCart', 'Sunscreen', 'Sun Protection', 'all', 'Lightweight mineral sunscreen for everyday use.', 'Zinc Oxide, Titanium Dioxide, Vitamin E', 4200, 25, 'https://images.unsplash.com/photo-1556228578-8c89e6adf883'),
('Gentle Gel Cleanser', 'GlowCart', 'Cleanser', 'Daily Cleansing', 'sensitive', 'A non-stripping cleanser for sensitive skin.', 'Aloe Vera, Glycerin, Mild Surfactants', 2400, 50, 'https://images.unsplash.com/photo-1571781926291-c477ebfd024b')
ON CONFLICT DO NOTHING;
