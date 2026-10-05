import { useEffect, useState, type FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

function App() {
  type Session = {pharmacy_id: string; csrf_token: string};
  type Product = {product_id: string; brand_name: string; dosage_form: string; source_record: {ingredients: {name: string; strength: {amount: string; unit: string; per_amount: string; per_unit: string}}[]; pack_size: {amount: string; unit: string} | null}};
  type Stock = {id: string; product_id: string; quantity: number; price: string; currency: string; sale_basis: string; revision: number; stock_confirmed_at: string};
  const [session, setSession] = useState<Session | null>(null);
  const [catalog, setCatalog] = useState<Product[]>([]);
  const [stock, setStock] = useState<Stock[]>([]);
  const [name, setName] = useState('');
  const [message, setMessage] = useState('Checking session...');
  const [busy, setBusy] = useState(false);

  async function api(path: string, method = 'GET', data?: unknown, current = session) {
    const response = await fetch('/api/v1' + path, {
      method, credentials: 'same-origin', headers: {
        ...(data !== undefined ? {'Content-Type': 'application/json'} : {}),
        ...(current && method !== 'GET' ? {'X-CSRF-Token': current.csrf_token} : {}),
      }, body: data === undefined ? undefined : JSON.stringify(data),
    });
    if (!response.ok) {
      if (response.status === 401) {setSession(null); setCatalog([]); setStock([]); setName('');}
      const error = await response.json().catch(() => null);
      throw new Error(error?.error?.message ?? `Request failed (${response.status})`);
    }
    return response.status === 204 ? null : response.json();
  }
  async function refresh(current: Session) {
    const base = `/pharmacies/${current.pharmacy_id}`;
    const [profile, products, items] = await Promise.all([
      api(base, 'GET', undefined, current), api('/catalog', 'GET', undefined, current),
      api(base + '/inventory', 'GET', undefined, current),
    ]);
    setName(profile.name + (profile.synthetic ? ' — SYNTHETIC pharmacy/location' : ''));
    setCatalog(products); setStock(items);
  }
  useEffect(() => {
    api('/auth/session').then(async current => {setSession(current); await refresh(current); setMessage('Session restored.');})
      .catch(error => setMessage(error.message === 'Authentication required'
        ? 'Sign in with your privately provisioned pharmacy account.' : error.message));
  }, []);
  async function run(operation: () => Promise<void>) {
    setBusy(true); setMessage('');
    try {await operation();} catch (error) {setMessage(error instanceof Error ? error.message : 'Request failed');}
    finally {setBusy(false);}
  }
  function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    void run(async () => {
      const current = await api('/auth/login', 'POST', {username: data.get('username'), password: data.get('password')});
      form.reset(); setSession(current); await refresh(current); setMessage('Signed in.');
    });
  }
  function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    if (!session) return;
    void run(async () => {
      await api(`/pharmacies/${session.pharmacy_id}/inventory`, 'POST', {
        product_id: data.get('product_id'), quantity: Number(data.get('quantity')),
        price: data.get('price'), currency: 'PKR', sale_basis: data.get('sale_basis'),
      });
      form.reset(); await refresh(session); setMessage('Inventory added and stock confirmed.');
    });
  }
  function edit(event: FormEvent<HTMLFormElement>, item: Stock, field: 'price' | 'quantity') {
    event.preventDefault(); const data = new FormData(event.currentTarget); if (!session) return;
    const value = field === 'quantity' ? Number(data.get(field)) : data.get(field);
    void run(async () => {
      await api(`/pharmacies/${session.pharmacy_id}/inventory/${item.id}`, 'PATCH', {revision: item.revision, [field]: value});
      await refresh(session); setMessage(field === 'price' ? 'Price updated; stock confirmation unchanged.' : 'Quantity updated and stock confirmed.');
    });
  }
  function label(product: Product) {
    const pack = product.source_record.pack_size;
    return `${product.brand_name} — ${product.source_record.ingredients.map(item => `${item.name} ${item.strength.amount} ${item.strength.unit} per ${item.strength.per_amount} ${item.strength.per_unit}`).join(' + ')} — ${product.dosage_form ?? 'form unknown'} — ${pack ? `${pack.amount} ${pack.unit}` : 'pack unknown'}`;
  }
  return <main>
    <span className="badge">Academic demo — pharmacy inventory</span><h1>MEDIFIND</h1>
    <p>No real pharmacy availability or clinical alternatives are shown. Customer search is not available yet.</p>
    <p className="note">Catalog transcription: Getz Pharma all rights reserved. Source transcription is not clinical review.</p>
    <p role="status" aria-live="polite">{message}</p>
    {!session && <section><h2>Pharmacy login</h2><form onSubmit={login}>
      <label>Username<input name="username" autoComplete="username" required maxLength={80}/></label>
      <label>Password<input name="password" type="password" autoComplete="current-password" required maxLength={128}/></label>
      <button disabled={busy}>Sign in</button>
    </form></section>}
    {session && <>
      <section><h2>{name}</h2><button disabled={busy} onClick={() => void run(async () => {await refresh(session); setMessage('Reloaded current revisions.');})}>Reload inventory</button>
        <button disabled={busy} onClick={() => void run(async () => {await api('/auth/logout', 'POST'); setSession(null); setName(''); setStock([]); setCatalog([]);})}>Sign out</button>
      </section>
      <section><h2>Add catalog presentation</h2><form onSubmit={add}>
        <label>Exact presentation<select name="product_id" required>{catalog.map(product => <option key={product.product_id} value={product.product_id}>{label(product)}</option>)}</select></label>
        <label>Quantity<input name="quantity" type="number" min="0" step="1" max="2147483647" required/></label>
        <label>Price (PKR)<input name="price" type="text" inputMode="decimal" pattern="[0-9]+([.][0-9]{1,2})?" required/></label>
        <label>Sale basis<select name="sale_basis"><option value="pack">Per sourced pack/presentation</option><option value="unit">Per individual unit</option></select></label>
        <button disabled={busy || catalog.length === 0}>Add and confirm stock</button>
      </form></section>
      <section><h2>Own inventory</h2>{stock.length === 0 && <p>No inventory yet.</p>}
        {stock.map(item => <article key={`${item.id}:${item.revision}`}>
          <h3>{catalog.find(product => product.product_id === item.product_id)?.brand_name ?? item.product_id}</h3>
          <p>{catalog.find(product => product.product_id === item.product_id) && label(catalog.find(product => product.product_id === item.product_id)!)}</p>
          <p>Quantity: {item.quantity} · Price: {item.price} {item.currency} per {item.sale_basis} · Revision: {item.revision}</p>
          <p>Staff-confirmed: {new Date(item.stock_confirmed_at).toLocaleString()} — reported stock, not a reservation.</p>
          <form onSubmit={event => edit(event, item, 'quantity')}><label>New quantity<input name="quantity" type="number" min="0" step="1" defaultValue={item.quantity} required/></label><button disabled={busy}>Update quantity and confirm</button></form>
          <form onSubmit={event => edit(event, item, 'price')}><label>New price (PKR)<input name="price" type="text" inputMode="decimal" defaultValue={item.price} pattern="[0-9]+([.][0-9]{1,2})?" required/></label><button disabled={busy}>Update price only</button></form>
          <button disabled={busy} onClick={() => void run(async () => {await api(`/pharmacies/${session.pharmacy_id}/inventory/${item.id}/confirm`, 'POST', {revision: item.revision}); await refresh(session); setMessage('Stock explicitly confirmed.');})}>Confirm unchanged stock</button>
          <button disabled={busy} onClick={() => void run(async () => {await api(`/pharmacies/${session.pharmacy_id}/inventory/${item.id}`, 'DELETE', {revision: item.revision}); await refresh(session); setMessage('Inventory removed.');})}>Remove inventory</button>
        </article>)}
      </section>
    </>}
  </main>;
}

createRoot(document.getElementById('root')!).render(<App />);
