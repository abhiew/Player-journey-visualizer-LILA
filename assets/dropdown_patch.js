/**
 * LILA · Dropdown Dark-Mode Patch
 * 
 * React-Select v1 (used by Dash's dcc.Dropdown) sets background-color: white
 * as an inline style on .Select-control and .Select-menu-outer at render time.
 * CSS !important cannot override inline styles, so we use a MutationObserver
 * to scrub it immediately after React applies it.
 */
(function () {
  'use strict';

  const BG_CONTROL = '#1a1e24';
  const BG_MENU    = '#14171d';
  const FG         = '#ffffff';

  /** Force dark styles onto a Select-control element */
  function patchControl(el) {
    el.style.setProperty('background-color', BG_CONTROL, 'important');
    el.style.setProperty('background',       BG_CONTROL, 'important');
    el.style.setProperty('color',            FG,         'important');
    el.style.setProperty('border-color',     'rgba(255,255,255,0.12)', 'important');
  }

  /** Force dark styles onto a Select-menu-outer / Select-menu element */
  function patchMenu(el) {
    el.style.setProperty('background-color', BG_MENU, 'important');
    el.style.setProperty('background',       BG_MENU, 'important');
    el.style.setProperty('color',            FG,      'important');
  }

  /** Patch all value/placeholder text nodes */
  function patchText(root) {
    root.querySelectorAll(
      '.Select-value-label, .Select-single-value, .Select-placeholder, .Select-input > input'
    ).forEach(function (el) {
      el.style.setProperty('color', FG, 'important');
    });
  }

  function patchAll(root) {
    /* Controls */
    root.querySelectorAll('.Select-control').forEach(patchControl);
    /* Menu panels */
    root.querySelectorAll('.Select-menu-outer, .Select-menu').forEach(patchMenu);
    /* Option rows */
    root.querySelectorAll('.Select-option').forEach(function (el) {
      el.style.setProperty('color', '#dde4ed', 'important');
      el.style.removeProperty('background-color');
    });
    /* Text */
    patchText(root);
  }

  /* Run once on initial load */
  document.addEventListener('DOMContentLoaded', function () {
    patchAll(document);
  });

  /* Watch for future React re-renders (dropdown open/close, match changes) */
  var observer = new MutationObserver(function (mutations) {
    var needsPatch = false;
    mutations.forEach(function (m) {
      if (m.type === 'childList' || m.type === 'attributes') {
        needsPatch = true;
      }
    });
    if (needsPatch) patchAll(document);
  });

  /* Start observing once DOM is ready */
  function startObserver() {
    var target = document.getElementById('sidebar-body') || document.body;
    observer.observe(target, {
      childList:  true,
      subtree:    true,
      attributes: true,
      attributeFilter: ['style'],
    });
    patchAll(document);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startObserver);
  } else {
    startObserver();
  }

})();
