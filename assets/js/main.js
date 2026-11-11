// Footy Daily Network — interactions
(() => {
  // Mobile menu
  const btn = document.querySelector('.menu-btn');
  const nav = document.querySelector('.nav');
  if (btn && nav) {
    btn.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open);
    });
  }

  // Old ?league= links -> the league's own page
  const lg = new URLSearchParams(location.search).get('league');
  if (lg) location.replace('/leagues/' + lg.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '/');

  // Story search
  const list = document.querySelector('[data-story-list]');
  const search = document.querySelector('[data-search]');
  if (list && search) {
    const cards = [...list.querySelectorAll('[data-text]')];
    const empty = document.querySelector('[data-empty]');
    search.addEventListener('input', () => {
      const q = search.value.trim().toLowerCase();
      let shown = 0;
      cards.forEach(c => { c.hidden = !!q && !c.dataset.text.includes(q); if (!c.hidden) shown++; });
      if (empty) empty.hidden = shown > 0;
    });
  }

  // Lightbox for any [data-lightbox] group
  const groups = {};
  document.querySelectorAll('[data-lightbox]').forEach(a => {
    const g = a.dataset.lightbox;
    (groups[g] ||= []).push(a);
  });
  if (Object.keys(groups).length) {
    const lb = document.createElement('div');
    lb.className = 'lightbox';
    lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true');
    lb.innerHTML = `
      <img alt="">
      <button class="lb-btn lb-close" aria-label="Close">✕</button>
      <button class="lb-btn lb-prev" aria-label="Previous photo">‹</button>
      <button class="lb-btn lb-next" aria-label="Next photo">›</button>
      <div class="lb-count"></div>`;
    document.body.appendChild(lb);
    const img = lb.querySelector('img');
    const count = lb.querySelector('.lb-count');
    let cur = [], i = 0;
    const show = () => {
      img.src = cur[i].href;
      img.alt = cur[i].querySelector('img')?.alt || '';
      count.textContent = `${i + 1} / ${cur.length}`;
      const nxt = cur[(i + 1) % cur.length]; if (nxt) new Image().src = nxt.href;
    };
    const open = (g, idx) => { cur = groups[g]; i = idx; show(); lb.classList.add('open'); document.body.style.overflow = 'hidden'; };
    const close = () => { lb.classList.remove('open'); document.body.style.overflow = ''; img.src = ''; };
    const step = d => { i = (i + d + cur.length) % cur.length; show(); };
    Object.entries(groups).forEach(([g, items]) => items.forEach((a, idx) =>
      a.addEventListener('click', e => { e.preventDefault(); open(g, idx); })));
    lb.querySelector('.lb-close').onclick = close;
    lb.querySelector('.lb-prev').onclick = e => { e.stopPropagation(); step(-1); };
    lb.querySelector('.lb-next').onclick = e => { e.stopPropagation(); step(1); };
    lb.addEventListener('click', e => { if (e.target === lb) close(); });
    document.addEventListener('keydown', e => {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowRight') step(1);
      if (e.key === 'ArrowLeft') step(-1);
    });
    let x0 = null;
    lb.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', e => {
      if (x0 === null) return;
      const dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
      x0 = null;
    });
  }

  // Copy link
  document.querySelectorAll('[data-copy]').forEach(b => b.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(location.href); b.textContent = 'Copied!'; }
    catch { b.textContent = location.href; }
    setTimeout(() => { b.textContent = 'Copy link'; }, 2000);
  }));
})();
