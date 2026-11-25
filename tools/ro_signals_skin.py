#!/usr/bin/env python3
"""Re-skin ro-signals.html into a sidebar app — UI/UX only.

    python3 tools/ro_signals_skin.py

ro-signals.html is an upstream page that is replaced whole on every update. This script
adds a layer on top of it and changes nothing underneath: the 3D/2D radar, the signal
list, the breakout layer, the large-order / whale money-flow chart and the BTC overlay
keep their own markup, data and code. The skin only
  * injects one <style> block (sidebar shell, page header, spacing),
  * injects one <script> block that puts the existing sections into sidebar pages and
    shows one at a time (it sends a resize afterwards so the radar and the flow chart
    re-measure the box they are drawn in),
  * points the page's "Bàn quản lý" link at the merged portfolio page, robinhood.html.
It is idempotent: running it again replaces the previous skin instead of stacking a second.
Run it after copying a new upstream ro-signals.html into the repo.
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / 'ro-signals.html'
s = P.read_text(encoding='utf-8')

# remove a previous skin, if any
s = re.sub(r'\n?<style id="cre-skin">[\s\S]*?</style>', '', s)
s = re.sub(r'\n?<script id="cre-skin-js">[\s\S]*?</script>', '', s)

# the merged portfolio page replaces the separate desk page as this page's companion
s = s.replace('href="ro-desk.html" style="text-decoration:none">Bàn quản lý</a>',
              'href="robinhood.html" style="text-decoration:none">Danh mục</a>')

for need in ('<div class="app">', 'id="stats"', 'class="stage"', 'id="list"', 'id="brk"', 'id="mf"', 'id="btc"', 'class="more"'):
    if need not in s:
        sys.exit('ro-signals.html layout changed — missing ' + need + '; update the page map in this script')

CSS = r'''
<style id="cre-skin">
/* ── CRE skin: sidebar shell around the original page (layout only) ── */
body{display:grid;grid-template-columns:228px minmax(0,1fr);min-height:100vh}
.sk-side{position:sticky;top:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column;gap:16px;padding:18px 12px 14px;
  border-right:1px solid var(--line);background:linear-gradient(180deg,var(--panel),color-mix(in srgb,var(--panel) 92%,var(--bg)))}
.sk-brand{display:flex;align-items:center;gap:10px;padding:0 8px 16px;border-bottom:1px solid var(--line);text-decoration:none;color:inherit}
.sk-brand .mk{width:34px;height:34px;border-radius:9px;display:grid;place-items:center;flex:none;background:var(--mint);color:var(--bg)}
.sk-brand .mk svg{width:18px;height:18px}
.sk-brand b{display:block;font:700 11px/1.35 var(--mono);letter-spacing:.08em;text-transform:uppercase}
.sk-brand b em{font-style:normal;color:var(--mint)}
.sk-brand small{display:block;font-size:10px;color:var(--muted)}
.sk-lbl{font:700 9.5px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--dim);padding:0 10px 6px;margin-top:6px}
.sk-nav{display:flex;flex-direction:column;gap:3px}
.sk-ni{display:flex;align-items:center;gap:11px;padding:9px 11px;border-radius:9px;border:1px solid transparent;color:var(--muted);
  text-decoration:none;font-size:12.5px;font-weight:600;background:none;width:100%;text-align:left;cursor:pointer}
.sk-ni svg{width:16px;height:16px;flex:none;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;opacity:.8}
.sk-ni:hover{background:var(--panel2);color:var(--text)}
.sk-ni[aria-current="page"]{color:var(--mint);background:color-mix(in srgb,var(--mint) 10%,var(--panel2));border-color:color-mix(in srgb,var(--mint) 28%,transparent)}
.sk-ni .c{margin-left:auto;font:600 9.5px var(--mono);padding:2px 6px;border-radius:5px;background:var(--panel2);color:var(--muted)}
.sk-sp{flex:1}
.sk-state{padding:11px;border:1px solid var(--line);border-radius:10px;background:var(--panel2);font-size:10.5px;color:var(--muted);line-height:1.45}
.sk-state b{display:flex;justify-content:space-between;font:700 9.5px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:5px}
.sk-state b span{color:var(--text)}
.sk-btns{display:flex;gap:6px}
.sk-btn{flex:1;display:inline-flex;justify-content:center;align-items:center;gap:6px;padding:7px 9px;border-radius:8px;border:1px solid var(--line);
  background:transparent;color:var(--muted);font:600 11px var(--mono);cursor:pointer;text-decoration:none;white-space:nowrap}
.sk-btn:hover{color:var(--text);border-color:var(--mint)}
.app{max-width:1440px;width:100%;padding-top:0}
.app>.top{position:sticky;top:0;z-index:30;margin:0 -20px;padding:12px 20px;background:color-mix(in srgb,var(--bg) 88%,transparent);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
.app>.top .brand p{display:none}
.app>.top .brand .mark{display:none}
.app>.top .brand h1{font:700 11.5px var(--mono);letter-spacing:.1em;text-transform:uppercase}
.sk-ph{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin:18px 0 2px}
.sk-ph .e{font:700 10px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.sk-ph h2{font-size:24px;font-weight:700;letter-spacing:-.035em;line-height:1.15;margin:4px 0}
.sk-ph h2 em{font-style:normal;color:var(--mint)}
.sk-ph p{margin:0;font-size:12.5px;color:var(--muted);max-width:760px}
.sk-ph .r{font:600 10px var(--mono);letter-spacing:.08em;color:var(--muted);text-align:right;line-height:1.7;white-space:nowrap}
.sk-off{display:none!important}
/* explanatory prose is hidden; numbers, charts, tables, legends and fake-token warnings stay */
#lead,#mf .mf-hd p,#mf-note,#mf-ev,#brk .mf-hd p,#brk p:not([style*="--red"]),#brk h3,#btc .bz-why,.app>.more{display:none!important}
.app>section{margin-top:14px}
.app>.readout,.stage .readout{top:76px}

.sk-tabs{display:none}
@media (max-width:860px){
  body{display:block}
  .sk-side{display:none}
  .app>.top{margin:0 -12px;padding:10px 12px 0;flex-wrap:wrap}
  .sk-tabs{display:block;flex:0 0 calc(100% + 24px);margin:8px -12px 0;overflow-x:auto;scrollbar-width:none;border-top:1px solid var(--line)}
  .sk-tabs::-webkit-scrollbar{display:none}
  .sk-tabs .in{display:flex;gap:4px;padding:7px 12px;width:max-content}
  .sk-tabs .sk-ni{width:auto;padding:7px 10px;font-size:12px;white-space:nowrap}
  .sk-ph{margin-top:14px}.sk-ph h2{font-size:21px}.sk-ph .r{display:none}
  .app>.top .brand,.app>.top .stamp,.app>.top #csvBtn{display:none}
  .app>.top .tools{width:100%;justify-content:flex-end}
}
</style>
'''

JS = r'''
<script id="cre-skin-js">
/* CRE skin — layout only. Moves nothing into new code: it assigns the page's own sections to
   sidebar pages and shows one at a time. The radar, list, breakout, flow chart and BTC overlay
   keep running their original code. */
(function(){
  const q=s=>document.querySelector(s), app=q('.app'); if(!app) return;
  const date=(q('#date')||{}).textContent||'';
  // language: site-wide cre-lang key, ?lang= override; EN swaps this shell only — the upstream page text stays as published
  const LANG=(()=>{ const u=new URLSearchParams(location.search).get('lang'); if(u==='en'||u==='vi'){ try{localStorage.setItem('cre-lang',u);}catch(e){} return u; }
    try{return localStorage.getItem('cre-lang')==='en'?'en':'vi';}catch(e){return 'vi';} })();
  const TT=(vi,en)=>LANG==='en'?en:vi;
  const PAGES=[
    {k:'radar',  t:'Radar',        g:TT('Khám phá','Discovery'), els:['#stats','.stage'], e:TT('Bảng tín hiệu','Signal terminal')+' / Robinhood Chain', h:TT('Xem tín hiệu. <em>Đọc bối cảnh.</em>','See the signal. <em>Read the context.</em>'), p:TT('Chọn token trên radar để xem thông tin hiện có. Bộ lọc và cách hiển thị không thay đổi logic tín hiệu.','Pick a token on the radar to see what is known about it. Filters and display options do not change the signal logic.'),
     i:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12l6-6"/>'},
    {k:'list',   t:TT('Danh sách','Signal list'), g:TT('Khám phá','Discovery'), els:['#list'], e:TT('Bảng tín hiệu / danh sách','Signal terminal / list'), h:TT('Tín hiệu &amp; <em>token</em>','Signals &amp; <em>tokens</em>'), p:TT('Danh sách hiện có, hiển thị gọn để so sánh.','The current list, laid out compactly for comparison.'),
     i:'<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>'},
    {k:'flow',   t:TT('Dòng tiền','Money flow'), g:TT('Dòng tiền & nghiên cứu','Flow & research'), els:['#mf'], e:TT('Dòng tiền / lệnh lớn &amp; cá voi','Flow / large orders &amp; whales'), h:TT('Dòng tiền <em>lệnh lớn</em>','Large-order <em>flow</em>'), p:TT('Giá đóng cửa, dòng lệnh lớn theo ngày và dấu cá voi. Lớp quan sát, không phải tín hiệu giao dịch độc lập.','Closes, daily large-order flow and whale marks. An observation layer, not a standalone trading signal.'),
     i:'<path d="M3 12h4l3-8 4 16 3-8h4"/>'},
    {k:'breakout',t:'Breakout',    g:TT('Dòng tiền & nghiên cứu','Flow & research'), els:['#brk'], e:TT('Lớp khám phá','Discovery layer'), h:TT('Khám phá <em>breakout</em>','Breakout <em>discovery</em>'), p:TT('Token mới được phát hiện qua lớp breakout. Khám phá và theo dõi, không phải lệnh mua.','New tokens found by the breakout layer. For discovery and watching, not buy orders.'),
     i:'<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>'},
    {k:'btc',    t:TT('Bối cảnh BTC','BTC context'), g:TT('Bối cảnh','Context'), els:['#btc'], e:TT('Bối cảnh thị trường','Market backdrop'), h:TT('Bối cảnh <em>BTC</em>','BTC <em>context</em>'), p:TT('Lớp phủ chế độ thị trường. Không tự động thay đổi tín hiệu token.','Market-regime overlay. It does not change token signals by itself.'),
     i:'<path d="M12 3v18M7 7h7a3 3 0 010 6H7h8a3 3 0 010 6H7"/>'}
  ];
  PAGES.forEach(P=>{ P.nodes=P.els.map(s=>q('.app>'+s)||q(s)).filter(Boolean); });
  const cnt={list:(q('#list')?q('#list').querySelectorAll('.row').length:0)||'', breakout:'BR-001',
    flow:((q('#mf-rng [aria-pressed="true"]')||{}).textContent||'').trim()};
  const link=P=>`<a class="sk-ni" href="#${P.k}" data-k="${P.k}"><svg viewBox="0 0 24 24" aria-hidden="true">${P.i}</svg><span>${P.t}</span>${cnt[P.k]?`<span class="c">${cnt[P.k]}</span>`:''}</a>`;
  let groups=''; [...new Set(PAGES.map(P=>P.g))].forEach(g=>{ groups+=`<div class="sk-lbl">${g}</div><nav class="sk-nav">${PAGES.filter(P=>P.g===g).map(link).join('')}</nav>`; });
  const side=document.createElement('aside'); side.className='sk-side'; side.setAttribute('aria-label',TT('Điều hướng','Navigation'));
  side.innerHTML=`<a class="sk-brand" href="index.html" title="${TT('Về trang chủ CRE','Back to the CRE home page')}"><span class="mk"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="8"/><path d="M12 12l5-5"/></svg></span>
      <span><b>Robinhood Chain<br><em>${TT('Rổ tín hiệu','Signal basket')}</em></b><small>${TT('Khám phá &amp; nghiên cứu','Discovery &amp; research terminal')}</small></span></a>
    ${groups}
    <div class="sk-lbl">${TT('Trang riêng','Pages')}</div><nav class="sk-nav"><a class="sk-ni" href="robinhood.html"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 13h4v8H3zM10 9h4v12h-4zM17 4h4v17h-4z"/></svg><span>${TT('Danh mục','Portfolio')}</span><span class="c">↗</span></a></nav>
    <div class="sk-lbl">${TT('Tài sản','Assets')}</div><nav class="sk-nav"><a class="sk-ni" href="btc-dashboard.html"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v18M7 7h7a3 3 0 010 6H7h8a3 3 0 010 6H7"/></svg><span>Bitcoin</span><span class="c">↗</span></a><a class="sk-ni" href="ada-dashboard.html"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2"/></svg><span>Cardano</span><span class="c">↗</span></a></nav>
    <div class="sk-sp"></div>
    <div class="sk-state"><b>${TT('Dữ liệu','Data')} <span>${TT('Lịch sử','Historical')}</span></b>Close ${date} UTC</div>
    <div class="sk-btns"><a class="sk-btn" href="index.html">${TT('← Trang chủ','← Home')}</a><button class="sk-btn" type="button" data-lang>${LANG==='en'?'VI':'EN'}</button><button class="sk-btn" type="button" data-proxy="themeBtn" aria-label="${TT('Đổi giao diện sáng / tối','Toggle light / dark')}">◐</button><button class="sk-btn" type="button" data-proxy="csvBtn">↓ CSV</button></div>`;
  document.body.insertBefore(side,document.body.firstChild);
  const tabs=document.createElement('nav'); tabs.className='sk-tabs'; tabs.setAttribute('aria-label',TT('Chức năng','Sections'));
  tabs.innerHTML='<div class="in">'+PAGES.map(link).join('')+'<a class="sk-ni" href="robinhood.html"><span>'+TT('Danh mục','Portfolio')+' ↗</span></a><a class="sk-ni" href="btc-dashboard.html"><span>BTC ↗</span></a><a class="sk-ni" href="ada-dashboard.html"><span>ADA ↗</span></a></div>';
  q('.app>.top').appendChild(tabs);
  const lb=document.createElement('button'); lb.type='button'; lb.className='ghost sk-langm'; lb.setAttribute('data-lang',''); lb.textContent=LANG==='en'?'VI':'EN';
  lb.addEventListener('click',()=>{ const nx=LANG==='en'?'vi':'en'; try{localStorage.setItem('cre-lang',nx);}catch(err){} const u=new URL(location.href); u.searchParams.set('lang',nx); location.href=u.toString(); });
  const tl=q('.app>.top .tools'); tl&&tl.insertBefore(lb,tl.firstChild);
  if(LANG==='en'){ const dl=q('.app>.top a[href="robinhood.html"]'); if(dl) dl.textContent='Portfolio'; }
  const ph=document.createElement('div'); ph.className='sk-ph';
  q('.app>.top').insertAdjacentElement('afterend',ph);
  side.addEventListener('click',e=>{ const b=e.target.closest('[data-proxy]'); if(b){ const t=document.getElementById(b.dataset.proxy); t&&t.click(); }
    if(e.target.closest('[data-lang]')){ const nx=LANG==='en'?'vi':'en'; try{localStorage.setItem('cre-lang',nx);}catch(err){} const u=new URL(location.href); u.searchParams.set('lang',nx); location.href=u.toString(); } });

  const all=PAGES.flatMap(P=>P.nodes);
  function go(k,top){
    const P=PAGES.find(x=>x.k===k)||PAGES[0];
    all.forEach(n=>n.classList.toggle('sk-off',!P.nodes.includes(n)));
    document.querySelectorAll('.sk-ni[data-k]').forEach(a=>a.dataset.k===P.k?a.setAttribute('aria-current','page'):a.removeAttribute('aria-current'));
    ph.innerHTML=`<div><div class="e">${P.e}</div><h2>${P.h}</h2></div><div class="r">${date} · UTC CLOSE<br>HISTORICAL SNAPSHOT</div>`;
    document.title=P.t+' · '+TT('Rổ tín hiệu','Signal basket')+' · Robinhood Chain';
    try{ if(location.hash.slice(1)!==P.k) history.pushState(null,'','#'+P.k); }catch(e){}
    // the radar and the flow chart size themselves from their box: let them re-measure now that it is visible
    requestAnimationFrame(()=>{ dispatchEvent(new Event('resize')); });
    if(innerWidth<=860){ const a=tabs.querySelector(`[data-k="${P.k}"]`); a&&a.scrollIntoView({block:'nearest',inline:'center'}); }
    if(top) scrollTo({top:0});
  }
  document.addEventListener('click',e=>{ const a=e.target.closest('.sk-ni[data-k]'); if(!a||e.metaKey||e.ctrlKey||e.shiftKey||e.button) return; e.preventDefault(); go(a.dataset.k,true); });
  addEventListener('popstate',()=>go(location.hash.slice(1),false));
  go(location.hash.slice(1)||'radar',false);
})();
</script>
'''

s = s.replace('</head>', CSS + '</head>', 1)
i = s.rindex('</body>')
s = s[:i] + JS + s[i:]
P.write_text(s, encoding='utf-8')
print('ro-signals.html skinned · pages: radar, list, flow, breakout, btc')
