"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { motion } from "motion/react";
import {
  ArrowRight, Bell, Bot, BriefcaseBusiness, Building2, Check, ClipboardCheck,
  Database, FileText, Globe2, LayoutDashboard, LogOut, MapPin, Menu, MoreHorizontal,
  Play, Search, Send, Settings, ShieldCheck, Sparkles, Star, TrendingUp, Upload, Zap
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";

const nav = [
  ["dashboard", "Dashboard", LayoutDashboard], ["jobs", "Job Search", Search],
  ["portals", "All Portals", Building2], ["screening", "Portal Screening", ClipboardCheck],
  ["applications", "Applications", FileText], ["rag", "AI Resume (RAG)", Database],
  ["globe", "Globe View", Globe2], ["telegram", "Telegram", Send],
  ["analytics", "Analytics", TrendingUp], ["settings", "Settings", Settings],
] as const;

type Job = { id?: number; title?: string; company?: string; location?: string; source?: string; employment_type?: string; score?: number; remote?: string; match_reasons?: string[]; url?: string; };
type Profile = { full_name?: string; phone?: string; city?: string; country?: string; education?: string; college?: string; graduation_year?: number; experience_mode?: string; roles?: string[]; skills?: string[]; remote_modes?: string[]; preferred_countries?: string[]; excluded_countries?: string[]; india_eligibility_required?: boolean; onboarding_complete?: boolean; cv?: any };

const statCards = [
  {icon:BriefcaseBusiness,value:1248,label:"Jobs Scanned",growth:"12%",tone:"i0"},
  {icon:Send,value:86,label:"Applications Sent",growth:"25%",tone:"i1"},
  {icon:Check,value:12,label:"Interviews",growth:"50%",tone:"i2"},
  {icon:Star,value:3,label:"Offers",growth:"200%",tone:"i3"},
];

const mockJobs: Job[] = [
  {title:"Software Engineer (AI/ML)", company:"Google", location:"Bengaluru, India", source:"Top Startups", employment_type:"full-time", score:96, remote:"Hybrid", match_reasons:["AI/ML", "Python", "Strong profile fit"]},
  {title:"SDE II", company:"Microsoft", location:"Hyderabad, India", source:"Greenhouse", employment_type:"full-time", score:92, remote:"Hybrid", match_reasons:["TypeScript", "React", "Cloud"]},
  {title:"Applied Scientist", company:"Amazon", location:"Bengaluru, India", source:"Amazon", employment_type:"full-time", score:89, remote:"Onsite", match_reasons:["Machine Learning", "AWS", "Python"]},
  {title:"Research Scientist", company:"ISRO", location:"India", source:"StartupMap", employment_type:"full-time", score:87, remote:"Onsite", match_reasons:["AI", "Robotics", "Space Tech"]},
];

function initials(name?: string) { return (name || "Vijay Ramdev").split(" ").map(x=>x[0]).join("").slice(0,2).toUpperCase(); }
function normalizeJob(j: Job): Job { return {...j, score:Number(j.score||0)}; }

export default function Dashboard() {
  const [view, setView] = useState("dashboard");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [profile, setProfile] = useState<Profile>({full_name:"Vijay Ramdev", country:"India", city:"Jodhpur"});
  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState({total:1248,strong:86,queue:12});
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [assistantOpen, setAssistantOpen] = useState(false);

  async function api(path:string, options:any={}) {
    const r = await fetch(path, {credentials:"include", ...options, headers:{...(options.body instanceof FormData ? {} : {"Content-Type":"application/json"}), ...(options.headers||{})}});
    if (!r.ok) { let m=`Request failed (${r.status})`; try { const x=await r.json(); m=x.detail||m; } catch {} throw new Error(m); }
    return r.json();
  }
  async function bootstrap() {
    try {
      const x=await api("/api/auth/me"); setUser(x.user); setProfile(x.profile||{});
      const [s,j]=await Promise.all([api("/api/stats"),api("/api/jobs?limit=200")]);
      setStats({total:s.total||0,strong:s.strong||0,queue:s.queue||0}); setJobs(j.map(normalizeJob));
    } catch { /* Auth screen handles unauthenticated users. */ }
    finally { setLoading(false); }
  }
  useEffect(()=>{bootstrap()},[]);

  const filtered = useMemo(()=>jobs.filter(j=>`${j.title} ${j.company} ${j.location} ${j.source}`.toLowerCase().includes(query.toLowerCase())).slice(0,12),[jobs,query]);
  const displayJobs = jobs.length ? filtered : mockJobs;

  async function runHunt() { try { toast.loading("Scanning configured portals…", {id:"hunt"}); const x=await api("/api/hunt",{method:"POST"}); toast.success(`Found ${x.discovered||0} opportunities`,{id:"hunt"}); await bootstrap(); } catch(e:any){toast.error(e.message,{id:"hunt"})} }
  async function logout(){await api("/api/auth/logout",{method:"POST"}).catch(()=>{});setUser(null);toast.success("Signed out");}
  function openJob(j:Job){ if(j.url) window.open(j.url,"_blank","noopener,noreferrer"); else toast.info(`${j.title} · ${j.company}`); }

  if (loading) return <div className="loading-screen"><div className="orbit-loader"><span/></div><p>Booting your career command center…</p></div>;
  if (!user) return <AuthScreen onAuth={(u,p)=>{setUser(u);setProfile(p||{});bootstrap()}} api={api}/>;

  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen?"open":""}`}>
      <div className="brand"><div className="brand-mark"><Globe2 size={26}/><BriefcaseBusiness size={24}/></div><span>JOB <b>AUTOMATION</b></span></div>
      <div className="nav-label">WORKSPACE</div>
      <nav>{nav.map(([key,label,Icon])=><button key={key} className={view===key?"active":""} onClick={()=>{setView(key);setMobileOpen(false)}}><Icon size={19}/><span>{label}</span>{key==="applications"&&<em>12</em>}</button>)}</nav>
      <div className="sidebar-spacer"/>
      <div className="profile-mini"><div className="avatar">{initials(profile.full_name)}</div><div><b>{profile.full_name||"Vijay Ramdev"}</b><small>B.Tech CSE (AI & ML)</small></div><MoreHorizontal size={17}/></div>
      <div className="dream-card"><Sparkles size={18}/><div><b>Dream • Build • Automate</b><small>“Automate today. A better tomorrow.”</small></div></div>
    </aside>

    <main className="main-shell">
      <header className="topbar"><button className="mobile-menu" onClick={()=>setMobileOpen(v=>!v)}><Menu/></button><div className="global-search"><Search size={18}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search jobs, companies, or keywords…"/><kbd>Ctrl K</kbd></div><div className="top-actions"><button className="icon-button"><Bell size={19}/><i/></button><span className="pro-pill"><Star size={13} fill="currentColor"/> Pro</span><div className="top-avatar">{initials(profile.full_name).slice(0,1)}</div></div></header>

      <div className="content">
        {view==="dashboard" && <DashboardHome jobs={displayJobs} stats={stats} profile={profile} onFind={()=>setView("jobs")} onUpload={()=>setView("rag")} onOpen={openJob} onHunt={runHunt} assistantOpen={assistantOpen} setAssistantOpen={setAssistantOpen}/>} 
        {view==="jobs" && <JobsView jobs={jobs.length?jobs:mockJobs} query={query} onOpen={openJob} onHunt={runHunt}/>} 
        {view==="portals" && <PortalsView api={api}/>} 
        {view==="screening" && <ScreeningView onHunt={runHunt}/>} 
        {view==="applications" && <ApplicationsView api={api}/>} 
        {view==="rag" && <RagView api={api} profile={profile} setProfile={setProfile}/>} 
        {view==="globe" && <GlobeView jobs={jobs.length?jobs:mockJobs}/>} 
        {view==="telegram" && <TelegramView/>} 
        {view==="analytics" && <AnalyticsView stats={stats} jobs={jobs.length?jobs:mockJobs}/>} 
        {view==="settings" && <SettingsView api={api} profile={profile} setProfile={setProfile} onLogout={logout}/>} 
      </div>
    </main>
  </div>;
}

function DashboardHome({jobs,stats,profile,onFind,onUpload,onOpen,onHunt,assistantOpen,setAssistantOpen}:{jobs:Job[];stats:any;profile:Profile;onFind:()=>void;onUpload:()=>void;onOpen:(j:Job)=>void;onHunt:()=>void;assistantOpen:boolean;setAssistantOpen:(v:boolean)=>void}){
  return <>
    <section className="hero-grid"><motion.div initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} className="hero-card glass-card"><div className="hero-copy"><span className="eyebrow"><span className="pulse-dot"/> WELCOME BACK, {String(profile.full_name||"VIJAY").split(" ")[0].toUpperCase()}</span><h1>Automate Your<br/><span>Dream Career</span></h1><p>AI-powered job search, multi-portal apply, and global opportunities — all in one place.</p><div className="hero-actions"><Button onClick={onFind} className="gradient-button">Find Jobs <ArrowRight size={17}/></Button><Button onClick={onUpload} variant="outline" className="glass-button"><Upload size={17}/> Upload Your Resume</Button></div></div><div className="hero-earth"><div className="earth-glow"/><div className="earth"><div className="continent c1"/><div className="continent c2"/><div className="continent c3"/><div className="orbit orbit1"/><div className="orbit orbit2"/></div><div className="quote">“Same Effort<br/><span>More Opportunities</span>”<i/></div></div></motion.div>
      <div className="assistant-card glass-card"><div className="assistant-head"><div className="bot-face"><Bot size={25}/></div><div><b>AI Assistant</b><small><span className="online-dot"/> Online</small></div></div><div className="assistant-input"><input placeholder="Ask me anything…"/><button onClick={()=>setAssistantOpen(!assistantOpen)}><Send size={16}/></button></div><div className="chips"><button onClick={onHunt}>Find remote jobs</button><button>ATS check my resume</button><button>Top companies</button><button>Check application status</button></div>{assistantOpen&&<motion.div initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} className="assistant-pop">I can search your saved jobs, explain match scores, and guide your application queue.</motion.div>}</div>
    </section>
    <section className="stats-row">{statCards.map(({icon:I,value,label,growth,tone})=><Card key={label} className="stat-card"><div className={`stat-icon ${tone}`}><I size={19}/></div><div><strong>{label==="Jobs Scanned"?(stats.total||value):value}</strong><span>{label}</span></div><em>↑ {growth}</em></Card>)}</section>
    <section className="dashboard-grid"><Card className="featured-card"><SectionHead title="Featured Jobs For You" action="View All →"/><div className="job-list">{jobs.slice(0,4).map((j,i)=><JobRow key={i} job={j} onOpen={onOpen}/>)}</div></Card><Card className="global-card"><SectionHead title="Global Opportunities" live/><MiniWorld jobs={jobs}/><div className="world-stats"><span><b>50+</b><small>Countries</small></span><span><b>200+</b><small>Companies</small></span><span><b>10K+</b><small>Jobs Daily</small></span></div></Card></section>
    <section className="portal-strip">{["LinkedIn","Naukri","Indeed","Glassdoor","AngelList","Wellfound","Internshala","CutShort","Hirist","Shine"].map((x,i)=><div key={x} className="portal-logo"><span>{x.slice(0,2)}</span><small>{x}</small></div>)}<button>+ More</button></section>
    <section className="lower-grid"><Card><SectionHead title="Goal Progress" action="Edit"/><div className="goal"><div className="progress-ring"><span>70%</span></div><div><h3>Get Placed in 2026</h3><p>Keep going! You’re doing great.</p></div></div></Card><Card><SectionHead title="Recent Activity" action="View All"/><div className="activity">{[[Send,"Applied to Google","2 hours ago"],[FileText,"Resume scanned (98% match)","5 hours ago"],[Search,"New jobs found (42)","Today"],[ClipboardCheck,"Interview from Microsoft","1 day ago"]].map(([I,a,t])=><div key={a as string}><span>{(() => {const Icon=I as any; return <Icon size={16}/>})()}</span><div><b>{a as string}</b><small>{t as string}</small></div></div>)}</div></Card></section>
  </>;
}
function SectionHead({title,action,live}:{title:string;action?:string;live?:boolean}){return <div className="section-head"><h2>{title}</h2>{live?<span className="live-pill"><i/> Live</span>:<button>{action}</button>}</div>}
function JobRow({job,onOpen}:{job:Job;onOpen:(j:Job)=>void}){return <div className="job-row"><div className="company-logo">{String(job.company||"?").slice(0,1)}</div><div className="job-info"><div><b>{job.title}</b><small>{job.company} · {job.location||"Worldwide"} · {job.employment_type||"Full-time"}</small></div><div className="tags">{(job.match_reasons||["AI/ML","Python","Remote"]).slice(0,3).map(x=><span key={x}>{x}</span>)}</div></div><small className="age">2d ago</small><Button size="sm" onClick={()=>onOpen(job)} className="mini-apply">Apply</Button><button className="bookmark">☆</button></div>}
function MiniWorld({jobs}:{jobs:Job[]}){return <div className="mini-world"><div className="world-grid"/><div className="world-land">WORLDWIDE</div>{jobs.slice(0,8).map((j,i)=><i key={i} style={{left:`${12+(i*13)%75}%`,top:`${20+(i*17)%55}%`}}/> )}</div>}

function JobsView({jobs,query,onOpen,onHunt}:{jobs:Job[];query:string;onOpen:(j:Job)=>void;onHunt:()=>void}){const [type,setType]=useState("all");const list=jobs.filter(j=>!query||`${j.title} ${j.company} ${j.location}`.toLowerCase().includes(query.toLowerCase())).filter(j=>type==="all"||String(j.employment_type).toLowerCase().includes(type));return <div className="view-stack"><ViewTitle icon={Search} title="Job Search" subtitle="Every opportunity ranked against your profile." action={<Button onClick={onHunt} className="gradient-button"><Play size={15}/> Run All Portals</Button>}/><div className="filter-row"><div className="search-box"><Search size={16}/><input value={query} readOnly placeholder="Search jobs…"/></div>{["all","internship","full-time","contract"].map(x=><button key={x} className={type===x?"filter active":"filter"} onClick={()=>setType(x)}>{x}</button>)}</div><div className="job-cards">{list.map((j,i)=><motion.div layout key={i}><Card className="big-job"><div className="company-logo xl">{String(j.company||"?").slice(0,1)}</div><div className="big-job-main"><div className="job-line"><span>{j.source||"Portal"}</span><b>{j.score||0}% Match</b></div><h3>{j.title}</h3><p>{j.company} · {j.location||"Worldwide"} · {j.employment_type||"Full-time"}</p><div className="tags">{(j.match_reasons||[]).map(x=><span key={x}>{x}</span>)}</div></div><Button onClick={()=>onOpen(j)} className="gradient-button">Apply</Button></Card></motion.div>)}</div></div>}
function ViewTitle({icon:Icon,title,subtitle,action}:{icon:any;title:string;subtitle:string;action?:ReactNode}){return <div className="view-title"><div><span className="eyebrow"><Icon size={14}/> CAREER OS</span><h1>{title}</h1><p>{subtitle}</p></div>{action}</div>}

function PortalsView({api}:{api:any}){const [items,setItems]=useState<any[]>([]);useEffect(()=>{api("/api/portals").then(setItems).catch(()=>{})},[]);return <div className="view-stack"><ViewTitle icon={Building2} title="All Portals" subtitle="One command center across your configured job sources."/><div className="portal-grid-new">{(items.length?items:["LinkedIn","Naukri","Indeed","Wellfound","Startup Jobs","Top Startups","The Hub","StartupMap"]).map((p:any,i)=><Card key={i} className="portal-card-new"><div className="portal-icon"><Globe2 size={21}/></div><div><h3>{p.name||p}</h3><p>{p.description||"Job discovery and profile matching"}</p></div><span className="portal-count">{p.job_count||"—"}</span><button onClick={()=>p.url&&window.open(p.url,"_blank")}>Open <ArrowRight size={14}/></button></Card>)}</div></div>}
function ScreeningView({onHunt}:{onHunt:()=>void}){return <div className="view-stack"><ViewTitle icon={ClipboardCheck} title="Portal Screening" subtitle="Run source-aware discovery and rank every role before you apply." action={<Button onClick={onHunt} className="gradient-button"><Zap size={15}/> Screen Everything</Button>}/><Card className="screen-hero"><div><span className="eyebrow">AUTOMATION PIPELINE</span><h2>Discover → Match → Prepare → Approve</h2><p>Human approval stays in control. The engine handles repetitive research, ranking and resume intelligence.</p></div><div className="pipeline">{[Search,Sparkles,FileText,ShieldCheck].map((I,i)=><div key={i}><span><I/></span><b>{["Discover","Match","Prepare","Approve"][i]}</b>{i<3&&<ArrowRight/>}</div>)}</div></Card></div>}
function ApplicationsView({api}:{api:any}){const [items,setItems]=useState<any[]>([]);useEffect(()=>{api("/api/applications").then(setItems).catch(()=>{})},[]);return <div className="view-stack"><ViewTitle icon={FileText} title="Applications" subtitle="Review every prepared application before submission."/><div className="application-list">{(items.length?items:mockJobs.slice(0,3).map((j,i)=>({title:j.title,company:j.company,status:["review","ready","submitted"][i],source:j.source,url:j.url}))).map((a,i)=><Card key={i} className="application-card"><div className="company-logo">{String(a.company||"?").slice(0,1)}</div><div><span className="status-badge">{a.status||"review"}</span><h3>{a.title}</h3><p>{a.company} · {a.source||"Portal"}</p></div><Button variant="outline" onClick={()=>a.url&&window.open(a.url,"_blank")}>Review <ArrowRight size={15}/></Button></Card>)}</div></div>}
function RagView({api,profile,setProfile}:{api:any;profile:Profile;setProfile:(p:Profile)=>void}){const [uploading,setUploading]=useState(false);async function upload(file:File){setUploading(true);try{const fd=new FormData();fd.append("file",file);const x=await api("/api/profile/cv",{method:"POST",body:fd});setProfile({...profile,cv:x.cv});toast.success("Resume saved to your private Neon profile")}catch(e:any){toast.error(e.message)}finally{setUploading(false)}}return <div className="view-stack"><ViewTitle icon={Database} title="AI Resume (RAG)" subtitle="Turn your resume into a private evidence layer for matching and applications."/><div className="rag-grid"><Card className="upload-card"><div className="drop-zone"><div className="upload-icon"><Upload/></div><h2>Upload your resume</h2><p>PDF, DOCX, TXT or MD · up to 10 MB</p><label><input type="file" accept=".pdf,.docx,.txt,.md" onChange={e=>e.target.files?.[0]&&upload(e.target.files[0])}/>{uploading?"Processing…":"Choose Resume"}</label></div></Card><Card><span className="eyebrow">KNOWLEDGE BASE</span><h2>Resume intelligence</h2><div className="rag-items"><div><Check/><span><b>CV stored per user</b><small>{profile.cv?.filename||"No resume uploaded"}</small></span></div><div><Sparkles/><span><b>Semantic match layer</b><small>Skills, projects, evidence and role fit</small></span></div><div><ShieldCheck/><span><b>Approval-first applications</b><small>No autonomous submission without your review</small></span></div></div></Card></div></div>}
function GlobeView({jobs}:{jobs:Job[]}){return <div className="view-stack"><ViewTitle icon={Globe2} title="Global Opportunities" subtitle="Explore jobs by country, city and workplace mode."/><Card className="globe-page"><div className="big-globe"><div className="big-earth"/><div className="latitude l1"/><div className="latitude l2"/><div className="longitude lo1"/><div className="longitude lo2"/>{jobs.slice(0,15).map((j,i)=><i key={i} style={{left:`${8+(i*17)%84}%`,top:`${14+(i*11)%72}%`}}/> )}</div><div className="country-feed">{["India","United States","United Kingdom","Germany","Canada","Singapore"].map((c)=><div key={c}><MapPin size={15}/><b>{c}</b><span>{Math.max(3, jobs.filter(j=>String(j.location).toLowerCase().includes(c.toLowerCase())).length*7)} jobs</span></div>)}</div></Card></div>}
function TelegramView(){return <div className="view-stack"><ViewTitle icon={Send} title="Telegram Alerts" subtitle="Keep your job hunt visible wherever you are."/><Card className="telegram-card"><div className="telegram-icon"><Send/></div><div><h2>Telegram automation</h2><p>Connect your bot and receive high-match roles, screening summaries and application reminders.</p><div className="telegram-status"><span className="online-dot"/> Waiting for connection</div></div><Button className="gradient-button">Configure</Button></Card></div>}
function AnalyticsView({stats,jobs}:{stats:any;jobs:Job[]}){const avg=Math.round(jobs.reduce((a,j)=>a+(j.score||0),0)/(jobs.length||1));return <div className="view-stack"><ViewTitle icon={TrendingUp} title="Analytics" subtitle="Understand where your job-search engine is creating leverage."/><div className="analytics-grid">{[["Match quality",`${avg}%`,`+8% this week`],["Portal coverage","9","active sources"],["Daily opportunities","42","new roles"],["Goal progress","70%","placement target"]].map(([a,b,c])=><Card key={a} className="analytic-card"><small>{a}</small><strong>{b}</strong><span>{c}</span><div className="sparkline"><i/><i/><i/><i/><i/></div></Card>)}</div><Card><SectionHead title="Search momentum" action="Last 30 days"/><div className="chart"><div className="chart-fill"/><div className="chart-line"/></div></Card></div>}
function SettingsView({api,profile,setProfile,onLogout}:{api:any;profile:Profile;setProfile:(p:Profile)=>void;onLogout:()=>void}){const [p,setP]=useState(profile);async function save(e:any){e.preventDefault();try{const x=await api("/api/profile",{method:"PUT",body:JSON.stringify({...p,roles:String(p.roles||[]).split(",").map((x:string)=>x.trim()).filter(Boolean),skills:String(p.skills||[]).split(",").map((x:string)=>x.trim()).filter(Boolean)})});setProfile(x);setP(x);toast.success("Preferences saved")}catch(e:any){toast.error(e.message)}}return <div className="view-stack"><ViewTitle icon={Settings} title="Settings" subtitle="Tune the engine to your next role."/><div className="settings-grid"><Card><form className="settings-form" onSubmit={save}>{[["full_name","Full name"],["phone","Phone"],["city","City"],["country","Country"],["education","Education"],["college","College"],["roles","Target roles"],["skills","Skills"],["remote_modes","Remote preference"]].map(([k,l])=><label key={k}>{l}<input value={Array.isArray((p as any)[k])?(p as any)[k].join(", "):(p as any)[k]||""} onChange={e=>setP({...p,[k]:e.target.value})}/></label>)}<button className="gradient-button" type="submit">Save Preferences</button></form></Card><Card><span className="eyebrow">ACCOUNT</span><div className="account-block"><div className="top-avatar">{initials(p.full_name).slice(0,1)}</div><div><h3>{p.full_name||"Vijay Ramdev"}</h3><p>Private career workspace</p></div></div><button className="logout-button" onClick={onLogout}><LogOut size={16}/> Sign out</button></Card></div></div>}

function AuthScreen({onAuth,api}:{onAuth:(u:any,p:any)=>void;api:any}){const [create,setCreate]=useState(false);const [email,setEmail]=useState("");const [password,setPassword]=useState("");const [busy,setBusy]=useState(false);async function submit(e:any){e.preventDefault();setBusy(true);try{const x=await api(create?"/api/auth/register":"/api/auth/login",{method:"POST",body:JSON.stringify({email,password})});onAuth(x.user,x.profile);toast.success(create?"Workspace created":"Welcome back") }catch(e:any){toast.error(e.message)}finally{setBusy(false)}}return <div className="auth-page"><div className="auth-orbit"/><div className="auth-card glass-card"><div className="brand centered"><div className="brand-mark"><Globe2 size={26}/><BriefcaseBusiness size={24}/></div><span>JOB <b>AUTOMATION</b></span></div><span className="eyebrow"><Sparkles size={13}/> AI CAREER OPERATING SYSTEM</span><h1>{create?"Build your career command center":"Welcome back"}</h1><p>AI-powered discovery, resume intelligence and application preparation in one private workspace.</p><form onSubmit={submit}><input type="email" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} required/><input type="password" placeholder="Password (8+ characters)" value={password} onChange={e=>setPassword(e.target.value)} minLength={8} required/><Button disabled={busy} className="gradient-button">{busy?"Starting…":create?"Create account":"Sign in"} <ArrowRight size={16}/></Button></form><button className="switch-auth" onClick={()=>setCreate(v=>!v)}>{create?"Already have an account? Sign in":"Create an account"}</button></div></div>}
