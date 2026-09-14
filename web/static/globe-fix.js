(() => {
  const CDN = 'https://cdn.jsdelivr.net/npm/globe.gl@2.46.2/dist/globe.gl.min.js';
  let globeInstance = null;
  let loading = null;

  function patchNavigation() {
    const viewMeta = {
      dashboard:['Career Command Center','One workspace for every portal, match, application and preference.'],
      portals:['Job Portals','Screen supported public sources separately and see exactly where each job came from.'],
      jobs:['All Jobs','Search and filter opportunities across every saved portal.'],
      applications:['Application Queue','Review prepared applications before submission.'],
      rag:['RAG / Resume Intelligence','Your CV knowledge base powers semantic matching and preparation.'],
      settings:['Profile & Settings','Change internship/full-time, roles, locations and portal preferences.']
    };
    window.setView = function(view) {
      if (!viewMeta[view]) view = 'dashboard';
      window.state.view = view;
      document.querySelectorAll('[data-page]').forEach(x => x.classList.toggle('active-page', x.dataset.page === view));
      document.querySelectorAll('#nav a').forEach(x => x.classList.toggle('active', x.dataset.view === view));
      const title = document.getElementById('page-title'), subtitle = document.getElementById('page-subtitle');
      if (title) title.textContent = viewMeta[view][0];
      if (subtitle) subtitle.textContent = viewMeta[view][1];
      if (location.hash !== '#' + view) history.replaceState(null,'','#' + view);
      if (view === 'jobs') {
        setTimeout(() => {
          if (typeof window.loadStartupMapJobs === 'function') window.loadStartupMapJobs();
          else setTimeout(() => window.loadStartupMapJobs?.(), 300);
        }, 0);
      } else if (view === 'applications') window.loadApplications?.();
      else if (view === 'rag') window.loadRag?.();
      else if (view === 'settings') window.loadProfile?.();
      else if (view === 'portals') window.loadPortals?.();
      else if (view === 'dashboard') { window.loadStats?.(); window.loadPortals?.(); }
    };
  }

  function loadGlobe() {
    if (typeof window.Globe === 'function') return Promise.resolve();
    if (loading) return loading;
    loading = new Promise((resolve,reject) => {
      const s = document.createElement('script');
      s.src = CDN; s.async = true;
      s.onload = () => typeof window.Globe === 'function' ? resolve() : reject(new Error('Globe global missing'));
      s.onerror = reject;
      document.head.appendChild(s);
    });
    return loading;
  }

  function coords(location) {
    const s = String(location || '').toLowerCase();
    const map = {
      london:[51.5074,-0.1278],paris:[48.8566,2.3522],berlin:[52.52,13.405],amsterdam:[52.3676,4.9041],stockholm:[59.3293,18.0686],madrid:[40.4168,-3.7038],dublin:[53.3498,-6.2603],zurich:[47.3769,8.5417],munich:[48.1351,11.582],vienna:[48.2082,16.3738],prague:[50.0755,14.4378],milan:[45.4642,9.19],rome:[41.9028,12.4964],bengaluru:[12.9716,77.5946],bangalore:[12.9716,77.5946],delhi:[28.6139,77.209],mumbai:[19.076,72.8777],hyderabad:[17.385,78.4867],pune:[18.5204,73.8567],chennai:[13.0827,80.2707],gurugram:[28.4595,77.0266],gurgaon:[28.4595,77.0266],noida:[28.5355,77.391],jodhpur:[26.2389,73.0243],singapore:[1.3521,103.8198],sydney:[-33.8688,151.2093],melbourne:[-37.8136,144.9631],toronto:[43.6532,-79.3832],newyork:[40.7128,-74.006],sanfrancisco:[37.7749,-122.4194],boston:[42.3601,-71.0589],seattle:[47.6062,-122.3321]
    };
    for (const [name,xy] of Object.entries(map)) if (s.includes(name)) return xy;
    if (s.includes('india')) return [20.5937,78.9629];
    if (s.includes('germany')) return [51.1657,10.4515];
    if (s.includes('france')) return [46.2276,2.2137];
    if (s.includes('uk') || s.includes('united kingdom')) return [55.3781,-3.436];
    if (s.includes('usa') || s.includes('united states')) return [37.0902,-95.7129];
    if (s.includes('canada')) return [56.1304,-106.3468];
    if (s.includes('australia')) return [-25.2744,133.7751];
    return null;
  }

  function render() {
    const el = document.getElementById('sm-globe');
    if (!el || el.clientWidth < 50 || el.clientHeight < 50 || typeof window.Globe !== 'function') return;
    const jobs = Array.isArray(window.state?.jobs) ? window.state.jobs : [];
    const grouped = {};
    jobs.forEach(job => {
      const p = coords(job.location); if (!p) return;
      const key = p.join(','); grouped[key] ||= {lat:p[0],lng:p[1],count:0,label:String(job.location || 'Location')}; grouped[key].count++;
    });
    try {
      el.innerHTML = '';
      globeInstance = window.Globe()(el)
        .backgroundColor('#07101f')
        .showAtmosphere(true)
        .atmosphereColor('#8b5cf6')
        .atmosphereAltitude(0.16)
        .waitForGlobeReady(false)
        .globeImageUrl('https://cdn.jsdelivr.net/npm/three-globe@2.45.2/example/img/earth-blue-marble.jpg')
        .bumpImageUrl('https://cdn.jsdelivr.net/npm/three-globe@2.45.2/example/img/earth-topology.png')
        .pointsData(Object.values(grouped))
        .pointLat('lat').pointLng('lng')
        .pointAltitude(p => Math.min(0.3,0.04 + Math.log2(p.count + 1) * 0.04))
        .pointRadius(p => Math.min(0.5,0.09 + Math.log2(p.count + 1) * 0.05))
        .pointColor(() => '#a78bfa')
        .pointLabel(p => `<b>${p.label}</b><br>${p.count} job${p.count === 1 ? '' : 's'}`);
      globeInstance.pointOfView({lat:20,lng:20,altitude:2.05},800);
      globeInstance.controls().autoRotate = true;
      globeInstance.controls().autoRotateSpeed = 0.3;
      globeInstance.controls().enableZoom = true;
      window.__jobGlobe = globeInstance;
    } catch (error) {
      console.error('[JOB-AUTOMATION] globe render failed', error);
      el.innerHTML = '<div class="globe-fallback"><div class="fallback-earth"><span>🌍</span></div><b>Global hiring map</b><small>Interactive globe could not initialize. Country and city job data is still available.</small></div>';
    }
  }

  function boot() {
    patchNavigation();
    if (location.hash === '#jobs') setTimeout(() => window.setView('jobs'), 50);
    const observer = new MutationObserver(() => {
      const el = document.getElementById('sm-globe');
      if (el && !el.querySelector('canvas')) {
        loadGlobe().then(() => setTimeout(render,50)).catch(err => console.error('[JOB-AUTOMATION] globe CDN failed',err));
      }
    });
    observer.observe(document.body,{childList:true,subtree:true});
    setTimeout(() => {
      if (document.getElementById('sm-globe')) loadGlobe().then(render).catch(console.error);
    },500);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();
