#!/usr/bin/env bash
#
# The whole real-data sequence, from the three raw inputs to the shareable results
# directory, in one command. Every step runs offline: mock model clients, the lexical
# embedding fallback, no API key and no network. Nothing here passes --live.
#
#   make results-full
#   CORPUS_CSV=... TAGGED_CSV=... DEFINITIONS_MD=... ./scripts/run_full_results.sh
#
# Everything verbatim stays under runs/, which is gitignored. The only thing this
# script writes outside runs/ is $RESULTS_OUT, and the exporter's own guard is what
# decides whether a file may land there: it is fed every text the run directories
# hold, re-reads every file it writes, and deletes the whole export on a single shared
# run of characters.
#
# No respondent text appears in this file, and none is ever echoed by it: every line
# it prints is a count, a path or a code name.
#
set -euo pipefail

# ---------------------------------------------------------------- inputs (override me)
: "${CORPUS_CSV:=../Grounded AI Futures/data/IndiaProcess(1-200)-FinalCleaned.csv}"
: "${TAGGED_CSV:=../Grounded AI Futures/data/CodebookIndiaProcess(1-20)CodesExamples.csv}"
: "${DEFINITIONS_MD:=../Grounded AI Futures/codebook/AI_Perceptions_Codebook1.md}"
: "${QUESTION_VARIANT:=v2}"

# ---------------------------------------------------------------- outputs (override me)
: "${RUN_DIR:=runs/process200}"
: "${HUMAN_DIR:=runs/human200}"
: "${SEEDED_DIR:=runs/process200-seeded}"
: "${HALTED_DIR:=runs/process200-halted}"
: "${RESUMED_DIR:=runs/process200-resumed}"
: "${RESULTS_OUT:=results/india-process-1-200}"
: "${RESULTS_LABEL:=India Process, responses 1-200}"
: "${GUARD_SHINGLE:=20}"
: "${RUN_ID:=process200}"

step() { printf '\n=== %s ===\n' "$1"; }

for input in "$CORPUS_CSV" "$TAGGED_CSV" "$DEFINITIONS_MD"; do
    if [ ! -f "$input" ]; then
        echo "missing input: $input" >&2
        echo "set CORPUS_CSV / TAGGED_CSV / DEFINITIONS_MD to where the real files are" >&2
        exit 2
    fi
done

step "1. ingest the corpus"
uv run gaf ingest --input "$CORPUS_CSV" --question-variant "$QUESTION_VARIANT" \
    --out "$RUN_DIR/corpus.json"

step "2. organise his tagged export onto it, with his definitions"
uv run gaf codebook organise --tagged "$TAGGED_CSV" --corpus "$RUN_DIR/corpus.json" \
    --definitions "$DEFINITIONS_MD" --out "$HUMAN_DIR"

step "3a. his coding against his own rules"
uv run gaf check all --codebook "$HUMAN_DIR/codebook.json" --data "$RUN_DIR/corpus.json" \
    --offline --out "$HUMAN_DIR/golden_checks.json"

step "3b. the analysis tail over his coding, restricted to the coded set"
# No --data on purpose: the row universe is then the responses his export actually
# codes, not the whole corpus with the uncoded ones as all-zero rows. 04-clustering.md
# states the choice and measures the alternative, which is what step 3c builds.
uv run gaf analyse --assignments "$HUMAN_DIR/golden.json" --out "$HUMAN_DIR/analysis_golden" \
    --codebook "$HUMAN_DIR/codebook.json"

step "3c. the same coding over the whole corpus, for the contrast only"
uv run gaf analyse --assignments "$HUMAN_DIR/golden.json" --data "$RUN_DIR/corpus.json" \
    --out "$HUMAN_DIR/analysis_golden_all200" --codebook "$HUMAN_DIR/codebook.json"

step "3d. is his export's row order the same coding order as response id order?"
uv run python - "$HUMAN_DIR" <<'PY'
import json, sys
from pathlib import Path
from gaf.checks.growth import code_growth
from gaf.models import Assignment

human = Path(sys.argv[1])
placement = json.loads((human / "placement.json").read_text(encoding="utf-8"))
order: list[int] = []
for mapping in placement["mappings"]:
    rid = mapping.get("response_id")
    if mapping["outcome"] in ("exact", "fuzzy", "resolved") and rid is not None and rid not in order:
        order.append(int(rid))
rows = [Assignment.from_json(r) for r in json.loads((human / "golden.json").read_text(encoding="utf-8"))]
in_export_order = code_growth(rows, batch_size=10, order=order)
by_response_id = code_growth(rows, batch_size=10)
same = [p.to_json() for p in in_export_order.points] == [p.to_json() for p in by_response_id.points]
(human / "growth_export_order.json").write_text(
    json.dumps(
        {
            "order": "his export's row order",
            "n_responses": len(order),
            "identical_to_response_id_order": same,
            "curve": in_export_order.to_json(),
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
print(f"  coded responses in export order: {len(order)}")
print(f"  growth curve identical to response-id order: {same}")
PY

step "3e. a views page for his coding"
uv run gaf views --assignments "$HUMAN_DIR/golden.json" --codebook "$HUMAN_DIR/codebook.json" \
    --analysis "$HUMAN_DIR/analysis_golden" --out "$HUMAN_DIR/views/views.html"

step "4a. the cold machine run"
uv run gaf run --corpus "$RUN_DIR/corpus.json" --run-id "$RUN_ID" --offline --out "$RUN_DIR"

step "4b. the analysis tail over the machine run, with the crosswalk onto his codebook"
# --run so the growth curve here is cut the way the run itself cut it: its own
# processing order, its own batch size, and the responses it coded to nothing (which
# leave no assignment row and would otherwise shift every later batch).
uv run gaf analyse --assignments "$RUN_DIR/assignments.json" --data "$RUN_DIR/corpus.json" \
    --run "$RUN_DIR/run.json" \
    --out "$RUN_DIR/analysis" --codebook "$RUN_DIR/codebook.json" \
    --crosswalk-target "$HUMAN_DIR/codebook.json"

step "4c. the run report, the timeline, the trail and the decision matrix"
uv run gaf report --run "$RUN_DIR" --analysis "$RUN_DIR/analysis"

step "4d. a views page for the machine run"
uv run gaf views --run "$RUN_DIR" --analysis "$RUN_DIR/analysis" --out "$RUN_DIR/views/views.html"

step "5a. restrict the machine coding to the coded set, and merge both sides' definitions"
uv run python - "$RUN_DIR" "$HUMAN_DIR" <<'PY'
import json, sys
from pathlib import Path

run, human = Path(sys.argv[1]), Path(sys.argv[2])
golden = json.loads((human / "golden.json").read_text(encoding="utf-8"))
coded = sorted({int(r["response_id"]) for r in golden})
machine = json.loads((run / "assignments.json").read_text(encoding="utf-8"))
subset = [r for r in machine if int(r["response_id"]) in set(coded)]
(run / "assignments_coded_set.json").write_text(
    json.dumps(subset, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)

# One description map for both vocabularies. `gaf validate agreement` takes a single
# --codebook, and the point of this comparison is that neither side is now missing its
# definitions. Where a name exists on both sides the researcher's definition wins: it
# is the authored one, and a stand-in coder's sentence should never displace it.
his = json.loads((human / "codebook.json").read_text(encoding="utf-8"))["codes"]
its = json.loads((run / "codebook.json").read_text(encoding="utf-8"))["codes"]
by_name = {c["name"]: c for c in his}
collisions = sorted(c["name"] for c in its if c["name"] in by_name)
for code in its:
    by_name.setdefault(code["name"], code)
merged = []
for i, name in enumerate(sorted(by_name)):
    row = dict(by_name[name])
    row.update({"id": f"merged-{i:04d}", "parent_id": None, "evidence": [], "meta": {}})
    merged.append(row)
(run / "agreement_codebook_merged.json").write_text(
    json.dumps({"codes": merged}, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(f"  coded set: {len(coded)} responses; machine rows on it: {len(subset)} of {len(machine)}")
print(f"  merged description map: {len(merged)} codes; names on both sides: {len(collisions)}")
PY

step "5b. agreement, with descriptions on both sides"
uv run gaf validate agreement --human "$HUMAN_DIR/golden.json" \
    --machine "$RUN_DIR/assignments_coded_set.json" --data "$RUN_DIR/corpus.json" \
    --codebook "$RUN_DIR/agreement_codebook_merged.json" --out "$RUN_DIR/agreement" >/dev/null

step "5c. agreement, names only, for continuity with the earlier figures"
uv run gaf validate agreement --human "$HUMAN_DIR/golden.json" \
    --machine "$RUN_DIR/assignments_coded_set.json" --data "$RUN_DIR/corpus.json" \
    --out "$RUN_DIR/agreement_nameonly" >/dev/null

step "5d. threshold calibration against his coding"
uv run python - "$RUN_DIR" "$HUMAN_DIR" <<'PY'
import json, sys
from pathlib import Path
from gaf.checks.health import calibrate_thresholds
from gaf.config import CodingRules
from gaf.embed.service import EmbeddingService
from gaf.models import Assignment

run, human = Path(sys.argv[1]), Path(sys.argv[2])
load = lambda p: [Assignment.from_json(r) for r in json.loads(p.read_text(encoding="utf-8"))]  # noqa: E731
report = calibrate_thresholds(
    load(human / "golden.json"),
    load(run / "assignments_coded_set.json"),
    EmbeddingService(),
    CodingRules(),
)
payload = report.to_json()
(run / "calibration_report.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
for name, sweep in sorted(payload["sweeps"].items()):
    print(f"  {name}: {sweep['n_units']} unit(s), current {sweep['current']}, "
          f"recommended {sweep['recommended']}")
PY

step "6. a seeded run — coding into his organisation"
uv run gaf run --corpus "$RUN_DIR/corpus.json" --run-id "${RUN_ID}-seeded" --offline \
    --out "$SEEDED_DIR" --seed-codebook "$HUMAN_DIR/codebook.json" >/dev/null

step "7a. a halted run — stop at the first handover"
uv run gaf run --corpus "$RUN_DIR/corpus.json" --run-id "${RUN_ID}-halted" --offline \
    --out "$HALTED_DIR" --halt-on-checkpoint >/dev/null

step "7b. resume it from the codebook the halt left behind"
uv run gaf run --corpus "$RUN_DIR/corpus.json" --run-id "${RUN_ID}-resumed" --offline \
    --out "$RESUMED_DIR" --seed-codebook "$HALTED_DIR/codebook.json" \
    --skip-coded "$HALTED_DIR" >/dev/null

step "7c. does halted + resumed reproduce the cold run, row for row?"
uv run python - "$RUN_DIR" "$HALTED_DIR" "$RESUMED_DIR" <<'PY'
import json, sys
from pathlib import Path

def rows(directory: str):
    payload = json.loads((Path(directory) / "assignments.json").read_text(encoding="utf-8"))
    return [(int(r["response_id"]), r["code"], r.get("segment", "")) for r in payload]

cold, halted, resumed = (rows(a) for a in sys.argv[1:4])
print(f"  cold {len(cold)} rows; halted {len(halted)} + resumed {len(resumed)} = "
      f"{len(halted) + len(resumed)}")
print(f"  rows the two halves share: {len(set(halted) & set(resumed))}")
print(f"  row-for-row identical to the cold run: {halted + resumed == cold}")
PY

step "8. export the shareable results"
uv run python scripts/export_results.py \
    --run "$RUN_DIR" --human "$HUMAN_DIR" \
    --seeded "$SEEDED_DIR" --halted "$HALTED_DIR" --resumed "$RESUMED_DIR" \
    --guard-shingle "$GUARD_SHINGLE" --readme \
    --out "$RESULTS_OUT" --label "$RESULTS_LABEL"

step "9. the repository's own provenance scan over every tracked file"
uv run pytest tests/test_golden.py::test_no_tracked_file_contains_real_respondent_text -q -rs

printf '\nresults written to %s\n' "$RESULTS_OUT"
printf 'run directories (gitignored, they hold the corpus verbatim): %s %s %s %s %s\n' \
    "$RUN_DIR" "$HUMAN_DIR" "$SEEDED_DIR" "$HALTED_DIR" "$RESUMED_DIR"
printf 'run `make scrub` before this directory leaves the machine by any path but git push\n'
