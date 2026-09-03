"""render.py — renderizador HTML do site de produto da TOC Federada.

Origem: `GHDaru/daruskills`, skill `spec-to-code-docs` (render.py). Vendorizado e adaptado
neste repositório (ADR 0008). As adaptações estão listadas em `tools/product-site/README.md`.
O `templates/styles.css` é mantido **byte a byte idêntico** ao do original — é a régua de
design já validada, e mexer nele seria trocar a régua pelo gosto.

Uso:
    python tools/product-site/render.py docs/product-site/data.json --output docs/product-site

Siglas usadas neste arquivo: TOC — Teoria das Restrições; APH — o padrão Aplicação ↔
Harness; ADR — Architecture Decision Record (Registro de Decisão Arquitetural);
RF/RI/RNF/RN/INT — requisito funcional / de interface / não funcional / regra de negócio /
integração; DoD — Definition of Done; DoR — Definition of Ready; DDD — Domain-Driven Design.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from html import escape

# ──────────────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────────────

_FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&'
    'family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />'
)

_ICONS = {
    "overview": '<svg viewBox="0 0 24 24"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M9 12h6"/><path d="M9 16h4"/></svg>',
    "taxonomy": '<svg viewBox="0 0 24 24"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><circle cx="7" cy="7" r="1"/></svg>',
    "roadmap": '<svg viewBox="0 0 24 24"><circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h6a4 4 0 0 0 4-4V7"/></svg>',
    "modules": '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
    "traceability": '<svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg>',
    "workflow": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>',
    "adrs": '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h6"/></svg>',
    "principles": '<svg viewBox="0 0 24 24"><path d="M12 3v18"/><path d="M5 7h14"/><path d="M5 7l-3 7a4 4 0 0 0 6 0z"/><path d="M19 7l3 7a4 4 0 0 1-6 0z"/><path d="M8 21h8"/></svg>',
    "metrics": '<svg viewBox="0 0 24 24"><path d="M3 21h18"/><path d="M7 21V13"/><path d="M13 21V8"/><path d="M19 21V4"/></svg>',
    "artifacts": '<svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.27 6.96L12 12.01l8.73-5.05"/><path d="M12 22.08V12"/></svg>',
}

_MOON_SVG = '<svg viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
_SUN_SVG = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'


def _theme_script(key: str) -> str:
    return """\
<script>
const tt=document.getElementById("themeToggle");
const MOON_SVG='{moon}';
const SUN_SVG='{sun}';
const THEME_KEY="{key}";
function applyTheme(t){{document.documentElement.setAttribute("data-theme",t);tt.innerHTML=t==="dark"?SUN_SVG:MOON_SVG;try{{localStorage.setItem(THEME_KEY,t);}}catch(e){{}}}}
tt.addEventListener("click",()=>applyTheme(document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark"));
try{{const saved=localStorage.getItem(THEME_KEY);if(saved)applyTheme(saved);else applyTheme("light");}}catch(e){{}}
</script>""".format(moon=_MOON_SVG, sun=_SUN_SVG, key=key)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _e(s) -> str:
    return escape(str(s)) if s else ""


_CODE_RE = re.compile(r"`([^`]+)`")


def _md(s) -> str:
    """Escapa o HTML de um texto vindo do repositório e devolve o mínimo de marcação:
    `código` vira <code> e **negrito** vira <b>. Sem isto, um requisito que fala de
    `NNN-para-<repo>-<assunto>.md` perderia `<repo>` dentro do navegador — o defeito
    silencioso que o original tinha."""
    if not s:
        return ""
    out = escape(str(s))
    out = _CODE_RE.sub(r"<code>\1</code>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    return out


def _js(s: str) -> str:
    """Escapa uma string para dentro de um template literal JavaScript."""
    if not s:
        return ""
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def _up(path: str) -> str:
    """Caminho do repositório visto de dentro de `docs/product-site/`."""
    return "../../" + path if path and not path.startswith(("http", "../")) else path


def _sidebar(active: str, project: dict, data: dict) -> str:
    name = project.get("name", "")
    mark = project.get("mark", "T")
    subtitle = project.get("subtitle", "")
    n_mod = len(data.get("modules", []))
    n_specs = len(data.get("specs", []))
    n_adrs = len(data.get("adrs", []))

    def route(icon, label, key, badge=""):
        ic = _ICONS.get(icon, "")
        b = f' <span class="badge">{_e(badge)}</span>' if badge else ""
        if active == "index":
            return f'<button class="nav-item" data-route="{key}"><span class="ic">{ic}</span>{_e(label)}{b}</button>'
        return f'<a class="nav-item" href="index.html#{key}"><span class="ic">{ic}</span>{_e(label)}{b}</a>'

    def link(icon, label, page, href, badge=""):
        ic = _ICONS.get(icon, "")
        b = f' <span class="badge">{_e(badge)}</span>' if badge else ""
        cls = "nav-item" + (" active" if active == page else "")
        return f'<a class="{cls}" href="{href}"><span class="ic">{ic}</span>{_e(label)}{b}</a>'

    return f"""\
<aside class="sidebar">
  <div class="brand">
    <div class="logo"><span class="mark">{_e(mark)}</span><span class="name">{_e(name)}</span></div>
    <div class="sub">{_e(subtitle)}</div>
  </div>
  <div class="nav-group">
    <div class="label">Visão geral</div>
    {route("overview", "Visão geral", "overview")}
    {route("taxonomy", "Taxonomia", "taxonomy")}
  </div>
  <div class="nav-group">
    <div class="label">Produto</div>
    {link("roadmap", "Roadmap", "roadmap", "roadmap.html", str(len(data.get("roadmap", {}).get("cycles", []))))}
    {link("modules", "Módulos", "modules", "modules.html", str(n_mod))}
    {link("traceability", "Rastreabilidade", "traceability", "traceability.html", str(n_specs))}
  </div>
  <div class="nav-group">
    <div class="label">Engenharia</div>
    {route("workflow", "Workflow", "workflow")}
    {route("adrs", "ADRs", "adrs", str(n_adrs))}
    {route("principles", "Princípios", "principios")}
    {route("artifacts", "Artefatos", "artifacts")}
  </div>
  <div class="nav-group">
    <div class="label">Métricas</div>
    {route("metrics", "Métricas", "metrics")}
  </div>
</aside>"""


def _page(title: str, body: str, active: str, project: dict, data: dict,
          extra_css: str = "", script: str = "") -> str:
    lang = project.get("lang", "pt-BR")
    sidebar = _sidebar(active, project, data)
    inline_css = f"\n<style>\n{extra_css}\n</style>" if extra_css else ""
    script_html = f"\n{script}" if script else ""
    content_id = ' id="content"' if active in ("index", "traceability") else ""
    return f"""<!doctype html>
<html lang="{_e(lang)}" data-theme="light">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{_e(title)}</title>
{_FONT_LINK}
<link rel="stylesheet" href="styles.css" />{inline_css}
</head>
<body>
<button class="theme-toggle" id="themeToggle" aria-label="Alternar tema"></button>
<div class="app">
  {sidebar}
  <main class="main"{content_id}>
{body}
  </main>
</div>
{_theme_script(project.get("theme_key", "tocfed-theme"))}{script_html}
</body>
</html>"""


def _prep(data: dict) -> None:
    """Prepara para o navegador o texto que veio do repositório.

    Os campos curados por este gerador (taxonomia, workflow, chamadas "Barra:") já são HTML
    e passam intactos; tudo que foi **lido de um arquivo** — requisito, decisão de ADR,
    princípio, fonte — é escapado e recebe apenas <code> e <b>. Sem esta passagem, um
    requisito que cita `<repo>` some dentro do navegador.
    """
    for a in data.get("adrs", []):
        a["title"] = _md(a.get("title", ""))
        a["description"] = _md(a.get("description", ""))
        a["principios"] = _md(a.get("principios", ""))
    for pr in data.get("principles", []):
        pr["title"] = _md(pr.get("title", ""))
        pr["d"] = _md(pr.get("d", ""))
    for s in data.get("skills", []):
        s["description"] = _md(s.get("description", ""))
    for s in data.get("scripts", []):
        s["description"] = _md(s.get("description", ""))
    data["journeys_note"] = _md(data.get("journeys_note", ""))
    data["stack"] = {k: _md(v) for k, v in data.get("stack", {}).items()}
    for m in data.get("traceability", {}).get("modules", []):
        m["name"] = _md(m.get("name", ""))
        for kind in ("rfs", "ris", "rnfs", "rns", "ints"):
            for r in m.get(kind, []):
                r["d"] = _md(r.get("d", ""))
                r["group"] = _md(r.get("group", ""))
        for src in m.get("sources", []):
            tip = (src.get("path", "") or "")
            if src.get("lines"):
                tip += ":" + src["lines"]
            tip += " — " + (src.get("desc", "") or "")
            src["t"] = _e(tip)
        for c in m.get("chain", []):
            c["label"] = _e(c.get("label", ""))


# ──────────────────────────────────────────────────────────────────────
# index.html — casca de aplicação de página única
# ──────────────────────────────────────────────────────────────────────

_INDEX_CSS = """
.term{padding:20px 0;border-bottom:1px solid var(--border)}
.term:last-child{border-bottom:none}
.term .term-head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.term .term-name{font-size:18px;font-weight:700;letter-spacing:-.01em}
.term .term-id{font-family:var(--font-mono);font-size:12px;color:var(--faint);background:var(--surface-2);padding:2px 8px;border-radius:5px;border:1px solid var(--border)}
.term .term-def{color:var(--muted);font-size:14.5px;margin:0 0 10px;max-width:70ch}
.term .term-map{font-size:13px;color:var(--ink);background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin:0}
.term .term-map b{color:var(--accent)}
.phase-fail{border-left:3px solid var(--amber);background:rgba(176,107,0,.06);padding:10px 14px;border-radius:0 8px 8px 0;font-size:13px}
.chk{font-size:13px;color:var(--muted);margin-bottom:4px;list-style:none;padding-left:22px;position:relative}
.chk span.box{position:absolute;left:0;top:0}
.slab{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--faint);margin:0 0 6px}
.kv-wide{display:grid;grid-template-columns:230px 1fr;gap:6px 14px;font-size:13.5px}
.kv-wide dt{color:var(--faint);font-weight:600}
.kv-wide dd{margin:0}
"""


def _render_index(data: dict, project: dict) -> str:
    ov = data.get("overview", {})
    tax = data.get("taxonomy", {})
    wf = data.get("workflow", {})

    payload = {
        "overview": ov,
        "taxonomy": tax,
        "workflow": wf,
        "adrs": data.get("adrs", []),
        "principles": data.get("principles", []),
        "metrics": data.get("metrics", []),
        "stack": data.get("stack", {}),
        "skills": data.get("skills", []),
        "scripts": data.get("scripts", []),
        "journeys": data.get("journeys", []),
        "journeys_note": data.get("journeys_note", ""),
        "counts": data.get("counts", {}),
        "generated_from": project.get("generated_from", ""),
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    script = """<script>
const D = __PAYLOAD__;
const el = document.getElementById("content");
const routes = {overview:renderOverview,taxonomy:renderTaxonomy,workflow:renderWorkflow,adrs:renderAdrs,principios:renderPrinciples,artifacts:renderArtifacts,metrics:renderMetrics};
function go(route){
  const fn = routes[route] || renderOverview;
  el.innerHTML = "";
  fn(el);
  document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active", b.dataset.route===route));
  history.replaceState(null,"",`#${route}`);
  window.scrollTo(0,0);
}
document.querySelectorAll(".nav-item[data-route]").forEach(b=>b.addEventListener("click",()=>go(b.dataset.route)));

function renderOverview(c){
  const o = D.overview;
  const cards = o.cards.map(k=>`<div class="card"><p class="card-title">${k.title}</p><p class="muted" style="font-size:13.5px;margin:0">${k.content}</p></div>`).join("");
  const st = D.stack;
  const stackRows = Object.keys(st).filter(k=>st[k]).map(k=>`<dt>${k.charAt(0).toUpperCase()+k.slice(1)}</dt><dd>${st[k]}</dd>`).join("");
  c.innerHTML = `
    <p class="eyebrow">${o.eyebrow}</p>
    <h1>${o.title}</h1>
    <p class="lede">${o.lede}</p>
    <div class="callout">${o.callout}</div>
    <div class="grid grid-2">${cards}</div>
    <h2>Decisões estruturais vigentes</h2>
    <p class="muted" style="font-size:13.5px">Lidas de <code>docs/governance/constitution.md</code>. Trocar qualquer linha exige um ADR novo que suceda o anterior (regra R5).</p>
    <div class="card"><dl class="kv-wide">${stackRows}</dl></div>
    <p class="faint" style="font-size:12px">Gerado de: <code>${D.generated_from}</code></p>`;
}

function renderTaxonomy(c){
  const t = D.taxonomy;
  let html = "";
  for(const cat of t.categories){
    const terms = t.terms.filter(x=>x.cat===cat.key);
    html += `<h2 style="margin-top:36px">${cat.icon} ${cat.label} <span class="faint" style="font-size:13px;font-weight:400">— ${cat.hint} · ${terms.length} termos</span></h2>`;
    for(const x of terms){
      html += `<div class="term"><div class="term-head"><span class="term-name">${x.term}</span><span class="term-id">${x.id}</span></div><p class="term-def">${x.def}</p><p class="term-map">${x.map}</p><p class="faint" style="font-size:12px;margin:6px 0 0;font-style:italic">↳ ${x.analogy}</p></div>`;
    }
  }
  c.innerHTML = `<p class="eyebrow">Nomenclatura</p><h1>Taxonomia de produto</h1><p class="lede">${t.lede}</p><div class="callout">${t.callout}</div>${html}`;
}

function renderWorkflow(c){
  const w = D.workflow;
  const chk = items => items.map(i=>`<li class="chk"><span class="box">☐</span>${i}</li>`).join("");
  const phases = w.phases.map(p=>`<div class="card" style="margin-bottom:14px"><p class="card-title"><span style="font-size:18px">${p.icon}</span> Fase ${p.n} — ${p.title} <span class="pill muted" style="margin-left:auto">${p.owner}</span></p><p class="muted" style="font-size:14px;margin:0 0 14px">${p.goal}</p><div class="grid grid-2" style="margin-bottom:14px"><div><p class="slab">Entrada (critérios)</p><ul style="margin:0;padding:0">${chk(p.entrada)}</ul></div><div><p class="slab">Saída (verificável)</p><ul style="margin:0;padding:0">${chk(p.saida)}</ul></div></div><p style="font-size:13px;margin:0 0 10px"><span class="pill ok">Métrica</span> <span class="muted mono" style="font-size:12px">${p.metric}</span></p><div class="phase-fail"><span class="pill wip">Se gate vermelho</span> <span class="muted"> → volta à <b>Fase ${p.fail.to}</b>: ${p.fail.action}</span></div></div>`).join("");
  c.innerHTML = `<p class="eyebrow">Engenharia</p><h1>Workflow reproduzível</h1><p class="lede">${w.lede}</p><div class="callout">${w.callout}</div>${phases}`;
}

function renderAdrs(c){
  const rows = D.adrs.map(a=>`<div class="card"><p class="card-title">ADR ${a.n} <span class="pill ok">${a.status||""}</span></p><p style="font-size:13.5px;font-weight:650;margin:0 0 6px">${a.title||""}</p><p class="muted" style="font-size:12.5px;margin:0 0 8px;line-height:1.5">${a.description||""}</p><p class="faint" style="font-size:11.5px;margin:0"><b>Princípios tocados:</b> ${a.principios||"—"}</p><p class="faint" style="font-size:11px;margin:6px 0 0"><a href="../../${a.path}">${a.path}</a></p></div>`).join("");
  c.innerHTML = `<p class="eyebrow">Engenharia</p><h1>Registros de decisão (ADRs)</h1><p class="lede">Decisões datadas e imutáveis: corrigem-se com um ADR novo que declare a sucessão nos dois textos, nunca reescrevendo o antigo — e um <i>guard hook</i> recusa a reescrita. Todo ADR daqui declara os <b>princípios tocados</b>, com <code>nenhum</code> escrito por extenso quando for o caso.</p><div class="callout"><b>Barra:</b> formato herdado do corpus da irmã <b>gestaodeprioridades</b> — contexto, decisão numerada, <b>alternativas descartadas com número real executado</b>, consequências com pelo menos uma negativa, e "o que este ADR não decide".</div><div class="grid grid-2">${rows}</div>`;
}

function renderPrinciples(c){
  const rows = D.principles.map(p=>`<div class="card"><p class="card-title">${p.id} — ${p.title} ${p.hard?'<span class="pill wip">INEGOCIÁVEL</span>':'<span class="pill muted">negociável por ADR</span>'}</p><p class="muted" style="font-size:13px;margin:0">${p.d}</p></div>`).join("");
  c.innerHTML = `<p class="eyebrow">Engenharia</p><h1>Princípios do projeto (P1–P7)</h1><p class="lede">A constituição própria deste repositório, lida de <code>docs/governance/constitution.md</code>. Ela não substitui a constituição do método (princípios I–VIII do Maestro): as duas valem, e todo <code>plan.md</code> traz as <b>duas</b> tabelas de Constitution Check — um plano com só a primeira está incompleto.</p><div class="callout"><b>Barra:</b> um princípio só existe se algo o reprova. Cada P tem função de aptidão executável em <code>scripts/</code>; princípio sem portão é retórica.</div><div class="grid grid-2">${rows}</div>`;
}

function renderArtifacts(c){
  let html = `<p class="eyebrow">Engenharia</p><h1>Artefatos</h1><p class="lede">O que este repositório carrega além das specs: as skills que comandam o comportamento dos agentes, os portões executáveis e as jornadas vivas.</p><div class="callout"><b>Barra:</b> um artefato só existe se for insumo consumido com função forçante (princípio VI do Maestro). Documento que ninguém lê e nenhum portão confere é peso morto, e sai.</div>`;
  if(D.skills.length){ html += `<h2>Skills (${D.skills.length})</h2><div class="grid grid-2">` + D.skills.map(s=>`<div class="card"><p class="card-title">${s.name}</p><p class="muted" style="font-size:12.5px;margin:0">${s.description}</p><p class="faint" style="font-size:11px;margin:6px 0 0"><a href="../../${s.path}">${s.path}</a></p></div>`).join("") + `</div>`; }
  if(D.scripts.length){ html += `<h2>Portões executáveis (${D.scripts.length})</h2><div class="grid grid-2">` + D.scripts.map(s=>`<div class="card"><p class="card-title"><code>${s.name}</code> <span class="pill muted" style="margin-left:auto">${s.type}</span></p><p class="muted" style="font-size:12.5px;margin:0">${s.description||"—"}</p></div>`).join("") + `</div>`; }
  html += `<h2>Jornadas vivas (${D.journeys.length})</h2>`;
  if(D.journeys.length){ html += D.journeys.map(j=>`<div class="card"><p class="card-title">${j.name}</p><p class="muted" style="font-size:13px;margin:0">${j.steps} passos</p></div>`).join(""); }
  else { html += `<div class="callout"><b>Zero — e é decisão, não atraso.</b> ${D.journeys_note}</div>`; }
  c.innerHTML = html;
}

function renderMetrics(c){
  const rows = D.metrics.map(([k,v])=>`<dt>${k}</dt><dd><strong>${v}</strong></dd>`).join("");
  c.innerHTML = `<p class="eyebrow">Métricas</p><h1>Estado quantificado</h1><p class="lede">Todos os números desta página são <b>contados pelo gerador</b> ao ler o repositório — nenhum é digitado à mão. Reexecutar <code>tools/product-site/generate.py</code> reproduz esta tabela ou o site diverge do commitado, que é o portão do ciclo 012.</p><div class="callout"><b>Barra:</b> regra R1 do projeto — número só entra em documento depois de executado, com a saída colada. A última linha desta tabela é a que mais importa hoje.</div><div class="card"><dl class="kv-wide">${rows}</dl></div>`;
}

go(location.hash.slice(1)||"overview");
</script>""".replace("__PAYLOAD__", payload_json)

    return _page(f'{project.get("name","")} — Produto', "", "index", project, data,
                 extra_css=_INDEX_CSS, script=script)


# ──────────────────────────────────────────────────────────────────────
# modules.html — M1–M8 e as 12 specs
# ──────────────────────────────────────────────────────────────────────

_MODULES_CSS = """
.summary{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:24px}
@media(max-width:860px){.summary{grid-template-columns:repeat(3,1fr)}}
@media(max-width:520px){.summary{grid-template-columns:repeat(2,1fr)}}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 14px;box-shadow:var(--shadow)}
.stat .v{font-size:22px;font-weight:800;letter-spacing:-.02em;line-height:1.1}
.stat .k{font-size:10.5px;font-weight:600;color:var(--faint);text-transform:uppercase;letter-spacing:.06em;margin-top:3px}
.jumpbar{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:18px}
.jumpbar a{font-size:12px;font-weight:600;font-family:var(--font-mono);background:var(--surface);border:1px solid var(--border);border-radius:7px;padding:5px 10px;color:var(--muted)}
.jumpbar a:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.mod{background:var(--surface);border:1px solid var(--border);border-radius:12px;box-shadow:var(--shadow);margin-bottom:12px;padding:18px 22px 20px}
.mod-head{display:flex;align-items:flex-start;gap:12px;margin-bottom:10px}
.mod-tag{flex-shrink:0;width:38px;height:38px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;color:#fff;letter-spacing:-.02em}
.mod-title{font-size:16px;font-weight:700;letter-spacing:-.01em;margin:0 0 2px}
.mod-sub{font-size:12.5px;color:var(--muted);margin:0}
.mod-sub .sep{color:var(--border-strong);margin:0 5px}
.mod-status{margin-left:auto;flex-shrink:0;font-size:11px;font-weight:600;padding:3px 9px;border-radius:999px;align-self:flex-start}
.mod-status.tv{background:var(--surface-2);color:var(--faint)}
.mod-status.wip{background:rgba(176,107,0,.12);color:var(--amber)}
.vision{font-size:13.5px;color:var(--muted);margin:0 0 12px;max-width:78ch;line-height:1.55}
.deps{font-size:12.5px;margin:0 0 12px;padding:7px 11px;background:var(--surface-2);border:1px solid var(--border);border-radius:7px}
.deps b{color:var(--ink);font-weight:650}
.mod-body{display:grid;grid-template-columns:1.55fr 1fr;gap:20px}
@media(max-width:760px){.mod-body{grid-template-columns:1fr}}
.slabel{font-size:10.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin:0 0 7px}
.features{display:flex;flex-direction:column;gap:0}
.feat{display:flex;align-items:baseline;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px;line-height:1.4}
.feat:last-child{border-bottom:none}
.feat-name{font-weight:650;color:var(--ink);flex-shrink:0}
.feat-desc{color:var(--muted);flex:1;min-width:0}
.feat-meta{font-family:var(--font-mono);font-size:10.5px;color:var(--faint);flex-shrink:0;white-space:nowrap}
.mgrid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-bottom:14px}
@media(max-width:520px){.mgrid{grid-template-columns:repeat(3,1fr)}}
.mcell{background:var(--surface-2);border:1px solid var(--border);border-radius:7px;padding:8px 10px}
.mcell .mv{font-size:17px;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.mcell .mk{font-size:9.5px;font-weight:600;color:var(--faint);text-transform:uppercase;letter-spacing:.05em;margin-top:2px}
.tv-note{font-size:12.5px;color:var(--muted);padding:9px 11px;background:var(--surface-2);border:1px solid var(--border);border-radius:7px;margin-bottom:14px}
.links{display:flex;flex-wrap:wrap;gap:8px}
.links a{font-size:11.5px;font-weight:600;font-family:var(--font-mono);background:var(--surface-2);border:1px solid var(--border);border-radius:6px;padding:4px 9px;color:var(--muted)}
.links a:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
@media(max-width:720px){.main{padding:28px 18px 80px}.sidebar{display:none}}
"""


def _render_modules(data: dict, project: dict) -> str:
    modules = data.get("modules", [])
    specs = data.get("specs", [])
    counts = data.get("counts", {})

    summary = [
        ("Módulos", counts.get("modules", 0)),
        ("Épicos", sum(len(m.get("epics", [])) for m in modules)),
        ("Specs", counts.get("specs", 0)),
        ("RF", counts.get("rf", 0)),
        ("RI", counts.get("ri", 0)),
        ("RNF", counts.get("rnf", 0)),
    ]
    summary_html = '<div class="summary">' + "".join(
        f'<div class="stat"><div class="v">{v}</div><div class="k">{_e(k)}</div></div>'
        for k, v in summary) + "</div>"

    jumpbar = '<div class="jumpbar">' + "".join(
        f'<a href="#{m["id"]}">{m["id"]}</a>' for m in modules
    ) + "".join(f'<a href="#spec-{s["id"]}">{s["id"]}</a>' for s in specs) + "</div>"

    mods_html = ""
    for m in modules:
        feats = "".join(
            f'<div class="feat"><span class="feat-name">{_e(e["id"])}</span>'
            f'<span class="feat-desc"><b>{_md(e["n"])}</b> — {_md(e["d"])}</span></div>'
            for e in m.get("epics", []))
        spec_links = "".join(
            f'<a href="{_up("specs/" + sn["dir"] + "/spec.md")}">📄 spec {sn["num"]}</a>'
            for sn in m.get("specNames", []))
        cycles = ", ".join(sn["num"] for sn in m.get("specNames", [])) or "—"
        shared_note = ""
        if m.get("shared"):
            shared_note = ('<div class="tv-note">Contagem honesta: a spec '
                           + ", ".join(_e(s) for s in m["shared"])
                           + " entrega recortes de mais de um módulo, e os requisitos dela contam "
                             "inteiros nos dois. O corte fino por épico está na própria spec.</div>")
        mods_html += f"""
  <div class="mod" id="{_e(m["id"])}">
    <div class="mod-head">
      <div class="mod-tag" style="background:{_e(m.get("color","#5b5bd6"))}">{_e(m["id"])}</div>
      <div>
        <p class="mod-title">{_e(m["id"])} — {_md(m["name"])}</p>
        <p class="mod-sub"><i>Bounded context</i>: {_md(m.get("context",""))}<span class="sep">·</span>ciclo(s) {_e(cycles)}</p>
      </div>
      <span class="mod-status wip">planejado</span>
    </div>
    <p class="vision">{_md(m.get("job",""))}</p>
    <p class="deps"><b>Depende de:</b> {_md(m.get("deps","—"))}<br><b>Origem:</b> {_md(m.get("origin",""))}</p>
    <div class="mod-body">
      <div>
        <p class="slabel">Épicos ({len(m.get("epics", []))})</p>
        <div class="features">{feats}</div>
      </div>
      <div>
        <p class="slabel">Requisitos nas specs que o entregam</p>
        <div class="mgrid">
          <div class="mcell"><div class="mv">{m.get("rf",0)}</div><div class="mk">RF</div></div>
          <div class="mcell"><div class="mv">{m.get("ri",0)}</div><div class="mk">RI</div></div>
          <div class="mcell"><div class="mv">{m.get("rnf",0)}</div><div class="mk">RNF</div></div>
          <div class="mcell"><div class="mv">{m.get("rn",0)}</div><div class="mk">RN</div></div>
          <div class="mcell"><div class="mv">{m.get("int",0)}</div><div class="mk">INT</div></div>
        </div>
        {shared_note}
        <p class="slabel">Links</p>
        <div class="links">{spec_links}<a href="{_up("docs/produto/modulos.md")}">🗺️ modulos.md</a></div>
      </div>
    </div>
  </div>"""

    specs_html = ""
    for s in specs:
        feats = "".join(
            f'<div class="feat"><span class="feat-name">{_md(f["n"])}</span>'
            f'<span class="feat-desc">{_e(f["d"])}</span></div>' for f in s.get("features", []))
        arts = "".join(
            f'<a href="{_up(a["path"])}">📋 {_e(a["name"])}</a>' for a in s.get("artifacts", []))
        mods = ", ".join(s.get("modules", [])) or "transversal"
        lac = "".join(f'<div class="feat"><span class="feat-name">{_e(l["id"])}</span>'
                      f'<span class="feat-desc">{_md(l["d"])}</span></div>'
                      for l in s.get("lacunas", []))
        specs_html += f"""
  <div class="mod" id="spec-{_e(s["id"])}">
    <div class="mod-head">
      <div class="mod-tag" style="background:#5b5bd6">{_e(s["id"])}</div>
      <div>
        <p class="mod-title">Spec {_e(s["id"])} — {_md(s["name"])}</p>
        <p class="mod-sub">Módulos: {_e(mods)}<span class="sep">·</span>raia {_e(s.get("raia",""))}<span class="sep">·</span>{s.get("rf",0)} RF · {s.get("ri",0)} RI · {s.get("rnf",0)} RNF</p>
      </div>
      <span class="mod-status tv">{_e(s.get("status",""))}</span>
    </div>
    <p class="vision">{_md(s.get("vision",""))}</p>
    <div class="mod-body">
      <div>
        <p class="slabel">Features declaradas ({len(s.get("features", []))})</p>
        <div class="features">{feats}</div>
      </div>
      <div>
        <p class="slabel">Lacunas declaradas ({len(s.get("lacunas", []))})</p>
        <div class="features">{lac or '<div class="feat"><span class="feat-desc">nenhuma</span></div>'}</div>
        <p class="slabel" style="margin-top:12px">Dúvidas em aberto</p>
        <div class="tv-note">{len(s.get("clarify", []))} no <code>## Clarify</code>, levadas ao gate humano — nenhuma resolvida em silêncio.</div>
        <p class="slabel">Artefatos</p>
        <div class="links"><a href="{_up(s["specPath"])}">📄 spec.md</a>{arts}</div>
      </div>
    </div>
  </div>"""

    body = f"""\
    <p class="eyebrow">Produto</p>
    <h1>Módulos (M1–M8) e specs</h1>
    <p class="lede">Cada módulo é um <i>bounded context</i> do Design Orientado a Domínio (DDD) e um
    <strong>épico de produto</strong>, decomposto em épicos numerados (E&lt;m&gt;.&lt;n&gt;) que as specs
    quebram em features, user stories e requisitos. O mapa é lido de
    <code>docs/produto/modulos.md</code>; os requisitos, das 12 specs.</p>
    {summary_html}
    <div class="callout"><b>Barra:</b> hierarquia módulo → épico → feature → story medida contra o
    <b>Atlassian Agile Coach</b>, e profundidade de requisitos contra a spec 001 do <b>PROJETO_ECS</b>;
    densidade e conteúdo sempre aberto (sem sanfonas) pela <b>régua Linear</b>.</div>
    {jumpbar}
    <h2>Os oito módulos</h2>
    {mods_html}
    <h2>As doze specs</h2>
    <p class="muted" style="font-size:13.5px">Uma spec por ciclo do roadmap. As specs 001, 002 e 012
    são transversais — não entregam um módulo, e sim o corpus, o protótipo descartável e o fechamento
    com autodeclaração.</p>
    {specs_html}"""

    return _page(f'{project.get("name","")} — Módulos', body, "modules", project, data,
                 extra_css=_MODULES_CSS)


# ──────────────────────────────────────────────────────────────────────
# traceability.html — RF + RI + RNF com fontes
# ──────────────────────────────────────────────────────────────────────

_TRACE_CSS = """
.grid-3{grid-template-columns:repeat(3,1fr)}
@media(max-width:900px){.grid-3{grid-template-columns:1fr}}
.pill.rf{background:rgba(91,91,214,.12);color:var(--accent)}
.pill.ri{background:rgba(15,118,110,.14);color:#0f766e}
.pill.rnf{background:rgba(43,108,176,.12);color:var(--blue)}
.stat-tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 18px;text-align:center}
.stat-tile .num{font-size:28px;font-weight:800;letter-spacing:-.02em;color:var(--ink)}
.stat-tile .lbl{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin-top:2px}
.req-row{display:grid;grid-template-columns:74px 1fr 132px;gap:8px 12px;align-items:start;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px}
.req-row:last-child{border-bottom:none}
.req-row .req-id{font-family:var(--font-mono);font-size:11.5px;font-weight:600;color:var(--accent);white-space:nowrap}
.req-row.ri .req-id{color:#0f766e}
.req-row.rnf .req-id{color:var(--blue)}
.req-row .req-desc{color:var(--ink);line-height:1.45}
.req-row .req-group{display:block;font-size:10.5px;color:var(--faint);font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px}
.req-row .req-src{font-size:10.5px;color:var(--faint);font-family:var(--font-mono);text-align:right;white-space:normal}
.req-row .req-src a,.req-row .req-src span.ext{color:var(--faint);text-decoration:none;border-bottom:1px dotted var(--border-strong);cursor:help}
.req-row .req-src a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.st-pill{display:inline-block;font-size:9px;font-weight:700;padding:1px 5px;border-radius:4px;letter-spacing:.02em;vertical-align:middle;margin-right:3px}
.st-pill.ok{background:rgba(26,122,76,.15);color:var(--green)}
.st-pill.wip{background:rgba(176,107,0,.15);color:var(--amber)}
.st-pill.na{background:var(--surface-2);color:var(--faint)}
.fwd-row{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:8px 0 10px;font-size:11px}
.fwd-label{color:var(--faint);font-weight:600;text-transform:uppercase;letter-spacing:.05em;font-size:9.5px}
.fwd-link{font-family:var(--font-mono);font-size:10.5px;padding:2px 7px;border-radius:5px;background:var(--surface-2);border:1px solid var(--border);color:var(--muted);text-decoration:none;white-space:nowrap}
.fwd-link:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.fwd-link.todo{color:var(--faint);border-style:dashed}
.fwd-link.pending{color:var(--amber)}
.fwd-arrow{color:var(--faint);font-size:10px}
.fwd-ac{font-size:11px;color:var(--muted);font-style:italic;margin-left:8px}
.module-section{margin-bottom:36px}
.module-header{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px}
.module-header .m-id{font-family:var(--font-mono);font-size:13px;font-weight:700;color:var(--accent);background:var(--accent-soft);padding:4px 10px;border-radius:7px}
.module-header .m-name{font-size:18px;font-weight:700;letter-spacing:-.01em}
.module-header .m-links{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.module-header .m-links a{font-size:12px;font-weight:500;padding:4px 10px;border-radius:6px;border:1px solid var(--border);background:var(--surface)}
.source-list{font-size:12px;color:var(--muted);margin:0 0 16px;line-height:1.9}
.source-list .src-tag{font-family:var(--font-mono);font-size:11px;background:var(--surface-2);border:1px solid var(--border);padding:1px 6px;border-radius:4px;margin-right:6px;display:inline-block;margin-bottom:2px;color:var(--muted);text-decoration:none;cursor:help}
.source-list .src-tag:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.req-table{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 18px;box-shadow:var(--shadow);margin-bottom:14px}
.req-table .rt-head{display:grid;grid-template-columns:74px 1fr 132px;gap:10px 14px;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);padding-bottom:8px;border-bottom:1px solid var(--border);margin-bottom:4px}
.req-table .rt-head .rt-src{text-align:right}
.filter-bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.filter-chip{font-size:12px;font-weight:600;padding:5px 12px;border-radius:999px;border:1px solid var(--border);background:var(--surface);cursor:pointer;color:var(--muted);font-family:inherit}
.filter-chip:hover{border-color:var(--accent);color:var(--ink)}
.filter-chip.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.search-box{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--ink);font-size:14px;font-family:inherit;margin-bottom:16px}
.search-box:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
"""


def _render_traceability(data: dict, project: dict) -> str:
    tr = data.get("traceability", {})
    payload = {
        "modules": tr.get("modules", []),
        "callout": tr.get("callout", ""),
        "counts": data.get("counts", {}),
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    script = """<script>
const D = __PAYLOAD__;
const MODULES = D.modules;
const el = document.getElementById("content");
let specFilter = "all";
let typeFilter = "all";
let searchTerm = "";
const KINDS = [
  {key:"rfs", id:"RF", label:"Requisitos funcionais", cls:"rf", head:"Requisito funcional (forma EARS)"},
  {key:"ris", id:"RI", label:"Requisitos de interface", cls:"ri", head:"Requisito de interface (tela, estado, acessibilidade)"},
  {key:"rnfs", id:"RNF", label:"Requisitos não funcionais", cls:"rnf", head:"Requisito não funcional (desempenho, segurança, observabilidade)"}
];

function totals(){
  let t = {rf:0, ri:0, rnf:0, src:0, comFonte:0, total:0};
  MODULES.forEach(m=>{
    t.rf+=m.rfs.length; t.ri+=m.ris.length; t.rnf+=m.rnfs.length; t.src+=m.sources.length;
    ["rfs","ris","rnfs"].forEach(k=>m[k].forEach(r=>{ t.total++; if(r.s) t.comFonte++; }));
  });
  return t;
}

function seal(r){
  if(r.seal==="🟢") return '<span class="st-pill ok" title="confirmado com arquivo:linha">🟢</span>';
  if(r.seal==="🔴") return '<span class="st-pill na" title="lacuna">🔴</span>';
  if(r.seal==="🟡") return '<span class="st-pill wip" title="planejado">🟡</span>';
  return '';
}

function srcLinks(r, m){
  if(!r.s) return '<span class="faint" title="requisito sem fonte na linhagem: nasce da norma ou da decisão deste projeto">—</span>';
  return r.s.split(", ").map(tag=>{
    const s = m.sources.find(x=>x.tag===tag);
    if(!s) return tag;
    if(s.internal) return `<a href="../../${s.rel}" title="${s.t}">${tag}</a>`;
    return `<span class="ext" title="${s.t}">${tag}</span>`;
  }).join(" ");
}

function chainRow(m){
  const parts = m.chain.map(c=>{
    const cls = c.state==="todo" ? "fwd-link todo" : (c.state==="pending" ? "fwd-link pending" : "fwd-link");
    return c.href ? `<a class="${cls}" href="../../${c.href}">${c.label}</a>` : `<span class="${cls}">${c.label}</span>`;
  });
  return `<div class="fwd-row"><span class="fwd-label">cadeia forward do ciclo</span> ${parts.join(' <span class="fwd-arrow">→</span> ')} <span class="fwd-ac">↳ a cadeia é do ciclo, não do requisito: nenhum requisito tem código hoje, e fingir granularidade seria mentir</span></div>`;
}

function renderOverview(){
  const t = totals();
  const pct = t.total ? Math.round(t.comFonte/t.total*100) : 0;
  const tiles = `
    <div class="grid grid-3" style="margin-bottom:14px">
      <div class="stat-tile"><div class="num">${t.rf}</div><div class="lbl">Requisitos funcionais</div></div>
      <div class="stat-tile"><div class="num">${t.ri}</div><div class="lbl">Requisitos de interface</div></div>
      <div class="stat-tile"><div class="num">${t.rnf}</div><div class="lbl">Requisitos não funcionais</div></div>
    </div>
    <div class="grid grid-3" style="margin-bottom:28px">
      <div class="stat-tile"><div class="num">${t.src}</div><div class="lbl">Fontes declaradas (F-NN)</div></div>
      <div class="stat-tile"><div class="num">${t.total}</div><div class="lbl">Requisitos totais</div></div>
      <div class="stat-tile"><div class="num">${pct}%</div><div class="lbl">Citam uma fonte</div></div>
    </div>`;
  const cards = MODULES.map(m=>`
    <div class="card" style="cursor:pointer" onclick="setSpec('${m.id}')">
      <p class="card-title"><span class="pill rf">${m.id}</span> ${m.name}</p>
      <p class="card-sub">${m.rfs.length} RF · ${m.ris.length} RI · ${m.rnfs.length} RNF · ${m.sources.length} fontes</p>
      <p class="muted" style="font-size:12px;margin:0">Módulos: ${(m.modules&&m.modules.length)?m.modules.join(", "):"transversal"} · <a href="../../${m.specPath}" onclick="event.stopPropagation()">spec.md</a></p>
    </div>`).join("");
  return `
    <p class="eyebrow">Rastreabilidade</p>
    <h1>Matriz de rastreabilidade</h1>
    <p class="lede">A cadeia inteira, nos dois sentidos. <b>Backward</b>: cada requisito cita as fontes F-NN da sua spec, com <code>arquivo:linha</code> na linhagem TOC-Builder, na norma APH ou na plataforma. <b>Forward</b>: spec → plan → tasks → contratos → qa-report → código do ciclo. Clique num ciclo para abrir os seus requisitos.</p>
    <div class="callout">${D.callout}</div>
    ${tiles}
    <h2>Resumo por ciclo</h2>
    <div class="grid grid-2">${cards}</div>`;
}

function renderModule(m){
  const sources = m.sources.map(s=>{
    return s.internal ? `<a class="src-tag" href="../../${s.rel}" title="${s.t}">${s.tag} ${s.seal||""}</a>`
                      : `<span class="src-tag" title="${s.t}">${s.tag} ${s.seal||""}</span>`;
  }).join("");
  let tables = "";
  for(const k of KINDS){
    if(typeFilter!=="all" && typeFilter!==k.id) continue;
    const rows = m[k.key];
    if(!rows.length) continue;
    const html = rows.map(r=>`<div class="req-row ${k.cls}"><span class="req-id">${seal(r)}${r.id}</span><span class="req-desc">${r.group?`<span class="req-group">${r.group}</span>`:""}${r.d}</span><span class="req-src">${srcLinks(r,m)}</span></div>`).join("");
    tables += `<div class="req-table"><div class="rt-head"><span>ID</span><span>${k.head} — ${rows.length} ${k.id}</span><span class="rt-src">Fonte (backward)</span></div>${html}</div>`;
  }
  return `
    <div class="module-section" data-mid="${m.id}">
      <div class="module-header">
        <span class="m-id">${m.id}</span>
        <span class="m-name">${m.name}</span>
        <span class="m-links">
          <span class="st-pill wip">${(m.modules&&m.modules.length)?m.modules.join(" "):"transversal"}</span>
          <a href="../../${m.specPath}">spec.md</a>
        </span>
      </div>
      ${chainRow(m)}
      <div class="source-list"><strong>Fontes consultadas:</strong> ${sources||"—"}</div>
      ${tables||'<div class="callout">Nenhum requisito deste tipo nesta spec.</div>'}
    </div>`;
}

function renderFiltered(){
  let html = `
    <p class="eyebrow">Rastreabilidade</p>
    <h1>Matriz de rastreabilidade</h1>
    <p class="lede">Requisito → fonte (backward) e ciclo → artefatos (forward). Filtre por tipo ou por ciclo, ou busque por identificador, texto e fonte.</p>
    <input class="search-box" id="searchBox" placeholder="Buscar por identificador, texto ou fonte (ex.: UDE, F-06, snapshot)..." value="${searchTerm}">
    <div class="filter-bar">
      <button class="filter-chip type" data-type="all">Todos os tipos</button>
      <button class="filter-chip type" data-type="RF">RF</button>
      <button class="filter-chip type" data-type="RI">RI</button>
      <button class="filter-chip type" data-type="RNF">RNF</button>
    </div>
    <div class="filter-bar">
      <button class="filter-chip spec" data-spec="all">Todos os ciclos</button>
      ${MODULES.map(m=>`<button class="filter-chip spec" data-spec="${m.id}">${m.id}</button>`).join("")}
    </div>`;
  let mods = specFilter==="all" ? MODULES : MODULES.filter(m=>m.id===specFilter);
  if(searchTerm){
    const q = searchTerm.toLowerCase();
    const hit = r => r.id.toLowerCase().includes(q) || (r.d||"").toLowerCase().includes(q) || (r.s||"").toLowerCase().includes(q) || (r.group||"").toLowerCase().includes(q);
    mods = mods.map(m=>({...m, rfs:m.rfs.filter(hit), ris:m.ris.filter(hit), rnfs:m.rnfs.filter(hit)}))
               .filter(m=>m.rfs.length||m.ris.length||m.rnfs.length);
  }
  const shown = mods.reduce((a,m)=>a+m.rfs.length+m.ris.length+m.rnfs.length,0);
  html += `<p class="faint" style="font-size:12px">${shown} requisitos em ${mods.length} ciclo(s) — a contagem é do filtro atual, não do repositório inteiro.</p>`;
  if(!mods.length) html += `<div class="callout">Nenhum requisito encontrado para "${searchTerm}".</div>`;
  else mods.forEach(m=>{ html += renderModule(m); });
  return html;
}

function render(){
  if(specFilter==="all" && typeFilter==="all" && !searchTerm){ el.innerHTML = renderOverview(); }
  else {
    el.innerHTML = renderFiltered();
    const sb = document.getElementById("searchBox");
    if(sb){ sb.addEventListener("input", e=>{ searchTerm=e.target.value; render(); const s2=document.getElementById("searchBox"); if(s2){ s2.focus(); s2.setSelectionRange(s2.value.length,s2.value.length);} }); }
  }
  document.querySelectorAll(".filter-chip.spec").forEach(b=>b.classList.toggle("active", b.dataset.spec===specFilter));
  document.querySelectorAll(".filter-chip.type").forEach(b=>b.classList.toggle("active", b.dataset.type===typeFilter));
  document.querySelectorAll(".filter-chip.spec").forEach(b=>b.addEventListener("click",()=>setSpec(b.dataset.spec)));
  document.querySelectorAll(".filter-chip.type").forEach(b=>b.addEventListener("click",()=>setType(b.dataset.type)));
}
function setSpec(f){ specFilter=f; render(); window.scrollTo(0,0); }
function setType(t){ typeFilter=t; if(specFilter==="all"&&!searchTerm&&t!=="all"){} render(); window.scrollTo(0,0); }
render();
</script>""".replace("__PAYLOAD__", payload_json)

    return _page(f'{project.get("name","")} — Rastreabilidade', "", "traceability", project,
                 data, extra_css=_TRACE_CSS, script=script)


# ──────────────────────────────────────────────────────────────────────
# roadmap.html — os 12 ciclos de docs/roadmap.md
# ──────────────────────────────────────────────────────────────────────

_ROADMAP_CSS = """
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:8px}
@media(max-width:760px){.metrics{grid-template-columns:repeat(2,1fr)}}
.metric{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.metric .v{font-size:24px;font-weight:800;letter-spacing:-.02em;line-height:1.1}
.metric .k{font-size:12px;color:var(--faint);font-weight:600;margin-top:4px;letter-spacing:.02em}
.metric .v.green{color:var(--green)} .metric .v.accent{color:var(--accent)} .metric .v.amber{color:var(--amber)}
.metric .sub{font-size:11px;color:var(--faint);margin-top:3px}
.flow{display:flex;align-items:stretch;gap:0;margin:22px 0 6px;overflow-x:auto;padding-bottom:6px}
.flow-step{flex:1 1 0;min-width:150px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 14px 12px;position:relative;box-shadow:var(--shadow)}
.flow-step + .flow-step{margin-left:22px}
.flow-step + .flow-step::before{content:"";position:absolute;left:-15px;top:50%;width:14px;height:2px;background:var(--border-strong)}
.flow-step + .flow-step::after{content:"\\25B6";position:absolute;left:-9px;top:50%;transform:translateY(-50%);color:var(--faint);font-size:10px}
.flow-step .fn{font-family:var(--font-mono);font-size:11px;color:var(--accent);font-weight:600}
.flow-step .ft{font-weight:700;font-size:14px;margin:2px 0 4px}
.flow-step .fg{font-size:12px;color:var(--muted);margin:0;line-height:1.45}
.flow-step .gate{margin-top:8px;font-size:11px;color:var(--amber);font-weight:600;display:flex;align-items:center;gap:4px}
.band{margin:34px 0 6px}
.timeline{position:relative;padding-left:38px;border-left:2px solid var(--border)}
.tl-item{position:relative;margin-bottom:18px}
.tl-item::before{content:"";position:absolute;left:-44px;top:6px;width:14px;height:14px;border-radius:50%;background:var(--surface);border:3px solid var(--accent);box-shadow:0 0 0 4px var(--bg)}
.tl-item.fix::before{border-color:var(--amber)}
.tl-item.demo::before{border-color:var(--green)}
.tl-item.infra::before{border-color:var(--blue)}
.tl-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px 20px;box-shadow:var(--shadow);transition:border-color .15s, transform .15s}
.tl-card:hover{border-color:var(--border-strong);transform:translateY(-1px)}
.tl-top{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.tl-num{font-family:var(--font-mono);font-size:12px;font-weight:600;color:var(--faint);background:var(--surface-2);padding:2px 8px;border-radius:6px;border:1px solid var(--border)}
.tl-title{font-size:16px;font-weight:700;letter-spacing:-.01em;margin:0}
.tl-mod{font-family:var(--font-mono);font-size:11px;color:var(--accent);font-weight:600}
.tl-desc{font-size:13.5px;color:var(--muted);margin:0 0 10px;max-width:68ch}
.tl-meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:8px 0}
.pill.fix{background:rgba(176,107,0,.12);color:var(--amber)}
.pill.demo{background:rgba(43,108,176,.12);color:var(--blue)}
.artifacts{display:inline-flex;gap:5px;flex-wrap:wrap}
.artifacts a{font-size:10.5px;padding:1px 6px;font-family:var(--font-mono);background:var(--surface-2);border:1px solid var(--border);border-radius:5px;color:var(--muted);text-decoration:none}
.artifacts a:hover{border-color:var(--accent);color:var(--accent)}
.gatelist{margin:10px 0 0;padding:0;list-style:none}
.gatelist li{font-size:12.5px;color:var(--muted);line-height:1.5;padding-left:20px;position:relative;margin-bottom:5px}
.gatelist li::before{content:"⏳";position:absolute;left:0;top:0;font-size:11px}
.entrylist{margin:6px 0 0;padding:0;list-style:none}
.entrylist li{font-size:12.5px;color:var(--muted);line-height:1.5;padding-left:20px;position:relative;margin-bottom:5px}
.entrylist li::before{content:"⛔";position:absolute;left:0;top:0;font-size:10px}
.sublabel{font-size:10.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin:12px 0 2px}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:10px 0 0}
.legend span{display:inline-flex;align-items:center;gap:6px}
.dot{width:10px;height:10px;border-radius:50%;border:2.5px solid var(--accent);background:var(--bg)}
.dot.fix{border-color:var(--amber)} .dot.demo{border-color:var(--green)} .dot.infra{border-color:var(--blue)}
.horizons{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:18px 0}
@media(max-width:760px){.horizons{grid-template-columns:1fr}}
.horizon{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px 22px;box-shadow:var(--shadow)}
.horizon .h-label{font-size:13px;font-weight:700;margin-bottom:8px}
.horizon .h-title{font-size:15px;font-weight:650;margin-bottom:12px;color:var(--ink)}
.horizon ul{margin:0;padding-left:18px}
.horizon li{font-size:13px;color:var(--muted);margin-bottom:6px}
.horizon.done{border-left:3px solid var(--green)}
.horizon.now{border-left:3px solid var(--amber)}
.horizon.later{border-left:3px solid var(--accent)}
.callout.warn{border-left-color:var(--amber);background:rgba(176,107,0,.06)}
"""


def _render_roadmap(data: dict, project: dict) -> str:
    rm = data.get("roadmap", {})
    cycles = rm.get("cycles", [])
    counts = data.get("counts", {})
    phases = data.get("workflow", {}).get("phases", [])

    em_curso = [c for c in cycles if c["state"] == "em curso"]
    infra = [c for c in cycles if c["raia"] == "infra"]
    metrics = [
        ("amber", str(len(em_curso)), "Ciclos em curso", "nenhum promovido ainda"),
        ("", str(len(cycles)), "Ciclos propostos", "001 a 012"),
        ("accent", str(counts.get("requisitos", 0)), "Requisitos planejados", "RF + RI + RNF"),
        ("green", "0", "Linhas de código", "nada antes do ciclo 003"),
    ]
    metrics_html = '<div class="metrics">' + "".join(
        f'<div class="metric"><div class="v {c}">{_e(v)}</div><div class="k">{_e(k)}</div>'
        f'<div class="sub">{_e(sub)}</div></div>' for c, v, k, sub in metrics) + "</div>"

    horizons = [
        ("now", "🔸 Agora", "Ciclo 001 — em curso",
         ["Corpus de planejamento (specs, ADRs, roadmap, site)",
          "Aguarda o gate humano do Product Steward"]),
        ("later", "🔜 A seguir", "Ciclos 002–003",
         ["002 · protótipo descartável de interfaces",
          "003 · esqueleto federado — a junta fecha contra a ghdaru real (raia infra)"]),
        ("done", "🧭 Depois", "Ciclos 004–012",
         ["004–005 · núcleo de diagramas e Árvore da Realidade Atual",
          "006–008 · ações governadas, Nuvem de Conflito, árvores de futuro",
          "009–012 · focalização, Estratégia & Táticas, fundações, autodeclaração APH"]),
    ]
    horizons_html = '<div class="horizons">' + "".join(
        f'<div class="horizon {cls}"><div class="h-label">{_e(lbl)}</div>'
        f'<div class="h-title">{_e(title)}</div><ul>'
        + "".join(f"<li>{_e(i)}</li>" for i in items) + "</ul></div>"
        for cls, lbl, title, items in horizons) + "</div>"

    flow_html = '<div class="flow">' + "".join(
        f'<div class="flow-step"><div class="fn">Fase {p["n"]}</div><div class="ft">{_e(p["title"])}</div>'
        f'<div class="fg">{_e(p["owner"])}</div>'
        f'<div class="gate">⏳ {_e(p["metric"][:58])}…</div></div>' for p in phases) + "</div>"

    timeline = '<div class="timeline">'
    for c in cycles:
        cls = "fix" if c["state"] == "em curso" else c.get("cls", "")
        arts = "".join(f'<a href="{_up(a["href"])}">{_e(a["text"])}</a>' for a in c.get("artifacts", []))
        gates = "".join(f"<li>{_md(g)}</li>" for g in c.get("portoes", []))
        entry = "".join(f"<li>{_md(g)}</li>" for g in c.get("entrada", []))
        mods = " ".join(c.get("modules", []))
        reqs = (f'<span class="pill muted">{c["rf"]} RF · {c["ri"]} RI · {c["rnf"]} RNF</span>'
                if c.get("rf") or c.get("ri") or c.get("rnf") else "")
        state_pill = ('<span class="pill wip">em curso</span>' if c["state"] == "em curso"
                      else '<span class="pill muted">planejado</span>')
        timeline += f"""
      <div class="tl-item {cls}">
        <div class="tl-card">
          <div class="tl-top"><span class="tl-num">{_e(c["num"])}</span><span class="tl-title">{_md(c["title"])}</span><span class="tl-mod">{_e(mods)}</span></div>
          <p class="tl-desc">{_md(c["desc"])}</p>
          <div class="tl-meta">{state_pill}<span class="pill {"demo" if c["raia"] == "infra" else "muted"}">raia {_e(c["raia"])}</span>{reqs}<span class="artifacts">{arts}</span></div>
          <p class="sublabel">Portões deste ciclo ({len(c.get("portoes", []))})</p>
          <ul class="gatelist">{gates or "<li>—</li>"}</ul>
          <p class="sublabel">O que o ciclo não pode começar sem ({len(c.get("entrada", []))})</p>
          <ul class="entrylist">{entry or "<li>—</li>"}</ul>
        </div>
      </div>"""
    timeline += "</div>"

    legend_html = '<div class="legend">' + "".join(
        f'<span><span class="dot {l["cls"]}"></span> {_e(l["label"])}</span>'
        for l in rm.get("legend", [])) + "</div>"

    honesty = (
        "<b>Nota de honestidade.</b> Este roadmap é uma <b>sequência proposta</b>, não uma promessa "
        "de data — e o estado real, em 2026-09-03, é este: o <b>ciclo 001 está em curso</b> e ainda "
        "não passou pelo gate humano; <b>nenhum ciclo foi promovido</b>; existem <b>zero linhas de "
        "código de produção</b> no repositório (nenhuma nasce antes do ciclo 003, por decisão); os "
        "doze <code>qa-report.md</code> estão deliberadamente vazios, dizendo “ciclo planejado no "
        "001; execução ainda não iniciada”, porque caixa marcada não é testemunha; e <b>não há "
        "nenhuma jornada viva</b> — <code>docs/jornadas/</code> traz só a convenção, já que jornada "
        "sem captura de build real é ficção (princípio P6). Todo requisito das 12 specs nasce com "
        "selo 🟡 PLANEJADO; o selo 🟢 pertence às fontes medidas na linhagem, com "
        "<code>arquivo:linha</code>.")

    footer = (f'Gerado por <code>tools/product-site/generate.py</code> + '
              f'<code>render.py</code> a partir de <code>{_e(rm.get("source", "docs/roadmap.md"))}</code> — '
              f'{len(cycles)} ciclos lidos, nenhum digitado à mão (ADR 0008).')

    body = f"""
  <p class="eyebrow">{_e(rm.get("eyebrow", "Roadmap"))}</p>
  <h1>{_e(rm.get("title", "Roadmap"))}</h1>
  <p class="lede">{rm.get("lede", "")}</p>
  <div class="callout">{rm.get("callout", "")}</div>
  <h2>Estado quantificado</h2>
  {metrics_html}
  <h2>Horizonte — Agora / A seguir / Depois</h2>
  {horizons_html}
  <h2>As oito fases que cada ciclo percorre</h2>
  <p class="muted" style="font-size:13.5px">O fluxo do método Maestro, com dono e métrica por fase.
  A descrição completa, com critérios de entrada, saídas e arestas de falha, está no
  <a href="index.html#workflow">workflow</a>.</p>
  {flow_html}
  <h2>Linha do tempo dos ciclos</h2>
  {legend_html}
  <div class="band">{timeline}</div>
  <div class="divider"></div>
  <div class="callout warn">{honesty}</div>
  <p class="faint" style="font-size:12px">{footer}</p>
"""
    return _page(f'{project.get("name","")} — Roadmap', body, "roadmap", project, data,
                 extra_css=_ROADMAP_CSS)


# ──────────────────────────────────────────────────────────────────────
# Entrada
# ──────────────────────────────────────────────────────────────────────

def render(data: dict, output_dir: str | Path) -> list[str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    project = data.get("project", {})
    _prep(data)

    css_src = Path(__file__).parent / "templates" / "styles.css"
    if not css_src.exists():
        raise SystemExit(f"styles.css não encontrado em {css_src}")
    shutil.copy2(css_src, out / "styles.css")

    pages = {
        "index.html": _render_index(data, project),
        "modules.html": _render_modules(data, project),
        "traceability.html": _render_traceability(data, project),
        "roadmap.html": _render_roadmap(data, project),
    }
    written = ["styles.css"]
    for name, html in pages.items():
        (out / name).write_text(html, encoding="utf-8")
        written.append(name)
    return written


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Renderiza o site de produto da TOC Federada")
    parser.add_argument("input", help="Arquivo JSON produzido por generate.py")
    parser.add_argument("--output", "-o", default="docs/product-site", help="Diretório de saída")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    written = render(data, args.output)
    for name in written:
        p = Path(args.output) / name
        print(f"  {p} ({p.stat().st_size} bytes)", file=sys.stderr)
    print(f"Site renderizado em {args.output}/", file=sys.stderr)


if __name__ == "__main__":
    main()
