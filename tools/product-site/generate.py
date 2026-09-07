"""generate.py — descoberta e extração para o site de produto da TOC Federada.

Origem: `GHDaru/daruskills`, skill `spec-to-code-docs` (generate.py). Vendorizado e
adaptado neste repositório por decisão do ADR 0008 — o site é gerado por script
versionado, nunca escrito à mão. O que mudou em relação ao original está listado em
`tools/product-site/README.md`.

Varre o diretório do projeto e produz um dicionário JSON consumido por `render.py`.
Somente biblioteca padrão.

Uso:
    python tools/product-site/generate.py . --output docs/product-site/data.json

Sem `--output`, o JSON vai para a saída padrão.

Siglas usadas neste arquivo: TOC — Teoria das Restrições; UDE — Efeito Indesejável;
ARA — Árvore da Realidade Atual; NC — Nuvem de Conflito; ARF — Árvore da Realidade
Futura; APR — Árvore de Pré-Requisitos; AT — Árvore de Transição; S&T — Árvore de
Estratégia & Táticas; OI — Objetivo Intermediário; APH — o padrão Aplicação ↔ Harness;
ADR — Architecture Decision Record (Registro de Decisão Arquitetural); RF/RI/RNF/RN/INT —
requisito funcional / de interface / não funcional / regra de negócio / integração;
DoR — Definition of Ready; DoD — Definition of Done; DDD — Domain-Driven Design;
FSM — máquina de estados finitos; OTel — OpenTelemetry.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import posixpath
import re
import sys
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _first_line_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _strip_emphasis(s: str) -> str:
    """Remove ênfase markdown (**negrito**, *itálico*, `código`) de uma string."""
    return re.sub(r"`?\*{1,2}(.*?)\*{1,2}`?", r"\1", s).strip()


def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


def _delink(s: str, base: str = "") -> str:
    """Troca o link markdown pelo caminho que ele aponta, resolvido a partir da raiz do
    repositório e em fonte de código.

    Sem isto, a prosa extraída chegaria ao navegador como `[`visao.md`](visao.md)` — texto
    cru de markdown numa página HTML, que é o cheiro de gerador que não lê o que copia.
    O caminho resolvido é mais útil que o rótulo: diz onde o fato mora.
    """
    def rep(m: re.Match[str]) -> str:
        label = m.group(1).strip().strip("`")
        target = m.group(2)
        if target.startswith(("http://", "https://", "#", "mailto:")):
            return label or target
        path = posixpath.normpath(posixpath.join(base, target)) if base else posixpath.normpath(target)
        return f"`{path}`"
    return _LINK_RE.sub(rep, s)


def _section(text: str, title_pattern: str) -> str:
    """Devolve o corpo da seção `## <title_pattern>` até o próximo `## ` (ou o fim)."""
    m = re.search(r"^##\s+" + title_pattern + r"\s*$", text, re.M | re.I)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^##\s+", text[start:], re.M)
    return text[start:start + nxt.start()] if nxt else text[start:]


_SEAL_RE = re.compile(r"[🟢🟡🔴]")


def _seal(s: str) -> str:
    m = _SEAL_RE.search(s)
    return m.group(0) if m else ""


# ──────────────────────────────────────────────────────────────────────
# Requisitos — RF, RI, RNF, RN, INT
# ──────────────────────────────────────────────────────────────────────

# ADAPTAÇÃO (a): a mesma família de expressão regular do original, agora parametrizada
# por prefixo, para que RI-NN (requisito de interface) seja extraído com o mesmo rigor de
# RF e RNF. A âncora de parada inclui todos os prefixos da taxonomia do ADR 0004.
_STOP_PREFIXES = "RF|RI|RNF|RN|INT|US|L|F"


def _req_pattern(prefix: str) -> re.Pattern[str]:
    return re.compile(
        r"(?:^|\n)[-*\s]*\*{0,2}(" + prefix + r"-?\d+)\*{0,2}\s*[:：]\s*(.+?)"
        r"(?=\n[-*\s]*\*{0,2}(?:" + _STOP_PREFIXES + r")-?\d+\s*[:：]|\n#{2,4}\s|\Z)",
        re.DOTALL,
    )


# Onde cada tipo de requisito mora na spec (formato fixado pelo ADR 0004).
_REQ_SECTIONS = {
    "rf": ("RF", r"Requisitos funcionais"),
    "ri": ("RI", r"Requisitos de interface"),
    "rnf": ("RNF", r"Requisitos n[ãa]o funcionais"),
    "rn": ("RN", r"Regras de neg[óo]cio"),
    "int": ("INT", r"Integra[çc][õo]es"),
}


def _extract_kind(text: str, prefix: str, section_title: str) -> tuple[list[dict], list[dict]]:
    """Extrai os requisitos de um tipo e os sub-cabeçalhos `###` que os agrupam.

    Devolve (requisitos, grupos). Cada requisito é
    {id, d (descrição), s (fontes F-NN), seal, group}.
    """
    section = _section(text, section_title)
    if not section:
        return [], []

    pat = _req_pattern(prefix)
    # Mapa posição → sub-cabeçalho `###` corrente (o gerador prefere o nome do autor).
    heads: list[tuple[int, str]] = [
        (m.start(), _strip_emphasis(m.group(1).strip()))
        for m in re.finditer(r"^###\s+(.+?)$", section, re.M)
    ]

    def group_at(pos: int) -> str:
        name = ""
        for start, title in heads:
            if start < pos:
                name = title
            else:
                break
        return name

    reqs: list[dict] = []
    seen: set[str] = set()
    for m in pat.finditer(section):
        rid = m.group(1)
        if "-" not in rid:  # normaliza RF01 → RF-01
            rid = re.sub(r"^([A-Z]+)(\d+)$", r"\1-\2", rid)
        if rid in seen:
            continue
        seen.add(rid)
        desc = _collapse(m.group(2))
        # O selo do requisito é o que fecha a linha. Selo no meio do texto é conteúdo
        # (ex.: "(linhagem 🟢, planejado 🟡)") e fica onde está — apagá-lo mutilaria a frase.
        trailing = re.search(r"([🟢🟡🔴])\s*$", desc)
        seal = trailing.group(1) if trailing else ""
        if trailing:
            desc = desc[:trailing.start()]
        refs = re.findall(r"F-\d+", desc)
        desc = _strip_emphasis(desc).strip()
        desc = re.sub(r"\s*\[(?:F-\d+(?:,\s*)?)+\]\s*", " ", desc)
        desc = re.sub(r"\s+([,.;:)])", r"\1", desc).strip(" .·—-")
        reqs.append({
            "id": rid,
            "d": _collapse(desc),
            "s": ", ".join(dict.fromkeys(refs)),
            "seal": seal,
            "group": group_at(m.start()),
        })

    groups: list[dict] = []
    for r in reqs:
        g = r["group"] or "Requisitos"
        hit = next((x for x in groups if x["n"] == g), None)
        if hit:
            hit["ids"].append(r["id"])
        else:
            groups.append({"n": g, "ids": [r["id"]]})
    for g in groups:
        ids = g["ids"]
        g["d"] = f"{len(ids)} requisitos ({ids[0]}–{ids[-1]})" if len(ids) > 1 else f"1 requisito ({ids[0]})"
    return reqs, groups


def _extract_requirements(text: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    groups: dict[str, list[dict]] = {}
    for key, (prefix, title) in _REQ_SECTIONS.items():
        reqs, grps = _extract_kind(text, prefix, title)
        out[key] = reqs
        groups[key] = grps
    out["_groups"] = groups  # type: ignore[assignment]
    return out


# ──────────────────────────────────────────────────────────────────────
# Fontes (§ Fontes — F-NN: caminho:linha — trecho — uso SELO)
# ──────────────────────────────────────────────────────────────────────

def _extract_sources(text: str, project: Path) -> list[dict]:
    """Extrai as fontes declaradas na seção `## Fontes` da spec.

    ADAPTAÇÃO: o original procurava caminhos soltos no corpo do texto (e perdia tudo que
    tivesse dígito no nome). Aqui a cadeia backward é a que a spec declara: F-NN com
    `arquivo:linha`, trecho e uso — a mesma que os requisitos citam entre colchetes.
    """
    section = _section(text, r"Fontes")
    if not section:
        return []
    sources: list[dict] = []
    pat = _req_pattern("F")
    for m in pat.finditer(section):
        tag = m.group(1)
        body = _collapse(m.group(2))
        trailing = re.search(r"([🟢🟡🔴])\s*$", body)
        seal = trailing.group(1) if trailing else ""
        body_clean = (body[:trailing.start()] if trailing else body).strip(" —·-")
        # O separador é travessão **cercado de espaço**: um hífen simples pertence ao nome
        # do arquivo (`padrao-aph.md`), e tratá-lo como separador partia a fonte ao meio.
        path_m = re.match(
            r"`?([^\s`]+?)(?::(\d[\d,\u2013\u2014-]*))?`?\s+[\u2014\u2013]\s+(.*)$",
            body_clean)
        if path_m and "/" in path_m.group(1):
            path = path_m.group(1)
            lines = path_m.group(2) or ""
            desc = path_m.group(3)
        else:
            path, lines, desc = "", "", body_clean
        internal = False
        rel = path
        if path:
            candidate = path
            prefix = str(project) + "/"
            if candidate.startswith(prefix):        # fonte deste mesmo repositório
                candidate = candidate[len(prefix):]
            candidate = candidate.lstrip("./")
            if not candidate.startswith("/") and (project / candidate).exists():
                internal, rel = True, candidate
        sources.append({
            "tag": tag,
            "path": path,
            "rel": rel,
            "lines": lines,
            "desc": _collapse(desc)[:400],
            "seal": seal,
            "internal": internal,
        })
    return sources


# ──────────────────────────────────────────────────────────────────────
# Outras seções da spec
# ──────────────────────────────────────────────────────────────────────

def _extract_status(text: str) -> str:
    m = re.search(r"\*\*Status\*\*:\s*\*{0,2}([^*(\n]+)", text)
    if m:
        return _collapse(m.group(1)).strip(" .·—-")
    return ""


def _extract_field(text: str, label: str) -> str:
    m = re.search(r"\*\*" + label + r"\*\*:\s*(.+)", text)
    return _collapse(_strip_emphasis(m.group(1))) if m else ""


def _extract_vision(text: str) -> str:
    section = _section(text, r"O qu[êe] e por qu[êe]")
    if not section:
        return ""
    for para in section.strip().split("\n\n"):
        para = para.strip()
        if para and not para.startswith((">", "|", "-")):
            sentences = re.split(r"(?<=[.!?])\s+", _collapse(para))
            return _strip_emphasis(" ".join(sentences[:3]))
    return ""


def _extract_artifacts(spec_dir: Path, project: Path) -> list[dict]:
    artifacts = []
    for f in sorted(spec_dir.iterdir()):
        if f.is_file() and f.suffix == ".md" and f.name != "spec.md":
            artifacts.append({"name": f.name, "path": str(f.relative_to(project))})
    contracts = spec_dir / "contracts"
    if contracts.is_dir():
        for f in sorted(contracts.iterdir()):
            if f.is_file():
                artifacts.append({"name": f"contracts/{f.name}", "path": str(f.relative_to(project))})
    return artifacts


def _extract_lacunas(text: str) -> list[dict]:
    """Lacunas declaradas (L-NN), **sem truncar**.

    A origem cortava em 300 caracteres. Como a convenção deste repositório escreve o risco
    no FIM da linha (`... — risco **médio**`), o corte apagava justamente o risco: 33 das 58
    lacunas chegavam ao JSON sem ele. Medido antes da correção:

        $ python3 -c "...len(l['d'])>=300..."
        total lacunas 58 truncadas(>=300) 33 sem risco no texto 30

    A lacuna mais longa do corpus tem 542 caracteres — não há razão de tamanho para cortar.
    """
    section = _section(text, r"Lacunas e assun[çc][õo]es")
    out = []
    for m in _req_pattern("L").finditer(section):
        out.append({"id": m.group(1), "d": _collapse(_strip_emphasis(m.group(2)))})
    return out


def _extract_clarify(text: str) -> list[str]:
    """Dúvidas em aberto. Um marcador `[DÚVIDA]` costuma ocupar várias linhas: as linhas
    indentadas seguintes pertencem ao mesmo item."""
    section = _section(text, r"Clarify")
    out: list[str] = []
    for line in section.splitlines():
        s = line.strip()
        if s.startswith("- ") and "[DÚVIDA]" in s:
            out.append(_collapse(_strip_emphasis(s[2:])))
        elif out and s and line.startswith((" ", "\t")) and not s.startswith(("#", "|")):
            out[-1] += " " + _collapse(_strip_emphasis(s))
    return out


# ──────────────────────────────────────────────────────────────────────
# Nomes de feature — vocabulário TOC (ADAPTAÇÃO b)
# ──────────────────────────────────────────────────────────────────────

# O gerador prefere os sub-cabeçalhos `###` que o autor escreveu dentro de
# `## Requisitos funcionais` (é assim que as 12 specs deste repositório estão escritas).
# Estes mapas são a rede de segurança para uma spec futura que não os traga.
DOMAIN_MAP = {
    "ude": "UDEs", "ude.md": "UDEs",
    "ara": "Árvore da Realidade Atual", "arf": "Árvore da Realidade Futura",
    "apr": "Árvore de Pré-Requisitos", "at": "Árvore de Transição",
    "s&t": "Estratégia & Táticas",
    "nuvem": "Nuvem de Conflito", "conflito": "Nuvem de Conflito",
    "injecao": "Injeções", "injeção": "Injeções",
    "premissa": "Premissas", "premissas": "Premissas",
    "obstaculo": "Obstáculos", "obstáculo": "Obstáculos",
    "restricao": "Restrição", "restrição": "Restrição",
    "focalizacao": "Focalização", "focalização": "Focalização",
    "manifesto": "Manifesto", "manifesto.json": "Manifesto",
    "catalogo": "Catálogo toc.*", "catálogo": "Catálogo toc.*",
    "introspect": "Introspecção", "snapshot": "Snapshot de tela",
    "embarque": "Embarque", "iframe": "Embarque",
    "action_proposal": "Proposta de ação", "proposta": "Proposta de ação",
    "canvas": "Canvas", "no": "Nós", "nó": "Nós", "aresta": "Arestas causais",
    "projeto": "Projetos", "tenant": "Inquilino", "otel": "Observabilidade",
    "alembic": "Migrações", "neon": "Persistência", "i18n": "Internacionalização",
    "adr": "ADRs", "jornada": "Jornadas", "jornadas": "Jornadas",
    "rest-api.md": "Contrato REST", "data-model.md": "Modelo de dados",
}

HIGH_SIGNAL_KEYWORDS = {
    "efeito indesejável": "UDEs", "ude": "UDEs",
    "árvore da realidade atual": "Árvore da Realidade Atual",
    "árvore da realidade futura": "Árvore da Realidade Futura",
    "árvore de pré-requisitos": "Árvore de Pré-Requisitos",
    "árvore de transição": "Árvore de Transição",
    "estratégia & táticas": "Estratégia & Táticas",
    "nuvem": "Nuvem de Conflito", "conflito": "Nuvem de Conflito",
    "injeção": "Injeções", "premissa": "Premissas",
    "obstáculo": "Obstáculos", "objetivo intermediário": "Objetivos Intermediários",
    "restrição": "Restrição", "focalização": "Focalização",
    "catálogo": "Catálogo toc.*", "action_proposal": "Proposta de ação",
    "proposta": "Proposta de ação", "manifesto": "Manifesto",
    "introspecção": "Introspecção", "introspect": "Introspecção",
    "snapshot": "Snapshot de tela", "embarque": "Embarque", "iframe": "Embarque",
    "canvas": "Canvas", "aresta": "Arestas causais", "nó": "Nós",
    "lixeira": "Exclusão suave", "desfazer": "Desfazer de sessão",
    "exportação": "Exportação/importação", "importação": "Exportação/importação",
    "traço": "Observabilidade", "otel": "Observabilidade",
    "inquilino": "Isolamento por inquilino", "capacidade": "Capacidades",
}

_STOP_WORDS = {
    "o", "a", "os", "as", "de", "do", "da", "dos", "das", "e", "ou", "um", "uma",
    "no", "na", "nos", "nas", "por", "para", "com", "sem", "que", "não", "se", "em",
    "sistema", "deve", "devem", "quando", "então", "cada", "toda", "todo", "ao", "à",
}


def _group_requirements_into_features(reqs: list[dict], groups: list[dict]) -> list[dict]:
    """Converte os grupos declarados (`###`) em features. Sem grupos, cai no vocabulário."""
    if not reqs:
        return []
    if groups and any(g["n"] != "Requisitos" for g in groups):
        return [{"n": g["n"], "d": g["d"], "ep": 0, "t": 0} for g in groups]

    features: list[dict] = []
    used: set[str] = set()
    chunk_size = 3
    for i in range(0, len(reqs), chunk_size):
        chunk = reqs[i:i + chunk_size]
        text = " ".join(r["d"] for r in chunk).lower()
        found: list[str] = []
        for ref in re.findall(r"`([^`]+)`", " ".join(r["d"] for r in chunk)):
            base = ref.lower().split("/")[-1]
            if base in DOMAIN_MAP and DOMAIN_MAP[base] not in found:
                found.append(DOMAIN_MAP[base])
        for kw, term in HIGH_SIGNAL_KEYWORDS.items():
            if kw in text and term not in found:
                found.append(term)
        found = [f for f in found if f not in used]
        if found:
            name = " e ".join(sorted(found[:2], key=str.lower))
            used.update(found[:2])
        else:
            words = [w for w in re.findall(r"[A-Za-zà-úÀ-Ú]{4,}", text) if w not in _STOP_WORDS]
            name = words[0].capitalize() if words else f"{chunk[0]['id']}–{chunk[-1]['id']}"
        features.append({
            "n": name,
            "d": f"{len(chunk)} requisitos ({chunk[0]['id']}–{chunk[-1]['id']})",
            "ep": 0, "t": 0,
        })
    return features


# ──────────────────────────────────────────────────────────────────────
# Specs
# ──────────────────────────────────────────────────────────────────────

def discover_specs(project: Path) -> list[dict]:
    specs = []
    for spec_md in sorted(project.glob("specs/*/spec.md")):
        spec_dir = spec_md.parent
        spec_id = spec_dir.name
        text = _delink(_read(spec_md), f"specs/{spec_id}")
        num = spec_id.split("-")[0]
        title = _first_line_heading(text) or spec_id
        reqs = _extract_requirements(text)
        groups = reqs.pop("_groups")  # type: ignore[arg-type]
        sources = _extract_sources(text, project)
        artifacts = _extract_artifacts(spec_dir, project)

        # Cadeia forward honesta: só artefatos que existem de fato no repositório, na ordem
        # em que o método os produz (spec → plan → tasks → apoio → qa-report → código).
        order = {"plan.md": 0, "tasks.md": 1, "data-model.md": 2, "qa-report.md": 9}
        chain = [{"label": "spec.md", "href": str(spec_md.relative_to(project)), "state": "ok"}]
        for art in sorted(artifacts, key=lambda a: (order.get(a["name"], 5), a["name"])):
            state = "pending" if art["name"] == "qa-report.md" else "ok"
            chain.append({"label": art["name"], "href": art["path"], "state": state})
        chain.append({"label": f"código do ciclo {num}", "href": "", "state": "todo"})

        specs.append({
            "id": num,
            "specId": spec_id,
            "name": re.sub(r"^Spec\s+\d+\s*[—–-]\s*", "", title).strip(),
            "titulo": title,
            "status": _extract_status(text),
            "raia": _extract_field(text, "Raia"),
            "data": _extract_field(text, "Data"),
            "artifacts": artifacts,
            "rfs": reqs["rf"], "ris": reqs["ri"], "rnfs": reqs["rnf"],
            "rns": reqs["rn"], "ints": reqs["int"],
            "rf": len(reqs["rf"]), "ri": len(reqs["ri"]), "rnf": len(reqs["rnf"]),
            "features": _group_requirements_into_features(reqs["rf"], groups["rf"]),
            "uiFeatures": _group_requirements_into_features(reqs["ri"], groups["ri"]),
            "specDir": spec_id,
            "specNum": num,
            "specPath": str(spec_md.relative_to(project)),
            "vision": _extract_vision(text),
            "lacunas": _extract_lacunas(text),
            "clarify": _extract_clarify(text),
            "sources": sources,
            "chain": chain,
            "modules": [],  # preenchido por `link_modules_and_specs`
            "color": "#5b5bd6",
        })
    return specs


# ──────────────────────────────────────────────────────────────────────
# Módulos M1–M8 (docs/produto/modulos.md)
# ──────────────────────────────────────────────────────────────────────

_MODULE_COLORS = ["#5b5bd6", "#2b6cb0", "#1a7a4c", "#b06b00", "#8b5cf6", "#0f766e", "#c0392b", "#475569"]


def discover_modules(project: Path) -> list[dict]:
    """Lê o mapa M1–M8 de `docs/produto/modulos.md` (tabela + seção por módulo)."""
    text = _delink(_read(project / "docs" / "produto" / "modulos.md"), "docs/produto")
    if not text:
        return []
    modules: list[dict] = []
    for m in re.finditer(r"^\|\s*\*\*(M\d)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", text, re.M):
        modules.append({
            "id": m.group(1),
            "name": _strip_emphasis(m.group(2)),
            "context": _strip_emphasis(m.group(3)),
            "origin": _strip_emphasis(m.group(4)),
            "job": "", "epics": [], "specs": [], "deps": "", "sources": "",
        })
    for mod in modules:
        sec = re.search(
            r"^##\s+" + mod["id"] + r"\s+[—–-]\s+.+?$(.*?)(?=^##\s|\Z)",
            text, re.M | re.S,
        )
        body = sec.group(1) if sec else ""
        job = re.search(r"\*\*O job\*\*:\s*(.+?)(?=\n\n)", body, re.S)
        if job:
            j = _collapse(_strip_emphasis(job.group(1)))
            mod["job"] = (j[0].upper() + j[1:]) if j else j
        for e in re.finditer(r"^\|\s*(E\d\.\d)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", body, re.M):
            mod["epics"].append({
                "id": e.group(1),
                "n": _strip_emphasis(e.group(2)),
                "d": _collapse(_strip_emphasis(e.group(3))),
            })
        dep = re.search(r"^\-\s+\*\*Depende de\*\*:\s*(.+?)(?=\n-\s+\*\*|\n\n|\Z)", body, re.M | re.S)
        if dep:
            mod["deps"] = _collapse(_strip_emphasis(dep.group(1)))
        src = re.search(r"^\-\s+\*\*Fontes\*\*:\s*(.+?)(?=\n-\s+\*\*|\n\n|\Z)", body, re.M | re.S)
        if src:
            mod["sources"] = _collapse(_strip_emphasis(src.group(1)))
        mod["specs"] = sorted(set(re.findall(r"specs/(\d{3}-[a-z0-9-]+)/", body)))
        mod["color"] = _MODULE_COLORS[len(modules) and (int(mod["id"][1:]) - 1) % len(_MODULE_COLORS)]
    return modules


def link_modules_and_specs(modules: list[dict], specs: list[dict]) -> None:
    """Cruza os dois lados: cada módulo soma os requisitos das suas specs; cada spec sabe
    quais módulos entrega."""
    by_dir = {s["specDir"]: s for s in specs}
    for mod in modules:
        rf = ri = rnf = rn = intg = 0
        for sd in mod["specs"]:
            s = by_dir.get(sd)
            if not s:
                continue
            s["modules"].append(mod["id"])
            rf += len(s["rfs"]); ri += len(s["ris"]); rnf += len(s["rnfs"])
            rn += len(s["rns"]); intg += len(s["ints"])
        mod["rf"], mod["ri"], mod["rnf"], mod["rn"], mod["int"] = rf, ri, rnf, rn, intg
        mod["specNames"] = [
            {"dir": sd, "num": sd.split("-")[0], "name": by_dir[sd]["name"]}
            for sd in mod["specs"] if sd in by_dir
        ]
    # Uma spec pode entregar recortes de dois módulos (a 003 entrega E7.1–E7.2 e E8.1–E8.5):
    # nesse caso o total do módulo conta a spec inteira, e o site declara isso em vez de
    # fingir precisão que a contagem não tem.
    for mod in modules:
        mod["shared"] = [
            sd for sd in mod["specs"]
            if sum(1 for other in modules if sd in other["specs"]) > 1
        ]


# ──────────────────────────────────────────────────────────────────────
# ADRs, princípios, skills, scripts, jornadas
# ──────────────────────────────────────────────────────────────────────

def discover_adrs(project: Path) -> list[dict]:
    adrs = []
    for f in sorted(project.glob("docs/adr/*.md")):
        if f.name == "README.md":
            continue
        text = _delink(_read(f), "docs/adr")
        title = _first_line_heading(text)
        m = re.search(r"(\d+)", f.name)
        n = m.group(1) if m else ""
        status = _extract_field(text, "Status") or ""
        clean_title = re.sub(r"^ADR\s*\d+\s*[—–-]\s*", "", title).strip() or title
        decision = ""
        dec = _section(text, r"Decis[ãa]o")
        if dec:
            for para in dec.strip().split("\n\n"):
                para = para.strip()
                if para and not para.startswith(("|", ">")):
                    decision = _collapse(_strip_emphasis(para))[:400]
                    break
        principios = _extract_field(text, "Princípios tocados")
        adrs.append({
            "n": n,
            "title": clean_title,
            "status": status.split("·")[0].strip(),
            "description": decision,
            "principios": principios,
            "path": str(f.relative_to(project)),
        })
    return adrs


def discover_principles(project: Path) -> list[dict]:
    """P1–P7 da constituição do projeto — aplicam-se a todas as specs, por isso são
    extraídos uma vez (o original os copiava dentro de cada spec e inflava a contagem)."""
    text = _delink(_read(project / "docs" / "governance" / "constitution.md"), "docs/governance")
    out = []
    for m in re.finditer(r"^###\s+(P\d)\.\s+(.+?)$", text, re.M):
        title = _strip_emphasis(m.group(2))
        negotiable = "INEGOCIÁVEL" in title.upper()
        title = re.sub(r"\s*\((?:INEGOCIÁVEL|inegociável)\)\s*$", "", title).strip()
        start = m.end()
        nxt = re.search(r"^###\s+", text[start:], re.M)
        body = text[start:start + nxt.start()] if nxt else text[start:]
        first = next((p.strip() for p in body.strip().split("\n\n") if p.strip()), "")
        out.append({
            "id": m.group(1),
            "title": title,
            "hard": negotiable,
            "d": _collapse(_strip_emphasis(first))[:300],
        })
    return out


def discover_skills(project: Path) -> list[dict]:
    skills = []
    for f in sorted(project.glob("skills/*/SKILL.md")):
        text = _read(f)
        name, description = f.parent.name, ""
        if text.startswith("---"):
            fm_end = text.find("---", 3)
            if fm_end > 0:
                fm = text[3:fm_end]
                mn = re.search(r"^name:\s*(.+)$", fm, re.M)
                md = re.search(r"^description:\s*(.+)$", fm, re.M)
                name = mn.group(1).strip() if mn else name
                description = md.group(1).strip() if md else ""
        skills.append({"name": name, "description": description[:220],
                       "path": str(f.relative_to(project))})
    return skills


def discover_scripts(project: Path) -> list[dict]:
    scripts = []
    d = project / "scripts"
    if not d.is_dir():
        return scripts
    type_map = {".py": "Python", ".sh": "Bash", ".mjs": "Node", ".js": "Node"}
    for f in sorted(d.iterdir()):
        if f.is_file() and not f.name.startswith(".") and f.suffix in type_map:
            head = _read(f).splitlines()[:4]
            desc = ""
            for line in head:
                if line.startswith("#") and "—" in line:
                    desc = _collapse(line.lstrip("# ").split("—", 1)[1])
                    break
            scripts.append({"name": f.name, "description": desc[:180],
                            "type": type_map[f.suffix], "path": f"scripts/{f.name}"})
    return scripts


def discover_jornadas(project: Path) -> tuple[list[dict], str]:
    """Jornadas reais (README de convenção não é jornada — P6: jornada sem captura de
    build real é ficção)."""
    journeys = []
    for f in sorted(project.glob("docs/jornadas/*.md")):
        if f.name == "README.md":
            continue
        text = _read(f)
        # Passo da jornada: a convenção deste repositório é `### N · título` sob
        # `## O percurso` (a origem procurava `## Passo N`, que aqui não existe — e o site
        # anunciava "0 passos" para jornadas de treze passos, que é pior que não anunciar).
        steps = len(re.findall(r"^###\s+\d+\s+·", text, re.M))
        if not steps:
            steps = len(re.findall(r"^##\s+Passo\s+\d+", text, re.M))
        journeys.append({"id": f.stem, "name": _first_line_heading(text) or f.stem,
                         "description": "", "steps": steps,
                         "path": str(f.relative_to(project))})
    note = ""
    readme = project / "docs" / "jornadas" / "README.md"
    if readme.exists() and not journeys:
        note = ("Nenhuma jornada ainda, por decisão: jornada sem captura de build real é "
                "ficção (princípio P6). A convenção está em `docs/jornadas/README.md`; as "
                "jornadas nascem no ciclo em que a sua ferramenta passa a existir.")
    return journeys, note


# ──────────────────────────────────────────────────────────────────────
# Código de produção — ADAPTAÇÃO (17)
#
# Por que existe: este gerador nasceu num repositório que era só specs, e por isso
# escrevia `["Linhas de código de produção", "0"]` como CONSTANTE. Quando o serviço e a
# interface nasceram, a constante virou uma afirmação falsa vestida de medição — o pior
# tipo de mentira num site cujo argumento inteiro é honestidade (é o mesmo defeito que
# `scripts/check-evidencia-colada.sh` existe para pegar). Daqui em diante o gerador
# ENXERGA `apps/api` e `apps/web` e CONTA: arquivos, linhas, casos de teste por camada,
# rotas publicadas, migrações, tabelas e portões.
#
# O que ele não faz: rodar a suíte. Contar `def test_` é contar o que está escrito, não o
# que passou — e o site diz isso com todas as letras. Quem prova que passa é o
# `qa-report.md` do ciclo, com a saída colada.
# ──────────────────────────────────────────────────────────────────────

_EXT_CODIGO = {".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
               ".mjs": "JavaScript", ".mts": "TypeScript"}
_DIR_IGNORADO = {"__pycache__", "node_modules", ".venv", "dist", ".pytest_cache",
                 ".mypy_cache", ".ruff_cache", "coverage"}

# Atribuição DECLARADA de caminho a módulo M1–M8. O gerador não adivinha o módulo de um
# arquivo (tentar adivinhar por menção a "M4" no comentário devolve 47 arquivos para um
# módulo de 9 — medido antes de escrever isto): ele conta o que encontra sob cada padrão,
# na ordem, e o primeiro padrão que casa leva o arquivo. O que não casa padrão nenhum
# entra em "não atribuído" e APARECE na linha de contagem — nada some em silêncio.
_MAPA_DE_CODIGO: list[tuple[str, list[str]]] = [
    ("M2", [
        "apps/api/src/toc_api/dominio/ara.py",
        "apps/api/src/toc_api/dominio/criterios_ude.py",
        "apps/api/src/toc_api/dominio/suficiencia.py",
        "apps/api/src/toc_api/dominio/analise.py",
        "apps/api/src/toc_api/dominio/lexico.py",
        "apps/api/src/toc_api/dominio/formulacao.py",
        "apps/api/src/toc_api/aplicacao/ara.py",
        "apps/api/src/toc_api/http/roteadores/ara.py",
        "apps/web/src/componentes/ude/*",
        "apps/web/src/telas/TelaDaAra.tsx",
    ]),
    ("M3", [
        "apps/api/src/toc_api/dominio/nuvem.py",
        "apps/api/src/toc_api/dominio/geracao.py",
        "apps/api/src/toc_api/aplicacao/nuvem.py",
        "apps/api/src/toc_api/http/roteadores/nuvem.py",
        "apps/api/src/toc_api/infra/geracao/*",
        "apps/web/src/componentes/nuvem/*",
        "apps/web/src/telas/TelaDaNuvem.tsx",
    ]),
    ("M4", [
        "apps/api/src/toc_api/dominio/arf.py",
        "apps/api/src/toc_api/dominio/apr.py",
        "apps/api/src/toc_api/dominio/at.py",
        "apps/api/src/toc_api/dominio/encadeamento.py",
        "apps/api/src/toc_api/dominio/verbalizacao.py",
        "apps/api/src/toc_api/dominio/referencia.py",
        "apps/api/src/toc_api/aplicacao/arvores.py",
        "apps/api/src/toc_api/aplicacao/cadeia.py",
        "apps/api/src/toc_api/http/roteadores/arvores.py",
        "apps/api/src/toc_api/http/roteadores/cadeia.py",
        "apps/web/src/componentes/arf/*",
        "apps/web/src/componentes/apr/*",
        "apps/web/src/componentes/at/*",
        "apps/web/src/componentes/cadeia/*",
        "apps/web/src/telas/TelaDaArf.tsx",
        "apps/web/src/telas/TelaDaApr.tsx",
        "apps/web/src/telas/TelaDaAt.tsx",
        "apps/web/src/telas/TelaDaCadeia.tsx",
    ]),
    ("M5", [
        "apps/api/src/toc_api/dominio/snt.py",
        "apps/api/src/toc_api/aplicacao/snt.py",
        "apps/api/src/toc_api/http/roteadores/snt.py",
        "apps/web/src/componentes/snt/*",
        "apps/web/src/telas/TelaDaSnT.tsx",
    ]),
    ("M6", [
        "apps/api/src/toc_api/dominio/focalizacao.py",
        "apps/api/src/toc_api/aplicacao/focalizacao.py",
        "apps/api/src/toc_api/http/roteadores/focalizacao.py",
        "apps/web/src/componentes/focalizacao/*",
        "apps/web/src/telas/TelaDaFocalizacao.tsx",
        "apps/web/src/telas/TelaDeAnalisesDeFocalizacao.tsx",
    ]),
    ("M7", [
        "apps/api/src/toc_api/dominio/federacao/*",
        "apps/api/src/toc_api/aplicacao/federacao/*",
        "apps/api/src/toc_api/aplicacao/politica.py",
        "apps/api/src/toc_api/aplicacao/governanca.py",
        "apps/api/src/toc_api/infra/federacao/*",
        "apps/api/src/toc_api/infra/identidade/*",
        "apps/api/src/toc_api/http/aph.py",
        "apps/api/src/toc_api/http/roteadores/propostas.py",
        "apps/web/src/federacao/*",
        "apps/web/src/componentes/federacao/*",
        "apps/web/src/telas/registro.ts",
        "apps/web/src/App.tsx",
        "apps/web/src/main.tsx",
    ]),
    ("M8", [
        "apps/api/src/toc_api/alembic/*",
        "apps/api/src/toc_api/alembic/versions/*",
        "apps/api/src/toc_api/infra/persistencia/*",
        "apps/api/src/toc_api/infra/observabilidade/*",
        "apps/api/src/toc_api/infra/configuracao.py",
        "apps/api/src/toc_api/infra/relogio.py",
        "apps/api/src/toc_api/http/app.py",
        "apps/api/src/toc_api/http/arranque.py",
        "apps/api/src/toc_api/http/dependencias.py",
        "apps/api/src/toc_api/http/erros.py",
        "apps/api/src/toc_api/http/esquemas.py",
        "apps/web/src/i18n/*",
        "apps/web/src/documentacao/*",
        "apps/web/src/documentacao/verbetes/*",
        "apps/web/src/componentes/documentacao/*",
        "apps/web/src/api/*",
    ]),
    # O M1 vem por último de propósito: ele é o núcleo compartilhado, e ficar no fim
    # impede que `dominio/projeto.py` engula o que pertence a uma ferramenta.
    ("M1", [
        "apps/api/src/toc_api/dominio/projeto.py",
        "apps/api/src/toc_api/dominio/grafo.py",
        "apps/api/src/toc_api/dominio/valores.py",
        "apps/api/src/toc_api/dominio/serializacao.py",
        "apps/api/src/toc_api/dominio/identidade.py",
        "apps/api/src/toc_api/dominio/erros.py",
        "apps/api/src/toc_api/dominio/eventos.py",
        "apps/api/src/toc_api/dominio/portas.py",
        "apps/api/src/toc_api/dominio/exportacao.py",
        "apps/api/src/toc_api/dominio/legado.py",
        "apps/api/src/toc_api/aplicacao/projetos.py",
        "apps/api/src/toc_api/aplicacao/grafo.py",
        "apps/api/src/toc_api/aplicacao/casos_de_uso.py",
        "apps/api/src/toc_api/aplicacao/portabilidade.py",
        "apps/api/src/toc_api/http/roteadores/projetos.py",
        "apps/api/src/toc_api/http/roteadores/portabilidade.py",
        "apps/web/src/componentes/canvas/*",
        "apps/web/src/componentes/PainelDeEntidades.tsx",
        "apps/web/src/componentes/Estados.tsx",
        "apps/web/src/componentes/mensagemDeErro.ts",
        "apps/web/src/estado/*",
        "apps/web/src/dominio/*",
        "apps/web/src/telas/TelaDeProjetos.tsx",
        "apps/web/src/telas/TelaDaLixeira.tsx",
    ]),
]


def _e_teste(rel: str) -> bool:
    """Teste é o que o executor de teste roda: `test_*.py`, `*.test.ts(x)`, `*.test.mjs`,
    ou qualquer arquivo sob `tests/`, `testes/` e `e2e/`."""
    nome = rel.rsplit("/", 1)[-1]
    return (nome.startswith("test_") or ".test." in nome
            or "/tests/" in rel or "/testes/" in rel or "/e2e/" in rel)


def _casos_de_teste(texto: str, sufixo: str) -> int:
    """Casos ESCRITOS (não casos que passaram — quem prova isso é o `qa-report.md`)."""
    if sufixo == ".py":
        return len(re.findall(r"^\s*(?:async\s+)?def\s+test_", texto, re.M))
    # `it(`, `test(` e as formas com modificador (`it.each(...)`, `test.skip`) — uma
    # DECLARAÇÃO cada. `it.each` vira N casos em tempo de execução, e é por isso que este
    # número é rotulado "casos escritos" e nunca "testes que passaram".
    return len(re.findall(r"^\s*(?:it|test)(?:\.\w+(?:\([^\n]*\))?)?\s*\(", texto, re.M))


def _varrer_codigo(raiz: Path, project: Path) -> list[dict]:
    arquivos: list[dict] = []
    if not raiz.is_dir():
        return arquivos
    for f in sorted(raiz.rglob("*")):
        if not f.is_file() or f.suffix not in _EXT_CODIGO:
            continue
        if any(part in _DIR_IGNORADO for part in f.parts):
            continue
        texto = _read(f)
        rel = f.relative_to(project).as_posix()
        arquivos.append({
            "path": rel,
            "ext": f.suffix,
            "lang": _EXT_CODIGO[f.suffix],
            "linhas": len(texto.splitlines()),
            "teste": _e_teste(rel),
            "casos": _casos_de_teste(texto, f.suffix) if _e_teste(rel) else 0,
        })
    return arquivos


def _modulo_do_arquivo(rel: str) -> str:
    for mod, padroes in _MAPA_DE_CODIGO:
        for p in padroes:
            if fnmatch.fnmatchcase(rel, p):
                return mod
    return ""


def _rotas_publicadas(project: Path) -> list[dict]:
    """Rotas declaradas por decorador nos roteadores FastAPI, com o prefixo do próprio
    `APIRouter` — contadas do código, não do OpenAPI (o gerador não sobe o serviço)."""
    rotas: list[dict] = []
    base = project / "apps" / "api" / "src" / "toc_api" / "http"
    if not base.is_dir():
        return rotas
    for f in sorted(base.rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        texto = _read(f)
        prefixos = {m.group(1): m.group(2)
                    for m in re.finditer(r"(\w+)\s*=\s*APIRouter\(\s*prefix=\"([^\"]*)\"", texto)}
        for m in re.finditer(r"(\w+)\s*=\s*APIRouter\(\s*\)", texto):
            prefixos.setdefault(m.group(1), "")
        for m in re.finditer(
                r"@(\w+)\.(get|post|put|patch|delete)\(\s*\"([^\"]*)\"", texto):
            var, verbo, caminho = m.group(1), m.group(2).upper(), m.group(3)
            rotas.append({
                "metodo": verbo,
                "caminho": prefixos.get(var, "") + caminho,
                "arquivo": f.relative_to(project).as_posix(),
            })
    return sorted(rotas, key=lambda r: (r["caminho"], r["metodo"]))


def _migracoes(project: Path) -> list[dict]:
    d = project / "apps" / "api" / "src" / "toc_api" / "alembic" / "versions"
    saida = []
    for f in sorted(d.glob("[0-9]*.py")) if d.is_dir() else []:
        texto = _read(f)
        rev = re.search(r"^revision(?::\s*str)?\s*=\s*\"([^\"]+)\"", texto, re.M)
        down = re.search(r"^down_revision(?::[^=]+)?\s*=\s*(\"[^\"]+\"|None)", texto, re.M)
        saida.append({
            "id": rev.group(1) if rev else f.stem.split("_")[0],
            "nome": f.stem,
            "anterior": (down.group(1).strip('"') if down and down.group(1) != "None" else ""),
            "path": f.relative_to(project).as_posix(),
        })
    return saida


def discover_codebase(project: Path) -> dict:
    api = _varrer_codigo(project / "apps" / "api", project)
    web = _varrer_codigo(project / "apps" / "web", project)
    todos = api + web

    producao = [a for a in todos if not a["teste"]]
    testes = [a for a in todos if a["teste"]]

    def _soma(lista, campo="linhas"):
        return sum(a[campo] for a in lista)

    # Camadas do serviço (P3 — DDD + hexagonal) e pastas da interface.
    camadas_api = []
    for nome, prefixo, papel in [
        ("domínio", "apps/api/src/toc_api/dominio/", "puro: entidades, regras e portas"),
        ("aplicação", "apps/api/src/toc_api/aplicacao/", "puro: casos de uso e política"),
        ("infraestrutura", "apps/api/src/toc_api/infra/", "adaptadores: SQLAlchemy, OTel, identidade"),
        ("HTTP", "apps/api/src/toc_api/http/", "roteadores FastAPI, wire APH, composição"),
        ("migrações", "apps/api/src/toc_api/alembic/", "Alembic — nunca `create_all`"),
    ]:
        sel = [a for a in producao if a["path"].startswith(prefixo)]
        camadas_api.append({"nome": nome, "papel": papel, "prefixo": prefixo,
                            "arquivos": len(sel), "linhas": _soma(sel)})

    camadas_web = []
    for nome, prefixo, papel in [
        ("telas", "apps/web/src/telas/", "uma tela por ferramenta + registro compartilhado"),
        ("componentes", "apps/web/src/componentes/", "canvas, fichas, diagramas, painéis"),
        ("federação", "apps/web/src/federacao/", "canal `ghd.*`, admissão, embarque, tema"),
        ("i18n", "apps/web/src/i18n/", "pt como língua-fonte, en como tradução"),
        ("documentação", "apps/web/src/documentacao/", "verbete por ferramenta, com procedência"),
        ("cliente e estado", "apps/web/src/api/", "cliente do serviço e envelope de erro"),
    ]:
        sel = [a for a in producao if a["path"].startswith(prefixo)]
        camadas_web.append({"nome": nome, "papel": papel, "prefixo": prefixo,
                            "arquivos": len(sel), "linhas": _soma(sel)})

    suites = []
    for nome, prefixo, papel in [
        ("domínio", "apps/api/tests/dominio/", "sem banco e sem rede"),
        ("aplicação", "apps/api/tests/aplicacao/", "com duplos das portas"),
        ("federação", "apps/api/tests/federacao/", "fronteira APH: catálogo, FSM, wire, snapshot"),
        ("contrato", "apps/api/tests/contrato/", "portas, schemas e cadeia de migrações"),
        ("integração", "apps/api/tests/integracao/", "contra o PostgreSQL real"),
        ("interface (vitest)", "apps/web/src/", "React Testing Library, jsdom"),
        ("canal (node:test)", "apps/web/src/federacao/", "envelope `ghd.*` sem framework"),
    ]:
        if nome == "canal (node:test)":
            sel = [a for a in testes if a["path"].startswith(prefixo) and a["ext"] == ".mjs"]
        elif nome == "interface (vitest)":
            sel = [a for a in testes if a["path"].startswith(prefixo) and a["ext"] in (".ts", ".tsx")]
        else:
            sel = [a for a in testes if a["path"].startswith(prefixo)]
        # "arquivos" conta os que TÊM caso: `conftest.py`, `__init__.py` e o módulo de
        # apoio da interface moram sob `tests/` mas não são arquivos de teste, e contá-los
        # inflaria o denominador que a regra R2 pede honesto. Eles entram em "apoio".
        com_caso = [a for a in sel if a["casos"]]
        suites.append({"nome": nome, "papel": papel, "prefixo": prefixo,
                       "arquivos": len(com_caso), "apoio": len(sel) - len(com_caso),
                       "casos": _soma(sel, "casos"), "linhas": _soma(sel)})

    por_modulo: dict[str, dict] = {}
    nao_atribuidos: list[str] = []
    for a in producao:
        mod = _modulo_do_arquivo(a["path"])
        if not mod:
            nao_atribuidos.append(a["path"])
            continue
        alvo = por_modulo.setdefault(mod, {"arquivos": 0, "linhas": 0, "api": 0, "web": 0,
                                           "caminhos": []})
        alvo["arquivos"] += 1
        alvo["linhas"] += a["linhas"]
        alvo["api" if a["path"].startswith("apps/api/") else "web"] += 1
        alvo["caminhos"].append(a["path"])

    rotas = _rotas_publicadas(project)
    migracoes = _migracoes(project)

    tabelas = len(re.findall(
        r"^[a-z_]+ = Table\(",
        _read(project / "apps" / "api" / "src" / "toc_api" / "infra" / "persistencia" / "tabelas.py"),
        re.M))

    portoes = sorted(p.name for p in (project / "scripts").glob("check-*.sh"))
    # Conta como a própria suíte conta (`n_sabotagens=${#SABOTAGENS[@]}/5`): a cabeça de
    # cada tupla de cinco campos dentro do array `SABOTAGENS`. O `grep` de uma linha só do
    # registro de evidência colada devolve 67 porque `[a-z-]+` não casa `check-i18n.sh`;
    # quem manda é a suíte, que declara 76.
    sabotagem = _read(project / "scripts" / "tests" / "run-sabotagem.sh")
    bloco_sab = re.search(r"^SABOTAGENS=\((.*?)^\)$", sabotagem, re.M | re.S)
    sabotagens = len([l for l in (bloco_sab.group(1).splitlines() if bloco_sab else [])
                      if l.strip().startswith('"scripts/check-')])
    bases = len([d for d in (project / "scripts" / "tests" / "sabotagem").glob("*")
                 if d.is_dir()]) if (project / "scripts" / "tests" / "sabotagem").is_dir() else 0

    return {
        "producao": {
            "arquivos": len(producao),
            "linhas": _soma(producao),
            "api_arquivos": len([a for a in producao if a["path"].startswith("apps/api/")]),
            "api_linhas": _soma([a for a in producao if a["path"].startswith("apps/api/")]),
            "web_arquivos": len([a for a in producao if a["path"].startswith("apps/web/")]),
            "web_linhas": _soma([a for a in producao if a["path"].startswith("apps/web/")]),
        },
        "testes": {
            "arquivos": len([a for a in testes if a["casos"]]),
            "apoio": len([a for a in testes if not a["casos"]]),
            "linhas": _soma(testes),
            "casos": _soma(testes, "casos"),
        },
        "camadas_api": camadas_api,
        "camadas_web": camadas_web,
        "suites": suites,
        "modulos": por_modulo,
        "nao_atribuidos": sorted(nao_atribuidos),
        "rotas": rotas,
        "rotas_por_metodo": {v: len([r for r in rotas if r["metodo"] == v])
                             for v in ("GET", "POST", "PUT", "PATCH", "DELETE")},
        "migracoes": migracoes,
        "tabelas": tabelas,
        "portoes": portoes,
        "sabotagens": sabotagens,
        "bases_de_sabotagem": bases,
        "nota": ("Contagens do código como ele está escrito: arquivos, linhas, casos de "
                 "teste declarados, rotas por decorador, migrações e tabelas. O gerador "
                 "NÃO roda a suíte — que os testes passem é afirmação do `qa-report.md` "
                 "do ciclo, com a saída colada."),
    }

# ──────────────────────────────────────────────────────────────────────
# Stack e visão geral
# ──────────────────────────────────────────────────────────────────────

def extract_stack(project: Path) -> dict:
    text = _read(project / "docs" / "governance" / "constitution.md")
    stack = {"interface": "", "serviço": "", "banco": "", "armazenamento": "",
             "telemetria": "", "deploy": "", "federação": ""}
    for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(ADR[^|]*?)\s*\|\s*$", text, re.M):
        key = _strip_emphasis(m.group(1)).lower()
        val = _collapse(_strip_emphasis(m.group(2)))
        if key.startswith("interface"):
            stack["interface"] = val
        elif key.startswith("serviço"):
            stack["serviço"] = val
        elif key.startswith("banco"):
            stack["banco"] = val
        elif key.startswith("armazenamento"):
            stack["armazenamento"] = val
        elif key.startswith("telemetria"):
            stack["telemetria"] = val
        elif key.startswith("deploy"):
            stack["deploy"] = val
        elif key.startswith("federação"):
            stack["federação"] = val
    return stack


def extract_overview(project: Path, specs: list[dict], modules: list[dict],
                     adrs: list[dict], counts: dict) -> dict:
    visao = _delink(_read(project / "docs" / "produto" / "visao.md"), "docs/produto")
    lede = ""
    for para in visao.split("\n\n"):
        p = para.strip()
        if p and not p.startswith((">", "-", "#", "|")):
            lede = _collapse(_strip_emphasis(p))
            break
    cards = [
        {"title": "📦 O que é",
         "content": "Os <b>Processos de Pensamento da Teoria das Restrições (TOC)</b> como "
                    "ferramenta multiusuário — Árvore da Realidade Atual, Nuvem de Conflito, "
                    "Árvore da Realidade Futura, Árvore de Pré-Requisitos, Árvore de Transição, "
                    "Estratégia &amp; Táticas — costurados pela jornada dos cinco passos de "
                    "focalização. Sucessora da linhagem TOC-Builder (quatro gerações de "
                    "protótipo) e segunda aplicação candidata à federação da plataforma."},
        {"title": "📐 Corpus de planejamento",
         "content": f"{counts['specs']} specs · {counts['modules']} módulos (M1–M8) · "
                    f"{counts['adrs']} ADRs · {counts['rf']} RF · {counts['ri']} RI · "
                    f"{counts['rnf']} RNF · {counts['rn']} regras de negócio · "
                    f"{counts['int']} integrações. Números contados pelo gerador, não declarados."},
        {"title": "🤝 Federação",
         "content": "Padrão APH (Aplicação ↔ Harness) Nível 2 (Operador), <code>mode: embedded</code>, "
                    "<code>app_id: toc</code>, identidade por <code>POST /auth/introspect</code>, "
                    "servida de eTLD+1 distinto do hospedeiro (ADR 0003). Assistência de "
                    "inteligência artificial exclusivamente pela fundação, por catálogo de ações "
                    "governadas (ADR 0007)."},
        {"title": "🧱 O que já existe em código",
         "content": f"{counts['linhas_producao']} linhas de produção em "
                    f"{counts['arquivos_producao']} arquivos (<code>apps/api</code> + "
                    f"<code>apps/web</code>), com {counts['casos_de_teste']} casos de teste "
                    f"escritos em {counts['arquivos_de_teste']} arquivos, "
                    f"{counts['rotas']} rotas HTTP publicadas, {counts['migracoes']} migrações "
                    f"Alembic sobre {counts['tabelas']} tabelas e "
                    f"{counts['modulos_com_codigo']} dos {counts['modules']} módulos com código. "
                    "Contado pelo gerador nos arquivos; que a suíte passe é afirmação do "
                    "<code>qa-report.md</code> do ciclo, com a saída colada."},
        {"title": "⚖️ Estado honesto",
         "content": f"Nenhum ciclo foi <b>promovido</b>: o gate humano é indelegável e continua "
                    f"aberto em todos eles. O que existe é construção fechada do lado do agente, "
                    f"com {counts['portoes']} portões executáveis e {counts['sabotagens']} "
                    f"sabotagens que provam que os portões sabem reprovar, e "
                    f"{counts['journeys']} jornadas vivas com captura do build real (P6). "
                    "O selo 🟡 PLANEJADO continua no requisito que ninguém mediu; 🟢 só com "
                    "<code>arquivo:linha</code>."},
    ]
    return {
        "eyebrow": "Visão geral",
        "title": "TOC Federada",
        "lede": lede or "Aplicação dos Processos de Pensamento da Teoria das Restrições.",
        "cards": cards,
        "callout": "<b>Barra:</b> honestidade de estado medida contra o corpus da irmã "
                   "<b>gestaodeprioridades</b> (nenhuma contagem sem a saída colada — regra R1); "
                   "clareza e densidade pela <b>régua Linear</b>.",
    }


# ──────────────────────────────────────────────────────────────────────
# Roadmap (docs/roadmap.md — 12 ciclos) — ADAPTAÇÃO (f)
# ──────────────────────────────────────────────────────────────────────

def extract_roadmap(project: Path, specs: list[dict]) -> dict:
    text = _delink(_read(project / "docs" / "roadmap.md"), "docs")
    cycles: list[dict] = []
    for m in re.finditer(r"^\|\s*\*\*(\d{3})\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", text, re.M):
        desc = _collapse(_strip_emphasis(m.group(3)))
        cycles.append({
            "num": m.group(1),
            "title": _strip_emphasis(m.group(2)),
            "desc": (desc[0].upper() + desc[1:]) if desc else desc,
            "raia": _strip_emphasis(m.group(4)),
            "portoes": [], "entrada": [], "state": "planejado",
        })

    by_num = {c["num"]: c for c in cycles}
    for m in re.finditer(r"^##\s+Ciclo\s+(\d{3})\s*[—–-]\s*(.+?)$", text, re.M):
        num = m.group(1)
        heading = m.group(2)
        start = m.end()
        nxt = re.search(r"^##\s+", text[start:], re.M)
        body = text[start:start + nxt.start()] if nxt else text[start:]
        cut = re.search(r"^###\s+", body, re.M)
        gates_body = body[:cut.start()] if cut else body
        entry_body = body[cut.end():] if cut else ""
        c = by_num.get(num)
        if not c:
            continue
        # O estado sai do que o CABEÇALHO do ciclo declara em `docs/roadmap.md` — nunca de
        # uma lista fixa aqui dentro. Cinco estados, na ordem em que são testados.
        h = heading.lower()
        if "promovido" in h:
            c["state"] = "promovido"
        elif "construção concluída" in h or "fechado do lado do agente" in h:
            c["state"] = "construído"
        elif "execução parcial" in h:
            c["state"] = "parcial"
        elif "em andamento" in h or "em curso" in h:
            c["state"] = "em curso"
        for line in gates_body.splitlines():
            s = line.strip()
            if s.startswith("- "):
                c["portoes"].append(_collapse(_strip_emphasis(s[2:])))
            elif c["portoes"] and s and not s.startswith(("#", "|")) and line.startswith("  "):
                c["portoes"][-1] += " " + _collapse(_strip_emphasis(s))
        for line in entry_body.splitlines():
            s = line.strip()
            if s.startswith("- "):
                c["entrada"].append(_collapse(_strip_emphasis(s[2:])))
            elif c["entrada"] and s and not s.startswith(("#", "|")) and line.startswith("  "):
                c["entrada"][-1] += " " + _collapse(_strip_emphasis(s))

    by_num_spec = {s["specNum"]: s for s in specs}
    for c in cycles:
        s = by_num_spec.get(c["num"])
        if s:
            c["specDir"] = s["specDir"]
            c["specPath"] = s["specPath"]
            c["rf"], c["ri"], c["rnf"] = s["rf"], s["ri"], s["rnf"]
            c["artifacts"] = [{"text": "spec.md", "href": s["specPath"]}] + [
                {"text": a["name"], "href": a["path"]} for a in s["artifacts"]
            ]
            c["modules"] = s["modules"]
        else:
            c["specDir"] = ""; c["specPath"] = ""
            c["rf"] = c["ri"] = c["rnf"] = 0
            c["artifacts"] = []; c["modules"] = []
        c["cls"] = {"infra": "infra", "plena": "", "leve": "demo"}.get(c["raia"], "")

    deps = []
    for c in cycles:
        for e in c["entrada"]:
            deps.append({"from": f"Ciclo {c['num']}", "why": e})

    return {
        "eyebrow": "Roadmap",
        "title": "Sequência de ciclos",
        "lede": ("Doze ciclos propostos ao Product Steward em 2026-09-03 e lidos de "
                 "<code>docs/roadmap.md</code> como estão escritos — inclusive o estado que "
                 "cada cabeçalho declara. O protótipo do ciclo 002 é descartável por decisão, "
                 "não por promessa; apetite de um ciclo por linha — estourou, perde escopo, "
                 "não ganha ciclo. Promoção é gate humano, e nenhuma foi assinada."),
        "callout": ("<b>Barra:</b> roadmap julgado contra o <b>GitLab Product Handbook</b> "
                    "(fonte única, portões explícitos, responsável nomeado) — cada ciclo mostra "
                    "os seus portões reais e o que não pode começar sem; clareza pela "
                    "<b>régua Linear</b>."),
        "cycles": cycles,
        "dependencies": deps,
        "legend": [
            {"cls": "", "label": "Raia plena"},
            {"cls": "infra", "label": "Raia infra (reversibilidade explícita)"},
            {"cls": "fix", "label": "Construção concluída — aguardando o gate humano"},
        ],
        "source": "docs/roadmap.md",
    }


# ──────────────────────────────────────────────────────────────────────
# Rastreabilidade
# ──────────────────────────────────────────────────────────────────────

def build_traceability(specs: list[dict]) -> dict:
    modules = []
    for s in specs:
        modules.append({
            "id": s["specNum"],
            "name": s["name"],
            "specNum": s["specNum"],
            "specPath": s["specPath"],
            "modules": s["modules"],
            "rfs": s["rfs"], "ris": s["ris"], "rnfs": s["rnfs"],
            "rns": s["rns"], "ints": s["ints"],
            "sources": s["sources"],
            "chain": s["chain"],
            "lacunas": s["lacunas"],
        })
    return {
        "modules": modules,
        "callout": ("<b>Barra:</b> rastreabilidade medida contra a matriz do site de produto do "
                    "<b>PROJETO_ECS</b> — cada requisito com identificador, texto, selo, fonte "
                    "<i>backward</i> (F-NN com <code>arquivo:linha</code>) e cadeia "
                    "<i>forward</i> navegável até o artefato que existe hoje."),
    }


# ──────────────────────────────────────────────────────────────────────
# Taxonomia — 15 termos em 3 categorias (ADAPTAÇÃO d)
# ──────────────────────────────────────────────────────────────────────

TAXONOMY_CATEGORIES = [
    {"key": "produto", "label": "Produto", "icon": "📦",
     "hint": "O domínio da TOC — o vocabulário que o usuário fala"},
    {"key": "engenharia", "label": "Engenharia", "icon": "⚙️",
     "hint": "Padrão APH, DDD e hexagonal — a estrutura técnica"},
    {"key": "metodologia", "label": "Metodologia", "icon": "📋",
     "hint": "Maestro — como um humano rege muitos agentes"},
]

TAXONOMY_TERMS = [
    {"term": "Efeito Indesejável (UDE)", "id": "ude", "cat": "produto",
     "def": "Sintoma verificável e presente do sistema, escrito como fato observável — não como "
            "opinião, causa ou falta de solução. É a matéria-prima da Árvore da Realidade Atual.",
     "map": "Módulo <b>M2</b>, spec <code>005-arvore-da-realidade-atual</code>: os critérios formais "
            "de UDE viram <b>regra de domínio pura</b>, testável sem rede — saíram do prompt do "
            "modelo, onde a 4ª geração os deixava (<code>tocbuilderv3/constants.ts:109-137</code>).",
     "analogy": "O sintoma que o paciente relata — ainda não é o diagnóstico."},
    {"term": "Árvore da Realidade Atual (ARA)", "id": "ara", "cat": "produto",
     "def": "Diagrama de causa e efeito que liga os efeitos indesejáveis às poucas causas raiz que "
            "os produzem, checado por suficiência causal.",
     "map": "Módulo <b>M2</b>, ciclo 005. É a ferramenta mais madura da linhagem TOC-Builder e a "
            "primeira reconstruída com desenvolvimento guiado por teste (TDD).",
     "analogy": "O mapa que sobe dos sintomas até a doença."},
    {"term": "Nuvem de Conflito (NC)", "id": "nc", "cat": "produto",
     "def": "Modelo do dilema em cinco entidades — objetivo, duas necessidades e duas ações "
            "conflitantes — ligadas por sete arestas, cada uma carregando uma premissa.",
     "map": "Módulo <b>M3</b>, spec <code>007-nuvem-de-conflito</code>: as cinco entidades e as "
            "sete premissas são invariantes de domínio verificadas por teste, não desenho livre.",
     "analogy": "O nó da corda desenhado antes de tentar desatá-lo."},
    {"term": "Premissa e Injeção", "id": "premissa-injecao", "cat": "produto",
     "def": "Premissa é a crença que sustenta uma aresta do conflito; injeção é a ideia que invalida "
            "uma premissa e evapora o conflito em vez de negociá-lo.",
     "map": "Épicos <b>E3.2</b> (premissas por aresta, injeção ligada à premissa que invalida) e "
            "<b>E4.1</b> — a injeção da nuvem é o que semeia a Árvore da Realidade Futura.",
     "analogy": "O prego escondido no pneu: achar é resolver, não empurrar o carro."},
    {"term": "Obstáculo e Objetivo Intermediário (OI)", "id": "obstaculo-oi", "cat": "produto",
     "def": "Na Árvore de Pré-Requisitos, cada obstáculo entre o hoje e a meta ganha um objetivo "
            "intermediário que o supera; os OIs são então sequenciados por dependência.",
     "map": "Épico <b>E4.2</b>, spec <code>008-arvores-de-futuro-e-implementacao</code> — a metade "
            "da TOC que quatro gerações prometeram e nenhuma entregou.",
     "analogy": "As pedras do rio, colocadas na ordem em que se pisa."},
    {"term": "Restrição e os cinco passos de focalização", "id": "restricao", "cat": "produto",
     "def": "A restrição é o elo que limita o desempenho do sistema inteiro; os cinco passos "
            "(identificar, explorar, subordinar, elevar, recomeçar) são o ciclo que a trata.",
     "map": "Módulo <b>M6</b>, spec <code>009-focalizacao</code>: a jornada guiada que costura as "
            "outras ferramentas. Inteiramente nova — zero ocorrências na linhagem.",
     "analogy": "O gargalo da garrafa: alargar qualquer outro ponto não faz sair mais água."},
    {"term": "Padrão APH (Aplicação ↔ Harness)", "id": "aph", "cat": "engenharia",
     "def": "Norma da fronteira entre uma aplicação e o ambiente que a hospeda. O alvo aqui é o "
            "Nível 2 (Operador), com <code>mode: embedded</code>.",
     "map": "Módulo <b>M7</b>, ADR 0003. A norma vive em <code>GHDaru/protocolos</code> e é leitura; "
            "a aderência se autodeclara no ciclo 012, com evidência por requisito.",
     "analogy": "A tomada de três pinos: quem fabrica o aparelho não redefine o padrão."},
    {"term": "Introspecção e embarque", "id": "introspeccao", "cat": "engenharia",
     "def": "Identidade obtida do hospedeiro por <code>POST /auth/introspect</code> (servidor a "
            "servidor) e embarque da aplicação por iframe com envelope de mensagens <code>ghd.*</code>.",
     "map": "Épicos <b>E7.1</b> e <b>E7.2</b>, spec <code>003-esqueleto-federado</code>. Nada de "
            "login próprio: é o princípio P2 do projeto, inegociável.",
     "analogy": "O crachá conferido na portaria — não impresso pelo visitante."},
    {"term": "Manifesto e catálogo <code>toc.*</code>", "id": "manifesto", "cat": "engenharia",
     "def": "O manifesto declara o que a aplicação é e oferece; o catálogo lista, ação a ação, o que "
            "o modelo de linguagem pode enxergar e propor, com risco e capacidade exigida.",
     "map": "Épico <b>E7.3</b>, spec <code>006-acoes-governadas-e-snapshot</code>, contrato em "
            "<code>specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json</code>.",
     "analogy": "O cardápio do restaurante: quem pede escolhe do cardápio, não da cozinha."},
    {"term": "Proposta de ação (<code>action_proposal</code>) e snapshot", "id": "proposta",
     "cat": "engenharia",
     "def": "Todo verbo que muta estado nasce como proposta, aprovada fora do modelo por uma máquina "
            "de estados no servidor; o snapshot é a tela entregue como <b>dado sanitizado</b>, nunca "
            "como instrução.",
     "map": "Épicos <b>E7.4</b> e <b>E7.5</b>. Sem capacidade de escrita, as ações mutadoras somem do "
            "catálogo — portão executável do ciclo 006, com a contagem antes e depois na saída.",
     "analogy": "O pedido de compra que precisa de assinatura: quem digita não é quem autoriza."},
    {"term": "Módulo, porta e adaptador", "id": "modulo", "cat": "engenharia",
     "def": "Módulo é um <i>bounded context</i> do Design Orientado a Domínio (DDD): vocabulário e "
            "modelo próprios. Porta é a interface do domínio; adaptador é a implementação na borda.",
     "map": "M1–M8 em <code>docs/produto/modulos.md</code>; a regra vira função de aptidão com "
            "<code>import-linter</code>, que falha a integração contínua se o domínio importar "
            "framework (princípio P3).",
     "analogy": "A tomada e o aparelho: o domínio não sabe qual usina gera a energia."},
    {"term": "Spec (a partitura) e RF / RI / RNF", "id": "spec", "cat": "metodologia",
     "def": "A especificação é a fonte de verdade que <b>gera</b> o código. Os requisitos são "
            "funcionais (RF), de interface (RI) e não funcionais (RNF), escritos em forma EARS: "
            "“O SISTEMA DEVE …”, “QUANDO … O SISTEMA DEVE …”.",
     "map": "<code>specs/NNN-slug/spec.md</code>, formato fixado pelo ADR 0004 e conferido por "
            "<code>scripts/check-specs.sh</code>; régua de prontidão (DoR) com corte em 80 pontos.",
     "analogy": "A partitura: a orquestra executa, o maestro não toca cada nota."},
    {"term": "ADR e “Princípios tocados”", "id": "adr", "cat": "metodologia",
     "def": "Architecture Decision Record — decisão datada e imutável, com contexto, alternativas "
            "numeradas e consequências. Todo ADR daqui declara quais princípios toca, com "
            "<code>nenhum</code> escrito por extenso quando for o caso.",
     "map": "<code>docs/adr/</code> mais uma linha em <code>docs/records/decisoes.jsonl</code>. "
            "Sucessão declarada nos dois textos e conferida por "
            "<code>scripts/check-adrs-sucessao.sh</code> (regra R5).",
     "analogy": "A ata da reunião: corrige-se com uma ata nova, nunca apagando a antiga."},
    {"term": "Selo de confiança e lacuna (L-NN)", "id": "selo", "cat": "metodologia",
     "def": "🟢 confirmado com <code>arquivo:linha</code>; 🟡 planejado ou inferido; 🔴 lacuna. "
            "Cada lacuna vira uma linha L-NN com assunção e risco declarados.",
     "map": "Selo por requisito nas 12 specs e na matriz de rastreabilidade deste site. É a regra R1 "
            "em forma visível: afirmação factual só entra depois de executada, com a saída colada.",
     "analogy": "O selo de inspeção no extintor: sem data, não vale."},
    {"term": "Jornada viva e gate humano", "id": "jornada", "cat": "metodologia",
     "def": "Jornada viva é a documentação de um fluxo com capturas geradas do build real por script "
            "versionado e avaliação heurística datada, no mesmo pull request. Gate humano é a "
            "aprovação indelegável do Product Steward.",
     "map": "Princípio P6 e skill <code>living-journey</code>. <code>docs/jornadas/</code> tem hoje "
            "apenas a convenção: sem build, jornada seria ficção.",
     "analogy": "A foto do prédio construído — não a maquete."},
]


def build_taxonomy() -> dict:
    return {
        "categories": TAXONOMY_CATEGORIES,
        "terms": TAXONOMY_TERMS,
        "lede": ("Os quinze termos que estruturam este projeto, definidos e mapeados ao uso real — "
                 "agrupados em domínio (TOC), engenharia (APH, DDD, hexagonal) e metodologia "
                 "(Maestro). A mesma linguagem ubíqua aparece na constituição, nas specs, no código, "
                 "na interface e nos testes."),
        "callout": ("<b>Barra:</b> nomenclatura alinhada ao <b>Atlassian Agile Coach + Product "
                    "Guide</b> (hierarquia épico → feature → story, critérios de aceitação) e à "
                    "linguagem ubíqua do Design Orientado a Domínio; clareza pela <b>régua Linear</b>. "
                    "Regra local: sigla nunca nasce nua (princípio VIII do Maestro)."),
    }


# ──────────────────────────────────────────────────────────────────────
# Workflow — as fases reais do Maestro instalado (ADAPTAÇÃO c)
# ──────────────────────────────────────────────────────────────────────

def build_workflow() -> dict:
    phases = [
        {"n": 1, "title": "Spec", "icon": "📝", "owner": "Spec-agent · humano aprova",
         "goal": "Escrever a especificação que gera o código: o quê, por quê, requisitos em forma "
                 "EARS, fontes com arquivo:linha, lacunas e dúvidas em aberto.",
         "entrada": ["Ciclo aberto com raia declarada (docs/roadmap.md)",
                     "Módulo e épicos mapeados em docs/produto/modulos.md",
                     "Apetite fixado — o tempo do ciclo é constante"],
         "saida": ["specs/NNN-slug/spec.md com as seções do ADR 0004",
                   "RF / RI / RNF / RN / INT numerados e com selo",
                   "## Fontes com F-NN (arquivo:linha) e ## Clarify com no máximo 5 dúvidas"],
         "metric": "scripts/check-specs.sh NNN verde; toda seção obrigatória presente; "
                   "régua de prontidão (DoR) ≥ 80 pontos",
         "fail": {"to": 1, "action": "critério sem verificação executável, ou requisito sem fonte "
                                     "nem selo → reescrever a spec; nada de plano sobre spec vaga"}},
        {"n": 2, "title": "Plan + Constitution Check", "icon": "🗺️",
         "owner": "plan-architect · Architect/Tech Lead humano aprova",
         "goal": "Decidir arquitetura do módulo e confrontar o plano com as duas constituições, "
                 "linha a linha, antes de existir código.",
         "entrada": ["spec.md com o ## Clarify respondido ou o adiamento registrado",
                     "ADRs que a spec consome ratificados"],
         "saida": ["plan.md com DUAS tabelas de Constitution Check (Maestro I–VIII e projeto P1–P7)",
                   "Cinco artefatos condicionais declarados (research, data-model, contracts, "
                   "checklist, ux-design) com justificativa",
                   "Riscos GATE-<nome> ligados às lacunas L-NN da spec"],
         "metric": "scripts/check-specs.sh NNN acusa as duas tabelas, sem linha vazia; "
                   "toda violação de princípio justificada por escrito ou removida",
         "fail": {"to": 1, "action": "princípio inegociável tocado sem alternativa → volta à Fase 1 "
                                     "para reduzir escopo, ou abre ADR novo que declare a decisão"}},
        {"n": 3, "title": "Tasks", "icon": "🗂️", "owner": "plan-architect",
         "goal": "Decompor o plano em tarefas com dependência explícita e aceite que uma máquina "
                 "consegue verificar.",
         "entrada": ["plan.md aprovado no gate humano do plano"],
         "saida": ["tasks.md com T-NN (Dep / Ref / Aceite executável)",
                   "Cauda de fechamento não marcada: TAIL:review, TAIL:security, TAIL:mutation, "
                   "TAIL:gate",
                   "qa-report.md criado vazio, com a estrutura que a execução preenche"],
         "metric": "toda T-NN referencia um RF/RI/RNF e traz comando de aceite; "
                   "a cauda existe e está desmarcada",
         "fail": {"to": 2, "action": "tarefa sem aceite executável ou sem referência → re-decompor "
                                     "o plano; se a ambiguidade for da spec, volta à Fase 1"}},
        {"n": 4, "title": "Implement (TDD)", "icon": "🔨", "owner": "dev-implementer",
         "goal": "Implementar domínio puro primeiro, sempre com o teste que falha antes do código "
                 "de produção (princípio P4).",
         "entrada": ["tasks.md aprovado", "Ciclo anterior promovido (dependência do roadmap)"],
         "saida": ["Teste vermelho no commit anterior ao verde",
                   "Domínio e aplicação sem framework; efeito só por porta",
                   "Traço OpenTelemetry, log correlacionado e métrica nascendo com a funcionalidade"],
         "metric": "import-linter verde na integração contínua (domínio não importa framework); "
                   "suíte de domínio verde e sem rede",
         "fail": {"to": 3, "action": "quebrou o grafo de dependência das tarefas → re-decompor; "
                                     "se o requisito estiver errado, volta à Fase 1 — nunca se "
                                     "corrige requisito dentro do código"}},
        {"n": 5, "title": "DoD", "icon": "✅", "owner": "qa-agent",
         "goal": "Provar, não declarar: cada função de aptidão executada, com a saída colada e o "
                 "tamanho do que foi examinado.",
         "entrada": ["Implementação com a suíte verde localmente"],
         "saida": ["qa-report.md com comando, saída observada e código de saída por verificação",
                   "Cobertura, mutação e portões locais (check-links, check-caminhos, check-specs)",
                   "Jornada viva com captura gerada do build por script versionado (P6)"],
         "metric": "nenhuma caixa marcada sem a saída colada (regra R1); todo portão verde declara "
                   "quanto examinou (regra R2)",
         "fail": {"to": 4, "action": "portão vermelho → corrigir a implementação e reexecutar; "
                                     "transcrever um ✓ sem a saída é defeito, não evidência"}},
        {"n": 6, "title": "Revisão em contexto fresco", "icon": "🔍",
         "owner": "review-agent + security-agent (quem executa não verifica)",
         "goal": "Revisão independente do diff contra o plano, mais passagem de segurança sobre "
                 "admissão, autorização e segredos.",
         "entrada": ["DoD verde com evidência anexada", "Diff fechado e legível"],
         "saida": ["Achados com arquivo:linha e veredito por achado",
                   "TAIL:review e TAIL:security marcadas com a evidência no qa-report.md",
                   "Contradição entre decisões declarada (regra R5) se houver"],
         "metric": "zero achado de correção em aberto; o revisor é agente diferente do autor, "
                   "em contexto novo",
         "fail": {"to": 4, "action": "achado de correção → volta à implementação; achado de lacuna "
                                     "de requisito → volta à Fase 1, com a lacuna virando L-NN"}},
        {"n": 7, "title": "Gate humano", "icon": "🚦", "owner": "Product Steward (indelegável)",
         "goal": "A decisão que nenhum agente toma: aprovar a spec, o plano, o merge e autorizar "
                 "migração ou deploy.",
         "entrada": ["Revisão independente fechada", "Evidência completa no qa-report.md"],
         "saida": ["Decisão registrada por scripts/record-decision.sh em docs/records/decisoes.jsonl",
                   "ADR novo quando a decisão for estrutural, com Princípios tocados declarados",
                   "Ações irreversíveis com backup, ensaio e rollback documentados (raia infra)"],
         "metric": "linha de decisão gravada (o arquivo é somente-acréscimo; um guard hook recusa "
                   "reescrita)",
         "fail": {"to": 6, "action": "reprovado → volta à fase que o achado nomeia; se o motivo for "
                                     "escopo ou valor, volta à Fase 1 — perde escopo, não ganha ciclo"}},
        {"n": 8, "title": "Merge e promoção", "icon": "🚀", "owner": "Product Steward + integração contínua",
         "goal": "Promover o ciclo, deixando rastro entre especificação, pull request, testes e jornada.",
         "entrada": ["Gate humano aprovado", "Integração contínua verde no ramo"],
         "saida": ["scripts/promote-main.sh registra o gate no índice de decisões",
                   "CHANGELOG, docs/roadmap.md e artefatos vivos atualizados no mesmo pull request",
                   "Site de produto regenerado por este gerador (ADR 0008)"],
         "metric": "scripts/check-conformance.sh NNN verde; o site regenerado não diverge do "
                   "commitado (diff vazio)",
         "fail": {"to": 5, "action": "integração contínua vermelha depois do merge → reverter a "
                                     "promoção e voltar ao DoD; a reversão é a ação barata, o "
                                     "conserto no ar não é"}},
    ]
    return {
        "lede": ("O fluxo do método Maestro como este repositório o executa: "
                 "<code>spec → plan (Constitution Check) → tasks → implement → DoD → revisão em "
                 "contexto fresco → gate humano → merge</code>. Cada fase tem um <b>dono</b>, uma "
                 "<b>métrica verificável</b>, critérios de entrada e de saída, e uma <b>aresta de "
                 "falha</b> que diz a qual fase se volta e o que se refaz quando o portão fica "
                 "vermelho."),
        "callout": ("<b>Barra:</b> workflow julgado contra o <b>GitLab Product Handbook</b> "
                    "(fonte única, portões explícitos, responsável nomeado por fase) e contra o "
                    "modelo operacional instalado em <code>docs/governance/operating-model.md</code>, "
                    "que é a norma de onde estas fases saem — não uma invenção deste site."),
        "phases": phases,
    }


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def generate(project_dir: str | Path) -> dict:
    project = Path(project_dir).resolve()

    specs = discover_specs(project)
    modules = discover_modules(project)
    link_modules_and_specs(modules, specs)
    adrs = discover_adrs(project)
    principles = discover_principles(project)
    skills = discover_skills(project)
    scripts = discover_scripts(project)
    journeys, journeys_note = discover_jornadas(project)
    codebase = discover_codebase(project)
    # Cada módulo passa a saber o que existe dele em código (adaptação 17). O mapa é
    # declarado em `_MAPA_DE_CODIGO`; os números são contados nos arquivos.
    for mod in modules:
        mod["code"] = codebase["modulos"].get(mod["id"], {"arquivos": 0, "linhas": 0,
                                                          "api": 0, "web": 0, "caminhos": []})
    # A cadeia forward da spec deixa de dizer "todo" quando o código do módulo existe.
    for s in specs:
        com_codigo = [m for m in s["modules"] if codebase["modulos"].get(m)]
        if com_codigo and s["chain"] and s["chain"][-1]["state"] == "todo":
            s["chain"][-1]["state"] = "ok"
            s["chain"][-1]["label"] = (
                "código: " + ", ".join(
                    f"{m} ({codebase['modulos'][m]['arquivos']} arq.)" for m in com_codigo))
    stack = extract_stack(project)
    roadmap = extract_roadmap(project, specs)
    traceability = build_traceability(specs)
    taxonomy = build_taxonomy()
    workflow = build_workflow()

    counts = {
        "specs": len(specs),
        "modules": len(modules),
        "adrs": len(adrs),
        "rf": sum(len(s["rfs"]) for s in specs),
        "ri": sum(len(s["ris"]) for s in specs),
        "rnf": sum(len(s["rnfs"]) for s in specs),
        "rn": sum(len(s["rns"]) for s in specs),
        "int": sum(len(s["ints"]) for s in specs),
        "sources": sum(len(s["sources"]) for s in specs),
        "lacunas": sum(len(s["lacunas"]) for s in specs),
        "clarify": sum(len(s["clarify"]) for s in specs),
        "skills": len(skills),
        "scripts": len(scripts),
        "journeys": len(journeys),
        "cycles": len(roadmap["cycles"]),
        "principles": len(principles),
        # Contadas por `discover_codebase` (adaptação 17): o site deixou de afirmar
        # "0 linhas" por constante e passou a contar o que existe.
        "linhas_producao": codebase["producao"]["linhas"],
        "arquivos_producao": codebase["producao"]["arquivos"],
        "casos_de_teste": codebase["testes"]["casos"],
        "arquivos_de_teste": codebase["testes"]["arquivos"],
        "rotas": len(codebase["rotas"]),
        "migracoes": len(codebase["migracoes"]),
        "tabelas": codebase["tabelas"],
        "portoes": len(codebase["portoes"]),
        "sabotagens": codebase["sabotagens"],
        "modulos_com_codigo": len(codebase["modulos"]),
    }
    counts["requisitos"] = counts["rf"] + counts["ri"] + counts["rnf"]

    overview = extract_overview(project, specs, modules, adrs, counts)

    metrics = [
        ["Módulos (M1–M8)", str(counts["modules"])],
        ["Specs (ciclos 001–012)", str(counts["specs"])],
        ["ADRs", str(counts["adrs"])],
        ["Princípios do projeto (P1–P7)", str(counts["principles"])],
        ["Requisitos funcionais (RF)", str(counts["rf"])],
        ["Requisitos de interface (RI)", str(counts["ri"])],
        ["Requisitos não funcionais (RNF)", str(counts["rnf"])],
        ["Regras de negócio (RN)", str(counts["rn"])],
        ["Integrações (INT)", str(counts["int"])],
        ["Total RF + RI + RNF", str(counts["requisitos"])],
        ["Fontes declaradas (F-NN)", str(counts["sources"])],
        ["Lacunas declaradas (L-NN)", str(counts["lacunas"])],
        ["Dúvidas em aberto (## Clarify)", str(counts["clarify"])],
        ["Skills instaladas", str(counts["skills"])],
        ["Scripts de aptidão", str(counts["scripts"])],
        ["Jornadas vivas", str(counts["journeys"])],
        ["Módulos com código (M1–M8)", f"{counts['modulos_com_codigo']} de {counts['modules']}"],
        ["Arquivos de produção (apps/api + apps/web)", str(counts["arquivos_producao"])],
        ["Linhas de código de produção", str(counts["linhas_producao"])],
        ["Arquivos de teste", str(counts["arquivos_de_teste"])],
        ["Casos de teste escritos", str(counts["casos_de_teste"])],
        ["Rotas HTTP publicadas", str(counts["rotas"])],
        ["Migrações Alembic", str(counts["migracoes"])],
        ["Tabelas do esquema", str(counts["tabelas"])],
        ["Portões executáveis (scripts/check-*.sh)", str(counts["portoes"])],
        ["Sabotagens declaradas", str(counts["sabotagens"])],
    ]

    return {
        "project": {
            "name": "TOC Federada",
            "mark": "TF",
            "subtitle": (f"{counts['modulos_com_codigo']} de {counts['modules']} módulos com "
                         f"código · {counts['linhas_producao']} linhas"),
            "lang": "pt-BR",
            "theme_key": "tocfed-theme",
            "generated_from": "docs/roadmap.md · docs/produto/modulos.md · specs/ · docs/adr/",
        },
        "overview": overview,
        "taxonomy": taxonomy,
        "workflow": workflow,
        "adrs": adrs,
        "principles": principles,
        "metrics": metrics,
        "counts": counts,
        "modules": modules,
        "specs": specs,
        "skills": skills,
        "scripts": scripts,
        "journeys": journeys,
        "journeys_note": journeys_note,
        "stack": stack,
        "traceability": traceability,
        "roadmap": roadmap,
        "codebase": codebase,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Gera o JSON do site de produto da TOC Federada a partir do repositório.")
    parser.add_argument("project", help="Caminho do diretório do projeto")
    parser.add_argument("--output", "-o", help="Arquivo JSON de saída (padrão: saída padrão)")
    args = parser.parse_args()

    data = generate(args.project)
    output = json.dumps(data, ensure_ascii=False, indent=2)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
        c = data["counts"]
        print(f"JSON escrito em {args.output}", file=sys.stderr)
        print(f"  módulos={c['modules']} specs={c['specs']} adrs={c['adrs']} "
              f"RF={c['rf']} RI={c['ri']} RNF={c['rnf']} RN={c['rn']} INT={c['int']} "
              f"fontes={c['sources']} lacunas={c['lacunas']} ciclos={c['cycles']}", file=sys.stderr)
        # A segunda linha é a adaptação 17: o gerador agora enxerga o código e diz o que
        # contou nele (regra R2 — verde que não declara o denominador não é evidência).
        print(f"  código: arquivos={c['arquivos_producao']} linhas={c['linhas_producao']} "
              f"testes={c['arquivos_de_teste']} casos={c['casos_de_teste']} "
              f"rotas={c['rotas']} migrações={c['migracoes']} tabelas={c['tabelas']} "
              f"portões={c['portoes']} sabotagens={c['sabotagens']} "
              f"módulos com código={c['modulos_com_codigo']}/{c['modules']} "
              f"não atribuídos={len(data['codebase']['nao_atribuidos'])}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
