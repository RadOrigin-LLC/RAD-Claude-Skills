# plugins/rad-okf/scripts/okf_viz.py
"""Render a normalized model as a single self-contained HTML file.
No external resources, no build step: a circular graph coloured by concept type,
a type legend (click to filter), a searchable concept list, and a detail panel
showing frontmatter, body, outbound links, and backlinks (graph reversal).
All user-supplied text is injected via the JSON blob (with `</` neutralized) and
rendered with textContent, so a concept body can never break out or execute."""
import json, html

def render_html(model, name="OKF Bundle"):
    nodes = []
    for cid, f in model["files"].items():
        meta = f.get("meta") or {}
        def _s(key):
            v = meta.get(key)
            return v if isinstance(v, str) else ""
        nodes.append({
            "id": cid,
            "type": f.get("type", "") or "",
            "reserved": bool(f.get("reserved")),
            "error": bool(f.get("errors")),
            "title": _s("title"),
            "desc": _s("description"),
            "resource": _s("resource"),
            "body": f.get("body", "") or "",
        })
    edges = [{"src": l["src"], "dst": l["dst"], "resolved": bool(l.get("resolved"))}
             for l in model["links"] if l.get("dst")]
    # Escape `</` so a concept id/type/body containing `</script>` can't break out
    # of the inlined <script> block. `<\/` parses identically inside a JS string.
    data = json.dumps({"nodes": nodes, "edges": edges}, indent=2).replace("</", "<\\/")
    return _TEMPLATE.replace("__TITLE__", html.escape(name)).replace("__DATA__", data)

_TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>__TITLE__</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;background:#0f1115;color:#e6e6e6}
 header{display:flex;gap:12px;align-items:center;padding:10px 16px;background:#171a21}
 header .title{font-weight:600}
 header input{flex:1;max-width:320px;background:#0f1115;border:1px solid #2a2f3a;color:#e6e6e6;
   border-radius:6px;padding:6px 10px;font-size:13px}
 #wrap{display:flex;height:calc(100vh - 52px)}
 svg{flex:1}
 aside{width:320px;overflow:auto;border-left:1px solid #2a2f3a;padding:8px 12px;font-size:13px}
 .n{cursor:pointer} .lbl{font-size:10px;fill:#9aa4b2} text{pointer-events:none}
 #legend{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
 .leg{display:inline-flex;align-items:center;gap:4px;cursor:pointer;font-size:11px;
   border:1px solid #2a2f3a;border-radius:10px;padding:1px 8px}
 .leg.off{opacity:.4;text-decoration:line-through} .leg i{width:9px;height:9px;border-radius:50%;display:inline-block}
 #list{list-style:none;margin:0;padding:0;max-height:34vh;overflow:auto}
 #list li{cursor:pointer;padding:2px 4px;border-radius:4px} #list li:hover{background:#1c2330}
 #detail{border-top:1px solid #2a2f3a;margin-top:8px;padding-top:8px}
 #detail h3{margin:0 0 6px} #detail .meta div{margin:1px 0;color:#cbd3df}
 #detail .meta b{color:#9aa4b2}
 ul.lnk{list-style:none;margin:2px 0 8px;padding:0} ul.lnk li{padding:1px 0}
 ul.lnk a{color:#88c0d0;text-decoration:none} ul.lnk .broken{color:#bf616a}
 pre.body{white-space:pre-wrap;word-break:break-word;background:#11151c;border:1px solid #2a2f3a;
   border-radius:6px;padding:8px;font-size:12px;max-height:40vh;overflow:auto}
 .hint{color:#9aa4b2}
</style></head>
<body>
<header><span class="title">__TITLE__</span><input id="q" placeholder="Search concepts…"></header>
<div id="wrap"><svg id="g"></svg>
<aside><div id="legend"></div><ul id="list"></ul>
<div id="detail"><p class="hint">Select a concept to see its details.</p></div></aside></div>
<script>
const DATA = __DATA__;
const nodes = DATA.nodes, edges = DATA.edges, byId = {};
nodes.forEach(n => byId[n.id] = n);

const PALETTE = ['#a3be8c','#81a1c1','#b48ead','#ebcb8b','#88c0d0','#d08770',
                 '#8fbcbb','#5e81ac','#bf616a','#e5e9f0'];
const types = [...new Set(nodes.filter(n => !n.reserved && n.type).map(n => n.type))].sort();
const colorOf = {};
types.forEach((t, i) => colorOf[t] = PALETTE[i - PALETTE.length * Math.floor(i / PALETTE.length)]);
function nodeColor(n){ if(n.error) return '#bf616a'; if(n.reserved) return '#4c566a'; return colorOf[n.type] || '#a3be8c'; }
const hidden = new Set();
function visible(n){ return !hidden.has(n.type); }

const out = {}, inn = {};
nodes.forEach(n => { out[n.id] = []; inn[n.id] = []; });
edges.forEach(e => { if(byId[e.src]) out[e.src].push(e); if(byId[e.dst]) inn[e.dst].push(e); });

const svg = document.getElementById('g');
const W = svg.clientWidth || 820, H = svg.clientHeight || 600;
const R = Math.min(W, H) / 2 - 70, cx = W / 2, cy = H / 2, pos = {};
nodes.forEach((n, i) => { const a = 2 * Math.PI * i / Math.max(1, nodes.length);
  pos[n.id] = [cx + R * Math.cos(a), cy + R * Math.sin(a)]; });
const NS = 'http://www.w3.org/2000/svg';

function draw(){
  while(svg.firstChild) svg.removeChild(svg.firstChild);
  edges.forEach(e => { const s = byId[e.src], d = byId[e.dst];
    if(!s || !d || !visible(s) || !visible(d)) return;
    const l = document.createElementNS(NS, 'line'); const p = pos[e.src], q = pos[e.dst];
    l.setAttribute('x1', p[0]); l.setAttribute('y1', p[1]); l.setAttribute('x2', q[0]); l.setAttribute('y2', q[1]);
    l.setAttribute('stroke', e.resolved ? '#3b4252' : '#bf616a');
    l.setAttribute('stroke-width', e.resolved ? 1 : 1.5); svg.appendChild(l); });
  nodes.forEach(n => { if(!visible(n)) return; const xy = pos[n.id];
    const c = document.createElementNS(NS, 'circle');
    c.setAttribute('cx', xy[0]); c.setAttribute('cy', xy[1]); c.setAttribute('r', n.reserved ? 5 : 7);
    c.setAttribute('fill', nodeColor(n)); c.setAttribute('class', 'n');
    c.addEventListener('click', () => select(n.id));
    const ttl = document.createElementNS(NS, 'title'); ttl.textContent = n.id + ' [' + (n.type || 'reserved') + ']';
    c.appendChild(ttl); svg.appendChild(c);
    const t = document.createElementNS(NS, 'text'); t.setAttribute('x', xy[0] + 9); t.setAttribute('y', xy[1] + 3);
    t.setAttribute('class', 'lbl'); t.textContent = n.title || n.id; svg.appendChild(t); });
}

function renderLegend(){
  const L = document.getElementById('legend'); L.textContent = '';
  types.forEach(t => { const b = document.createElement('span'); b.className = 'leg' + (hidden.has(t) ? ' off' : '');
    const i = document.createElement('i'); i.style.background = colorOf[t]; b.appendChild(i);
    b.appendChild(document.createTextNode(t));
    b.addEventListener('click', () => { hidden.has(t) ? hidden.delete(t) : hidden.add(t);
      renderLegend(); renderList(); draw(); });
    L.appendChild(b); });
}

function renderList(){
  const q = (document.getElementById('q').value || '').toLowerCase();
  const ul = document.getElementById('list'); ul.textContent = '';
  nodes.filter(n => !n.reserved && visible(n))
    .filter(n => !q || (n.id + ' ' + (n.title || '') + ' ' + (n.desc || '')).toLowerCase().indexOf(q) >= 0)
    .sort((a, b) => a.id < b.id ? -1 : 1)
    .forEach(n => { const li = document.createElement('li');
      li.textContent = (n.title || n.id) + (n.error ? '  ⚠' : '');
      li.addEventListener('click', () => select(n.id)); ul.appendChild(li); });
}

function kv(k, v){ const p = document.createElement('div'); const b = document.createElement('b');
  b.textContent = k + ': '; p.appendChild(b); p.appendChild(document.createTextNode(v)); return p; }

function linksBlock(label, ids){
  const w = document.createElement('div'); const b = document.createElement('b');
  b.textContent = label + ' (' + ids.length + ')'; w.appendChild(b);
  const ul = document.createElement('ul'); ul.className = 'lnk';
  ids.forEach(id => { const li = document.createElement('li');
    if(byId[id]){ const a = document.createElement('a'); a.href = '#'; a.textContent = byId[id].title || id;
      a.addEventListener('click', ev => { ev.preventDefault(); select(id); }); li.appendChild(a); }
    else { li.textContent = id + ' (unwritten)'; li.className = 'broken'; }
    ul.appendChild(li); });
  w.appendChild(ul); return w;
}

function select(id){
  const n = byId[id]; if(!n) return; const d = document.getElementById('detail'); d.textContent = '';
  const h = document.createElement('h3'); h.textContent = n.title || n.id; d.appendChild(h);
  const meta = document.createElement('div'); meta.className = 'meta';
  meta.appendChild(kv('id', n.id));
  if(n.type) meta.appendChild(kv('type', n.type));
  if(n.resource) meta.appendChild(kv('resource', n.resource));
  if(n.desc) meta.appendChild(kv('description', n.desc));
  d.appendChild(meta);
  d.appendChild(linksBlock('Links', out[id].map(e => e.dst)));
  d.appendChild(linksBlock('Backlinks', inn[id].map(e => e.src)));
  if(n.body){ const pre = document.createElement('pre'); pre.className = 'body'; pre.textContent = n.body; d.appendChild(pre); }
}

document.getElementById('q').addEventListener('input', renderList);
renderLegend(); renderList(); draw();
</script>
</body></html>"""
