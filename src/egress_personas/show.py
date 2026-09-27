"""Looking at one persona in the terminal.

Sampling somebody and reading them is how you tell whether the generator is producing
people or noise, and it is the fastest check there is: the card says who they are, the
blocks say what the simulation will act on, the connections say who they would reach
for, and the provenance says which paper each number came from.
"""

from __future__ import annotations

from typing import Any, Callable

from .parameters import Trace
from .rng import draw_rng
from .sample import Population

#: The subsets worth pulling out, because each is a case the research cares about.
FILTERS: dict[str, tuple[str, Callable[[Any], bool]]] = {
    "all": ("everybody", lambda p: True),
    "cases": ("the hand-authored cases", lambda p: bool(p.case_id)),
    "isolated": ("nobody in the flat, no neighbour, no phone, not in the chat",
                 lambda p: not p.ties),
    "lift": ("cannot use the stairs at all",
             lambda p: p.body.get("mobility") == "wheelchair"),
    "unheard": ("cannot hear the alarm where they are",
                lambda p: p.situation.get("alarm_audible") is False),
    "slow": ("walks with difficulty", lambda p: bool(p.body.get("limiting_condition"))),
    "children": ("under 18", lambda p: p.identity["age_years"] < 18),
    "older": ("65 and over", lambda p: p.identity["age_years"] >= 65),
    "committed": ("will not leave without something", lambda p: bool(p.commitments)),
    "absent": ("not in the building", lambda p: not p.situation.get("present")),
    "alone": ("lives alone", lambda p: p.household_index is None),
}

TIE_LABEL = {
    "household": "household",
    "knock": "would knock",
    "phone": "would phone",
    "group_chat": "building chat",
}


def _wrap(text: str, width: int, indent: str) -> list[str]:
    words, lines, line = text.split(), [], ""
    for w in words:
        if line and len(line) + 1 + len(w) > width:
            lines.append(indent + line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        lines.append(indent + line)
    return lines


def _num(v: Any) -> str:
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def pick(pop: Population, *, which: str = "all", persona_id: str | None = None,
         floor: int | None = None, unit: str | None = None,
         count: int = 1, seed: int | None = None) -> list[Any]:
    """The personas to show. Sampling is seeded, so a shown persona can be shown again."""
    if persona_id:
        wanted = persona_id.strip()
        found = [p for p in pop.people
                 if wanted in (p.id, p.key, p.case_id)]
        if not found:
            raise KeyError(
                f"no persona {wanted!r}. Use an id like P0041, a key like "
                f"'case:C01' or 'synth:4A:0', or a case id like C01."
            )
        return found

    if which not in FILTERS:
        raise KeyError(f"unknown filter {which!r}; try one of: {', '.join(FILTERS)}")
    pool = [p for p in pop.people if FILTERS[which][1](p)]
    if floor is not None:
        pool = [p for p in pool if p.situation.get("floor_label") == floor]
    if unit:
        pool = [p for p in pool if p.situation.get("unit") == unit.upper()]
    if not pool:
        return []

    # Sample without replacement, deterministically: order the pool by a draw of its
    # own and take the front of it.
    tag = seed if seed is not None else pop.seed
    ordered = sorted(pool, key=lambda p: draw_rng(tag, f"show/{which}/{p.key}").unit())
    return ordered[:max(count, 1)]


def render(pop: Population, person: Any, *, width: int = 92,
           provenance: bool = True) -> str:
    L: list[str] = []
    ident, body, sit = person.identity, person.body, person.situation
    by_key = {p.key: p for p in pop.people}

    title = ident.get("name") or f"{ident['age_years']}-year-old {ident['sex']}"
    tag = f"  ·  case {person.case_id}" if person.case_id else ""
    L.append(f"{person.id}  {title}{tag}")
    where = (f"{sit.get('unit')} · floor {sit.get('floor_label')} "
             f"(simulation floor {sit.get('sim_floor')}) · {sit.get('activity')}")
    if not sit.get("present"):
        where += " · NOT IN THE BUILDING"
    L.append(where)
    L.append("─" * width)
    L += _wrap(person.narrative, width - 2, "  ")
    L.append("")

    L.append("  identity      " + "   ".join([
        f"age {ident['age_years']}", ident["sex"],
        ident.get("household_role", "?"),
        f"{_num(ident.get('tenure_years'))}y in the building",
        f"type {body.get('sim_agent_type')}",
    ]))
    mob = body.get("mobility")
    stairs = "cannot use stairs" if body.get("can_use_stairs") is False else "uses stairs"
    L.append(f"  mobility      {mob}   {stairs}"
             + (f"   escorted by {body['escorted_by']}" if body.get("escorted_by") else "")
             + (f"   escorts {body['escorts']}" if body.get("escorts") else ""))

    for label, block, unit_of in (
        ("body", person.body, {"base_speed": " m/s", "patience_s": " s",
                               "smoke_limit_m": " m", "delay_s": " s"}),
        ("knowledge", person.knowledge, {}),
        ("dispositions", person.dispositions, {}),
    ):
        shown = {k: v for k, v in sorted(block.items())
                 if k not in ("mobility", "sim_agent_type", "can_use_stairs",
                              "escorts", "escorted_by")}
        if not shown:
            continue
        bits = [f"{k} {_num(v)}{unit_of.get(k, '')}" for k, v in shown.items()]
        first = f"  {label:<13} "
        line = first
        for b in bits:
            if len(line) + len(b) + 3 > width:
                L.append(line.rstrip())
                line = " " * len(first)
            line += b + "   "
        L.append(line.rstrip())

    if person.commitments:
        what = ", ".join(
            f"{c.get('what') or c['kind']} (+{_num(c.get('delay_s'))}s)"
            for c in person.commitments)
        L.append(f"  will not leave without  {what}")

    L.append("")
    if not person.ties:
        L.append("  connections   none. Nobody in the flat, no neighbour they would "
                 "knock for,")
        L.append("                nobody to phone, and not in the building chat.")
    else:
        L.append(f"  connections   {len(person.ties)}")
        for kind in ("household", "knock", "phone", "group_chat"):
            group = [t for t in person.ties if t["kind"] == kind]
            if not group:
                continue
            for i, t in enumerate(sorted(group, key=lambda t: -t["strength"])):
                label = TIE_LABEL[kind] if i == 0 else ""
                other = by_key.get(t["to"])
                if other is None:
                    members = next((len(g["members"]) for g in pop.groups
                                    if g["id"] == t["to"]), 0)
                    who = f"{t['to']}  ({members} members)"
                    extra = ""
                else:
                    name = other.identity.get("name") or other.body.get("sim_agent_type")
                    who = f"{other.id} {other.situation.get('unit'):<5} {name}"
                    extra = ""
                bar = "█" * max(1, round(t["strength"] * 8))
                L.append(f"    {label:<14}{who:<44}{bar:<8} {t['strength']:.2f}{extra}")

    if provenance:
        traces: dict[str, Trace] = pop.traces.get(person.key, {})
        if traces:
            L.append("")
            L.append("  where the numbers come from")
            for path, tr in sorted(traces.items()):
                if tr.inherited:
                    L.append(f"    {path:<38} — left to the simulation's own rules")
                    continue
                chain = " then ".join(
                    f"{s.rule} {s.mechanism}" for s in tr.steps if not s.shadowed)
                labels = sorted({s.evidence for s in tr.steps if not s.shadowed})
                srcs = sorted({x for s in tr.steps if not s.shadowed for x in s.sources})
                tail = f"  [{', '.join(srcs)}]" if srcs else ""
                pinned = "  (pinned by the case)" if tr.pinned else ""
                L.append(f"    {path:<38} {_num(tr.final):<9} {chain}"
                         f"  {'/'.join(labels)}{tail}{pinned}")
    return "\n".join(L)


def summary(pop: Population) -> str:
    """One line per interesting subset, so you know what there is to sample."""
    L = [f"{len(pop.people)} residents · {len(pop.households)} households · "
         f"{sum(len(p.ties) for p in pop.people)} tie endpoints", ""]
    for name, (what, test) in FILTERS.items():
        n = sum(1 for p in pop.people if test(p))
        L.append(f"  {name:<11} {n:>4}   {what}")
    return "\n".join(L)
