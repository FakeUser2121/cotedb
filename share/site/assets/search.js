(function () {
  var input = document.getElementById('q');
  var box = document.getElementById('results');
  if (!input || !box || typeof SEARCH_INDEX === 'undefined') return;
  var ROOT = document.body.getAttribute('data-root') || '';
  var sel = -1;

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function search(q) {
    q = q.trim().toLowerCase();
    if (q.length < 2) return [];
    var terms = q.split(/\s+/);
    var hits = [];
    for (var i = 0; i < SEARCH_INDEX.length; i++) {
      var r = SEARCH_INDEX[i];
      var t = (r.t + ' ' + r.s + ' ' + r.x).toLowerCase();
      var score = 0, ok = true;
      for (var j = 0; j < terms.length; j++) {
        var w = terms[j];
        if (t.indexOf(w) < 0) { ok = false; break; }
        if (r.t.toLowerCase().indexOf(w) >= 0) score += 4;
        if (r.s.toLowerCase().indexOf(w) >= 0) score += 3;
        score += 1;
      }
      if (ok) hits.push({ r: r, score: score, at: t.indexOf(terms[0]) });
    }
    hits.sort(function (a, b) { return b.score - a.score || a.at - b.at; });
    return hits.slice(0, 12);
  }
  function snippet(x, terms) {
    var low = x.toLowerCase(), at = -1;
    for (var j = 0; j < terms.length && at < 0; j++) at = low.indexOf(terms[j]);
    if (at < 0) at = 0;
    var a = Math.max(0, at - 55), b = Math.min(x.length, at + 95);
    var s = (a > 0 ? '…' : '') + x.slice(a, b) + (b < x.length ? '…' : '');
    s = esc(s);
    for (var k = 0; k < terms.length; k++) {
      var re = new RegExp('(' + terms[k].replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig');
      s = s.replace(re, '<mark>$1</mark>');
    }
    return s;
  }
  function render(q) {
    var terms = q.trim().toLowerCase().split(/\s+/);
    var hits = search(q);
    sel = -1;
    if (!q.trim() || q.trim().length < 2) { box.hidden = true; return; }
    if (!hits.length) {
      box.innerHTML = '<div class="none">No matches for “' + esc(q) + '”</div>';
      box.hidden = false; return;
    }
    var html = '';
    for (var i = 0; i < hits.length; i++) {
      var r = hits[i].r;
      html += '<a href="' + ROOT + r.u + '">' +
        '<div class="rt">' + esc(r.t) + '</div>' +
        '<div class="rs">' + esc(r.s) + '</div>' +
        '<div class="rx">' + snippet(r.x, terms) + '</div></a>';
    }
    box.innerHTML = html;
    box.hidden = false;
  }
  input.addEventListener('input', function () { render(input.value); });
  input.addEventListener('focus', function () { render(input.value); });
  document.addEventListener('click', function (e) {
    if (!box.contains(e.target) && e.target !== input) box.hidden = true;
  });
  document.addEventListener('keydown', function (e) {
    var links = box.querySelectorAll('a');
    if (e.key === '/' && document.activeElement !== input) {
      e.preventDefault(); input.focus(); input.select();
    } else if (e.key === 'Escape') { box.hidden = true; input.blur(); }
    else if (e.key === 'ArrowDown' && !box.hidden && links.length) {
      e.preventDefault(); sel = Math.min(sel + 1, links.length - 1); mark(links);
    } else if (e.key === 'ArrowUp' && !box.hidden && links.length) {
      e.preventDefault(); sel = Math.max(sel - 1, 0); mark(links);
    } else if (e.key === 'Enter' && !box.hidden && links.length && sel >= 0) {
      e.preventDefault(); links[sel].click();
    }
  });
  function mark(links) {
    for (var i = 0; i < links.length; i++)
      links[i].classList.toggle('sel', i === sel);
    if (links[sel]) links[sel].scrollIntoView({ block: 'nearest' });
  }
  if (location.hash.indexOf('#q=') === 0) {
    input.value = decodeURIComponent(location.hash.slice(3));
    input.focus();
    render(input.value);
  }
})();
