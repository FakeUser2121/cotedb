(function(){
'use strict';
if(window.__fx)return;window.__fx=1;
var d=document,h=d.documentElement;
var on=function(){return h.dataset.fx==='full'};
var mm=function(q){return !!(window.matchMedia&&matchMedia(q).matches)};
var mouse=mm('(hover:hover) and (pointer:fine)');
var raf=window.requestAnimationFrame||function(f){return setTimeout(f,16)};
var $=function(s,r){return (r||d).querySelector(s)};

var introT=0;
function intro(ms){h.setAttribute('data-intro','');clearTimeout(introT);introT=setTimeout(function(){h.removeAttribute('data-intro')},ms||1400)}

// ---- boot ring (once per session)
function boot(){
 var brand=$('.brand'),el=d.createElement('div'),seg='';
 for(var i=0;i<12;i++)seg+='<i style="--a:'+i*30+'deg;--i:'+i+'"></i>';
 el.className='fxboot';
 el.innerHTML='<div class="fxring">'+seg+'</div><div class="fxlab"></div>';
 $('.fxlab',el).textContent=brand?brand.textContent:'';
 d.body.appendChild(el);h.classList.remove('fx-boot');
 var done=false;
 function out(){if(done)return;done=true;intro();el.classList.add('out');setTimeout(function(){el.remove()},300)}
 el.addEventListener('pointerdown',out);
 setTimeout(out,1000)}

// ---- ripple
var RIP='button,.task,.tabs a,.brand,.morebtn,.ptr,summary,.alpha button';
function ripple(x,y){if(!d.body.animate)return;
 var s=d.createElement('span');s.className='fxrip';d.body.appendChild(s);
 var t='translate('+x+'px,'+y+'px) scale(';
 var a=s.animate([{transform:t+'.15)',opacity:.9},{transform:t+'1.9)',opacity:0}],{duration:520,easing:'cubic-bezier(.2,.7,.2,1)'});
 a.onfinish=function(){s.remove()}}

// ---- 3D tilt
var TILT='.task,.card,.facts,.chap',cur=null,rect=null,px=0,py=0,pend=0,MAX=6;
function paint(){pend=0;if(!cur)return;
 var x=(px-rect.left)/rect.width,y=(py-rect.top)/rect.height,s=cur.style;
 s.setProperty('--ry',((x-.5)*MAX*2).toFixed(2)+'deg');
 s.setProperty('--rx',((.5-y)*MAX*2).toFixed(2)+'deg');
 s.setProperty('--gx',(px-rect.left).toFixed(0)+'px');
 s.setProperty('--gy',(py-rect.top).toFixed(0)+'px')}
function leave(){if(!cur)return;
 cur.classList.remove('fx-tilt');
 ['--rx','--ry','--gx','--gy'].forEach(function(k){cur.style.removeProperty(k)});
 cur=null}
function enter(el,x,y){if(cur===el)return;leave();
 var r=el.getBoundingClientRect();if(r.height>600||r.width<40)return;
 cur=el;rect=r;MAX=Math.max(2,Math.min(8,2400/Math.max(r.width,r.height)));
 el.classList.add('fx-tilt');move(x,y)}
function move(x,y){px=x;py=y;if(!pend){pend=1;raf(paint)}}
function hit(e){return e.target&&e.target.closest?e.target.closest(TILT):null}

d.addEventListener('pointermove',function(e){
 if(!on()||e.pointerType!=='mouse'||!mouse)return;
 var t=hit(e);if(!t){leave();return}
 if(t!==cur)enter(t,e.clientX,e.clientY);else move(e.clientX,e.clientY)},{passive:true});
d.addEventListener('mouseout',function(e){if(cur&&!cur.contains(e.relatedTarget))leave()});
d.addEventListener('scroll',function(){if(cur&&mouse)leave()},{passive:true,capture:true});

d.addEventListener('pointerdown',function(e){
 if(!on()||e.button>0)return;
 var t=e.target.closest?e.target.closest(RIP):null;
 if(t&&!t.disabled)ripple(e.clientX,e.clientY);
 if(e.pointerType!=='mouse'){var p=hit(e);if(p)enter(p,e.clientX,e.clientY)}},{passive:true});
function release(e){if(e.pointerType!=='mouse')leave()}
d.addEventListener('pointerup',release,{passive:true});
d.addEventListener('pointercancel',release,{passive:true});

// ---- tab indicator that slides from the previous page's tab
function tabs(){
 var t=$('.tabs');if(!t||$('.fxind',t))return;
 var ind=d.createElement('span');ind.className='fxind';t.appendChild(ind);
 var at=function(a){return 'translateX('+a.offsetLeft+'px) scaleX('+(a.offsetWidth/100).toFixed(3)+')'};
 var c=$('a[aria-current]',t);
 if(!c){ind.style.opacity=0;return}
 t.scrollLeft=Math.max(0,c.offsetLeft-(t.clientWidth-c.offsetWidth)/2);
 var now=at(c),old=null;
 try{old=JSON.parse(sessionStorage.getItem('fxtab'));sessionStorage.setItem('fxtab',JSON.stringify({x:c.offsetLeft,w:c.offsetWidth}))}catch(e){}
 ind.style.transform=now;
 if(old&&ind.animate&&on()){
  ind.animate([{transform:'translateX('+old.x+'px) scaleX('+(old.w/100).toFixed(3)+')'},{transform:now}],{duration:420,easing:'cubic-bezier(.2,.7,.2,1)'})}
 t.addEventListener('pointerover',function(e){if(!on()||e.pointerType!=='mouse')return;var a=e.target.closest('a');if(a&&t.contains(a))ind.style.transform=at(a)});
 t.addEventListener('pointerleave',function(){ind.style.transform=at(c)});
 addEventListener('resize',function(){ind.style.transform=at(c)});
 addEventListener('load',function(){ind.style.transform=at(c)})}

function start(){tabs();if(h.classList.contains('fx-boot')&&on())boot();else h.classList.remove('fx-boot')}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',start);else start();
})();
