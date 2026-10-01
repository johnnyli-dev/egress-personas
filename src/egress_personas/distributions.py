"""The makeup of a building, and what that makeup will do to an evacuation.

Two kinds of thing here, kept apart on purpose.

**Distributions** are what the population *is*: ages, sexes, mobility, tenure,
household sizes, walking speeds, how many ties people have. A sampled population is
only as good as these look, and a crosstab catches things a marginal share hides — a
building can have the right number of over-65s and the wrong number of them living
alone.

**Egress drivers** are what the population will *do* to the numbers the research cares
about. They are inputs to RSET, not RSET: nothing here simulates an evacuation, and the
honest reading of a cohort comparison is "this is what changes before the simulation
runs". They are grouped by which half of the split they land on — TTS, the time before
anybody moves, or TTE, the time it then takes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .households import AGE_BANDS, TENURE_BANDS
from .sample import Population

#: Order the bands are reported in, so two reports line up column for column.
MOBILITY_ORDER = ("none", "ambulatory_difficulty", "walker_cane", "wheelchair")
TYPE_ORDER = ("adult", "child", "elderly", "wheelchair", "caregiver", "athletic",
              "visitor")
SEX_ORDER = ("female", "male", "other")


@dataclass
class Dist:
    """One distribution: counts by category, with the stats worth printing."""

    name: str
    unit: str
    counts: dict[str, int]
    total: int
    mean: float | None = None
    median: float | None = None
    p5: float | None = None
    p95: float | None = None
    low: float | None = None
    high: float | None = None

    @property
    def shares(self) -> dict[str, float]:
        n = self.total or 1
        return {k: v / n for k, v in self.counts.items()}


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = q * (len(xs) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def categorical(name: str, values: Iterable[Any], order: Iterable[str] = ()) -> Dist:
    vals = [v for v in values if v is not None]
    counts: dict[str, int] = {k: 0 for k in order}
    for v in vals:
        counts[str(v)] = counts.get(str(v), 0) + 1
    counts = {k: v for k, v in counts.items() if v or k in order}
    return Dist(name=name, unit="people", counts=counts, total=len(vals))


def numeric(name: str, unit: str, values: Iterable[float],
            edges: list[float]) -> Dist:
    vals = [float(v) for v in values if v is not None]
    counts: dict[str, int] = {}
    labels = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        labels.append(f"{lo:g}–{hi:g}")
        counts[labels[-1]] = 0
    for v in vals:
        for i in range(len(edges) - 1):
            if edges[i] <= v < edges[i + 1] or (i == len(edges) - 2 and v == edges[-1]):
                counts[labels[i]] += 1
                break
    return Dist(
        name=name, unit=unit, counts=counts, total=len(vals),
        mean=(sum(vals) / len(vals)) if vals else None,
        median=_quantile(vals, 0.5), p5=_quantile(vals, 0.05),
        p95=_quantile(vals, 0.95),
        low=min(vals) if vals else None, high=max(vals) if vals else None,
    )


def crosstab(rows: Iterable[Any], row_of: Callable[[Any], str],
             col_of: Callable[[Any], str], row_order: Iterable[str] = (),
             col_order: Iterable[str] = ()) -> dict[str, Any]:
    table: dict[str, dict[str, int]] = {}
    items = list(rows)
    for p in items:
        table.setdefault(row_of(p), {})
        table[row_of(p)][col_of(p)] = table[row_of(p)].get(col_of(p), 0) + 1
    r_keys = [k for k in row_order if k in table] + \
             [k for k in table if k not in set(row_order)]
    c_keys = list(col_order) or sorted({c for r in table.values() for c in r})
    return {
        "rows": r_keys,
        "cols": [c for c in c_keys if any(table[r].get(c) for r in r_keys)],
        "cells": {r: {c: table[r].get(c, 0) for c in c_keys} for r in r_keys},
        "row_totals": {r: sum(table[r].values()) for r in r_keys},
        "total": len(items),
    }


def distributions(pop: Population) -> dict[str, Dist]:
    """Every distribution worth looking at, keyed for a stable report order."""
    people = pop.people
    present = [p for p in people if p.situation.get("present")]
    return {
        "age": numeric("Age", "years", [p.identity["age_years"] for p in people],
                       [0, 18, 25, 35, 50, 65, 75, 101]),
        "age_band": categorical("Age band",
                                [p.identity["age_band"] for p in people],
                                AGE_BANDS),
        "sex": categorical("Sex", [p.identity["sex"] for p in people], SEX_ORDER),
        "mobility": categorical("Mobility", [p.body["mobility"] for p in people],
                                MOBILITY_ORDER),
        "agent_type": categorical("Occupant class",
                                  [p.body["sim_agent_type"] for p in people],
                                  TYPE_ORDER),
        "household_role": categorical(
            "Role in the flat", [p.identity.get("household_role") for p in people],
            ("head", "partner", "child", "parent", "carer", "lodger", "other")),
        "household_size": categorical(
            "Household size", [str(len(h.members)) for h in pop.households],
            ("1", "2", "3", "4", "5")),
        "tenure": numeric("Years in the building", "years",
                          [p.identity.get("tenure_years") or 0.0 for p in people],
                          [0, 1, 2, 5, 10, 20, 31]),
        "tenure_band": categorical(
            "Tenure band",
            [next((b for b, (lo, hi) in TENURE_BANDS.items()
                   if lo <= (p.identity.get("tenure_years") or 0) < hi), "5_plus")
             for p in people],
            TENURE_BANDS),
        "base_speed": numeric("Walking speed", "m/s",
                              [p.body.get("base_speed") for p in people],
                              [0.2, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0]),
        "familiarity": numeric("Knows the layout", "0–1",
                               [p.knowledge.get("floorplan_familiarity")
                                for p in people],
                               [0, 0.2, 0.4, 0.6, 0.8, 1.0]),
        "mill": numeric("Confers before acting", "0–1",
                        [p.dispositions.get("mill_tendency") for p in people],
                        [0, 0.2, 0.4, 0.6, 0.8, 1.0]),
        "ties": numeric("Connections each", "ties",
                        [float(len(p.ties)) for p in people],
                        [0, 1, 2, 4, 6, 9, 15]),
        "activity": categorical("What they are doing",
                                [p.situation.get("activity") for p in present]),
    }


def crosstabs(pop: Population) -> dict[str, dict[str, Any]]:
    people = pop.people
    return {
        "age_by_mobility": crosstab(
            people, lambda p: p.identity["age_band"],
            lambda p: p.body["mobility"], AGE_BANDS, MOBILITY_ORDER),
        "age_by_sex": crosstab(
            people, lambda p: p.identity["age_band"],
            lambda p: p.identity["sex"], AGE_BANDS, SEX_ORDER),
        "age_by_living_alone": crosstab(
            people, lambda p: p.identity["age_band"],
            lambda p: "alone" if p.household_index is None else "with others",
            AGE_BANDS, ("alone", "with others")),
        "mobility_by_help": crosstab(
            [p for p in people if p.body["mobility"] != "none"],
            lambda p: p.body["mobility"],
            lambda p: "has help in the flat" if p.body.get("escorted_by")
            else ("alone in the flat" if p.household_index is None
                  else "others in the flat"),
            MOBILITY_ORDER,
            ("has help in the flat", "others in the flat", "alone in the flat")),
    }


def egress_drivers(pop: Population) -> list[dict[str, Any]]:
    """What this population does to the inputs of RSET, split TTS from TTE.

    Not an evacuation result. Every row here is something the simulation reads; what it
    then does with them is the simulation's answer, not this one's.
    """
    people = pop.people
    present = [p for p in people if p.situation.get("present")]
    n = len(present) or 1
    speeds = [p.body.get("base_speed") for p in present
              if p.body.get("base_speed") is not None]
    gather = sum((c.get("delay_s") or 0.0) for p in present for c in p.commitments)
    no_second = sum(1 for p in present
                    if p.knowledge.get("knows_second_stair") is False)
    unheard = sum(1 for p in present if p.situation.get("alarm_audible") is False)
    isolated = sum(1 for p in present if not p.ties)
    asleep = sum(1 for p in present if p.situation.get("asleep"))
    stairless = [p for p in present if p.body.get("can_use_stairs") is False]
    unhelped = [p for p in stairless if not p.body.get("escorted_by")]
    slow = [p for p in present if p.body.get("limiting_condition")]
    mill = [p.dispositions.get("mill_tendency") for p in present
            if p.dispositions.get("mill_tendency") is not None]
    confirm = [p.dispositions.get("seeks_confirmation") for p in present
               if p.dispositions.get("seeks_confirmation") is not None]

    def row(phase: str, what: str, value: Any, unit: str, why: str,
            raw: float | None = None, key: str = "") -> dict[str, Any]:
        """One driver. `raw` is the number to average across seeds; `value` is how it
        reads to a person, and the two must not be confused."""
        if raw is None:
            raw = value if isinstance(value, (int, float)) else None
        return {"key": key or what, "phase": phase, "what": what, "value": value,
                "raw": raw, "unit": unit, "why": why}

    return [
        row("—", "in the building", len(present), "people",
            "Everything below is of these.", key="present"),
        row("TTS", "asleep when it starts", f"{asleep / n:.0%}", "share",
            "Waking is the first and largest part of pre-movement.",
            raw=asleep / n, key="asleep"),
        row("TTS", "cannot hear the alarm", unheard, "people",
            "Audibility was the largest single driver Proulx measured: 169 s against "
            "515 s.", key="unheard"),
        row("TTS", "nobody would warn them", isolated, "people",
            "No household, no neighbour, no phone, not in the chat. For these the "
            "alarm is the only cue there is.", key="isolated"),
        row("TTS", "confers before acting, mean", f"{_mean(mill):.2f}", "0–1",
            "NIST found about 70% of occupants milled before evacuating.",
            raw=_mean(mill), key="mill"),
        row("TTS", "seeks a second cue, mean", f"{_mean(confirm):.2f}", "0–1",
            "A corridor-only alarm raises this; an in-flat one does not.",
            raw=_mean(confirm), key="confirm"),
        row("TTS", "will not leave without something",
            sum(1 for p in present if p.commitments), "people",
            "A pet, a child, documents. Time spent before the door, not after it.",
            key="committed"),
        row("TTS", "that gathering, all told", f"{gather / 60:.0f}", "minutes",
            "Summed across the building, not per person.",
            raw=gather / 60.0, key="gather_min"),
        row("TTE", "walking speed, mean", f"{_mean(speeds):.2f}", "m/s",
            "On the level and uncrowded; the simulation slows this for density, "
            "smoke and stairs.", raw=_mean(speeds), key="speed_mean"),
        row("TTE", "walking speed, slowest twentieth",
            f"{_quantile(speeds, 0.05):.2f}" if speeds else "—", "m/s",
            "A household moves at its slowest member's pace, so the tail matters more "
            "than the mean.", raw=_quantile(speeds, 0.05), key="speed_p5"),
        row("TTE", "walks with difficulty", len(slow), "people",
            "Uses the stairs, but slower and tires sooner.", key="slow"),
        row("TTE", "cannot use the stairs at all", len(stairless), "people",
            "Depends on the lift or on being carried.", key="stairless"),
        row("TTE", "of those, nobody in the flat to help", len(unhelped), "people",
            "The simulation looks for a caregiver on the same floor and will not find "
            "one for a one-person household.", key="unhelped"),
        row("TTE", "does not know a second staircase exists", no_second, "people",
            "Removes the alternative the model relies on when one stair blocks.",
            key="no_second_stair"),
        row("TTE", "knows the layout, mean",
            f"{_mean([p.knowledge.get('floorplan_familiarity') for p in present if p.knowledge.get('floorplan_familiarity') is not None]):.2f}",
            "0–1", "Residents chose familiar stairs over nearer ones (Proulx 1995).",
            raw=_mean([p.knowledge.get("floorplan_familiarity") for p in present]),
            key="familiarity"),
    ]


def _mean(values: list[Any]) -> float:
    vals = [float(v) for v in values if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


def makeup(pop: Population) -> dict[str, Any]:
    """Everything about this building's composition, as data."""
    return {
        "cohort": pop.cohort or "",
        "cohort_name": pop.cohort_name or "the base building",
        "question": pop.cohort_question,
        "scenario": pop.scenario.get("scenario_id"),
        "seed": pop.seed,
        "run_id": pop.run_id,
        "residents": len(pop.people),
        "households": len(pop.households),
        "distributions": {
            k: {"name": d.name, "unit": d.unit, "counts": d.counts,
                "total": d.total, "mean": d.mean, "median": d.median,
                "p5": d.p5, "p95": d.p95, "low": d.low, "high": d.high}
            for k, d in distributions(pop).items()
        },
        "crosstabs": crosstabs(pop),
        "egress_drivers": egress_drivers(pop),
        "conformance": pop.conformance,
    }
