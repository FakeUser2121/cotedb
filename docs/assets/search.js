(function () {
  var input = document.getElementById("q");
  var box = document.getElementById("results");
  if (!input || !box || typeof SEARCH_INDEX === "undefined") return;
  var root = document.body.getAttribute("data-root") || "";
  var sel = -1, hits = [];
  var norm = function (s) {
    return s.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "");
  };
  var tokens = function (s) { return norm(s).replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter(Boolean); };
  var pool = SEARCH_INDEX.map(function (r) {
    return { r: r, hay: norm([r.t, r.s, r.k || "", r.x].join(" ")), toks: tokens(r.t + " " + r.s) };
  });
  function score(item, qtoks) {
    var hay = item.hay, s = 0, all = true;
    for (var i = 0; i < qtoks.length; i++) {
      var t = qtoks[i];
      if (hay.indexOf(t) === -1) { all = false; continue; }
      s += 1;
      if (item.toks.indexOf(t) !== -1) s += 3;
    }
    if (!all && qtoks.length > 1) return 0;
    if (all) s += 4;
    return s;
  }
  function run(q) {
    var qtoks = tokens(q);
    if (!qtoks.length) return [];
    var out = [];
    for (var i = 0; i < pool.length; i++) {
      var sc = score(pool[i], qtoks);
      if (sc > 0) out.push([sc, pool[i]]);
    }
    out.sort(function (a, b) { return b[0] - a[0]; });
    return out.slice(0, 24).map(function (p) { return p[1]; });
  }
  function snippet(item, qtoks) {
    var x = item.r.x || "";
    var low = norm(x);
    for (var i = 0; i < qtoks.length; i++) {
      var at = low.indexOf(qtoks[i]);
      if (at > -1) {
        var s = Math.max(0, at - 60), e = Math.min(x.length, at + 180);
        return (s ? "…" : "") + x.slice(s, e) + (e < x.length ? "…" : "");
      }
    }
    return x.slice(0, 200);
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function draw(q) {
    hits = run(q); sel = -1;
    if (!q) { box.hidden = true; box.innerHTML = ""; return; }
    if (!hits.length) {
      box.hidden = false;
      box.innerHTML = '<div class="none">Nothing matches “' + esc(q) + '”.</div>';
      return;
    }
    var qtoks = tokens(q);
    var out = hits.map(function (item, i) {
      var r = item.r;
      return '<a href="' + root + r.u + '" class="' + (i === sel ? "sel" : "") + '">'
        + '<div class="rt">' + esc(r.t) + '</div>'
        + (r.s && r.s !== r.t ? '<div class="rs">' + esc(r.k ? r.k + " · " : "") + esc(r.s) + '</div>' : '<div class="rs">' + esc(r.k || "") + '</div>')
        + '<div class="rx">' + esc(snippet(item, qtoks)) + '</div></a>';
    });
    box.hidden = false; box.innerHTML = out.join("");
  }
  input.addEventListener("input", function () { draw(input.value.trim()); });
  input.addEventListener("focus", function () { if (input.value) draw(input.value.trim()); });
  input.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      var links = box.querySelectorAll("a"); if (!links.length) return;
      sel = e.key === "ArrowDown" ? Math.min(sel + 1, links.length - 1) : Math.max(sel - 1, 0);
      for (var i = 0; i < links.length; i++) links[i].className = i === sel ? "sel" : "";
      links[sel].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && sel >= 0) {
      var l = box.querySelectorAll("a")[sel]; if (l) window.location.href = l.href;
    } else if (e.key === "Escape") { box.hidden = true; input.blur(); }
  });
  document.addEventListener("click", function (e) {
    if (!box.contains(e.target) && e.target !== input) box.hidden = true;
  });
})();