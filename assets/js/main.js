/* ==========================================================================
   Vellore Catering — main.js
   Version: V2  (see CHANGELOG.md)
   Progressive enhancement only: every page is readable and navigable
   without JavaScript. No external libraries, no paid APIs.
   ========================================================================== */
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  var body = doc.body;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var WA_NUMBER = body.getAttribute('data-wa') || '919940466250';

  // Path to assets/, worked out from this script's own URL (works at any folder depth)
  var scriptEl = doc.currentScript || doc.querySelector('script[src*="main.js"]');
  var ASSETS = scriptEl ? scriptEl.src.replace(/js\/main\.js.*$/, '') : 'assets/';

  window.VC_READY = true;

  function $(sel, ctx) { return (ctx || doc).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel)); }

  /* ---------------------------------------------------------------
     1. Broken remote image → local placeholder (never a blank box)
     --------------------------------------------------------------- */
  function useFallback(img) {
    if (img.dataset.fallbackApplied) return;
    img.dataset.fallbackApplied = '1';
    img.removeAttribute('srcset');
    img.src = ASSETS + 'img/fallback.svg';
  }
  $$('img').forEach(function (img) {
    if (img.complete && img.naturalWidth === 0 && img.getAttribute('src')) useFallback(img);
    img.addEventListener('error', function () { useFallback(img); });
  });

  /* ---------------------------------------------------------------
     2. Header: scrolled state
     --------------------------------------------------------------- */
  var header = $('.site-header');
  var toTop = $('.to-top');
  var ticking = false;
  function onScroll() {
    var y = window.scrollY || window.pageYOffset;
    if (header) header.classList.toggle('is-scrolled', y > 24);
    if (toTop) toTop.classList.toggle('is-visible', y > 700);
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { window.requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
  });

  /* ---------------------------------------------------------------
     3. Mobile navigation + services submenu
     --------------------------------------------------------------- */
  var toggle = $('.site-nav__toggle');
  var list = $('.site-nav__list');
  var mobileMq = window.matchMedia('(max-width: 1079px)');

  if (list) {
    $$(':scope > li', list).forEach(function (li, i) { li.style.setProperty('--i', i); });
  }

  function setNav(open) {
    if (!toggle || !list) return;
    list.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.querySelector('.visually-hidden').textContent = open ? 'Close menu' : 'Open menu';
    body.classList.toggle('nav-open', open);
    if (open) {
      var first = list.querySelector('a');
      if (first) setTimeout(function () { first.focus({ preventScroll: true }); }, 250);
    }
  }
  if (toggle && list) {
    toggle.addEventListener('click', function () {
      setNav(!list.classList.contains('is-open'));
    });
    list.addEventListener('click', function (e) {
      if (e.target.closest('a') && mobileMq.matches) setNav(false);
    });
    var onMq = function (e) { if (!e.matches) setNav(false); };
    if (mobileMq.addEventListener) mobileMq.addEventListener('change', onMq);
    else if (mobileMq.addListener) mobileMq.addListener(onMq);
  }

  $$('.sub-toggle').forEach(function (btn) {
    var li = btn.closest('.has-sub');
    btn.addEventListener('click', function () {
      var open = !li.classList.contains('is-open');
      li.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', String(open));
    });
    li.addEventListener('focusout', function (e) {
      if (!mobileMq.matches && !li.contains(e.relatedTarget)) {
        li.classList.remove('is-open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  });
  doc.addEventListener('click', function (e) {
    if (mobileMq.matches) return;
    $$('.has-sub.is-open').forEach(function (li) {
      if (!li.contains(e.target)) {
        li.classList.remove('is-open');
        li.querySelector('.sub-toggle').setAttribute('aria-expanded', 'false');
      }
    });
  });
  doc.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (list && list.classList.contains('is-open')) { setNav(false); toggle.focus(); }
    $$('.has-sub.is-open').forEach(function (li) {
      li.classList.remove('is-open');
      var b = li.querySelector('.sub-toggle');
      b.setAttribute('aria-expanded', 'false');
      b.focus();
    });
  });

  /* ---------------------------------------------------------------
     4. Reveal on scroll + counters + kolam drawing
     --------------------------------------------------------------- */
  function countUp(el) {
    var target = el.hasAttribute('data-since')
      ? new Date().getFullYear() - parseInt(el.getAttribute('data-since'), 10)
      : parseInt(el.getAttribute('data-count'), 10);
    var suffix = el.getAttribute('data-suffix') || '';
    if (isNaN(target)) return;
    if (reduceMotion) { el.textContent = target.toLocaleString('en-IN') + suffix; return; }
    var start = null;
    var dur = 1600;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased).toLocaleString('en-IN') + suffix;
      if (p < 1) window.requestAnimationFrame(step);
    }
    window.requestAnimationFrame(step);
  }

  $$('.kolam__dots circle').forEach(function (c, i) { c.style.setProperty('--i', i); });

  var observed = $$('[data-reveal], [data-count], [data-since], .kolam');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        if (el.hasAttribute('data-reveal')) el.classList.add('is-in');
        if (el.hasAttribute('data-count') || el.hasAttribute('data-since')) countUp(el);
        if (el.classList.contains('kolam')) el.classList.add('is-drawn');
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
    observed.forEach(function (el) { io.observe(el); });
  } else {
    observed.forEach(function (el) {
      el.classList.add('is-in', 'is-drawn');
      if (el.hasAttribute('data-count') || el.hasAttribute('data-since')) countUp(el);
    });
  }

  /* ---------------------------------------------------------------
     5. Hero: load sequence + background video (desktop only)
     --------------------------------------------------------------- */
  var hero = $('.hero');
  if (hero) {
    window.requestAnimationFrame(function () { hero.classList.add('is-ready'); });
    var video = $('video[data-src]', hero);
    var conn = navigator.connection || {};
    var allowVideo = video && !reduceMotion && !conn.saveData &&
      window.matchMedia('(min-width: 768px)').matches &&
      !/(^|-)2g$/.test(conn.effectiveType || '');
    if (allowVideo) {
      var startVideo = function () {
        video.src = video.getAttribute('data-src');
        video.muted = true;
        video.addEventListener('playing', function () { video.classList.add('is-playing'); }, { once: true });
        var p = video.play();
        if (p && p.catch) p.catch(function () { /* autoplay blocked: poster image stays */ });
      };
      if (doc.readyState === 'complete') setTimeout(startVideo, 400);
      else window.addEventListener('load', function () { setTimeout(startVideo, 400); });

      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            if (!video.src) return;
            if (en.isIntersecting) { var pp = video.play(); if (pp && pp.catch) pp.catch(function () {}); }
            else video.pause();
          });
        }).observe(hero);
      }
    }
  }

  /* ---------------------------------------------------------------
     6. Tabs (menu teaser) — WAI-ARIA tabs pattern
     --------------------------------------------------------------- */
  $$('[role="tablist"]').forEach(function (tablist) {
    var tabs = $$('[role="tab"]', tablist);
    function select(tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        var panel = doc.getElementById(t.getAttribute('aria-controls'));
        if (!panel) return;
        panel.hidden = !on;
        if (on) {
          panel.classList.remove('is-entering');
          void panel.offsetWidth;
          panel.classList.add('is-entering');
        }
      });
      if (focus) tab.focus();
    }
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { select(tab); });
      tab.addEventListener('keydown', function (e) {
        var next = null;
        if (e.key === 'ArrowRight') next = tabs[(i + 1) % tabs.length];
        if (e.key === 'ArrowLeft') next = tabs[(i - 1 + tabs.length) % tabs.length];
        if (e.key === 'Home') next = tabs[0];
        if (e.key === 'End') next = tabs[tabs.length - 1];
        if (next) { e.preventDefault(); select(next, true); }
      });
    });
    // no-JS: all panels visible; with JS show only the selected one
    var current = tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0] || tabs[0];
    select(current);
  });

  /* ---------------------------------------------------------------
     7. Testimonials slider
     --------------------------------------------------------------- */
  $$('.quotes').forEach(function (wrap) {
    var track = $('.quotes__track', wrap);
    var prev = $('[data-dir="prev"]', wrap);
    var next = $('[data-dir="next"]', wrap);
    if (!track) return;
    function slide(dir) {
      var card = track.firstElementChild;
      var stepX = card ? card.getBoundingClientRect().width + 24 : 300;
      var max = track.scrollWidth - track.clientWidth - 4;
      if (dir > 0 && track.scrollLeft >= max) track.scrollTo({ left: 0 });
      else track.scrollBy({ left: dir * stepX });
    }
    if (prev) prev.addEventListener('click', function () { slide(-1); });
    if (next) next.addEventListener('click', function () { slide(1); });
    if (!reduceMotion) {
      var timer = setInterval(function () { slide(1); }, 6500);
      ['pointerenter', 'focusin', 'touchstart'].forEach(function (ev) {
        wrap.addEventListener(ev, function () { clearInterval(timer); }, { passive: true });
      });
    }
  });

  /* ---------------------------------------------------------------
     8. Gallery filter + lightbox (native <dialog>)
     --------------------------------------------------------------- */
  var filterBtns = $$('[data-filter]');
  var items = $$('.gallery-item');
  filterBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var f = btn.getAttribute('data-filter');
      filterBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
      items.forEach(function (it) {
        var show = f === 'all' || (it.getAttribute('data-cat') || '').split(' ').indexOf(f) > -1;
        it.classList.toggle('is-hidden', !show);
      });
    });
  });

  var box = $('.lightbox');
  if (box && typeof box.showModal === 'function') {
    var boxImg = $('img', box);
    var boxCap = $('figcaption', box);
    var index = 0;
    var visible = function () { return items.filter(function (it) { return !it.classList.contains('is-hidden'); }); };
    var show = function (i) {
      var list2 = visible();
      if (!list2.length) return;
      index = (i + list2.length) % list2.length;
      var img = $('img', list2[index]);
      boxImg.src = img.getAttribute('data-full') || img.currentSrc || img.src;
      boxImg.alt = img.alt;
      boxCap.textContent = img.alt;
    };
    items.forEach(function (it) {
      var btn = $('button', it);
      if (!btn) return;
      btn.addEventListener('click', function () {
        show(visible().indexOf(it));
        box.showModal();
      });
    });
    $('.lightbox__close', box).addEventListener('click', function () { box.close(); });
    $('.lightbox__prev', box).addEventListener('click', function () { show(index - 1); });
    $('.lightbox__next', box).addEventListener('click', function () { show(index + 1); });
    box.addEventListener('click', function (e) { if (e.target === box) box.close(); });
    box.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') show(index + 1);
      if (e.key === 'ArrowLeft') show(index - 1);
    });
  }

  /* ---------------------------------------------------------------
     9. Menus page: highlight the section in view
     --------------------------------------------------------------- */
  var indexLinks = $$('.menu-index a');
  if (indexLinks.length && 'IntersectionObserver' in window) {
    var byId = {};
    indexLinks.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        indexLinks.forEach(function (a) { a.classList.remove('is-current'); });
        var link = byId[en.target.id];
        if (link) {
          link.classList.add('is-current');
          link.scrollIntoView({ block: 'nearest', inline: 'center', behavior: reduceMotion ? 'auto' : 'smooth' });
        }
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    Object.keys(byId).forEach(function (id) { var s = doc.getElementById(id); if (s) spy.observe(s); });
  }

  /* ---------------------------------------------------------------
     10. Enquiry forms → WhatsApp (no backend, no paid API)
     --------------------------------------------------------------- */
  function todayISO() {
    var d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 10);
  }
  function prettyDate(iso) {
    var parts = iso.split('-');
    var d = new Date(+parts[0], +parts[1] - 1, +parts[2]);
    var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    return days[d.getDay()] + ', ' + d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear();
  }
  function cleanPhone(v) {
    var digits = (v || '').replace(/\D/g, '');
    if (digits.length === 12 && digits.indexOf('91') === 0) digits = digits.slice(2);
    if (digits.length === 11 && digits.charAt(0) === '0') digits = digits.slice(1);
    return digits;
  }
  function setError(input, msg) {
    var err = doc.getElementById(input.id + '-error');
    input.setAttribute('aria-invalid', msg ? 'true' : 'false');
    if (err) err.textContent = msg || '';
  }

  $$('form[data-wa-form]').forEach(function (form) {
    var name = $('input[name="name"]', form);
    var phone = $('input[name="phone"]', form);
    var date = $('input[name="event_date"]', form);
    var status = $('.form-status', form);
    var eventType = form.getAttribute('data-event') || 'Catering';
    if (date) date.min = todayISO();

    [name, phone, date].forEach(function (input) {
      if (input) input.addEventListener('input', function () { setError(input, ''); });
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var ok = true;
      var n = (name.value || '').trim();
      var p = cleanPhone(phone.value);
      var dt = date.value;

      if (n.length < 2) { setError(name, 'Please enter your name.'); ok = false; }
      if (!/^[6-9]\d{9}$/.test(p)) { setError(phone, 'Enter a 10-digit mobile number, e.g. 98765 43210.'); ok = false; }
      if (!dt) { setError(date, 'Please choose your event date.'); ok = false; }
      else if (dt < todayISO()) { setError(date, 'The event date cannot be in the past.'); ok = false; }
      if (!ok) {
        var firstBad = $('[aria-invalid="true"]', form);
        if (firstBad) firstBad.focus();
        return;
      }

      var lines = [
        'Hello Vellore Catering,',
        'I would like a catering quote.',
        '',
        'Name: ' + n,
        'Contact number: +91 ' + p.slice(0, 5) + ' ' + p.slice(5),
        'Event date: ' + prettyDate(dt),
        'Enquiry for: ' + eventType,
        '',
        '(Sent from ' + doc.title.split('|')[0].trim() + ')'
      ];
      var url = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(lines.join('\n'));
      if (status) status.textContent = 'Opening WhatsApp with your details…';
      var win = window.open(url, '_blank');
      if (win) { win.opener = null; }
      else { window.location.href = url; }
      setTimeout(function () {
        if (status) status.textContent = 'WhatsApp opened. Tap send and we will reply shortly. Prefer a call? Dial 99404 66250.';
        form.reset();
      }, 900);
    });
  });

  /* ---------------------------------------------------------------
     10.5 V2 catalog mega-menu, filters and page motion
     --------------------------------------------------------------- */
  $$('.mega-group__toggle').forEach(function (btn) {
    var group = btn.closest('.mega-group');
    btn.addEventListener('click', function () {
      var open = !group.classList.contains('is-open');
      group.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  var megaSearch = $('[data-mega-search]');
  if (megaSearch) {
    megaSearch.addEventListener('input', function () {
      var q = (megaSearch.value || '').trim().toLowerCase();
      $$('.mega-group').forEach(function (group) {
        var links = $$('a', group);
        var visible = 0;
        links.forEach(function (a) {
          var match = !q || a.textContent.toLowerCase().indexOf(q) !== -1;
          var li = a.closest('li');
          if (li) li.hidden = !match;
          if (match) visible++;
        });
        group.hidden = visible === 0;
        if (q && visible) {
          group.classList.add('is-open');
          var b = $('.mega-group__toggle', group);
          if (b) b.setAttribute('aria-expanded', 'true');
        }
      });
    });
  }

  var catalogFilter = $('[data-catalog-filter]');
  if (catalogFilter) {
    catalogFilter.addEventListener('input', function () {
      var q = (catalogFilter.value || '').trim().toLowerCase();
      $$('.catalog-group').forEach(function (group) {
        var shown = 0;
        $$('li', group).forEach(function (li) {
          var match = !q || li.textContent.toLowerCase().indexOf(q) !== -1;
          li.hidden = !match;
          if (match) shown++;
        });
        group.hidden = shown === 0;
      });
    });
  }

  var blogFilter = $('[data-blog-search]');
  if (blogFilter) {
    blogFilter.addEventListener('input', function () {
      var q = (blogFilter.value || '').trim().toLowerCase();
      $$('.blog-index-group').forEach(function (group) {
        var shown = 0;
        $$('[data-blog-card]', group).forEach(function (card) {
          var match = !q || card.textContent.toLowerCase().indexOf(q) !== -1;
          card.hidden = !match;
          if (match) shown += 1;
        });
        group.hidden = shown === 0;
      });
    });
  }

  // V2: page clips are real stock video now — load them only on tablet/desktop
  // with no data-saver or 2G connection; phones keep the poster photo.
  var pmConn = navigator.connection || {};
  var allowPageMotion = !pmConn.saveData && !/(^|-)2g$/.test(pmConn.effectiveType || '') &&
    window.matchMedia('(min-width: 768px)').matches;
  $$('.page-motion[data-src]').forEach(function (video) {
    if (!allowPageMotion) return;
    function loadAndPlay() {
      if (!video.src) video.src = video.getAttribute('data-src');
      var p = video.play();
      if (p && p.catch) p.catch(function () {});
    }
    if (reduceMotion) return;
    if ('IntersectionObserver' in window) {
      var vio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) loadAndPlay();
          else if (video.src) video.pause();
        });
      }, { rootMargin: '200px 0px' });
      vio.observe(video);
    } else loadAndPlay();
  });

  /* ---------------------------------------------------------------
     11. Footer year
     --------------------------------------------------------------- */
  $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
