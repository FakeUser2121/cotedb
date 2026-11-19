// Search telemetry dashboard — GET /api/stats?key=STATS_KEY
// Protected by the STATS_KEY environment variable (dashboard: Settings >
// Environment variables). Without the right key this endpoint answers 404.
// HTML by default; &format=json for raw data. Options: &days=7|30|90 and
// &final=1 to count only committed searches (Enter / result click / deep
// link) instead of every typed pause.

const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

let schemaReady = null;
function ensureSchema(db) {
  if (!schemaReady) {
    schemaReady = db.batch([
      db.prepare(`CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY, ts INTEGER NOT NULL, day TEXT NOT NULL, sid TEXT,
        kind TEXT NOT NULL, surface TEXT, q TEXT, n INTEGER, why TEXT,
        page TEXT, href TEXT, country TEXT)`),
      db.prepare('CREATE INDEX IF NOT EXISTS idx_events_day ON events(day)'),
      db.prepare('CREATE INDEX IF NOT EXISTS idx_events_q ON events(q)'),
    ]).catch((e) => { schemaReady = null; throw e; });
  }
  return schemaReady;
}

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const key = url.searchParams.get('key') || '';
  if (!env.STATS_KEY || key !== env.STATS_KEY) return new Response('not found', { status: 404 });
  if (!env.DB) {
    return new Response('telemetry storage not configured: bind a D1 database as DB (see functions/README.md)', { status: 503 });
  }
  const days = Math.min(90, Math.max(1, parseInt(url.searchParams.get('days'), 10) || 30));
  const finalOnly = url.searchParams.get('final') === '1';
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const finalCond = finalOnly ? " AND why IN ('enter','click','init')" : '';

  let data;
  try {
    await ensureSchema(env.DB);
    const [totals, top, zero, recent, clicks] = await Promise.all([
      env.DB.prepare(`SELECT COUNT(*) AS searches, COUNT(DISTINCT sid) AS sessions,
        SUM(CASE WHEN n=0 THEN 1 ELSE 0 END) AS zero
        FROM events WHERE kind='q' AND day>=?${finalCond}`).bind(since).first(),
      env.DB.prepare(`SELECT LOWER(q) AS q, COUNT(*) AS c, COUNT(DISTINCT sid) AS u,
        SUM(CASE WHEN n=0 THEN 1 ELSE 0 END) AS zero
        FROM events WHERE kind='q' AND day>=?${finalCond}
        GROUP BY LOWER(q) ORDER BY c DESC, u DESC LIMIT 60`).bind(since).all(),
      env.DB.prepare(`SELECT LOWER(q) AS q, COUNT(*) AS c
        FROM events WHERE kind='q' AND n=0 AND day>=?
        GROUP BY LOWER(q) ORDER BY c DESC LIMIT 40`).bind(since).all(),
      env.DB.prepare(`SELECT ts,sid,kind,surface,q,n,why,page,href,country
        FROM events ORDER BY id DESC LIMIT 120`).all(),
      env.DB.prepare(`SELECT href, LOWER(q) AS q, COUNT(*) AS c
        FROM events WHERE kind='click' AND day>=?
        GROUP BY href, LOWER(q) ORDER BY c DESC LIMIT 30`).bind(since).all(),
    ]);
    data = { days, finalOnly, totals, top: top.results, zero: zero.results, recent: recent.results, clicks: clicks.results };
  } catch (e) {
    return new Response('stats error: ' + (e && e.message), { status: 500 });
  }
  if (url.searchParams.get('format') === 'json') return Response.json(data);

  const link = (d, f) => `?key=${encodeURIComponent(key)}&days=${d}${f ? '&final=1' : ''}`;
  const t = data.totals || {};
  const table = (head, arr, cols) => arr.length
    ? `<table><tr>${head.map((h) => `<th>${esc(h)}</th>`).join('')}</tr>${arr.map((r) => `<tr>${cols.map((c) => `<td>${esc(c(r))}</td>`).join('')}</tr>`).join('')}</table>`
    : '<p class="dim">nothing yet</p>';
  const when = (ts) => new Date(ts).toISOString().slice(5, 16).replace('T', ' ');
  const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>Search telemetry</title>
<style>
body{font:14px/1.5 system-ui,sans-serif;background:#14161a;color:#d8dbe0;margin:2rem auto;max-width:1100px;padding:0 1rem}
h1{font-size:1.4rem}h2{font-size:1.05rem;margin-top:2.2rem;color:#9fb3c8}
table{border-collapse:collapse;width:100%;margin:.5rem 0}
th,td{text-align:left;padding:.3rem .6rem;border-bottom:1px solid #2a2e35;vertical-align:top}
th{color:#8fa3b8;font-weight:600}td.num{text-align:right}
a{color:#7fb4e8}.dim{color:#7a828c}.pill{display:inline-block;padding:.15rem .6rem;border:1px solid #2a2e35;border-radius:1rem;margin-right:.4rem}
.pill.on{background:#2a2e35;color:#fff}code{color:#c9a86a}
</style></head><body>
<h1>Search telemetry</h1>
<p>${esc(t.searches || 0)} searches · ${esc(t.sessions || 0)} sessions · ${esc(t.zero || 0)} with no results (last ${days} days${finalOnly ? ', committed only' : ''})</p>
<p><span class="pill${days === 7 ? ' on' : ''}"><a href="${link(7, finalOnly)}">7 days</a></span>
<span class="pill${days === 30 ? ' on' : ''}"><a href="${link(30, finalOnly)}">30 days</a></span>
<span class="pill${days === 90 ? ' on' : ''}"><a href="${link(90, finalOnly)}">90 days</a></span>
<span class="pill${finalOnly ? ' on' : ''}"><a href="${link(days, !finalOnly)}">${finalOnly ? '✓ ' : ''}committed only</a></span>
<span class="pill"><a href="${link(days, finalOnly)}&format=json">JSON</a></span></p>
<p class="dim">Queries are logged while people type: every ≥1s pause, plus the final query on Enter, result click or leaving.
<code>why</code>: pause = mid-typing, enter/click/init = committed, leave = typed but never committed. <code>n</code> = results shown.</p>
<h2>Top searches</h2>
${table(['query', 'count', 'sessions', 'no-result count'], data.top, [(r) => r.q, (r) => r.c, (r) => r.u, (r) => r.zero || 0])}
<h2>No-result searches — content gaps to fill</h2>
${table(['query', 'count'], data.zero, [(r) => r.q, (r) => r.c])}
<h2>Clicked results</h2>
${table(['result', 'after query', 'count'], data.clicks, [(r) => r.href, (r) => r.q, (r) => r.c])}
<h2>Recent events (UTC)</h2>
${table(['time', 'what', 'where', 'n', 'why', 'page', 'geo', 'session'], data.recent, [
    (r) => when(r.ts),
    (r) => r.kind === 'click' ? '→ ' + r.href : r.q,
    (r) => r.surface,
    (r) => r.kind === 'q' ? r.n : '',
    (r) => r.why,
    (r) => r.page,
    (r) => r.country,
    (r) => (r.sid || '').slice(0, 6),
  ])}
</body></html>`;
  return new Response(html, { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' } });
}

export function onRequest() {
  return new Response('method not allowed', { status: 405, headers: { allow: 'GET' } });
}
