"""The HTML codebook explorer — one self-contained file, for reading.

A methods reviewer should be able to audit a codebook — every code, its description,
its family, the quotes offered as evidence with their response ids and spans, and the
findings attached to it — without opening a database or a Python prompt. That is what
this page is, and it is all it is: **reading, not editing**. The human gate is a CLI
workflow at refactor level (ADR-0004), so there is nothing here to click that changes
anything.

Three properties the page holds, all of them tested.

**Self-contained.** Hand-written HTML with one inline stylesheet. No template engine,
no JavaScript, no font, image or script fetched from anywhere. The file opens from a
memory stick on a machine with no network, which is what "auditable" has to mean for
an artefact attached to a methods appendix.

**Deterministic.** No timestamp, no generated id, no dictionary iterated in insertion
order. The same codebook renders byte-identical HTML, so the page can be diffed
between snapshots exactly as the codebook JSON can (ADR-0007).

**Escaped without exception.** Survey text is arbitrary respondent input: it contains
``<``, ``&``, quotation marks and — in the real corpus — punctuation that survived an
encoding round trip. Every value that reaches the page goes through :func:`html.escape`
with ``quote=True``, including the values that build anchors and ``id`` attributes.

Vocabulary is grounded theory's throughout (ADR-0005): families, codes, evidence,
clusters, themes.

Validation principle: **transparency**.
"""

from __future__ import annotations

import html
import re
from typing import Any

from gaf.checks.contracts import CHECK_IDS, CheckFinding, CheckReport, Severity
from gaf.models import Code, Codebook
from gaf.report.run_report import CHECK_NOTES, RunArtefact

__all__ = ["findings_by_code", "render_codebook_html"]

#: Finding data keys that name a code. Used to attach a finding to the code it is about.
_NAME_KEYS: tuple[str, ...] = ("name", "code", "candidate", "a_name", "b_name")

_SLUG_RE = re.compile(r"[^a-z0-9]+")

_STYLE = """
:root {
  --ink: #1b1b1b;
  --muted: #5b5b5b;
  --rule: #d8d5cf;
  --paper: #fbfaf7;
  --panel: #ffffff;
  --accent: #29506d;
  --error: #8c1d18;
  --warn: #8a5a00;
  --info: #40566b;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 0 0 4rem;
  background: var(--paper);
  color: var(--ink);
  font: 16px/1.55 "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
}
main { max-width: 62rem; margin: 0 auto; padding: 0 1.5rem; }
header.page {
  border-bottom: 2px solid var(--ink);
  margin-bottom: 1.5rem;
  padding: 2rem 0 1rem;
}
h1 { font-size: 1.7rem; margin: 0 0 .35rem; letter-spacing: -.01em; }
h2 { font-size: 1.25rem; margin: 2.25rem 0 .6rem; border-bottom: 1px solid var(--rule); padding-bottom: .3rem; }
h3 { font-size: 1.05rem; margin: 1.4rem 0 .3rem; }
p { margin: .5rem 0; }
a { color: var(--accent); }
.sub { color: var(--muted); font-size: .9rem; margin: 0; }
.mono, code, .id {
  font-family: "SF Mono", ui-monospace, "DejaVu Sans Mono", Menlo, Consolas, monospace;
  font-size: .85em;
}
.caveat {
  background: #fdf6e3;
  border: 1px solid #e0cfa0;
  border-left: 5px solid #b8860b;
  padding: .8rem 1rem;
  margin: 1rem 0;
}
.caveat h2 { border: 0; margin: 0 0 .4rem; font-size: 1rem; }
table { border-collapse: collapse; width: 100%; margin: .8rem 0; font-size: .92rem; }
th, td { border-bottom: 1px solid var(--rule); padding: .38rem .5rem; text-align: left; vertical-align: top; }
th { border-bottom: 2px solid var(--ink); font-weight: 600; }
td.num, th.num { text-align: right; }
.wrap { overflow-x: auto; }
section.code {
  background: var(--panel);
  border: 1px solid var(--rule);
  border-radius: 3px;
  padding: .9rem 1.1rem;
  margin: 1rem 0;
}
section.code > h3 { margin-top: 0; }
.meta { color: var(--muted); font-size: .82rem; margin: .1rem 0 .6rem; }
blockquote {
  margin: .45rem 0;
  padding: .3rem 0 .3rem .9rem;
  border-left: 3px solid var(--rule);
}
blockquote .prov { display: block; color: var(--muted); font-size: .78rem; margin-top: .2rem; }
.sev { font-weight: 600; font-size: .78rem; letter-spacing: .04em; }
.sev-ERROR { color: var(--error); }
.sev-WARN { color: var(--warn); }
.sev-INFO { color: var(--info); }
ul.findings { list-style: none; margin: .4rem 0 0; padding: 0; }
ul.findings li { border-top: 1px dotted var(--rule); padding: .3rem 0; font-size: .88rem; }
.empty { color: var(--muted); font-style: italic; }
footer { border-top: 1px solid var(--rule); margin-top: 2.5rem; padding-top: .8rem; color: var(--muted); font-size: .85rem; }
@media print { body { background: #fff; } section.code { break-inside: avoid; } }
""".strip()


# --------------------------------------------------------------------------- #
# Escaping and identifiers
# --------------------------------------------------------------------------- #


def _e(value: Any) -> str:
    """Escape anything for HTML text or an attribute value. No exceptions."""
    return html.escape("" if value is None else str(value), quote=True)


def _slug(value: str) -> str:
    """A stable anchor fragment. Pure ASCII, so it never needs escaping twice."""
    slug = _SLUG_RE.sub("-", value.casefold()).strip("-")
    return slug or "unnamed"


# --------------------------------------------------------------------------- #
# Attaching findings to codes
# --------------------------------------------------------------------------- #


def findings_by_code(report: CheckReport, codebook: Codebook) -> dict[str, list[CheckFinding]]:
    """Index findings by the code name each one is about, preserving report order.

    A finding names its subject, and pair-scoped findings name two codes inside
    ``data`` (``a_name`` / ``b_name``). Both routes are followed, so a near-duplicate
    WARN shows up under **both** leaves rather than only the one that happened to sort
    first. A finding that names no code in the codebook is not attached here; the
    caller renders those separately, so nothing is silently dropped.
    """
    known = set(codebook.names())
    index: dict[str, list[CheckFinding]] = {name: [] for name in sorted(known)}
    for finding in report.findings:
        attached: set[str] = set()
        if finding.subject in known:
            attached.add(finding.subject)
        for key in _NAME_KEYS:
            value = finding.data.get(key)
            if isinstance(value, str) and value in known:
                attached.add(value)
        for name in sorted(attached):
            index[name].append(finding)
    return index


def _unattached(report: CheckReport, index: dict[str, list[CheckFinding]]) -> list[CheckFinding]:
    attached = {id(f) for findings in index.values() for f in findings}
    return [f for f in report.findings if id(f) not in attached]


# --------------------------------------------------------------------------- #
# Fragments
# --------------------------------------------------------------------------- #


def _finding_item(finding: CheckFinding) -> str:
    severity = finding.severity.value
    return (
        "<li>"
        f'<span class="sev sev-{_e(severity)}">{_e(severity)}</span> '
        f'<span class="mono">{_e(finding.check_id)}</span> '
        f'<span class="mono">{_e(finding.scope)}:{_e(finding.subject)}</span> — '
        f"{_e(finding.message)}"
        "</li>"
    )


def _evidence_block(code: Code) -> list[str]:
    if not code.evidence:
        return ['<p class="empty">No evidence quote is attached to this code.</p>']
    out = ["<h4 class=\"sub\">Evidence</h4>"]
    ordered = sorted(
        code.evidence,
        key=lambda e: (e.response_id, e.span or (-1, -1), e.quote),
    )
    for evidence in ordered:
        span = (
            f"characters {evidence.span[0]} to {evidence.span[1]}"
            if evidence.span is not None
            else "span not located"
        )
        status = "verified" if evidence.verified else "UNVERIFIED"
        out.append(
            "<blockquote>"
            f"{_e(evidence.quote)}"
            f'<span class="prov">response {_e(evidence.response_id)} · {_e(span)} · '
            f"{_e(status)} · locator score {evidence.score:.3f}</span>"
            "</blockquote>"
        )
    return out


def _code_section(code: Code, findings: list[CheckFinding], n_responses: int) -> list[str]:
    out = [
        f'<section class="code" id="code-{_e(_slug(code.name))}">',
        f"<h3>{_e(code.name)}</h3>",
        f'<p class="meta">id <span class="id">{_e(code.id)}</span>'
        f' · parent <span class="id">{_e(code.parent_id or "none")}</span>'
        f' · created in <span class="id">{_e(code.created_in_snapshot or "unrecorded")}</span>'
        f" · {n_responses} response(s) · {len(code.evidence)} quote(s)</p>",
    ]
    description = code.description.strip()
    out.append(
        f"<p>{_e(description)}</p>"
        if description
        else '<p class="empty">This code carries no description.</p>'
    )
    out.extend(_evidence_block(code))
    if findings:
        out.append('<h4 class="sub">Findings on this code</h4>')
        out.append('<ul class="findings">')
        out.extend(_finding_item(f) for f in findings)
        out.append("</ul>")
    out.append("</section>")
    return out


def _checks_table(report: CheckReport) -> list[str]:
    summary = report.summary()
    totals = report.totals()
    order = [check for check in CHECK_IDS if check in summary]
    order += [check for check in sorted(summary) if check not in CHECK_IDS]
    out = [
        '<div class="wrap"><table>',
        "<thead><tr><th>check</th><th class=\"num\">ERROR</th><th class=\"num\">WARN</th>"
        "<th class=\"num\">INFO</th><th class=\"num\">total</th><th>what it checks</th></tr></thead>",
        "<tbody>",
    ]
    for check in order:
        counts = summary[check]
        out.append(
            f'<tr><td class="mono">{_e(check)}</td>'
            f'<td class="num">{counts.get("ERROR", 0)}</td>'
            f'<td class="num">{counts.get("WARN", 0)}</td>'
            f'<td class="num">{counts.get("INFO", 0)}</td>'
            f'<td class="num">{sum(counts.values())}</td>'
            f"<td>{_e(CHECK_NOTES.get(check, ''))}</td></tr>"
        )
    if not order:
        out.append('<tr><td colspan="6" class="empty">No check emitted a finding.</td></tr>')
    out.append(
        f'<tr><th>TOTAL</th><th class="num">{totals["ERROR"]}</th>'
        f'<th class="num">{totals["WARN"]}</th><th class="num">{totals["INFO"]}</th>'
        f'<th class="num">{len(report)}</th><th></th></tr>'
    )
    out.append("</tbody></table></div>")
    verdict = (
        "No ERROR finding: the codebook is structurally valid."
        if report.passed()
        else f"{totals['ERROR']} ERROR finding(s): the codebook is invalid where they point."
    )
    out.append(f"<p><strong>{_e(verdict)}</strong></p>")
    return out


def _summary_table(artefact: RunArtefact, per_code: dict[str, int]) -> list[str]:
    families = artefact.codebook.families()
    out = [
        '<div class="wrap"><table>',
        '<thead><tr><th>family</th><th class="num">codes</th><th class="num">quotes</th>'
        '<th class="num">responses</th><th>codes in this family</th></tr></thead>',
        "<tbody>",
    ]
    for family, codes in families.items():
        quotes = sum(len(code.evidence) for code in codes)
        responses = sorted({e.response_id for code in codes for e in code.evidence if e.verified})
        links = " · ".join(
            f'<a href="#code-{_e(_slug(code.name))}">{_e(code.name)}</a>'
            f' <span class="sub">({per_code.get(code.name, len(code.response_ids()))})</span>'
            for code in codes
        )
        out.append(
            f'<tr><td><a href="#family-{_e(_slug(family))}">{_e(family)}</a></td>'
            f'<td class="num">{len(codes)}</td><td class="num">{quotes}</td>'
            f'<td class="num">{len(responses)}</td><td>{links}</td></tr>'
        )
    if not families:
        out.append('<tr><td colspan="5" class="empty">The codebook is empty.</td></tr>')
    out.append("</tbody></table></div>")
    return out


# --------------------------------------------------------------------------- #
# The page
# --------------------------------------------------------------------------- #


def render_codebook_html(artefact: RunArtefact, *, title: str | None = None) -> str:
    """The whole explorer as one HTML document. Pure and deterministic."""
    stats = artefact.stats
    codebook = artefact.codebook
    heading = title or f"Codebook explorer — {stats.run_id}"
    index = findings_by_code(artefact.report, codebook)
    unattached = _unattached(artefact.report, index)

    per_code: dict[str, int] = {}
    for assignment in artefact.assignments:
        per_code[assignment.code] = per_code.get(assignment.code, 0) + 1

    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_e(heading)}</title>",
        f"<style>{_STYLE}</style>",
        "</head>",
        "<body>",
        "<main>",
        '<header class="page">',
        f"<h1>{_e(heading)}</h1>",
        f'<p class="sub">{len(codebook)} code(s) in {len(codebook.families())} '
        f"grounded-theory famil{'y' if len(codebook.families()) == 1 else 'ies'} · "
        f"{stats.n_responses} response(s) coded · embedding space "
        f'<span class="mono">{_e(stats.space_id)}</span> · '
        f'snapshot <span class="mono">{_e(stats.snapshot_ids[-1] if stats.snapshot_ids else "none")}</span></p>',
        '<p class="sub">This page is for reading. Codebook edits happen at the human '
        "gate in the slow loop, never here.</p>",
        # The one link out of this page. `views.html` is the shareable half of the
        # pair: it carries no respondent text, where this page carries every quote.
        '<p class="sub">Eleven views of the same dataset — the codebook tree, the '
        "response-by-code heatmap, code growth, the timeline, the reorganisation trail "
        '— are in <a href="views.html">views.html</a>, written beside this page by '
        "<code>gaf report</code>. That page shows code names, counts and response "
        "numbers only, and carries no respondent text.</p>",
        "</header>",
    ]

    if stats.caveats:
        parts.append('<div class="caveat">')
        parts.append("<h2>Caveats — read these before the numbers</h2>")
        for caveat in stats.caveats:
            parts.append(f"<p>{_e(caveat)}</p>")
        parts.append(
            "<p>Treat the M3 and M2 rows of the CHECKS table below as diagnostics of "
            "the stand-in embedder, not as findings about this codebook.</p>"
        )
        parts.append("</div>")

    parts.append('<h2 id="summary">Families</h2>')
    parts.extend(_summary_table(artefact, per_code))

    parts.append('<h2 id="checks">Checks</h2>')
    parts.append(
        "<p>Every check emits through one contract, so this table is the whole of what "
        "the run observed. Counts are findings, not responses.</p>"
    )
    parts.extend(_checks_table(artefact.report))

    parts.append('<h2 id="codes">Codes</h2>')
    if not codebook.codes:
        parts.append('<p class="empty">No candidate was admitted to the codebook.</p>')
    for family, codes in codebook.families().items():
        parts.append(f'<h3 id="family-{_e(_slug(family))}">{_e(family)}</h3>')
        parts.append(
            f'<p class="sub">{len(codes)} code(s) · '
            f'<a href="#summary">back to the family table</a></p>'
        )
        for code in codes:
            parts.extend(
                _code_section(code, index.get(code.name, []), per_code.get(code.name, len(code.response_ids())))
            )

    parts.append('<h2 id="other-findings">Findings not attached to a code</h2>')
    if unattached:
        parts.append(
            "<p>Findings about a segment, a response, a pair or the codebook as a whole. "
            "They belong to the run rather than to any single code.</p>"
        )
        parts.append('<ul class="findings">')
        parts.extend(_finding_item(f) for f in unattached)
        parts.append("</ul>")
    else:
        parts.append('<p class="empty">Every finding names a code in this codebook.</p>')

    errors = [f for f in artefact.report.findings if f.severity is Severity.ERROR]
    parts.append("<footer>")
    parts.append(
        f"<p>Generated by gaf from run <span class=\"mono\">{_e(stats.run_id)}</span>. "
        f"{len(artefact.report)} finding(s), {len(errors)} of them ERROR. "
        "This file is self-contained: no script, no network request, no external asset.</p>"
    )
    parts.append("</footer>")
    parts.extend(["</main>", "</body>", "</html>"])
    return "\n".join(parts) + "\n"
