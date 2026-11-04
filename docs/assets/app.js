(function(){
'use strict';
var $=function(s,r){return (r||document).querySelector(s)},$$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
var fold=function(s){return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9 ]+/g,' ').trim()};
var store={get:function(k){try{return localStorage.getItem(k)}catch(e){return null}},set:function(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
var root=document.body.dataset.root||'';
var th=store.get('theme');if(th)document.documentElement.dataset.theme=th;
var tb=$('#theme');if(tb)tb.onclick=function(){var n=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=n;store.set('theme',n)};

var upto=+store.get('upto')||0,panels=[],scopeY='';
var sel=$('#upto');
if(sel&&window.VOLS){sel.innerHTML='<option value="0">all volumes</option>'+VOLS.map(function(v){return '<option value="'+v[0]+'">'+v[1]+'</option>'}).join('');sel.value=upto;
 sel.onchange=function(){upto=+sel.value;store.set('upto',upto);applyScope();panels.forEach(function(p){p.refresh()});if(window.dirApply)dirApply()}}
function applyScope(){$$('[data-o]:not(.card)').forEach(function(e){var hide=(upto>0&&+e.dataset.o>upto)||(scopeY&&e.dataset.y&&e.dataset.y!==scopeY);e.hidden=!!hide});
 $$('section[data-y]').forEach(function(e){e.hidden=!!(scopeY&&e.dataset.y!==scopeY)})}

// ---- scene panels
$$('.results[data-key]').forEach(function(res){
 var items=(window.CARDS||{})[res.dataset.key]||[],wrap=res.parentNode,size=+res.dataset.size||12;
 var st={q:'',k:{},w:'',v:'',n:size},fq=$('.fq',wrap),fw=$('.fw',wrap),fv=$('.fv',wrap),more=$('.morebtn',wrap),cnt=$('.count',wrap);
 var noun=(cnt.textContent.replace(/^\d+\s*/,'')||'scenes');
 function ok(it){if(upto&&it.o>upto)return false;if(scopeY&&String(it.y)!==scopeY)return false;if(st.v&&it.v!==st.v)return false;
  if(st.w&&(' '+it.w+' ').indexOf(' '+st.w+' ')<0)return false;
  var ks=Object.keys(st.k).filter(function(k){return st.k[k]});if(ks.length&&!ks.some(function(k){return(' '+it.k+' ').indexOf(' '+k+' ')>=0}))return false;
  if(st.q){var q=fold(st.q).split(' ').filter(Boolean),hits=0;for(var i=0;i<q.length;i++){var tok=q[i],alt=stem(tok);if(it.q.indexOf(tok)>=0||(alt!==tok&&alt.length>2&&it.q.indexOf(alt)>=0))hits++}if(hits<Math.ceil(q.length/2))return false}return true}
 function list(){return items.filter(ok)}
 function refresh(keep){if(!keep)st.n=size;var l=list(),shown=l.slice(0,st.n);res.innerHTML=shown.map(function(i){return i.h}).join('');
  cnt.textContent='Showing '+shown.length+' of '+l.length+' '+noun+(l.length<items.length?' (filtered from '+items.length+')':'');more.hidden=l.length<=st.n}
 function go(id){var l=list(),i=l.findIndex(function(x){return x.i===id});
  if(i<0){st.q='';st.k={};st.w='';st.v='';if(fq)fq.value='';if(fw)fw.value='';if(fv)fv.value='';$$('.chips [data-k]',wrap).forEach(function(b){b.classList.remove('on')});l=list();i=l.findIndex(function(x){return x.i===id})}
  if(i<0)return false;if(i>=st.n)st.n=i+1;refresh(true);var el=document.getElementById(id);
  if(el){el.scrollIntoView({block:'center'});el.classList.add('flash');setTimeout(function(){el.classList.remove('flash')},1600)}return true}
 if(fq)fq.oninput=function(){st.q=fq.value;refresh()};if(fw)fw.onchange=function(){st.w=fw.value;refresh()};if(fv)fv.onchange=function(){st.v=fv.value;refresh()};
 $$('.chips [data-k]',wrap).forEach(function(b){b.onclick=function(){st.k[b.dataset.k]=!st.k[b.dataset.k];b.classList.toggle('on');refresh()}});
 more.onclick=function(){st.n+=size;refresh(true)};
 res.addEventListener('click',function(e){var b=e.target.closest('button.ptr');if(b)go(b.dataset.go)});
 var p={refresh:refresh,go:go,setWith:function(w){st.w=w;if(fw)fw.value=w;refresh()}};panels.push(p);refresh();
});
$$('.chipbtn[data-with]').forEach(function(b){b.onclick=function(){panels.forEach(function(p){p.setWith(b.dataset.with)});var c=$('.cards');if(c)c.scrollIntoView()}});
$$('[data-pagescope] button').forEach(function(b){b.onclick=function(){$$('[data-pagescope] button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');scopeY=b.dataset.y;applyScope();panels.forEach(function(p){p.refresh()})}});
function hash(){var h=location.hash.slice(1);if(h.indexOf('with=')===0){var w=h.slice(5);panels.forEach(function(p){p.setWith(w)})}else if(h.indexOf('sc-')===0){var done=false;panels.forEach(function(p){if(!done&&p.go(h))done=true})}}
window.addEventListener('hashchange',hash);

// ---- people directory
var dir=$('.dirpanel');
if(dir){var rows=$$('.dir .row'),tiers=$$('section.tier[data-tier]'),sc='all',dq=$('#dq'),dc=$('#dc'),dr=$('#dr'),dp=$('#dp'),dcount=$('#dcount'),letter='';
 rows.forEach(function(r,i){r.dataset.i=i});
 window.dirApply=function(){var q=fold(dq.value).split(' ').filter(Boolean),shown=0,counts={main:0,supporting:0,minor:0},tkey=sc==='all'?'ta':'t'+sc;
  var buckets={main:[],supporting:[],minor:[]};
  rows.forEach(function(r){var t=r.dataset[tkey],ys=(r.dataset.y||'').split(' '),vis=!!t;
   if(vis&&sc!=='all'&&ys.indexOf(sc)<0)vis=false;if(vis&&dc.value&&r.dataset.c!==dc.value)vis=false;
   if(vis&&dr.value&&(' '+r.dataset.r+' ').indexOf(' '+dr.value+' ')<0)vis=false;if(vis&&dp.checked&&r.dataset.p!=='1')vis=false;
   if(vis&&letter&&r.dataset.l!==letter)vis=false;if(vis&&q.length){for(var i=0;i<q.length;i++)if(r.dataset.n.indexOf(q[i])<0){vis=false;break}}
   r.hidden=!vis;if(vis){shown++;counts[t]++;buckets[t].push(r)}});
  tiers.forEach(function(s){var k=s.dataset.tier,ul=$('ul',s);buckets[k].sort(function(a,b){return a.dataset.i-b.dataset.i});
   var all=rows.filter(function(r){return r.dataset[tkey]===k}).sort(function(a,b){return a.dataset.i-b.dataset.i});all.forEach(function(r){ul.appendChild(r)});
   $('.ct',s).textContent=counts[k];s.hidden=counts[k]===0});
  dcount.textContent=shown+' of '+rows.length+' shown'};
 [dq,dc,dr,dp].forEach(function(e){e.oninput=e.onchange=dirApply});
 $$('[data-dirscope] button').forEach(function(b){b.onclick=function(){$$('[data-dirscope] button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');sc=b.dataset.s;dirApply()}});
 $$('.alpha button').forEach(function(b){b.onclick=function(){var on=b.classList.contains('on');$$('.alpha button').forEach(function(x){x.classList.remove('on')});letter=on?'':b.dataset.l;if(!on)b.classList.add('on');dirApply()}});
 var gid=location.hash.slice(1),tgt=gid&&document.getElementById(gid);if(tgt&&tgt.classList.contains('row')){var d=$('details',tgt);if(d)d.open=true;tgt.scrollIntoView({block:'center'})}
 dirApply()}

// ---- search
var idxLoaded=false;
function loadIdx(cb){if(window.IDX||idxLoaded){cb();return}idxLoaded=true;var s=document.createElement('script');s.src=root+'assets/search-index.js';s.onload=cb;document.head.appendChild(s)}
function stem(w){return w.length>4?w.replace(/(ing|ed|es|s)$/,''):w}
var cmap=null;
function charScope(toks){
 if(!cmap){cmap={};
  for(var i=0;i<IDX.length;i++){var r=IDX[i];if(r[1]!=='Character')continue;
   var id=r[2].replace(/^people\//,'').replace(/\.html(#.*)?$/,'');
   if(id==='index'||!id)continue;
   var ws=(fold(r[0])+' '+r[3]).split(' ');
   for(var j=0;j<ws.length;j++){var w=ws[j];if(w.length<2)continue;
    if(!cmap[w])cmap[w]=[];if(cmap[w].indexOf(id)<0)cmap[w].push(id)}}}
 var ids=[];
 for(var i=0;i<toks.length;i++){
  var cands=[];
  [toks[i],stem(toks[i])].forEach(function(w){var l=cmap[w];
   if(l)l.forEach(function(id){if(cands.indexOf(id)<0)cands.push(id)})});
  if(cands.length===1&&ids.indexOf(cands[0])<0)ids.push(cands[0])}
 return ids}
function find(q){var raw=fold(q),t=raw.split(' ').filter(Boolean);if(!t.length)return[];
 var ids=charScope(t),need=Math.ceil(t.length/2),out=[];
 for(var i=0;i<IDX.length;i++){var r=IDX[i];
  if(ids.length){var inscope=false;
   for(var p=0;p<ids.length;p++){var pre='people/'+ids[p]+'.html';if(r[2].indexOf(pre)===0){inscope=true;break}}
   if(!inscope)continue}
  var ti=fold(r[0]),body=r[3],hits=0,sc=0;
  for(var j=0;j<t.length;j++){var tok=t[j],alt=stem(tok);
   if(body.indexOf(tok)<0&&!(alt!==tok&&alt.length>2&&body.indexOf(alt)>=0))continue;
   hits++;if(ti.indexOf(tok)===0)sc+=3;else if(ti.indexOf(tok)>=0)sc+=2;else sc+=1}
  if(hits<need)continue;
  if(t.length>1&&body.indexOf(raw)>=0)sc+=4;
  out.push([sc+hits+(r[1]==='Scene'?0:2),r])}
 out.sort(function(a,b){return b[0]-a[0]});return out.slice(0,40).map(function(x){return x[1]})}
function show(box,res,max){var q=box.value;if(!q.trim()){res.innerHTML='';res.hidden=true;return}
 loadIdx(function(){var f=find(q).slice(0,max);res.innerHTML=f.length?f.map(function(r){return '<a href="'+root+r[2]+'"><span class="sr-t">'+r[0].replace(/</g,'&lt;')+'</span><span class="sr-k">'+r[1]+'</span></a>'}).join(''):'<a>No match</a>';res.hidden=false})}
var q=$('#q'),sr=$('#sr');if(q&&sr){q.oninput=function(){show(q,sr,10)};document.addEventListener('click',function(e){if(!sr.contains(e.target)&&e.target!==q)sr.hidden=true});
 q.onkeydown=function(e){if(e.key==='Enter'&&q.value.trim()){location.href=root+'search/index.html#q='+encodeURIComponent(q.value)}}}
var sq=$('#sq'),sres=$('#sres');if(sq&&sres){var m=/#q=(.*)$/.exec(location.hash);if(m)sq.value=decodeURIComponent(m[1]);sq.oninput=function(){show(sq,sres,40)};if(sq.value)show(sq,sres,40)}
applyScope();hash();
})();
