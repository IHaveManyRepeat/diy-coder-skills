"""diy-viewer CSS/JS 模板常量（Q-130 自 viewer_render 拆出，400 行卡线）。

viewer_render 再导出 CSS/PANE_JS/TOOLTIP_JS/COPY_JS，viewer_pages 导入面零改动。
"""


CSS = """
:root{--ink:#1a2333;--mut:#6b7280;--line:#e3e8ef;--bg:#f6f8fa;--card:#fff;
--accent:#1d4ed8;--ok:#15803d;--warn:#b45309;--bad:#b91c1c;--dim:#6b7280}
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI","Microsoft YaHei",
system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.65}
main{max-width:1080px;margin:0 auto;padding:32px 24px 64px}
header.top{background:#fff;border-bottom:1px solid var(--line);padding:14px 24px}
header.top .wrap{max-width:1080px;margin:0 auto;display:flex;justify-content:
space-between;align-items:baseline}header.top a{color:var(--accent);
text-decoration:none;font-size:.9em}h1{font-size:1.6em;margin:0 0 4px}
h2,h3,h4,h5,h6{margin:1.6em 0 .5em}h2{font-size:1.25em;border-bottom:
1px solid var(--line);padding-bottom:.3em}table{border-collapse:collapse;
width:100%;background:var(--card);border:1px solid var(--line);border-radius:
8px;overflow:hidden;font-size:.92em}th,td{padding:8px 12px;text-align:left;
vertical-align:top;border-bottom:1px solid var(--line)}thead th{background:
#eef2f7;font-weight:600}tbody tr:last-child td{border-bottom:none}
table.kv th{width:180px;background:#eef2f7;font-weight:600}ul{padding-left:22px}
.table-scroll{overflow-x:auto}table.data th,table.data td{white-space:nowrap}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:4px 18px;margin:10px 0}.card h3,.card h4,.card h5{margin:.7em 0 .3em}
.badge{display:inline-block;padding:1px 10px;border-radius:999px;font-size:.8em;
font-weight:600;border:1px solid transparent}.b-ok{color:var(--ok);background:
#ecfdf3;border-color:#b7e7c8}.b-warn{color:var(--warn);background:#fff8eb;
border-color:#f3ddab}.b-bad{color:var(--bad);background:#fef2f2;
border-color:#f3c1c1}.b-dim{color:var(--dim);background:#f3f4f6;
border-color:#e0e2e6}.b-must{color:#fff;background:var(--accent)}.b-neutral{
color:var(--ink);background:#eef2f7;border-color:var(--line)}
.assume{background:#fef9c3;padding:0 4px;border-radius:4px}.refsum{
color:var(--dim);font-size:.85em;margin-left:6px}
.dangling{color:var(--bad);font-weight:600}
.alert-bad{background:#fef2f2;border-color:#f3c1c1;color:var(--bad)}
tr.orphan td{background:#fef2f2}
.idl,.asset{color:var(--accent);text-decoration:underline dotted;text-underline-offset:3px}
.idl:hover{background:#eef2f7;border-radius:3px}
.asset:hover{background:#eef2f7;border-radius:3px}
.reflist{list-style:none;padding-left:0;margin:4px 0}
.reflist>li{margin:6px 0}
main{transition:margin-right .25s ease}
body.pane-open main{margin-right:46%}
#refpane{position:fixed;top:0;right:0;width:46%;height:100vh;background:var(--card);
border-left:1px solid var(--line);box-shadow:-6px 0 20px rgba(0,0,0,.08);
transform:translateX(105%);transition:transform .25s ease;overflow-y:auto;z-index:50}
#refpane.open{transform:translateX(0)}
#refpane .rp-head{position:sticky;top:0;background:var(--card);border-bottom:
1px solid var(--line);padding:12px 20px;display:flex;align-items:center;gap:12px;z-index:1}
#refpane .rp-head h3{margin:0;font-size:1.05em}
#refpane .rp-head .src{color:var(--accent);text-decoration:none;font-size:.85em;margin-left:auto}
#refpane .rp-close{border:1px solid var(--line);background:#fff;border-radius:6px;
padding:2px 10px;cursor:pointer;font-size:.85em;color:var(--ink)}
#refpane .rp-close:hover{background:#eef2f7}
#refpane .rp-body{padding:4px 20px 32px}
@media(max-width:860px){#refpane{width:100vw}body.pane-open main{margin-right:0}}
tr:target td{background:#fff8eb}
.card:target{border-color:var(--warn);box-shadow:0 0 0 3px #fff8eb}
.dim{color:var(--mut)}p{margin:.4em 0}
.doc-meta{color:var(--mut);font-size:.9em;margin-bottom:8px}
.alert{background:#fff8eb;border:1px solid #f3ddab;color:var(--warn);border-radius:
8px;padding:10px 16px;margin:0 0 18px;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
gap:16px}a.doc-card{display:block;background:var(--card);border:1px solid
var(--line);border-radius:10px;padding:18px 20px;text-decoration:none;
color:var(--ink);transition:box-shadow .15s}a.doc-card:hover{box-shadow:0 4px
14px rgba(0,0,0,.08)}a.doc-card .name{font-weight:700;color:var(--accent);
font-size:1.05em}a.doc-card .sub{color:var(--mut);font-size:.85em;margin-top:4px}
.term{border-bottom:1px dotted var(--accent);cursor:help}
.term:hover{background:#eef2f7;border-radius:3px}
#gloss-tip{position:fixed;display:none;z-index:99;max-width:340px;background:
#1a2333;color:#fff;font-size:.85em;line-height:1.5;padding:8px 12px;border-radius:
8px;box-shadow:0 4px 14px rgba(0,0,0,.25);pointer-events:none}
.plain{color:var(--mut);font-size:.95em;background:#f6f8fa;border-left:3px
solid #cbd5e1;padding:6px 12px;margin:6px 0 10px;border-radius:0 6px 6px 0}
details.detail{margin:10px 0 4px;border:1px dashed var(--line);border-radius:8px}
details.detail summary{cursor:pointer;padding:7px 14px;color:var(--mut);
font-size:.88em;user-select:none}
details.detail summary:hover{color:var(--accent)}
details.detail[open] summary{border-bottom:1px dashed var(--line)}
details.detail .d-body{padding:6px 14px 10px;font-size:.95em;color:var(--mut)}
.foot{color:var(--mut);font-size:.85em;border-top:1px solid var(--line);
margin-top:40px;padding-top:12px}
.copy-id{margin-left:6px;padding:0 6px;font-size:.8em;color:var(--mut);background:#f6f8fa;border:1px solid var(--line);border-radius:4px;cursor:pointer}
.copy-id:hover{color:var(--accent);border-color:var(--accent)}
"""


PANE_JS = """
(function(){
var pane=document.getElementById('refpane');
var body=document.getElementById('rp-body');
var title=document.getElementById('rp-title');
var src=document.getElementById('rp-src');
function closePane(){pane.classList.remove('open');document.body.classList.remove('pane-open');}
document.getElementById('rp-close').addEventListener('click',closePane);
document.addEventListener('keydown',function(e){if(e.key==='Escape')closePane();});
document.addEventListener('click',function(e){
  var a=e.target.closest('a.idl');
  if(!a)return;
  var id=(a.textContent||'').trim();
  var tpl=document.querySelector('template[data-detail="'+id+'"]');
  if(!tpl)return;
  e.preventDefault();
  title.textContent=id;
  src.setAttribute('href',a.getAttribute('href')||'#');
  body.innerHTML='';
  body.appendChild(tpl.content.cloneNode(true));
  pane.classList.add('open');
  document.body.classList.add('pane-open');
  pane.scrollTop=0;
});
})();
"""


TOOLTIP_JS = """
(function(){
var tip=null;
function show(t){
  if(!tip){tip=document.createElement('div');tip.id='gloss-tip';
  document.body.appendChild(tip);}
  tip.textContent=t.getAttribute('data-tip');
  tip.style.display='block';
  var r=t.getBoundingClientRect();
  var left=Math.max(8,Math.min(r.left,window.innerWidth-tip.offsetWidth-8));
  var top=r.bottom+6;
  if(top+tip.offsetHeight>window.innerHeight){top=r.top-tip.offsetHeight-6;}
  tip.style.left=left+'px';tip.style.top=top+'px';
}
function hide(){if(tip){tip.style.display='none';}}
document.addEventListener('mouseover',function(e){
  var t=e.target.closest('.term');
  if(t){show(t);}else{hide();}
});
document.addEventListener('scroll',hide,true);
})();
"""


COPY_JS = """
(function(){
document.addEventListener('click',function(e){
  var btn=e.target.closest('button.copy-id');if(!btn)return;
  var file=btn.getAttribute('data-file')||'',id=btn.getAttribute('data-id')||'';
  var text='请打开产物文件 '+file+'，定位条目 '+id+'，读取该条目的完整内容，然后按我的后续指令处理（解释/修改等）。';
  function done(){var old=btn.textContent;btn.textContent='已复制';
    setTimeout(function(){btn.textContent=old;},1200);}
  function legacy(){
    var ta=document.createElement('textarea');ta.value=text;
    ta.style.position='fixed';ta.style.top='-9999px';
    document.body.appendChild(ta);ta.select();
    var ok=false;try{ok=document.execCommand('copy');}catch(err){ok=false;}
    document.body.removeChild(ta);if(ok){done();}
  }
  if(!navigator.clipboard||!navigator.clipboard.writeText){legacy();return;}
  navigator.clipboard.writeText(text).then(done,legacy);
});
})();
"""
