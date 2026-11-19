# Search telemetry (Cloudflare Pages Functions)

The site logs what visitors search **while they type** — no Enter needed.
Every pause of ≥1 second in any search box is captured, plus the final query
on Enter, on clicking a result, and when the page is left. Result clicks and
the number of results shown are logged too, so you can see both what people
want and what the site fails to answer.

```
functions/api/collect.js   POST /api/collect  — receives batches, writes to D1
functions/api/stats.js     GET  /api/stats    — key-protected dashboard + JSON
gen/assets/telemetry.js    the client (built into docs/assets/telemetry.js)
```

Because the site is deployed on **Cloudflare Pages via the GitHub
integration**, the `functions/` directory at the repo root is picked up and
deployed automatically on every push — same origin as the site, no CORS, no
separate Worker, no endpoint configuration. (Keep `functions/` at the repo
root, *not* inside `docs/`.)

## One-time setup (Cloudflare dashboard, ~3 minutes)

1. **Create the database**: dashboard → **Storage & Databases → D1 SQL
   Database → Create database**. Name it e.g. `cotedb-telemetry`.
   The `events` table is created automatically on the first search — no
   migration needed.
2. **Bind it to the Pages project**: **Workers & Pages → your project →
   Settings → Bindings → Add → D1 database**. Variable name: **`DB`**,
   select the database. (Add it to the Preview environment too if you want
   telemetry on preview deployments.)
3. **Set the stats key**: **Settings → Environment variables → Add** →
   variable **`STATS_KEY`**, value = a long random string (this is the
   password for the stats page). Treat it as a secret.
4. **Redeploy** — bindings and variables only take effect on a new
   deployment, so push a commit (or hit *Retry deployment*). That's it.

View the logs at:

```
https://<your-site>/api/stats?key=<STATS_KEY>
```

Top searches, no-result searches (content gaps), clicked results, and a live
tail of recent events. Options: `&days=7|30|90`, `&final=1` (only committed
searches, not typed pauses), `&format=json`.

## What is captured

| Field | Meaning |
|---|---|
| `q` | the text in the box (trimmed, ≤160 chars) |
| `surface` | `nav` header search · `search` search page · `scenes` scene filter · `dir` people directory |
| `why` | `pause` typed then paused ≥1s · `enter` · `click` result clicked · `init` arrived via search link · `leave` typed, then left without committing |
| `n` | results shown (0 = no match — these are your content gaps) |
| `page`, `href` | where it happened / which result was clicked |
| `sid` | random per-tab id (sessionStorage) to group one visit's typing |
| `country` | coarse country from Cloudflare's edge |

**Not captured / privacy:** no cookies, no IPs, no fingerprinting, no
cross-site identity; the session id dies with the tab. Do-Not-Track and
Global Privacy Control are honored (nothing is sent). A visitor can opt out
with `localStorage.setItem('tel','off')` in the console. On `file://` and on
hosts without the endpoint (e.g. github.io) telemetry is inert and
self-disables after a few failed sends. If you publish this data or keep it
long-term, consider a retention policy and a note on the About page.

## SQL cookbook (D1 console → your database → Console)

```sql
-- What are people searching for? (last 30 days)
SELECT LOWER(q) AS query, COUNT(*) AS n, COUNT(DISTINCT sid) AS people
FROM events WHERE kind='q' AND day >= date('now','-30 days')
GROUP BY LOWER(q) ORDER BY n DESC LIMIT 50;

-- Searches that found nothing: what content to add next
SELECT LOWER(q) AS query, COUNT(*) AS n
FROM events WHERE kind='q' AND n=0 AND day >= date('now','-30 days')
GROUP BY LOWER(q) ORDER BY n DESC;

-- Watch one visitor type (prefix chain: aya → ayanok → ayanokoji)
SELECT ts, surface, q, n, why FROM events
WHERE sid='<sid from stats>' ORDER BY ts;

-- Searches per day
SELECT day, COUNT(*) FROM events WHERE kind='q' GROUP BY day ORDER BY day;

-- Retention: keep 90 days
DELETE FROM events WHERE day < date('now','-90 days');
```

## Local testing

```
npx wrangler pages dev docs --d1 DB=cotedb-telemetry
```

serves `docs/` with the functions and a local D1. Type in the search box,
wait a second, and watch rows appear (`wrangler d1 execute cotedb-telemetry
--local --command "SELECT * FROM events ORDER BY id DESC LIMIT 10"`).
For the stats page locally, add `--binding STATS_KEY=devkey` and open
`/api/stats?key=devkey`.

## Troubleshooting

- **503 from `/api/collect`** — the `DB` binding is missing, or the project
  wasn't redeployed after adding it.
- **404 from `/api/stats`** — wrong or missing `key`, or `STATS_KEY` not set
  (the endpoint intentionally hides itself without the key).
- **No rows** — check the browser console/network tab for `api/collect`
  (should be 204). DNT/GPC, an ad blocker, or `tel=off` disables sending.
  Remember queries are only sent after a ≥1s pause or when leaving.
- The service worker never caches `/api/*`, so stats are always live.
