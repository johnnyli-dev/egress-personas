"""Who knows whom: the cross-household edges.

Three kinds beyond the household, chosen because the literature says something
about each:

* `knock` — you would knock on their door on the way out. Proulx found 62% of
  residents left in groups and that seniors gathered on the landing first; NIST
  found 30-34% of WTC occupants helped others. Both are about people acting on a
  tie, so they bound the rate rather than fix it.
* `phone` — you would call or message them. One of NIST's listed pre-evacuation
  behaviours. Sparse, and strong where it exists.
* `group_chat` — a building group chat. This one has no literature at all; it comes
  from the team's own first-person walkthrough, and the rows that carry it say
  INVENTED. Modelled as membership of one node rather than a tie to every other
  member, because a clique of 200 people would be dense and say nothing.

Every edge is drawn from a stream keyed by the *unordered* pair, so a tie exists or
does not regardless of which end you ask from, and adding a third person elsewhere in
the building cannot change it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import dists
from .rng import draw_rng
from .tables import Tables, as_bool, as_float, as_list, text

GROUP_KINDS = ("group_chat",)

#: However new somebody is, they are not completely unconnected: they have met the
#: person opposite. An estimate, and the reason the floor is not a clamp at zero.
MIN_CONNECTEDNESS = 0.15


def connectedness(person: Any, ref_years: float | None) -> float:
    """How connected somebody is relative to an established resident, 0.15 to 1.

    Somebody who moved in last month has not met their neighbours yet. Proulx found
    residents relying on familiar people and familiar stairs, which is the mechanism;
    the shape here is ours, and the rows that use it say so.
    """
    if not ref_years:
        return 1.0
    tenure = person.identity.get("tenure_years")
    if tenure is None:
        return 1.0
    return max(MIN_CONNECTEDNESS, min(1.0, float(tenure) / ref_years))


@dataclass(frozen=True)
class TieRule:
    id: str
    kind: str
    scope: str
    rate: float
    rate_kind: str
    tenure_ref_years: float | None
    min_age_years: float | None
    dist: str
    params: tuple[float | None, ...]
    symmetric: bool
    evidence: str
    sources: tuple[str, ...]


def load_tie_rules(tables: Tables) -> list[TieRule]:
    out = []
    for row in tables["social"]:
        kind = text(row.get("tie_kind"))
        if kind == "household":
            continue  # structural: everyone in a flat, handled by the sampler
        rate = as_float(row.get("formation_rate"))
        if kind is None or rate is None:
            continue
        out.append(TieRule(
            id=text(row.get("id")) or "?",
            kind=kind,
            scope=text(row.get("scope")) or "building",
            rate=rate,
            rate_kind=text(row.get("rate_kind")) or "per_pair",
            tenure_ref_years=as_float(row.get("tenure_ref_years")),
            min_age_years=as_float(row.get("min_age_years")),
            dist=text(row.get("strength_dist")) or "const",
            params=tuple(
                (None if text(row.get(f"s{i}")) is None else float(row[f"s{i}"]))
                for i in range(1, 5)
            ),
            symmetric=bool(as_bool(row.get("symmetric"))),
            evidence=text(row.get("evidence")) or "INVENTED",
            sources=tuple(as_list(row.get("source_ids"))),
        ))
    return out


def _in_scope(scope: str, a: Any, b: Any) -> bool:
    fa, fb = a.situation.get("floor_label"), b.situation.get("floor_label")
    if scope == "same_floor":
        return fa == fb
    if scope == "adjacent_floor":
        return fa is not None and fb is not None and abs(fa - fb) == 1
    return True


def _old_enough(person: Any, min_age: float | None) -> bool:
    if not min_age:
        return True
    age = person.identity.get("age_years")
    return age is None or age >= min_age


def _eligible(people: list[Any], scope: str, min_age: float | None = None):
    """Every pair this scope could tie, households excluded (already tied)."""
    pool = [p for p in people if _old_enough(p, min_age)]
    for i, a in enumerate(pool):
        for b in pool[i + 1:]:
            if a.household and a.household == b.household:
                continue
            if _in_scope(scope, a, b):
                yield a, b


def build(
    people: list[Any],
    rules: list[TieRule],
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Add ties to every persona in place. Returns (groups, per-kind statistics)."""
    # Household edges: complete within a flat, at full strength.
    by_household: dict[str, list[Any]] = {}
    for p in people:
        if p.household:
            by_household.setdefault(p.household, []).append(p)
    for members in by_household.values():
        for a in members:
            for b in members:
                if a is not b:
                    a.ties.append({"to": b.key, "kind": "household", "strength": 1.0})

    groups: list[dict[str, Any]] = []
    stats: list[dict[str, Any]] = []

    for rule in rules:
        if rule.kind in GROUP_KINDS:
            node = f"G_{rule.kind}_building"
            members = []
            conn = {p.key: connectedness(p, rule.tenure_ref_years) for p in people
                    if _old_enough(p, rule.min_age_years)}
            total = sum(conn.values())
            base = (rule.rate * len(conn) / total) if total else 0.0
            for p in people:
                if not _old_enough(p, rule.min_age_years):
                    continue
                rng = draw_rng(seed, f"tie/{rule.kind}/{p.key}")
                if not rng.chance(min(1.0, base * conn[p.key])):
                    continue
                strength = dists.sample(
                    rule.dist, list(rule.params),
                    draw_rng(seed, f"tie/{rule.kind}/{p.key}/strength"),
                )
                p.ties.append({"to": node, "kind": rule.kind,
                               "strength": round(float(strength), 3)})
                members.append(p.key)
            groups.append({"id": node, "kind": rule.kind, "members": members,
                           "evidence": rule.evidence, "sources": list(rule.sources)})
            stats.append({"rule": rule.id, "kind": rule.kind, "scope": rule.scope,
                          "rate_kind": rule.rate_kind, "rate": rule.rate,
                          "tenure_ref_years": rule.tenure_ref_years,
                          "realized": len(members) / max(len(conn), 1),
                          "eligible_people": len(conn),
                          "realized_degree": round(
                              len(members) / max(len(conn), 1), 3),
                          "edges": len(members), "pairs": len(conn)})
            continue

        conn = {p.key: connectedness(p, rule.tenure_ref_years) for p in people
                if _old_enough(p, rule.min_age_years)}
        n_eligible_people = len(conn)
        eligible = list(_eligible(people, rule.scope, rule.min_age_years))
        weight_total = sum(conn[a.key] * conn[b.key] for a, b in eligible)

        # The stated rate is met on average whichever way it is stated; the weights
        # only decide who gets the ties, not how many there are.
        wanted_edges = (rule.rate * n_eligible_people / 2.0
                        if rule.rate_kind == "per_person_degree"
                        else rule.rate * len(eligible))
        base = wanted_edges / weight_total if weight_total else 0.0

        made = pairs = 0
        for a, b in eligible:
                pairs += 1
                lo, hi = sorted((a.key, b.key))
                path = f"tie/{rule.kind}/{lo}|{hi}"
                rate = min(1.0, base * conn[a.key] * conn[b.key])
                if not draw_rng(seed, path).chance(rate):
                    continue
                strength = round(float(dists.sample(
                    rule.dist, list(rule.params), draw_rng(seed, path + "/strength"))), 3)
                a.ties.append({"to": b.key, "kind": rule.kind, "strength": strength})
                if rule.symmetric:
                    b.ties.append({"to": a.key, "kind": rule.kind, "strength": strength})
                made += 1
        stats.append({"rule": rule.id, "kind": rule.kind, "scope": rule.scope,
                      "rate_kind": rule.rate_kind, "rate": rule.rate,
                      "tenure_ref_years": rule.tenure_ref_years,
                      "base_pair_rate": round(base, 6),
                      "realized": made / pairs if pairs else 0.0,
                      "eligible_people": n_eligible_people,
                      "realized_degree": round(
                          2.0 * made / max(n_eligible_people, 1), 3),
                      "edges": made, "pairs": pairs})

    for p in people:
        p.ties.sort(key=lambda t: (t["kind"], t["to"]))
    return groups, stats


def degree_summary(people: list[Any]) -> dict[str, dict[str, float]]:
    """Mean and max degree per tie kind, for the report."""
    out: dict[str, dict[str, float]] = {}
    for p in people:
        counts: dict[str, int] = {}
        for t in p.ties:
            counts[t["kind"]] = counts.get(t["kind"], 0) + 1
        for kind, n in counts.items():
            d = out.setdefault(kind, {"total": 0.0, "max": 0.0, "with_any": 0.0})
            d["total"] += n
            d["max"] = max(d["max"], n)
            d["with_any"] += 1
    n_people = max(len(people), 1)
    for kind, d in out.items():
        d["mean_over_all"] = round(d["total"] / n_people, 3)
        d["share_with_any"] = round(d["with_any"] / n_people, 3)
    return out
