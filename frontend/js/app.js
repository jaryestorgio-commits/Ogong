const apiBase = 'http://localhost:5000/api';

function getStoredUser() {
  return JSON.parse(localStorage.getItem('ogongUser') || 'null');
}

function setStoredUser(user) {
  localStorage.setItem('ogongUser', JSON.stringify(user));
}

function clearStoredUser() {
  localStorage.removeItem('ogongUser');
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    headers: {
      'Content-Type': 'application/json'
    },
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || 'API request failed.');
  }
  return data;
}

function navigateTo(page) {
  window.location.href = page;
}

function requireAuth(allowedRoles = []) {
  const user = getStoredUser();
  if (!user) {
    navigateTo('login.html');
    return null;
  }
  if (allowedRoles.length && !allowedRoles.includes(user.role)) {
    navigateTo('dashboard.html');
    return null;
  }
  document.querySelectorAll('.current-user').forEach(el => {
    el.textContent = `${user.name} (${user.role})`;
  });
  return user;
}

function logout() {
  clearStoredUser();
  navigateTo('login.html');
}

function sidebarIcon(name) {
  const paths = {
    dashboard: '<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/>',
    pos: '<path d="M4 4v16h16"/><path d="M8 16h8M8 12h5M8 8h8"/>',
    products: '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z"/><path d="m4.5 7.5 7.5 4 7.5-4M12 12v9"/>',
    categories: '<path d="M4 5h16M4 12h16M4 19h16"/><circle cx="8" cy="5" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="10" cy="19" r="2"/>',
    suppliers: '<path d="M3 7h11v10H3zM14 10h4l3 3v4h-7z"/><circle cx="7" cy="19" r="2"/><circle cx="17" cy="19" r="2"/>',
    reports: '<path d="M4 20V4M4 20h16"/><path d="m8 15 3-3 3 2 5-6"/>',
    users: '<circle cx="9" cy="8" r="3"/><path d="M3 20c.5-3 2.5-5 6-5s5.5 2 6 5M16 5.5a3 3 0 0 1 0 5.8M17 15c2.3.4 3.6 2 4 4"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.8 1.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-2.5V20a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1-1.8-1.8.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H6.3v-2.5H6.5a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1 1.8-1.8.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6V5h2.5v.2a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.8 1.8-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v2.5h-.2a1.7 1.7 0 0 0-1.6 1Z"/>',
    logout: '<path d="M10 5H5v14h5M14 8l4 4-4 4M18 12H9"/>'
  };
  return `<svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.dashboard}</svg>`;
}

function sidebarLink(page, label, icon, activePage) {
  return `<a class="nav-link ${activePage === page ? 'active' : ''}" href="${page}.html" title="${label}" aria-current="${activePage === page ? 'page' : 'false'}">${sidebarIcon(icon)}<span class="nav-label">${label}</span></a>`;
}

function setupSidebarDrawer() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar || document.querySelector('.sidebar-toggle')) return;
  const toggle = document.createElement('button');
  toggle.className = 'sidebar-toggle';
  toggle.type = 'button';
  toggle.setAttribute('aria-label', 'Open navigation');
  toggle.innerHTML = '<span></span><span></span><span></span>';
  const overlay = document.createElement('button');
  overlay.className = 'sidebar-overlay';
  overlay.type = 'button';
  overlay.setAttribute('aria-label', 'Close navigation');
  document.body.append(toggle, overlay);
  const close = () => { sidebar.classList.remove('is-open'); overlay.classList.remove('is-visible'); };
  toggle.addEventListener('click', () => { sidebar.classList.add('is-open'); overlay.classList.add('is-visible'); });
  overlay.addEventListener('click', close);
  sidebar.querySelectorAll('.nav-link').forEach(link => link.addEventListener('click', close));
}

function renderSidebar(activePage) {
  const user = getStoredUser();
  const nav = document.getElementById('sidebar-nav');
  if (!nav) return;
  const isAdmin = user?.role === 'ADMIN';
  nav.innerHTML = `
    <div class="sidebar-section"><div class="sidebar-section-label">Main</div>
      ${sidebarLink('dashboard', 'Dashboard', 'dashboard', activePage)}
      ${sidebarLink('pos', 'POS / Sales', 'pos', activePage)}
      ${sidebarLink('products', 'Products', 'products', activePage)}
      ${sidebarLink('categories', 'Categories', 'categories', activePage)}
      ${sidebarLink('suppliers', 'Suppliers', 'suppliers', activePage)}
    </div>
    ${isAdmin ? `<div class="sidebar-section"><div class="sidebar-section-label">Reports</div>
      ${sidebarLink('reports', 'Reports', 'reports', activePage)}
      ${sidebarLink('sales', 'Sales History', 'reports', activePage)}
    </div>` : ''}
    ${isAdmin ? `<div class="sidebar-section"><div class="sidebar-section-label">Management</div>${sidebarLink('users', 'Users / Staff', 'users', activePage)}</div>` : ''}
    <div class="sidebar-profile">
      <div class="sidebar-avatar">${(user?.name || user?.username || 'U').charAt(0).toUpperCase()}</div>
      <div class="sidebar-profile-copy"><strong>${user?.name || user?.username || 'User'}</strong><span>${isAdmin ? 'Administrator' : 'Staff Account'}</span></div>
      <button class="sidebar-profile-action" type="button" title="Log out" aria-label="Log out" onclick="logout()">${sidebarIcon('logout')}</button>
    </div>
  `;
  setupSidebarDrawer();
}

function renderTopbar() {
  const user = getStoredUser();
  if (!user) return;
  document.querySelectorAll('.current-user').forEach(el => {
    el.textContent = `${user.name} (${user.role})`;
  });
  const headers = document.querySelectorAll('.header');
  headers.forEach(h => {
    if (h.querySelector('.header-right')) return; // already rendered
    const right = document.createElement('div');
    right.className = 'header-right';
    right.innerHTML = `
      <div style="text-align:right">
        <div class="header-user">${user.name}</div>
        <div class="role-badge">${user.role}</div>
        <div class="header-datetime"><span class="header-date"></span> <span class="header-time"></span></div>
        <div><button class="button button-secondary" onclick="logout()">Logout</button></div>
      </div>
    `;
    h.appendChild(right);
  });
  function updateDateTime() {
    const now = new Date();
    const date = now.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    document.querySelectorAll('.header-date').forEach(el => el.textContent = date);
    document.querySelectorAll('.header-time').forEach(el => el.textContent = time);
  }
  updateDateTime();
  setInterval(updateDateTime, 60000);
}

function showAlert(message, type = 'info', targetId = 'alert-container') {
  const container = document.getElementById(targetId);
  if (!container) return;
  container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
  setTimeout(() => { container.innerHTML = ''; }, 4000);
}

function formatCurrency(amount) {
  return `₱${Number(amount).toLocaleString('en-PH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

function createOption(value, text) {
  const option = document.createElement('option');
  option.value = value;
  option.textContent = text;
  return option;
}

function closeModal(modalId) {
  document.getElementById(modalId)?.classList.remove('open');
}

function openModal(modalId) {
  document.getElementById(modalId)?.classList.add('open');
}

function setupModalClose(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.querySelector('.modal-close')?.addEventListener('click', () => closeModal(modalId));
  modal.addEventListener('click', e => {
    if (e.target === modal) closeModal(modalId);
  });
}

function setText(elementId, text) {
  const el = document.getElementById(elementId);
  if (el) el.textContent = text;
}
