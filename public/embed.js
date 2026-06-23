/**
 * Escape Call — embeddable one-button widget.
 *
 * Drop this anywhere with a single div:
 *   <div data-escape-call data-base="https://your-escape-call-host"></div>
 *   <script src="https://your-escape-call-host/embed.js"></script>
 *
 * Optional data-* attributes:
 *   data-base      backend origin (default: where this script is served from)
 *   data-delay     seconds before the call (default 60)
 *   data-scenario  scenario key (default "generic")
 *   data-phone     destination id from /config (default: first)
 *   data-label     button text (default "📞 Escape Call")
 */
(function () {
  var me = document.currentScript;
  function init() {
    var el = document.querySelector('[data-escape-call]') || document.getElementById('escape-call');
    if (!el || el.dataset.ecReady) return;
    el.dataset.ecReady = '1';

    var scriptBase = me && me.src ? me.src.replace(/\/embed\.js.*$/, '') : '';
    var base = (el.getAttribute('data-base') || scriptBase || location.origin).replace(/\/$/, '');
    var delay = parseInt(el.getAttribute('data-delay') || '60', 10);
    var scenario = el.getAttribute('data-scenario') || 'generic';
    var phone = el.getAttribute('data-phone') || '';
    var label = el.getAttribute('data-label') || '📞 Escape Call';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = label;
    btn.style.cssText =
      'font:600 14px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;' +
      'padding:12px 18px;border:0;border-radius:12px;background:#5b8cff;color:#fff;' +
      'cursor:pointer;display:inline-flex;align-items:center;gap:8px;transition:filter .15s';
    btn.onmouseenter = function () { btn.style.filter = 'brightness(1.1)'; };
    btn.onmouseleave = function () { btn.style.filter = ''; };

    var status = document.createElement('span');
    status.style.cssText =
      'margin-left:10px;font:13px -apple-system,"Segoe UI",Roboto,sans-serif;color:#7e889c';

    function pretty(s) { return s < 60 ? s + 's' : (s % 60 === 0 ? (s / 60) + ' min' : Math.round(s / 60) + ' min'); }

    btn.onclick = function () {
      var orig = btn.textContent;
      btn.disabled = true; btn.textContent = '…';
      fetch(base + '/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delay: delay, scenario: scenario, phone: phone })
      })
        .then(function (r) { return r.json(); })
        .then(function (j) { status.textContent = j.ok ? ('📞 ringing in ' + pretty(j.delay)) : ('⚠️ ' + (j.error || 'failed')); })
        .catch(function () { status.textContent = '⚠️ could not reach server'; })
        .then(function () { btn.disabled = false; btn.textContent = orig; });
    };

    el.appendChild(btn);
    el.appendChild(status);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
