(() => {
  const CDNS = [
    'https://cdn.jsdelivr.net/npm/globe.gl@2.45.7/dist/globe.gl.min.js',
    'https://unpkg.com/globe.gl@2.45.7/dist/globe.gl.min.js'
  ];
  const coords = {
    london:[51.5074,-0.1278],paris:[48.8566,2.3522],berlin:[52.52,13.405],amsterdam:[52.3676,4.9041],stockholm:[59.3293,18.0686],madrid:[40.4168,-3.7038],dublin:[53.3498,-6.2603],zurich:[47.3769,8.5417],munich:[48.1351,11.582],vienna:[48.2082,16.3738],prague:[50.0755,14.4378],brussels:[50.8503,4.3517],milan:[45.4642,9.19],rome:[41.9028,12.4964],bengaluru:[12.9716,77.5946],bangalore:[12.9716,77.5946],delhi:[28.6139,77.209],mumbai:[19.076,72.8777],hyderabad:[17.385,78.4867],pune:[18.5204,73.8567],chennai:[13.0827,80.2707],gurugram:[28.4595,77.0266],gurgaon:[28.4595,77.0266],noida:[28.5355,77.391],jodhpur:[26.2389,73.0243],singapore:[1.3521,103.8198],sydney:[-33.8688,151.2093],melbourne:[-37.8136,144.9631],toronto:[43.6532,-79.3832],newyork:[40.7128,-74.006],sanfrancisco:[37.7749,-122.4194],boston:[42.3601,-71.0589],seattle:[47.6062,-122.3321]
  };
  const countryCoords = {india:[20.5937,78.9629],germany:[51.1657,10.4515],france:[46.2276,2.2137],uk:[55.3781,-3.436],netherlands:[52.1326,5.2913],sweden:[60.1282,18.6435],spain:[40.4637,-3.7492],ireland:[53.1424,-7.6921],switzerland:[46.8182,8.2275],austria:[47.5162,14.5501],belgium:[50.5039,4.4699],italy:[41.8719,12.5674],canada:[56.1304,-106.3468],usa:[37.0902,-95.7129],singapore:[1.3521,103.8198],australia:[-25.2744,133.7751],japan:[36.2048,138.2529],uae:[23.4241,53.8478]};
  let instance = null;
  let loading = null;

  const norm = value => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  function place(location) {
    const raw = String(location || 'Remote');
    const n = norm(raw);
    const city = Object.keys(coords).find(k => n.includes(k));
    const country = Object.keys(countryCoords).find(k => n.includes(k));
    return { city: city ? city.replace(/\b\w/g,c=>c.toUpperCase()) : raw.split(',')[0].trim(), coords: city ? coords[city] : (country ? countryCoords[country] : null) };
  }
  function jobs() {
    if (Array.isArray(window.state?.jobs) && window.state.jobs.length) return window.state.jobs;
    return [];
  }
  function hasWebGL() {
    try { const c = document.createElement('canvas'); return !!(c.getContext('webgl') || c.getContext('experimental-webgl')); } catch (_) { return false; }
  }
  function showFallback(message) {
    const el = document.getElementById('sm-globe');
    if (!el) return;
    el.innerHTML = `<div class="globe-fallback"><div class="fallback-earth"><span>🌍</span></div><b>Global hiring map</b><small>${message}</small></div>`;
  }
  function loadScript(url) {
    return new Promise((resolve,reject) => {
      const existing = document.querySelector(`script[data-globe-src="${url}"]`);
      if (existing) { existing.addEventListener('load',resolve,{once:true}); existing.addEventListener('error',reject,{once:true}); if (typeof window.Globe === 'function') resolve(); return; }
      const s = document.createElement('script'); s.src = url; s.async = true; s.dataset.globeSrc = url;
      s.onload = () => typeof window.Globe === 'function' ? resolve() : reject(new Error('Globe global missing'));
      s.onerror = reject; document.head.appendChild(s);
    });
  }
  async function ensureLibrary() {
    if (typeof window.Globe === 'function') return;
    if (loading) return loading;
    loading = (async () => {
      let last;
      for (const cdn of CDNS) { try { await loadScript(cdn); if (typeof window.Globe === 'function') return; } catch (e) { last = e; } }
      throw last || new Error('No globe CDN loaded');
    })();
    return loading;
  }
  function markerData() {
    const grouped = {};
    jobs().forEach(job => {
      const p = place(job.location);
      if (!p.coords) return;
      const key = p.coords.join(',');
      grouped[key] ||= {lat:p.coords[0],lng:p.coords[1],count:0,label:p.city};
      grouped[key].count += 1;
    });
    return Object.values(grouped);
  }
  async function render() {
    const el = document.getElementById('sm-globe');
    if (!el || el.clientWidth < 20 || el.clientHeight < 20) return false;
    if (el.dataset.globeReady === '1' && instance) return true;
    if (!hasWebGL()) { showFallback('WebGL is disabled in this browser. Jobs remain available by country and city.'); return false; }
    try {
      await ensureLibrary();
      if (typeof window.Globe !== 'function') throw new Error('Globe library unavailable');
      el.innerHTML = '';
      instance = window.Globe()(el)
        .backgroundColor('#07101f')
        .showAtmosphere(true)
        .atmosphereColor('#8b5cf6')
        .atmosphereAltitude(0.16)
        .globeImageUrl('https://cdn.jsdelivr.net/npm/three-globe@2.45.2/example/img/earth-blue-marble.jpg')
        .bumpImageUrl('https://cdn.jsdelivr.net/npm/three-globe@2.45.2/example/img/earth-topology.png')
        .pointOfView({lat:20,lng:20,altitude:2.15},900)
        .pointsData(markerData())
        .pointLat('lat').pointLng('lng')
        .pointAltitude(p => Math.min(0.32,0.05 + Math.log2(p.count + 1) * 0.04))
        .pointRadius(p => Math.min(0.65,0.11 + Math.log2(p.count + 1) * 0.06))
        .pointColor(() => '#a78bfa')
        .pointLabel(p => `<b>${p.label}</b><br>${p.count} job${p.count === 1 ? '' : 's'}`)
        .enablePointerInteraction(true);
      instance.controls().autoRotate = true;
      instance.controls().autoRotateSpeed = 0.28;
      instance.controls().enableZoom = true;
      el.dataset.globeReady = '1';
      window.addEventListener('resize', () => { if (instance && el.clientWidth) instance.width(el.clientWidth).height(el.clientHeight); });
      return true;
    } catch (error) {
      console.error('[JOB-AUTOMATION] globe failed', error);
      showFallback('Interactive Earth could not load. The job feed and location filters are still active.');
      return false;
    }
  }
  function refreshPoints() { if (instance) instance.pointsData(markerData()); }
  function boot() {
    const page = document.querySelector('[data-page="jobs"]');
    if (!page) return;
    const observer = new MutationObserver(() => { if (document.getElementById('sm-globe')) render(); });
    observer.observe(page,{childList:true,subtree:true});
    setTimeout(render,250);
    setTimeout(render,1000);
    setTimeout(render,2500);
    setInterval(refreshPoints,5000);
  }
  window.addEventListener('hashchange', () => { if (location.hash === '#jobs') setTimeout(render,250); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();
