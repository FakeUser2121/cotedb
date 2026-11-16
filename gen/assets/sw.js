var V='cote-__VERSION__',CORE=__CORE__,WARM=__WARM__;
var scope=self.registration.scope;
function abs(p){return new URL(p,scope).href}
function keyOf(u){var k=new URL(u.href);k.search='';k.hash='';if(/\/$/.test(k.pathname))k.pathname+='index.html';return k.href}

self.addEventListener('install',function(e){
 e.waitUntil(caches.open(V).then(function(c){return c.addAll(CORE.map(abs))}).then(function(){return self.skipWaiting()}))});

self.addEventListener('activate',function(e){
 e.waitUntil(caches.keys().then(function(ks){
  return Promise.all(ks.filter(function(k){return k.indexOf('cote-')===0&&k!==V}).map(function(k){return caches.delete(k)}))
 }).then(function(){return self.clients.claim()}))});

self.addEventListener('fetch',function(e){
 var r=e.request;if(r.method!=='GET')return;
 var u=new URL(r.url);if(u.origin!==self.location.origin||u.href.indexOf(scope)!==0)return;
 var key=keyOf(u);
 e.respondWith(caches.open(V).then(function(c){
  return c.match(key).then(function(hit){
   if(hit)return hit;
   return fetch(r).then(function(res){
    if(res.ok&&res.type==='basic')c.put(key,res.clone());
    return res
   }).catch(function(){
    return r.mode==='navigate'?c.match(abs('index.html')):Response.error()})})}))});

self.addEventListener('message',function(e){
 if(e.data==='warm')e.waitUntil(warm())});

function warm(){
 return caches.open(V).then(function(c){
  var q=WARM.slice();
  function run(){
   var p=q.shift();if(!p)return Promise.resolve();
   var url=abs(p);
   return c.match(url).then(function(hit){
    return hit||fetch(url).then(function(res){if(res.ok)return c.put(url,res)}).catch(function(){})
   }).then(run)}
  return Promise.all([run(),run(),run(),run()])})}
