"""`gaf codebook` — build a codebook from a finished human coding, and describe it.

Two subcommands over one directory.

``gaf codebook organise`` reads the researcher's own code-text pairings, organises them
into the two-level codebook his coding already implies, places each segment onto the
corpus when one is given, attaches his own descriptions when they are given, and writes
the whole thing out: the tree, the listing, the machine-readable codebook every other
command reads, the placement record and a row-oriented golden set. It consults no model
at all. Every part of the researcher's own prompt for building a codebook inductively
from pairings is arithmetic, and arithmetic is what this is.

``gaf codebook define`` fills in the one part that is not: the one-to-three-sentence
description of a code. That is the Definer (`gaf.agents.definer`), the fourth LLM role
and the only one outside both loops. It runs over a coding a person has already
finished; it cannot rename, merge, split or create a code, because none of those is in
what it returns.

**This directory is a run directory.** ``organised.md``, ``organised.json``,
``placement.json`` and ``golden.json`` carry respondent text verbatim, exactly as
``runs/`` does, and the command says so every time it writes them. ``tree.mmd`` carries
names and counts only. ``organised_shareable.md`` withholds the examples — but it
carries the descriptions, and **a description is only as shareable as whoever wrote it
made it**: measured on the real codebook, 5 of the researcher's own 131 imported
definitions share a run of thirty or more characters with a response, one of them
forty-eight characters long. The Definer's output is guarded against exactly that
(`gaf.agents.definer`, guard D4); an imported description is not, because it is the
researcher's own document and is not this build's to rewrite (ADR-0032).

Exit codes follow this package's convention: organising and defining ask *what does this
coding contain and what did the guards find*, and findings are their deliverable, so
they exit 0 whenever the work completes and non-zero only on bad arguments or input the
readers refuse.

Serves **transparency** — the codebook a run is seeded from, the placement behind every
piece of its evidence, and the source of every description are all written down — and
**interpretive depth**: consolidations and near-misses are flagged for the researcher,
never merged away.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from gaf.agents.definer import (
    ChildSummary,
    DefineContext,
    DefinerAgent,
    Definition,
)
from gaf.analysis.matrix import assignments_from_codebook
from gaf.checks.contracts import CheckReport
from gaf.cli._common import (
    EXIT_OK,
    CliError,
    _add_cache,
    _add_mode,
    _add_seed,
    _banner,
    _cached,
    _config_from_args,
    _live_client,
    _out,
    _read_json,
    _write,
    _write_json,
    load_corpus_arg,
)
from gaf.ids import content_hash
from gaf.ingest.definitions import DEFINITION_SOURCE, attach_definitions, read_definitions_md
from gaf.ingest.tagged import (
    OrganisedCodebook,
    TaggedPair,
    organise_tagged,
    read_tagged_pairs,
    to_codebook,
    with_descriptions,
)
from gaf.ingest.xlsx import (
    HighlightMapping,
    HighlightsReport,
    SpreadsheetFormatError,
    place_highlights,
)
from gaf.llm.base import CallLog
from gaf.llm.mock import MockDefinerClient
from gaf.models import Code, Codebook

__all__ = [
    "CODEBOOK_JSON",
    "DEFINER_FINDINGS_JSON",
    "GOLDEN_JSON",
    "ORGANISED_JSON",
    "ORGANISED_MD",
    "PLACEMENT_JSON",
    "SHAREABLE_MD",
    "TREE_MMD",
    "add_codebook_parser",
    "cmd_codebook_define",
    "cmd_codebook_organise",
    "contexts_for",
    "placements_from_json",
    "segments_by_code",
    "stamp_description_sources",
]

ORGANISED_JSON = "organised.json"
ORGANISED_MD = "organised.md"
SHAREABLE_MD = "organised_shareable.md"
TREE_MMD = "tree.mmd"
CODEBOOK_JSON = "codebook.json"
PLACEMENT_JSON = "placement.json"
GOLDEN_JSON = "golden.json"
DEFINER_FINDINGS_JSON = "definer_findings.json"

#: Which of the written files carry a respondent's words. Printed every time, because a
#: directory nobody labelled is a directory somebody emails.
_CARRY_TEXT = (ORGANISED_MD, ORGANISED_JSON, PLACEMENT_JSON, GOLDEN_JSON)
_SAFE = (SHAREABLE_MD, TREE_MMD)

#: Column the printed counts line up on.
_LABEL_WIDTH = 32


# --------------------------------------------------------------------------- #
# Reading a coding back out of an organised directory
# --------------------------------------------------------------------------- #


def segments_by_code(
    pairs: Sequence[TaggedPair], organised: OrganisedCodebook
) -> dict[str, list[str]]:
    """Every segment assigned to each code, in the source file's own row order.

    Keyed by the *canonical* label, so a consolidated spelling and the label it was
    consolidated onto contribute to one code — the same mapping `to_codebook` uses for
    evidence. Blank segments are skipped: `organise_tagged` already counted them as a
    note, and a blank is not text to describe a code from.
    """
    grouped: dict[str, list[str]] = {}
    for pair in pairs:
        if not pair.content.strip():
            continue
        grouped.setdefault(organised.canonical(pair.tag), []).append(pair.content)
    return grouped


def contexts_for(
    organised: OrganisedCodebook,
    pairs: Sequence[TaggedPair],
    *,
    described: Mapping[str, str],
    only: Sequence[str] | None = None,
) -> Iterator[DefineContext]:
    """One `DefineContext` per code, **leaves first**, each group sorted by name.

    Leaves first is not cosmetic: a parent is described from its children's
    descriptions, so the children have to be described before it. `described` is read
    for the child glosses, which is why the caller updates it as it goes.

    **A generator, and that is the point.** Materialising the whole list built every
    parent's `ChildSummary` — each carrying its child's *description* — before the
    caller's loop had described a single leaf, so on a first pass over an undescribed
    codebook (the only pass there normally is) every parent was described from names
    and counts alone, while the docstring and ADR-0034 said otherwise (R1 I2). Yielding
    the parents last, and building each one at the moment it is yielded, makes the
    stated ordering true in effect and not only in sequence. A caller that wraps this
    in `list()` gets the stale behaviour back and should not.

    Built here rather than in `gaf.agents.definer` so that the agents package does not
    import the ingest layer — and through it numpy, scipy and the check layer — for the
    sake of one shape conversion.
    """
    wanted = None if only is None else set(only)
    segments = segments_by_code(pairs, organised)
    top_level = [code.name for code in organised.parents]

    leaves: list[DefineContext] = []
    for code in organised.parents:
        siblings = tuple(name for name in top_level if name != code.name)
        if code.is_leaf:
            leaves.append(
                DefineContext(
                    name=code.name,
                    parent="",
                    siblings=siblings,
                    segments=tuple(segments.get(code.name, ())),
                    count=code.count,
                )
            )
            continue
        child_names = [child.name for child in code.children]
        for child in code.children:
            leaves.append(
                DefineContext(
                    name=child.name,
                    parent=code.name,
                    siblings=tuple(n for n in child_names if n != child.name),
                    segments=tuple(segments.get(child.name, ())),
                    count=child.count,
                )
            )

    for context in sorted(leaves, key=lambda c: c.name):
        if wanted is None or context.name in wanted:
            yield context

    families = sorted(
        (code for code in organised.parents if not code.is_leaf), key=lambda c: c.name
    )
    for code in families:
        if wanted is not None and code.name not in wanted:
            continue
        beneath: list[str] = []
        for child in code.children:
            beneath.extend(segments.get(child.name, ()))
        yield DefineContext(
            name=code.name,
            parent="",
            siblings=tuple(name for name in top_level if name != code.name),
            # A parent is described from its subcodes. The segments travel anyway,
            # unrendered, because the guards must still be able to see a quote.
            segments=tuple(beneath),
            # Read **now**, not when this generator was created: by the time a parent
            # is reached the caller has filled `described` with its children's.
            children=tuple(
                ChildSummary(
                    name=child.name,
                    description=described.get(child.name, child.description),
                    count=child.count,
                )
                for child in code.children
            ),
            count=code.count,
        )


def placements_from_json(payload: Mapping[str, Any]) -> HighlightsReport:
    """Rebuild a `HighlightsReport` from the `placement.json` this command wrote.

    Placement is the expensive step — it locates every segment in every response — and
    a description pass has no business paying for it a second time when the answer is
    already on disk beside it.
    """
    mappings = []
    for row in payload.get("mappings") or []:
        span = row.get("span")
        mappings.append(
            HighlightMapping(
                highlight_id=str(row["highlight_id"]),
                tag=str(row["tag"]),
                content=str(row["content"]),
                response_id=None if row.get("response_id") is None else int(row["response_id"]),
                outcome=str(row["outcome"]),
                score=float(row.get("score", 0.0)),
                candidates=tuple(int(c) for c in row.get("candidates") or ()),
                span=None if not span else (int(span[0]), int(span[1])),
            )
        )
    return HighlightsReport(
        path=str(payload.get("path", "")),
        total=int(payload.get("total", 0)),
        exact=int(payload.get("exact", 0)),
        fuzzy=int(payload.get("fuzzy", 0)),
        ambiguous=int(payload.get("ambiguous", 0)),
        unlocated=int(payload.get("unlocated", 0)),
        per_response={int(k): int(v) for k, v in (payload.get("per_response") or {}).items()},
        mappings=tuple(mappings),
        resolved=int(payload.get("resolved", 0)),
        coded_response_count=int(payload.get("coded_response_count", 0)),
    )


def _descriptions_from_json(payload: Mapping[str, Any]) -> dict[str, str]:
    """Every non-empty description in an `organised.json`, by code name."""
    found: dict[str, str] = {}

    def walk(rows: Sequence[Mapping[str, Any]]) -> None:
        for row in rows:
            description = str(row.get("description") or "").strip()
            if description:
                found[str(row["name"])] = description
            walk(row.get("children") or ())

    walk(payload.get("codes") or ())
    return found


# --------------------------------------------------------------------------- #
# Writing the directory
# --------------------------------------------------------------------------- #


def stamp_description_sources(codebook: Codebook, sources: Mapping[str, str]) -> Codebook:
    """Put the *per-code* description source on every described code.

    `gaf.ingest.tagged.to_codebook` stamps one source on every code, which is right when
    every description came from the same document. Once the Definer has written some of
    them that is no longer true, and a reader has to be able to tell a researcher's own
    definition from a stand-in one code at a time.
    """
    codes: dict[str, Code] = {}
    for code_id, code in codebook.codes.items():
        meta = dict(code.meta)
        source = sources.get(code.name, "")
        if code.description and source:
            meta["description_source"] = source
        else:
            meta.pop("description_source", None)
        codes[code_id] = replace(code, meta=meta)
    return Codebook(codes=codes)


#: What each description source means to somebody holding the document. Keyed by the
#: source strings `gaf.ingest.definitions` and `gaf.agents.definer` write.
_SOURCE_GLOSS: dict[str, str] = {
    DEFINITION_SOURCE: "written by the researcher, imported as given",
    "definer-mock": (
        "an OFFLINE STAND-IN, built by counting the commonest words of the code's own "
        "segments. Not a definition, and not to be read as one"
    ),
    "definer-live": "written by the Definer from the code's own segments",
}


def _provenance_block(sources: Mapping[str, str]) -> str:
    """A header naming where the descriptions in this document came from.

    `OrganisedCodebook.to_markdown` renders a description and not its source, so an
    artefact carrying a machine-written stand-in would otherwise look exactly like one
    carrying the researcher's own definitions. This is what makes the label travel with
    the document rather than only with the JSON beside it.
    """
    counted: dict[str, int] = {}
    for source in sources.values():
        if source:
            counted[source] = counted.get(source, 0) + 1
    if not counted:
        return ""
    lines = ["> **Where these descriptions came from**", ">"]
    for source in sorted(counted):
        gloss = _SOURCE_GLOSS.get(source, "source not recognised by this build")
        lines.append(f"> - `{source}` — {counted[source]} code(s): {gloss}.")
    lines.append(">")
    lines.append("> `organised.json` records the source of each code one by one.")
    return "\n".join(lines) + "\n\n"


def _write_organised(
    out: Path,
    organised: OrganisedCodebook,
    *,
    placements: HighlightsReport | None,
    described: Mapping[str, str],
    sources: Mapping[str, str],
) -> list[str]:
    """Write every derived artefact from one organised codebook. Returns their names."""
    book = with_descriptions(
        organised, described, {"description_sources": dict(sorted(sources.items()))}
    )
    codebook = stamp_description_sources(
        to_codebook(book, placements=placements, descriptions=described), sources
    )
    header = _provenance_block(sources)
    written = [ORGANISED_JSON, ORGANISED_MD, SHAREABLE_MD, TREE_MMD, CODEBOOK_JSON]
    _write_json(out / ORGANISED_JSON, book.to_json(include_examples=True))
    _write(out / ORGANISED_MD, header + book.to_markdown(include_examples=True))
    _write(out / SHAREABLE_MD, header + book.to_markdown(include_examples=False))
    _write(out / TREE_MMD, book.to_mermaid())
    _write(out / CODEBOOK_JSON, codebook.to_json_str())
    if placements is not None:
        _write_json(out / PLACEMENT_JSON, placements.to_json())
        _write_json(
            out / GOLDEN_JSON, [row.to_json() for row in assignments_from_codebook(codebook)]
        )
        written += [PLACEMENT_JSON, GOLDEN_JSON]
    return written


def _count(label: str, value: Any, *, indent: int = 2) -> None:
    """One ``label   value`` line. Padded to a fixed column so the counts line up.

    A label longer than the column still gets a separating space rather than running
    into its own number, which is the failure mode of a bare f-string.
    """
    text = f"{' ' * indent}{label}"
    _out(f"{text.ljust(_LABEL_WIDTH)} {value}")


def _report_files(out: Path, written: Sequence[str]) -> None:
    _out("")
    _out(f"Artefacts written to {out}:")
    for name in written:
        mark = "  [holds respondent text]" if name in _CARRY_TEXT else ""
        _out(f"  {out / name}{mark}")
    safe = [name for name in written if name in _SAFE]
    if safe:
        _out("")
        _out(
            f"  Everything here except {', '.join(safe)} holds the responses verbatim: "
            "treat this directory like runs/ and keep it out of git (see `make scrub`)."
        )
        _out(
            f"  {TREE_MMD} carries names and counts only. {SHAREABLE_MD} withholds the "
            "examples, but it still carries the descriptions, and a description is only "
            "as shareable as whoever wrote it made it: check it before it leaves this "
            "machine."
        )


# --------------------------------------------------------------------------- #
# organise
# --------------------------------------------------------------------------- #


def cmd_codebook_organise(args: argparse.Namespace) -> int:
    """Organise a finished human coding into a codebook, and count everything."""
    tagged = Path(args.tagged)
    if not tagged.exists():
        raise CliError(f"{tagged} does not exist")
    out = Path(args.out)
    config = _config_from_args(args, run_id="codebook", output_dir=out)

    try:
        pairs = read_tagged_pairs(tagged, sheet=args.sheet)
    except (SpreadsheetFormatError, ValueError, OSError) as exc:
        raise CliError(f"cannot read the pairings {tagged}: {exc}") from exc
    if not pairs:
        raise CliError(f"{tagged} holds no code-text pairings")

    organised = organise_tagged(pairs, rules=config.rules)
    _banner("gaf codebook organise", str(tagged))
    _out("")
    _count("pairs read", organised.pair_count)
    _count("segments counted", organised.segment_count)
    _count("families (top level)", len(organised.parents))
    _count("leaves", len(organised.leaves()))
    _count("consolidations", len(organised.consolidations))
    for consolidation in organised.consolidations:
        _out(
            f"    {consolidation.from_label} -> {consolidation.to} "
            f"({consolidation.rule}, {len(consolidation.rows)} row(s))"
        )
    notes = organised.notes_by_category()
    _count("notes", len(organised.notes))
    for category, rows in notes.items():
        _count(category, len(rows), indent=4)

    placements = _place(pairs, args, config=config, tagged=tagged)
    described, sources = _definitions(organised, args)

    out.mkdir(parents=True, exist_ok=True)
    organised = with_descriptions(
        organised,
        {},
        {
            "tagged_path": str(tagged),
            "tagged_content_hash": content_hash(tagged.read_bytes()),
            "corpus_path": str(Path(args.corpus)) if args.corpus else None,
            "definitions_path": str(Path(args.definitions)) if args.definitions else None,
        },
    )
    written = _write_organised(
        out, organised, placements=placements, described=described, sources=sources
    )
    _report_files(out, written)
    _out("")
    _out(f"Next: gaf codebook define --organised {out}")
    return EXIT_OK


def _place(
    pairs: Sequence[TaggedPair], args: argparse.Namespace, *, config: Any, tagged: Path
) -> HighlightsReport | None:
    """Place every segment onto the corpus, or say why placement did not happen."""
    if not args.corpus:
        _out("")
        _out(
            "  placement                   not attempted: no --corpus, so no segment "
            "has a response id and no golden set can be written"
        )
        return None
    corpus = load_corpus_arg(Path(args.corpus), config=config)
    assert corpus is not None
    _, report = place_highlights(
        pairs,
        corpus,
        fuzzy_threshold=config.rules.fuzzy_threshold,
        path=str(tagged),
    )
    _out("")
    _count("placement", f"{report.total} segment(s) on {len(corpus)} response(s)")
    _count("exact", report.exact, indent=4)
    _count("fuzzy", report.fuzzy, indent=4)
    _count("resolved", report.resolved, indent=4)
    _count("ambiguous (excluded)", report.ambiguous, indent=4)
    _count("unlocated (excluded)", report.unlocated, indent=4)
    _count("mapped", report.mapped, indent=4)
    _count("responses in the coded set", report.coded_response_count, indent=4)
    return report


def _definitions(
    organised: OrganisedCodebook, args: argparse.Namespace
) -> tuple[dict[str, str], dict[str, str]]:
    """Read and attach the researcher's own descriptions, and report both directions."""
    if not args.definitions:
        _out("")
        _out("  definitions                 none supplied; every code is undescribed")
        _out("                              (`gaf codebook define` writes them)")
        return {}, {}
    path = Path(args.definitions)
    if not path.exists():
        raise CliError(f"{path} does not exist")
    try:
        report = read_definitions_md(path)
    except (ValueError, OSError) as exc:
        raise CliError(str(exc)) from exc
    described_book, match = attach_definitions(organised, report)
    described = {
        name: code.description
        for name in described_book.names()
        if (code := described_book.parent(name) or described_book.leaf(name)) and code.description
    }
    _out("")
    _count("definitions read", len(report))
    _count("matched", match.matched, indent=4)
    _count("defined but never tagged", len(match.defined_not_tagged), indent=4)
    _count("tagged but never defined", len(match.tagged_not_defined), indent=4)
    _count("matched after consolidation", len(match.matched_after_consolidation), indent=4)
    for name in match.defined_not_tagged:
        _out(f"      defined, not tagged:    {name}")
    for name in match.tagged_not_defined:
        _out(f"      tagged, not defined:    {name}")
    return described, dict.fromkeys(described, DEFINITION_SOURCE)


# --------------------------------------------------------------------------- #
# define
# --------------------------------------------------------------------------- #


def _definer_for(config: Any, call_log: CallLog) -> DefinerAgent:
    """The Definer, offline or live. It reuses the `refactorer` model slot (ADR-0034)."""
    spec = config.models.refactorer
    client = MockDefinerClient(spec) if config.offline else _live_client(spec, config)
    return DefinerAgent(_cached(client, config), config=config, call_log=call_log)


def cmd_codebook_define(args: argparse.Namespace) -> int:
    """Write the description of every code that lacks one. Changes nothing else."""
    out = Path(args.organised)
    document = out / ORGANISED_JSON
    if not document.exists():
        raise CliError(
            f"{document} does not exist. Point --organised at a directory written by "
            "`gaf codebook organise`."
        )
    payload = _read_json(document)
    meta = dict(payload.get("meta") or {})
    tagged = Path(str(meta.get("tagged_path", "")))
    if not tagged.exists():
        raise CliError(
            f"{document} was organised from {tagged}, which is no longer there. The "
            "Definer needs every segment of a code, and only the pairings hold them."
        )
    if content_hash(tagged.read_bytes()) != meta.get("tagged_content_hash"):
        raise CliError(
            f"{tagged} has changed since `gaf codebook organise` read it. Re-run "
            "organise: describing one coding against another coding's segments would "
            "produce definitions that no longer match the text under them."
        )

    config = _config_from_args(args, run_id="definer", output_dir=out)
    pairs = read_tagged_pairs(tagged)
    organised = organise_tagged(pairs, rules=config.rules)
    described = _descriptions_from_json(payload)
    sources: dict[str, str] = dict(meta.get("description_sources") or {})
    for name in described:
        sources.setdefault(name, str(meta.get("description_source") or DEFINITION_SOURCE))

    imported = {name for name, source in sources.items() if source == DEFINITION_SOURCE}
    every = set(organised.names())
    # Redefining what the Definer already wrote is what a second pass is for;
    # `--only-missing` says not to. The researcher's own definitions are never
    # overwritten under either setting.
    targets = (every - set(described)) if args.only_missing else (every - imported)

    _banner("gaf codebook define", str(out))
    _out("")
    _count("codes", len(every))
    _count("already defined by hand", f"{len(imported)}  (never overwritten)")
    _count("to describe", len(targets))

    log = CallLog()
    definer = _definer_for(config, log)
    definitions: list[Definition] = []
    report = CheckReport()
    for context in contexts_for(organised, pairs, described=described, only=sorted(targets)):
        definition = definer.define(context)
        definitions.append(definition)
        report.findings.extend(definition.findings)
        if definition.accepted and definition.description:
            described[context.name] = definition.description
            sources[context.name] = definition.source

    accepted = [d for d in definitions if d.accepted and d.description]
    refused = [d for d in definitions if not d.accepted]
    _count("accepted", len(accepted), indent=4)
    _count("refused", len(refused), indent=4)
    for severity, count in sorted(report.totals().items()):
        _count(f"findings {severity}", count, indent=4)
    for finding in report.findings:
        _out(f"      [{finding.severity}] {finding.check_id} {finding.subject}: {finding.message}")

    organised = with_descriptions(organised, {}, meta)
    placement = out / PLACEMENT_JSON
    placements = placements_from_json(_read_json(placement)) if placement.exists() else None
    written = _write_organised(
        out, organised, placements=placements, described=described, sources=sources
    )
    _write_json(
        out / DEFINER_FINDINGS_JSON,
        {
            "organised": str(out),
            "prompt_version": definer.prompt_version,
            "source": definer.source,
            "offline": config.offline,
            "only_missing": bool(args.only_missing),
            "counts": {
                "codes": len(every),
                "considered": len(definitions),
                "accepted": len(accepted),
                "refused": len(refused),
                "held_because_defined_by_hand": len(imported),
            },
            "summary": report.summary(),
            "severities": report.totals(),
            "llm": log.summary(),
            "definitions": [definition.to_json() for definition in definitions],
            "findings": report.to_json(),
        },
    )
    _report_files(out, [*written, DEFINER_FINDINGS_JSON])
    if definer.source == "definer-mock":
        _out("")
        _out(
            "  Every description written here is an offline stand-in, labelled "
            "description_source: definer-mock. It is a placeholder built by counting "
            "words, not a definition, and it carries respondent words: this directory "
            "stays out of git."
        )
    return EXIT_OK


# --------------------------------------------------------------------------- #
# The parser
# --------------------------------------------------------------------------- #


def add_codebook_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    codebook = sub.add_parser(
        "codebook",
        help="organise a finished human coding into a codebook, and describe it",
        description=(
            "Build the codebook a human coding already implies, and fill in the one "
            "part of it that is not arithmetic: the description of each code."
        ),
    )
    kind = codebook.add_subparsers(dest="codebook_kind", required=True, metavar="KIND")

    organise = kind.add_parser(
        "organise",
        help="code-text pairings -> the two-level codebook, placed on a corpus",
        description=(
            "Read the pairings, organise them into families and leaves, place every "
            "segment onto the corpus when one is given, attach the researcher's own "
            "descriptions when they are given, and write the codebook, the tree, the "
            "placement record and a row-oriented golden set. No model is consulted."
        ),
    )
    organise.add_argument("--tagged", required=True, help="code-text pairings (csv or xlsx)")
    organise.add_argument("--corpus", help="corpus JSON or xlsx — places every segment on a response")
    organise.add_argument("--definitions", help="the researcher's codebook Markdown")
    organise.add_argument("--sheet", help="worksheet name, when the pairings are a workbook")
    organise.add_argument("--out", required=True, help="output directory")
    _add_seed(organise)
    organise.set_defaults(handler=cmd_codebook_organise, offline=True)

    define = kind.add_parser(
        "define",
        help="the Definer writes the description of every code that lacks one",
        description=(
            "Run the Definer over an organised directory. It writes one description of "
            "one to three sentences per code, grounded in that code's own segments, and "
            "nothing else: it cannot rename, merge, split or create a code. A "
            "description the researcher wrote himself is never overwritten."
        ),
    )
    define.add_argument(
        "--organised", required=True, help="a directory written by `gaf codebook organise`"
    )
    define.add_argument(
        "--only-missing",
        action="store_true",
        help="describe only codes with no description at all, leaving earlier Definer output alone",
    )
    _add_cache(define)
    _add_seed(define)
    _add_mode(define)
    define.set_defaults(handler=cmd_codebook_define)
