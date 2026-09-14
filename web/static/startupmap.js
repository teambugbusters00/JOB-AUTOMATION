(() => {
  const cities = {
    london:[51.5074,-0.1278], paris:[48.8566,2.3522], berlin:[52.52,13.405], amsterdam:[52.3676,4.9041], stockholm:[59.3293,18.0686], copenhagen:[55.6761,12.5683], madrid:[40.4168,-3.7038], barcelona:[41.3874,2.1686], lisbon:[38.7223,-9.1393], dublin:[53.3498,-6.2603], zurich:[47.3769,8.5417], geneva:[46.2044,6.1432], munich:[48.1351,11.582], hamburg:[53.5511,9.9937], frankfurt:[50.1109,8.6821], aachen:[50.7753,6.0839], freiburg:[47.999,7.8421], cologne:[50.9375,6.9603], stuttgart:[48.7758,9.1829], vienna:[48.2082,16.3738], prague:[50.0755,14.4378], warsaw:[52.2297,21.0122], brussels:[50.8503,4.3517], ghent:[51.0543,3.7174], antwerp:[51.2194,4.4025], leuven:[50.8798,4.7005], porto:[41.1579,-8.6291], milan:[45.4642,9.19], rome:[41.9028,12.4964], uppsala:[59.8586,17.6389], reykjavik:[64.1466,-21.9426], budapest:[47.4979,19.0402], bucharest:[44.4268,26.1025], sofia:[42.6977,23.3219], zagreb:[45.815,15.9819], belgrade:[44.7866,20.4489], istanbul:[41.0082,28.9784], athens:[37.9838,23.7275], bengaluru:[12.9716,77.5946], bangalore:[12.9716,77.5946], delhi:[28.6139,77.209], newdelhi:[28.6139,77.209], mumbai:[19.076,72.8777], hyderabad:[17.385,78.4867], pune:[18.5204,73.8567], chennai:[13.0827,80.2707], gurugram:[28.4595,77.0266], gurgaon:[28.4595,77.0266], noida:[28.5355,77.391], jodhpur:[26.2389,73.0243], singapore:[1.3521,103.8198], sydney:[-33.8688,151.2093], melbourne:[-37.8136,144.9631], toronto:[43.6532,-79.3832], montreal:[45.5017,-73.5673], newyork:[40.7128,-74.006], sanfrancisco:[37.7749,-122.4194], boston:[42.3601,-71.0589], seattle:[47.6062,-122.3321]
  };
  const countries = {
    india:[20.5937,78.9629], germany:[51.1657,10.4515], france:[46.2276,2.2137], uk:[55.3781,-3.436], "united kingdom":[55.3781,-3.436], netherlands:[52.1326,5.2913], sweden:[60.1282,18.6435], denmark:[56.2639,9.5018], spain:[40.4637,-3.7492], portugal:[39.3999,-8.2245], ireland:[53.1424,-7.6921], switzerland:[46.8182,8.2275], austria:[47.5162,14.5501], belgium:[50.5039,4.4699], luxembourg:[49.8153,6.1296], finland:[61.9241,25.7482], norway:[60.472,8.4689], estonia:[58.5953,25.0136], poland:[51.9194,19.1451], czechia:[49.8175,15.473], italy:[41.8719,12.5674], greece:[39.0742,21.8243], hungary:[47.1625,19.5033], romania:[45.9432,24.9668], bulgaria:[42.7339,25.4858], croatia:[45.1,15.2], serbia:[44.0165,21.0059], turkey:[38.9637,35.2433], iceland:[64.9631,-19.0208], canada:[56.1304,-106.3468], usa:[37.0902,-95.7129], "united states":[37.0902,-95.7129], singapore:[1.3521,103.8198], australia:[-25.2744,133.7751], japan:[36.2048,138.2529], uae:[23.4241,53.8478], "united arab emirates":[23.4241,53.8478]
  };
  const aliases = {uk:'United Kingdom','united kingdom':'United Kingdom',usa:'United States','united states':'United States',us:'United States',uae:'United Arab Emirates'};
  const filters = {q:'', type:'', country:'', remote:'', score:'', source:''};
  let globe = null, globePromise = null, filteredJobs = [];

  const normalize = value => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  const jobType = job => {
    const type = String(job.employment_type || '').toLowerCase();
    if (type.includes('intern')) return 'internship';
    if (type.includes('part')) return 'part-time';
    if (type.includes('contract')) return 'contract';
    return 'full-time';
  };
  const locationParts = location => {
    const raw = String(location || 'Remote').trim();
    const parts = raw.split(',').map(x => x.trim()).filter(Boolean);
    const text = normalize(raw);
    const cityKey = Object.keys(cities).find(key => text.includes(key));
    const countryKey = Object.keys(countries).find(key => text.includes(key));
    const country = countryKey ? (aliases[countryKey] || countryKey.replace(/\b\w/g, c => c.toUpperCase())) : (parts.length > 1 ? parts[parts.length - 1] : 'Worldwide');
    return { city: cityKey ? cityKey.replace(/\b\w/g,c=>c.toUpperCase()) : (parts[0] || 'Remote'), country, coords: cityKey ? cities[cityKey] : (countryKey ? countries[countryKey] : null) };
  };
  const jobData = () => Array.isArray(window.state?.jobs) ? window.state.jobs : [];
  const matches = job => {
    const place = locationParts(job.location);
    const text = `${job.title || ''} ${job.company || ''} ${job.description || ''} ${job.source || ''} ${job.location || ''}`.toLowerCase();
    return (!filters.q || text.includes(filters.q)) && (!filters.type || jobType(job) === filters.type) && (!filters.country || place.country.toLowerCase() === filters.country.toLowerCase()) && (!filters.remote || String(job.remote || '').toLowerCase().includes(filters.remote)) && (!filters.score || Number(job.score || 0) >= Number(filters.score)) && (!filters.source || String(job.source || '').toLowerCase() === filters.source.toLowerCase());
  };

  function shell() {
    const page = document.querySelector('[data-page="jobs"]');
    if (!page) return false;
    page.innerHTML = `<div class="sm-shell">
      <div class="sm-topbar"><div class="sm-brand"><span class="sm-logo">◎</span><b>Job Hunter</b><span class="sm-divider"></span><span class="sm-tab active">Map</span><span class="sm-tab">Jobs <em id="sm-job-count">0</em></span></div><div class="sm-search-wrap"><span>⌕</span><input id="sm-search" placeholder="Search jobs, companies, cities, countries…"><kbd>Ctrl K</kbd></div><button class="sm-icon-btn" id="sm-reset">↻</button></div>
      <div class="sm-filterbar"><button class="sm-filter" data-filter="type">Role <span>⌄</span></button><button class="sm-filter" data-filter="location">Location <span>⌄</span></button><button class="sm-filter" data-filter="remote">Workplace <span>⌄</span></button><button class="sm-filter" data-filter="score">Match score <span>⌄</span></button><button class="sm-filter" data-filter="source">Portal <span>⌄</span></button><div class="sm-live"><span></span> Live jobs</div></div>
      <div class="sm-main"><aside class="sm-sidebar"><div class="sm-side-head"><div><b>Worldwide hiring</b><small>Jobs grouped by country and city</small></div><span id="sm-side-total">0</span></div><div id="sm-country-list" class="sm-country-list"></div></aside><section class="sm-map-panel"><div id="sm-globe" class="sm-globe"></div><div class="sm-map-overlay"><div><strong>Global hiring map</strong><small>Click a country or city marker to focus jobs</small></div><div class="sm-map-stats"><span><b id="sm-map-jobs">0</b> jobs</span><span><b id="sm-map-countries">0</b> countries</span></div></div><div id="sm-job-feed" class="sm-job-feed"></div></section></div><div id="sm-menu" class="sm-menu hidden"></div>
    </div>`;
    return true;
  }

  function renderCountries() {
    const groups = {};
    filteredJobs.forEach(job => { const p = locationParts(job.location); groups[p.country] ||= {count:0,cities:{}}; groups[p.country].count++; groups[p.country].cities[p.city] = (groups[p.country].cities[p.city] || 0) + 1; });
    const list = Object.entries(groups).sort((a,b) => b[1].count - a[1].count);
    $('#sm-job-count').textContent = filteredJobs.length;
    $('#sm-side-total').textContent = filteredJobs.length;
    $('#sm-map-jobs').textContent = filteredJobs.length;
    $('#sm-map-countries').textContent = list.length;
    $('#sm-country-list').innerHTML = list.length ? list.map(([country,data]) => `<div class="sm-country ${filters.country === country ? 'selected' : ''}"><button class="sm-country-main" data-country="${esc(country)}"><span class="sm-pin">◉</span><span><b>${esc(country)}</b><small>${Object.entries(data.cities).slice(0,3).map(([city,count]) => `${esc(city)} ${count}`).join(' · ')}</small></span><strong>${data.count}</strong></button></div>`).join('') : '<div class="sm-empty">No locations match.</div>';
    document.querySelectorAll('.sm-country-main').forEach(button => button.onclick = () => { filters.country = button.dataset.country; renderAll(); });
  }

  function renderFeed() {
    const list = filteredJobs.slice(0,60);
    $('#sm-job-feed').innerHTML = `<div class="sm-feed-head"><div><b>${filteredJobs.length.toLocaleString()} jobs</b><small>from saved portals · ranked for your profile</small></div><select id="sm-sort"><option value="score">Best match</option><option value="newest">Recently seen</option><option value="company">Company A–Z</option></select></div>` + (list.length ? list.map((job,index) => { const p = locationParts(job.location); return `<article class="sm-job-card"><div class="sm-company-dot">${esc(String(job.company || '?').slice(0,1).toUpperCase())}</div><div class="sm-job-body"><div class="sm-job-line"><span class="sm-source">${esc(job.source || 'Portal')}</span><span class="sm-job-type">${esc(jobType(job))}</span><span class="sm-match">${Number(job.score || 0)}%</span></div><h3>${esc(job.title || 'Untitled role')}</h3><b>${esc(job.company || 'Unknown company')}</b><p>${esc(p.city)} · ${esc(p.country)} · ${esc(job.remote || 'Workplace not specified')}</p><div class="sm-reasons">${(job.match_reasons || []).slice(0,3).map(esc).join(' · ')}</div></div><button class="sm-open" data-index="${index}">Apply ↗</button></article>`; }).join('') : '<div class="sm-empty">No jobs match these filters. Try another country, city or role.</div>');
    const sort = $('#sm-sort');
    if (sort) sort.onchange = () => { const mode = sort.value; filteredJobs.sort((a,b) => mode === 'company' ? String(a.company || '').localeCompare(String(b.company || '')) : mode === 'newest' ? new Date(b.last_seen_at || 0) - new Date(a.last_seen_at || 0) : Number(b.score || 0) - Number(a.score || 0); renderFeed(); bindJobButtons(); };
    bindJobButtons();
  }

  function bindJobButtons() {
    document.querySelectorAll('.sm-open').forEach(button => button.onclick = () => { const job = filteredJobs[Number(button.dataset.index)]; if (job && typeof window.openJob === 'function') window.openJob(job); });
  }

  function renderFilterMenu(kind) {
    const menu = $('#sm-menu');
    let html = '';
    if (kind === 'type') html = '<b>Role type</b><button data-v="">All jobs</button><button data-v="internship">Internship</button><button data-v="full-time">Full-time</button><button data-v="part-time">Part-time</button><button data-v="contract">Contract</button>';
    if (kind === 'remote') html = '<b>Workplace</b><button data-v="">All workplaces</button><button data-v="remote">Remote</button><button data-v="hybrid">Hybrid</button><button data-v="onsite">Onsite</button>';
    if (kind === 'score') html = '<b>Minimum match</b><button data-v="">Any score</button><button data-v="75">75%+</button><button data-v="85">85%+</button><button data-v="90">90%+</button>';
    if (kind === 'location') html = '<b>Country</b><button data-v="">All countries</button>' + [...new Set(jobData().map(job => locationParts(job.location).country))].sort().map(country => `<button data-v="${esc(country)}">${esc(country)}</button>`).join('');
    if (kind === 'source') html = '<b>Portal</b><button data-v="">All portals</button>' + [...new Set(jobData().map(job => job.source).filter(Boolean))].sort().map(source => `<button data-v="${esc(source)}">${esc(source)}</button>`).join('');
    menu.innerHTML = html; menu.classList.remove('hidden');
    menu.querySelectorAll('button').forEach(button => button.onclick = () => { const value = button.dataset.v; if (kind === 'type') filters.type = value; if (kind === 'remote') filters.remote = value; if (kind === 'score') filters.score = value; if (kind === 'location') filters.country = value; if (kind === 'source') filters.source = value; menu.classList.add('hidden'); renderAll(); });
  }

  function controls() {
    $('#sm-search').oninput = event => { filters.q = event.target.value.toLowerCase().trim(); renderAll(); };
    $('#sm-reset').onclick = () => { Object.keys(filters).forEach(key => filters[key] = ''); $('#sm-search').value = ''; renderAll(); };
    document.querySelectorAll('.sm-filter').forEach(button => button.onclick = () => renderFilterMenu(button.dataset.filter));
    document.addEventListener('click', event => { if (!event.target.closest('.sm-filter') && !event.target.closest('#sm-menu')) $('#sm-menu')?.classList.add('hidden'); });
  }

  function renderGlobePoints() {
    if (!globe) return;
    const grouped = {};
    filteredJobs.forEach(job => { const p = locationParts(job.location); if (!p.coords) return; const key = p.coords.join(','); grouped[key] ||= {lat:p.coords[0],lng:p.coords[1],count:0,label:p.city,country:p.country}; grouped[key].count++; });
    globe.pointsData(Object.values(grouped)).pointLat('lat').pointLng('lng').pointAltitude(p => Math.min(.35,.06 + Math.log2(p.count + 1) * .035)).pointRadius(p => Math.min(.7,.12 + Math.log2(p.count + 1) * .07)).pointColor(() => '#a78bfa').pointLabel(p => `<b>${esc(p.label)}, ${esc(p.country)}</b><br>${p.count} matching job${p.count === 1 ? '' : 's'}`);
  }

  function loadGlobeScript() {
    if (globePromise) return globePromise;
    globePromise = new Promise((resolve,reject) => { if (typeof window.Globe === 'function') return resolve(); const script = document.createElement('script'); script.src = 'https://cdn.jsdelivr.net/npm/globe.gl@2.45.7/dist/globe.gl.min.js'; script.onload = () => resolve(); script.onerror = reject; document.head.appendChild(script); });
    return globePromise;
  }

  async function initGlobe() {
    try {
      await loadGlobeScript();
      const el = document.getElementById('sm-globe');
      if (!el || typeof window.Globe !== 'function') throw new Error('Globe library did not load');
      globe = window.Globe()(el).backgroundColor('#07101f').showAtmosphere(true).atmosphereColor('#8b5cf6').atmosphereAltitude(.14).globeImageUrl('https://cdn.jsdelivr.net/npm/three-globe@2.45.2/example/img/earth-blue-marble.jpg').bumpImageUrl('https://cdn.jsdelivr.net/npm/three-globe@2.45.2/example/img/earth-topology.png').width(el.clientWidth).height(el.clientHeight).enablePointerInteraction(true).pointOfView({lat:25,lng:15,altitude:2.1},1000);
      globe.controls().autoRotate = true; globe.controls().autoRotateSpeed = .25; renderGlobePoints();
      window.addEventListener('resize', () => { if (globe) globe.width(el.clientWidth).height(el.clientHeight); });
    } catch (error) {
      const el = document.getElementById('sm-globe');
      if (el) el.innerHTML = '<div class="sm-globe-fallback"><div class="sm-fallback-earth">🌍</div><b>Interactive globe unavailable</b><small>Check the browser network/CDN access. Jobs are still grouped by country and city.</small></div>';
      console.error('Globe initialization failed:', error);
    }
  }

  function renderAll() {
    filteredJobs = jobData().filter(matches);
    renderCountries(); renderFeed(); renderGlobePoints();
  }

  async function loadStartupMapJobs() {
    if (!shell()) return;
    controls();
    try {
      window.state.jobs = await api('/api/jobs?limit=200');
      renderAll();
      initGlobe();
    } catch (error) {
      $('#sm-job-feed').innerHTML = `<div class="sm-empty error-text">${esc(error.message)}</div>`;
    }
  }

  window.loadStartupMapJobs = loadStartupMapJobs;
  const originalSetView = window.setView;
  window.setView = function(view) { if (typeof originalSetView === 'function') originalSetView(view); if (view === 'jobs') setTimeout(loadStartupMapJobs, 0); };
  window.loadJobs = loadStartupMapJobs;
  if (location.hash === '#jobs') setTimeout(loadStartupMapJobs, 200);
})();
