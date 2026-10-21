"""Compiling personas into the quantities an egress model can act on.

The registry gives a resident dispositions and knowledge: how readily they confer
before acting, whether they know a second staircase exists, how well they know the
layout. No egress simulation reads any of that. What simulations read is a
pre-movement time, a walking speed, a queue patience, a turn-back threshold.

This module is the bridge, and it is where a heuristic stops being a note and starts
changing a number. Each **effect** names one canonical output and says how the
persona decides it. Five mechanisms:

* `quantile` — compose a score from weighted traits, rank it within the population,
  and read the value off a published reference distribution at that quantile. The
  marginal is preserved exactly; what the traits decide is the ordering.
* `direct` — carry a persona field straight across, unit for unit.
* `scale` — multiply an output by a factor.
* `gate` — a condition forces an output to a fixed value, whatever else produced it.
* `sum` — add up a quantity across a resident's commitments.

Effects run after every heuristic has finished, on the completed persona, so unlike
`applies_to` inside the registry they may read fields the registry writes. That is the
point of their being a separate pass.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any

from .dists_ref import FAMILIES, Reference
from .filters import FilterError, Predicate, matches, parse
from .rng import draw_rng
from .tables import Tables, as_bool, as_float, as_int, as_list, text

MECHANISMS = ("quantile", "direct", "scale", "gate", "sum")

#: Order effects are applied in. A gate must be able to override whatever set the
#: value, so it goes last; a scale needs something to scale, so it goes after the
#: things that establish a value.
MECHANISM_ORDER = {"quantile": 0, "direct": 0, "sum": 0, "scale": 1, "gate": 2}


@dataclass(frozen=True)
class Output:
    """One canonical per-occupant quantity an egress model needs."""

    id: str
    name: str
    unit: str
    dtype: str
    phase: str
    required: bool
    reference_dist: str = ""
    lo: float | None = None
    hi: float | None = None
    decimals: int | None = None
    vocab: str = ""
    what: str = ""
    status: str = "proposed"


@dataclass(frozen=True)
class Effect:
    id: str
    name: str
    output: str
    mechanism: str
    terms: tuple[tuple[str, float], ...]
    pred: Predicate
    value: float | None
    from_field: str
    within: str
    evidence: str
    sources: tuple[str, ...]
    finding: str
    priority: int


@dataclass
class Step:
    effect: str
    mechanism: str
    detail: str
    result: Any
    evidence: str
    sources: list[str] = field(default_factory=list)


@dataclass
class Compiled:
    """One resident's simulation-facing quantities, and how each was arrived at."""

    values: dict[str, Any] = field(default_factory=dict)
    quantiles: dict[str, float] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    steps: dict[str, list[Step]] = field(default_factory=dict)


# ── reading the three tabs ──────────────────────────────────────────────────

def read_outputs(tables: Tables) -> dict[str, Output]:
    out: dict[str, Output] = {}
    for row in (tables.get("outputs") or []):
        oid = text(row.get("output_id"))
        if not oid:
            continue
        out[oid] = Output(
            id=oid,
            name=text(row.get("name")) or oid,
            unit=text(row.get("unit")) or "",
            dtype=text(row.get("dtype")) or "float",
            phase=text(row.get("phase")) or "both",
            required=bool(as_bool(row.get("required"))),
            reference_dist=text(row.get("reference_dist")) or "",
            lo=as_float(row.get("lo")), hi=as_float(row.get("hi")),
            decimals=as_int(row.get("decimals")),
            vocab=text(row.get("vocab")) or "",
            what=text(row.get("what")) or "",
            status=text(row.get("status")) or "proposed",
        )
    return out


def read_references(tables: Tables) -> dict[str, Reference]:
    out: dict[str, Reference] = {}
    for row in (tables.get("distributions") or []):
        did = text(row.get("dist_id"))
        fam = text(row.get("family"))
        if not did or fam not in FAMILIES:
            continue
        curve: list[tuple[float, float]] = []
        for pair in as_list(row.get("curve")):
            bits = pair.split(":")
            if len(bits) == 2:
                try:
                    curve.append((float(bits[0]), float(bits[1])))
                except ValueError:
                    pass
        out[did] = Reference(
            id=did, name=text(row.get("name")) or did, family=fam,
            unit=text(row.get("unit")) or "",
            params=tuple(as_float(row.get(f"p{i}")) for i in range(1, 5)),
            curve=tuple(curve),
            applies_when=text(row.get("applies_when")) or "",
            evidence=text(row.get("evidence")) or "INVENTED",
            sources=tuple(as_list(row.get("source_ids"))),
            finding=text(row.get("finding")) or "",
        )
    return out


def read_effects(tables: Tables) -> list[Effect]:
    out: list[Effect] = []
    for row in (tables.get("effects") or []):
        if as_bool(row.get("enabled")) is False:
            continue
        mech = text(row.get("mechanism"))
        if mech not in MECHANISMS:
            continue
        terms: list[tuple[str, float]] = []
        for part in as_list(row.get("terms")):
            name, _, weight = part.partition(":")
            try:
                terms.append((name.strip(), float(weight)))
            except ValueError:
                continue
        try:
            pred = parse(row.get("applies_to") or "")
        except FilterError:
            pred = parse("")
        out.append(Effect(
            id=text(row.get("effect_id")) or "?",
            name=text(row.get("name")) or "",
            output=text(row.get("output")) or "",
            mechanism=mech,
            terms=tuple(terms),
            pred=pred,
            value=as_float(row.get("value")),
            from_field=text(row.get("from_field")) or "",
            within=text(row.get("within")) or "",
            evidence=text(row.get("evidence")) or "INVENTED",
            sources=tuple(as_list(row.get("source_ids"))),
            finding=text(row.get("finding")) or "",
            priority=as_int(row.get("priority")) or 100,
        ))
    # Ascending priority: a later application overwrites an earlier one, so the
    # highest priority is the one that survives.
    out.sort(key=lambda e: (MECHANISM_ORDER[e.mechanism], e.priority, e.id))
    return out


# ── reading a trait off a finished persona ──────────────────────────────────

def trait(person: Any, name: str) -> Any:
    """A value by bare name, looked up across the persona's blocks.

    Effects run on a finished persona, so they may read anything on it — including the
    dispositions and knowledge the registry wrote, which `applies_to` inside the
    registry deliberately may not.
    """
    for block in ("dispositions", "knowledge", "body", "identity", "situation"):
        got = getattr(person, block, {})
        if name in got:
            return got[name]
    if name == "household_size":
        return None
    if name == "ties":
        return len(person.ties)
    if name == "commitments":
        return len(person.commitments)
    if name == "lives_alone":
        return person.household_index is None
    if name == "alarm_heard":
        # Derived, and named so a reference distribution can be keyed on it: a resident
        # who cannot hear the alarm belongs in the poor-alarm fit.
        return "poor" if person.situation.get("alarm_audible") is False else "good"
    if name == "age_class":
        age = person.identity.get("age_years")
        if age is None:
            return "adult"
        return "child" if age < 18 else ("older" if age >= 65 else "adult")
    return None


#: Everything an effect may read: every block of the finished persona, plus the derived
#: traits. Deliberately wider than the registry's own `applies_to` vocabulary, because
#: effects run after the registry has finished and exist precisely to consume what it
#: wrote.
DERIVED = ("alarm_heard", "age_class", "lives_alone", "ties", "commitments")


def effect_attrs(person: Any) -> dict[str, Any]:
    """The view an effect's `applies_to` is matched against."""
    view: dict[str, Any] = {}
    for block in ("identity", "situation", "body", "knowledge", "dispositions"):
        view.update(getattr(person, block, {}) or {})
    for name in DERIVED:
        view[name] = trait(person, name)
    return view


def readable(person: Any = None) -> set[str]:
    """Every name an effect may reference, for the validator's did-you-mean."""
    from .persona import FIELDS
    names = {p.split(".", 1)[1] for p in FIELDS}
    names |= {"age_years", "age_band", "sex", "household_role", "tenure_years",
              "unit", "floor_label", "sim_floor", "present", "asleep", "activity",
              "mobility", "sim_agent_type", "can_use_stairs", "limiting_condition",
              "base_speed", "home_tile"}
    names |= set(DERIVED)
    return names


def _numeric(v: Any) -> float | None:
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    return None


def score_of(person: Any, effect: Effect, warnings: list[str] | None = None,
             ) -> tuple[float, list[str]]:
    """The weighted sum of an effect's terms for one resident, and how it reads."""
    total = 0.0
    parts: list[str] = []
    for name, weight in effect.terms:
        raw = trait(person, name)
        num = _numeric(raw)
        if num is None:
            # A resident who simply has not got this one contributes zero, which is
            # what a weighted sum should do. Whether *nobody* has it is checked once,
            # for the whole population, by `missing_terms` below.
            continue
        total += weight * num
        parts.append(f"{name} {num:g}×{weight:+g}")
    return total, parts


# ── the compile pass ────────────────────────────────────────────────────────

def compile_population(people: list[Any], outputs: dict[str, Output],
                       refs: dict[str, Reference], effects: list[Effect],
                       *, seed: int, scenario: dict[str, Any] | None = None,
                       attrs_of=None, warnings: list[str] | None = None,
                       ) -> dict[str, Compiled]:
    """Turn every persona into the quantities an egress model reads.

    A quantile effect needs the whole population at once: a resident's place in a
    distribution is only defined relative to everybody else. That is the one piece of
    this pipeline that is deliberately not per-person.
    """
    warnings = warnings if warnings is not None else []
    out = {p.key: Compiled() for p in people}
    scen = scenario or {}
    blocked: list[str] = []

    for name in missing_terms(people, effects):
        warnings.append(
            f"no resident carries {name!r}, which an effect reads, so that term "
            f"contributes nothing to anybody — check the spelling against the fields "
            f"the registry writes")

    for effect in effects:
        if effect.output not in outputs:
            warnings.append(
                f"{effect.id} targets output {effect.output!r}, which the Outputs tab "
                f"does not define, so it changes nothing")
            continue
        spec = outputs[effect.output]
        subject = [p for p in people if matches(effect.pred, effect_attrs(p))]
        if not subject:
            warnings.append(
                f"{effect.id} ({effect.name}) matched no resident: {effect.pred}")
            continue

        if effect.mechanism == "quantile":
            if not spec.reference_dist:
                blocked.append(
                    f"{effect.id} ({effect.name}) has nothing to read a value off: "
                    f"{spec.id} has no reference distribution, because no published "
                    f"figure for it was found. The effect is kept so the gap stays "
                    f"visible.")
                continue
            _apply_quantile(subject, effect, spec, refs, out, seed, scen, warnings)
        elif effect.mechanism == "direct":
            for p in subject:
                v = trait(p, effect.from_field)
                if v is None:
                    continue
                out[p.key].values[spec.id] = v
                out[p.key].steps.setdefault(spec.id, []).append(Step(
                    effect.id, "direct", f"from {effect.from_field}", v,
                    effect.evidence, list(effect.sources)))
        elif effect.mechanism == "sum":
            for p in subject:
                total = sum((c.get(effect.from_field) or 0.0)
                            for c in p.commitments)
                out[p.key].values[spec.id] = total
                out[p.key].steps.setdefault(spec.id, []).append(Step(
                    effect.id, "sum",
                    f"{len(p.commitments)} commitment(s) × {effect.from_field}",
                    total, effect.evidence, list(effect.sources)))
        elif effect.mechanism == "scale":
            for p in subject:
                have = out[p.key].values.get(spec.id)
                if not isinstance(have, (int, float)) or isinstance(have, bool):
                    continue
                factor = effect.value
                if factor is None and effect.from_field:
                    factor = _numeric(trait(p, effect.from_field))
                if factor is None:
                    continue
                now = float(have) * factor
                out[p.key].values[spec.id] = now
                out[p.key].steps.setdefault(spec.id, []).append(Step(
                    effect.id, "scale", f"×{factor:g}", now,
                    effect.evidence, list(effect.sources)))
        elif effect.mechanism == "gate":
            for p in subject:
                v: Any = effect.value
                if spec.dtype == "bool":
                    v = bool(effect.value) if effect.value is not None else False
                out[p.key].values[spec.id] = v
                out[p.key].steps.setdefault(spec.id, []).append(Step(
                    effect.id, "gate", str(effect.pred), v,
                    effect.evidence, list(effect.sources)))

    # Bounds and rounding, once, after every effect has had its say.
    for p in people:
        c = out[p.key]
        for oid, v in list(c.values.items()):
            spec = outputs[oid]
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            if spec.lo is not None:
                v = max(v, spec.lo)
            if spec.hi is not None:
                v = min(v, spec.hi)
            if spec.decimals is not None:
                v = round(float(v), spec.decimals)
            c.values[oid] = int(v) if spec.dtype == "int" else v
    if blocked:
        out["__blocked__"] = Compiled(steps={"blocked": [
            Step("—", "blocked", b, None, "—") for b in blocked]})
    return out


def _apply_quantile(subject: list[Any], effect: Effect, spec: Output,
                    refs: dict[str, Reference], out: dict[str, Compiled],
                    seed: int, scen: dict[str, Any], warnings: list[str]) -> None:
    # Stratify where the distribution itself differs by group, so a resident's place is
    # compared against the population the fit describes and the marginal of each
    # stratum comes out as published.
    groups: dict[Any, list[Any]] = {}
    for p in subject:
        groups.setdefault(trait(p, effect.within) if effect.within else None,
                          []).append(p)

    for _key, members in groups.items():
        ref = _reference_for(spec, refs, scen, members[0])
        if ref is None:
            warnings.append(
                f"{effect.id} is a quantile effect on {spec.id}, but no reference "
                f"distribution matches (the Outputs tab asks for "
                f"{spec.reference_dist!r}"
                + (f", stratum {_key!r}" if _key is not None else "")
                + "), so it cannot read a value off anything")
            continue
        scored: list[tuple[float, float, Any, list[str]]] = []
        for p in members:
            s, parts = score_of(p, effect, warnings)
            # A tie is broken from the resident's own stream, so two identical
            # personas do not land in array order.
            jitter = draw_rng(seed, f"effect/{effect.id}/{p.key}").unit() * 1e-6
            scored.append((s + jitter, s, p, parts))
        scored.sort(key=lambda t: t[0])
        n = len(scored)
        for rank, (_tie, raw_score, p, parts) in enumerate(scored):
            q = (rank + 0.5) / n
            value = ref.ppf(q)
            c = out[p.key]
            c.values[spec.id] = value
            c.quantiles[spec.id] = q
            c.scores[spec.id] = raw_score
            detail = (f"score {raw_score:+.3f} → {q:.0%} of "
                      f"{n} {'(' + str(_key) + ')' if _key is not None else ''}".strip()
                      + f" → {ref.name}")
            if parts:
                detail += "  [" + ", ".join(parts) + "]"
            c.steps.setdefault(spec.id, []).append(Step(
                effect.id, "quantile", detail, value,
                _weakest(effect.evidence, ref.evidence),
                sorted(set(effect.sources) | set(ref.sources))))


def _reference_for(spec: Output, refs: dict[str, Reference], scen: dict[str, Any],
                   person: Any = None) -> Reference | None:
    """The reference distribution for an output, resolving a templated choice.

    `reference_dist` may name one distribution or carry a `{key}` filled from the
    scenario or from the resident. The second is what lets somebody who cannot hear the
    alarm be drawn from the *poor-alarm* fit rather than scaled away from the good one:
    Proulx's poor-alarm figure comes from buildings where a quarter of residents could
    not hear it, so an individual who cannot belongs in that distribution, not at a
    multiple of the other.
    """
    want = spec.reference_dist
    if not want:
        return None
    if "{" in want:
        for key, value in (scen or {}).items():
            want = want.replace("{" + str(key) + "}", str(value))
    if "{" in want and person is not None:
        import re as _re
        for key in _re.findall(r"\{([a-z0-9_]+)\}", want):
            got = trait(person, key)
            if got is not None:
                want = want.replace("{" + key + "}", str(got))
    return refs.get(want)


_ORDER = {"SOURCED": 0, "ESTIMATE": 1, "INVENTED": 2}


def _weakest(*labels: str) -> str:
    """The weakest label among those that contributed.

    A value read off a sourced distribution at a quantile decided by an invented
    ordering is not sourced. The chain is only as good as its weakest link, and saying
    otherwise would launder a guess.
    """
    return max((l for l in labels if l in _ORDER), key=lambda l: _ORDER[l],
               default="INVENTED")


def missing_terms(people: list[Any], effects: list[Effect]) -> list[str]:
    """Names an effect reads that *no* resident carries. Almost always a typo."""
    wanted: set[str] = set()
    for e in effects:
        wanted |= {n for n, _ in e.terms}
        # A `sum` effect's from_field names a key inside each commitment, not a field
        # on the persona, so looking for it there would always come up empty.
        if e.from_field and e.mechanism != "sum":
            wanted.add(e.from_field)
    return sorted(n for n in wanted
                  if all(trait(p, n) is None for p in people))


def coverage(outputs: dict[str, Output], effects: list[Effect],
             heuristic_targets: set[str]) -> dict[str, Any]:
    """What reaches a simulation, and what stops at the registry.

    The question this whole module exists to answer: of the fields the heuristics
    write, which end up changing a number a simulation reads?
    """
    reached_fields: set[str] = set()
    how: dict[str, set[str]] = {}
    per_output: dict[str, list[str]] = {}
    for e in effects:
        per_output.setdefault(e.output, []).append(e.id)
        # A field can reach an output four ways, and counting only the first two
        # reported a field as a dead end when a gate or a stratum was using it.
        for name, _w in e.terms:
            reached_fields.add(name)
            how.setdefault(name, set()).add(f"{e.id} weighs it")
        if e.from_field:
            reached_fields.add(e.from_field)
            how.setdefault(e.from_field, set()).add(f"{e.id} carries it across")
        for attr in e.pred.attrs:
            reached_fields.add(attr)
            how.setdefault(attr, set()).add(f"{e.id} gates on it")
        if e.within:
            reached_fields.add(e.within)
            how.setdefault(e.within, set()).add(f"{e.id} strata by it")
    # A derived trait stands in for the field it is computed from, so crediting the
    # derivation means crediting its input too.
    for derived, source in (("alarm_heard", "alarm_audible"),
                            ("age_class", "age_years")):
        if derived in reached_fields:
            reached_fields.add(source)
            how.setdefault(source, set()).add(f"via the derived {derived!r}")

    bare = {t.split(".", 1)[-1] for t in heuristic_targets}
    return {
        "outputs": {oid: {"effects": per_output.get(oid, []),
                          "required": o.required,
                          "status": o.status,
                          "has_effect": bool(per_output.get(oid))}
                    for oid, o in outputs.items()},
        "fields_reaching_a_simulation": sorted(bare & reached_fields),
        "fields_stopping_at_the_registry": sorted(bare - reached_fields),
        "how": {k: sorted(v) for k, v in sorted(how.items()) if k in bare},
        "outputs_without_an_effect": sorted(
            oid for oid, o in outputs.items() if not per_output.get(oid)),
    }


def marginal_check(people: list[Any], compiled: dict[str, Compiled],
                   outputs: dict[str, Output], refs: dict[str, Reference],
                   scen: dict[str, Any]) -> list[dict[str, Any]]:
    """Did assigning quantiles by trait preserve each reference distribution?

    This is the claim the whole quantile mechanism rests on: the persona decides the
    ordering, the literature keeps the shape. If the realized mean drifts from the
    published one, it does not.
    """
    rows: list[dict[str, Any]] = []
    for oid, spec in outputs.items():
        ref = _reference_for(spec, refs, scen)
        if ref is None:
            continue
        vals = [c.values.get(oid) for c in compiled.values()
                if isinstance(c.values.get(oid), (int, float))
                and not isinstance(c.values.get(oid), bool)]
        if not vals:
            continue
        want = ref.mean_estimate()
        got = statistics.fmean(vals)
        rows.append({
            "output": oid, "reference": ref.id, "unit": spec.unit,
            "published_mean": None if want is None else round(want, 3),
            "realized_mean": round(got, 3),
            "n": len(vals),
            "within_1pc": (want is not None and want != 0
                           and abs(got - want) / abs(want) < 0.01),
        })
    return rows
