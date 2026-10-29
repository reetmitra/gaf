"""The spend cap and the run statistics (ADR-0053).

Two halves, one file, because both are about what a run tells the person who started it.

**`--max-usd`**, the claims a paid run depends on:

1. **The cap is checked before a call, and a call in flight is never cut short**, so the
   total can pass the cap by at most one call and never by more.
2. **A cache replay never counts**, and a cap that has been reached still answers a
   question already paid for.
3. **A halt is clean and resumable**: the response in flight is left out, the working
   codebook is the one the last complete response left, every paid call is in
   `llm_calls`, and a resumed run continues the same budget instead of starting fresh.
4. **With no flag, or with a flag that never trips, nothing else changes.**
5. **A cap that could not see the spend is refused up front**: a non-positive cap, and a
   hosted model with no price.

**The run statistics**, computed from the blackboard:

6. Coder agreement reconciles with the loop's own counts; the judge's siding reconciles
   with the judge's own calls; the 0.65 flag is exactly `>`.
7. Latency ignores cache replays and unmeasured calls, and an offline run reports no wall
   clock; spend groups by role and task.
8. They are computable for a run written before they existed, and carry no respondent
   text.

Every client here is a fake: a mock coder or judge billed a fixed price per fresh call.
No network, no key, and no respondent's words.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from gaf.agents.judge import JudgeAgent
from gaf.cli import EXIT_OK, EXIT_USAGE, main
from gaf.cli._budget import EXIT_BUDGET, cumulative_spend
from gaf.config import DEFAULT_LIVE_REGISTRY, ModelSpec, RunConfig
from gaf.ingest.corpus import write_corpus_json
from gaf.llm.base import CallLog, LLMClient, LLMRequest, LLMResult, TaskType
from gaf.llm.budget import (
    BudgetedLLMClient,
    BudgetExceededError,
    SpendBudget,
    guard_agents,
    guard_client,
    unpriced_hosted_roles,
)
from gaf.llm.cache import CachingLLMClient
from gaf.llm.mock import MockCoderClient, MockDefinerClient, MockJudgeClient
from gaf.pipeline.fast_loop import LoopComponents, offline_components, run_fast_loop
from gaf.pipeline.run_metrics import (
    SIDING_FLAG_SHARE,
    coder_agreement,
    compute_run_metrics,
    judge_siding,
    latency_summary,
    spend_summary,
)
from gaf.report.run_report import RUN_JSON_NAME, RunArtefact, render_run_report
from gaf.store.audit import AuditEvent
from gaf.store.blackboard import Blackboard, LLMCallRecord
from tests.fixtures.corpus import synthetic_corpus
from tests.fixtures.tagged import SAMPLE_PAIRS, write_tagged_csv
from tests.test_fast_loop import GreyEmbedder, RecordingJudge

PRICE = 0.10
"""What every fresh fake call bills, in dollars."""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


class PricedClient:
    """A fake provider: a mock client whose every fresh call is billed a fixed price."""

    def __init__(self, inner: LLMClient, cost_usd: float = PRICE) -> None:
        self.inner = inner
        self.spec = inner.spec
        self.cost_usd = cost_usd
        self.calls = 0

    def complete_json(self, request: LLMRequest) -> LLMResult:
        self.calls += 1
        return replace(self.inner.complete_json(request), cost_usd=self.cost_usd)


def priced_components(config: RunConfig, cost: float = PRICE) -> LoopComponents:
    """The offline triple with every agent's client replaced by a priced fake."""
    components = offline_components(config)
    for agent in (components.coder_a, components.coder_b, components.judge):
        assert agent is not None
        agent.client = PricedClient(agent.client, cost)
    return components


def config_for(run_id: str, **changes: Any) -> RunConfig:
    settings: dict[str, Any] = {"offline": True, "cache_dir": None, "batch_size": 5}
    settings.update(changes)
    return RunConfig(run_id=run_id, **settings)


def run_capped(
    cap: float | None,
    *,
    run_id: str = "capped",
    components: LoopComponents | None = None,
    baseline: float = 0.0,
    responses: Any = None,
    **changes: Any,
) -> tuple[Any, Blackboard, SpendBudget | None]:
    """`run_fast_loop` over the synthetic corpus with a priced triple under a cap."""
    config = config_for(run_id, **changes)
    triple = components or priced_components(config)
    budget = None if cap is None else SpendBudget(cap_usd=cap, baseline_usd=baseline)
    if budget is not None:
        guard_agents(budget, (triple.coder_a, triple.coder_b, triple.judge))
    board = Blackboard()
    result = run_fast_loop(
        list(responses if responses is not None else synthetic_corpus()),
        config=config,
        board=board,
        components=triple,
        budget=budget,
    )
    return result, board, budget


def run_cli(*argv: str) -> int:
    return main(list(argv))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_json(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("corpus") / "corpus.json"
    write_corpus_json(synthetic_corpus(), path)
    return path


@pytest.fixture
def priced(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make `gaf run` build the priced fakes instead of the free mocks."""
    monkeypatch.setattr("gaf.cli.run._components", lambda config: priced_components(config))


# --------------------------------------------------------------------------- #
# 1. The budget itself
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("cap", [0.0, -1.0, float("nan"), float("inf")])
def test_a_cap_must_be_a_positive_finite_amount(cap: float) -> None:
    with pytest.raises(ValueError, match="positive"):
        SpendBudget(cap_usd=cap)


def test_a_baseline_cannot_be_negative() -> None:
    with pytest.raises(ValueError, match="negative"):
        SpendBudget(cap_usd=1.0, baseline_usd=-0.01)


def test_reaching_the_cap_is_enough_to_stop() -> None:
    budget = SpendBudget(cap_usd=1.0)
    budget.charge(0.99)
    budget.check()  # under the cap: a call may start
    budget.charge(0.01)
    assert budget.exhausted and budget.remaining_usd == 0.0
    with pytest.raises(BudgetExceededError) as stopped:
        budget.check(role="judge", task="judge_fit")
    assert stopped.value.role == "judge" and stopped.value.cap_usd == 1.0
    assert budget.tripped is not None


def test_the_baseline_counts_against_the_cap() -> None:
    budget = SpendBudget(cap_usd=1.0, baseline_usd=0.95)
    budget.check()
    budget.charge(0.05)
    with pytest.raises(BudgetExceededError):
        budget.check()
    assert budget.cumulative_usd == pytest.approx(1.0)


def test_a_free_call_never_moves_the_total() -> None:
    budget = SpendBudget(cap_usd=1.0)
    budget.charge(0.0)
    budget.charge(-5.0)
    assert budget.run_usd == 0.0


def test_the_budget_serialises_without_text() -> None:
    budget = SpendBudget(
        cap_usd=2.0, baseline_usd=0.5, baseline_sources=[{"run": "runs/a", "usd": 0.5}]
    )
    budget.charge(0.25)
    assert budget.to_json() == {
        "cap_usd": 2.0,
        "baseline_usd": 0.5,
        "run_usd": 0.25,
        "cumulative_usd": 0.75,
        "halted": False,
        "baseline_sources": [{"run": "runs/a", "usd": 0.5}],
    }


# --------------------------------------------------------------------------- #
# 2. The guard: before a call, never during one, never on a replay
# --------------------------------------------------------------------------- #


def request(user: str = "q") -> LLMRequest:
    return LLMRequest(task=TaskType.CODE, system="s", user=user, prompt_version="test-v1")


def coder_spec() -> ModelSpec:
    return RunConfig().models.coder_a


def test_the_guard_stops_before_the_call_that_would_start_over_the_cap() -> None:
    fake = PricedClient(MockCoderClient(coder_spec()), cost_usd=0.40)
    guarded = BudgetedLLMClient(fake, SpendBudget(cap_usd=1.0))
    guarded.complete_json(request("1"))  # total 0.40
    guarded.complete_json(request("2"))  # total 0.80, still under the cap
    guarded.complete_json(request("3"))  # started under the cap; total 1.20 is the overshoot
    with pytest.raises(BudgetExceededError):
        guarded.complete_json(request("4"))
    assert fake.calls == 3, "the refused call must never reach the provider"
    assert guarded.budget.cumulative_usd - 1.0 < 0.40, "overshoot is at most one call"


def test_a_call_that_started_under_the_cap_is_completed_not_cut_short() -> None:
    fake = PricedClient(MockCoderClient(coder_spec()), cost_usd=5.0)
    guarded = BudgetedLLMClient(fake, SpendBudget(cap_usd=1.0))
    result = guarded.complete_json(request())
    assert result.cost_usd == 5.0 and guarded.budget.run_usd == 5.0


def test_a_cache_replay_never_counts_and_is_answered_even_at_the_cap(tmp_path: Path) -> None:
    fake = PricedClient(MockCoderClient(coder_spec()), cost_usd=0.60)
    budget = SpendBudget(cap_usd=1.0)
    cached = guard_client(CachingLLMClient(fake, tmp_path / "cache"), budget)

    first = cached.complete_json(request("paid"))
    again = cached.complete_json(request("paid"))
    assert not first.cache_hit and again.cache_hit
    assert fake.calls == 1 and budget.run_usd == pytest.approx(0.60)

    budget.charge(0.60)  # now over the cap
    assert budget.exhausted
    assert cached.complete_json(request("paid")).cache_hit, "an answer already paid for is free"
    with pytest.raises(BudgetExceededError):
        cached.complete_json(request("new"))
    assert fake.calls == 1


def test_guard_client_puts_the_guard_inside_the_cache_and_is_idempotent(tmp_path: Path) -> None:
    fake = PricedClient(MockCoderClient(coder_spec()))
    budget = SpendBudget(cap_usd=1.0)
    cache = CachingLLMClient(fake, tmp_path)
    assert guard_client(cache, budget) is cache
    assert isinstance(cache.inner, BudgetedLLMClient) and cache.inner.inner is fake
    guard_client(cache, budget)
    assert cache.inner.inner is fake, "guarding twice must not stack two guards"

    bare = guard_client(fake, budget)  # the --no-cache case
    assert isinstance(bare, BudgetedLLMClient) and bare.spec is fake.spec


def test_guard_agents_skips_an_absent_judge() -> None:
    config = config_for("no-judge")
    components = offline_components(config)
    budget = SpendBudget(cap_usd=1.0)
    guard_agents(budget, (components.coder_a, None, components.coder_b))
    assert isinstance(components.coder_a.client, BudgetedLLMClient)
    assert isinstance(components.coder_b.client, BudgetedLLMClient)


def test_a_refusal_is_not_an_llm_error() -> None:
    """Nothing that retries or catches a transport fault may swallow a spend cap."""
    from gaf.llm.base import LLMError

    assert not issubclass(BudgetExceededError, LLMError)


def test_hosted_roles_without_a_price_are_found_and_free_ones_are_not() -> None:
    assert unpriced_hosted_roles(DEFAULT_LIVE_REGISTRY) == []
    assert unpriced_hosted_roles(RunConfig().models) == [], "mock roles are free"
    free = ModelSpec(provider="local", model="qwen3.5:9b", role="coder_a")
    hosted = ModelSpec(provider="anthropic", model="some-model", role="judge")
    registry = replace(DEFAULT_LIVE_REGISTRY, coder_a=free, judge=hosted)
    assert unpriced_hosted_roles(registry) == [hosted]


# --------------------------------------------------------------------------- #
# 3. A halt is clean and resumable
# --------------------------------------------------------------------------- #


def test_an_uncapped_run_and_a_capped_run_that_never_trips_are_the_same_run() -> None:
    plain, _, _ = run_capped(None, run_id="same")
    roomy, _, budget = run_capped(1000.0, run_id="same")
    assert plain.codebook_json() == roomy.codebook_json()
    assert roomy.stats.responses_uncoded == 0
    assert budget is not None and not budget.exhausted
    assert plain.stats.budget is None and "budget" not in plain.stats.to_json()
    assert roomy.stats.budget is not None and roomy.stats.budget["halted"] is False


def test_a_run_stops_at_the_cap_and_says_where() -> None:
    result, board, budget = run_capped(2.0)
    stats = result.stats
    assert budget is not None and stats.budget is not None
    assert stats.budget["halted"] is True
    assert 0 < stats.n_responses < len(synthetic_corpus())
    assert stats.responses_uncoded == len(synthetic_corpus()) - stats.n_responses
    assert stats.budget["responses_uncoded"] == stats.responses_uncoded
    assert stats.budget["halted_at_response"] not in {o.response_id for o in result.outcomes}
    assert stats.halted_at_batch is None, "a spend halt is not a checkpoint halt"
    with board:
        events = board.audit("capped").events(event="run_halted_spend_cap")
        assert len(events) == 1
        payload = events[0].payload
        assert payload["reason"] == "max_usd" and payload["cap_usd"] == 2.0
        assert payload["response_id"] == stats.budget["halted_at_response"]
        assert board.audit("capped").events(event="run_completed"), "the run closes normally"


@pytest.mark.parametrize("cap", [0.05, 0.15, 0.45, 0.95, 1.55, 2.5, 4.05])
def test_whatever_the_cap_every_paid_call_is_recorded_and_overshoot_is_one_call(
    cap: float,
) -> None:
    """The invariant that makes the cap trustworthy, at caps that fall mid-response."""
    result, board, budget = run_capped(cap)
    assert budget is not None
    with board:
        recorded = board.llm_spend("capped")
        calls = board.read_llm_calls("capped")
    assert recorded == pytest.approx(budget.run_usd), "a paid call missing from llm_calls"
    assert len(calls) == round(budget.run_usd / PRICE)
    assert budget.cumulative_usd >= cap, "the run stopped early"
    assert budget.cumulative_usd < cap + PRICE + 1e-9, "overshoot is at most one call"
    assert result.stats.llm["cost_usd"] == pytest.approx(budget.run_usd)


def test_a_response_halted_mid_way_is_not_counted_as_coded_by_the_store() -> None:
    """Both coders answered, the first judge call was refused: nothing was finished."""
    result, board, budget = run_capped(0.15)
    assert budget is not None and result.stats.n_responses == 0
    with board:
        assert board.coded_response_count("capped") == 1, "the coders' rows are real, and kept"
        assert board.completed_response_count("capped") == 0
        assert len(board.read_llm_calls("capped")) == 2, "the two coder calls were paid and recorded"


def test_a_halted_codebook_is_the_codebook_of_the_responses_it_coded() -> None:
    """The response in flight leaves no trace in the codebook."""
    halted, _, _ = run_capped(2.0, run_id="prefix")
    coded = [o.response_id for o in halted.outcomes]
    prefix, _, _ = run_capped(None, run_id="prefix", responses=[
        r for r in synthetic_corpus() if r.id in set(coded)
    ])
    assert halted.codebook_json() == prefix.codebook_json()
    assert [a.to_json() for a in halted.assignments] == [a.to_json() for a in prefix.assignments]


def test_a_cap_already_reached_codes_nothing_and_still_closes_the_run() -> None:
    result, board, _ = run_capped(1.0, baseline=1.0)
    assert result.stats.n_responses == 0
    assert result.stats.responses_uncoded == len(synthetic_corpus())
    assert result.stats.budget is not None and result.stats.budget["halted"] is True
    with board:
        assert board.llm_spend("capped") == 0.0, "no call may be made past the cap"


def test_replays_of_paid_questions_spend_nothing_so_a_resumed_run_finishes(
    tmp_path: Path,
) -> None:
    """Fill the cache under a roomy cap, then re-run under a cap of one cent."""
    cache = tmp_path / "cache"

    def cached_triple(config: RunConfig) -> LoopComponents:
        triple = offline_components(config)
        for agent in (triple.coder_a, triple.coder_b, triple.judge):
            assert agent is not None
            agent.client = CachingLLMClient(PricedClient(agent.client, PRICE), cache)
        return triple

    config = config_for("cached")
    first, _, first_budget = run_capped(1000.0, run_id="cached", components=cached_triple(config))
    assert first_budget is not None and first_budget.run_usd > 0

    second, _, second_budget = run_capped(0.01, run_id="cached", components=cached_triple(config))
    assert second_budget is not None
    assert second_budget.run_usd == 0.0, "every answer was in the cache"
    assert second.stats.responses_uncoded == 0
    assert second.codebook_json() == first.codebook_json()
    assert second.stats.llm["cache_hits"] == second.stats.llm["calls"]


# --------------------------------------------------------------------------- #
# 4. Through the CLI
# --------------------------------------------------------------------------- #


@pytest.fixture
def halted_run(
    tmp_path: Path, corpus_json: Path, priced: None, capsys: pytest.CaptureFixture[str]
) -> tuple[Path, str]:
    out = tmp_path / "first"
    code = run_cli(
        "run", "--corpus", str(corpus_json), "--run-id", "first", "--out", str(out),
        "--no-cache", "--max-usd", "0.5",
    )
    printed = capsys.readouterr().out
    assert code == EXIT_OK, "a spend halt is the designed behaviour, like a checkpoint halt"
    return out, printed


def test_a_capped_run_exits_zero_and_says_why_and_how_to_continue(
    halted_run: tuple[Path, str],
) -> None:
    out, printed = halted_run
    assert "HALTED at the spend cap" in printed
    assert "responses remaining" in printed and "not counted as coded" in printed
    assert f"--skip-coded {out}" in printed and "--max-usd <USD>" in printed
    stats = read_json(out / "stats.json")
    assert stats["budget"]["halted"] is True
    assert stats["budget"]["cumulative_usd"] >= 0.5
    assert stats["responses_uncoded"] > 0
    for name in (RUN_JSON_NAME, "codebook.json", "assignments.json", "audit.jsonl", "report.txt"):
        assert (out / name).exists(), "a halted run still closes its directory"
    report = (out / "report.txt").read_text(encoding="utf-8")
    assert "STOPPED EARLY at its spend cap" in report and "SPEND CAP" in report


def test_a_resumed_run_continues_the_same_budget(
    tmp_path: Path, corpus_json: Path, halted_run: tuple[Path, str], priced: None
) -> None:
    first, _ = halted_run
    spent_first = read_json(first / "stats.json")["budget"]["run_usd"]
    resumed = tmp_path / "second"
    assert run_cli(
        "run", "--corpus", str(corpus_json), "--run-id", "second", "--out", str(resumed),
        "--no-cache", "--seed-codebook", str(first / "codebook.json"),
        "--skip-coded", str(first), "--max-usd", "1.0",
    ) == EXIT_OK
    budget = read_json(resumed / "stats.json")["budget"]
    assert budget["baseline_usd"] == pytest.approx(spent_first), "the first run's spend counts"
    assert [row["run"] for row in budget["baseline_sources"]] == [str(first)]
    assert budget["cumulative_usd"] == pytest.approx(budget["baseline_usd"] + budget["run_usd"])
    # It spent only what was left under the cap (plus at most one call), not a fresh $1.00.
    assert budget["run_usd"] < 1.0 - spent_first + PRICE + 1e-9
    assert budget["cumulative_usd"] >= 1.0 and budget["halted"] is True

    third = tmp_path / "third"
    assert run_cli(
        "run", "--corpus", str(corpus_json), "--run-id", "third", "--out", str(third),
        "--no-cache", "--seed-codebook", str(resumed / "codebook.json"),
        "--skip-coded", str(resumed), "--max-usd", "100",
    ) == EXIT_OK
    chain = read_json(third / "stats.json")["budget"]
    assert [row["run"] for row in chain["baseline_sources"]] == [str(resumed), str(first)]
    assert chain["baseline_usd"] == pytest.approx(spent_first + budget["run_usd"])
    assert chain["halted"] is False and read_json(third / "stats.json")["responses_uncoded"] == 0


def test_resuming_under_a_cap_already_reached_is_refused_before_anything_changes(
    tmp_path: Path, corpus_json: Path, halted_run: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    first, _ = halted_run
    before = (first / "gaf.sqlite").stat().st_size
    code = run_cli(
        "run", "--corpus", str(corpus_json), "--run-id", "again", "--out", str(first),
        "--no-cache", "--skip-coded", str(first), "--max-usd", "0.5",
    )
    assert code == EXIT_BUDGET
    assert "raise --max-usd" in capsys.readouterr().err
    assert (first / "gaf.sqlite").stat().st_size == before, "the ledger must survive a refusal"


def test_a_checkpoint_counts_the_spend_of_its_run(
    halted_run: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    first, _ = halted_run
    assert run_cli("checkpoint", "--run", str(first), "--max-usd", "0.01") == EXIT_BUDGET
    assert "spend cap reached" in capsys.readouterr().err
    with Blackboard(first / "gaf.sqlite") as board:
        assert not board.audit("first").events(event="checkpoint_started"), (
            "a refused checkpoint writes nothing"
        )
    assert run_cli("checkpoint", "--run", str(first), "--max-usd", "100") == EXIT_OK


def test_every_reading_command_still_works_on_a_halted_run(
    halted_run: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    first, _ = halted_run
    assert run_cli("report", "--run", str(first)) == EXIT_OK
    assert (first / "views.html").exists() and (first / "run_metrics.json").exists()
    text = (first / "report.txt").read_text(encoding="utf-8")
    assert "STOPPED EARLY" in text and "SPEND BY ROLE AND TASK" in text
    capsys.readouterr()


@pytest.mark.parametrize("cap", ["0", "-1", "nan", "inf"])
def test_a_cap_that_is_not_a_positive_amount_is_a_usage_error(
    tmp_path: Path, corpus_json: Path, cap: str
) -> None:
    assert run_cli(
        "run", "--corpus", str(corpus_json), "--out", str(tmp_path / "x"), "--max-usd", cap
    ) == EXIT_USAGE


def test_a_live_cap_over_a_hosted_model_with_no_price_is_refused(
    tmp_path: Path, corpus_json: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    profile = tmp_path / "unpriced.json"
    profile.write_text(
        json.dumps(
            {
                "models": {
                    "coder_a": {"provider": "anthropic", "model": "m-a"},
                    "coder_b": {"provider": "openai", "model": "m-b"},
                    "judge": {"provider": "anthropic", "model": "m-j"},
                    "refactorer": {"provider": "anthropic", "model": "m-r"},
                }
            }
        ),
        encoding="utf-8",
    )
    code = run_cli(
        "run", "--corpus", str(corpus_json), "--out", str(tmp_path / "o"), "--live",
        "--profile", str(profile), "--max-usd", "5",
    )
    assert code == EXIT_USAGE
    assert "needs a price for every hosted model" in capsys.readouterr().err


def test_the_flag_changes_nothing_when_it_never_trips(tmp_path: Path, corpus_json: Path) -> None:
    runs = {}
    for label, extra in (("plain", []), ("roomy", ["--max-usd", "1000"])):
        out = tmp_path / label
        assert run_cli(
            "run", "--corpus", str(corpus_json), "--run-id", "same", "--out", str(out),
            "--no-cache", *extra,
        ) == EXIT_OK
        runs[label] = out
    for name in ("codebook.json", "assignments.json", "findings.json"):
        assert (runs["plain"] / name).read_bytes() == (runs["roomy"] / name).read_bytes()
    assert "budget" not in read_json(runs["plain"] / "stats.json")
    roomy = read_json(runs["roomy"] / "stats.json")["budget"]
    assert roomy["halted"] is False and roomy["cumulative_usd"] == 0.0
    assert "SPEND CAP" not in (runs["plain"] / "report.txt").read_text(encoding="utf-8")
    assert "cap not reached" in (runs["roomy"] / "report.txt").read_text(encoding="utf-8")


def test_the_cap_reaches_the_judge_of_gaf_check(
    tmp_path: Path, corpus_json: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from tests.fixtures.codebooks import toy_codebook

    codebook = tmp_path / "toy.json"
    codebook.write_text(toy_codebook().to_json_str(), encoding="utf-8")

    def priced_judge(config: RunConfig) -> JudgeAgent:
        client = PricedClient(MockJudgeClient(config.models.judge))
        return JudgeAgent(client, config=config, call_log=CallLog())

    monkeypatch.setattr("gaf.cli.check._judge_for", priced_judge)
    code = run_cli(
        "check", "semantic", "--codebook", str(codebook), "--data", str(corpus_json),
        "--max-usd", "0.05",
    )
    assert code == EXIT_BUDGET
    assert "spend cap reached" in capsys.readouterr().err


def test_the_cap_reaches_the_definer(
    tmp_path: Path, corpus_json: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from gaf.agents.definer import DefinerAgent

    organised = tmp_path / "book"
    tagged = write_tagged_csv(tmp_path / "pairs.csv", SAMPLE_PAIRS)
    assert run_cli(
        "codebook", "organise", "--tagged", str(tagged), "--corpus", str(corpus_json),
        "--out", str(organised),
    ) == EXIT_OK
    capsys.readouterr()

    def priced_definer(config: Any, call_log: CallLog) -> DefinerAgent:
        client = PricedClient(MockDefinerClient(config.models.refactorer))
        return DefinerAgent(client, config=config, call_log=call_log)

    monkeypatch.setattr("gaf.cli.codebook._definer_for", priced_definer)
    code = run_cli("codebook", "define", "--organised", str(organised), "--max-usd", "0.05")
    assert code == EXIT_BUDGET
    assert "spend cap reached" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# 5. Where the money is counted from
# --------------------------------------------------------------------------- #


def make_run_dir(path: Path, run_id: str, spend: float, *, parent: Path | None = None) -> Path:
    """A run directory with a ledger of `spend` dollars and an optional resume link."""
    path.mkdir(parents=True)
    with Blackboard(path / "gaf.sqlite") as board:
        board.register_run(config_for(run_id))
        board.write_llm_call(
            LLMResult(
                data={}, task=TaskType.CODE, provider="p", model="m", prompt_version="v",
                cost_usd=spend,
            ),
            run_id=run_id, role="coder_a",
        )
    provenance = {"skipped_from": {"run": str(parent)}} if parent else {}
    document = {"result": {"run_id": run_id}, "provenance": provenance}
    (path / "run.json").write_text(json.dumps(document), encoding="utf-8")
    return path


def test_the_chain_is_followed_through_every_resume(tmp_path: Path) -> None:
    a = make_run_dir(tmp_path / "a", "a", 1.25)
    b = make_run_dir(tmp_path / "b", "b", 0.50, parent=a)
    c = make_run_dir(tmp_path / "c", "c", 0.25, parent=b)
    total, sources = cumulative_spend(c)
    assert total == pytest.approx(2.0)
    assert [row["run"] for row in sources] == [str(c), str(b), str(a)]


def test_a_missing_ledger_is_reported_not_counted_as_zero(tmp_path: Path) -> None:
    b = make_run_dir(tmp_path / "b", "b", 0.50, parent=tmp_path / "gone")
    total, sources = cumulative_spend(b)
    assert total == pytest.approx(0.50)
    assert sources[-1] == {"run": str(tmp_path / "gone"), "usd": None, "unreadable": True}


def test_a_resume_loop_cannot_hang_the_count(tmp_path: Path) -> None:
    a = make_run_dir(tmp_path / "a", "a", 1.0)
    document = read_json(a / "run.json")
    document["provenance"] = {"skipped_from": {"run": str(a)}}
    (a / "run.json").write_text(json.dumps(document), encoding="utf-8")
    total, sources = cumulative_spend(a)
    assert total == pytest.approx(1.0) and len(sources) == 1


# --------------------------------------------------------------------------- #
# 6. Coder agreement and the judge's siding
# --------------------------------------------------------------------------- #


def accepted_event(
    *, agreed: int = 0, keeps: int = 0, drops: int = 0, disputed: int = 0,
    only_a: int = 0, only_b: int = 0, unresolved: int = 0,
) -> AuditEvent:
    """One `candidates_accepted` row, built the way the router writes it."""
    accepted: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    accepted += [{"origin": "agreed", "escalated": False}] * agreed
    for _ in range(keeps):
        accepted += [{"origin": "grey", "escalated": True, "verdict": "KEEP"}] * 2
    for _ in range(drops):
        accepted.append({"origin": "grey", "escalated": True, "verdict": "DROP"})
        dropped.append({"origin": "grey", "escalated": True, "verdict": "DROP"})
    accepted += [{"origin": "grey", "escalated": False}] * (2 * unresolved)
    accepted += [{"origin": "disputed", "escalated": False}] * (2 * disputed)
    accepted += [{"origin": "unmatched_a", "escalated": False}] * only_a
    accepted += [{"origin": "unmatched_b", "escalated": False}] * only_b
    return AuditEvent(
        event_id=1, run_id="r", created_at="2026-10-04T00:00:00.000000Z",
        event="candidates_accepted", payload={"accepted": accepted, "dropped": dropped},
    )


def test_every_comparison_lands_in_exactly_one_outcome() -> None:
    block = coder_agreement(
        [accepted_event(agreed=5, keeps=2, drops=1, disputed=3, only_a=2, only_b=1, unresolved=4)]
    )
    assert block["comparisons"] == 5 + (2 + 1) + 4 + 3 + 2 + 1
    assert block["agreed_outright"] == {"count": 5, "share": round(5 / 18, 4)}
    assert block["grey_zone"]["count"] == 7
    assert (block["grey_zone"]["judged"], block["grey_zone"]["unresolved_no_judge"]) == (3, 4)
    dispute = block["disputed_or_unmatched"]
    assert (dispute["disputed"], dispute["unmatched_a"], dispute["unmatched_b"]) == (3, 2, 1)
    assert block["agreed_outright"]["count"] + block["grey_zone"]["count"] + dispute["count"] == 18


def test_a_run_with_no_comparisons_has_no_shares_rather_than_a_division_error() -> None:
    block = coder_agreement([])
    assert block["comparisons"] == 0 and block["agreed_outright"]["share"] is None
    siding = judge_siding([])
    assert siding["decisions"] == 0 and siding["flag"] is False


def test_the_siding_flag_is_strictly_above_sixty_five_percent() -> None:
    at = judge_siding([accepted_event(drops=13, keeps=7)])  # 13/20 = 0.65 exactly
    assert at["coder_a"]["share"] == SIDING_FLAG_SHARE and at["flag"] is False
    above = judge_siding([accepted_event(drops=14, keeps=6)])
    assert above["flag"] is True and above["coder_a"]["count"] == 14
    assert above["neither"]["count"] == 6 and above["coder_b"] == {"count": 0, "share": 0.0}


def test_few_rulings_are_flagged_unreliable_but_still_counted() -> None:
    few = judge_siding([accepted_event(drops=3)])
    assert few["flag"] is True and few["reliable"] is False
    assert judge_siding([accepted_event(drops=15, keeps=5)])["reliable"] is True


def test_siding_counts_only_pairs_a_judge_actually_ruled_on() -> None:
    siding = judge_siding([accepted_event(drops=2, keeps=1, unresolved=9, disputed=9)])
    assert siding["decisions"] == 3


@pytest.mark.parametrize("verdict", ["KEEP", "DROP"])
def test_the_siding_reconciles_with_the_judge_s_own_calls_in_a_real_run(verdict: str) -> None:
    """GreyEmbedder puts every distinct pair in the grey zone, so the judge is asked."""
    config = config_for("grey")
    log = CallLog()
    offline = offline_components(config, call_log=log)
    judge = RecordingJudge(dispute=verdict)
    components = LoopComponents(
        coder_a=offline.coder_a, coder_b=offline.coder_b, embedder=GreyEmbedder(),
        judge=judge, call_log=log,
    )
    board = Blackboard()
    result = run_fast_loop(
        synthetic_corpus(), config=config, board=board, components=components
    )
    asked = sum(1 for kind, _ in judge.calls if kind == "dispute")
    siding = result.stats.run_metrics["judge_siding"]
    assert asked > 0 and siding["decisions"] == asked
    if verdict == "DROP":
        assert siding["coder_a"]["count"] == asked == result.stats.candidates_dropped["dispute"]
        assert siding["flag"] is True
    else:
        assert siding["neither"]["count"] == asked and siding["flag"] is False
    agreement = result.stats.run_metrics["coder_agreement"]
    assert agreement["grey_zone"]["judged"] == asked
    assert agreement["routing"]["candidates"] == sum(
        result.stats.routes[key] for key in ("MERGE", "CREATE", "JUDGE")
    )


def test_agreement_reconciles_with_the_loop_s_own_counts_offline() -> None:
    result, _, _ = run_capped(None)
    origins = result.stats.acceptance_by_origin
    block = result.stats.run_metrics["coder_agreement"]
    assert block["agreed_outright"]["count"] == origins["agreed"]
    assert block["disputed_or_unmatched"]["disputed"] == origins["disputed"] // 2
    assert block["disputed_or_unmatched"]["unmatched_a"] == origins["unmatched_a"]
    assert block["disputed_or_unmatched"]["unmatched_b"] == origins["unmatched_b"]
    assert block["grey_zone"]["count"] == 0, "the offline lexical space has no grey zone"


# --------------------------------------------------------------------------- #
# 7. Latency and spend
# --------------------------------------------------------------------------- #


def call(role: str, task: str, subject: str, latency: float, *, hit: bool = False) -> LLMCallRecord:
    return LLMCallRecord(
        call_id=f"{role}-{task}-{subject}-{latency}", run_id="r", role=role, task=task,
        provider="p", model="m", prompt_version="v", subject=subject, input_tokens=10,
        output_tokens=5, cost_usd=0.0 if hit else 0.01, latency_ms=latency, cache_hit=hit,
        fail_safe=False, created_at="t",
    )


def test_latency_ignores_replays_and_unmeasured_calls_and_sums_per_response() -> None:
    calls = [
        call("coder_a", "code", "response:1", 1000.0),
        call("coder_b", "code", "response:1", 3000.0),
        call("judge", "judge_fit", "response:1", 500.0),
        call("coder_a", "code", "response:2", 2000.0),
        call("judge", "judge_fit", "response:2", 0.0, hit=True),  # a replay is not timed
        call("judge", "judge_fit", "response:2", 0.0),  # never measured
        call("refactorer", "refactor", "snap-1", 9000.0),  # not about a response
    ]
    block = latency_summary(calls, [], offline=False)
    assert block["measured"] is True
    assert block["per_call_ms"]["n"] == 5 and block["per_call_ms"]["max"] == 9000.0
    per_response = block["per_response_model_s"]
    assert per_response["n"] == 2 and per_response["total"] == pytest.approx(6.5)
    assert per_response["max"] == pytest.approx(4.5) and per_response["median"] == pytest.approx(3.25)
    rows = {(r["role"], r["task"]): r for r in block["by_role_task_ms"]}
    assert rows[("coder_a", "code")]["n"] == 2 and rows[("coder_a", "code")]["mean"] == 1500.0


def test_an_offline_run_reports_unmeasured_latency_and_no_wall_clock() -> None:
    calls = [call("coder_a", "code", "response:1", 0.0)]
    block = latency_summary(calls, [], offline=True)
    assert block["measured"] is False and block["per_call_ms"]["mean"] is None
    assert block["wall_clock"] is None


def stamped(event: str, subject: str, stamp: str) -> AuditEvent:
    return AuditEvent(
        event_id=1, run_id="r", created_at=stamp, event=event, subject=subject, payload={}
    )


def test_a_live_run_adds_wall_clock_from_the_audit_log_and_an_offline_one_does_not() -> None:
    events = [
        stamped("run_started", "r", "2026-10-05T10:00:00.000000Z"),
        stamped("response_prepared", "1", "2026-10-05T10:00:01.000000Z"),
        stamped("assignments_written", "1", "2026-10-05T10:00:11.000000Z"),
        stamped("response_prepared", "2", "2026-10-05T10:00:11.500000Z"),
        stamped("assignments_written", "2", "2026-10-05T10:00:31.500000Z"),
        stamped("run_completed", "r", "2026-10-05T10:00:32.000000Z"),
    ]
    live = latency_summary([], events, offline=False)["wall_clock"]
    assert live["per_response_s"]["mean"] == 15.0 and live["per_response_s"]["max"] == 20.0
    assert live["run_total_s"] == 32.0
    assert latency_summary([], events, offline=True)["wall_clock"] is None


def test_spend_groups_by_role_and_task_and_a_replay_costs_nothing() -> None:
    board = Blackboard()
    board.register_run(config_for("spend"))

    def write(role: str, task: TaskType, cost: float, *, hit: bool = False, n: int = 1) -> None:
        for index in range(n):
            board.write_llm_call(
                LLMResult(
                    data={}, task=task, provider="p", model=f"model-{role}", prompt_version="v",
                    input_tokens=100, output_tokens=20, cost_usd=cost, cache_hit=hit,
                ),
                run_id="spend", role=role, subject=f"response:{index}",
            )

    write("coder_a", TaskType.CODE, 0.02, n=3)
    write("judge", TaskType.JUDGE_FIT, 0.005, n=4)
    write("judge", TaskType.JUDGE_FIT, 0.0, hit=True, n=2)
    usage = board.llm_usage("spend")
    assert [(r["role"], r["task"]) for r in usage] == [("coder_a", "code"), ("judge", "judge_fit")]
    judge = usage[1]
    assert (judge["calls"], judge["billed_calls"], judge["cache_hits"]) == (6, 4, 2)
    assert judge["input_tokens"] == 600, "tokens size the workload, replays included"
    assert judge["cost_usd"] == pytest.approx(0.02)
    assert board.llm_spend("spend") == pytest.approx(0.06 + 0.02)

    block = spend_summary(usage, responses=3)
    assert block["cost_usd"] == pytest.approx(0.08) and block["calls"] == 9
    assert block["usd_per_response"] == pytest.approx(0.08 / 3, abs=1e-6)
    assert [row["role"] for row in block["by_role"]] == ["coder_a", "judge"]
    assert spend_summary([], responses=0)["usd_per_response"] is None


# --------------------------------------------------------------------------- #
# 8. The report, old runs, and no respondent text
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def offline_run(tmp_path_factory: pytest.TempPathFactory, corpus_json: Path) -> Path:
    out = tmp_path_factory.mktemp("offline") / "run"
    assert run_cli(
        "run", "--corpus", str(corpus_json), "--run-id", "offline", "--out", str(out),
        "--no-cache",
    ) == EXIT_OK
    return out


def test_the_run_report_carries_every_new_section(offline_run: Path) -> None:
    text = (offline_run / "report.txt").read_text(encoding="utf-8")
    for heading in (
        "CODER AGREEMENT", "JUDGE SIDING", "SPEND BY ROLE AND TASK", "LATENCY",
    ):
        assert heading in text
    stats = read_json(offline_run / "stats.json")
    assert set(stats["run_metrics"]) == {
        "schema", "coder_agreement", "judge_siding", "latency", "spend",
    }


def test_a_run_written_before_the_statistics_existed_still_gets_them(
    offline_run: Path, tmp_path: Path
) -> None:
    old = tmp_path / "old"
    old.mkdir()
    for name in (RUN_JSON_NAME, "gaf.sqlite"):
        (old / name).write_bytes((offline_run / name).read_bytes())
    document = read_json(old / RUN_JSON_NAME)
    del document["result"]["stats"]["run_metrics"]
    (old / RUN_JSON_NAME).write_text(json.dumps(document), encoding="utf-8")
    assert RunArtefact.from_json(read_json(old / RUN_JSON_NAME)).stats.run_metrics == {}
    assert "CODER AGREEMENT" not in render_run_report(
        RunArtefact.from_json(read_json(old / RUN_JSON_NAME))
    )

    assert run_cli("report", "--run", str(old)) == EXIT_OK
    assert "CODER AGREEMENT" in (old / "report.txt").read_text(encoding="utf-8")
    recomputed = read_json(old / "run_metrics.json")
    assert recomputed == read_json(offline_run / "stats.json")["run_metrics"]


def test_report_recomputes_spend_a_later_command_added_to_the_ledger(
    offline_run: Path, tmp_path: Path
) -> None:
    run = tmp_path / "later"
    run.mkdir()
    for name in (RUN_JSON_NAME, "gaf.sqlite"):
        (run / name).write_bytes((offline_run / name).read_bytes())
    with Blackboard(run / "gaf.sqlite") as board:
        board.write_llm_call(
            LLMResult(
                data={}, task=TaskType.REFACTOR, provider="p", model="m", prompt_version="v",
                cost_usd=0.75,
            ),
            run_id="offline", role="refactorer", subject="checkpoint",
        )
    assert run_cli("report", "--run", str(run)) == EXIT_OK
    assert read_json(run / "run_metrics.json")["spend"]["cost_usd"] == pytest.approx(0.75)


def test_the_run_statistics_carry_no_respondent_text(offline_run: Path) -> None:
    blob = json.dumps(read_json(offline_run / "stats.json")["run_metrics"])
    for response in synthetic_corpus():
        assert response.content[:40] not in blob
    # No judge reasoning either: it paraphrases the response.
    assert "reasoning" not in blob


def test_the_siding_block_states_that_coder_b_cannot_be_backed_alone() -> None:
    basis = judge_siding([])["basis"]
    assert "cannot back coder B alone" in basis and "self-preference or position bias" in basis


def test_a_halted_run_report_leads_with_the_stop() -> None:
    result, _, _ = run_capped(2.0)
    artefact = RunArtefact.from_result(result, config=config_for("capped"))
    text = render_run_report(artefact)
    assert text.index("STOPPED EARLY") < text.index("PROVENANCE")
    assert "HALTED at response" in text


def test_a_version_one_database_is_migrated_in_place_and_stays_readable(
    tmp_path: Path,
) -> None:
    """`llm_calls.stop_reason` is additive: an older store gains it, and loses nothing."""
    from gaf.store.schema import SCHEMA_SQL, SCHEMA_VERSION

    old_ddl = SCHEMA_SQL.replace(
        ",\n    stop_reason    TEXT                 -- NULL unless the model stopped early: "
        "'refusal', 'max_tokens'",
        "",
    )
    assert "stop_reason" not in old_ddl, "the fixture must really be the old shape"
    database = tmp_path / "old.sqlite"
    connection = sqlite3.connect(database)
    connection.executescript(old_ddl)
    connection.execute("INSERT INTO meta(key, value) VALUES('schema_version', '1')")
    connection.execute(
        "INSERT INTO runs(run_id, created_at, gaf_version, offline, config_json) "
        "VALUES('legacy', 't', '0', 1, '{}')"
    )
    connection.execute(
        "INSERT INTO llm_calls(call_id, run_id, role, task, provider, model, prompt_version, "
        "cost_usd, created_at) VALUES('c1', 'legacy', 'judge', 'judge_fit', 'p', 'm', 'v', "
        "0.5, 't')"
    )
    connection.commit()
    connection.close()

    with Blackboard(database) as board:
        old = board.read_llm_calls("legacy")
        assert [(c.call_id, c.cost_usd, c.stop_reason) for c in old] == [("c1", 0.5, None)]
        board.write_llm_call(
            LLMResult(
                data={"_stop_reason": "refusal"}, task=TaskType.JUDGE_FIT, provider="p",
                model="m", prompt_version="v", fail_safe=True,
            ),
            run_id="legacy", role="judge", subject="response:1",
        )
        board.write_llm_call(
            LLMResult(data={}, task=TaskType.JUDGE_FIT, provider="p", model="m", prompt_version="v"),
            run_id="legacy", role="judge", subject="response:2",
        )
        assert board.llm_stop_reasons("legacy") == {"refusal": 1}
        assert board.llm_usage("legacy")[0]["stopped_early"] == 1
        metrics = compute_run_metrics(board, "legacy", offline=True)
    assert metrics["spend"]["stop_reasons"] == {"refusal": 1}
    assert metrics["spend"]["stopped_early"] == 1
    assert metrics["coder_agreement"]["comparisons"] == 0
    with Blackboard(database) as board:  # opening it again is a no-op, not a second ALTER
        assert board.conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()[0] == str(SCHEMA_VERSION)


def test_a_normal_reply_records_no_stop_reason() -> None:
    reply = LLMResult(
        data={"candidates": []}, task=TaskType.CODE, provider="p", model="m", prompt_version="v"
    )
    assert reply.stop_reason is None
    stopped = replace(reply, data={"_stop_reason": "max_tokens", "_stop_category": "x"})
    assert stopped.stop_reason == "max_tokens"


# --------------------------------------------------------------------------- #
# --thresholds (ADR-0054)
# --------------------------------------------------------------------------- #


def _rules_from_thresholds_file(path: Path | None) -> Any:
    import argparse

    from gaf.cli._common import _config_from_args

    args = argparse.Namespace(thresholds=None if path is None else str(path))
    return _config_from_args(args, run_id="t", output_dir=Path(".")).rules


def test_a_thresholds_file_moves_only_the_thresholds_it_names(tmp_path: Path) -> None:
    from gaf.config import CodingRules

    file = tmp_path / "t.json"
    file.write_text(json.dumps({"tau_fit": 0.9, "tau_low": 0.85}), encoding="utf-8")
    rules = _rules_from_thresholds_file(file)
    assert (rules.tau_fit, rules.tau_low) == (0.9, 0.85)
    assert rules.tau_high == CodingRules().tau_high


def test_without_the_flag_the_defaults_stand() -> None:
    from gaf.config import CodingRules

    assert _rules_from_thresholds_file(None) == CodingRules()


@pytest.mark.parametrize(
    "body", ['{"tau_x": 0.5}', '{"tau_fit": 1.5}', '{"tau_fit": true}', "[]", "{}", "not json"]
)
def test_a_bad_thresholds_file_is_refused(tmp_path: Path, body: str) -> None:
    from gaf.cli._common import CliError

    file = tmp_path / "t.json"
    file.write_text(body, encoding="utf-8")
    with pytest.raises(CliError):
        _rules_from_thresholds_file(file)
