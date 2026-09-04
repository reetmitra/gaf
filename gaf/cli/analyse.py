"""`gaf analyse` — the deterministic analysis tail: matrix, Ward's HCA, saturation.

Binary occurrence matrix, the low-frequency filter, Ward's hierarchical cluster
analysis and the theoretical-saturation curve. No model is consulted anywhere in this
command, and respondent metadata is joined here and nowhere else — never during
coding, so that a demographic column can never bias which code a response receives.

A degenerate matrix is **refused, not repaired**: `DegenerateMatrixError` still writes
the occurrence matrix and the saturation curve already computed, and says plainly why
clustering did not run, rather than returning a partition nobody asked for.

Serves **reliability**: the same assignments and the same `AnalysisConfig` produce the
same matrix, the same agglomeration schedule and the same cluster means, every time.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from gaf.analysis.hca import (
    DegenerateMatrixError,
    cluster_responses,
    dendrogram_svg,
    saturation_curve,
    saturation_svg,
)
from gaf.analysis.matrix import build_matrix
from gaf.cli._common import (
    EXIT_OK,
    CliError,
    _add_seed,
    _banner,
    _config_from_args,
    _out,
    _write,
    _write_json,
    load_artefact,
    load_corpus_arg,
)
from gaf.config import AnalysisConfig


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

    _banner("gaf analyse", str(path))
    _out(f"  {artefact.describe()}")

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
        _out(f"Artefacts written to {out}")
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
        "saturation.json",
        "saturation.md",
        "saturation.svg",
    ):
        _out(f"  {out / name}")
    return EXIT_OK


def add_analyse_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    analyse = sub.add_parser(
        "analyse",
        help="the deterministic analysis tail: matrix, Ward's HCA, saturation",
        description=(
            "Build the binary occurrence matrix, apply the low-frequency filter, run "
            "Ward's hierarchical cluster analysis and the saturation curve. No model "
            "is consulted. Respondent metadata is joined here and nowhere else."
        ),
    )
    analyse.add_argument(
        "--assignments", required=True, help="assignments JSON/xlsx, or a codebook JSON"
    )
    analyse.add_argument("--data", help="corpus JSON or xlsx — fixes the row universe and metadata")
    analyse.add_argument("--out", required=True, help="output directory")
    analyse.add_argument("--min-frequency", type=int, help="override AnalysisConfig.min_code_frequency")
    analyse.add_argument(
        "--n-clusters",
        type=int,
        help="state the cluster count explicitly; recorded as an override (ADR-0020)",
    )
    _add_seed(analyse)
    analyse.set_defaults(handler=cmd_analyse, offline=True)
