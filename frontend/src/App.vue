<script setup>
import { ref, onMounted } from 'vue';

const API_URL = 'http://localhost:8000/api/v1';

const token = ref(localStorage.getItem('access_token') || '');
const username = ref('');
const password = ref('');
const error = ref('');
const funds = ref([]);
const subscriptions = ref([]);
const loading = ref(false);

const login = async () => {
  error.value = '';
  loading.value = true;
  try {
    const response = await fetch(`${API_URL}/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value })
    });
    if (!response.ok) throw new Error('Invalid credentials');
    const data = await response.json();
    token.value = data.access;
    localStorage.setItem('access_token', data.access);
    await fetchData();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

const logout = () => {
  token.value = '';
  funds.value = [];
  subscriptions.value = [];
  localStorage.removeItem('access_token');
};

const fetchWithAuth = async (endpoint) => {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: { 'Authorization': `Bearer ${token.value}` }
  });
  if (response.status === 401) {
    logout();
    throw new Error('Session expired');
  }
  return response.json();
};

const fetchData = async () => {
  if (!token.value) return;
  loading.value = true;
  try {
    funds.value = await fetchWithAuth('/funds/');
    subscriptions.value = await fetchWithAuth('/subscriptions/');
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  if (token.value) fetchData();
});

const formatAmount = (value) =>
  new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
</script>

<template>
  <main class="container">
    <div class="brand-bar">
      <span class="brand-name">CapCall</span>
      <span class="brand-tag">Investor Portal</span>
    </div>

    <div v-if="!token" class="login-box">
      <h2>Connect to backend</h2>
      <p class="login-hint">Log in as <code>manager</code> or <code>investor1</code> to test permissions.</p>
      <form @submit.prevent="login">
        <input v-model="username" type="text" placeholder="Username" required />
        <input v-model="password" type="password" placeholder="Password" required />
        <button type="submit" :disabled="loading">
          {{ loading ? 'Connecting…' : 'Login' }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>

    <div v-else>
      <header class="dashboard-header">
        <div class="status-dot-group">
          <span class="status-dot"></span>
          <span class="status-label">Connected to backend</span>
        </div>
        <button @click="logout" class="logout-btn">Logout</button>
      </header>

      <p v-if="loading" class="loading-text">Loading data from the database…</p>

      <div v-else>
        <section class="panel">
          <h2>Available Funds</h2>
          <ul class="fund-list">
            <li v-for="fund in funds" :key="fund.id" class="fund-item">
              <span class="fund-name">{{ fund.fund_name }}</span>
              <span class="fund-size">{{ formatAmount(fund.fund_size) }} <em>{{ fund.currency }}</em></span>
            </li>
          </ul>
        </section>

        <section class="panel">
          <h2>Active Subscriptions</h2>
          <table>
            <thead>
              <tr>
                <th>Investor</th>
                <th>Fund</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="sub in subscriptions" :key="sub.id">
                <td>{{ sub.investor_name || 'Me' }}</td>
                <td>{{ sub.fund }}</td>
                <td class="amount">{{ formatAmount(sub.amount) }}</td>
                <td>
                  <span class="badge" :class="sub.status.toLowerCase()">
                    {{ sub.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </div>
  </main>
</template>

<style>
:root {
  --bg:           #ffffff;
  --surface:      #f1f5f9;
  --border:       #e2e8f0;
  --teal:         #208e8d;
  --teal-dim:     #165f5e;
  --lime:         #96b706;
  --jade:         #00a36c;
  --text-primary: #1e293b;
  --text-muted:   #64748b;
  --red:          #ef4444;
}
</style>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.container {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  max-width: 900px;
  margin: 3rem auto;
  color: var(--text-primary);
  min-height: 100vh;
  padding: 0 1.5rem 4rem;
}

.brand-bar {
  display: flex;
  align-items: baseline;
  gap: 0.10rem;
  padding: 2rem 0 2.5rem;
  margin-bottom: 2.5rem;
}
.brand-name {
  font-size: 1.50rem;
  font-weight: 700;
  color: var(--teal);
  letter-spacing: -0.02em;
}
.brand-tag {
  font-size: 0.70rem;
  font-weight: 500;
  color: var(--lime);
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  vertical-align: middle;
  position: relative;
  top: 2px;
}

.login-box {
  background: var(--surface);
  padding: 2.5rem;
  border-radius: 10px;
  max-width: 420px;
  margin: 0 auto;
  border: 1px solid var(--border);
}
.login-box h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem;
}
.login-hint {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0 0 1.75rem;
}
.login-hint code {
  background: rgba(32, 142, 141, 0.15);
  color: var(--teal);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
}

input {
  display: block;
  width: 100%;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 0.9rem;
  box-sizing: border-box;
  transition: border-color 0.15s;
}
input:focus {
  outline: none;
  border-color: var(--teal);
}
input::placeholder { color: var(--text-muted); }

button {
  background: var(--teal);
  color: #fff;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  width: 100%;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  transition: background 0.15s, transform 0.1s;
}
button:active:not(:disabled) { transform: translateY(1px); }
button:disabled { opacity: 0.5; cursor: not-allowed; }

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  padding: 12px 0;
  margin-bottom: 2rem;
}
.status-dot-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--jade);
  box-shadow: 0 0 6px var(--jade);
}
.status-label {
  font-size: 0.85rem;
  color: var(--text-muted);
}
.logout-btn {
  background: transparent;
  color: var(--text-muted);
  width: auto;
  padding: 6px 14px;
  font-size: 0.8rem;
}
.logout-btn:hover {
  color: var(--red);
}

.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.75rem;
  margin-bottom: 1.5rem;
}
.panel h2 {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--teal);
  margin: 0 0 1.25rem;
}

.fund-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.fund-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
}
.fund-name {
  font-weight: 500;
  font-size: 0.9rem;
}
.fund-size {
  font-family: 'IBM Plex Mono', 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
  color: var(--jade);
}
.fund-size em {
  font-style: normal;
  color: var(--text-muted);
  margin-left: 4px;
  font-size: 0.75rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}
th {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 0 12px 10px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

th:nth-child(3), td:nth-child(3),
th:last-child, td:last-child {
  text-align: right;
}

td {
  padding: 13px 12px;
  font-size: 0.875rem;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(0, 0, 0, 0.02); }

.amount {
  font-family: 'IBM Plex Mono', 'JetBrains Mono', monospace;
  font-variant-numeric: tabular-nums;
  color: var(--jade);
  font-weight: 600;
}

.badge {
  padding: 4px 10px;
  border-radius: 5px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.draft     { background: #dde3ed; color: #475569; }
.submitted { background: #fef3c7; color: #b45309; }
.approved  { background: #ccfbf1; color: #0f766e; }
.funded    { background: #dcfce7; color: #15803d; }

.loading-text {
  color: var(--text-muted);
  font-size: 0.85rem;
  text-align: center;
  padding: 3rem 0;
}
.error {
  color: var(--red);
  font-size: 0.82rem;
  margin-top: 0.75rem;
}
</style>