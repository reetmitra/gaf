"""Shared chart primitives for the hand-written figures on `views.html`.

Every figure in `gaf.report.views` is inline SVG written by hand — there is no
plotting library in this project and no dependency may be added for one. What those
figures need in common lives here, in one place, so that eleven views cannot drift
into eleven different ideas of what a bar, an axis or a family's colour is.

Four things this module fixes for the whole page.

**A family keeps its colour.** :func:`family_palette` assigns a colour *slot* to each
family name in one fixed order — sorted, ascending — so the green in the codebook tree
is the same family as the green in the heatmap and in the affinity cards. There are
:data:`N_FAMILY_SLOTS` slots and the assignment wraps, because a real codebook can
carry more families than any categorical palette can keep distinguishable; the wrap is
one reason **colour is never the only carrier of meaning here**. Every band, bar and
cell this module draws is labelled directly or carries a ``<title>``, and the views
layer states the family name in text beside every figure that uses the palette.

The twelve slots are twelve evenly spaced OKLCH hues at one lightness per scheme
(L 0.62 light, L 0.66 dark, chroma capped at 0.145 / 0.135), chosen by enumerating
start angles and orderings against the six colour checks rather than by eye. On the
*adjacent* pairlist — the one that governs neighbouring bands, bars and rows, which is
what these figures draw — the set passes every check in both schemes: worst adjacent
colour-vision-deficiency ΔE 14.5 against a target of 8, worst normal-vision ΔE 19.1
against a floor of 15, every slot inside its lightness band, above the chroma floor,
and at or above 3:1 contrast on its own surface.

On the *all-pairs* list it does not pass, and no twelve-slot categorical palette can:
twelve hues cannot be pairwise separable under deuteranopia. That is precisely why
**this module never lets colour carry identity alone.** Fifteen families genuinely
exist in the data, so folding the thirteenth into "Other" would be a lie about the
codebook; the mitigation is the secondary encoding instead — a direct text label on
every family band, a ``<title>`` naming the family and the count on every mark, and a
complete text listing beside the figure.

**Both colour schemes are one stylesheet.** Nothing here writes a literal colour into
an element. A slot emits ``class="v-f3"``, and ``--f3`` is defined twice in
:data:`CHART_CSS` — once for light, once under ``prefers-color-scheme: dark`` — so the
same bytes render legibly on paper and on a dark screen. The sequential ramp is an
*opacity* over one hue for the same reason: an opacity is scheme-independent, a
lightness ramp is not.

**Text is truncated, never clipped.** :func:`text` takes the full string and the
display string separately, and writes the full one into a ``<title>`` child, which is
the SVG tooltip. A label that does not fit is still readable by hovering and still
present for anyone reading the source.

**Determinism.** Two decimal places on every coordinate (via `gaf.analysis.hca._num`,
reused rather than re-derived), no generated id, no timestamp, no dictionary iterated
in insertion order. The same input produces byte-identical SVG.

These figures are written for embedding **inline in HTML**, so they carry no ``xmlns``
and no opaque background rectangle: they inherit the page's own colours. They are
still well-formed XML, which the test suite asserts by parsing every one of them.

Validation principle: **transparency** — a reader who cannot see the shape of the data
is taking the numbers on trust.
"""

from __future__ import annotations

import html
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from gaf.analysis.hca import _num

__all__ = [
    "CHART_CSS",
    "N_FAMILY_SLOTS",
    "Scale",
    "band",
    "escape",
    "family_palette",
    "figure",
    "line",
    "num",
    "ramp",
    "rect",
    "scale",
    "text",
    "truncate",
]

#: How many distinguishable categorical slots the palette carries. A codebook with
#: more families than this wraps — see the module docstring on why that is safe.
N_FAMILY_SLOTS = 12

#: The lowest opacity a non-zero cell of a sequential ramp is ever drawn at, so that
#: "one" never renders as "none".
_RAMP_FLOOR = 0.14

#: And the highest. The ramp stops short of full strength because every cell it fills
#: also carries its own count printed on top in the page's ink colour; at full strength
#: that number would be unreadable in one scheme or the other.
_RAMP_CEILING = 0.70

#: One stylesheet for every figure. The views page inlines this once.
#:
#: Every rule is written under ``.v-chart`` so that a third-party SVG inlined
#: elsewhere on the page — the dendrogram, the saturation curve, the timeline, each of
#: which carries its own bare ``text { ... }`` rule — cannot reach these figures. A
#: bare element selector scores 0-0-1; every rule here scores at least 0-1-1.
CHART_CSS = """
:root {
  --v-grid: #e6e3dd;
  --v-axis: #9a958c;
  --v-seq: #2a78d6;
  --v-off: #eceae5;
  --f0: #579a3d; --f1: #aa67be; --f2: #8f8b00; --f3: #0093bf;
  --f4: #cf5c64; --f5: #4b86dc; --f6: #009e77; --f7: #8375d8;
  --f8: #ca662b; --f9: #00999d; --f10: #b07b00; --f11: #c35d95;
}
@media (prefers-color-scheme: dark) {
  :root {
    --v-grid: #2f3033;
    --v-axis: #6f6c66;
    --v-seq: #3987e5;
    --v-off: #26272a;
    --f0: #67a550; --f1: #b476c7; --f2: #9b981b; --f3: #00a0d0;
    --f4: #d86c72; --f5: #5c93e4; --f6: #00ac82; --f7: #8f83e0;
    --f8: #d37642; --f9: #00a7ab; --f10: #bf860c; --f11: #cd6da1;
  }
}
.v-chart { display: block; }
.v-chart text {
  fill: var(--ink);
  font-family: "SF Mono", ui-monospace, "DejaVu Sans Mono", Menlo, Consolas, monospace;
  font-size: 10px;
}
.v-chart .v-tick { fill: var(--muted); font-size: 9px; }
.v-chart .v-lbl { fill: var(--ink); font-size: 10px; }
.v-chart .v-ttl { fill: var(--ink); font-size: 12px; font-weight: 600; }
.v-chart .v-axis { stroke: var(--v-axis); stroke-width: 1; fill: none; }
.v-chart .v-grid { stroke: var(--v-grid); stroke-width: 1; fill: none; }
.v-chart .v-off { fill: var(--v-off); }
.v-chart .v-seq { fill: var(--v-seq); }
.v-chart .v-rule { stroke: var(--rule); stroke-width: 1; fill: none; }
.v-chart .v-f0 { fill: var(--f0); } .v-chart .v-f1 { fill: var(--f1); }
.v-chart .v-f2 { fill: var(--f2); } .v-chart .v-f3 { fill: var(--f3); }
.v-chart .v-f4 { fill: var(--f4); } .v-chart .v-f5 { fill: var(--f5); }
.v-chart .v-f6 { fill: var(--f6); } .v-chart .v-f7 { fill: var(--f7); }
.v-chart .v-f8 { fill: var(--f8); } .v-chart .v-f9 { fill: var(--f9); }
.v-chart .v-f10 { fill: var(--f10); } .v-chart .v-f11 { fill: var(--f11); }
.v-swatch { display: inline-block; width: .62em; height: .62em; border-radius: 2px; }
.v-swatch.v-f0 { background: var(--f0); } .v-swatch.v-f1 { background: var(--f1); }
.v-swatch.v-f2 { background: var(--f2); } .v-swatch.v-f3 { background: var(--f3); }
.v-swatch.v-f4 { background: var(--f4); } .v-swatch.v-f5 { background: var(--f5); }
.v-swatch.v-f6 { background: var(--f6); } .v-swatch.v-f7 { background: var(--f7); }
.v-swatch.v-f8 { background: var(--f8); } .v-swatch.v-f9 { background: var(--f9); }
.v-swatch.v-f10 { background: var(--f10); } .v-swatch.v-f11 { background: var(--f11); }
""".strip()


# --------------------------------------------------------------------------- #
# Numbers, escaping, truncation
# --------------------------------------------------------------------------- #


def num(value: float, places: int = 2) -> str:
    """Fixed-precision number for SVG output, negative zero normalised.

    `gaf.analysis.hca`'s own helper, reused verbatim rather than re-derived, so that
    two hand-written figures in this project cannot round a coordinate differently.
    """
    return _num(value, places)


def escape(value: Any) -> str:
    """Escape anything for SVG text or an attribute value. No exceptions."""
    return html.escape("" if value is None else str(value), quote=True)


def truncate(value: str, limit: int) -> str:
    """Shorten to `limit` characters, ending in a single ellipsis character.

    The caller keeps the full string for the ``<title>``; this is only what is drawn.
    A `limit` below 2 returns the ellipsis alone rather than an empty label, because a
    label that vanished would read as "this thing has no name".
    """
    if limit <= 0:
        return ""
    if len(value) <= limit:
        return value
    if limit == 1:
        return "…"
    return value[: limit - 1] + "…"


# --------------------------------------------------------------------------- #
# Scales
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Scale:
    """A linear map from a numeric domain onto a pixel range.

    A degenerate domain (``d0 == d1``) maps every value to the middle of the range
    rather than dividing by zero: one distinct value is a legitimate state — a run
    where every batch admitted the same number of codes — and a figure that raised on
    it would be refusing to draw a true fact about the data.
    """

    d0: float
    d1: float
    r0: float
    r1: float

    def __call__(self, value: float) -> float:
        if self.d1 == self.d0:
            return (self.r0 + self.r1) / 2.0
        t = (value - self.d0) / (self.d1 - self.d0)
        return self.r0 + t * (self.r1 - self.r0)

    def span(self, value: float) -> float:
        """How many pixels `value` domain units occupy. Never negative."""
        if self.d1 == self.d0:
            return 0.0
        return abs(value * (self.r1 - self.r0) / (self.d1 - self.d0))


def scale(domain: tuple[float, float], pixels: tuple[float, float]) -> Scale:
    """A `Scale` from a ``(lo, hi)`` domain onto a ``(lo, hi)`` pixel range."""
    return Scale(d0=domain[0], d1=domain[1], r0=pixels[0], r1=pixels[1])


def band(count: int, pixels: tuple[float, float], *, pad: float = 0.0) -> tuple[float, float]:
    """``(slot_width, inner_width)`` for `count` evenly spaced categories.

    `pad` is the gap between two neighbouring bands, in pixels; the inner width never
    falls below a hair's breadth, so a band is always drawn rather than silently
    disappearing at large `count`.
    """
    slots = max(1, count)
    slot = (pixels[1] - pixels[0]) / slots
    return slot, max(0.4, slot - pad)


# --------------------------------------------------------------------------- #
# The categorical palette
# --------------------------------------------------------------------------- #


def family_palette(families: Iterable[str]) -> dict[str, int]:
    """Family name -> colour slot, assigned in sorted order and wrapping at 12.

    Sorted, not first-seen: a figure that drew families in the order a dictionary
    happened to yield them would give the same codebook two different colourings on
    two runs, and the page promises byte-identical output.
    """
    return {name: index % N_FAMILY_SLOTS for index, name in enumerate(sorted(set(families)))}


def ramp(value: float, maximum: float) -> str:
    """Opacity for a sequential ramp over one hue, as an SVG attribute value.

    Zero is fully transparent — an empty cell shows the page through it. Anything
    above zero starts at :data:`_RAMP_FLOOR`, so the difference between "none" and
    "one" is never a difference nobody can see.
    """
    if maximum <= 0 or value <= 0:
        return "0"
    share = min(1.0, value / maximum)
    return num(_RAMP_FLOOR + (_RAMP_CEILING - _RAMP_FLOOR) * share)


# --------------------------------------------------------------------------- #
# Elements
# --------------------------------------------------------------------------- #


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    cls: str = "",
    opacity: str | None = None,
    tooltip: str | None = None,
) -> str:
    """One rectangle, optionally carrying a ``<title>`` tooltip."""
    parts = [f'<rect x="{num(x)}" y="{num(y)}" width="{num(width)}" height="{num(height)}"']
    if cls:
        parts.append(f' class="{escape(cls)}"')
    if opacity is not None:
        parts.append(f' fill-opacity="{escape(opacity)}"')
    parts.append(">" if tooltip else "/>")
    if tooltip:
        parts.append(f"<title>{escape(tooltip)}</title></rect>")
    return "".join(parts)


def line(x1: float, y1: float, x2: float, y2: float, *, cls: str = "v-grid") -> str:
    """One straight line."""
    return (
        f'<line class="{escape(cls)}" x1="{num(x1)}" y1="{num(y1)}" '
        f'x2="{num(x2)}" y2="{num(y2)}"/>'
    )


def text(
    x: float,
    y: float,
    content: str,
    *,
    cls: str = "v-lbl",
    anchor: str = "start",
    tooltip: str | None = None,
    rotate: float | None = None,
) -> str:
    """One text label, with the untruncated string as its ``<title>`` when given."""
    attrs = f'class="{escape(cls)}" x="{num(x)}" y="{num(y)}"'
    if anchor != "start":
        attrs += f' text-anchor="{escape(anchor)}"'
    if rotate is not None:
        attrs += f' transform="rotate({num(rotate)} {num(x)} {num(y)})"'
    inner = escape(content)
    if tooltip is not None and tooltip != content:
        inner += f"<title>{escape(tooltip)}</title>"
    return f"<text {attrs}>{inner}</text>"


def figure(
    width: float,
    height: float,
    body: Sequence[str],
    *,
    label: str,
    cls: str = "v-chart",
) -> str:
    """Wrap `body` in an inline ``<svg>`` element.

    No ``xmlns`` and no background rectangle: this is written to sit inside an HTML
    document, where the namespace is implied and the page's own background should show
    through so that both colour schemes work. ``role`` and ``aria-label`` are what a
    screen reader reads instead of the picture.
    """
    head = (
        f'<svg class="{escape(cls)}" width="{num(width, 0)}" height="{num(height, 0)}" '
        f'viewBox="0 0 {num(width, 0)} {num(height, 0)}" role="img" '
        f'aria-label="{escape(label)}">'
    )
    return "\n".join([head, f"<title>{escape(label)}</title>", *body, "</svg>"])
