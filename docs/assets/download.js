(function(){
'use strict';
var $=function(s,r){return (r||document).querySelector(s)};
var $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
var root=document.body.dataset.root||'';
var people=window.DLPEOPLE||[];
var cache={};
var data=null,cid='',raw='';
var state={scenes:{},mode:'dialogue',setup:true};

function plural(n,word){return n+' '+word+(n===1?'':'s')}
function yearName(y){return y?'Year '+y:'Side stories'}
function yearOf(label){
  if(/^Side Stories/.test(label))return 0;
  var m=/^Year (\d+)/.exec(label);
  return m?+m[1]:0;
}
function has(key){return Object.prototype.hasOwnProperty.call(state.scenes,key)}

function parse(md){
  var lines=md.split('\n');
  var title=(lines[0]||'').replace(/^# /,'').trim();
  var start=lines.indexOf('## Scenes');
  var vols=[],v=null,s=null,i,l;
  for(i=start+1;i<lines.length;i++){
    l=lines[i];
    if(l.indexOf('### ')===0){
      v={label:l.slice(4).trim(),year:yearOf(l.slice(4)),scenes:[]};
      vols.push(v);s=null;continue;
    }
    if(l.indexOf('#### ')===0&&v){
      var h=l.slice(5),k=h.indexOf(' — ');
      s={pages:k<0?h.trim():h.slice(0,k),title:k<0?'':h.slice(k+3),setup:'',rows:[]};
      v.scenes.push(s);continue;
    }
    if(!s)continue;
    var m=/^- \*\*(.+?)\*\*(?: \((.*?)\))? — (.*)$/.exec(l);
    if(m){s.rows.push({label:m[1],pg:m[2]||'',text:m[3]});continue}
    if(l.trim()&&!s.setup)s.setup=l.trim();
  }
  return {title:title,vols:vols};
}

function keep(r){
  var l=r.label;
  if(state.mode==='dialogue')return l.indexOf('Spoken')===0||l.indexOf('Asked')===0;
  if(state.mode==='voice')return l.indexOf('Spoken')===0||l.indexOf('Asked')===0||l.indexOf('Inner voice')===0;
  return true;
}

function volKeys(vi){
  var out=[];
  data.vols[vi].scenes.forEach(function(_,si){out.push(vi+':'+si)});
  return out;
}
function yearKeys(y){
  var out=[];
  data.vols.forEach(function(v,vi){if(v.year===y)out=out.concat(volKeys(vi))});
  return out;
}
function yearsOf(){
  var seen={},out=[];
  data.vols.forEach(function(v){if(!seen[v.year]){seen[v.year]=1;out.push(v.year)}});
  out.sort(function(a,b){return (a||9)-(b||9)});
  return out;
}
function selected(){
  var out=[];
  if(!data)return out;
  data.vols.forEach(function(v,vi){
    v.scenes.forEach(function(s,si){
      if(!has(vi+':'+si))return;
      var rows=s.rows.filter(keep);
      if(rows.length)out.push({vi:vi,s:s,rows:rows});
    });
  });
  return out;
}
function isFull(){
  if(!data||state.mode!=='all'||!state.setup)return false;
  var total=0,sel=0;
  data.vols.forEach(function(v,vi){v.scenes.forEach(function(_,si){total++;if(has(vi+':'+si))sel++})});
  return total>0&&sel===total;
}

function update(){
  var sel=selected(),n=0;
  sel.forEach(function(x){n+=x.rows.length});
  $('#dlcount').textContent=sel.length?(plural(sel.length,'scene')+', '+plural(n,'line')+' selected.'):'Nothing selected yet.';
  $('#dlgo').disabled=!sel.length;
}

function sync(){
  $$('#dlyears input[data-year]').forEach(function(cb){
    var y=+cb.dataset.year,tot=0,sel=0;
    data.vols.forEach(function(v,vi){
      if(v.year!==y)return;
      v.scenes.forEach(function(_,si){tot++;if(has(vi+':'+si))sel++});
    });
    cb.checked=sel>0&&sel===tot;
    cb.indeterminate=sel>0&&sel<tot;
  });
  $$('#dlvols input[data-vol]').forEach(function(cb){
    var vi=+cb.dataset.vol,keys=volKeys(vi),sel=0;
    keys.forEach(function(k){if(has(k))sel++});
    cb.checked=sel>0&&sel===keys.length;
    cb.indeterminate=sel>0&&sel<keys.length;
  });
  $$('#dlscenes input[data-scene]').forEach(function(cb){cb.checked=has(cb.dataset.scene)});
}

function render(){
  var ys=yearsOf(),h='';
  state.scenes={};
  data.vols.forEach(function(v,vi){v.scenes.forEach(function(_,si){state.scenes[vi+':'+si]=1})});
  ys.forEach(function(y){
    var n=0;yearKeys(y).forEach(function(k){n++});
    h+='<label><input type="checkbox" data-year="'+y+'" checked> '+yearName(y)+' <span class="n">('+plural(n,'scene')+')</span></label>';
  });
  $('#dlyears').innerHTML=h;

  h='';
  data.vols.forEach(function(v,vi){
    h+='<label><input type="checkbox" data-vol="'+vi+'" checked> '+v.label+' <span class="n">('+plural(v.scenes.length,'scene')+')</span></label>';
  });
  $('#dlvols').innerHTML=h;

  h='';
  data.vols.forEach(function(v,vi){
    if(!v.scenes.length)return;
    h+='<div class="dlgrp"><p class="n">'+v.label+'</p>';
    v.scenes.forEach(function(s,si){
      var label=s.pages+(s.title?' — '+s.title:'');
      h+='<label title="'+label.replace(/"/g,'&quot;')+'"><input type="checkbox" data-scene="'+vi+':'+si+'" checked> '+label+'</label>';
    });
    h+='</div>';
  });
  $('#dlscenes').innerHTML=h;
  update();
}

function load(id){
  cid=id;
  if(!id){data=null;raw='';reset();return}
  if(cache[id]){data=cache[id].data;raw=cache[id].raw;render();return}
  $('#dlcount').textContent='Loading…';
  $('#dlgo').disabled=true;
  fetch(root+'people/'+id+'.md').then(function(r){
    if(!r.ok)throw new Error(String(r.status));
    return r.text();
  }).then(function(t){
    raw=t;data=parse(t);cache[id]={data:data,raw:t};render();
  }).catch(function(){
    data=null;raw='';
    $('#dlcount').textContent='That card could not be loaded.';
  });
}

function reset(){
  state.scenes={};
  $('#dlyears').innerHTML='<p class="n">Choose a character first.</p>';
  $('#dlvols').innerHTML='';
  $('#dlscenes').innerHTML='';
  $('#dlcount').textContent='Choose a character to see what is available.';
  $('#dlgo').disabled=true;
  $('#dlrawline').innerHTML='';
}

function subtitle(){
  for(var i=0;i<people.length;i++){
    if(people[i][0]===cid){
      var p=people[i],bits=['Character',p[3]];
      if(p[2])bits.push(p[2]);
      return bits.join(' · ');
    }
  }
  return 'Character';
}

function scopeText(sel){
  if(isFull())return 'full card';
  var ys=[];
  sel.forEach(function(x){var y=data.vols[x.vi].year;if(ys.indexOf(y)<0)ys.push(y)});
  ys.sort(function(a,b){return (a||9)-(b||9)});
  var vols=[];sel.forEach(function(x){if(vols.indexOf(x.vi)<0)vols.push(x.vi)});
  if(vols.length<=2&&vols.length){
    return vols.map(function(vi){return data.vols[vi].label}).join(' · ');
  }
  return ys.map(yearName).join(' · ');
}

function fileName(sel){
  if(isFull())return cid+'.md';
  var ys=[];sel.forEach(function(x){var y=data.vols[x.vi].year;if(ys.indexOf(y)<0)ys.push(y)});
  ys.sort(function(a,b){return (a||9)-(b||9)});
  var ypart=ys.length===yearsOf().length?'all':ys.map(function(y){return y?'y'+y:'side'}).join('-');
  var mode=state.mode==='dialogue'?'dialogue':state.mode==='voice'?'dialogue-voice':'all-notes';
  return cid+'-'+ypart+'-'+mode+'.md';
}

function compose(sel){
  if(isFull())return {text:raw,name:cid+'.md'};
  var n=0;sel.forEach(function(x){n+=x.rows.length});
  var mode=state.mode==='dialogue'?'Spoken lines only':state.mode==='voice'?'Spoken lines and inner voice':'Every note';
  var out=['# '+data.title+' — '+scopeText(sel),'','*'+subtitle()+'*','',
           mode+' from '+scopeText(sel)+'. '+plural(sel.length,'scene')+', '+plural(n,'line')+'.',''];
  var cur=-1;
  sel.forEach(function(x){
    var v=data.vols[x.vi];
    if(x.vi!==cur){cur=x.vi;out.push('## '+v.label);out.push('')}
    out.push('### '+x.s.pages+(x.s.title?' — '+x.s.title:''));
    out.push('');
    if(state.setup&&x.s.setup){out.push(x.s.setup);out.push('')}
    x.rows.forEach(function(r){
      out.push('- **'+r.label+'**'+(r.pg?' ('+r.pg+')':'')+' — '+r.text);
    });
    out.push('');
  });
  return {text:out.join('\n').replace(/\n+$/,'\n'),name:fileName(sel)};
}

function save(text,name){
  var blob=new Blob([text],{type:'text/markdown;charset=utf-8'});
  var url=URL.createObjectURL(blob);
  var a=document.createElement('a');
  a.href=url;a.download=name;document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(url);a.remove()},1500);
}

function selectCharacter(id){
  var sel=$('#dlchar');
  if(id&&people.some(function(p){return p[0]===id})){
    sel.value=id;
    $('#dlrawline').innerHTML='<a href="'+root+'people/'+id+'.md" download>Full card as one file</a> — every scene, every note.';
    load(id);
  }else{
    sel.value='';
    reset();
  }
}

function init(){
  var sel=$('#dlchar'),h='<option value="">Choose a character…</option>';
  people.forEach(function(p){
    h+='<option value="'+p[0]+'">'+p[1]+(p[2]?' ('+p[2]+')':'')+'</option>';
  });
  sel.innerHTML=h;
  sel.onchange=function(){selectCharacter(sel.value)};

  $('#dlyears').addEventListener('change',function(e){
    var cb=e.target;
    if(!cb.dataset.year)return;
    var keys=yearKeys(+cb.dataset.year);
    keys.forEach(function(k){if(cb.checked)state.scenes[k]=1;else delete state.scenes[k]});
    sync();update();
  });
  $('#dlvols').addEventListener('change',function(e){
    var cb=e.target;
    if(!cb.dataset.vol)return;
    volKeys(+cb.dataset.vol).forEach(function(k){if(cb.checked)state.scenes[k]=1;else delete state.scenes[k]});
    sync();update();
  });
  $('#dlscenes').addEventListener('change',function(e){
    var cb=e.target;
    if(!cb.dataset.scene)return;
    if(cb.checked)state.scenes[cb.dataset.scene]=1;else delete state.scenes[cb.dataset.scene];
    sync();update();
  });
  $$('#dlmodes input').forEach(function(r){r.onchange=function(){state.mode=r.value;update()}});
  $('#dlsetup').onchange=function(){state.setup=this.checked;update()};
  $('#dlall').onclick=function(){
    if(!data)return;
    data.vols.forEach(function(v,vi){v.scenes.forEach(function(_,si){state.scenes[vi+':'+si]=1})});
    sync();update();
  };
  $('#dlnone').onclick=function(){state.scenes={};sync();update()};
  $('#dlgo').onclick=function(){
    var sel=selected();
    if(!sel.length)return;
    var out=compose(sel);
    save(out.text,out.name);
  };

  var m=/[?&]char=([^&]+)/.exec(location.search);
  if(m)selectCharacter(decodeURIComponent(m[1]));
}

if(window.__DLTEST__)window.DLtest={
  parse:parse,
  load:function(text,id){raw=text;cid=id;data=parse(text);state.scenes={}},
  set:function(keys,mode,setup){
    state.scenes={};keys.forEach(function(k){state.scenes[k]=1});
    state.mode=mode;state.setup=setup;
  },
  keys:function(){var out=[];data.vols.forEach(function(v,vi){v.scenes.forEach(function(_,si){out.push(vi+':'+si)})});return out},
  years:function(){var out=[];data.vols.forEach(function(v,vi){if(out.indexOf(v.year)<0)out.push(v.year)});return out},
  yearKeys:yearKeys,
  build:function(){return compose(selected())},
  count:function(){return selected().length}
};

init();
})();
