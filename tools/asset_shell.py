#!/usr/bin/env python3
"""Give btc-dashboard.html and ada-dashboard.html the same app shell as the Robinhood pages.

    python3 tools/asset_shell.py

UI/UX only. The heatmap, the volatility cone, the Context Layer bands, the weekly Wyckoff
panel, the scenario panel, every tooltip and every number keep their own code. The shell:
  * injects one <style> block (sidebar, sticky top bar, page header, the site palette and fonts),
  * injects one <script> block that groups the page's existing blocks into sidebar pages and
    adds three read-only views built from values the page already holds — a KPI strip, the
    level ladder as a table, and (ADA) the cone as a month-by-month table — using the page's own
    price[], levelLines, levelZones, coneDays(), conePct() and coneProbs(),
  * hides prose: the meta line and long legend sentences (colour keys stay).
Idempotent: running it again replaces the previous shell.
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link id="cre-shell-fonts" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">')

CSS = r'''<style id="cre-shell">
/* ── CRE shell: site palette + sidebar app around the original dashboard ── */
:root:not([data-theme="light"]){--bg:#090d12;--bg2:#111820;--card:#111820;--bord:rgba(173,191,211,.13);--txt:#edf2f5;--txt2:#8d9baa;
  --btn-bg:#17212b;--tt-bg:#17212b;--tt-bord:rgba(173,191,211,.24);--mint:#54d6b4;--p2:#17212b;--p3:#1c2934;--line2:rgba(173,191,211,.22);--t3:#5f6e7d;--good:#62d9a2;--bad:#f0787f}
:root[data-theme="light"]{--bg:#edf1ef;--bg2:#ffffff;--card:#ffffff;--bord:rgba(25,40,45,.11);--txt:#162229;--txt2:#60717b;
  --btn-bg:#f4f7f5;--mint:#087d68;--p2:#f4f7f5;--p3:#e9efec;--line2:rgba(25,40,45,.18);--t3:#8c9aa0;--good:#148354;--bad:#c43c46}
:root{--sans:"Be Vietnam Pro",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;--mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
body{display:grid;grid-template-columns:232px minmax(0,1fr);padding:0;min-height:100vh;font-family:var(--sans);-webkit-font-smoothing:antialiased}
.wrap{max-width:1400px;width:100%;margin:0;padding:0 22px 40px;min-width:0}
.wrap>.nav,.wrap>h1,.wrap>.meta,.sh-hide,.sh-off{display:none!important}
.chart-card{border-radius:12px;border-color:var(--bord)}
.controls{margin:12px 0}
.ctrl-group{border-radius:10px;border-color:var(--bord)}
button.toggle,button.zoom-btn,.theme-toggle,a.zoom-btn{border-radius:7px!important;font-family:var(--mono)!important;font-size:10.5px!important}
button.toggle.active{background:color-mix(in srgb,var(--mint) 14%,var(--btn-bg));color:var(--mint);border-color:color-mix(in srgb,var(--mint) 40%,transparent)}
button.zoom-btn.active{background:var(--mint);color:var(--bg);border-color:var(--mint)}
.ctrl-label,.legend-row{font-family:var(--mono)}
.legend-row{font-size:10.5px}
.wyk-sec{border-top:0;margin-top:0;padding-top:0}
.sh-side{position:sticky;top:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column;gap:14px;padding:18px 12px 14px;
  border-right:1px solid var(--bord);background:linear-gradient(180deg,var(--card),color-mix(in srgb,var(--card) 92%,var(--bg)))}
.sh-brand{display:flex;align-items:center;gap:10px;padding:0 8px 14px;border-bottom:1px solid var(--bord);text-decoration:none;color:var(--txt)}
.sh-brand .mk{width:34px;height:34px;border-radius:9px;display:grid;place-items:center;flex:none;background:var(--mint);color:var(--bg);font:700 13px var(--mono)}
.sh-brand .mk img{width:20px;height:20px;object-fit:contain;filter:brightness(0) invert(1)}
:root[data-theme="light"] .sh-brand .mk img{filter:brightness(0) invert(1)}
.sh-brand b{display:block;font:700 11px/1.35 var(--mono);letter-spacing:.08em;text-transform:uppercase}
.sh-brand b em{font-style:normal;color:var(--mint)}
.sh-brand small{display:block;font-size:10px;color:var(--txt2)}
.sh-lbl{font:700 9.5px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--t3);padding:0 10px 5px;margin-top:4px}
.sh-nav{display:flex;flex-direction:column;gap:3px}
.sh-ni{display:flex;align-items:center;gap:11px;padding:8px 11px;border-radius:9px;border:1px solid transparent;color:var(--txt2);
  text-decoration:none;font-size:12.5px;font-weight:600}
.sh-ni svg{width:16px;height:16px;flex:none;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;opacity:.8}
.sh-ni:hover{background:var(--p2);color:var(--txt)}
.sh-ni[aria-current="page"]{color:var(--mint);background:color-mix(in srgb,var(--mint) 10%,var(--p2));border-color:color-mix(in srgb,var(--mint) 28%,transparent)}
.sh-ni .c{margin-left:auto;font:600 9.5px var(--mono);padding:2px 6px;border-radius:5px;background:var(--p3);color:var(--txt2)}
.sh-sp{flex:1}
.sh-state{padding:11px;border:1px solid var(--bord);border-radius:10px;background:var(--p2);font-size:10.5px;color:var(--txt2)}
.sh-state b{display:flex;justify-content:space-between;font:700 9.5px var(--mono);letter-spacing:.14em;text-transform:uppercase;margin-bottom:4px}
.sh-state b span{color:var(--txt)}
.sh-btns{display:flex;gap:6px}
.sh-btn{flex:1;display:inline-flex;justify-content:center;align-items:center;padding:7px 9px;border-radius:8px;border:1px solid var(--bord);
  background:transparent;color:var(--txt2);font:600 11px var(--mono);cursor:pointer;text-decoration:none;white-space:nowrap}
.sh-btn:hover{color:var(--txt);border-color:var(--mint)}
.sh-top{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:12px;flex-wrap:wrap;min-height:56px;margin:0 -22px;padding:10px 22px;
  border-bottom:1px solid var(--bord);background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
.sh-top strong{font:700 11.5px var(--mono);letter-spacing:.1em;text-transform:uppercase}
.sh-top .ctx{font-size:11px;color:var(--txt2)}
.sh-top .sp{flex:1}
.sh-chip{display:inline-flex;align-items:center;gap:7px;font:600 10px var(--mono);letter-spacing:.06em;color:var(--txt2);border:1px solid var(--line2);border-radius:8px;padding:6px 9px;white-space:nowrap}
.sh-chip i{width:6px;height:6px;border-radius:50%;background:var(--mint)}
.sh-tabs{display:none}
.sh-ph{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin:18px 0 12px}
.sh-ph .e{font:700 10px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--txt2)}
.sh-ph h2{font-size:24px;font-weight:700;letter-spacing:-.035em;line-height:1.15;margin:4px 0 0}
.sh-ph h2 em{font-style:normal;color:var(--mint)}
.sh-ph .r{font:600 10px var(--mono);letter-spacing:.08em;color:var(--txt2);text-align:right;line-height:1.7;white-space:nowrap}
.sh-kpis{display:grid;grid-template-columns:1.3fr repeat(4,minmax(0,1fr));gap:8px;margin-bottom:4px}
.sh-k{background:var(--card);border:1px solid var(--bord);border-radius:10px;padding:11px 13px;min-width:0}
.sh-k .k{font:700 9.5px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--txt2)}
.sh-k .v{font:600 20px var(--mono);letter-spacing:-.03em;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sh-k .v.big{font-size:27px}
.sh-k .s{font:500 10.5px var(--mono);color:var(--txt2);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sh-up{color:var(--good)}.sh-dn{color:var(--bad)}
.sh-panel{background:var(--card);border:1px solid var(--bord);border-radius:12px;overflow:hidden}
.sh-pt{display:flex;justify-content:space-between;align-items:baseline;gap:12px;padding:12px 14px;border-bottom:1px solid var(--bord)}
.sh-pt h3{font:700 10.5px var(--mono);letter-spacing:.14em;text-transform:uppercase;margin:0}
.sh-pt .m{font:500 10px var(--mono);color:var(--txt2)}
.sh-tbl{width:100%;border-collapse:collapse;font-size:12.5px}
.sh-tbl th{font:700 9.5px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--t3);text-align:right;padding:9px 12px;border-bottom:1px solid var(--bord);white-space:nowrap}
.sh-tbl td{padding:10px 12px;text-align:right;border-bottom:1px solid var(--bord);white-space:nowrap;font-family:var(--mono);font-size:12px}
.sh-tbl th:first-child,.sh-tbl td:first-child{text-align:left;padding-left:14px}
.sh-tbl td.l{text-align:left;font-family:var(--sans);white-space:normal}
.sh-tbl tr.r{cursor:pointer}.sh-tbl tr.r:hover td{background:var(--p2)}
.sh-tbl tr.cur td{background:color-mix(in srgb,var(--mint) 8%,transparent)}
.sh-tbl tr.x td{white-space:normal;text-align:left;font-family:var(--sans);font-size:12px;color:var(--txt2);background:var(--p2);padding:4px 14px 12px}
.sh-sw{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:7px;vertical-align:-1px}
.sh-tier{font:700 9px var(--mono);letter-spacing:.06em;border:1px solid var(--line2);border-radius:5px;padding:1px 5px;color:var(--txt2)}
.sh-bk{display:flex;height:8px;border-radius:4px;overflow:hidden;min-width:120px;background:var(--p3)}
.sh-bk i{display:block;height:100%}
@media (max-width:1100px){.sh-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:860px){
  body{display:block}
  .sh-side{display:none}
  .wrap{padding:0 12px 34px}
  .sh-top{margin:0 -12px;padding:10px 12px 0}
  .sh-top .ctx{display:none}
  .sh-tabs{display:block;flex:0 0 calc(100% + 24px);min-width:0;max-width:calc(100% + 24px);margin:6px -12px 0;overflow-x:auto;scrollbar-width:none;border-top:1px solid var(--bord)}
  .sh-tabs::-webkit-scrollbar{display:none}
  .sh-tabs .in{display:flex;gap:4px;padding:7px 12px;width:max-content}
  .sh-tabs .sh-ni{padding:7px 10px;font-size:12px;white-space:nowrap}
  .sh-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
  .sh-kpis .sh-k:first-child{grid-column:span 2}
  .sh-ph h2{font-size:21px}.sh-ph .r{display:none}
  .sh-tbl .hs{display:none}
  .ctrl-group{flex-wrap:wrap;max-width:100%}
  .sc-tab{display:block;overflow-x:auto;max-width:100%}
}
</style>'''

JS = r'''<script id="cre-shell-js">
/* CRE shell — layout and read-only views. Reads the page's own globals; computes nothing new
   except distances from the month-to-date close and the cone table the page's cone functions return. */
(function(){
  const q=s=>document.querySelector(s), wrap=q('.wrap'); if(!wrap) return;
  const ASSET=document.body.dataset.asset;
  // language: one site-wide key (cre-lang), overridable with ?lang=en|vi; EN swaps the interface only
  const LANG=(()=>{ const u=new URLSearchParams(location.search).get('lang'); if(u==='en'||u==='vi'){ try{localStorage.setItem('cre-lang',u);}catch(e){} return u; }
    try{return localStorage.getItem('cre-lang')==='en'?'en':'vi';}catch(e){return 'vi';} })();
  const TT=(vi,en)=>LANG==='en'?en:vi;
  document.documentElement.lang=LANG;
  const isADA=ASSET==='ADA';
  const M=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const cur=currentIdx, close=price[cur], prev=price[cur-1], mo=months[cur];
  // ADA levels are quoted to 5 significant digits ($0.14454, $0.13337); BTC to whole dollars
  const fmt=v=>v==null?'—':(isADA?'$'+String(+v.toPrecision(5)):'$'+Math.round(v).toLocaleString('en-US'));
  const sgn=(v,d=2)=>(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(d)+'%';
  const cls=v=>v>0?'sh-up':v<0?'sh-dn':'';
  const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const block=wyckoff.find(b=>cur>=b.s&&cur<b.e)||{};
  const KIND={acc:'Accumulation',markup:'Markup',dist:'Distribution',markdown:'Markdown'};
  const mchg=prev?(close/prev-1)*100:null;

  // ── level ladder: lines + zones, ordered by price ──
  const KL=LANG==='en'?{res:'Resistance',sup:'Support',gate:'Trigger',ema:'Average',zone:'Zone',dist:'Supply',hard:'Stop',entry:'Entry'}
                     :{res:'Kháng cự',sup:'Hỗ trợ',gate:'Ngưỡng',ema:'Trung bình',zone:'Vùng',dist:'Cung',hard:'Dừng lỗ',entry:'Vào lệnh'};
  const rows=[...levelLines.map(L=>({p:L.p,lo:L.p,hi:L.p,kind:L.kind,tier:L.tier,tag:L.tag,label:L.label,zone:false})),
              ...levelZones.map(Z=>({p:(Z.lo+Z.hi)/2,lo:Z.lo,hi:Z.hi,kind:Z.kind,tier:Z.tier,tag:Z.tag,label:Z.label,zone:true}))].sort((a,b)=>b.hi-a.hi);
  const above=levelLines.filter(L=>L.p>close).sort((a,b)=>a.p-b.p)[0], below=levelLines.filter(L=>L.p<close).sort((a,b)=>b.p-a.p)[0];
  const clean=t=>String(t).replace(/\s*·\s*[+−-]?\d[\d.,]*%.*$/,'');

  // ── pages: existing blocks + generated views ──
  const legends=[...wrap.querySelectorAll(':scope>.legend-row')];
  const secs=[...wrap.querySelectorAll(':scope>.wyk-sec')];
  const kpi=document.createElement('div'); kpi.className='sh-kpis';
  const fngV=(typeof fng!=='undefined'&&fng)?fng[cur]:null;
  let coneK='';
  if(isADA&&typeof coneProbs==='function'){ const pr=coneProbs(cur); if(pr){ const u=Math.round(pr.bull*100), d=Math.round(pr.bear*100);
    coneK=`<div class="sh-k"><div class="k">Cone ${M[mo.m]}</div><div class="v">${u} / ${100-u-d} / ${d}</div><div class="s">${TT('lên · giữa · xuống ±25%','up · within · down ±25%')}</div></div>`; } }
  kpi.innerHTML=`
    <div class="sh-k"><div class="k">Close ${M[mo.m]} ${mo.y} · MTD</div><div class="v big">${fmt(close)}</div><div class="s"><span class="${cls(mchg)}">${mchg==null?'—':sgn(mchg)}</span> ${TT('so với close','vs close')} ${M[months[cur-1].m]}</div></div>
    <div class="sh-k"><div class="k">Wyckoff</div><div class="v">${KIND[block.kind]||'—'}</div><div class="s">${M[mo.m]} · ${TT('đang chạy','in progress')}</div></div>
    <div class="sh-k"><div class="k">${TT('Mức gần trên','Nearest above')}</div><div class="v">${above?fmt(above.p):'—'}</div><div class="s">${above?`<span class="sh-up">${sgn((above.p/close-1)*100)}</span> · ${esc(clean(above.tag))}`:''}</div></div>
    <div class="sh-k"><div class="k">${TT('Mức gần dưới','Nearest below')}</div><div class="v">${below?fmt(below.p):'—'}</div><div class="s">${below?`<span class="sh-dn">${sgn((below.p/close-1)*100)}</span> · ${esc(clean(below.tag))}`:''}</div></div>
    ${coneK||`<div class="sh-k"><div class="k">Fear &amp; Greed</div><div class="v">${fngV==null?'—':fngV}</div><div class="s">${M[mo.m]} ${mo.y} · ${TT('trọng số 0','zero weight')}</div></div>`}`;
  wrap.insertBefore(kpi, q('.wrap>.controls'));

  const lad=document.createElement('section'); lad.className='sh-panel';
  lad.innerHTML=`<div class="sh-pt"><h3>${TT('Thang mức giá','Level ladder')}</h3><div class="m">${rows.length} ${TT('mức · khoảng cách so với close','levels · distance from close')} ${M[mo.m]} ${fmt(close)}</div></div>
    <div style="overflow-x:auto"><table class="sh-tbl"><thead><tr><th>${TT('Mức','Level')}</th><th>${TT('Loại','Type')}</th><th class="hs">Tier</th><th>${TT('Khoảng cách','Distance')}</th><th style="text-align:left">${TT('Nhãn','Tag')}</th></tr></thead><tbody>${
    rows.map((r,i)=>{ const ref=r.zone?(close>r.hi?r.hi:close<r.lo?r.lo:close):r.p, d=(ref/close-1)*100, inside=r.zone&&close>=r.lo&&close<=r.hi;
      const col=getComputedStyle(document.documentElement).getPropertyValue('--txt2');
      return `<tr class="r${inside?' cur':''}" tabindex="0" data-i="${i}"><td>${r.zone?fmt(r.lo)+' – '+fmt(r.hi):fmt(r.p)}</td>
        <td style="text-align:right"><span class="sh-sw" style="background:${lvlColor(r.kind)}"></span>${KL[r.kind]||r.kind}${r.zone?TT(' · vùng',' · zone'):''}</td>
        <td class="hs"><span class="sh-tier">T${r.tier}</span></td><td class="${inside?'':cls(d)}">${inside?TT('trong vùng','inside'):sgn(d)}</td><td class="l">${esc(r.tag)}</td></tr>
        <tr class="x" hidden data-x="${i}"><td colspan="5">${esc(r.label)}</td></tr>`; }).join('')}</tbody></table></div>`;
  lad.addEventListener('click',e=>{ const r=e.target.closest('tr.r'); if(!r) return; const x=lad.querySelector(`tr[data-x="${r.dataset.i}"]`); x.hidden=!x.hidden; });
  lad.addEventListener('keydown',e=>{ const r=e.target.closest('tr.r'); if(r&&e.key==='Enter'){ const x=lad.querySelector(`tr[data-x="${r.dataset.i}"]`); x.hidden=!x.hidden; } });
  wrap.appendChild(lad);

  let cone=null;
  if(isADA&&typeof conePct==='function'){
    cone=document.createElement('section'); cone.className='sh-panel';
    const zi=typeof Z_IN!=='undefined'?Z_IN:0.6745, zo=typeof Z_OUT!=='undefined'?Z_OUT:1.6449;
    const rr=[]; for(let i=trajStart;i<N;i++){ const pr=coneProbs(i); if(!pr) continue; const u=Math.round(pr.bull*100), d=Math.round(pr.bear*100);
      rr.push({i,m:months[i],t:coneDays(i),p5:conePct(i,-zo),p25:conePct(i,-zi),p75:conePct(i,zi),p95:conePct(i,zo),u,w:100-u-d,d}); }
    const f4=v=>'$'+v.toFixed(4);
    cone.innerHTML=`<div class="sh-pt"><h3>${TT('Cone theo tháng','Cone by month')}</h3><div class="m">${TT('neo','anchor')} ${fmt(CONE_SPOT)} · σ ${(CONE_SIGMA_D*100).toFixed(4)}%/${TT('ngày','day')} · ${TT('ngưỡng','thresholds')} ±25%</div></div>
      <div style="overflow-x:auto"><table class="sh-tbl"><thead><tr><th>${TT('Tháng','Month')}</th><th class="hs">${TT('Ngày','Days')}</th><th>5th</th><th>25th</th><th>75th</th><th>95th</th><th>${TT('Lên / giữa / xuống','Up / within / down')}</th><th class="hs"></th></tr></thead><tbody>${
      rr.map(r=>`<tr${r.i===cur?' class="cur"':''}><td>${M[r.m.m]} ${r.m.y}</td><td class="hs">${r.t}</td><td>${f4(r.p5)}</td><td>${f4(r.p25)}</td><td>${f4(r.p75)}</td><td>${f4(r.p95)}</td>
        <td>${r.u} / ${r.w} / ${r.d}</td><td class="hs"><div class="sh-bk"><i style="width:${r.u}%;background:var(--good)"></i><i style="width:${r.w}%;background:var(--p3)"></i><i style="width:${r.d}%;background:var(--bad)"></i></div></td></tr>`).join('')}</tbody></table></div>`;
    wrap.appendChild(cone);
  }

  const heat=[kpi,q('.wrap>.controls'),q('.wrap>.chart-card'),...legends];
  const P=[{k:'heatmap',t:'Heatmap',nodes:heat,e:TT('Heatmap tháng / ','Monthly heatmap / ')+ASSET,h:TT(`${ASSET} <em>theo chu kỳ</em>`,`${ASSET} <em>through the cycle</em>`),i:'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16M15 4v16"/>'},
           {k:'levels',t:TT('Mức giá','Levels'),nodes:[lad],e:'Level ladder / '+ASSET,h:TT(`Thang <em>mức giá</em>`,`Level <em>ladder</em>`),c:String(rows.length),i:'<path d="M4 6h16M4 12h10M4 18h6"/>'}];
  if(cone) P.push({k:'cone',t:'Cone',nodes:[cone],e:'Volatility cone / ADA',h:TT(`Cone <em>biến động</em>`,`Volatility <em>cone</em>`),c:'26T',i:'<path d="M3 12h18"/><path d="M3 12l18-8M3 12l18 8"/>'});
  if(secs[0]) P.push({k:'weekly',t:TT('Wyckoff tuần','Weekly Wyckoff'),nodes:[secs[0]],e:'Wyckoff / weekly',h:TT(`Chu kỳ <em>Wyckoff</em> tuần`,`Weekly <em>Wyckoff</em> cycle`),c:'Nov 5',i:'<path d="M3 17l5-6 4 3 4-7 5 5"/>'});
  if(secs[1]) P.push({k:'scenario',t:TT('Kịch bản 14N','14-day scenarios'),nodes:[secs[1]],e:'Range test / scenarios',h:TT(`Kịch bản <em>7–14 ngày</em>`,`<em>7–14 day</em> scenarios`),c:'Nov 5',i:'<path d="M3 12h6l3-6 3 12 3-6h3"/>'});
  const all=P.flatMap(p=>p.nodes).filter(Boolean);

  // ── prose: hide long legend sentences and analysis notes; colour keys stay ──
  wrap.querySelectorAll('.legend-row > span, .legend-row > div').forEach(sp=>{ const t=sp.textContent.trim(); if(t.length>70 || /levels:$/.test(t)) sp.classList.add('sh-hide'); });
  wrap.querySelectorAll('.legend-row').forEach(r=>{ if(![...r.children].some(c=>!c.classList.contains('sh-hide')&&c.textContent.trim()&&!/:$/.test(c.textContent.trim()))) r.classList.add('sh-hide'); });
  wrap.querySelectorAll('.sc-note,.src-note,.analysis,.hint').forEach(n=>n.classList.add('sh-hide'));
  const rep=q('.wrap .controls a.zoom-btn[href*="report"],.wrap .controls a.zoom-btn[href*="monthly_map"]'), repHref=rep?rep.getAttribute('href'):null;
  if(rep) rep.closest('.ctrl-group').classList.add('sh-hide');
  const tt=q('#themeToggle'); if(tt) tt.closest('.ctrl-group').classList.add('sh-hide');   // theme lives in the sidebar now

  // ── sidebar, top bar, page header ──
  const link=p=>`<a class="sh-ni" href="#${p.k}" data-k="${p.k}"><svg viewBox="0 0 24 24" aria-hidden="true">${p.i}</svg><span>${p.t}</span>${p.c?`<span class="c">${p.c}</span>`:''}</a>`;
  const ext=(h,t,i,c,curA)=>`<a class="sh-ni" href="${h}"${curA?' aria-current="page"':''}><svg viewBox="0 0 24 24" aria-hidden="true">${i}</svg><span>${t}</span>${c?`<span class="c">${c}</span>`:''}</a>`;
  const IC={btc:'<path d="M12 3v18M7 7h7a3 3 0 010 6H7h8a3 3 0 010 6H7"/>',ada:'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2"/>',
    pf:'<path d="M3 13h4v8H3zM10 9h4v12h-4zM17 4h4v17h-4z"/>',sig:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12l6-6"/>',rep:'<path d="M6 3h9l3 3v15H6z"/><path d="M9 11h6M9 15h6"/>'};
  const side=document.createElement('aside'); side.className='sh-side'; side.setAttribute('aria-label',TT('Điều hướng','Navigation'));
  const mark=isADA?'<img src="cardano-logo.svg" alt="">':'₿';
  side.innerHTML=`<a class="sh-brand" href="index.html" title="${TT('Về trang chủ CRE','Back to the CRE home page')}"><span class="mk">${mark}</span><span><b>${isADA?'Cardano':'Bitcoin'}<br><em>Framework</em></b><small>${TT('CRE · heatmap tháng','CRE · monthly heatmap')}</small></span></a>
    <div><div class="sh-lbl">${ASSET}</div><nav class="sh-nav">${P.map(link).join('')}${repHref?ext(repHref,isADA?'Monthly map':'Market GPS',IC.rep,'↗'):''}</nav></div>
    <div><div class="sh-lbl">${TT('Tài sản','Assets')}</div><nav class="sh-nav">${ext('btc-dashboard.html','Bitcoin',IC.btc,'',!isADA)}${ext('ada-dashboard.html','Cardano',IC.ada,'',isADA)}</nav></div>
    <div><div class="sh-lbl">Robinhood Chain</div><nav class="sh-nav">${ext('robinhood.html',TT('Danh mục','Portfolio'),IC.pf,'↗')}${ext('ro-signals.html',TT('Rổ tín hiệu','Signal basket'),IC.sig,'↗')}</nav></div>
    <div class="sh-sp"></div>
    <div class="sh-state"><b>${TT('Dữ liệu','Data')} <span>${M[mo.m]} ${mo.y} MTD</span></b>${fmt(close)} · ${KIND[block.kind]||''}</div>
    <div class="sh-btns"><a class="sh-btn" href="index.html">${TT('← Trang chủ','← Home')}</a><button class="sh-btn" type="button" data-lang>${LANG==='en'?'VI':'EN'}</button><button class="sh-btn" type="button" data-proxy="themeToggle" aria-label="${TT('Đổi giao diện sáng / tối','Toggle light / dark')}">◐</button></div>`;
  document.body.insertBefore(side,document.body.firstChild);
  const top=document.createElement('header'); top.className='sh-top';
  top.innerHTML=`<strong id="shTitle"></strong><span class="ctx">${isADA?'Cardano':'Bitcoin'} · CRE framework</span><span class="sp"></span>
    <span class="sh-chip"><i></i>${M[mo.m].toUpperCase()} ${mo.y} · MTD ${fmt(close)}</span>
    <button class="sh-btn" type="button" data-lang style="flex:none">${LANG==='en'?'VI':'EN'}</button><button class="sh-btn" type="button" data-proxy="themeToggle" aria-label="${TT('Đổi giao diện sáng / tối','Toggle light / dark')}" style="flex:none">◐</button>
    <nav class="sh-tabs" aria-label="${TT('Chức năng','Sections')}"><div class="in">${P.map(link).join('')}${ext(isADA?'btc-dashboard.html':'ada-dashboard.html',isADA?'BTC ↗':'ADA ↗',isADA?IC.btc:IC.ada,'')}${ext('robinhood.html','Robinhood ↗',IC.pf,'')}</div></nav>`;
  wrap.insertBefore(top,wrap.firstChild);
  const ph=document.createElement('div'); ph.className='sh-ph'; top.insertAdjacentElement('afterend',ph);
  document.addEventListener('click',e=>{ const b=e.target.closest('[data-proxy]'); if(b){ const t=document.getElementById(b.dataset.proxy); t&&t.click(); }
    if(e.target.closest('[data-lang]')){ const nx=LANG==='en'?'vi':'en'; try{localStorage.setItem('cre-lang',nx);}catch(err){} const u=new URL(location.href); u.searchParams.set('lang',nx); location.href=u.toString(); } });

  function go(k,scroll){
    const p=P.find(x=>x.k===k)||P[0];
    all.forEach(n=>n.classList.toggle('sh-off',!p.nodes.includes(n)));
    document.querySelectorAll('.sh-ni[data-k]').forEach(a=>a.dataset.k===p.k?a.setAttribute('aria-current','page'):a.removeAttribute('aria-current'));
    ph.innerHTML=`<div><div class="e">${p.e}</div><h2>${p.h}</h2></div><div class="r">${M[mo.m]} ${mo.y} · MTD<br>CRE FRAMEWORK</div>`;
    q('#shTitle').textContent=p.t; document.title=p.t+' · '+ASSET+' · CRE';
    try{ if(location.hash.slice(1)!==p.k) history.pushState(null,'','#'+p.k); }catch(e){}
    requestAnimationFrame(()=>{ dispatchEvent(new Event('resize')); if(p.k==='heatmap'&&typeof render==='function') render(); });
    // centre the active tab by scrolling the strip itself — scrollIntoView would also scroll the page sideways
    if(innerWidth<=860){ const st=top.querySelector('.sh-tabs'), a=st&&st.querySelector(`[data-k="${p.k}"]`); if(a) st.scrollLeft=a.offsetLeft-st.clientWidth/2+a.offsetWidth/2; }
    if(scroll) scrollTo({top:0});
  }
  document.addEventListener('click',e=>{ const a=e.target.closest('.sh-ni[data-k]'); if(!a||e.metaKey||e.ctrlKey||e.shiftKey||e.button) return; e.preventDefault(); go(a.dataset.k,true); });
  addEventListener('popstate',()=>go(location.hash.slice(1),false));
  go(location.hash.slice(1)||'heatmap',false);
})();
</script>'''

for name, asset in (('btc-dashboard.html', 'BTC'), ('ada-dashboard.html', 'ADA')):
    p = ROOT / name
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link id="cre-shell-fonts"[^>]*>', '', s)
    s = re.sub(r'\n?<style id="cre-shell">[\s\S]*?</style>', '', s)
    s = re.sub(r'\n?<script id="cre-shell-js">[\s\S]*?</script>', '', s)
    s = re.sub(r'<body[^>]*>', '<body data-asset="%s">' % asset, s, count=1)
    for need in ('<div class="wrap">', 'class="controls"', 'class="chart-card"', 'id="themeToggle"', 'const levelLines', 'const currentIdx'):
        if need not in s:
            sys.exit(name + ': layout changed — missing ' + need)
    s = s.replace('</head>', FONTS + '\n' + CSS + '\n</head>', 1)
    i = s.rindex('</body>')
    s = s[:i] + JS + '\n' + s[i:]
    p.write_text(s, encoding='utf-8')
    print(name, 'shelled')

# ── reports: a fixed "back" button on every BTC / ADA report page ──
BACK = r"""<div id="cre-back-wrap"><style>
#cre-back{position:fixed;top:14px;left:14px;z-index:9999;display:inline-flex;align-items:center;gap:6px;padding:8px 12px;border-radius:9px;
  font:600 12px ui-monospace,SFMono-Regular,Menlo,monospace;color:#edf2f5;background:rgba(17,24,32,.88);border:1px solid rgba(173,191,211,.24);
  text-decoration:none;backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);box-shadow:0 6px 20px rgba(0,0,0,.25)}
#cre-back:hover{border-color:#54d6b4;color:#54d6b4}
body{padding-top:52px!important}
@media print{#cre-back{display:none}body{padding-top:0!important}}
</style><a id="cre-back" href="__HOME__">← <span id="cre-back-t"></span></a><script>
(function(){ var a=document.getElementById('cre-back'), en=false;
  try{ en=(new URLSearchParams(location.search).get('lang')||localStorage.getItem('cre-lang'))==='en'; }catch(e){}
  document.getElementById('cre-back-t').textContent=en?'Back':'Quay lại';
  a.title=en?'Back to the previous page':'Quay lại trang trước';
  // go back when we came from this site, otherwise open the asset's dashboard
  a.addEventListener('click',function(e){ var r=document.referrer; if(history.length>1&&r&&r.indexOf(location.origin)===0){ e.preventDefault(); history.back(); } });
})();
</script></div>"""
for f in sorted(ROOT.glob('BTC_report_*.html')) + sorted(ROOT.glob('ADA_monthly_map_*.html')):
    t = f.read_text(encoding='utf-8')
    t = re.sub(r'<div id="cre-back-wrap">[\s\S]*?</script></div>', '', t)
    home = 'btc-dashboard.html' if f.name.startswith('BTC') else 'ada-dashboard.html'
    t = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + BACK.replace('__HOME__', home), t, count=1)
    f.write_text(t, encoding='utf-8')
    print(f.name, 'back button')

