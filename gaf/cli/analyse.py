"""`gaf analyse` — the deterministic analysis tail: matrix, Ward's HCA, saturation.

Binary occurrence matrix, the low-frequency filter, Ward's hierarchical cluster
analysis and the theoretical-saturation curve. No model is consulted anywhere in this
command, and respondent metadata is joined here and nowhere else — never during
coding, so that a demographic column can never bias which code a response receives.

Beside those, three further readings of the same matrix, each written as JSON and as
Markdown: **patterns** (which responses look alike, and which codes travel together),
**affinity** (leaf codes that belong together regardless of the family they were filed
under), and **code growth** (new codes per batch, with the spike rule's verdict). A
fourth, the **crosswalk**, runs only when ``--crosswalk-target`` names a second
codebook to map this one onto.

A degenerate matrix is **refused, not repaired**: `DegenerateMatrixError` still writes
the occurrence matrix and the saturation curve already computed, and says plainly why
clustering did not run, rather than returning a partition nobody asked for. The three
further readings are written *before* clustering is attempted, for the same reason:
none of them needs a partition, so none of them should be lost when one cannot be cut.

Serves **reliability**: the same assignments and the same `AnalysisConfig` produce the
same matrix, the same agglomeration schedule and the same cluster means, every time.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from gaf.analysis.affinity import build_affinity
from gaf.analysis.crosswalk import build_crosswalk
from gaf.analysis.hca import (
    DegenerateMatrixError,
    cluster_responses,
    dendrogram_svg,
    saturation_curve,
    saturation_svg,
)
from gaf.analysis.matrix import OccurrenceMatrix, build_matrix
from gaf.analysis.patterns import build_patterns
from gaf.checks.growth import code_growth, detect_spikes
from gaf.cli._common import (
    EXIT_OK,
    Artefact,
    CliError,
    _add_seed,
    _banner,
    _config_from_args,
    _embedder_for,
    _out,
    _read_json,
    _write,
    _write_json,
    load_artefact,
    load_codebook_arg,
    load_corpus_arg,
)
from gaf.config import AnalysisConfig, CheckpointPolicy, RunConfig
from gaf.ids import code_id
from gaf.models import Code, Codebook
from gaf.report.run_report import RunArtefact
from gaf.report.views import growth_markdown


def cmd_analyse(args: argparse.Namespace) -> int:
    """The deterministic analysis tail: matrix, Ward's HCA, saturation."""
    path = Path(args.assignments)
    artefact = load_artefact(path)
    config = _config_from_args(args, run_id="analyse", output_dir=Path(args.out))
    corpus = load_corpus_arg(Path(args.data) if args.data else None, config=config)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    analysis = config.analysis
    if args.min_frequency is not None:
        analysis = AnalysisConfig(
            **{**analysis.to_json(), "min_code_frequency": int(args.min_frequency)}
        )
    if args.n_clusters is not None:
        analysis = AnalysisConfig(**{**analysis.to_json(), "n_clusters": int(args.n_clusters)})

    coding = _coding_from_run(_path(args.run))

    _banner("gaf analyse", str(path))
    _out(f"  {artefact.describe()}")
    _out(f"  {coding.describe()}")

    try:
        matrix = build_matrix(artefact.assignments, config=analysis, responses=corpus)
    except ValueError as exc:
        raise CliError(f"cannot build the occurrence matrix: {exc}") from exc
    unfiltered = build_matrix(
        artefact.assignments,
        config=AnalysisConfig(
            **{
                **analysis.to_json(),
                "min_code_frequency": 1,
                "min_code_frequency_fraction": None,
            }
        ),
        responses=corpus,
    )

    _out("")
    _out(f"  {matrix.n_responses} response(s) x {matrix.n_codes} code(s) after filtering.")
    _out(f"  {matrix.filter.summary()}")
    matrix.write_csv(out / "occurrence_matrix.csv")
    _write(out / "occurrence_matrix.json", matrix.to_json_str())

    curve = saturation_curve(unfiltered, config=analysis)
    _write_json(out / "saturation.json", curve.to_json())
    _write(out / "saturation.md", curve.to_markdown())
    _write(out / "saturation.svg", saturation_svg(curve))
    _out("")
    _out(curve.to_markdown())

    extra = _write_readings(args, out, artefact, matrix, unfiltered, config, analysis, coding)

    try:
        clusters = cluster_responses(matrix, config=analysis)
    except DegenerateMatrixError as exc:
        _out("")
        _out(f"! Ward's HCA was refused: {exc}")
        _out(
            "  The matrix is too small or too degenerate to cluster. The occurrence "
            "matrix and the saturation curve above are still written."
        )
        _out("")
        _out(f"Artefacts written to {out}:")
        for name in ("occurrence_matrix.csv", "occurrence_matrix.json", *_SATURATION, *extra):
            _out(f"  {out / name}")
        return EXIT_OK

    _write(out / "clusters.json", clusters.to_json_str())
    _write(out / "clusters.md", clusters.to_markdown())
    _write(out / "dendrogram.svg", dendrogram_svg(clusters))
    _out("")
    _out(clusters.to_markdown())
    if clusters.warnings:
        _out("")
        for warning in clusters.warnings:
            _out(f"! {warning}")
        _out(
            "  ADR-0020: the cluster-count rule is applied literally and its degenerate "
            "results are reported, never silently repaired. Set --n-clusters to state "
            "the count explicitly; it is then recorded as an override."
        )

    _out("")
    _out(f"Artefacts written to {out}:")
    for name in (
        "occurrence_matrix.csv",
        "occurrence_matrix.json",
        "clusters.json",
        "clusters.md",
        "dendrogram.svg",
        *_SATURATION,
        *extra,
    ):
        _out(f"  {out / name}")
    return EXIT_OK


# --------------------------------------------------------------------------- #
# The three further readings, and the optional crosswalk
# --------------------------------------------------------------------------- #

#: Named once, because both exit paths list it.
_SATURATION: tuple[str, ...] = ("saturation.json", "saturation.md", "saturation.svg")

@dataclass(frozen=True, slots=True)
class _Coding:
    """What this analysis knows about *how* the coding was produced.

    A row-oriented assignments file knows the codes and nothing about the process that
    made them: a response coded to nothing leaves no row, so it is invisible, and the
    batch size a run used is not written anywhere in the rows. `gaf analyse --run
    <run.json>` supplies both. When it is absent this is empty and `growth_note` says
    so, because a growth curve cut on a different universe from the run's own is a
    different curve and must not be read as the run's (R1 C2).
    """

    order: tuple[int, ...] = ()
    batch_size: int | None = None
    policy: CheckpointPolicy | None = None
    run_id: str = ""

    def describe(self) -> str:
        if not self.order:
            return (
                "no --run: the growth curve is cut on the rows themselves, at the "
                "analysis batch size"
            )
        return (
            f"run `{self.run_id}`: {len(self.order)} response(s) coded, batch size "
            f"{self.batch_size}"
        )

    def growth_note(self) -> str:
        if not self.order:
            return (
                "> **This curve did not read the run.** It is cut on the responses that "
                "produced an assignment row, in the order those rows name them, at the "
                "analysis batch size. A response the run coded to nothing "
                "— a duplicate, or one whose every candidate was dropped — leaves no "
                "row, so it is absent from this universe and every batch after it is cut "
                "one response early. Pass `--run <run.json>` for the run's own curve: the "
                "one its decision trace, its handover verdicts and its timeline are keyed "
                "to."
            )
        return (
            f"> Cut the way run `{self.run_id}` cut it: {len(self.order)} response(s) in "
            f"the order the run processed them, at its own batch size of "
            f"{self.batch_size}. This is the curve the run's decision trace, handover "
            "verdicts and timeline are keyed to."
        )


def _coding_from_run(path: Path | None) -> _Coding:
    """Read the processing order, the batch size and the policy out of a `run.json`."""
    if path is None:
        return _Coding()
    if not path.exists():
        raise CliError(f"{path} does not exist")
    try:
        artefact = RunArtefact.from_json(_read_json(path))
    except (KeyError, TypeError, ValueError) as exc:
        raise CliError(f"cannot read {path} as a run.json: {exc}") from exc
    order = tuple(
        int(outcome["response_id"]) for outcome in artefact.outcomes if "response_id" in outcome
    )
    if not order:
        raise CliError(
            f"{path} records no coded response, so it cannot say what order the run "
            "coded in; drop --run, or point it at the run that produced these rows"
        )
    return _Coding(
        order=order,
        batch_size=int(artefact.config.get("batch_size") or RunConfig().batch_size),
        policy=artefact.checkpoint_policy(),
        run_id=str(artefact.stats.run_id),
    )


#: Said in `affinity.md` and on stdout when the run had no descriptions to compare.
_NAMES_ONLY_NOTE = (
    "> Affinity ran **names-only**: no codebook with descriptions was supplied, so the "
    "cosine half of the blend compares code names alone. Pass `--codebook "
    "<codebook.json>` to give it descriptions (ADR-0029)."
)


def _codebook_for(artefact: Artefact, explicit: Codebook | None) -> tuple[Codebook, bool]:
    """The codebook affinity clusters, and whether it carries any description.

    Three sources, in order: the `--codebook` a caller named, the codebook the
    artefact itself was (`gaf analyse --assignments codebook.json`), or — for a bare
    row-oriented coding — one synthesised from the code names the rows use. The third
    is not a real codebook and says so: every code is a leaf with an empty description,
    which is exactly what "names-only" means and is reported rather than implied.
    """
    codebook = explicit if explicit is not None else artefact.codebook
    if codebook is None:
        codebook = Codebook(
            codes={
                code_id(name): Code(id=code_id(name), name=name, description="")
                for name in artefact.code_names
            }
        )
    described = any(code.description.strip() for code in codebook.codes.values())
    return codebook, described


def _write_readings(
    args: argparse.Namespace,
    out: Path,
    artefact: Artefact,
    matrix: OccurrenceMatrix,
    unfiltered: OccurrenceMatrix,
    config: RunConfig,
    analysis: AnalysisConfig,
    coding: _Coding,
) -> list[str]:
    """Patterns, affinity, growth — and the crosswalk when a target was named.

    **Affinity and the crosswalk read the filtered matrix**, the same one the
    clustering and the heatmap on `views.html` read, so that a cluster, an affinity
    group and a row of the heatmap describe the same set of codes.

    **Patterns read the unfiltered one.** A pattern view exists to show which codes
    co-occur, including the rare ones, and `gaf.analysis.patterns` says so in its own
    docstring; handing it the filtered matrix defeated that in its only caller, and on
    the real corpus it removed exactly the long tail the PI's pattern-mapping question
    is about (R1 I4). `PatternReport.filter` records which filter ran, so the two are
    told apart in the artefact.

    **Growth reads the run's own order and batch size** when `coding` carries them.
    Without them a response coded to nothing is not in the curve at all, so every
    batch after it is re-cut and ``new_codes_per_response`` — the one column this
    curve exists to add — is wrong (R1 C2). `growth.md` says which it was.
    """
    written: list[str] = []

    patterns = build_patterns(unfiltered)
    _write(out / "patterns.json", patterns.to_json_str())
    _write(out / "patterns.md", patterns.to_markdown())
    written += ["patterns.json", "patterns.md"]

    codebook, described = _codebook_for(artefact, load_codebook_arg(_path(args.codebook)))
    embedder = _embedder_for(config)
    affinity = build_affinity(codebook, matrix, embedder)
    _write(out / "affinity.json", affinity.to_json_str())
    markdown = affinity.to_markdown()
    if not described:
        markdown = f"{_NAMES_ONLY_NOTE}\n\n{markdown}"
    _write(out / "affinity.md", markdown)
    written += ["affinity.json", "affinity.md"]

    growth = code_growth(
        artefact.assignments,
        batch_size=coding.batch_size or analysis.saturation_batch_size,
        order=coding.order or None,
        response_ids=coding.order or None,
    )
    spikes = detect_spikes(growth, coding.policy or config.checkpoints)
    _write_json(out / "growth.json", growth.to_json())
    _write(out / "growth.md", f"{coding.growth_note()}\n\n{growth_markdown(growth, spikes)}")
    written += ["growth.json", "growth.md"]

    _out("")
    _out(
        f"  {len(patterns.groups)} pattern group(s); "
        f"{len(affinity.groups)} affinity group(s)"
        f"{' (names-only)' if not described else ''}; "
        f"{growth.total_codes} code(s) over {len(growth.points)} batch(es), "
        f"{len(spikes)} spike(s)."
    )
    if not described:
        _out(
            "  Affinity compared code names alone: no codebook with descriptions was "
            "supplied. Pass --codebook to give it descriptions."
        )

    target_path = _path(args.crosswalk_target)
    if target_path is not None:
        target = load_codebook_arg(target_path)
        assert target is not None  # load_codebook_arg refuses anything else by name
        crosswalk = build_crosswalk(
            codebook, target, embedder, config.rules, names_only=bool(args.crosswalk_names_only)
        )
        _write(out / "crosswalk.json", crosswalk.to_json_str())
        _write(out / "crosswalk.md", crosswalk.to_markdown())
        written += ["crosswalk.json", "crosswalk.md"]
        _out(
            f"  Crosswalk onto {target_path}: {len(crosswalk.mappings)} source leaf/leaves, "
            f"{len(crosswalk.unmapped_target_leaves)} blind spot(s), "
            f"{len(crosswalk.unmapped_source_leaves)} invention(s)."
        )
        _out(f"  {crosswalk.fair_mode_note}")
    return written


def _path(value: str | None) -> Path | None:
    return Path(value) if value else None


def add_analyse_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    analyse = sub.add_parser(
        "analyse",
        help="the deterministic analysis tail: matrix, Ward's HCA, saturation, patterns",
        description=(
            "Build the binary occurrence matrix, apply the low-frequency filter, run "
            "Ward's hierarchical cluster analysis and the saturation curve, and write "
            "three further readings of the same matrix — patterns, affinity and code "
            "growth — plus a crosswalk onto a second codebook when one is named. No "
            "model is consulted. Respondent metadata is joined here and nowhere else."
        ),
    )
    analyse.add_argument(
        "--assignments", required=True, help="assignments JSON/xlsx, or a codebook JSON"
    )
    analyse.add_argument("--data", help="corpus JSON or xlsx — fixes the row universe and metadata")
    analyse.add_argument(
        "--run",
        help=(
            "the run.json these assignments came from. Supplies the order the run coded "
            "in, the responses it coded to nothing and its own batch size, so the growth "
            "curve here is the curve its decision trace and timeline are keyed to"
        ),
    )
    analyse.add_argument("--out", required=True, help="output directory")
    analyse.add_argument("--min-frequency", type=int, help="override AnalysisConfig.min_code_frequency")
    analyse.add_argument(
        "--n-clusters",
        type=int,
        help="state the cluster count explicitly; recorded as an override (ADR-0020)",
    )
    analyse.add_argument(
        "--codebook",
        help=(
            "codebook JSON whose descriptions the affinity map compares; without it "
            "affinity runs on code names alone and says so"
        ),
    )
    analyse.add_argument(
        "--crosswalk-target",
        help="a second codebook JSON to map this coding's codebook onto (writes crosswalk.json/.md)",
    )
    analyse.add_argument(
        "--crosswalk-names-only",
        action="store_true",
        help="compare code names alone on both sides — the fair comparison when only one "
        "codebook carries descriptions (ADR-0029)",
    )
    _add_seed(analyse)
    analyse.set_defaults(handler=cmd_analyse, offline=True)
