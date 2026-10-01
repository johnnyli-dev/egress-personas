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

    def mean(self, key: str) -> float | None:
        vals = [v for v in self.drivers.get(key, []) if v is not None]
        return statistics.fmean(vals) if vals else None

    def spread(self, key: str) -> float | None:
        vals = [v for v in self.drivers.get(key, []) if v is not None]
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
        columns.append(col)
    return columns


def rows_of(columns: list[Column]) -> list[dict[str, Any]]:
    """The driver rows, in the order one population reports them."""
    if not columns or not columns[0].runs:
        return []
    return [{"key": d["key"], "phase": d["phase"], "what": d["what"],
             "unit": d["unit"], "why": d["why"]}
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


def markdown(columns: list[Column], scenario_id: str, seeds: list[int]) -> str:
    L: list[str] = [
        f"# Buildings compared — {scenario_id}, {len(seeds)} seed"
        f"{'s' if len(seeds) != 1 else ''}",
        "",
        "Each column is a building the Sheet describes: a set of demographic targets "
        "with a question attached. Figures are means over "
        f"{len(seeds)} seeds, with the spread across those seeds in brackets — a "
        "difference smaller than the spread is not a difference.",
        "",
        "**These are inputs to RSET, not RSET.** Nothing here simulates an evacuation. "
        "What the columns show is what changes in the population *before* the "
        "simulation runs, which is the half of the question this project owns.",
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
        cells = []
        for c in columns:
            m, sd = c.mean(r["key"]), c.spread(r["key"])
            cell = _fmt(m, r["unit"])
            if sd and m is not None and sd > 0:
                cell += f" <sub>±{_fmt(sd, r['unit']).lstrip('±')}</sub>"
            cells.append(cell)
        L.append(f"| {r['what']} | {r['unit']} | " + " | ".join(cells) + " |")
    L.append("")

    L += ["## What moved most", ""]
    base = columns[0]
    moved: list[tuple[float, str, str, str, str]] = []
    for r in rows_of(columns):
        b = base.mean(r["key"])
        if b is None:
            continue
        noise = max(base.spread(r["key"]) or 0.0, 1e-9)
        for c in columns[1:]:
            v = c.mean(r["key"])
            if v is None:
                continue
            z = abs(v - b) / noise
            moved.append((z, c.name, r["what"],
                          f"{_fmt(b, r['unit'])} → {_fmt(v, r['unit'])}", r["unit"]))
    moved.sort(reverse=True)
    if moved:
        L += ["Ranked by how large the change is against the seed-to-seed spread of the "
              "base building, so a big absolute move in a noisy quantity does not "
              "outrank a small move in a stable one.", "",
              "| building | driver | base → cohort | × the base spread |",
              "|---|---|---|---|"]
        for z, name, what, delta, _unit in moved[:16]:
            z_text = "—" if z > 1e6 else f"{z:.0f}×"
            L.append(f"| {name} | {what} | {delta} | {z_text} |")
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
          "- Mobility is conditioned on age, so a cohort that only moves the age "
          "distribution still moves the walking-difficulty share. That is the model "
          "working, not a second assumption.",
          "- Nothing here is an evacuation time. Feeding these populations to the "
          "simulation is what turns a difference in drivers into a difference in "
          "outcome, and the size of that step is the open question.",
          ""]
    return "\n".join(L)
