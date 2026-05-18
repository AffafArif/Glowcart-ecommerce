import { supabase } from '../supabaseClient'
const API = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:8000'

async function token() {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token
}

export async function api(path, options = {}) {
  const t = await token()
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (t) headers.Authorization = `Bearer ${t}`
  const res = await fetch(`${API}${path}`, { ...options, headers })
  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) throw new Error(data?.detail || data?.message || 'API error')
  return data
}
