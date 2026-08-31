"""Synthetic response corpus — the only corpus tests and CI are allowed to touch.

Fourteen **invented** responses about AI in 2050, on ids in the 200s so that they can
never be confused with, or collide with, a real sample.

These were rewritten from scratch after an independent review found that an earlier
version of this file reproduced verbatim runs of up to 72 characters from real survey
responses, and reused nine of the real sample's response ids. That happened because the
first version was written immediately after profiling the real data and drew on its
phrasing. The current text is deliberately built from different scenarios and different
vocabulary, and a test asserts that no run of 30 characters or more matches any real
response. See ADR-0024.

Planted material, all documented so a reader knows why an odd sentence exists:

* ``FABRICATED_QUOTE`` — a string that occurs in no response, for S2.
* ``MOCKFIT_UNNECESSARY`` — the sentinel the mock judge answers UNNECESSARY to, in
  response 231, so M3's evidence-removal path can be exercised offline.
* Response 212 carries three short consecutive sentences, for the S2b multi-sentence
  quote check.
* Response 217 carries one distinctive sentence that three candidates all quote, for
  the S4 segment-discipline check.
* Response 244 carries curly quotes and an em dash, so normalisation is exercised.
* Response 203 is deliberately short (28 words) and response 218 deliberately carries no
  sentence terminator at all, mirroring two properties of real survey data without
  reproducing any of it.

Validation principle: **reliability** — the offline suite must be able to reproduce
every check outcome without a key, a network or a real respondent.
"""

from __future__ import annotations

from gaf.config import QUESTION_V2
from gaf.models import Response

__all__ = [
    "FABRICATED_QUOTE",
    "MOCKFIT_UNNECESSARY",
    "RAW_RESPONSES",
    "S2B_THREE_SENTENCES",
    "S4_SHARED_SENTENCE",
    "SOURCE",
    "corpus_by_id",
    "response_ids",
    "synthetic_corpus",
]

SOURCE = "synthetic"

#: Occurs in no response. A candidate citing it must fail S2 provenance.
FABRICATED_QUOTE = "artificial intelligence will abolish the concept of Tuesday"

#: The mock judge rules UNNECESSARY on any quote containing this token (M3).
MOCKFIT_UNNECESSARY = "MOCKFIT_UNNECESSARY"

#: Quoted verbatim by three candidates in the S4 fixture.
S4_SHARED_SENTENCE = "Municipal water boards will lean on forecasting engines by then."

#: Three consecutive sentences; quoting all three trips the S2b phrase/sentence rule.
S2B_THREE_SENTENCES = (
    "Recommendation engines already shape my evenings. They pick the music and the news. "
    "By 2050 that reach will be wider still."
)

RAW_RESPONSES: tuple[tuple[int, str], ...] = (
    (
        203,
        "Rural clinics get diagnostic support and the nearest specialist stops being four "
        "hours away. Clerical posts in the district office vanish quietly, and no retraining "
        "scheme arrives.",
    ),
    (
        207,
        "My worry is the ladder disappearing. Firms will hand ticket triage and first-draft "
        "paperwork to software, and those were the posts a graduate used to start in. "
        "Maintaining the systems becomes the new entry point, but it demands qualifications "
        "most school leavers in my district never had the chance to earn.",
    ),
    (
        212,
        "Recommendation engines already shape my evenings. They pick the music and the news. "
        "By 2050 that reach will be wider still. Picture one municipal system balancing "
        "traffic lights, reservoir levels and the power grid, adjusting itself hourly from "
        "whatever the sensors report.",
    ),
    (
        217,
        "Municipal water boards will lean on forecasting engines by then. Rainfall models will "
        "set release schedules for the reservoirs, and the engineers will spend their days "
        "arguing with the forecast rather than reading gauges, which strikes me as a real "
        "improvement in how that work is done.",
    ),
    (
        218,
        "the thing people forget is that these systems only know what we bothered to record "
        "so a district that never digitised its land registry gets worse answers than one "
        "that did and nobody notices because the output looks equally confident either way "
        "which is why I keep saying the record-keeping matters more than the algorithm",
    ),
    (
        221,
        "By 2050 I expect an assistant that drafts my correspondence, books the appointments "
        "and tells me what was decided in a meeting I missed. Whether that leaves me freer "
        "or merely busier depends on who sets the targets, and nobody is asking that yet.",
    ),
    (
        226,
        "Teaching changes most, I think. A tutor that never tires, adjusting to one child's "
        "pace, would reach pupils our classrooms lose by year three. The risk is that we "
        "then stop funding the teachers who notice why a child stopped trying.",
    ),
    (
        231,
        "Elderly relatives living alone will have something watching for a fall and calling a "
        f"doctor unprompted. {MOCKFIT_UNNECESSARY} It will track the medicine cabinet and "
        "nag them about the tablets they skip. My grandmother would have hated it and would "
        "have been safer for it.",
    ),
    (
        234,
        "Freight is where I notice it first. Containers routed by a system that knows the "
        "weather three ports ahead, drivers dispatched to the yard the moment a lorry is "
        "free. The port employs fewer people and moves twice the tonnage.",
    ),
    (
        239,
        "Packing and sorting went to machines in my mother's factory years ago. By 2050 the "
        "whole line runs without a shift supervisor. Those households had one wage between "
        "four people, and I have not heard a single proposal for what replaces it.",
    ),
    (
        244,
        "I am hopeful — these tools will help us with problems too large to hold in one head, "
        "like drought planning and drug discovery. People say “the machines will decide for "
        "us” and I don’t accept that. A tool has an owner, and the question is who.",
    ),
    (
        245,
        "Everything arrives pre-sorted for you: the news, the shopping, the course you are "
        "advised to take, the treatment you are offered. It is convenient right up to the "
        "moment you want something the profile did not predict, and then you discover how "
        "narrow the door has become.",
    ),
    (
        253,
        "We will forget how to do it ourselves. If the scheduling system is down for a week, "
        "nobody in the depot will remember how the rota used to be built. That dependence "
        "worries me more than any job losses.",
    ),
    (
        258,
        "Whole categories of work nobody has named yet will exist by then, the way nobody "
        "could have described a data-centre technician in 1975. Quality of life improves on "
        "average. It is the twenty years of transition that will be ugly, and averages hide "
        "exactly that.",
    ),
)



def synthetic_corpus(question: str = QUESTION_V2, source: str = SOURCE) -> list[Response]:
    """The full synthetic corpus, in id order."""
    return [
        Response(id=rid, question=question, content=content, source=source, meta={})
        for rid, content in RAW_RESPONSES
    ]


def corpus_by_id(question: str = QUESTION_V2, source: str = SOURCE) -> dict[int, Response]:
    return {r.id: r for r in synthetic_corpus(question=question, source=source)}


def response_ids() -> list[int]:
    return [rid for rid, _ in RAW_RESPONSES]
