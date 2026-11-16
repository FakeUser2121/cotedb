window.VOLS=[[1, "Year 1, Volume 1", "Y1V1", "y1v1"], [2, "Year 1, Volume 2", "Y1V2", "y1v2"], [3, "Year 1, Volume 3", "Y1V3", "y1v3"], [4, "Year 1, Volume 4", "Y1V4", "y1v4"], [5, "Year 1, Volume 4.5", "Y1V4.5", "y1v4.5"], [6, "Year 1, Volume 5", "Y1V5", "y1v5"], [7, "Year 1, Volume 6", "Y1V6", "y1v6"], [8, "Year 1, Volume 7", "Y1V7", "y1v7"], [9, "Year 1, Volume 7.5", "Y1V7.5", "y1v7.5"], [10, "Year 1, Volume 8", "Y1V8", "y1v8"], [11, "Year 1, Volume 9", "Y1V9", "y1v9"], [12, "Year 1, Volume 10", "Y1V10", "y1v10"], [13, "Year 1, Volume 11", "Y1V11", "y1v11"], [14, "Year 1, Volume 11.5", "Y1V11.5", "y1v11.5"], [15, "Year 1, Volume 11.75", "Y1V11.75", "y1v11.75"], [16, "Year 2, Volume 1", "Y2V1", "y2v1"], [17, "Year 2, Volume 2", "Y2V2", "y2v2"], [18, "Year 2, Volume 3", "Y2V3", "y2v3"], [19, "Year 2, Volume 4", "Y2V4", "y2v4"], [20, "Year 2, Volume 4.5", "Y2V4.5", "y2v4.5"], [21, "Year 2, Volume 5", "Y2V5", "y2v5"], [22, "Year 2, Volume 6", "Y2V6", "y2v6"], [23, "Year 2, Volume 7", "Y2V7", "y2v7"], [24, "Year 2, Volume 8", "Y2V8", "y2v8"], [25, "Year 2, Volume 9", "Y2V9", "y2v9"], [26, "Year 2, Volume 9.5", "Y2V9.5", "y2v9.5"], [27, "Year 2, Volume 9.75", "Y2V9.75", "y2v9.75"], [28, "Year 2, Volume 10", "Y2V10", "y2v10"], [29, "Year 2, Volume 10.25", "Y2V10.25", "y2v10.25"], [30, "Year 2, Volume 11", "Y2V11", "y2v11"], [31, "Year 2, Volume 12", "Y2V12", "y2v12"], [32, "Year 2, Volume 12.5", "Y2V12.5", "y2v12.5"], [33, "Year 3, Volume 1", "Y3V1", "y3v1"], [34, "Year 3, Volume 2", "Y3V2", "y3v2"], [35, "Year 3, Volume 3", "Y3V3", "y3v3"], [36, "Side Stories (Year 0)", "Side stories", "y0"]];
(function(){
var d=document,h=d.documentElement,N=navigator;
var ls=function(k,v){try{return v===undefined?localStorage.getItem(k):localStorage.setItem(k,v)}catch(e){return null}};
var me=d.currentScript,base=((me&&me.src)||'').replace(/assets\/meta\.js.*$/,'');
var mem=N.deviceMemory,cpu=N.hardwareConcurrency;
var weak=(mem&&mem<=1)||(cpu&&cpu<=2);
var calm=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
var pref=ls('fx');
var want=pref==='on'||(pref!=='off'&&!weak&&!calm);
h.dataset.theme=ls('theme')||'dark';
h.dataset.fx=want?'full':'static';

var seen;try{seen=sessionStorage.getItem('fxboot')}catch(e){}
var path=location.pathname;if(/\/$/.test(path))path+='index.html';
var key=location.origin+path;
function introFade(){h.setAttribute('data-intro','');setTimeout(function(){h.removeAttribute('data-intro')},1400)}
function coverMiss(){h.classList.add('fx-boot');
 setTimeout(function(){if(h.classList.contains('fx-boot'))h.classList.remove('fx-boot')},2500);
 if(window.__fxbell)window.__fxbell()}
if(want){
 if(!seen){h.classList.add('fx-boot');try{sessionStorage.setItem('fxboot','1')}catch(e){}
  setTimeout(function(){h.classList.remove('fx-boot')},3000)}
 else{
  try{caches.keys().then(function(ks){var k='',i;
   for(i=0;i<ks.length;i++)if(ks[i].indexOf('cote-')===0)k=ks[i];
   if(!k){coverMiss();return}
   return caches.open(k).then(function(c){return c.match(key)}).then(function(hit){if(hit)introFade();else coverMiss()})}).catch(function(){introFade()})}
  catch(e){introFade()}}
}

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
function mount(){var t=d.querySelector('.top');if(!t||d.getElementById('fxtoggle'))return;
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
