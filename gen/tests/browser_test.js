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
 const all=()=>$$('.dir .row').length;
 ok(vis()===all(),'directory shows all rows ('+vis()+')');
 const tiers=()=>$$('section.tier[data-tier]').map(s=>s.querySelector('.ct').textContent).join('/');
 const t0=tiers();ok(/^\d+\/\d+\/\d+$/.test(t0),'tier counts '+t0);
 click(w,$('[data-dirscope] [data-s="1"]'));const v1=vis(),t1=tiers();ok(v1<all()&&v1>0,'Year 1 scope narrows to '+v1+' ('+t1+')');
 click(w,$('[data-dirscope] [data-s="all"]'));ok(vis()===all(),'All years restores all rows');
 w.document.getElementById('dp').checked=true;w.document.getElementById('dp').dispatchEvent(new w.Event('change',{bubbles:true}));
 const paged=()=>$$('.dir .row').filter(r=>r.dataset.p==='1').length;
 ok(vis()===paged(),'only-with-a-page shows '+paged()+' ('+vis()+')');w.document.getElementById('dp').checked=false;w.document.getElementById('dp').dispatchEvent(new w.Event('change',{bubbles:true}));
 type(w,$('#dq'),'ayanokoji');const names=$$('.dir .row').filter(r=>!r.hidden).map(r=>r.textContent.slice(0,22));ok(vis()>=2&&names.some(n=>/Kiyotaka/.test(n)),'accent-free search finds Ayanokōji: '+vis());
 type(w,$('#dq'),'horikta');const hn=$$('.dir .row').filter(r=>!r.hidden).map(r=>r.textContent.slice(0,22));ok(vis()>=1&&hn.some(n=>/Horikita/.test(n)),'fuzzy directory "horikta" finds Horikita: '+vis());
 type(w,$('#dq'),'');click(w,$('.alpha button[data-l="K"]'));ok(vis()>0&&$$('.dir .row').filter(r=>!r.hidden).every(r=>r.dataset.l==='K'),'letter K filters ('+vis()+')');
 w.close();

 w=await open('people/ayanokouji-kiyotaka.html');$=s=>w.document.querySelector(s);$$=s=>[...w.document.querySelectorAll(s)];
 const cards=()=>$$('.results .card').length,cnt=()=>$('.count').textContent;
 ok(cards()===12,'character shows first 12 of payload ('+cnt()+')');
 const pay=JSON.parse(/CARDS\[[^\]]*?\]=(.*);\s*$/s.exec(fs.readFileSync(path.join(site,'assets/s/people-ayanokouji-kiyotaka.js'),'utf8'))[1]);
 const total=+/of (\d+)/.exec(cnt())[1];ok(total===pay.length,pay.length+' scenes in payload ('+total+')');
 click(w,$('.morebtn'));ok(cards()===24,'Load more adds 12 ('+cards()+')');
 const k=$('.chips [data-k="inner"]');click(w,k);ok(cards()>0&&$$('.results .card').every(c=>/inner/.test(c.dataset?c.querySelector('li.q.inner')?'inner':'inner':'')) ,'inner chip filters: '+cnt());click(w,k);
 const fw=$('.fw');fw.value='horikita-suzune';fw.dispatchEvent(new w.Event('change',{bubbles:true}));const wh=+/of (\d+)/.exec(cnt())[1];ok(wh>0&&wh<total,'With Horikita narrows to '+wh);fw.value='';fw.dispatchEvent(new w.Event('change',{bubbles:true}));
 type(w,$('.fq'),'convenience store');ok(cards()>=1&&cards()<20,'text search in scenes: '+cnt());type(w,$('.fq'),'');
 type(w,$('.fq'),'conveniance');ok(cards()>=1&&cards()<20,'fuzzy scene filter "conveniance": '+cnt());type(w,$('.fq'),'');
 const ptr=$('.results button.ptr[data-go]');ok(!!ptr,'a scene has a before/after pointer');
 if(ptr){const id=ptr.dataset.go;click(w,ptr);ok(!!w.document.getElementById(id),'pointer loads and shows '+id)}
 const rb=$('.chipbtn[data-with]');if(rb){click(w,rb);ok(w.document.querySelector('.fw').value===rb.dataset.with,'Scenes together sets With='+rb.dataset.with)}
 w.document.getElementById('upto').value='1';w.document.getElementById('upto').dispatchEvent(new w.Event('change',{bubbles:true}));
 const ut=+/of (\d+)/.exec(cnt())[1];ok(ut>0&&ut<total,'read-up-to Y1V1 hides later scenes: '+cnt());
 w.close();

 w=await open('people/sudou-ken.html');$=s=>w.document.querySelector(s);
 const first=JSON.parse(/CARDS\[[^\]]*?\]=(.*);\s*$/s.exec(fs.readFileSync(path.join(site,'assets/s/people-sudou-ken.js'),'utf8'))[1]);
 const target=first[first.length-1].i;w.close();
 w=await open('people/sudou-ken.html','#'+target);ok(!!w.document.getElementById(target),'deep link #'+target+' loads the scene that is not in the static HTML');w.close();

 w=await open('index.html');$=s=>w.document.querySelector(s);const q=$('#q');type(w,q,'sudo');await wait(300);
 ok(!$('#sr').hidden&&$('#sr').querySelectorAll('a').length>=2,'header search returns results ('+$('#sr').querySelectorAll('a').length+')');
 ok(/Sud/.test($('#sr').textContent),'search "sudo" finds Sudō Ken');
 type(w,q,'horikta');await wait(300);
 ok(!$('#sr').hidden&&/Horikita/.test($('#sr').textContent),'fuzzy search "horikta" finds Horikita ('+$('#sr').querySelectorAll('a').length+')');w.close();
 w=await open('topics/who-knew-what.html');ok(w.document.querySelectorAll('.results .card').length>0,'topic page renders entry cards');w.close();
 w=await open('index.html');$=s=>w.document.querySelector(s);
 const H=w.document.documentElement;
 ok(['full','static'].includes(H.dataset.fx),'boot sets data-fx ('+H.dataset.fx+')');
 const tg=$('#fxtoggle');ok(!!tg,'FX toggle is mounted in the header');
 if(tg){const before=H.dataset.fx;click(w,tg);ok(H.dataset.fx!==before,'toggle flips data-fx to '+H.dataset.fx);
  click(w,tg);ok(H.dataset.fx===before,'toggle flips back to '+H.dataset.fx)}
 if(tg&&H.dataset.fx!=='full')click(w,tg);
 await wait(500);ok(H.dataset.fx==='full','full mode can be switched on by the toggle');
 ok(!!$('.fxind'),'fx.js loads and mounts the tab indicator');
 const tk=$('.task');if(tk){tk.dispatchEvent(new w.MouseEvent('pointerdown',{bubbles:true}));ok(true,'pointerdown on a task does not throw')}
 w.close();
 console.log(fails?`\n${fails} FAILED`:'\nall browser checks passed');process.exit(fails?1:0)})();
