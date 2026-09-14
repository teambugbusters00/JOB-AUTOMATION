(() => {
  const cityCoords = {
    london:[51.5074,-0.1278],paris:[48.8566,2.3522],berlin:[52.52,13.405],amsterdam:[52.3676,4.9041],stockholm:[59.3293,18.0686],copenhagen:[55.6761,12.5683],madrid:[40.4168,-3.7038],barcelona:[41.3874,2.1686],lisbon:[38.7223,-9.1393],dublin:[53.3498,-6.2603],zurich:[47.3769,8.5417],geneva:[46.2044,6.1432],munich:[48.1351,11.582],hamburg:[53.5511,9.9937],frankfurt:[50.1109,8.6821],aachen:[50.7753,6.0839],freiburg:[47.999,7.8421],cologne:[50.9375,6.9603],stuttgart:[48.7758,9.1829],vienna:[48.2082,16.3738],prague:[50.0755,14.4378],warsaw:[52.2297,21.0122],tallinn:[59.437,24.7536],helsinki:[60.1699,24.9384],oslo:[59.9139,10.7522],brussels:[50.8503,4.3517],ghent:[51.0543,3.7174],antwerp:[51.2194,4.4025],leuven:[50.8798,4.7005],luxembourg:[49.6116,6.1319],luxembourgcity:[49.6116,6.1319],foetz:[49.515,6.096],porto:[41.1579,-8.6291],montpellier:[43.6108,3.8767],grenoble:[45.1885,5.7245],lyon:[45.764,4.8357],milan:[45.4642,9.19],rome:[41.9028,12.4964],lisbon:[38.7223,-9.1393],uppsala:[59.8586,17.6389],reykjavik:[64.1466,-21.9426],budapest:[47.4979,19.0402],bucharest:[44.4268,26.1025],sofia:[42.6977,23.3219],zagreb:[45.815,15.9819],belgrade:[44.7866,20.4489],istanbul:[41.0082,28.9784],athens:[37.9838,23.7275],bengaluru:[12.9716,77.5946],bangalore:[12.9716,77.5946],delhi:[28.6139,77.209],newdelhi:[28.6139,77.209],mumbai:[19.076,72.8777],hyderabad:[17.385,78.4867],pune:[18.5204,73.8567],chennai:[13.0827,80.2707],gurugram:[28.4595,77.0266],gurgaon:[28.4595,77.0266],noida:[28.5355,77.391],jodhpur:[26.2389,73.0243],singapore:[1.3521,103.8198],sydney:[-33.8688,151.2093],melbourne:[-37.8136,144.9631],toronto:[43.6532,-79.3832],montreal:[45.5017,-73.5673],newyork:[40.7128,-74.006],sanfrancisco:[37.7749,-122.4194],boston:[42.3601,-71.0589],seattle:[47.6062,-122.3321]};
  const countryCoords = {india:[20.5937,78.9629],germany:[51.1657,10.4515],france:[46.2276,2.2137],uk:[55.3781,-3.436],"united kingdom":[55.3781,-3.436],netherlands:[52.1326,5.2913],sweden:[60.1282,18.6435],denmark:[56.2639,9.5018],spain:[40.4637,-3.7492],portugal:[39.3999,-8.2245],ireland:[53.1424,-7.6921],switzerland:[46.8182,8.2275],austria:[47.5162,14.5501],belgium:[50.5039,4.4699],luxembourg:[49.8153,6.1296],finland:[61.9241,25.7482],norway:[60.472,8.4689],estonia:[58.5953,25.0136],poland:[51.9194,19.1451],czechia:[49.8175,15.473],"czech republic":[49.8175,15.473],italy:[41.8719,12.5674],greece:[39.0742,21.8243],hungary:[47.1625,19.5033],romania:[45.9432,24.9668],bulgaria:[42.7339,25.4858],croatia:[45.1,15.2],serbia:[44.0165,21.0059],turkey:[38.9637,35.2433],iceland:[64.9631,-19.0208],canada:[56.1304,-106.3468],usa:[37.0902,-95.7129],"united states":[37.0902,-95.7129],singapore:[1.3521,103.8198],australia:[-25.2744,133.7751],japan:[36.2048,138.2529],uae:[23.4241,53.8478],"united arab emirates":[23.4241,53.8478]};
  const countryAliases = {uk:'United Kingdom',"united kingdom":'United Kingdom',usa:'United States',"united states":'United States',us:'United States',uae:'United Arab Emirates'};
  let globe=null, globeReady=null, mapJobs=[], filteredJobs=[];

  function norm(v){return String(v||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim()}
  function locationParts(location){
    const raw=String(location||'Remote').trim();
    const parts=raw.split(',').map(x=>x.trim()).filter(Boolean);
    const n=norm(raw), cityKey=Object.keys(cityCoords).find(k=>n.includes(k));
    let country='Unknown';
    const countryKey=Object.keys(countryCoords).find(k=>n.includes(k));
    if(countryKey) country=countryAliases[countryKey]||countryKey.replace(/\b\w/g,c=>c.toUpperCase());
    else if(parts.length>1) country=parts[parts.length-1];
    const coords=cityKey?cityCoords[cityKey]:(countryKey?countryCoords[countryKey]:null);
    return {city:parts[0]||'Remote',country,coords};
  }
  function ensureShell(){
    const page=document.querySelector('[data-page="jobs"]'); if(!page) return false;
    page.innerHTML=`<div class="sm-shell">
      <div class="sm-topbar"><div class="sm-brand"><span class="sm-logo">◎</span><b>Job Hunter</b><span class="sm-divider"></span><span class="sm-tab active">Map</span><span class="sm-tab">Jobs <em id="sm-job-count">0</em></span></div><div class="sm-search-wrap"><span>⌕</span><input id="sm-search" placeholder="Search jobs, companies, cities, countries…"><kbd>Ctrl K</kbd></div><button class="sm-icon-btn" id="sm-reset">↻</button></div>
      <div class="sm-filterbar"><button class="sm-filter" data-filter="type">Role <span>⌄</span></button><button class="sm-filter" data-filter="location">Location <span>⌄</span></button><button class="sm-filter" data-filter="remote">Workplace <span>⌄</span></button><button class="sm-filter" data-filter="score">Match score <span>⌄</span></button><button class="sm-filter" data-filter="source">Portal <span>⌄</span></button><div class="sm-live"><span></span> Live jobs</div></div>
      <div class="sm-main"><aside class="sm-sidebar"><div class="sm-side-head"><div><b id="sm-side-title">Europe + Worldwide</b><small id="sm-side-sub">Jobs grouped by country and city</small></div><span id="sm-side-total">0</span></div><div id="sm-country-list" class="sm-country-list"></div></aside><section class="sm-map-panel"><div id="sm-globe" class="sm-globe"></div><div class="sm-map-overlay"><div><strong id="sm-map-title">Global hiring map</strong><small>Click a country or city to focus jobs</small></div><div class="sm-map-stats"><span><b id="sm-map-jobs">0</b> jobs</span><span><b id="sm-map-countries">0</b> countries</span></div></div><div id="sm-job-feed" class="sm-job-feed"></div></section></div>
      <div id="sm-menu" class="sm-menu hidden"></div>
    </div>`;
    return true;
  }
  function jobType(j){const t=String(j.employment_type||'').toLowerCase();if(t.includes('intern'))return'internship';if(t.includes('part'))return'part-time';if(t.includes('contract'))return'contract';return'full-time'}
  function jobData(){return state.jobs||[]}
  function matches(j,filters){
    const {city,country}=locationParts(j.location);
    const text=`${j.title} ${j.company} ${j.description||''} ${j.source||''} ${j.location||''}`.toLowerCase();
    return (!filters.q||text.includes(filters.q))&&(!filters.type||jobType(j)===filters.type)&&(!filters.country||country.toLowerCase()===filters.country.toLowerCase())&&(!filters.city||city.toLowerCase()===filters.city.toLowerCase())&&(!filters.remote||String(j.remote||'').toLowerCase().includes(filters.remote))&&(!filters.score||Number(j.score||0)>=Number(filters.score))&&(!filters.source||String(j.source||'').toLowerCase()===filters.source.toLowerCase());
  }
  const filters={q:'',type:'',country:'',city:'',remote:'',score:'',source:''};
  function applyFilters(){filteredJobs=jobData().filter(j=>matches(j,filters));renderCountryList();renderFeed();updateGlobe();}
  function renderCountryList(){
    const map={};filteredJobs.forEach(j=>{const p=locationParts(j.location);if(!map[p.country])map[p.country]={count:0,cities:{}};map[p.country].count++;map[p.country].cities[p.city]=(map[p.country].cities[p.city]||0)+1});
    const countries=Object.entries(map).sort((a,b)=>b[1].count-a[1].count);$('#sm-job-count').textContent=filteredJobs.length;$('#sm-side-total').textContent=filteredJobs.length;$('#sm-map-jobs').textContent=filteredJobs.length;$('#sm-map-countries').textContent=countries.length;
    $('#sm-country-list').innerHTML=countries.length?countries.map(([country,data])=>`<div class="sm-country ${filters.country===country?'selected':''}"><button class="sm-country-main" data-country="${esc(country)}"><span class="sm-pin">◉</span><span><b>${esc(country)}</b><small>${Object.entries(data.cities).slice(0,3).map(([c,n])=>`${esc(c)} ${n}`).join(' · ')}</small></span><strong>${data.count}</strong></button></div>`).join(''):'<div class="sm-empty">No locations match.</div>';
    document.querySelectorAll('.sm-country-main').forEach(b=>b.onclick=()=>{filters.country=b.dataset.country;filters.city='';applyFilters()});
  }
  function renderFeed(){
    const list=filteredJobs.slice(0,60);const feed=$('#sm-job-feed');
    feed.innerHTML=`<div class="sm-feed-head"><div><b>${filteredJobs.length.toLocaleString()} jobs</b><small>from saved portals · ranked for your profile</small></div><select id="sm-sort"><option value="score">Best match</option><option value="newest">Recently seen</option><option value="company">Company A–Z</option></select></div>`+ (list.length?list.map((j,i)=>{const p=locationParts(j.location);return `<article class="sm-job-card" data-index="${i}"><div class="sm-company-dot">${esc(String(j.company||'?').slice(0,1).toUpperCase())}</div><div class="sm-job-body"><div class="sm-job-line"><span class="sm-source">${esc(j.source)}</span><span class="sm-job-type">${esc(jobType(j))}</span><span class="sm-match">${Number(j.score||0)}%</span></div><h3>${esc(j.title)}</h3><b>${esc(j.company)}</b><p>${esc(p.city)} · ${esc(p.country)} · ${esc(j.remote||'Workplace not specified')}</p><div class="sm-reasons">${(j.match_reasons||[]).slice(0,3).map(esc).join(' · ')}</div></div><button class="sm-open" data-index="${i}">Apply ↗</button></article>`}).join(''):'<div class="sm-empty">No jobs match these filters. Try another country, city or role type.</div>');
    $('#sm-sort').onchange=()=>{const s=$('#sm-sort').value;filteredJobs.sort((a,b)=>s==='company'?String(a.company).localeCompare(String(b.company)):s==='newest'?new Date(b.last_seen_at||0)-new Date(a.last_seen_at||0):Number(b.score||0)-Number(a.score||0);renderFeed()};
    document.querySelectorAll('.sm-open').forEach(b=>b.onclick=()=>openJob(filteredJobs[Number(b.dataset.index)]));
  }
  function renderFilterMenu(kind){
    const menu=$('#sm-menu');let html='';
    if(kind==='type')html='<b>Role type</b><button data-v="">All jobs</button><button data-v="internship">Internship</button><button data-v="full-time">Full-time</button><button data-v="part-time">Part-time</button><button data-v="contract">Contract</button>';
    if(kind==='remote')html='<b>Workplace</b><button data-v="">All workplaces</button><button data-v="remote">Remote</button><button data-v="hybrid">Hybrid</button><button data-v="onsite">Onsite</button>';
    if(kind==='score')html='<b>Minimum match</b><button data-v="">Any score</button><button data-v="75">75%+</button><button data-v="85">85%+</button><button data-v="90">90%+</button>';
    if(kind==='source'){const src=[...new Set(jobData().map(j=>j.source).filter(Boolean))].sort();html='<b>Portal</b><button data-v="">All portals</button>'+src.map(x=>`<button data-v="${esc(x)}">${esc(x)}</button>`).join('')}
    if(kind==='location'){const countries=[...new Set(jobData().map(j=>locationParts(j.location).country))].sort();html='<b>Country</b><button data-v="">All countries</button>'+countries.map(x=>`<button data-v="${esc(x)}">${esc(x)}</button>`).join('')}
    menu.innerHTML=html;menu.classList.remove('hidden');
    menu.querySelectorAll('button').forEach(b=>b.onclick=()=>{const v=b.dataset.v;if(kind==='type')filters.type=v;if(kind==='remote')filters.remote=v;if(kind==='score')filters.score=v;if(kind==='source')filters.source=v;if(kind==='location')filters.country=v;menu.classList.add('hidden');applyFilters()});
  }
  function initControls(){
    $('#sm-search').oninput=e=>{filters.q=e.target.value.toLowerCase().trim();applyFilters()};
    $('#sm-reset').onclick=()=>{Object.keys(filters).forEach(k=>filters[k]='');$('#sm-search').value='';applyFilters()};
    document.querySelectorAll('.sm-filter').forEach(b=>b.onclick=()=>renderFilterMenu(b.dataset.filter));
    document.addEventListener('click',e=>{if(!e.target.closest('.sm-filter')&&!e.target.closest('#sm-menu'))$('#sm-menu')?.classList.add('hidden')});
  }
  async function ensureGlobe(){
    if(globeReady)return globeReady;
    globeReady=new Promise((resolve,reject)=>{
      if(window.Globe){resolve();return}
      const s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/globe.gl@2.45.7/dist/globe.gl.min.js';s.onload=resolve;s.onerror=reject;document.head.appendChild(s);
    });
    return globeReady;
  }
  function updateGlobe(){
    if(!globe)return;
    const points=[];const grouped={};
    filteredJobs.forEach(j=>{const p=locationParts(j.location);if(!p.coords)return;const key=p.coords.join(',');if(!grouped[key])grouped[key]={lat:p.coords[0],lng:p.coords[1],count:0,label:p.city, country:p.country,jobs:[]};grouped[key].count++;grouped[key].jobs.push(j)});
    Object.values(grouped).forEach(p=>points.push(p));
    globe.pointsData(points).pointLat('lat').pointLng('lng').pointAltitude(d=>Math.min(.35,.06+Math.log2(d.count+1)*.035)).pointRadius(d=>Math.min(.7,.12+Math.log2(d.count+1)*.07)).pointColor(()=>'#a78bfa').pointLabel(d=>`<b>${esc(d.label)}, ${esc(d.country)}</b><br>${d.count} matching job${d.count===1?'':'s'}`);
  }
  async function initGlobe(){
    try{await ensureGlobe();const el=document.getElementById('sm-globe');if(!el)return;globe=Globe()(el).backgroundColor('#07101f').showAtmosphere(true).atmosphereColor('#8b5cf6').atmosphereAltitude(.14).globeImageUrl('https://cdn.jsdelivr.net/npm/three-globe@2.45.2/example/img/earth-blue-marble.jpg').bumpImageUrl('https://cdn.jsdelivr.net/npm/three-globe@2.45.2/example/img/earth-topology.png').width(el.clientWidth).height(el.clientHeight).enablePointerInteraction(true).pointOfView({lat:25,lng:15,altitude:2.1},1000);globe.controls().autoRotate=true;globe.controls().autoRotateSpeed=.25;updateGlobe();window.addEventListener('resize',()=>globe.width(el.clientWidth).height(el.clientHeight));}catch(e){document.getElementById('sm-globe').innerHTML='<div class="sm-globe-fallback"><div class="sm-fallback-earth">◉</div><b>Interactive globe unavailable</b><small>Jobs are still grouped by country and city below.</small></div>'}}
  async function loadStartupMapJobs(){
    if(!ensureShell())return;
    initControls();
    try{state.jobs=await api('/api/jobs?limit=200');filteredJobs=state.jobs.slice();applyFilters();initGlobe();}
    catch(e){$('#sm-job-feed').innerHTML=`<div class="sm-empty error-text">${esc(e.message)}</div>`}
  }
  window.loadStartupMapJobs=loadStartupMapJobs;
  const originalSetView=window.setView;
  window.setView=function(view){originalSetView(view);if(view==='jobs')setTimeout(loadStartupMapJobs,0)};
  const originalLoadJobs=window.loadJobs;
  window.loadJobs=loadStartupMapJobs;
  if(location.hash==='#jobs')setTimeout(loadStartupMapJobs,200);
})();
