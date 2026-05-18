import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ShoppingBag, User, ShieldCheck, LogOut, ArrowLeft, Pencil, PackageCheck } from 'lucide-react'
import './index.css'
import { supabase } from './supabaseClient'
import { api } from './services/api'

function Nav({ session, profile, setPage, onLogout }) {
  return <div className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-stone-100">
    <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
      <button onClick={() => setPage('home')} className="flex items-center gap-2 font-black text-2xl"><ShoppingBag/> GlowCart</button>
      <div className="flex gap-2 items-center flex-wrap justify-end">
        <button className="btn-light" onClick={() => setPage('products')}>Products</button>
        {session && <button className="btn-light" onClick={() => setPage('cart')}>Cart</button>}
        {session && <button className="btn-light" onClick={() => setPage('orders')}>Orders</button>}
        {profile?.role === 'admin' && <button className="btn-light" onClick={() => setPage('admin')}>Admin</button>}
        {!session ? <button className="btn-primary" onClick={() => setPage('login')}>Login</button> : <button className="btn-light flex gap-2" onClick={onLogout}><LogOut size={18}/> Logout</button>}
      </div>
    </div>
  </div>
}

function Home({ setPage }) {
  return <section className="max-w-6xl mx-auto p-4 py-12 grid md:grid-cols-2 gap-8 items-center">
    <div>
      <p className="text-sm uppercase tracking-widest text-stone-500 mb-3">Distributed Skincare E-Commerce</p>
      <h1 className="text-5xl font-black leading-tight mb-4">Clinical-style skincare shopping, built with microservices.</h1>
      <p className="text-stone-600 text-lg mb-6">Browse serums, moisturizers, sunscreens, and cleansers. Add products to cart, checkout, and manage orders with a distributed FastAPI backend.</p>
      <button className="btn-primary" onClick={() => setPage('products')}>Shop products</button>
    </div>
    <div className="card p-8 bg-gradient-to-br from-rose-50 to-stone-50">
      <div className="rounded-3xl bg-white p-6 shadow-sm">
        <p className="font-bold text-xl mb-2">Architecture Demo</p>
        <p className="text-stone-600">Frontend → API Gateway → User/Product/Cart/Order/Payment Services → Supabase PostgreSQL</p>
      </div>
    </div>
  </section>
}

function Login() {
  const login = async () => {
    await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: window.location.origin } })
  }
  return <div className="max-w-md mx-auto p-4 py-16">
    <div className="card p-8 text-center">
      <User className="mx-auto mb-4" size={42}/>
      <h2 className="text-3xl font-black mb-2">Login to GlowCart</h2>
      <p className="text-stone-600 mb-6">Use Google login. The backend receives your Supabase JWT for authenticated distributed requests.</p>
      <button onClick={login} className="btn-primary w-full">Continue with Google</button>
    </div>
  </div>
}

function Products({ session, openProduct }) {
  const [products, setProducts] = useState([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [err, setErr] = useState('')
  const load = async () => {
    setErr('')
    const q = new URLSearchParams()
    if (search) q.set('search', search)
    if (category) q.set('category', category)
    try { setProducts(await api(`/products?${q.toString()}`)) } catch(e) { setErr(e.message) }
  }
  useEffect(() => { load() }, [])
  const add = async (p) => {
    if (!session) return alert('Login first')
    await api('/cart/items', { method: 'POST', body: JSON.stringify({ product_id: p.id, quantity: 1 }) })
    alert('Added to cart. Price and product data were fetched by Cart Service from Product Service.')
  }
  return <div className="max-w-6xl mx-auto p-4 py-8">
    <div className="flex flex-col md:flex-row gap-3 mb-6">
      <input className="input" placeholder="Search niacinamide, cleanser..." value={search} onChange={e=>setSearch(e.target.value)} />
      <select className="input md:w-64" value={category} onChange={e=>setCategory(e.target.value)}>
        <option value="">All categories</option><option>Serum</option><option>Moisturizer</option><option>Sunscreen</option><option>Cleanser</option><option>Mask</option>
      </select>
      <button className="btn-primary" onClick={load}>Search</button>
    </div>
    {err && <p className="text-red-600 mb-4">{err}</p>}
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
      {products.map(p => <div key={p.id} className="card overflow-hidden">
        <button onClick={() => openProduct(p.id)} className="block w-full text-left">
          <img src={p.image_url || 'https://images.unsplash.com/photo-1556228720-195a672e8a03'} className="h-52 w-full object-cover"/>
        </button>
        <div className="p-5">
          <div className="text-xs uppercase text-stone-500">{p.category} · {p.skin_type}</div>
          <button onClick={() => openProduct(p.id)} className="font-black text-xl mt-1 text-left hover:underline">{p.name}</button>
          <p className="text-stone-600 text-sm mt-2 line-clamp-2">{p.description}</p>
          <p className="text-sm mt-2"><b>Concern:</b> {p.skin_concern}</p>
          <div className="flex items-center justify-between mt-4 gap-2">
            <span className="font-black">PKR {Number(p.price).toFixed(0)}</span>
            <div className="flex gap-2"><button className="btn-light" onClick={() => openProduct(p.id)}>Details</button><button className="btn-primary" onClick={() => add(p)}>Add</button></div>
          </div>
          <p className="text-xs text-stone-500 mt-2">Stock: {p.stock}</p>
        </div>
      </div>)}
    </div>
  </div>
}

function ProductDetails({ productId, session, setPage }) {
  const [product, setProduct] = useState(null)
  const [qty, setQty] = useState(1)
  const [err, setErr] = useState('')
  useEffect(() => {
    api(`/products/${productId}`).then(setProduct).catch(e => setErr(e.message))
  }, [productId])
  const add = async () => {
    if (!session) return alert('Login first')
    await api('/cart/items', { method: 'POST', body: JSON.stringify({ product_id: product.id, quantity: Number(qty) }) })
    alert('Added to cart')
    setPage('cart')
  }
  if (err) return <div className="max-w-4xl mx-auto p-4 py-8 text-red-600">{err}</div>
  if (!product) return <div className="max-w-4xl mx-auto p-4 py-8">Loading product...</div>
  return <div className="max-w-5xl mx-auto p-4 py-8">
    <button className="btn-light flex gap-2 mb-5" onClick={() => setPage('products')}><ArrowLeft size={18}/> Back to products</button>
    <div className="card overflow-hidden grid md:grid-cols-2">
      <img src={product.image_url || 'https://images.unsplash.com/photo-1556228720-195a672e8a03'} className="h-full min-h-96 w-full object-cover"/>
      <div className="p-7">
        <div className="text-xs uppercase tracking-widest text-stone-500">{product.brand} · {product.category}</div>
        <h2 className="text-4xl font-black mt-2 mb-3">{product.name}</h2>
        <p className="text-stone-600 mb-4">{product.description}</p>
        <div className="grid sm:grid-cols-2 gap-3 text-sm mb-5">
          <p><b>Skin concern:</b> {product.skin_concern}</p>
          <p><b>Skin type:</b> {product.skin_type}</p>
          <p><b>Stock:</b> {product.stock}</p>
          <p><b>Status:</b> {product.is_active ? 'Active' : 'Disabled'}</p>
        </div>
        <div className="bg-stone-50 rounded-2xl p-4 mb-5">
          <p className="font-bold mb-1">Ingredients</p>
          <p className="text-stone-600">{product.ingredients}</p>
        </div>
        <p className="text-3xl font-black mb-4">PKR {Number(product.price).toFixed(0)}</p>
        <div className="flex gap-3">
          <input className="input max-w-28" type="number" min="1" max={product.stock} value={qty} onChange={e => setQty(e.target.value)} />
          <button className="btn-primary" onClick={add} disabled={!product.is_active || product.stock < 1}>Add to cart</button>
        </div>
      </div>
    </div>
  </div>
}

function Cart({ setPage }) {
  const [cart, setCart] = useState(null)
  const [address, setAddress] = useState('')
  const [message, setMessage] = useState('')
  const load = async () => setCart(await api('/cart'))
  useEffect(() => { load().catch(e=>setMessage(e.message)) }, [])
  const remove = async (id) => { await api(`/cart/items/${id}`, { method:'DELETE' }); load() }
  const updateQty = async (id, quantity) => { await api(`/cart/items/${id}`, { method:'PATCH', body: JSON.stringify({ quantity }) }); load() }
  const checkout = async () => {
    if (!address) return alert('Enter shipping address')
    const res = await api('/orders/checkout', { method:'POST', body: JSON.stringify({ shipping_address: address }) })
    setMessage(`Order ${res.order.status}. Transaction: ${res.payment?.transaction_reference || 'N/A'}`)
    setPage('orders')
  }
  return <div className="max-w-4xl mx-auto p-4 py-8">
    <h2 className="text-3xl font-black mb-5">Your Cart</h2>
    {message && <p className="mb-4 text-stone-700">{message}</p>}
    <div className="space-y-3">
      {cart?.items?.map(i => <div className="card p-4 flex flex-col sm:flex-row justify-between sm:items-center gap-3" key={i.id}>
        <div><b>{i.product_name}</b><p>Qty {i.quantity} · PKR {Number(i.price_snapshot).toFixed(0)}</p></div>
        <div className="flex gap-2">
          <button className="btn-light" onClick={()=>updateQty(i.id, Math.max(1, i.quantity - 1))}>-</button>
          <button className="btn-light" onClick={()=>updateQty(i.id, i.quantity + 1)}>+</button>
          <button className="btn-light" onClick={()=>remove(i.id)}>Remove</button>
        </div>
      </div>)}
      {cart?.items?.length === 0 && <p className="text-stone-500">Your cart is empty.</p>}
    </div>
    <div className="card p-5 mt-5">
      <p className="font-black text-xl mb-3">Total: PKR {Number(cart?.total || 0).toFixed(0)}</p>
      <textarea className="input mb-3" placeholder="Shipping address" value={address} onChange={e=>setAddress(e.target.value)} />
      <button className="btn-primary" onClick={checkout}>Checkout with simulated payment</button>
      <p className="text-xs text-stone-500 mt-3">Stock is reduced only if the Payment Service returns success.</p>
    </div>
  </div>
}

function Orders({ profile }) {
  const [orders, setOrders] = useState([])
  const [message, setMessage] = useState('')
  const statuses = ['pending','paid','payment_failed','cancelled','shipped','delivered']
  const load = () => api('/orders').then(setOrders).catch(e=>setMessage(e.message))
  useEffect(() => { load() }, [])
  const updateStatus = async (id, status) => {
    await api(`/orders/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) })
    setMessage('Order status updated')
    load()
  }
  return <div className="max-w-5xl mx-auto p-4 py-8">
    <h2 className="text-3xl font-black mb-5">Orders</h2>
    {message && <p className="mb-4 text-stone-700">{message}</p>}
    <div className="space-y-3">{orders.map(o => <div className="card p-5" key={o.id}>
      <div className="flex flex-col md:flex-row md:justify-between gap-3"><b>{o.id}</b><span className="rounded-full bg-stone-100 px-3 py-1 w-fit">{o.status}</span></div>
      <p>PKR {Number(o.total_amount).toFixed(0)} · {o.customer_email}</p>
      <p className="text-stone-500 text-sm">{new Date(o.created_at).toLocaleString()}</p>
      {profile?.role === 'admin' && <div className="mt-4 flex flex-wrap gap-2 items-center">
        <PackageCheck size={18}/><span className="text-sm font-semibold">Admin status update:</span>
        {statuses.map(s => <button key={s} className={s === o.status ? 'btn-primary' : 'btn-light'} onClick={() => updateStatus(o.id, s)}>{s}</button>)}
      </div>}
    </div>)}</div>
  </div>
}

function Admin() {
  const empty = {
    name: '',
    brand: 'GlowCart',
    category: 'Serum',
    skin_concern: 'Hydration',
    skin_type: 'all',
    description: '',
    ingredients: '',
    price: 0,
    stock: 0,
    image_url: '',
    is_active: true
  };

  const [form, setForm] = useState(empty);
  const [editingId, setEditingId] = useState(null);
  const [products, setProducts] = useState([]);
  const [message, setMessage] = useState('');

  const load = async () => {
    setProducts(await api('/products?active_only=false'));
  };

  useEffect(() => {
    load().catch(e => setMessage(e.message));
  }, []);

  const submit = async (e) => {
    e.preventDefault();

    const payload = {
      ...form,
      price: Number(form.price),
      stock: Number(form.stock),
      is_active: Boolean(form.is_active)
    };

    if (editingId) {
      await api(`/products/${editingId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload)
      });
      setMessage('Product updated');
    } else {
      await api('/products', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      setMessage('Product added');
    }

    setForm(empty);
    setEditingId(null);
    load();
  };

  const edit = (p) => {
    setEditingId(p.id);

    setForm({
      name: p.name || '',
      brand: p.brand || 'GlowCart',
      category: p.category || 'Serum',
      skin_concern: p.skin_concern || '',
      skin_type: p.skin_type || 'all',
      description: p.description || '',
      ingredients: p.ingredients || '',
      price: Number(p.price || 0),
      stock: Number(p.stock || 0),
      image_url: p.image_url || '',
      is_active: Boolean(p.is_active)
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm(empty);
  };

  const disable = async (id) => {
    await api(`/products/${id}`, {
      method: 'DELETE'
    });

    setMessage('Product disabled');
    load();
  };

  const enable = async (p) => {
    const payload = {
      name: p.name,
      brand: p.brand,
      category: p.category,
      skin_concern: p.skin_concern,
      skin_type: p.skin_type,
      description: p.description,
      ingredients: p.ingredients,
      price: Number(p.price),
      stock: Number(p.stock),
      image_url: p.image_url,
      is_active: true
    };

    await api(`/products/${p.id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });

    setMessage('Product enabled');
    load();
  };

  return (
    <div className="max-w-6xl mx-auto p-4 py-8">
      <div className="flex items-center gap-2 mb-5">
        <ShieldCheck />
        <h2 className="text-3xl font-black">Admin Dashboard</h2>
      </div>

      {message && <p className="mb-4 text-stone-700">{message}</p>}

      <form onSubmit={submit} className="card p-5 grid md:grid-cols-2 gap-3 mb-6">
        <h3 className="md:col-span-2 text-xl font-black">
          {editingId ? 'Edit Product' : 'Add Product'}
        </h3>

        {[
          'name',
          'brand',
          'category',
          'skin_concern',
          'skin_type',
          'description',
          'ingredients',
          'price',
          'stock',
          'image_url'
        ].map(k => (
          <input
            key={k}
            className="input"
            placeholder={k}
            value={form[k]}
            onChange={e => setForm({ ...form, [k]: e.target.value })}
          />
        ))}

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={e => setForm({ ...form, is_active: e.target.checked })}
          />
          Active product
        </label>

        <div className="md:col-span-2 flex gap-2">
          <button className="btn-primary">
            {editingId ? 'Save Product Changes' : 'Add Product'}
          </button>

          {editingId && (
            <button type="button" className="btn-light" onClick={cancelEdit}>
              Cancel Edit
            </button>
          )}
        </div>
      </form>

      <div className="grid md:grid-cols-2 gap-3">
        {products.map(p => (
          <div className="card p-4" key={p.id}>
            <b>{p.name}</b>

            <p>
              PKR {Number(p.price).toFixed(0)} · Stock {p.stock} ·{' '}
              {p.is_active ? 'Active' : 'Disabled'}
            </p>

            <p className="text-sm text-stone-500">
              {p.category} · {p.skin_concern}
            </p>

            <div className="flex gap-2 mt-3">
              <button className="btn-light flex gap-1" onClick={() => edit(p)}>
                <Pencil size={16} /> Edit
              </button>

              {p.is_active ? (
                <button className="btn-light" onClick={() => disable(p.id)}>
                  Disable
                </button>
              ) : (
                <button className="btn-primary" onClick={() => enable(p)}>
                  Enable
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function App() {
  const [session, setSession] = useState(null)
  const [profile, setProfile] = useState(null)
  const [page, setPage] = useState('home')
  const [selectedProductId, setSelectedProductId] = useState(null)
  const sync = async () => {
    try {
    await api('/users/sync', {
      method: 'POST'
    });

    const me = await api('/users/me');
    setProfile(me);
  } catch(e) {
    console.error(e);
  }
  }
  useEffect(() => {
    supabase.auth.getSession().then(({data}) => { setSession(data.session); if(data.session) sync() })
    const { data: sub } = supabase.auth.onAuthStateChange((_event, s) => { setSession(s); if(s) sync(); else setProfile(null) })
    return () => sub.subscription.unsubscribe()
  }, [])
  const logout = async()=>{ await supabase.auth.signOut(); setPage('home') }
  const openProduct = (id) => { setSelectedProductId(id); setPage('product-details') }
  return <>
    <Nav session={session} profile={profile} setPage={setPage} onLogout={logout}/>
    {page==='home' && <Home setPage={setPage}/>} {page==='login' && <Login/>}
    {page==='products' && <Products session={session} openProduct={openProduct}/>} {page==='product-details' && <ProductDetails productId={selectedProductId} session={session} setPage={setPage}/>} 
    {page==='cart' && <Cart setPage={setPage}/>} {page==='orders' && <Orders profile={profile}/>} {page==='admin' && <Admin/>}
  </>
}

createRoot(document.getElementById('root')).render(<App />)
