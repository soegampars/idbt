// ============================================================
// IDBT — DuckDB-WASM Query Frontend
// ============================================================

const REPO_BASE = "https://raw.githubusercontent.com/soegampars/idbt/main/";

// Hardcoded list of available fact tables (extend as more data arrives)
const FACT_TABLES = ["industri"];

// Global state
let db = null;
let conn = null;
let lastQueryResult = null; // Array of row objects from last query

// ============================================================
// DuckDB Initialization
// ============================================================

async function initDuckDB() {
  const duckdb = await import(
    "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm/+esm"
  );

  // Pick the best bundle for this browser
  const BUNDLES = duckdb.getJsDelivrBundles();
  const bundle = await duckdb.selectBundle(BUNDLES);

  // Create worker via blob URL to avoid cross-origin restrictions
  const workerUrl = URL.createObjectURL(
    new Blob([`importScripts("${bundle.mainWorker}");`], {
      type: "text/javascript",
    })
  );
  const worker = new Worker(workerUrl);
  const logger = new duckdb.ConsoleLogger();
  db = new duckdb.AsyncDuckDB(logger, worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
  conn = await db.connect();
}

// ============================================================
// Data Loading
// ============================================================

async function loadParquetFromURL(tableName, url) {
  // Fetch the Parquet file as a Uint8Array and register it in DuckDB
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status} for ${url}`);
  const buffer = await response.arrayBuffer();
  const fileName = `${tableName}.parquet`;
  await db.registerFileBuffer(fileName, new Uint8Array(buffer));
  await conn.query(
    `CREATE OR REPLACE TABLE ${tableName} AS SELECT * FROM read_parquet('${fileName}')`
  );
}

async function loadReferenceTables() {
  await loadParquetFromURL("ref_wilayah", REPO_BASE + "data/ref/ref_wilayah.parquet");
  await loadParquetFromURL("ref_indikator", REPO_BASE + "data/ref/ref_indikator.parquet");
  await loadParquetFromURL("ref_publikasi", REPO_BASE + "data/ref/ref_publikasi.parquet");
}

async function loadFactTable(name) {
  const url = REPO_BASE + `data/facts/${name}.parquet`;
  await loadParquetFromURL(`fact_${name}`, url);
}

// ============================================================
// UI Helpers
// ============================================================

function showMessage(text, isError = false) {
  const el = document.getElementById("message");
  el.textContent = text;
  el.className = isError ? "error" : "";
  el.style.display = "block";
}

function hideMessage() {
  document.getElementById("message").style.display = "none";
}

function showResults() {
  document.getElementById("results").style.display = "block";
}

function hideResults() {
  document.getElementById("results").style.display = "none";
}

// Convert a DuckDB arrow result to an array of plain objects
function arrowToObjects(arrowResult) {
  const rows = [];
  const batches = arrowResult.batches || [arrowResult];
  for (const batch of batches) {
    const numRows = batch.numRows;
    const schema = batch.schema;
    for (let i = 0; i < numRows; i++) {
      const row = {};
      for (const field of schema.fields) {
        const col = batch.getChild(field.name);
        const val = col.get(i);
        // Convert BigInt to Number for display
        row[field.name] = typeof val === "bigint" ? Number(val) : val;
      }
      rows.push(row);
    }
  }
  return rows;
}

// Render an array of row objects as an HTML table
function renderTable(rows) {
  const container = document.getElementById("table-container");
  if (!rows || rows.length === 0) {
    container.innerHTML = "";
    return;
  }

  const columns = Object.keys(rows[0]);
  let html = "<table><thead><tr>";
  for (const col of columns) {
    html += `<th>${escapeHTML(col)}</th>`;
  }
  html += "</tr></thead><tbody>";

  for (const row of rows) {
    html += "<tr>";
    for (const col of columns) {
      const val = row[col];
      const display = val === null || val === undefined ? "" : val;
      html += `<td>${escapeHTML(String(display))}</td>`;
    }
    html += "</tr>";
  }
  html += "</tbody></table>";
  container.innerHTML = html;
}

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ============================================================
// Populate Dropdowns
// ============================================================

function populateTopics() {
  const select = document.getElementById("topik");
  select.innerHTML = "";
  for (const name of FACT_TABLES) {
    const opt = document.createElement("option");
    opt.value = name;
    // Capitalize first letter for display
    opt.textContent = name.charAt(0).toUpperCase() + name.slice(1);
    select.appendChild(opt);
  }
}

async function populateIndicators(topic) {
  const listEl = document.getElementById("indikator-list");

  // Query ref_indikator. Filter by seri matching topic if possible.
  // If no match on seri, show all indicators.
  let rows;
  try {
    const result = await conn.query(
      `SELECT indikator_id, nama_id, seri FROM ref_indikator ORDER BY indikator_id`
    );
    rows = arrowToObjects(result);
  } catch {
    listEl.innerHTML = '<p class="muted">Tidak dapat memuat indikator.</p>';
    return;
  }

  if (rows.length === 0) {
    listEl.innerHTML = '<p class="muted">Belum ada indikator terdaftar.</p>';
    return;
  }

  // Try filtering by seri that loosely matches the topic
  const topicLower = topic.toLowerCase();
  let filtered = rows.filter(
    (r) => r.seri && r.seri.toLowerCase().includes(topicLower)
  );
  // Fall back to all if no match
  if (filtered.length === 0) filtered = rows;

  let html = "";
  for (const ind of filtered) {
    html += `<label>
      <input type="checkbox" value="${escapeHTML(ind.indikator_id)}" checked>
      ${escapeHTML(ind.nama_id || ind.indikator_id)}
    </label>`;
  }
  listEl.innerHTML = html;
}

// Check if the current fact table has a kode_wilayah column
async function checkHasWilayah(topic) {
  try {
    const result = await conn.query(
      `SELECT column_name FROM information_schema.columns
       WHERE table_name = 'fact_${topic}' AND column_name = 'kode_wilayah'`
    );
    const rows = arrowToObjects(result);
    return rows.length > 0;
  } catch {
    return false;
  }
}

// ============================================================
// Query Execution
// ============================================================

async function runQuery() {
  hideMessage();
  hideResults();

  const topic = document.getElementById("topik").value;
  const tahunDari = parseInt(document.getElementById("tahun-dari").value, 10);
  const tahunSampai = parseInt(document.getElementById("tahun-sampai").value, 10);
  const geoFilter = document.getElementById("geografi").value;

  // Gather selected indicators
  const checkboxes = document.querySelectorAll(
    '#indikator-list input[type="checkbox"]:checked'
  );
  const selectedIds = Array.from(checkboxes).map((cb) => cb.value);

  if (selectedIds.length === 0) {
    showMessage("Pilih setidaknya satu indikator.");
    return;
  }

  // Try loading the fact table
  try {
    await loadFactTable(topic);
  } catch {
    showMessage("Data belum tersedia untuk topik ini.", true);
    return;
  }

  const hasWilayah = await checkHasWilayah(topic);

  // Build the SQL query
  const idList = selectedIds.map((id) => `'${id}'`).join(", ");
  const factTable = `fact_${topic}`;

  // Determine the key column
  const keyCol = hasWilayah ? "kode_wilayah" : "kbli";
  const keyLabel = hasWilayah ? "nama_wilayah" : keyCol;

  let selectCols, joins, whereClauses;

  if (hasWilayah) {
    selectCols = `
      w.nama_wilayah,
      f.tahun,
      i.nama_id AS indikator,
      f.nilai,
      i.satuan`;
    joins = `
      LEFT JOIN ref_wilayah w ON f.kode_wilayah = w.kode_wilayah
      LEFT JOIN ref_indikator i ON f.indikator_id = i.indikator_id`;
  } else {
    selectCols = `
      f.kbli,
      f.tahun,
      i.nama_id AS indikator,
      f.nilai,
      i.satuan`;
    joins = `
      LEFT JOIN ref_indikator i ON f.indikator_id = i.indikator_id`;
  }

  whereClauses = [
    `f.indikator_id IN (${idList})`,
    `f.tahun BETWEEN ${tahunDari} AND ${tahunSampai}`,
  ];

  // Geography filter (only when the fact table has kode_wilayah)
  if (hasWilayah && geoFilter === "provinsi") {
    whereClauses.push(`w.tingkat = 'provinsi'`);
  } else if (hasWilayah && geoFilter === "kabupaten_kota") {
    whereClauses.push(`w.tingkat IN ('kabupaten', 'kota')`);
  }

  const sql = `
    SELECT ${selectCols}
    FROM ${factTable} f
    ${joins}
    WHERE ${whereClauses.join(" AND ")}
    ORDER BY f.tahun, ${hasWilayah ? "w.nama_wilayah" : "f.kbli"}, i.nama_id
  `;

  try {
    const result = await conn.query(sql);
    const rows = arrowToObjects(result);

    if (rows.length === 0) {
      showMessage("Tidak ada data yang sesuai dengan filter yang dipilih.");
      return;
    }

    lastQueryResult = rows;
    renderTable(rows);
    showResults();
  } catch (err) {
    showMessage(`Query gagal: ${err.message}`, true);
  }
}

// ============================================================
// CSV Download
// ============================================================

function downloadCSV() {
  if (!lastQueryResult || lastQueryResult.length === 0) return;

  const columns = Object.keys(lastQueryResult[0]);
  const header = columns.join(",");
  const rows = lastQueryResult.map((row) =>
    columns
      .map((col) => {
        const val = row[col];
        if (val === null || val === undefined) return "";
        const str = String(val);
        // Quote fields that contain commas or quotes
        if (str.includes(",") || str.includes('"') || str.includes("\n")) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      })
      .join(",")
  );

  const csv = [header, ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "idbt_hasil_query.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ============================================================
// Event Handlers & Initialization
// ============================================================

async function onTopicChange() {
  const topic = document.getElementById("topik").value;

  // Try to load fact table to check schema
  let hasWilayah = false;
  try {
    await loadFactTable(topic);
    hasWilayah = await checkHasWilayah(topic);
  } catch {
    // Fact table not available yet — that's OK, will error at query time
  }

  // Show/hide geography filter
  document.getElementById("geografi-group").style.display = hasWilayah
    ? "block"
    : "none";

  // Repopulate indicators
  await populateIndicators(topic);
}

async function init() {
  const loadingEl = document.getElementById("loading");
  const controlsEl = document.getElementById("controls");

  try {
    await initDuckDB();
    await loadReferenceTables();

    populateTopics();
    await onTopicChange();

    // Wire up events
    document.getElementById("topik").addEventListener("change", onTopicChange);
    document.getElementById("btn-cari").addEventListener("click", runQuery);
    document.getElementById("btn-unduh").addEventListener("click", downloadCSV);

    // Show controls
    loadingEl.style.display = "none";
    controlsEl.style.display = "block";
  } catch (err) {
    loadingEl.textContent = `Gagal memuat DuckDB: ${err.message}`;
    console.error(err);
  }
}

init();
