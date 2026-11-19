// Search telemetry collector — Cloudflare Pages Function at POST /api/collect.
// Receives batches from assets/telemetry.js (same origin, no CORS needed).
// Storage: a D1 database bound as DB (dashboard: Settings > Bindings > Add >
// D1 database). The table is created on first write; no migration step.
// No IPs are stored; country comes from Cloudflare's edge metadata.
// Setup guide + SQL cookbook: functions/README.md.

const MAX_BODY = 16 * 1024; // bytes per request
const MAX_BATCH = 50;       // events per request
const MAX_Q = 160;          // chars per query
const SURFACES = new Set(['nav', 'search', 'scenes', 'dir']);
const WHYS = new Set(['pause', 'enter', 'click', 'leave', 'init']);

let schemaReady = null;
function ensureSchema(db) {
  if (!schemaReady) {
    schemaReady = db.batch([
      db.prepare(`CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        ts INTEGER NOT NULL,      -- server time, ms epoch
        day TEXT NOT NULL,        -- UTC date, for grouping/retention
        sid TEXT,                 -- random per-tab id (sessionStorage)
        kind TEXT NOT NULL,       -- 'q' = query, 'click' = result click
        surface TEXT,             -- nav | search | scenes | dir
        q TEXT,                   -- what they typed (<=160 chars)
        n INTEGER,                -- results shown; 0 = no match; -1 = unknown
        why TEXT,                 -- pause | enter | click | leave | init
        page TEXT,                -- path where it happened
        href TEXT,                -- clicked result (kind='click')
        country TEXT              -- coarse geo from the edge; never an IP
      )`),
      db.prepare('CREATE INDEX IF NOT EXISTS idx_events_day ON events(day)'),
      db.prepare('CREATE INDEX IF NOT EXISTS idx_events_q ON events(q)'),
    ]).catch((e) => { schemaReady = null; throw e; });
  }
  return schemaReady;
}

function str(v, max) {
  return typeof v === 'string' ? v.replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max) : '';
}

// Best-effort per-IP rate limit, in memory per isolate. The IP is used as a
// transient key only and is never written to the database.
const hits = new Map();
function limited(ip) {
  const now = Date.now();
  let h = hits.get(ip);
  if (!h || now - h.t > 60000) {
    if (hits.size > 5000) hits.clear();
    h = { t: now, n: 0 };
    hits.set(ip, h);
  }
  return ++h.n > 120; // events per minute per visitor; typing debounces to far less
}

export async function onRequestPost({ request, env }) {
  if (!env.DB) {
    return new Response('telemetry storage not configured: bind a D1 database as DB (see functions/README.md)', { status: 503 });
  }
  const origin = request.headers.get('origin');
  if (origin && origin !== new URL(request.url).origin) return new Response('cross-origin', { status: 403 });
  if (limited(request.headers.get('cf-connecting-ip') || 'unknown')) return new Response('rate limited', { status: 429 });

  let events;
  try {
    const text = await request.text();
    if (text.length > MAX_BODY) return new Response('too large', { status: 413 });
    events = JSON.parse(text);
  } catch (e) {
    return new Response('bad json', { status: 400 });
  }
  if (!Array.isArray(events) || events.length === 0 || events.length > MAX_BATCH) {
    return new Response('bad batch', { status: 400 });
  }

  const now = Date.now();
  const day = new Date(now).toISOString().slice(0, 10);
  const country = str(request.cf && request.cf.country, 8);
  const stmts = [];
  for (const ev of events) {
    if (!ev || typeof ev !== 'object') continue;
    const kind = ev.k === 'q' ? 'q' : ev.k === 'c' ? 'click' : '';
    if (!kind) continue;
    const q = str(ev.q, MAX_Q);
    if (kind === 'q' && q.length < 2) continue;
    const n = Number.isFinite(ev.n) ? Math.max(-1, Math.min(9999, ev.n | 0)) : -1;
    stmts.push(env.DB.prepare(
      'INSERT INTO events (ts,day,sid,kind,surface,q,n,why,page,href,country) VALUES (?,?,?,?,?,?,?,?,?,?,?)'
    ).bind(
      now, day,
      str(ev.sid, 24).replace(/[^a-z0-9]/gi, ''),
      kind,
      SURFACES.has(ev.s) ? ev.s : '',
      q, n,
      WHYS.has(ev.w) ? ev.w : '',
      str(ev.p, 200),
      str(ev.h, 200),
      country
    ));
  }
  if (!stmts.length) return new Response(null, { status: 204 });
  try {
    await ensureSchema(env.DB);
    await env.DB.batch(stmts);
  } catch (e) {
    return new Response('store error', { status: 500 });
  }
  return new Response(null, { status: 204 });
}

export function onRequest() {
  return new Response('method not allowed', { status: 405, headers: { allow: 'POST' } });
}
