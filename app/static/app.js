// Study Notebook — Client-side SPA logic

const API = '';
const viewTitles = {
  home: 'Home',
  capture: 'Capture',
  library: 'Library',
  search: 'Search',
  detail: 'Detail',
};

const browseState = {
  type: 'all',
  query: '',
  sort: 'recent',
  collection: null,
};
let browseMaterials = [];

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

// View switching
function showView(viewName) {
  $$('.view').forEach(v => v.classList.remove('active'));
  const view = document.getElementById('view-' + viewName);
  if (view) view.classList.add('active');
  const title = $('#page-title');
  if (title) title.textContent = viewTitles[viewName] || 'Study Notebook';
  $$('.sidebar-link').forEach(link => {
    link.classList.toggle('active', link.dataset.view === viewName);
  });
  if (viewName === 'browse' || viewName === 'library') loadBrowse();
  if (viewName === 'search') $('#search-input').focus();
  if (viewName === 'home') loadRecent();
}

// Navigation via data-view on any clickable element
document.addEventListener('click', e => {
  const trigger = e.target.closest('[data-view]');
  if (!trigger) return;
  e.preventDefault();
  showView(trigger.dataset.view);
});

// Helper: fetch with JSON body and error handling
async function apiFetch(url, options = {}) {
  const defaults = {
    headers: { 'Content-Type': 'application/json' },
  };
  if (options.body && typeof options.body === 'object') {
    options.body = JSON.stringify(options.body);
  }
  const merged = { ...defaults, ...options };
  const res = await fetch(`${API}${url}`, merged);
  if (!res.ok) {
    const text = await res.text();
    let msg = `HTTP ${res.status}`;
    try { msg = JSON.parse(text).detail || msg; } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

// Shared capture handler
async function submitCapture(formId, resultId) {
  const form = $(formId);
  const result = $(resultId);
  if (!form) return;

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const title = $(formId + ' #cap-title, ' + formId + ' #cap-title-full').value.trim();
    const material_type = $(formId + ' #cap-type, ' + formId + ' #cap-type-full').value;
    const topic_summary = $(formId + ' #cap-topic, ' + formId + ' #cap-topic-full').value.trim();
    const language = $(formId + ' #cap-language, ' + formId + ' #cap-language-full').value.trim();
    const content = $(formId + ' #cap-content, ' + formId + ' #cap-content-full').value.trim();
    const tags = $(formId + ' #cap-tags, ' + formId + ' #cap-tags-full').value.trim();
    const change_note = $(formId + ' #cap-change-note, ' + formId + ' #cap-change-note-full').value.trim();

    if (!title) return;

    try {
      const mat = await apiFetch('/materials/', {
        method: 'POST',
        body: { title, material_type, topic_summary },
      });

      if (content || language) {
        const ver = await apiFetch(`/materials/${mat.id}/versions`, {
          method: 'POST',
          body: { language, change_note: change_note || 'Initial version', test_status: 'untested' },
        });

        const blockType = material_type === 'snippet' ? 'code' : 'text';
        await apiFetch(`/materials/${mat.id}/versions/${ver.id}/blocks`, {
          method: 'POST',
          body: {
            block_order: 0,
            block_type: blockType,
            language,
            text_content: content,
            code_content: content,
          },
        });
      }

      if (tags) {
        const tagNames = tags.split(',').map(t => t.trim()).filter(Boolean);
        for (const tagName of tagNames) {
          await apiFetch(`/materials/${mat.id}/tags`, {
            method: 'POST',
            body: { tag_name: tagName },
          });
        }
      }

      result.classList.remove('hidden');
      result.innerHTML = `<div class="toast success">Saved: ${esc(title)}</div>`;
      form.reset();
      setTimeout(() => result.classList.add('hidden'), 3000);
    } catch (err) {
      result.classList.remove('hidden');
      result.innerHTML = `<div class="toast error">Error: ${esc(err.message)}</div>`;
    }
  });
}

submitCapture('#capture-form', '#capture-result');
submitCapture('#capture-form-full', '#capture-result-full');

// Load recent materials (home sidebar + home page)
async function loadRecent() {
  try {
    const materials = await apiFetch('/materials/recent?limit=10');
    const container = $('#recent-cards');
    if (!container) return;
    if (!materials.length) {
      container.innerHTML = '<p>No materials yet. Start capturing!</p>';
      return;
    }
    container.innerHTML = materials.map(m => `
      <div class="material-card" onclick="loadDetail(${m.id})">
        <h3>${esc(m.title)}</h3>
        <div class="meta">${m.material_type} · ${m.updated_at || 'unknown'}</div>
        ${m.topic_summary ? `<div class="meta">${esc(m.topic_summary)}</div>` : ''}
      </div>
    `).join('');
  } catch (err) {
    const container = $('#recent-cards');
    if (container) container.innerHTML = `<p class="toast error">Error: ${esc(err.message)}</p>`;
  }
}

// Load sidebar recent
async function loadSidebarRecent() {
  try {
    const materials = await apiFetch('/materials/recent?limit=5');
    const container = $('#sidebar-recent');
    if (!container) return;
    if (!materials.length) {
      container.innerHTML = '<p class="sidebar-item"><em>No recent materials</em></p>';
      return;
    }
    container.innerHTML = materials.map(m => `
      <div class="sidebar-item" onclick="loadDetail(${m.id})">
        <div><strong>${esc(m.title)}</strong></div>
        <div class="meta">${m.material_type}</div>
      </div>
    `).join('');
  } catch (err) {
    const container = $('#sidebar-recent');
    if (container) container.innerHTML = `<p class="sidebar-item"><em>Error loading recent</em></p>`;
  }
}

// Load browse list
async function loadBrowse() {
  try {
    browseMaterials = await apiFetch('/materials/');
    renderBrowse();
  } catch (err) {
    const list = $('#browse-list');
    if (list) list.innerHTML = `<p class="toast error">Error loading materials: ${esc(err.message)}</p>`;
  }
}

function inferCollection(material) {
  const text = `${material.title || ''} ${material.topic_summary || ''}`.toLowerCase();
  if (text.includes('function')) return 'functions';
  if (text.includes('question') || text.includes('quiz')) return 'questions';
  if (text.includes('setup') || text.includes('install') || text.includes('apex')) return 'setup';
  return 'practice';
}

function renderBrowse() {
  const list = $('#browse-list');
  if (!list) return;
  let materials = [...browseMaterials];
  if (browseState.type !== 'all') {
    materials = materials.filter(m => m.material_type === browseState.type);
  }
  if (browseState.query) {
    const q = browseState.query.toLowerCase();
    materials = materials.filter(m =>
      `${m.title || ''} ${m.topic_summary || ''}`.toLowerCase().includes(q)
    );
  }
  if (browseState.collection) {
    materials = materials.filter(m => inferCollection(m) === browseState.collection);
  }
  if (browseState.sort === 'title') {
    materials.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
  } else if (browseState.sort === 'oldest') {
    materials.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''));
  } else {
    materials.sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
  }
  const status = $('#library-status');
  if (status) {
    const collectionLabel = browseState.collection ? ` in ${browseState.collection}` : '';
    status.textContent = `${materials.length} item(s) shown${collectionLabel}`;
  }

  if (!materials.length) {
    list.innerHTML = '<p>No materials match your current filters.</p>';
    return;
  }
  list.innerHTML = materials.map(m => `
    <div class="material-card" onclick="loadDetail(${m.id})">
      <h3>${esc(m.title)}</h3>
      <div class="meta">${m.material_type} · ${m.updated_at || 'unknown'}</div>
      ${m.topic_summary ? `<div class="meta">${esc(m.topic_summary)}</div>` : ''}
      <div class="tags"><span class="tag">${esc(inferCollection(m))}</span></div>
    </div>
  `).join('');
}

function setCollectionFilter(collection) {
  browseState.collection = collection;
  showView('library');
  renderBrowse();
}

// Library controls
$('#library-filter-input').addEventListener('input', e => {
  browseState.query = e.target.value.trim();
  renderBrowse();
});
$('#library-sort').addEventListener('change', e => {
  browseState.sort = e.target.value;
  renderBrowse();
});
$$('.type-filter').forEach(btn => {
  btn.addEventListener('click', () => {
    browseState.type = btn.dataset.type;
    $$('.type-filter').forEach(el => el.classList.remove('active'));
    btn.classList.add('active');
    renderBrowse();
  });
});
$$('.collection-card').forEach(btn => {
  btn.addEventListener('click', () => setCollectionFilter(btn.dataset.collection));
});

// Shortcut: slash to search, n for new note
document.addEventListener('keydown', e => {
  if (e.target.matches('input, textarea, select')) return;
  if (e.key === '/') {
    e.preventDefault();
    showView('search');
    $('#search-input').focus();
  }
  if (e.key.toLowerCase() === 'n') {
    e.preventDefault();
    showView('capture');
  }
});

// Load detail view
async function loadDetail(id) {
  try {
    const mat = await apiFetch(`/materials/${id}`);
    const container = $('#detail-content');
    if (!container) return;

    let html = `
      <div class="detail-header">
        <h2>${esc(mat.title)}</h2>
        <span class="tag">${mat.material_type}</span>
      </div>
      ${mat.topic_summary ? `<p>${esc(mat.topic_summary)}</p>` : ''}
      <div class="detail-tags">${(mat.tags || []).map(t => `<span class="tag">${esc(t.name)}</span>`).join(' ')}</div>
    `;

    // Version chain
    if (mat.versions && mat.versions.length > 0) {
      html += '<h3>Versions</h3><div class="version-chain">';
      for (const ver of mat.versions) {
        html += `
          <div class="version-item">
            <div class="vheader">
              <span class="vnumber">v${ver.version_number}</span>
              <span class="vmeta">${ver.created_at || ''} · ${ver.language || ''} · ${ver.test_status || ''}</span>
            </div>
            ${ver.change_note ? `<div class="vnote">${esc(ver.change_note)}</div>` : ''}
            ${ver.blocks && ver.blocks.length ? renderBlocks(ver.blocks) : ''}
          </div>
        `;
      }
      html += '</div>';

      // Compare latest two versions
      if (mat.versions.length >= 2) {
        const v1 = mat.versions[mat.versions.length - 1];
        const v2 = mat.versions[mat.versions.length - 2];
        html += `
          <h4>Compare v${v1.version_number} ↔ v${v2.version_number}</h4>
          <div class="compare-view">
            <div class="compare-panel">
              <h4>v${v1.version_number}</h4>
              ${renderBlocks(v1.blocks || [])}
            </div>
            <div class="compare-panel">
              <h4>v${v2.version_number}</h4>
              ${renderBlocks(v2.blocks || [])}
            </div>
          </div>
        `;
      }
    }

    // Relations
    if (mat.relations && mat.relations.length > 0) {
      html += '<h3>Related</h3><div class="detail-relations">';
      for (const rel of mat.relations) {
        html += `<a href="#" onclick="loadDetail(${rel.id}); return false;">${esc(rel.title)} (${rel.relation_type})</a>`;
      }
      html += '</div>';
    }

    container.innerHTML = html;
    showView('detail');
  } catch (err) {
    const container = $('#detail-content');
    if (container) container.innerHTML = `<p class="toast error">Error loading material: ${esc(err.message)}</p>`;
    showView('detail');
  }
}

function renderBlocks(blocks) {
  if (!blocks.length) return '<p><em>No content</em></p>';
  return blocks.map(b => {
    const content = b.code_content || b.text_content || '';
    const cls = b.block_type === 'code' ? 'block-content code' : 'block-content';
    return `<div class="${cls}">${esc(content)}</div>`;
  }).join('');
}

// Search
async function doSearch() {
  const q = $('#search-input').value.trim();
  if (!q) return;

  try {
    const data = await apiFetch(`/search/?q=${encodeURIComponent(q)}`);
    const container = $('#search-results');

    if (!data.results || !data.results.length) {
      container.innerHTML = '<p>No results found. Try different keywords.</p>';
      return;
    }

    container.innerHTML = data.results.map(m => `
      <div class="material-card" onclick="loadDetail(${m.id})">
        <h3>${esc(m.title)}</h3>
        <div class="meta">${m.topic_summary || ''}</div>
      </div>
    `).join('');
  } catch (err) {
    const container = $('#search-results');
    if (container) container.innerHTML = `<p class="toast error">Search error: ${esc(err.message)}</p>`;
  }
}

$('#search-btn').addEventListener('click', doSearch);
$('#search-input').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

// Search suggestions
$('#search-input').addEventListener('input', async e => {
  const q = e.target.value.trim();
  if (q.length < 2) { $('#search-suggestions').classList.add('hidden'); return; }
  try {
    const data = await apiFetch(`/search/suggest?q=${encodeURIComponent(q)}`);
    const sug = $('#search-suggestions');
    if (!data.length) { sug.classList.add('hidden'); return; }
    sug.classList.remove('hidden');
    sug.innerHTML = data.map(m => `<div class="suggestion-item" onclick="loadDetail(${m.id})">${esc(m.title)}</div>`).join('');
  } catch (err) {
    $('#search-suggestions').classList.add('hidden');
  }
});

// Sidebar search
$('#sidebar-search').addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    const q = e.target.value.trim();
    if (!q) return;
    $('#search-input').value = q;
    showView('search');
    doSearch();
  }
});

// Topbar actions
$('#go-home').addEventListener('click', () => showView('home'));
$('#open-capture').addEventListener('click', () => showView('capture'));
$('#refresh-library').addEventListener('click', () => loadBrowse());
$('#back-from-capture').addEventListener('click', () => showView('home'));
$('#back-btn').addEventListener('click', () => showView('library'));

function esc(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Initial load
showView('home');
