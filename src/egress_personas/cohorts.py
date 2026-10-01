"""Comparing buildings: the base against each cohort, over several seeds.

A cohort is a question — *does a building of older residents fail on the stairs, or
before anybody reaches them?* — expressed as a set of demographic targets. Comparing
them answers only half of it: what changes in the population before an evacuation is
simulated. The other half needs the simulation, and saying so is not a disclaimer, it
is the division of labour this project is built on.

What a comparison is good for is seeing which cohorts move which drivers, and by how
much relative to seed-to-seed noise. A difference smaller than the spread across seeds
is not a difference.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any

from .distributions import egress_drivers
from .households import cohort_ids
from .sample import Population, sample
from .tables import Tables, as_bool, text

BASE = "(base)"


@dataclass
class Column:
    """One building, measured over several seeds."""

    cohort: str
    name: str
    question: str
    include_cases: bool
    runs: list[Population] = field(default_factory=list)
    drivers: dict[str, list[float]] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    normed: dict[str, list[float]] = field(default_factory=dict)

    def mean(self, key: str, which: str = "raw") -> float | None:
        src = self.normed if which == "norm" else self.drivers
        vals = [v for v in src.get(key, []) if v is not None]
        return statistics.fmean(vals) if vals else None

    def spread(self, key: str, which: str = "raw") -> float | None:
        src = self.normed if which == "norm" else self.drivers
        vals = [v for v in src.get(key, []) if v is not None]
        return statistics.stdev(vals) if len(vals) > 1 else 0.0


def build(tables: Tables, scenario_id: str, *, seeds: list[int],
          which: list[str] | None = None,
          include_base: bool = True) -> list[Column]:
    """Sample every cohort over every seed."""
    names = which if which is not None else cohort_ids(tables)
    meta = {}
    for row in (tables.get("cohorts") or []):
        meta[text(row.get("cohort_id"))] = row

    columns: list[Column] = []
    todo = ([None] if include_base else []) + [c for c in names if c]
    for cohort in todo:
        row = meta.get(cohort or "", {}) or {}
        inc = as_bool(row.get("include_cases"))
        col = Column(
            cohort=cohort or "",
            name=(text(row.get("name")) if cohort else BASE) or (cohort or BASE),
            question=text(row.get("question")) or "",
            include_cases=True if inc is None else inc,
        )
        for seed in seeds:
            pop = sample(tables, scenario_id, seed, cohort=cohort)
            col.runs.append(pop)
            for d in egress_drivers(pop):
                col.drivers.setdefault(d["key"], []).append(d["raw"])
                col.normed.setdefault(d["key"], []).append(d.get("norm"))
        columns.append(col)
    return columns


def rows_of(columns: list[Column]) -> list[dict[str, Any]]:
    """The driver rows, in the order one population reports them."""
    if not columns or not columns[0].runs:
        return []
    return [{"key": d["key"], "phase": d["phase"], "what": d["what"],
             "unit": d["unit"], "norm_unit": d.get("norm_unit", d["unit"]),
             "why": d["why"]}
            for d in egress_drivers(columns[0].runs[0])]


def _fmt(value: float | None, unit: str) -> str:
    if value is None:
        return "—"
    if unit == "share":
        return f"{value:.0%}"
    if unit in ("m/s", "0–1"):
        return f"{value:.2f}"
    if unit == "minutes":
        return f"{value:.0f}"
    return f"{value:.1f}" if abs(value - round(value)) > 0.05 else f"{round(value):d}"


#: Beyond this, a fold change is reported as a bound rather than a number.
FOLD_CAP = 20.0


def _fold(a: float, b: float, noise: float) -> tuple[float, str]:
    """How many times apart two figures are, symmetrically, with a floor.

    A halving and a doubling are the same size of move, so the measure is
    `max(a/b, b/a)` rather than `b/a`. And a value below its own seed-to-seed spread
    is indistinguishable from zero, so dividing by it would manufacture a huge number
    out of noise: those are capped and marked.
    """
    lo, hi = sorted((abs(a), abs(b)))
    floor = max(noise, hi / FOLD_CAP, 1e-9)
    if lo < floor:
        return hi / floor, "≥"
    return hi / lo, ""


def markdown(columns: list[Column], scenario_id: str, seeds: list[int]) -> str:
    # Read the occupancy spread off the buildings themselves, so the sentence that
    # explains why counts are normalised cannot go stale when a cohort changes.
    occ = [c.runs[0].targets.persons_per_flat for c in columns if c.runs]
    _occ_lo, _occ_hi = (min(occ), max(occ)) if occ else (0.0, 0.0)

    L: list[str] = [
        f"# Buildings compared — {scenario_id}, {len(seeds)} seed"
        f"{'s' if len(seeds) != 1 else ''}",
        "",
        "Each column is a building the Sheet describes: a set of demographic targets "
        "with a question attached. Figures are means over "
        f"{len(seeds)} seeds, with the spread across those seeds in brackets — a "
        "difference smaller than the spread is not a difference.",
        "",
        "**Read this as arithmetic, not as evidence.** Every cohort target is "
        "`basis = team`: somebody chose it to ask a question, and no census or paper "
        "says a building looks like that. What the table shows is the consequence of "
        "those choices propagated through the model's own rules — including "
        "consequences nobody typed, which is the part worth looking at. It is not a "
        "finding about real buildings.",
        "",
        "**These are inputs to RSET, not RSET.** Nothing here simulates an evacuation.",
        "",
        f"Counts are shown per 100 residents, with the raw count in brackets. "
        f"Occupancy across these buildings runs from {_occ_lo:g} to {_occ_hi:g} people "
        f"a flat, so an unscaled count rising would mostly mean the building got "
        f"fuller rather than that anybody behaved differently.",
        "",
    ]

    L += ["## The questions", ""]
    for c in columns:
        if c.cohort:
            L.append(f"- **{c.name}** (`{c.cohort}`) — {c.question or 'no question recorded'}")
        else:
            L.append(f"- **{c.name}** — the building as the census and the literature "
                     f"describe it, with the hand-authored cases in it.")
    L.append("")

    head = ["driver", "unit"] + [c.name for c in columns]
    L += ["## Drivers", "", "| " + " | ".join(head) + " |",
          "|" + "|".join(["---"] * len(head)) + "|"]
    phase = None
    for r in rows_of(columns):
        if r["phase"] != phase:
            phase = r["phase"]
            tag = {"TTS": "**Before anybody moves (TTS)**",
                   "TTE": "**Getting out (TTE)**"}.get(phase, "**The building**")
            L.append(f"| {tag} |" + " |" * (len(head) - 1))
        counted = r["unit"] == "people" and r["key"] != "present"
        cells = []
        for c in columns:
            m = c.mean(r["key"], "norm" if counted else "raw")
            sd = c.spread(r["key"], "norm" if counted else "raw")
            unit = r["norm_unit"] if counted else r["unit"]
            cell = _fmt(m, unit)
            if sd and m is not None and sd > 0:
                cell += f" <sub>±{_fmt(sd, unit).lstrip('±')}</sub>"
            if counted:
                cell += f" <sub>({_fmt(c.mean(r['key']), 'people')})</sub>"
            cells.append(cell)
        unit_col = r["norm_unit"] if counted else r["unit"]
        L.append(f"| {r['what']} | {unit_col} | " + " | ".join(cells) + " |")
    L.append("")

    L += ["## What moved most", ""]
    base = columns[0]
    moved: list[tuple[float, str, str, str]] = []
    for r in rows_of(columns):
        counted = r["unit"] == "people" and r["key"] != "present"
        which = "norm" if counted else "raw"
        unit = r["norm_unit"] if counted else r["unit"]
        b = base.mean(r["key"], which)
        if b is None or b == 0:
            continue
        for c in columns[1:]:
            v = c.mean(r["key"], which)
            if v is None:
                continue
            fold, mark = _fold(b, v, max(base.spread(r["key"], which) or 0.0,
                                         c.spread(r["key"], which) or 0.0))
            arrow = "↑" if v > b else ("↓" if v < b else "")
            moved.append((fold, c.name, r["what"],
                          f"{_fmt(b, unit)} → {_fmt(v, unit)}",
                          f"{mark}×{fold:.1f} {arrow}".strip()))
    moved.sort(reverse=True)
    if moved:
        L += ["Ranked by **fold change** in the comparable figure — counts per 100 "
              "residents, means as they are — so a building being fuller does not get "
              "mistaken for its residents behaving differently, and a halving counts as "
              "the same size of move as a doubling.", "",
              "A change to or from nearly nothing is shown as a bound (`≥`), because "
              "dividing by a quantity smaller than its own seed-to-seed spread does not "
              "mean anything.", "",
              "A large change here means the targets were set far apart, nothing more. "
              "Whether it matters is a question for the simulation, and which of the "
              "underlying parameters deserve the weight is a question for a sensitivity "
              "run. Neither has been done.", "",
              "| building | driver | base → cohort | fold |",
              "|---|---|---|---|"]
        for _fold_v, name, what, delta, shown in moved[:16]:
            L.append(f"| {name} | {what} | {delta} | {shown} |")
        L.append("")

    warn = [(c.name, w) for c in columns for pop in c.runs for w in pop.warnings]
    seen: set[tuple[str, str]] = set()
    unique = [(n, w) for n, w in warn if not ((n, w) in seen or seen.add((n, w)))]
    if unique:
        L += ["## What the cohorts strained", "",
              "A cohort can ask for a building the plan or the arithmetic cannot "
              "provide. Those are findings, not faults — and they are the reason the "
              "targets are stated rather than assumed.", ""]
        for name, w in unique[:20]:
            L.append(f"- **{name}**: {w}")
        L.append("")

    gaps = [(c.name, g) for c in columns for pop in c.runs for g in pop.gaps]
    if gaps:
        agg: dict[tuple[str, str], list[int]] = {}
        for name, g in gaps:
            agg.setdefault((name, g["what"]), []).append(g["count"])
        L += ["## Gaps left open", "", "| building | gap | per run |", "|---|---|---|"]
        for (name, what), counts in agg.items():
            L.append(f"| {name} | {what} | {statistics.fmean(counts):.1f} |")
        L.append("")

    L += ["## Reading this honestly", "",
          "- A cohort is a **question**, not a measurement. The base building's targets "
          "come from the census and the literature; a cohort's come from the team, and "
          "its rows say `basis = team` for exactly that reason.",
          "- Most of what you see here is the arithmetic you set up. If you halve a "
          "cohort's mean tenure and the parameter rows assign familiarity by tenure "
          "band, mean familiarity falls — that is a weighted average, not a result. The "
          "rows worth a second look are the ones where a consequence appears in a "
          "quantity the cohort never named.",
          "- Mobility is conditioned on age, so a cohort that only moves the age "
          "distribution still moves the walking-difficulty share. That is the model "
          "working, not a second assumption.",
          "- Nothing here is an evacuation time. Feeding these populations to the "
          "simulation is what turns a difference in drivers into a difference in "
          "outcome, and the size of that step is the open question.",
          ""]
    return "\n".join(L)
