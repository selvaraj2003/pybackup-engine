'use strict';

// ── Token & Auth ──────────────────────────────────────────────────────
const Auth = {
  token: () => localStorage.getItem('pb-session'),
  user:  () => { try { return JSON.parse(localStorage.getItem('pb-user') || 'null'); } catch { return null; } },
  isAdmin: () => (Auth.user() || {}).role === 'admin',

  headers() {
    const t = this.token();
    return t ? { 'Content-Type': 'application/json', 'Authorization': `Bearer ${t}` }
             : { 'Content-Type': 'application/json' };
  },

  logout() {
    fetch('/api/auth/logout', { method: 'POST', headers: this.headers() }).catch(() => {});
    localStorage.removeItem('pb-session');
    localStorage.removeItem('pb-user');
    window.location.href = '/login.html';
  },

  redirectIfNotLoggedIn() {
    if (!this.token()) { window.location.href = '/login.html'; return true; }
    return false;
  },
};

// ── API ────────────────────────────────────────────────────────────────
const API = {
  async get(path) {
    const r = await fetch(`/api${path}`, { headers: Auth.headers() });
    if (r.status === 401) { Auth.logout(); throw new Error('Unauthorized'); }
    if (!r.ok) throw new Error(`API ${path} → ${r.status}`);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(`/api${path}`, {
      method: 'POST', headers: Auth.headers(), body: JSON.stringify(body),
    });
    if (r.status === 401) { Auth.logout(); throw new Error('Unauthorized'); }
    return r.json();
  },
  async del(path) {
    const r = await fetch(`/api${path}`, { method: 'DELETE', headers: Auth.headers() });
    if (r.status === 401) { Auth.logout(); throw new Error('Unauthorized'); }
    if (!r.ok) throw new Error(`DELETE ${path} → ${r.status}`);
    return r.json();
  },
};

// ── Toast ──────────────────────────────────────────────────────────────
function toast(msg, duration = 2800) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._tid);
  el._tid = setTimeout(() => el.classList.remove('show'), duration);
}

// ── Theme ──────────────────────────────────────────────────────────────
const ThemeManager = {
  current: () => document.documentElement.getAttribute('data-theme') || 'dark',
  set(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('pb-theme', theme);
    document.querySelectorAll('.theme-btn').forEach(b =>
      b.classList.toggle('active', b.dataset.themeVal === theme));
    Charts.rerender();
    API.post('/settings', { theme }).catch(() => {});
  },
  init() {
    const saved = localStorage.getItem('pb-theme') || 'dark';
    this.set(saved);
    const btn = document.getElementById('themeToggle');
    if (btn) btn.addEventListener('click', () =>
      this.set(this.current() === 'dark' ? 'light' : 'dark'));
    document.querySelectorAll('.theme-btn').forEach(b =>
      b.addEventListener('click', () => this.set(b.dataset.themeVal)));
  },
};

// ── Router ────────────────────────────────────────────────────────────
const Router = {
  titles: { dashboard:'Dashboard', runs:'Backup Runs', engines:'Engines',
            settings:'Settings', users:'Users' },
  init() {
    document.querySelectorAll('.nav-item').forEach(a =>
      a.addEventListener('click', e => { e.preventDefault(); this.navigate(a.dataset.view); }));
    document.querySelectorAll('.panel-link[data-view]').forEach(a =>
      a.addEventListener('click', e => { e.preventDefault(); this.navigate(a.dataset.view); }));
    const hash = window.location.hash.replace('#', '') || 'dashboard';
    this.navigate(hash);
  },
  navigate(view) {
    if (!document.getElementById(`view-${view}`)) view = 'dashboard';
    window.location.hash = view;
    const title = document.getElementById('pageTitle');
    if (title) title.textContent = this.titles[view] || view;
    document.querySelectorAll('.view').forEach(el =>
      el.classList.toggle('active', el.id === `view-${view}`));
    document.querySelectorAll('.nav-item').forEach(a =>
      a.classList.toggle('active', a.dataset.view === view));
    document.getElementById('sidebar')?.classList.remove('open');
    Views.load(view);
  },
};

// ── State ─────────────────────────────────────────────────────────────
const State = { runs: { data:[], total:0, page:0, limit:20, job:'', status:'' }, stats: null };

// ── Charts ────────────────────────────────────────────────────────────
const Charts = {
  _activity: null, _engine: null,
  cssVar: n => getComputedStyle(document.documentElement).getPropertyValue(n).trim(),
  renderActivity(daily) {
    const ctx = document.getElementById('activityChart');
    if (!ctx) return;
    if (this._activity) this._activity.destroy();
    const accent = this.cssVar('--accent'), green = this.cssVar('--green'),
          text2 = this.cssVar('--text2'), border = this.cssVar('--border'),
          bg2 = this.cssVar('--bg2');
    const map = {}; daily.forEach(d => { map[d.day] = d; });
    const labels = [], totals = [], oks = [];
    const now = new Date();
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now); d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      labels.push(key.slice(5));
      totals.push(map[key] ? map[key].total : 0);
      oks.push(map[key] ? map[key].ok : 0);
    }
    this._activity = new window.Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [
        { label:'Success', data:oks, backgroundColor:green+'99', borderRadius:3 },
        { label:'Failed',  data:totals.map((t,i)=>t-oks[i]), backgroundColor:accent+'55', borderRadius:3 },
      ]},
      options: { responsive:true, maintainAspectRatio:false, plugins:{
        legend:{labels:{color:text2,font:{family:'Inter',size:12},boxWidth:10}},
        tooltip:{backgroundColor:bg2,borderColor:border,borderWidth:1,titleColor:text2,bodyColor:text2},
      }, scales:{
        x:{stacked:true,ticks:{color:text2,font:{size:10},maxRotation:0,maxTicksLimit:10},grid:{color:border}},
        y:{stacked:true,ticks:{color:text2},grid:{color:border}},
      }},
    });
  },
  renderEngine(byEngine) {
    const ctx = document.getElementById('engineChart');
    if (!ctx || !byEngine.length) return;
    if (this._engine) this._engine.destroy();
    const COLORS = ['#6366f1','#22c55e','#38bdf8','#a78bfa','#eab308','#ef4444'];
    const text2 = this.cssVar('--text2'), bg2 = this.cssVar('--bg2'), border = this.cssVar('--border');
    this._engine = new window.Chart(ctx, {
      type: 'doughnut',
      data: { labels:byEngine.map(e=>e.engine||'unknown'),
              datasets:[{data:byEngine.map(e=>e.count),backgroundColor:COLORS,borderColor:bg2,borderWidth:2,hoverOffset:4}] },
      options: { responsive:true,maintainAspectRatio:false,cutout:'68%', plugins:{
        legend:{position:'bottom',labels:{color:text2,font:{family:'Inter',size:11},padding:12,boxWidth:10}},
        tooltip:{backgroundColor:bg2,borderColor:border,borderWidth:1,titleColor:text2,bodyColor:text2},
      }},
    });
  },
  rerender() { if (State.stats) { this.renderActivity(State.stats.daily||[]); this.renderEngine(State.stats.by_engine||[]); } },
};

// ── Formatting ────────────────────────────────────────────────────────
const fmtDate  = iso => iso ? new Date(iso).toLocaleString([],{dateStyle:'short',timeStyle:'short'}) : '—';
const fmtDur   = (s,e) => { if(!s||!e) return '—'; const ms=new Date(e)-new Date(s); if(ms<1000)return ms+'ms'; if(ms<60000)return(ms/1000).toFixed(1)+'s'; return Math.floor(ms/60000)+'m '+(ms%60000/1000|0)+'s'; };
const esc      = s => String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const badge    = s => { const cls={success:'badge-success',failed:'badge-failed',crashed:'badge-crashed',running:'badge-running'}; return `<span class="badge ${cls[s]||'badge-unknown'}">${s||'?'}</span>`; };
const ENGINE_DESC = {files:'Filesystem & configs',mongodb:'mongodump utility',postgresql:'pg_dump utility',mysql:'mysqldump utility',mssql:'sqlcmd BACKUP DATABASE'};

// ── Views ─────────────────────────────────────────────────────────────
const Views = {
  async load(view) {
    const fn = { dashboard:()=>this.loadDashboard(), runs:()=>this.loadRuns(),
                 engines:()=>this.loadEngines(), settings:()=>this.loadSettings(),
                 users:()=>this.loadUsers() }[view];
    if (fn) await fn();
  },

  async loadDashboard() {
    try {
      const data = State.stats = await API.get('/stats');
      const set = (id, v) => { const el=document.getElementById(id); if(el) el.textContent=v; };
      set('valTotal',   data.total??'—');
      set('valSuccess', data.success??'—');
      set('valFailed',  data.failed??'—');
      set('valRate',    `${data.success_rate??0}%`);
      const tbody = document.getElementById('recentBody');
      if (tbody) {
        tbody.innerHTML = (data.recent||[]).length
          ? data.recent.map(r=>`<tr><td><span class="job-name">${esc(r.job_name)}</span></td><td><span class="engine-tag">${esc(r.engine)}</span></td><td>${badge(r.status)}</td><td>${fmtDate(r.started_at)}</td><td>${fmtDur(r.started_at,r.finished_at)}</td></tr>`).join('')
          : '<tr><td colspan="5"><div class="empty-state"><p>No backup runs yet.</p></div></td></tr>';
      }
      await this._loadChartJs();
      Charts.renderActivity(data.daily||[]);
      Charts.renderEngine(data.by_engine||[]);
    } catch(err) { console.error(err); toast('⚠ Failed to load dashboard'); }
  },

  async loadRuns(page=0) {
    State.runs.page = page;
    const {limit,job,status} = State.runs;
    const qs = new URLSearchParams({limit,offset:page*limit,...(job?{job}:{}),...(status?{status}:{})});
    try {
      const data = await API.get(`/runs?${qs}`);
      State.runs.data = data.runs; State.runs.total = data.total;
      const tbody = document.getElementById('runsBody');
      if (!tbody) return;
      if (!data.runs.length) {
        tbody.innerHTML = '<tr><td colspan="8"><div class="empty-state"><p>No backup runs match your filter.</p></div></td></tr>';
      } else {
        tbody.innerHTML = data.runs.map(r=>`<tr>
          <td style="color:var(--text3);font-size:.8rem">#${r.id}</td>
          <td><span class="job-name">${esc(r.job_name)}</span></td>
          <td><span class="engine-tag">${esc(r.engine)}</span></td>
          <td>${badge(r.status)}</td>
          <td>${fmtDate(r.started_at)}</td>
          <td>${fmtDur(r.started_at,r.finished_at)}</td>
          <td><span class="output-path" title="${esc(r.output_path||'')}">${esc(r.output_path||'—')}</span></td>
          <td style="display:flex;gap:6px">
            <button class="btn-icon btn-icon-blue" onclick="Modal.show(${r.id})"><svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.3"/><path d="M8 7v4M8 5.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg></button>
            ${Auth.isAdmin()?`<button class="btn-icon btn-icon-red" onclick="Runs.del(${r.id})"><svg viewBox="0 0 16 16" fill="none"><path d="M3 4h10M6 4V3h4v1M5 4v8h6V4H5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg></button>`:''}
          </td></tr>`).join('');
      }
      this._renderPagination(data.total, limit, page);
    } catch(err) { console.error(err); toast('⚠ Failed to load runs'); }
  },

  _renderPagination(total, limit, page) {
    const el = document.getElementById('runsPagination'); if (!el) return;
    const pages = Math.ceil(total/limit);
    if (pages <= 1) { el.innerHTML=''; return; }
    let html = `<span>${total} total</span>&nbsp;`;
    for (let i=0; i<pages; i++)
      html += `<button class="page-btn ${i===page?'active':''}" onclick="Views.loadRuns(${i})">${i+1}</button>`;
    el.innerHTML = html;
  },

  async loadEngines() {
    try {
      const data = await API.get('/stats');
      const grid = document.getElementById('enginesGrid'); if (!grid) return;
      const byEng = {}; (data.by_engine||[]).forEach(e=>{ byEng[e.engine]=e; });
      const COLORS = {files:'var(--yellow-bg)',mongodb:'var(--green-bg)',postgresql:'var(--blue-bg)',mysql:'var(--blue-bg)',mssql:'var(--purple-bg)'};
      const EMOJI  = {files:'📁',mongodb:'🍃',postgresql:'🐘',mysql:'🐬',mssql:'🪟'};
      grid.innerHTML = ['files','mongodb','postgresql','mysql','mssql'].map(name=>{
        const info = byEng[name]||{count:0,successes:0};
        const rate = info.count ? Math.round(info.successes/info.count*100) : 0;
        return `<div class="engine-card">
          <div class="engine-card-header">
            <div class="engine-icon" style="background:${COLORS[name]||'var(--bg4)'};font-size:1.3rem">${EMOJI[name]||'🔧'}</div>
            <div><div class="engine-card-name">${name}</div><div class="engine-card-sub">${ENGINE_DESC[name]||''}</div></div>
          </div>
          <div class="engine-stats">
            <div class="engine-stat"><div class="engine-stat-val">${info.count}</div><div class="engine-stat-key">Runs</div></div>
            <div class="engine-stat"><div class="engine-stat-val">${info.successes||0}</div><div class="engine-stat-key">Success</div></div>
            <div class="engine-stat"><div class="engine-stat-val">${rate}%</div><div class="engine-stat-key">Rate</div></div>
          </div></div>`;
      }).join('');
    } catch(err) { console.error(err); toast('⚠ Failed to load engines'); }
  },

  async loadSettings() {
    try {
      const data = await API.get('/settings');
      if (data.retention_days) { const el=document.getElementById('retentionDays'); if(el) el.value=data.retention_days; }
      if (data.log_level) { const el=document.getElementById('logLevel'); if(el) el.value=data.log_level; }
    } catch {}
    // Show current user info
    const user = Auth.user();
    const userInfo = document.getElementById('currentUserInfo');
    if (userInfo && user) userInfo.textContent = `${user.username} (${user.role})`;
  },

  async loadUsers() {
    if (!Auth.isAdmin()) {
      const grid = document.getElementById('usersGrid');
      if (grid) grid.innerHTML = '<div class="empty-state"><p>Admin access required.</p></div>';
      return;
    }
    try {
      const data = await API.get('/users');
      const tbody = document.getElementById('usersBody'); if (!tbody) return;
      if (!data.users.length) {
        tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><p>No users found.</p></div></td></tr>';
      } else {
        tbody.innerHTML = data.users.map(u=>`<tr>
          <td>#${u.id}</td>
          <td><span class="job-name">${esc(u.username)}</span></td>
          <td><span class="badge ${u.role==='admin'?'badge-running':'badge-unknown'}">${u.role}</span></td>
          <td>${esc(u.email||'—')}</td>
          <td>${fmtDate(u.last_login)}</td>
          <td>
            <button class="btn-icon btn-icon-red" onclick="Users.del(${u.id},'${esc(u.username)}')">
              <svg viewBox="0 0 16 16" fill="none"><path d="M3 4h10M6 4V3h4v1M5 4v8h6V4H5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </td></tr>`).join('');
      }
    } catch(err) { console.error(err); toast('⚠ Failed to load users'); }
  },

  _chartJsLoaded: false,
  _loadChartJs() {
    if (this._chartJsLoaded || window.Chart) { this._chartJsLoaded=true; return Promise.resolve(); }
    return new Promise((res,rej) => {
      const s=document.createElement('script');
      s.src='https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
      s.onload=()=>{ this._chartJsLoaded=true; res(); }; s.onerror=rej;
      document.head.appendChild(s);
    });
  },
};

// ── Runs actions ──────────────────────────────────────────────────────
const Runs = {
  async del(id) {
    if (!confirm(`Delete run #${id}?`)) return;
    try { await API.del(`/runs/${id}`); toast(`Run #${id} deleted`); Views.loadRuns(State.runs.page); }
    catch { toast('⚠ Failed to delete run'); }
  },
};

// ── Users actions ─────────────────────────────────────────────────────
const Users = {
  async del(id, username) {
    if (!confirm(`Delete user "${username}"?`)) return;
    try {
      const data = await API.del(`/users/${id}`);
      if (data.error) { toast(`⚠ ${data.error}`); return; }
      toast(`User ${username} deleted`);
      Views.loadUsers();
    } catch(err) { toast('⚠ Failed to delete user'); }
  },
};

// ── Modal ─────────────────────────────────────────────────────────────
const Modal = {
  async show(runId) {
    try {
      const run = await API.get(`/runs/${runId}`);
      const title = document.getElementById('modalTitle');
      if (title) title.textContent = `Run #${runId} — ${run.job_name}`;
      const body = document.getElementById('modalBody');
      if (body) body.innerHTML = `
        <div class="detail-grid">
          <div class="detail-item"><div class="detail-key">Status</div><div class="detail-val">${badge(run.status)}</div></div>
          <div class="detail-item"><div class="detail-key">Engine</div><div class="detail-val">${esc(run.engine)}</div></div>
          <div class="detail-item"><div class="detail-key">Started</div><div class="detail-val">${fmtDate(run.started_at)}</div></div>
          <div class="detail-item"><div class="detail-key">Duration</div><div class="detail-val">${fmtDur(run.started_at,run.finished_at)}</div></div>
          <div class="detail-item" style="grid-column:1/-1"><div class="detail-key">Output</div><div class="detail-val" style="font-family:monospace;font-size:.8rem">${esc(run.output_path||'—')}</div></div>
        </div>
        ${run.error?`<div class="error-block">${esc(run.error)}</div>`:''}
      `;
      document.getElementById('modalOverlay')?.classList.add('open');
    } catch { toast('⚠ Failed to load run details'); }
  },
  close() { document.getElementById('modalOverlay')?.classList.remove('open'); },
};

// ── Init ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (Auth.redirectIfNotLoggedIn()) return;

  ThemeManager.init();

  // Show user info in topbar
  const user = Auth.user();
  const userBadge = document.getElementById('userBadge');
  if (userBadge && user) userBadge.textContent = user.username;

  // Hide Users nav item for non-admins
  if (!Auth.isAdmin()) {
    document.querySelector('[data-view="users"]')?.style.setProperty('display','none');
  }

  Router.init();

  // Sidebar toggle (mobile)
  document.getElementById('menuToggle')?.addEventListener('click', () =>
    document.getElementById('sidebar')?.classList.toggle('open'));

  // Refresh
  document.getElementById('refreshBtn')?.addEventListener('click', () => {
    const active = document.querySelector('.view.active')?.id?.replace('view-','') || 'dashboard';
    Views.load(active); toast('Refreshed');
  });

  // Logout
  document.getElementById('logoutBtn')?.addEventListener('click', () => Auth.logout());

  // Runs filter
  document.getElementById('runSearch')?.addEventListener('input', debounce(e => {
    State.runs.job = e.target.value.trim(); Views.loadRuns(0);
  }, 350));
  document.getElementById('runStatusFilter')?.addEventListener('change', e => {
    State.runs.status = e.target.value; Views.loadRuns(0);
  });

  // Add test run
  document.getElementById('addTestRunBtn')?.addEventListener('click', async () => {
    const engines=['files','mongodb','postgresql','mysql','mssql'];
    const statuses=['success','success','success','failed','crashed'];
    const engine=engines[Math.floor(Math.random()*engines.length)];
    const status=statuses[Math.floor(Math.random()*statuses.length)];
    try {
      await API.post('/runs',{job_name:`test-${engine}-${Date.now()%10000}`,engine,status,
        output_path:status==='success'?`/backups/${engine}/latest`:null,
        error:status!=='success'?'Simulated error':null});
      toast(`Test run added (${engine}/${status})`); Views.loadRuns(State.runs.page);
    } catch { toast('⚠ Failed to add test run'); }
  });

  // Save settings
  document.getElementById('saveSettingsBtn')?.addEventListener('click', async () => {
    const body = {
      retention_days: document.getElementById('retentionDays')?.value,
      log_level:      document.getElementById('logLevel')?.value,
      theme:          ThemeManager.current(),
    };
    try {
      await API.post('/settings', body);
      const el = document.getElementById('saveStatus');
      if (el) { el.textContent='✓ Saved'; setTimeout(()=>el.textContent='',2500); }
      toast('Settings saved');
    } catch { toast('⚠ Failed to save settings'); }
  });

  // Add user form
  document.getElementById('addUserForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const username = document.getElementById('newUsername')?.value.trim();
    const password = document.getElementById('newPassword')?.value;
    const role     = document.getElementById('newRole')?.value;
    const email    = document.getElementById('newEmail')?.value.trim() || null;
    const errEl    = document.getElementById('addUserError');
    if (errEl) errEl.textContent = '';
    try {
      const res = await API.post('/users', { username, password, role, email });
      if (res.error) { if (errEl) errEl.textContent = res.error; return; }
      toast(`User "${username}" created`);
      e.target.reset();
      Views.loadUsers();
    } catch { toast('⚠ Failed to create user'); }
  });

  // Change password form
  document.getElementById('changePasswordForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const current = document.getElementById('currentPassword')?.value;
    const newPw   = document.getElementById('newPassword2')?.value;
    const confirm = document.getElementById('confirmPassword')?.value;
    const errEl   = document.getElementById('changePwError');
    const okEl    = document.getElementById('changePwOk');
    if (errEl) errEl.textContent=''; if (okEl) okEl.textContent='';
    try {
      const res = await API.post('/auth/change-password',
        { current_password:current, new_password:newPw, confirm_password:confirm });
      if (res.error) { if (errEl) errEl.textContent=res.error; return; }
      if (okEl) okEl.textContent = '✓ Password changed. You will be logged out.';
      setTimeout(() => Auth.logout(), 2000);
    } catch { toast('⚠ Failed to change password'); }
  });

  // Modal close
  document.getElementById('modalClose')?.addEventListener('click', () => Modal.close());
  document.getElementById('modalOverlay')?.addEventListener('click', e => {
    if (e.target === document.getElementById('modalOverlay')) Modal.close();
  });
  document.addEventListener('keydown', e => { if (e.key==='Escape') Modal.close(); });

  // Health ping
  setInterval(async () => {
    try { await fetch('/api/stats',{headers:Auth.headers()}); document.getElementById('statusDot').style.background='var(--green)'; }
    catch { document.getElementById('statusDot').style.background='var(--red)'; }
  }, 30000);

  // Expose globals
  window.Modal = Modal; window.Runs = Runs; window.Views = Views; window.Users = Users;
});

function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t=setTimeout(()=>fn(...a),ms); }; }
