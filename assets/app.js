(() => {
  const PAGE = 30;
  const USED_KEY = 'sbv-used-v1';
  const $ = (s) => document.querySelector(s);

  const state = { batches: [], items: [], batch: 'all', scene: 'all', q: '', unused: false, used: false, limit: PAGE, suggest: null };

  // ---------- storage (fail-safe) ----------
  let used = {};
  try { used = JSON.parse(localStorage.getItem(USED_KEY) || '{}') || {}; } catch (e) { used = {}; }
  const saveUsed = () => { try { localStorage.setItem(USED_KEY, JSON.stringify(used)); } catch (e) {} };

  // ---------- helpers ----------
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pad = (n) => String(n).padStart(2, '0');
  const toast = (msg) => {
    const t = $('#toast'); t.textContent = msg; t.classList.add('show');
    clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove('show'), 1600);
  };
  async function copy(text, label) {
    try { await navigator.clipboard.writeText(text); }
    catch (e) {
      const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove();
    }
    toast(`✓ ${label} disalin`);
  }
  // seeded RNG untuk cadangan harian (sama sepanjang hari)
  function seeded(seed) { let h = 2166136261; for (const c of seed) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return () => { h += 0x6D2B79F5; let t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const todayKey = () => new Date().toISOString().slice(0, 10);

  // ---------- data ----------
  async function load() {
    const manifest = await fetch('data/manifest.json', { cache: 'no-cache' }).then((r) => r.json());
    const batches = await Promise.all(manifest.batches.map((b) => fetch('data/' + b.file, { cache: 'no-cache' }).then((r) => r.json())));
    state.batches = batches;
    for (const b of batches) {
      for (const s of b.sets) {
        for (const sc of s.scenes) {
          const isBoard = sc.panels && sc.panels.length > 0;
          const beats = isBoard ? sc.panels.map((p) => ({ t: p.time, a: p.action })) : sc.timeline.map((t) => ({ t: t.time, a: t.action }));
          const item = {
            id: `${b.id}:s${pad(s.set)}-sc${sc.scene}`,
            batch: b, set: s, sc, isBoard, beats,
            tags: [...(b.tags || []), `scene-${sc.scene}`],
          };
          item.hay = [s.title, sc.heading, s.gaya, s.ayat, b.label, ...item.tags, ...sc.dialog.map((d) => d.who + ' ' + d.line), ...beats.map((x) => x.a)].join(' ').toLowerCase();
          state.items.push(item);
        }
      }
    }
    renderChips(); render();
  }

  // ---------- filters ----------
  function filtered() {
    const words = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    return state.items.filter((it) =>
      (state.batch === 'all' || it.batch.id === state.batch) &&
      (state.scene === 'all' || it.sc.scene === +state.scene) &&
      (!state.unused || !used[it.id]) &&
      (!state.used || used[it.id]) &&
      words.every((w) => it.hay.includes(w)));
  }

  function renderChips() {
    const bc = $('#batchChips');
    const chip = (key, label, on) => `<button class="chip${on ? ' on' : ''}" data-k="${esc(key)}">${esc(label)}</button>`;
    bc.innerHTML = chip('all', 'Semua', state.batch === 'all') +
      state.batches.map((b) => chip(b.id, `${b.label} (${state.items.filter((i) => i.batch.id === b.id).length})`, state.batch === b.id)).join('');
    const scenes = [...new Set(state.items.map((i) => i.sc.scene))].sort();
    $('#sceneChips').innerHTML = chip('all', 'Semua scene', state.scene === 'all') +
      scenes.map((n) => chip(n, `Scene ${n}`, String(state.scene) === String(n))).join('');
  }

  // ---------- render ----------
  function cardHTML(it) {
    const { set: s, sc, batch: b } = it;
    const isUsed = !!used[it.id];
    const unit = it.isBoard ? `${sc.panels.length} panel` : `${it.beats.length} babak`;
    const broll = b.kind === 'broll';
    const where = broll ? `Klip ${pad(s.set)}` : `Set ${pad(s.set)} · Scene ${sc.scene}`;
    const title = broll ? `Klip ${pad(s.set)}: ${esc(s.title)}` : `Set ${pad(s.set)} #${sc.scene}: ${esc(s.title)}`;
    const box = sc.dialog.length
      ? `<div class="box"><div class="box-h">Dialog</div><ol>${sc.dialog.map((d) => `<li><div>${d.who && d.who !== 'Hos' ? `<b>${esc(d.who)}:</b> ` : ''}${esc(d.line)}</div></li>`).join('')}</ol></div>`
      : s.ayat ? `<div class="box"><div class="box-h">Guna untuk ayat</div><div>${esc(s.ayat)}</div></div>` : '';
    return `<article class="card${isUsed ? ' used' : ''}" data-id="${esc(it.id)}">
      <div class="badges"><span class="badge gold">${esc(b.label)}</span><span class="badge">${where} · ${unit}</span>${isUsed ? '<span class="badge ok">✓ dah guna</span>' : ''}</div>
      <h3 data-act="open">${title}</h3>
      <div class="sub">${esc(sc.heading)}${s.gaya ? ' • ' + esc(s.gaya) : ''} • ${s.duration || 10} saat • 9:16</div>
      ${box}
      <div class="tags">${it.tags.map((t) => `<span class="tag">#${esc(t)}</span>`).join('')}</div>
      <details class="expand"><summary>▼ Lihat ${unit}</summary><ol class="steps">${it.beats.map((x) => `<li><span>${esc(x.t)}</span>${esc(x.a)}</li>`).join('')}</ol></details>
      <div class="actions">
        <button class="btn btn-gold" data-act="img">🎨 ${it.isBoard ? 'Prompt Storyboard' : 'Prompt Image'}</button>
        <button class="btn btn-blue" data-act="vid">🎬 Prompt Video</button>
        <button class="btn btn-sm" data-act="sum">📝 Ringkasan ${it.isBoard ? 'Panel' : 'Babak'}</button>
        <button class="btn btn-sm${isUsed ? ' btn-used' : ''}" data-act="used">${isUsed ? '↺ Tanda belum guna' : '✓ Dah guna'}</button>
      </div>
    </article>`;
  }

  function render() {
    let list;
    if (state.suggest) {
      list = state.suggest.map((id) => state.items.find((i) => i.id === id)).filter(Boolean);
      $('#suggestBox').hidden = false;
      $('#suggestBox').innerHTML = `<span>✨ <b>Cadangan hari ni</b> — ${list.length} scene yang belum guna.</span><button class="btn btn-ghost" data-act="closeSuggest">Tutup cadangan</button>`;
    } else {
      list = filtered();
      $('#suggestBox').hidden = true;
    }
    const shown = state.suggest ? list : list.slice(0, state.limit);
    $('#grid').innerHTML = shown.length ? shown.map(cardHTML).join('') : '<p style="color:var(--muted)">Tiada padanan. Cuba kata kunci lain.</p>';
    $('#btnMore').hidden = state.suggest || shown.length >= list.length;
    $('#showing').textContent = `Papar ${shown.length} dari ${list.length}`;

    const total = state.items.length;
    const u = state.items.filter((i) => used[i.id]).length;
    const pct = total ? Math.round((u / total) * 100) : 0;
    $('#progText').textContent = `${u} / ${total} (${pct}%)`;
    $('#progBar').style.width = pct + '%';
    $('#usedCount').textContent = `${u} / ${total} dah guna`;
  }

  // ---------- text builders ----------
  const summary = (it) => {
    const { set: s, sc } = it;
    return [
      it.batch.kind === 'broll' ? `KLIP ${pad(s.set)}: ${s.title}` : `SET ${pad(s.set)} · SCENE ${sc.scene}: ${s.title}`,
      `${sc.heading}${s.gaya ? ' | ' + s.gaya : ''}`,
      '',
      ...(sc.dialog.length
        ? ['DIALOG:', ...sc.dialog.map((d, i) => `${i + 1}. ${d.who && d.who !== 'Hos' ? d.who + ': ' : ''}${d.line}`), '']
        : s.ayat ? ['GUNA UNTUK AYAT:', s.ayat, ''] : []),
      it.isBoard ? 'PANEL:' : 'BABAK:',
      ...it.beats.map((x, i) => `${i + 1}. [${x.t}] ${x.a}`),
    ].join('\n');
  };

  function openModal(it) {
    const { set: s, sc, batch: b } = it;
    $('#mTitle').textContent = b.kind === 'broll' ? `Klip ${pad(s.set)}: ${s.title}` : `Set ${pad(s.set)} · Scene ${sc.scene}: ${s.title}`;
    const siblings = s.scenes.map((x) => {
      const id = `${b.id}:s${pad(s.set)}-sc${x.scene}`;
      return `<button class="chip${x.scene === sc.scene ? ' on' : ''}" data-open="${esc(id)}">Scene ${x.scene}</button>`;
    }).join('');
    $('#mBody').innerHTML = `
      <div class="chips" style="margin:0">${siblings}</div>
      <div class="sub" style="margin:0">${esc(s.arc)}</div>
      <div class="pblock"><h4><span>🎨 ${esc(sc.imageLabel)}</span><button class="btn btn-gold" data-act="img">Salin</button></h4><pre>${esc(sc.imagePrompt)}</pre></div>
      <div class="pblock"><h4><span>🎬 ${esc(sc.videoLabel)}</span><button class="btn btn-blue" data-act="vid">Salin</button></h4><pre>${esc(sc.videoPrompt)}</pre></div>`;
    $('#mBody').dataset.id = it.id;
    const m = $('#modal'); if (!m.open) m.showModal(); m.scrollTop = 0;
  }

  function openGuide() {
    const bs = state.batch === 'all' ? state.batches : state.batches.filter((b) => b.id === state.batch);
    $('#mTitle').textContent = '📘 Panduan batch';
    $('#mBody').innerHTML = bs.map((b) => `<div class="guide"><div class="badges"><span class="badge gold">${esc(b.label)}</span><span class="badge">${esc(b.source || '')}</span></div>
      <h3 style="color:var(--text)">${esc(b.title)}</h3>
      ${b.guide.map((g) => g.h ? `<h3>${esc(g.h)}</h3>` : g.items ? `<ul>${g.items.map((i) => `<li>${esc(i)}</li>`).join('')}</ul>` : `<p>${esc(g.p)}</p>`).join('')}</div>`).join('<hr style="border-color:var(--line)">');
    delete $('#mBody').dataset.id;
    $('#modal').showModal();
  }

  const byId = (id) => state.items.find((i) => i.id === id);

  function act(action, it) {
    if (!it) return;
    if (action === 'img') copy(it.sc.imagePrompt, it.isBoard ? 'Prompt Storyboard' : 'Prompt Image');
    else if (action === 'vid') copy(it.sc.videoPrompt, 'Prompt Video');
    else if (action === 'sum') copy(summary(it), 'Ringkasan');
    else if (action === 'open') openModal(it);
    else if (action === 'used') {
      if (used[it.id]) delete used[it.id]; else used[it.id] = todayKey();
      saveUsed(); render(); toast(used[it.id] ? '✓ Ditanda dah guna' : 'Ditanda belum guna');
    }
  }

  // ---------- events ----------
  $('#grid').addEventListener('click', (e) => {
    const el = e.target.closest('[data-act]'); if (!el) return;
    act(el.dataset.act, byId(el.closest('.card').dataset.id));
  });
  $('#mBody').addEventListener('click', (e) => {
    const o = e.target.closest('[data-open]'); if (o) return openModal(byId(o.dataset.open));
    const el = e.target.closest('[data-act]'); if (el) act(el.dataset.act, byId($('#mBody').dataset.id));
  });
  $('#suggestBox').addEventListener('click', (e) => { if (e.target.closest('[data-act="closeSuggest"]')) { state.suggest = null; render(); } });
  $('#mClose').onclick = () => $('#modal').close();
  $('#modal').addEventListener('click', (e) => { if (e.target === $('#modal')) $('#modal').close(); });

  $('#batchChips').addEventListener('click', (e) => { const c = e.target.closest('.chip'); if (!c) return; state.batch = c.dataset.k; state.limit = PAGE; state.suggest = null; renderChips(); render(); });
  $('#sceneChips').addEventListener('click', (e) => { const c = e.target.closest('.chip'); if (!c) return; state.scene = c.dataset.k; state.limit = PAGE; state.suggest = null; renderChips(); render(); });

  let qt; $('#q').addEventListener('input', (e) => { clearTimeout(qt); qt = setTimeout(() => { state.q = e.target.value; state.limit = PAGE; state.suggest = null; render(); }, 120); });
  $('#fUnused').onchange = (e) => { state.unused = e.target.checked; if (state.unused) { state.used = false; $('#fUsed').checked = false; } state.limit = PAGE; render(); };
  $('#fUsed').onchange = (e) => { state.used = e.target.checked; if (state.used) { state.unused = false; $('#fUnused').checked = false; } state.limit = PAGE; render(); };
  $('#btnMore').onclick = () => { state.limit += PAGE; render(); };
  $('#btnGuide').onclick = openGuide;

  $('#btnSuggest').onclick = () => {
    const pool = state.items.filter((i) => !used[i.id]);
    if (!pool.length) return toast('Semua dah guna 🎉');
    const rnd = seeded(todayKey());
    const arr = [...pool];
    for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; }
    state.suggest = arr.slice(0, 5).map((i) => i.id);
    render(); $('#suggestBox').scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  $('#btnRandom').onclick = () => {
    const pool = filtered().filter((i) => !used[i.id]);
    const src = pool.length ? pool : state.items;
    openModal(src[Math.floor(Math.random() * src.length)]);
  };

  $('#today').textContent = '📅 ' + new Date().toLocaleDateString('ms-MY', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  load().catch((err) => { $('#showing').textContent = 'Gagal muat data: ' + err.message; });
})();
