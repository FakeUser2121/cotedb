var V='cote-__VERSION__',CORE=__CORE__,WARM=__WARM__;
var scope=self.registration.scope;
function abs(p){return new URL(p,scope).href}
function keyOf(u){var k=new URL(u.href);k.search='';k.hash='';if(/\/$/.test(k.pathname))k.pathname+='index.html';return k.href}

function cleanResponse(response) {
    if (!response || !response.redirected) {
        return Promise.resolve(response);
    }

    var copy = response.clone();

    return copy.blob().then(function(body) {
        return new Response(body, {
            headers: copy.headers,
            status: copy.status,
            statusText: copy.statusText
        });
    });
}

function putClean(cache, key, response) {
    return cleanResponse(response).then(function(clean) {
        return cache.put(key, clean.clone())
            .catch(function() {})
            .then(function() {
                return clean;
            });
    });
}

self.addEventListener('install', function(e) {
    e.waitUntil(
        caches.open(V).then(function(c) {
            return Promise.all(CORE.map(function(p) {
                var url = abs(p);

                return fetch(url).then(function(res) {
                    if (!res.ok || res.type !== 'basic') {
                        throw new Error('Precache failed: ' + url);
                    }

                    return putClean(c, url, res);
                });
            }));
        }).then(function() {
            return self.skipWaiting();
        })
    );
});

self.addEventListener('activate',function(e){
 e.waitUntil(caches.keys().then(function(ks){
  return Promise.all(ks.filter(function(k){return k.indexOf('cote-')===0&&k!==V}).map(function(k){return caches.delete(k)}))
 }).then(function(){return self.clients.claim()}))});

self.addEventListener('fetch', function(e) {
    var r = e.request;
    if (r.method !== 'GET') return;
    var u = new URL(r.url);
    if (u.origin !== self.location.origin || u.href.indexOf(scope) !== 0) return;
    if (u.href.indexOf(abs('api/')) === 0) return; // telemetry + stats: always live, never cached
    var key = keyOf(u);
    e.respondWith(
        caches.open(V).then(function(c) {
            return c.match(key).then(function(hit) {
                if (hit) {
                    return cleanResponse(hit).then(function(safe) {
                        if (hit.redirected) c.put(key, safe.clone()).catch(function() {});
                        return safe;
                    });
                }
                return fetch(r).then(function(res) {
                    if (res.ok && res.type === 'basic') {
                        return cleanResponse(res).then(function(clean) {
                            c.put(key, clean.clone()).catch(function() {});
                            return clean;
                        });
                    }
                    return res;
                }).catch(function() {
                    return r.mode === 'navigate'
                        ? c.match(abs('index.html')).then(function(fallback) {
                            return fallback ? cleanResponse(fallback) : Response.error();
                        })
                        : Response.error();
                });
            });
        }).catch(function() {
            return fetch(r);
        })
    );
});

self.addEventListener('message',function(e){
 if(e.data==='warm')e.waitUntil(warm())});

function warm(){
 return caches.open(V).then(function(c){
  var q=WARM.slice();
  function run(){
   var p=q.shift();if(!p)return Promise.resolve();
   var url=abs(p);
   return c.match(url).then(function(hit) {
    if (hit) {
        return cleanResponse(hit).then(function(safe) {
            if (!hit.redirected) return;

            return c.put(url, safe.clone()).catch(function() {});
        });
    }

    return fetch(url).then(function(res) {
        if (res.ok && res.type === 'basic') {
            return putClean(c, url, res);
        }
    }).catch(function() {});
 }).then(run)}
  return Promise.all([run(),run(),run(),run()])})}
