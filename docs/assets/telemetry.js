// Search telemetry: records what visitors type, while they type.
// Every pause (>=1s) in a search box is logged, plus the final query on
// Enter, result click or leaving the page. Batches go to the same-origin
// Pages Function at api/collect (functions/README.md). No cookies, no
// persistent ids, no IPs; honors DNT/GPC and localStorage tel=off.
// Inert on file:// and self-disables if the endpoint is missing.
(function(){
'use strict';
if(!/^https?:$/.test(location.protocol))return;
var N=navigator,W=window;
if(N.doNotTrack==='1'||W.doNotTrack==='1'||N.globalPrivacyControl)return;
var store=W.COTE_STORE||{get:function(k){try{return localStorage.getItem(k)}catch(e){return null}},set:function(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
if(store.get('tel')==='off')return;
var root=(document.body&&document.body.dataset.root)||'';
var EP=root+'api/collect';
var sid='s'+Math.random().toString(36).slice(2,10);
try{var s0=sessionStorage.getItem('telsid');if(!s0){s0=sid;sessionStorage.setItem('telsid',s0)}sid=s0}catch(e){}
var queue=[],timer=0,fails=0,dead=false;
var pend=Object.create(null),last=Object.create(null),cur=Object.create(null);
function clean(s){return String(s==null?'':s).replace(/[\u0000-\u001f\u007f]+/g,' ').replace(/\s+/g,' ').trim().slice(0,160)}
function fail(){if(++fails>=3)dead=true}
function send(ev){if(dead)return;ev.sid=sid;ev.p=location.pathname.replace(/index\.html$/,'');queue.push(ev);
 if(queue.length>40)queue.splice(0,queue.length-40);
 if(queue.length>=8)flush();else if(!timer)timer=setTimeout(flush,4000)}
function flush(){if(timer){clearTimeout(timer);timer=0}
 if(dead||!queue.length)return;
 var body=JSON.stringify(queue.splice(0,50));
 try{
  if(W.fetch){W.fetch(EP,{method:'POST',body:body,headers:{'Content-Type':'application/json'},keepalive:true,credentials:'omit',mode:'same-origin'}).then(function(r){if(r.ok)fails=0;else fail()}).catch(fail)}
  else if(N.sendBeacon){if(!N.sendBeacon(EP,new Blob([body],{type:'application/json'})))fail()}
  else fail();
 }catch(e){fail()}}
function record(surface,q,n,why){q=clean(q);cur[surface]=q;
 if(!q||q.length<2)return;
 if(last[surface]===q)return;
 last[surface]=q;send({k:'q',s:surface,q:q,n:(n==null?-1:n|0),w:why})}
// called on every input event; logs the query once typing settles
function query(surface,q,n){if(dead)return;q=clean(q);cur[surface]=q;
 var p=pend[surface];if(p)clearTimeout(p.t);
 if(!q||q.length<2||last[surface]===q){delete pend[surface];return}
 pend[surface]={q:q,n:n,t:setTimeout(function(){delete pend[surface];record(surface,q,n,'pause')},1000)}}
// called on Enter / result click / page leave: log the final state now
function commit(surface,q,n,why){if(dead)return;
 var p=pend[surface];if(p){clearTimeout(p.t);delete pend[surface]}
 record(surface,q==null?cur[surface]:q,n,why)}
function click(surface,href){if(dead)return;
 commit(surface,null,null,'click');
 send({k:'c',s:surface,q:cur[surface]||'',h:String(href||'').slice(0,200)});flush()}
function drain(){for(var s in pend){var p=pend[s];clearTimeout(p.t);record(s,p.q,p.n,'leave')}pend=Object.create(null);flush()}
W.addEventListener('pagehide',drain);
document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden')drain()});
W.coteTel={q:query,commit:commit,click:click,flush:flush,off:function(){store.set('tel','off');dead=true;queue.length=0}};
})();
