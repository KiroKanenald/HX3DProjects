'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const gallery = $('gallery');
  const search = $('search');
  const categories = $('categories');
  let models = [];
  let category = 'Alle';
  const fmt = n => Number(n).toLocaleString('de-DE');
  const bytes = n => n < 1024*1024 ? `${(n/1024).toFixed(0)} KB` : `${(n/1024/1024).toFixed(1)} MB`;

  function node(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function showMessage(message) {
    gallery.replaceChildren(node('p', 'empty-message', message));
  }
  function createCard(m) {
    const card = node('article','asset');
    const preview = node('div','preview');
    if (typeof m.image === 'string' && /^previews\/[\w./-]+\.png$/i.test(m.image) && !m.image.includes('..')) {
      const img = node('img'); img.src = m.image; img.alt = `Vorschau ${m.title}`; img.loading = 'lazy';
      preview.append(img);
    } else {preview.append(node('span','placeholder','◇'));}
    card.append(preview);
    const details = node('div','details');
    details.append(node('span','tag',m.category),node('h3','',m.title),node('p','',m.description));
    details.append(node('div','meta',`${fmt(m.triangles)} Dreiecke · HX3D ${m.version} · ${bytes(m.size_bytes)}`));
    const tools = node('div','tools');
    const view = node('a','button tiny','3D ansehen ↗');
    view.href = `viewer.html?${new URLSearchParams({model:m.path})}`;
    const download = node('a','button tiny plain','HX3D laden ↓');
    download.href = m.path; download.download = m.path.split('/').pop();
    tools.append(view,download);details.append(tools);card.append(details);
    return card;
  }
  function draw() {
    const q = search.value.trim().toLocaleLowerCase('de');
    const filtered = models.filter(m => (category === 'Alle' || m.category === category) &&
      `${m.title} ${m.category} ${m.description}`.toLocaleLowerCase('de').includes(q));
    gallery.replaceChildren(...filtered.map(createCard));
    if (!filtered.length) showMessage('Für diese Auswahl gibt es noch keine Modelle.');
  }
  function selectCategory(c) {
    category = c;
    for(const b of categories.querySelectorAll('button')){
      const active = b.dataset.category === category;
      b.classList.toggle('active',active); b.setAttribute('aria-pressed',String(active));
    }
    draw();
  }
  function renderCategories() {
    categories.replaceChildren();
    for(const c of ['Alle',...new Set(models.map(m => m.category))]){
      const b=node('button','tab',c);b.type='button';b.dataset.category=c;
      b.addEventListener('click',()=>selectCategory(c));categories.append(b);
    }
    selectCategory('Alle');
  }
  search.addEventListener('input',draw);
  async function loadCatalog() {
    try {
      const response = await fetch('catalog.json');
      if (!response.ok) throw Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (data.schema_version !== 1 || !Array.isArray(data.models)) throw Error('Unbekanntes Katalogformat');
      models = data.models.filter(m => typeof m.path === 'string' && /^models\/[\w./-]+\.hx3d$/i.test(m.path) && !m.path.includes('..'));
      $('count').textContent = fmt(models.length);
      $('triangles').textContent = fmt(models.reduce((sum,m)=>sum+m.triangles,0));
      renderCategories();
    } catch(e) {
      showMessage(`Katalog konnte nicht geladen werden (${e.message}). Bitte die Seite über einen lokalen Webserver oder GitHub Pages öffnen.`);
    }
  }
  loadCatalog();
})();
