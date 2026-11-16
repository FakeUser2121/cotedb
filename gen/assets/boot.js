(function(){
var d=document,h=d.documentElement,N=navigator;
var file=location.protocol==='file:';
function wn(){try{var m=/(?:^|;)cotefx=([^;]*)/.exec(window.name);return m?JSON.parse(decodeURIComponent(m[1])):{}}catch(e){return{}}}
var store={
 get:function(k){if(file){var o=wn();if(k in o)return o[k]}try{return localStorage.getItem(k)}catch(e){return null}},
 set:function(k,v){v=String(v);try{localStorage.setItem(k,v)}catch(e){}
  if(file){var o=wn();o[k]=v;try{window.name='cotefx='+encodeURIComponent(JSON.stringify(o))}catch(e){}}}};
window.COTE_STORE=store;
var ls=function(k,v){return v===undefined?store.get(k):store.set(k,v)};
var me=d.currentScript,base=((me&&me.src)||'').replace(/assets\/meta\.js.*$/,'');
var mem=N.deviceMemory,cpu=N.hardwareConcurrency;
var weak=(mem&&mem<=1)||(cpu&&cpu<=2);
var calm=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
var pref=ls('fx');
var want=pref==='on'||(pref!=='off'&&!weak&&!calm);
h.dataset.theme=ls('theme')||'dark';
h.dataset.fx=want?'full':'static';

if(!window.__bootCritical){
 var seen;try{seen=sessionStorage.getItem('fxboot')}catch(e){}
 var fast=false;
 function coverMiss(){h.classList.add('fx-boot');
  setTimeout(function(){if(h.classList.contains('fx-boot'))h.classList.remove('fx-boot')},2000);
  if(window.__fxbell)window.__fxbell()}
 if(want){
  if(!seen){h.classList.add('fx-boot');try{sessionStorage.setItem('fxboot','1')}catch(e){}
   setTimeout(function(){h.classList.remove('fx-boot')},2000)}
  else{
   fast=(window.performance&&performance.now())<300;
   if(!fast)coverMiss()}
 }
}
if(h.classList.contains('fx-boot')){
 setTimeout(function(){if(h.classList.contains('fx-boot'))h.classList.remove('fx-boot')},2000)}

var loaded=false;
function loadFx(){if(loaded)return;loaded=true;
 var s=d.createElement('script');s.src=base+'assets/fx.js';s.async=true;
 s.onerror=function(){loaded=false;h.classList.remove('fx-boot')};
 d.head.appendChild(s)}
if(want)loadFx();

function sync(){var b=d.getElementById('fxtoggle');if(!b)return;var on=h.dataset.fx==='full';
 b.setAttribute('aria-pressed',on);
 b.title=on?'Animations on. Click for the static look.':'Animations off. Click to turn them on.'}
function set(on){h.dataset.fx=on?'full':'static';if(on)loadFx();sync()}
function mount(){var t=d.querySelector('.tools')||d.querySelector('.top');if(!t||d.getElementById('fxtoggle'))return;
 var b=d.createElement('button');b.id='fxtoggle';b.type='button';b.setAttribute('aria-label','Animations');b.innerHTML='<i></i>FX';
 b.onclick=function(){var on=h.dataset.fx!=='full';ls('fx',on?'on':'off');set(on)};
 t.appendChild(b);sync()}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',mount);else mount();

var secure=location.protocol==='https:'||location.hostname==='localhost'||location.hostname==='127.0.0.1';
if(secure&&'serviceWorker' in N&&base){
 addEventListener('load',function(){
  N.serviceWorker.register(base+'sw.js').then(function(){return N.serviceWorker.ready}).then(function(r){
   var c=N.connection||{};if(c.saveData||/2g$/.test(c.effectiveType||''))return;
   var go=function(){if(r.active)r.active.postMessage('warm')};
   if(window.requestIdleCallback)requestIdleCallback(go,{timeout:6000});else setTimeout(go,3000)
  }).catch(function(){})})}
})();
