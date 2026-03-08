let ALL_DATA = [];

// Colonnes qui contiennent des liens de fichiers PDF
const FILE_COLUMNS = ['sujet_dev', 'sujet_exam', 'sujet', 'support_cours'];

async function loadData() {
  showLoading(true);
  try {
    const r = await fetch(API_GET);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    ALL_DATA = data;
    renderTable(data);
  } catch (e) {
    showError("Erreur de chargement : " + e.message);
  } finally {
    showLoading(false);
  }
}

async function applyFilter() {
  if (!API_POST) return;
  showLoading(true);

  const params = {};
  document.querySelectorAll('.filter-select').forEach(sel => {
    const key = sel.dataset.key;
    const val = sel.value;
    if (!key) return;
    if (val === "") {
      params[key] = null;
    } else {
      params[key] = isNaN(val) ? val : parseInt(val, 10);
    }
  });

  try {
    const r = await fetch(API_POST, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    ALL_DATA = data;
    renderTable(data);
  } catch (e) {
    showError("Erreur de filtrage : " + e.message);
  } finally {
    showLoading(false);
  }
}

function resetFilter() {
  document.querySelectorAll('.filter-select').forEach(sel => sel.value = "");
  document.getElementById('searchInput').value = "";
  loadData();
}

function localSearch(txt) {
  txt = txt.toLowerCase().trim();
  if (!txt) { renderTable(ALL_DATA); return; }
  const filtered = ALL_DATA.filter(row =>
    Object.values(row).some(v => String(v ?? '').toLowerCase().includes(txt))
  );
  renderTable(filtered);
}

function isFileUrl(val) {
  if (!val) return false;
  const v = String(val).toLowerCase();
  return v.includes('supabase.co/storage') || v.endsWith('.pdf') ||
         v.endsWith('.docx') || v.endsWith('.zip');
}

function makeDownloadBtn(url) {
  const parts = decodeURIComponent(url).split('/');
  const filename = parts[parts.length - 1];
  return `
    <div style="display:flex;gap:8px;align-items:center;">
      <a href="${url}" target="_blank" title="Aperçu du document"
         style="display:inline-flex;align-items:center;gap:6px;
                padding:6px 16px;border-radius:50px;
                border:1.5px solid #1A5276;background:transparent;
                color:#1A5276;font-size:11px;font-weight:600;text-decoration:none;">
        <span style="position:relative;display:inline-flex;align-items:center;">
          <i class="fas fa-file-lines" style="font-size:13px;"></i>
          <i class="fas fa-magnifying-glass" style="font-size:8px;position:absolute;bottom:-2px;right:-5px;"></i>
        </span>
        &nbsp;Aperçu
      </a>
      <a href="/api/download?url=${encodeURIComponent(url)}&filename=${encodeURIComponent(filename)}"
         title="Télécharger"
         style="display:inline-flex;align-items:center;gap:6px;
                padding:6px 16px;border-radius:50px;
                border:1.5px solid #2E86C1;background:rgba(46,134,193,0.12);
                color:#1A5276;font-size:11px;font-weight:600;text-decoration:none;">
        <span style="position:relative;display:inline-flex;align-items:center;">
          <i class="fas fa-cloud" style="font-size:15px;color:#2E86C1;opacity:0.7;"></i>
          <i class="fas fa-arrow-down" style="font-size:7px;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#1A5276;"></i>
        </span>
        &nbsp;Télécharger
      </a>
    </div>`;
}

function renderTable(data) {
  const head  = document.getElementById('tableHead');
  const body  = document.getElementById('tableBody');
  const empty = document.getElementById('tableEmpty');
  const errEl = document.getElementById('tableError');
  const count = document.getElementById('countBadge');

  errEl.classList.add('hidden');

  if (!data || data.length === 0) {
    head.innerHTML = '';
    body.innerHTML = '';
    empty.classList.remove('hidden');
    count.textContent = '0 résultats';
    return;
  }

  empty.classList.add('hidden');
  const cols = Object.keys(data[0]);

  head.innerHTML = '<tr>' +
    cols.map(c => `<th>${COL_LABELS[c] || c.replace(/_/g,' ')}</th>`).join('') +
    '</tr>';

  body.innerHTML = data.map(row =>
    '<tr>' +
    cols.map(c => {
      const v = row[c];
      // Si la colonne est une colonne fichier ET contient un lien Supabase
      if (FILE_COLUMNS.includes(c) && isFileUrl(v)) {
        return `<td>${makeDownloadBtn(v)}</td>`;
      }
      return `<td>${v === null || v === undefined
        ? '<span style="color:#aaa">—</span>'
        : escHtml(String(v))}</td>`;
    }).join('') +
    '</tr>'
  ).join('');

  count.textContent = `${data.length} résultat${data.length > 1 ? 's' : ''}`;
}

function showLoading(on) {
  const loading = document.getElementById('tableLoading');
  const table   = document.getElementById('dataTable');
  if (on) {
    loading.classList.remove('hidden');
    table.style.display = 'none';
  } else {
    loading.classList.add('hidden');
    table.style.display = '';
  }
}

function showError(msg) {
  const el = document.getElementById('tableError');
  el.classList.remove('hidden');
  el.textContent = '❌ ' + msg;
  document.getElementById('tableBody').innerHTML = '';
  document.getElementById('tableHead').innerHTML = '';
}

function escHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

document.addEventListener('DOMContentLoaded', loadData);