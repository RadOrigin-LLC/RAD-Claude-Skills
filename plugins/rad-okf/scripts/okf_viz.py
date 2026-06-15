# plugins/rad-okf/scripts/okf_viz.py
"""Render a normalized model as a single self-contained HTML file.
No external resources, no build step. v1: simple force-free circular graph."""
import json, html

def render_html(model, name="OKF Bundle"):
    nodes = [{"id": cid, "type": f.get("type", ""),
              "reserved": f.get("reserved", False),
              "error": bool(f.get("errors"))}
             for cid, f in model["files"].items()]
    edges = [{"src": l["src"], "dst": l["dst"], "resolved": l["resolved"]}
             for l in model["links"] if l.get("dst")]
    data = json.dumps({"nodes": nodes, "edges": edges}, indent=2)
    title = html.escape(name)
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>%s</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;background:#0f1115;color:#e6e6e6}
 header{padding:12px 16px;background:#171a21;font-weight:600}
 #wrap{display:flex;height:calc(100vh - 48px)}
 svg{flex:1}
 aside{width:280px;overflow:auto;border-left:1px solid #2a2f3a;padding:8px 12px;font-size:13px}
 .n{cursor:pointer} .lbl{font-size:10px;fill:#9aa4b2} text{pointer-events:none}
</style></head>
<body>
<header>%s</header>
<div id="wrap"><svg id="g"></svg>
<aside><b>Concepts</b><ul id="list"></ul></aside></div>
<script>
const DATA = %s;
const svg = document.getElementById('g');
const W = svg.clientWidth || 800, H = svg.clientHeight || 600;
const R = Math.min(W,H)/2 - 60, cx = W/2, cy = H/2;
const pos = {};
DATA.nodes.forEach((n,i)=>{const a=2*Math.PI*i/DATA.nodes.length;
  pos[n.id]=[cx+R*Math.cos(a), cy+R*Math.sin(a)];});
const NS='http'+'://www.w3.org/2000/svg';
function line(x1,y1,x2,y2,ok){const l=document.createElementNS(NS,'line');
  l.setAttribute('x1',x1);l.setAttribute('y1',y1);l.setAttribute('x2',x2);l.setAttribute('y2',y2);
  l.setAttribute('stroke',ok?'#3b4252':'#bf616a');l.setAttribute('stroke-width',ok?1:1.5);svg.appendChild(l);}
DATA.edges.forEach(e=>{if(pos[e.src]&&pos[e.dst])line(pos[e.src][0],pos[e.src][1],pos[e.dst][0],pos[e.dst][1],e.resolved);});
DATA.nodes.forEach(n=>{const [x,y]=pos[n.id];
  const c=document.createElementNS(NS,'circle');c.setAttribute('cx',x);c.setAttribute('cy',y);
  c.setAttribute('r',n.reserved?5:7);
  c.setAttribute('fill',n.error?'#bf616a':(n.reserved?'#5e81ac':'#a3be8c'));c.setAttribute('class','n');
  c.appendChild(Object.assign(document.createElementNS(NS,'title'),{textContent:n.id+' ['+(n.type||'reserved')+']'}));
  svg.appendChild(c);
  const t=document.createElementNS(NS,'text');t.setAttribute('x',x+9);t.setAttribute('y',y+3);
  t.setAttribute('class','lbl');t.textContent=n.id;svg.appendChild(t);});
const ul=document.getElementById('list');
DATA.nodes.slice().sort((a,b)=>a.id<b.id?-1:1).forEach(n=>{const li=document.createElement('li');
  li.textContent=n.id+(n.error?'  ⚠':'');ul.appendChild(li);});
</script>
</body></html>""" % (title, title, data)
