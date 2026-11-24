/* A2F Concept 2 — stories, reels, swipe deck, DMs, pull-up sheet. No libraries. */
(() => {
  const RM = window.matchMedia('(prefers-reduced-motion: reduce)');
  const reduced = () => RM.matches;
  if (!reduced()) document.documentElement.classList.add('motion');
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const ICON = 'assets/brand/White_Icon.png';

  /* ---------- toast ---------- */
  const toast = (msg) => {
    let t = $('.toast'); if (!t) { t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role','status'); document.body.appendChild(t); }
    t.textContent = msg; t.classList.add('on'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('on'), 2200);
  };

  /* ---------- reveal on scroll ---------- */
  if (!reduced() && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), {rootMargin:'0px 0px -8% 0px'});
    $$('.rv').forEach(el => io.observe(el));
  } else $$('.rv').forEach(el => el.classList.add('in'));

  /* ---------- story player ---------- */
  const svgPause = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>';
  const svgPlay = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5l12 7-12 7z"/></svg>';
  const svgX = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';

  function slideHTML(s, i, inline) {
    const media = s.video
      ? `<video src="${s.video}" poster="${s.poster || ''}" muted playsinline preload="${i === 0 ? 'auto' : 'none'}" aria-label="${esc(s.alt)}"></video>`
      : `<img src="${s.src}" alt="${esc(s.alt)}" ${i > 1 ? 'loading="lazy"' : ''} style="object-position:${s.pos || '50% 50%'}">`;
    const stickers = (s.stickers || []).map(k => `<span class="sticker ${k.c || ''}" style="left:${k.x};top:${k.y};--rot:${k.r || '-6deg'}" aria-hidden="true">${k.t}</span>`).join('');
    const poll = s.poll ? `<div class="poll" role="group" aria-label="${esc(s.poll.q)}"><b>${s.poll.q}</b><div class="opts">${s.poll.o.map(o => `<button type="button" aria-pressed="false">${o}</button>`).join('')}</div><div class="res" aria-live="polite"></div></div>` : '';
    const acts = (s.acts || []).map(a => a.href
      ? `<a class="pill ${a.c || 'y'}" href="${a.href}">${a.l}</a>`
      : `<button type="button" class="pill ${a.c || 'y'}" data-act="${a.act}">${a.l}</button>`).join('');
    const H = inline && i === 0 ? 'h2' : 'h3';
    return `<div class="slide" aria-hidden="true">${media}${stickers}${poll}
      <div class="cap">${s.k ? `<span class="k">${s.k}</span>` : ''}<${H}>${s.t}</${H}>${s.p ? `<p>${s.p}</p>` : ''}${acts ? `<div class="acts">${acts}</div>` : ''}</div></div>`;
  }

  class Story {
    constructor(root, slides, opts = {}) {
      this.root = root; this.slides = slides; this.o = opts; this.i = 0; this.t = 0; this.playing = false; this.held = false;
      root.classList.add('story');
      root.setAttribute('role', 'region'); root.setAttribute('aria-roledescription', 'story'); root.setAttribute('aria-label', opts.label || 'Story');
      root.innerHTML = `<div class="bars">${slides.map(() => '<i><b></b></i>').join('')}</div>
        <div class="head"><img src="${ICON}" alt=""><span>${esc(opts.name || 'acts2fellowship')}</span><span class="ago">${esc(opts.ago || '')}</span>
          <span class="ctrl"><button type="button" class="pp" aria-label="Pause">${svgPause}</button>${opts.closable ? `<button type="button" class="cl" aria-label="Close">${svgX}</button>` : ''}</span></div>
        <div class="slides">${slides.map((s, i) => slideHTML(s, i, opts.inline)).join('')}</div>
        <button type="button" class="tap prev" aria-label="Previous"></button><button type="button" class="tap next" aria-label="Next"></button>
        <div class="sr" aria-live="polite"></div>`;
      this.els = $$('.slide', root); this.bars = $$('.bars i', root); this.live = $('.sr', root); this.pp = $('.pp', root);
      $('.tap.prev', root).addEventListener('click', () => !this.wasHold && this.go(this.i - 1));
      $('.tap.next', root).addEventListener('click', () => !this.wasHold && this.go(this.i + 1));
      this.pp.addEventListener('click', () => this.playing ? this.pause(true) : this.play());
      const cl = $('.cl', root); if (cl) cl.addEventListener('click', () => opts.onClose && opts.onClose());
      // hold to pause
      root.addEventListener('pointerdown', e => {
        if (e.target.closest('.acts, .poll, .ctrl')) return;
        this.wasHold = false; clearTimeout(this.hT);
        this.hT = setTimeout(() => { if (this.playing) { this.held = true; this.wasHold = true; this.pause(); } }, 220);
        this.sx = e.clientX; this.sy = e.clientY;
      });
      const up = e => { clearTimeout(this.hT); if (this.held) { this.held = false; this.play(); }
        if (opts.closable && e && this.sy != null && e.clientY - this.sy > 90 && Math.abs(e.clientX - this.sx) < 60) opts.onClose && opts.onClose();
        this.sy = null; };
      root.addEventListener('pointerup', up); root.addEventListener('pointercancel', () => up());
      root.addEventListener('keydown', e => {
        if (e.key === 'ArrowRight') { this.go(this.i + 1); e.preventDefault(); }
        if (e.key === 'ArrowLeft') { this.go(this.i - 1); e.preventDefault(); }
      });
      // in-slide actions
      root.addEventListener('click', e => {
        const b = e.target.closest('[data-act]'); if (b) { this.pause(true); act(b.dataset.act); }
        const pb = e.target.closest('.poll button'); if (pb) {
          const poll = pb.closest('.poll'); $$('button', poll).forEach(x => x.setAttribute('aria-pressed', x === pb ? 'true' : 'false'));
          const s = this.slides[this.i]; $('.res', poll).textContent = s.poll.r || 'noted!';
        }
      });
      this.show(0);
    }
    show(i) {
      this.els.forEach((el, k) => { const on = k === i; el.classList.toggle('on', on); el.setAttribute('aria-hidden', on ? 'false' : 'true');
        $$('a,button', el).forEach(x => x.tabIndex = on ? 0 : -1);
        const v = $('video', el); if (v) { if (on) { v.currentTime = 0; if (this.playing) v.play().catch(() => {}); } else v.pause(); } });
      this.bars.forEach((b, k) => { b.classList.toggle('done', k < i); $('b', b).style.width = k < i ? '100%' : '0%'; });
      const s = this.slides[i]; this.live.textContent = `${i + 1} of ${this.slides.length}: ${s.t.replace(/<[^>]+>/g, '')}`;
      // preload next
      const nx = this.els[i + 1]; if (nx) { const v = $('video', nx); if (v && v.preload === 'none') v.preload = 'auto'; }
    }
    dur() { const s = this.slides[this.i]; return (s.d || (s.video ? 7 : 5.2)) * 1000; }
    go(i) {
      if (i < 0) i = 0;
      if (i >= this.slides.length) { if (this.o.onEnd) return this.o.onEnd(this); i = 0; }
      this.i = i; this.t = 0; this.show(i);
    }
    play() {
      if (this.playing) return; this.playing = true; this.pp.innerHTML = svgPause; this.pp.setAttribute('aria-label', 'Pause');
      const v = $('video', this.els[this.i]); if (v) v.play().catch(() => {});
      let last = performance.now();
      const step = now => {
        if (!this.playing) return;
        this.t += now - last; last = now;
        const p = Math.min(1, this.t / this.dur()); $('b', this.bars[this.i]).style.width = (p * 100) + '%';
        if (p >= 1) this.go(this.i + 1);
        this.raf = requestAnimationFrame(step);
      };
      this.raf = requestAnimationFrame(step);
    }
    pause(user) {
      this.playing = false; cancelAnimationFrame(this.raf); this.pp.innerHTML = svgPlay; this.pp.setAttribute('aria-label', 'Play');
      const v = $('video', this.els[this.i]); if (v) v.pause(); if (user) this.userPaused = true;
    }
  }

  /* ---------- fullscreen viewer ---------- */
  let viewer, vStory, lastFocus;
  function openStory(key) {
    const group = (window.STORIES || {})[key]; if (!group) return;
    lastFocus = document.activeElement;
    if (!viewer) { viewer = document.createElement('div'); viewer.className = 'viewer'; viewer.setAttribute('role', 'dialog'); viewer.setAttribute('aria-modal', 'true');
      viewer.addEventListener('click', e => { if (e.target === viewer) closeStory(); }); document.body.appendChild(viewer); }
    viewer.innerHTML = '<div tabindex="-1"></div>'; const host = viewer.firstChild;
    viewer.setAttribute('aria-label', group.name);
    vStory = new Story(host, group.slides, { name: group.name, ago: group.ago || '', closable: true, label: group.name, onClose: closeStory, onEnd: closeStory });
    viewer.classList.add('open'); document.body.classList.add('lock'); host.focus();
    if (!reduced()) vStory.play();
    $$(`.ring[data-story="${key}"]`).forEach(r => r.classList.add('seen'));
    if (hero) hero.pause();
  }
  function closeStory() {
    if (!viewer) return; if (vStory) vStory.pause(); viewer.classList.remove('open'); viewer.innerHTML = ''; document.body.classList.remove('lock');
    if (lastFocus) lastFocus.focus();
  }
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { if (viewer && viewer.classList.contains('open')) closeStory(); closeSheet(); closeLB(); } });
  document.addEventListener('click', e => { const r = e.target.closest('[data-story]'); if (r && !r.matches('a[href]')) { e.preventDefault(); openStory(r.dataset.story); } });

  /* ---------- inline hero story ---------- */
  let hero;
  const heroEl = $('#hero-story');
  if (heroEl && window.STORIES && STORIES.intro) {
    hero = new Story(heroEl, STORIES.intro.slides, { name: 'acts2fellowship', ago: 'pinned', inline: true, label: 'Intro story: tap the right side to go forward' });
    heroEl.tabIndex = 0;
    if (!reduced() && 'IntersectionObserver' in window) {
      new IntersectionObserver(([e]) => { if (e.isIntersecting && !hero.userPaused && !(viewer && viewer.classList.contains('open'))) hero.play(); else hero.pause(); }, {threshold:.45}).observe(heroEl);
    } else {
      const h = document.createElement('span'); h.className = 'hint'; h.textContent = 'tap →'; heroEl.appendChild(h);
    }
  }

  /* ---------- reels ---------- */
  const heart = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M12 20s-7-4.4-9.2-8.6C1.2 8.1 3.3 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.7 0 5.8 3.6 4.2 6.9C19 15.6 12 20 12 20z"/></svg>';
  const share = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/></svg>';
  $$('.reel[data-src]').forEach((r, n) => {
    const title = r.dataset.title, sub = r.dataset.sub || '', chip = r.dataset.chip || '', chipc = r.dataset.chipc || '';
    r.innerHTML = `<video src="${r.dataset.src}" poster="${r.dataset.poster}" muted loop playsinline preload="none" aria-label="${esc(r.dataset.alt || title)}"></video>
      ${chip ? `<span class="chip ${chipc}">${chip}</span>` : ''}
      <button type="button" class="playbtn" aria-label="Play or pause: ${esc(title)}"><span class="ic">${svgPlay.replace('20','30').replace('20','30')}</span></button>
      <div class="meta"><b>${title}</b><span>${sub}</span></div>
      <div class="side"><button type="button" class="like" aria-pressed="false" aria-label="Like">${heart}</button><small class="lc"></small>
        <button type="button" class="shr" aria-label="Share">${share}</button></div>`;
    const v = $('video', r); r.classList.add('paused');
    const setP = () => r.classList.toggle('paused', v.paused);
    v.addEventListener('play', setP); v.addEventListener('pause', setP);
    let lastTap = 0;
    $('.playbtn', r).addEventListener('click', () => {
      const now = Date.now();
      if (now - lastTap < 300) { like(true); lastTap = 0; return; }
      lastTap = now;
      setTimeout(() => { if (lastTap && Date.now() - lastTap >= 290) { r.dataset.user = '1'; v.paused ? v.play().catch(() => {}) : v.pause(); lastTap = 0; } }, 300);
    });
    const lb = $('.like', r);
    function like(force) {
      const on = force ? true : lb.getAttribute('aria-pressed') !== 'true';
      lb.setAttribute('aria-pressed', on); $('.lc', r).textContent = on ? '1' : '';
      if (on && !reduced()) { const b = document.createElement('div'); b.className = 'burst'; b.innerHTML = heart.replace(/width="22" height="22"/, 'width="90" height="90"').replace('fill="none"', 'fill="#ff5a6a"').replace('stroke="currentColor"', 'stroke="#ff5a6a"'); r.appendChild(b); setTimeout(() => b.remove(), 900); }
    }
    lb.addEventListener('click', () => like());
    $('.shr', r).addEventListener('click', () => shareIt(document.title, title));
    r._v = v;
  });
  if (!reduced() && 'IntersectionObserver' in window) {
    const rio = new IntersectionObserver(es => es.forEach(e => { const v = e.target._v; if (!v) return;
      if (e.isIntersecting && e.intersectionRatio > .6) { if (v.preload === 'none') v.preload = 'auto'; if (!e.target.dataset.user) v.play().catch(() => {}); }
      else v.pause(); }), {threshold:[0, .6, 1]});
    $$('.reel[data-src]').forEach(r => rio.observe(r));
  }

  /* ---------- share / sheet / calendar ---------- */
  async function shareIt(title, text) {
    const url = location.href.split('#')[0];
    if (navigator.share) { try { await navigator.share({ title, text, url }); } catch (_) {} return; }
    try { await navigator.clipboard.writeText(`${text} ${url}`); toast('link copied, send it to a friend'); } catch (_) { toast(url); }
  }
  function ics() {
    // next Sunday 11:30 local (America/New_York), weekly
    const d = new Date(); const add = (7 - d.getDay()) % 7 || 7; d.setDate(d.getDate() + (d.getDay() === 0 && d.getHours() < 11 ? 0 : add));
    const p = n => String(n).padStart(2, '0'); const ymd = `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`;
    const body = ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//A2F//Concept2//EN','BEGIN:VEVENT',`UID:a2f-sunday-${ymd}@acts2fellowship`,
      `DTSTAMP:${new Date().toISOString().replace(/[-:]/g,'').split('.')[0]}Z`,
      `DTSTART;TZID=America/New_York:${ymd}T113000`, `DTEND;TZID=America/New_York:${ymd}T133000`, 'RRULE:FREQ=WEEKLY;BYDAY=SU',
      'SUMMARY:A2F Sunday Service (UNC)', 'LOCATION:211 W Cameron Ave\\, Chapel Hill\\, NC',
      'DESCRIPTION:Bible teaching\\, prayer\\, and time to connect. Food provided. Questions welcome.', 'END:VEVENT','END:VCALENDAR'].join('\r\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([body], {type:'text/calendar'})); a.download = 'a2f-sunday.ics'; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000); toast('added, see you Sunday');
  }
  let sheet, sheetBg;
  function openSheet(tab) {
    sheet = sheet || $('#pullup'); sheetBg = sheetBg || $('#pullup-bg'); if (!sheet) return;
    lastFocus = document.activeElement;
    sheet.hidden = false; sheetBg.hidden = false; requestAnimationFrame(() => { sheet.classList.add('open'); sheetBg.classList.add('open'); });
    if (tab) setSeg(tab);
    setTimeout(() => $('h2', sheet).focus(), 50);
    if (hero) hero.pause();
  }
  function closeSheet() {
    if (!sheet || !sheet.classList.contains('open')) return;
    sheet.classList.remove('open'); sheetBg.classList.remove('open');
    setTimeout(() => { sheet.hidden = true; sheetBg.hidden = true; }, reduced() ? 0 : 320);
    if (lastFocus) lastFocus.focus();
  }
  function setSeg(which) {
    $$('#pullup .seg button').forEach(b => b.setAttribute('aria-selected', b.dataset.seg === which ? 'true' : 'false'));
    $$('#pullup [data-pane]').forEach(p => p.hidden = p.dataset.pane !== which);
  }
  document.addEventListener('click', e => {
    const s = e.target.closest('[data-seg]'); if (s) setSeg(s.dataset.seg);
    if (e.target.closest('#pullup-bg, #pullup .x')) closeSheet();
    const a = e.target.closest('[data-act]'); if (a && !a.closest('.story')) { e.preventDefault(); act(a.dataset.act, a); }
  });
  function act(name, el) {
    if (name === 'pullup') openSheet(document.body.classList.contains('ncsu') ? 'ncsu' : 'unc');
    if (name === 'pullup-ncsu') openSheet('ncsu');
    if (name === 'ics') ics();
    if (name === 'share') shareIt('Acts2Fellowship', 'pull up with me this Sunday? 11:30 at 211 W Cameron');
    if (name === 'campus') { closeStory(); const t = $('#campus'); if (t) t.scrollIntoView({behavior: reduced() ? 'auto' : 'smooth'}); }
    if (name === 'close') closeStory();
  }
  window.A2F = { openSheet, openStory };

  /* ---------- swipe deck ---------- */
  const deck = $('#deck');
  if (deck) {
    const picked = $('#picked');
    const top = () => $$('.vcard', deck).pop();
    const fling = (card, dir) => {
      if (!card) return;
      const x = dir > 0 ? 1 : -1;
      card.style.transform = `translate(${x * 140}%, -4%) rotate(${x * 22}deg)`; card.style.opacity = '0';
      if (dir > 0) { const t = document.createElement('span'); t.textContent = '✓ ' + card.dataset.name; picked.appendChild(t); }
      setTimeout(() => { card.remove(); if (!top()) $('.deck-done', deck).hidden = false; }, reduced() ? 0 : 320);
      const live = $('#deck-live'); if (live) live.textContent = dir > 0 ? `${card.dataset.name}: that's me` : `${card.dataset.name}: skipped`;
    };
    $('#deck-yes').addEventListener('click', () => fling(top(), 1));
    $('#deck-no').addEventListener('click', () => fling(top(), -1));
    $('#deck-again') && $('#deck-again').addEventListener('click', () => location.reload());
    deck.addEventListener('pointerdown', e => {
      const c = e.target.closest('.vcard'); if (!c || c !== top()) return;
      c.setPointerCapture(e.pointerId); const sx = e.clientX, sy = e.clientY; c.style.transition = 'none';
      const yes = $('.stamp.yes', c), no = $('.stamp.no', c);
      const mv = ev => { const dx = ev.clientX - sx, dy = ev.clientY - sy; c.style.transform = `translate(${dx}px, ${dy * .3}px) rotate(${dx / 14}deg)`;
        yes.style.opacity = Math.max(0, Math.min(1, dx / 90)); no.style.opacity = Math.max(0, Math.min(1, -dx / 90)); };
      const upf = ev => { c.removeEventListener('pointermove', mv); c.removeEventListener('pointerup', upf); c.removeEventListener('pointercancel', upf);
        c.style.transition = ''; const dx = ev.clientX - sx;
        if (Math.abs(dx) > 100) fling(c, dx); else { c.style.transform = ''; yes.style.opacity = 0; no.style.opacity = 0; } };
      c.addEventListener('pointermove', mv); c.addEventListener('pointerup', upf); c.addEventListener('pointercancel', upf);
    });
    deck.addEventListener('keydown', e => { if (e.key === 'ArrowRight') fling(top(), 1); if (e.key === 'ArrowLeft') fling(top(), -1); });
  }

  /* ---------- feed lightbox ---------- */
  let lb, lbItems = [], lbI = 0;
  function closeLB() { if (lb && lb.classList.contains('open')) { lb.classList.remove('open'); document.body.classList.remove('lock'); if (lastFocus) lastFocus.focus(); } }
  function showLB() { const it = lbItems[lbI]; const img = $('img', it); $('img', lb).src = img.src; $('img', lb).alt = img.alt; $('p', lb).textContent = it.dataset.cap || img.alt; }
  $$('.feed').forEach(f => f.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    lbItems = $$('button', f); lbI = lbItems.indexOf(b); lastFocus = b;
    if (!lb) { lb = document.createElement('div'); lb.className = 'lightbox'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-modal', 'true'); lb.setAttribute('aria-label', 'Photo');
      lb.innerHTML = '<button class="x" type="button" aria-label="Close">✕</button><button class="nav p" type="button" aria-label="Previous photo">‹</button><img alt=""><p></p><button class="nav n" type="button" aria-label="Next photo">›</button>';
      lb.addEventListener('click', ev => { if (ev.target === lb || ev.target.closest('.x')) closeLB();
        if (ev.target.closest('.nav.p')) { lbI = (lbI - 1 + lbItems.length) % lbItems.length; showLB(); }
        if (ev.target.closest('.nav.n')) { lbI = (lbI + 1) % lbItems.length; showLB(); } });
      lb.addEventListener('keydown', ev => { if (ev.key === 'ArrowRight') { lbI = (lbI + 1) % lbItems.length; showLB(); } if (ev.key === 'ArrowLeft') { lbI = (lbI - 1 + lbItems.length) % lbItems.length; showLB(); } });
      document.body.appendChild(lb); }
    showLB(); lb.classList.add('open'); document.body.classList.add('lock'); $('.x', lb).focus();
  }));

  /* ---------- DM FAQ ---------- */
  const dm = $('#dm');
  if (dm) {
    const log = $('.log', dm);
    const add = (cls, html) => { const b = document.createElement('div'); b.className = 'bub ' + cls; b.innerHTML = html; log.appendChild(b); log.scrollTop = log.scrollHeight; return b; };
    $$('.qs button', dm).forEach(q => q.addEventListener('click', () => {
      q.disabled = true; add('me', esc(q.textContent));
      if (reduced()) { add('them', q.dataset.a); return; }
      const t = add('them typing', '<i></i><i></i><i></i>'); t.setAttribute('aria-label', 'typing');
      setTimeout(() => { t.className = 'bub them'; t.removeAttribute('aria-label'); t.innerHTML = q.dataset.a; log.scrollTop = log.scrollHeight; }, 750);
    }));
  }

  /* ---------- campus tabs ---------- */
  $$('.tabs').forEach(tabs => {
    const btns = $$('[role="tab"]', tabs);
    const sel = b => { btns.forEach(x => { const on = x === b; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; $('#' + x.getAttribute('aria-controls')).hidden = !on; }); };
    btns.forEach((b, i) => { b.addEventListener('click', () => sel(b));
      b.addEventListener('keydown', e => { if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { const n = btns[(i + (e.key === 'ArrowRight' ? 1 : btns.length - 1)) % btns.length]; sel(n); n.focus(); } }); });
  });
})();
