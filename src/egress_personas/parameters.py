"""Turning Parameters rows into a persona's fields.

Composition for one (persona, field), in this order:

1. every matching row draws its value, *before* anything is composed, so no draw
   depends on the order rows happen to be in;
2. `set` — the matching row with the highest priority wins; the rest are recorded as
   shadowed rather than dropped in silence;
3. `add` — every matching delta, in (priority, id) order;
4. `mul` — every matching factor, in (priority, id) order. Float multiplication is
   not associative, so a fixed order is not a nicety;
5. `min` then `max`, then the field's own bounds, then rounding.

Additive before multiplicative because that is the shape the literature comes in: an
absolute anchor (adults walk 1.20 m/s) and then relative modifiers (a pet costs a
tenth of that).

If no `set` row matches and the field's default is INHERIT, the field is left out
entirely and the simulation's own rules decide it. A row that would have added to or
scaled an inherited field is reported: that is almost always an authoring mistake.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import dists
from .filters import Predicate, parse
from .persona import FIELDS, INHERIT, Persona
from .rng import draw_rng
from .tables import Tables, as_bool, as_int, as_list, text

ORDER = {"set": 0, "add": 1, "mul": 2, "min": 3, "max": 4}


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    target: str
    mechanism: str
    dist: str
    params: tuple[float | None, ...]
    categories: tuple[str, ...]
    weights: tuple[float, ...]
    pred: Predicate
    priority: int
    evidence: str
    sources: tuple[str, ...]
    phase: str

    @property
    def sort_key(self) -> tuple[int, int, str]:
        return (ORDER[self.mechanism], -self.priority, self.id)


@dataclass
class Step:
    """One contribution to one field, for the provenance sidecar."""

    rule: str
    mechanism: str
    dist: str
    drawn: Any
    result: Any
    evidence: str
    sources: list[str]
    why: str = ""
    draw_path: str = ""
    shadowed: bool = False


@dataclass
class Trace:
    field: str
    final: Any
    steps: list[Step] = field(default_factory=list)
    clamped: bool = False
    inherited: bool = False
    pinned: bool = False


def load_rules(tables: Tables) -> list[Rule]:
    """Every enabled Parameters row whose target is a writable field."""
    out: list[Rule] = []
    for row in tables["parameters"]:
        if as_bool(row.get("enabled")) is False:
            continue
        target = text(row.get("target"))
        mech = text(row.get("mechanism"))
        dist = text(row.get("dist"))
        if target not in FIELDS or mech not in ORDER or dist not in dists.PARAMS:
            continue  # validate() has already reported it
        params = tuple(
            (None if text(row.get(f"p{i}")) is None else float(row[f"p{i}"]))
            for i in range(1, 5)
        )
        ws = as_list(row.get("weights"))
        out.append(Rule(
            id=text(row.get("id")) or "?",
            name=text(row.get("name")) or "",
            target=target,
            mechanism=mech,
            dist=dist,
            params=params,
            categories=tuple(as_list(row.get("categories"))),
            weights=tuple(float(w) for w in ws) if ws else (),
            pred=parse(row.get("applies_to") or ""),
            priority=as_int(row.get("priority")) or 100,
            evidence=text(row.get("evidence")) or "INVENTED",
            sources=tuple(as_list(row.get("source_ids"))),
            phase=text(row.get("phase")) or "both",
        ))
    out.sort(key=lambda r: r.sort_key)
    return out


def _cast(value: Any, dtype: str) -> Any:
    if value is None:
        return None
    if dtype == "bool":
        return bool(value)
    if dtype == "int":
        return int(round(float(value)))
    if dtype == "float":
        return float(value)
    return value


def apply_rules(
    person: Persona,
    attrs: dict[str, Any],
    rules: list[Rule],
    seed: int,
    *,
    warnings: list[str] | None = None,
    missing_attrs: set[str] | None = None,
    matched: dict[str, int] | None = None,
) -> dict[str, Trace]:
    """Compose every field for one persona. Returns a trace per field it wrote."""
    from .filters import matches

    # Which rules apply to this persona, grouped by target.
    by_target: dict[str, list[Rule]] = {}
    for rule in rules:
        if not matches(rule.pred, attrs, missing_attrs):
            continue
        if matched is not None:
            matched[rule.id] = matched.get(rule.id, 0) + 1
        by_target.setdefault(rule.target, []).append(rule)

    traces: dict[str, Trace] = {}

    for target in sorted(set(by_target) | person.pinned):
        spec = FIELDS[target]
        applicable = by_target.get(target, [])
        trace = Trace(field=target, final=None)

        # A value pinned by a Cases row is a `set` at infinite priority.
        if target in person.pinned:
            pinned_value = person.get(target)
            trace.pinned = True
            trace.final = pinned_value
            trace.steps.append(Step(
                rule="case", mechanism="set", dist="const", drawn=pinned_value,
                result=pinned_value, evidence="ESTIMATE", sources=[],
                why=f"pinned by Cases row {person.case_id}",
            ))
            for rule in applicable:
                trace.steps.append(Step(
                    rule=rule.id, mechanism=rule.mechanism, dist=rule.dist,
                    drawn=None, result=pinned_value, evidence=rule.evidence,
                    sources=list(rule.sources), shadowed=True,
                    why="a hand-authored case pins this field",
                ))
            traces[target] = trace
            continue

        # 1. Draw everything first.
        drawn: list[tuple[Rule, Any, str]] = []
        for rule in applicable:
            path = f"persona/{person.key}/{target}/{rule.id}"
            rng = draw_rng(seed, path)
            value = dists.sample(
                rule.dist, list(rule.params), rng,
                categories=list(rule.categories) or None,
                weights=list(rule.weights) or None,
            )
            drawn.append((rule, value, path))

        # 2. set
        sets = [(r, v, p) for r, v, p in drawn if r.mechanism == "set"]
        base: Any
        if sets:
            best = max(sets, key=lambda t: (t[0].priority, t[0].id))
            base = best[1]
            for rule, value, path in sets:
                trace.steps.append(Step(
                    rule=rule.id, mechanism="set", dist=rule.dist, drawn=value,
                    result=base, evidence=rule.evidence, sources=list(rule.sources),
                    why=str(rule.pred), draw_path=path,
                    shadowed=rule is not best[0],
                ))
        elif spec.default is INHERIT:
            others = [r.id for r, _, _ in drawn if r.mechanism != "set"]
            if others and warnings is not None:
                warnings.append(
                    f"{', '.join(others)} would {applicable[0].mechanism} "
                    f"{target}, but nothing sets it and its default is 'inherit', so "
                    f"the field is not emitted at all and those rows do nothing"
                )
            trace.inherited = True
            trace.final = None
            traces[target] = trace
            continue
        else:
            base = spec.default
            trace.steps.append(Step(
                rule="default", mechanism="set", dist="const", drawn=base,
                result=base, evidence="ESTIMATE", sources=[],
                why="no parameter row matched; the field's own default",
            ))

        # 3-5. add, mul, min, max
        value = base
        for rule, drawn_value, path in drawn:
            if rule.mechanism == "set":
                continue
            if isinstance(value, bool) or isinstance(value, str):
                if warnings is not None:
                    warnings.append(
                        f"{rule.id} tries to {rule.mechanism} {target}, which is "
                        f"{spec.dtype}; only 'set' makes sense there"
                    )
                continue
            if rule.mechanism == "add":
                value = float(value) + float(drawn_value)
            elif rule.mechanism == "mul":
                value = float(value) * float(drawn_value)
            elif rule.mechanism == "min":
                value = max(float(value), float(drawn_value))
            elif rule.mechanism == "max":
                value = min(float(value), float(drawn_value))
            trace.steps.append(Step(
                rule=rule.id, mechanism=rule.mechanism, dist=rule.dist,
                drawn=drawn_value, result=value, evidence=rule.evidence,
                sources=list(rule.sources), why=str(rule.pred), draw_path=path,
            ))

        # bounds and rounding
        if not isinstance(value, (bool, str)):
            lo, hi = spec.lo, spec.hi
            bounded = value
            if lo is not None:
                bounded = max(bounded, lo)
            if hi is not None:
                bounded = min(bounded, hi)
            if bounded != value:
                trace.clamped = True
                value = bounded
            if spec.decimals is not None:
                value = round(float(value), spec.decimals)

        value = _cast(value, spec.dtype)
        trace.final = value
        traces[target] = trace

    for target, trace in traces.items():
        if trace.inherited:
            continue
        person.set(target, trace.final)

    return traces
