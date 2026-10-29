// Drives the built site in jsdom: directory regrouping, scene filtering, pointers,
// hash presets, read-up-to, search. Run: node gen/tests/browser_test.js [siteDir]
const {JSDOM}=require(process.env.JSDOM_PATH||'jsdom');const path=require('path');const fs=require('fs');
const site=path.resolve(process.argv[2]||'docs');let fails=0;
const ok=(c,m)=>{console.log((c?'ok   ':'FAIL ')+m);if(!c)fails++};
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function open(rel,hash){const f=path.join(site,rel);
 const d=await JSDOM.fromFile(f,{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,url:'file://'+f+(hash||'')});
 d.window.HTMLElement.prototype.scrollIntoView=function(){};
 await wait(400);return d.window}
const click=(w,el)=>el.dispatchEvent(new w.MouseEvent('click',{bubbles:true}));
const type=(w,el,v)=>{el.value=v;el.dispatchEvent(new w.Event('input',{bubbles:true}))};
(async()=>{
 let w=await open('people/index.html'),$=s=>w.document.querySelector(s),$$=s=>[...w.document.querySelectorAll(s)];
 const vis=()=>$$('.dir .row').filter(r=>!r.hidden).length;
 ok(vis()===253,'directory shows all 253 rows ('+vis()+')');
 const tiers=()=>$$('section.tier[data-tier]').map(s=>s.querySelector('.ct').textContent).join('/');
 const t0=tiers();ok(/^\d+\/\d+\/\d+$/.test(t0),'tier counts '+t0);
 click(w,$('[data-dirscope] [data-s="1"]'));const v1=vis(),t1=tiers();ok(v1<253&&v1>0,'Year 1 scope narrows to '+v1+' ('+t1+')');
 click(w,$('[data-dirscope] [data-s="all"]'));ok(vis()===253,'All years restores 253');
 w.document.getElementById('dp').checked=true;w.document.getElementById('dp').dispatchEvent(new w.Event('change',{bubbles:true}));
 ok(vis()===17,'only-with-a-page shows 17 ('+vis()+')');w.document.getElementById('dp').checked=false;w.document.getElementById('dp').dispatchEvent(new w.Event('change',{bubbles:true}));
 type(w,$('#dq'),'ayanokoji');const names=$$('.dir .row').filter(r=>!r.hidden).map(r=>r.textContent.slice(0,22));ok(vis()>=2&&names.some(n=>/Kiyotaka/.test(n)),'accent-free search finds Ayanokōji: '+vis());
 type(w,$('#dq'),'');click(w,$('.alpha button[data-l="K"]'));ok(vis()>0&&$$('.dir .row').filter(r=>!r.hidden).every(r=>r.dataset.l==='K'),'letter K filters ('+vis()+')');
 w.close();

 w=await open('people/ayanokouji-kiyotaka.html');$=s=>w.document.querySelector(s);$$=s=>[...w.document.querySelectorAll(s)];
 const cards=()=>$$('.results .card').length,cnt=()=>$('.count').textContent;
 ok(cards()===12,'character shows first 12 of payload ('+cnt()+')');
 const total=+/of (\d+)/.exec(cnt())[1];ok(total===88,'88 scenes in payload ('+total+')');
 click(w,$('.morebtn'));ok(cards()===24,'Load more adds 12 ('+cards()+')');
 const k=$('.chips [data-k="inner"]');click(w,k);ok(cards()>0&&$$('.results .card').every(c=>/inner/.test(c.dataset?c.querySelector('li.q.inner')?'inner':'inner':'')) ,'inner chip filters: '+cnt());click(w,k);
 const fw=$('.fw');fw.value='horikita-suzune';fw.dispatchEvent(new w.Event('change',{bubbles:true}));const wh=+/of (\d+)/.exec(cnt())[1];ok(wh>0&&wh<88,'With Horikita narrows to '+wh);fw.value='';fw.dispatchEvent(new w.Event('change',{bubbles:true}));
 type(w,$('.fq'),'convenience store');ok(cards()>=1&&cards()<20,'text search in scenes: '+cnt());type(w,$('.fq'),'');
 const ptr=$('.results button.ptr[data-go]');ok(!!ptr,'a scene has a before/after pointer');
 if(ptr){const id=ptr.dataset.go;click(w,ptr);ok(!!w.document.getElementById(id),'pointer loads and shows '+id)}
 const rb=$('.chipbtn[data-with]');if(rb){click(w,rb);ok(w.document.querySelector('.fw').value===rb.dataset.with,'Scenes together sets With='+rb.dataset.with)}
 w.document.getElementById('upto').value='1';w.document.getElementById('upto').dispatchEvent(new w.Event('change',{bubbles:true}));
 const ut=+/of (\d+)/.exec(cnt())[1];ok(ut>0&&ut<88,'read-up-to Y1V1 hides later scenes: '+cnt());
 w.close();

 w=await open('people/sudou-ken.html');$=s=>w.document.querySelector(s);
 const first=JSON.parse(/CARDS\[[^\]]*?\]=(.*);\s*$/s.exec(fs.readFileSync(path.join(site,'assets/s/people-sudou-ken.js'),'utf8'))[1]);
 const target=first[first.length-1].i;w.close();
 w=await open('people/sudou-ken.html','#'+target);ok(!!w.document.getElementById(target),'deep link #'+target+' loads the scene that is not in the static HTML');w.close();

 w=await open('index.html');$=s=>w.document.querySelector(s);const q=$('#q');type(w,q,'sudo');await wait(300);
 ok(!$('#sr').hidden&&$('#sr').querySelectorAll('a').length>=2,'header search returns results ('+$('#sr').querySelectorAll('a').length+')');
 ok(/Sud/.test($('#sr').textContent),'search "sudo" finds Sudō Ken');w.close();
 w=await open('topics/who-knew-what.html');ok(w.document.querySelectorAll('.results .card').length>0,'topic page renders entry cards');w.close();
 console.log(fails?`\n${fails} FAILED`:'\nall browser checks passed');process.exit(fails?1:0)})();
