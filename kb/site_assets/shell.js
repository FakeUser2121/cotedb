(function () {
  "use strict";

  var body = document.body;
  var root = body.getAttribute("data-root") || "";

  function store(key, value) {
    try {
      if (value === null) window.localStorage.removeItem(key);
      else window.localStorage.setItem(key, value);
    } catch (e) {}
  }

  function read(key, fallback) {
    try {
      var v = window.localStorage.getItem(key);
      return v === null ? fallback : v;
    } catch (e) {
      return fallback;
    }
  }

  function prefersDark() {
    return window.matchMedia
      && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function applyTheme(name) {
    if (name === "dark") document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.removeAttribute("data-theme");
    var btn = document.getElementById("theme");
    if (btn) btn.textContent = name === "dark" ? "Light" : "Dark";
  }

  var theme = read("cote.theme", prefersDark() ? "dark" : "light");
  applyTheme(theme);

  var toggle = document.getElementById("theme");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var dark = document.documentElement.getAttribute("data-theme") === "dark";
      theme = dark ? "light" : "dark";
      store("cote.theme", theme);
      applyTheme(theme);
    });
  }

  var menu = document.getElementById("menu");
  if (menu) {
    menu.addEventListener("click", function () {
      body.classList.toggle("menu-open");
    });
    document.addEventListener("click", function (ev) {
      if (!body.classList.contains("menu-open")) return;
      var rail = document.querySelector(".rail.left");
      if (rail && !rail.contains(ev.target) && ev.target !== menu) {
        body.classList.remove("menu-open");
      }
    });
  }

  var blocks = Array.prototype.slice.call(document.querySelectorAll(".later"));

  function applyScope(order) {
    body.removeAttribute("data-open-all");
    blocks.forEach(function (el) {
      var since = parseInt(el.getAttribute("data-since-order") || "0", 10);
      var past = order !== null && since > order;
      el.classList.toggle("is-hidden", past);
      if (!past) el.removeAttribute("data-revealed");
    });
  }

  var scopeSel = document.getElementById("scope");
  if (scopeSel && blocks.length) {
    var saved = read("cote.scope", "");
    if (saved) scopeSel.value = saved;
    var chosen = scopeSel.value;
    if (chosen && chosen !== "all") applyScope(parseInt(chosen, 10));
    scopeSel.addEventListener("change", function () {
      var v = scopeSel.value;
      if (v === "all") {
        store("cote.scope", null);
        blocks.forEach(function (el) { el.classList.remove("is-hidden"); });
      } else {
        store("cote.scope", v);
        applyScope(parseInt(v, 10));
      }
    });
  } else if (scopeSel) {
    scopeSel.parentNode.removeChild(scopeSel);
  }

  body.addEventListener("click", function (ev) {
    var btn = ev.target.closest ? ev.target.closest(".reveal") : null;
    if (!btn) return;
    var box = btn.closest(".later");
    if (box) {
      box.classList.remove("is-hidden");
      box.setAttribute("data-revealed", "1");
    }
  });

  var groups = document.querySelectorAll("[data-filterable]");
  if (groups.length) {
    document.body.addEventListener("click", function (ev) {
      var chip = ev.target.closest ? ev.target.closest(".filters button") : null;
      if (!chip) return;
      var wrap = chip.closest(".filter-host");
      if (!wrap) return;
      var want = chip.getAttribute("data-filter") || "";
      Array.prototype.forEach.call(
        wrap.querySelectorAll(".filters button"),
        function (b) { b.classList.toggle("on", b === chip); }
      );
      Array.prototype.forEach.call(
        wrap.querySelectorAll("[data-tags]"),
        function (item) {
          var tags = item.getAttribute("data-tags") || "";
          var show = !want || (" " + tags + " ").indexOf(" " + want + " ") > -1;
          item.hidden = !show;
          if (item.classList.contains("grid-list")) {
            item.style.display = show ? "" : "none";
          }
        }
      );
      var host = wrap.querySelector("[data-count-shown]");
      if (host) {
        var n = wrap.querySelectorAll("[data-tags]:not([hidden])").length;
        host.textContent = n;
      }
    });
  }

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") body.classList.remove("menu-open");
    if (ev.key === "/" && document.activeElement
        && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
      var q = document.getElementById("q");
      if (q) { ev.preventDefault(); q.focus(); q.select(); }
    }
  });

  var chipAll = document.getElementById("cite-all");
  if (chipAll) {
    chipAll.addEventListener("click", function () {
      var open = chipAll.getAttribute("aria-pressed") === "true";
      chipAll.setAttribute("aria-pressed", open ? "false" : "true");
      Array.prototype.forEach.call(
        document.querySelectorAll("details.citebox"),
        function (d) { d.open = !open; }
      );
    });
  }

  // Arriving at a folded scene (from search, a turning point, or a citation)
  // should show that scene, not a closed row: open it, and any details it is
  // nested in, before the browser settles on the anchor. A page pin points at
  // the scene's proof box, which sits inside the scene's own <details>.
  function revealHash() {
    var id = (location.hash || "").slice(1);
    if (!id) return;
    var el = document.getElementById(id);
    if (!el) return;
    for (var n = el; n; n = n.parentElement) {
      if (n.tagName === "DETAILS" && !n.open) n.open = true;
    }
    if (el.scrollIntoView) el.scrollIntoView({ block: "start" });
  }
  window.addEventListener("hashchange", revealHash);
  revealHash();
})();
