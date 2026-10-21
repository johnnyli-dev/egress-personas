"""The chain from a line in the literature to a number an engine acts on.

    source → heuristic → persona field → effect → canonical output → engine field

This is the view the whole pipeline exists to make checkable. It answers the question
that matters when somebody asks whether a model is grounded: *for this number the
simulation acts on, what is the weakest link behind it?*

The answer is deliberately pessimistic. A value read off a sourced distribution at a
quantile decided by an invented ordering is INVENTED, not SOURCED. Reporting the
stronger label would launder a guess into a citation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .tables import Tables, as_bool, as_list, text

ORDER = {"SOURCED": 0, "ESTIMATE": 1, "INVENTED": 2}


def weakest(*labels: str) -> str:
    known = [x for x in labels if x in ORDER]
    return max(known, key=lambda x: ORDER[x]) if known else "INVENTED"


@dataclass
class Link:
    """One end-to-end chain, from a heuristic to an engine field."""

    heuristic: str
    heuristic_name: str
    phase: str
    field: str
    heuristic_evidence: str
    heuristic_sources: list[str] = field(default_factory=list)
    effect: str = ""
    effect_name: str = ""
    effect_how: str = ""
    effect_evidence: str = ""
    output: str = ""
    output_name: str = ""
    reference: str = ""
    reference_evidence: str = ""
    engine_field: str = ""
    engine_supports: bool = False
    blocked_because: str = ""

    @property
    def chain_evidence(self) -> str:
        return weakest(self.heuristic_evidence, self.effect_evidence,
                       self.reference_evidence)

    @property
    def reaches_engine(self) -> bool:
        return bool(self.engine_field) and self.engine_supports


def build(tables: Tables, pop: Any, adapter: Any) -> list[Link]:
    """Every chain, including the ones that stop short."""
    effects = pop.effects
    outputs = pop.outputs
    refs = pop.references

    # Which effects consume which persona field, and how.
    consumers: dict[str, list[tuple[Any, str]]] = {}
    for e in effects:
        for name, w in e.terms:
            consumers.setdefault(name, []).append((e, f"weighs it {w:+g}"))
        if e.from_field and e.mechanism != "sum":
            consumers.setdefault(e.from_field, []).append((e, "carries it across"))
        for attr in e.pred.attrs:
            consumers.setdefault(attr, []).append((e, "gates on it"))
        if e.within:
            consumers.setdefault(e.within, []).append((e, "strata the ranking by it"))
    for derived, source in (("alarm_heard", "alarm_audible"),
                            ("age_class", "age_years")):
        for e, how in consumers.get(derived, []):
            consumers.setdefault(source, []).append((e, f"{how}, via {derived}"))

    links: list[Link] = []
    for row in tables["parameters"]:
        if as_bool(row.get("enabled")) is False:
            continue
        hid = text(row.get("id")) or "?"
        target = text(row.get("target")) or ""
        bare = target.split(".", 1)[-1]
        base = dict(
            heuristic=hid,
            heuristic_name=text(row.get("name")) or "",
            phase=text(row.get("phase")) or "",
            field=target,
            heuristic_evidence=text(row.get("evidence")) or "INVENTED",
            heuristic_sources=as_list(row.get("source_ids")),
        )
        got = consumers.get(bare, [])
        if not got:
            links.append(Link(**base,
                              blocked_because="no effect reads this field, so it "
                                              "changes nothing a model acts on"))
            continue
        for e, how in got:
            spec = outputs.get(e.output)
            ref = refs.get(spec.reference_dist) if spec else None
            if spec and spec.reference_dist and "{" in spec.reference_dist:
                # Templated: take the first matching family for the label.
                ref = next((r for rid, r in refs.items()
                            if rid.startswith(spec.reference_dist.split("{", 1)[0])),
                           None)
            engine_field = adapter.field_for(e.output) if adapter else e.output
            supports = adapter.supports(e.output) if adapter else True
            why = ""
            if spec and not spec.reference_dist and e.mechanism == "quantile":
                why = ("the output has no published reference distribution, so the "
                       "effect has nothing to read a value off")
            elif not supports:
                why = (adapter.unsupported.get(e.output, "")
                       or "this engine does not read that quantity")
            links.append(Link(
                **base,
                effect=e.id, effect_name=e.name, effect_how=how,
                effect_evidence=e.evidence,
                output=e.output,
                output_name=spec.name if spec else "",
                reference=ref.id if ref else "",
                reference_evidence=ref.evidence if ref else "",
                engine_field=engine_field or "",
                engine_supports=supports and not why,
                blocked_because=why,
            ))
    links.sort(key=lambda link: (not link.reaches_engine,
                                 ORDER.get(link.chain_evidence, 3),
                                 link.heuristic))
    return links


def markdown(links: list[Link], pop: Any, adapter: Any) -> str:
    live = [x for x in links if x.reaches_engine]
    dead = [x for x in links if not x.reaches_engine]
    by_label: dict[str, int] = {}
    for x in live:
        by_label[x.chain_evidence] = by_label.get(x.chain_evidence, 0) + 1

    L = ["# From the literature to a number the model acts on", "",
         f"Engine: **{adapter.name}** (`{adapter.id}`)"
         + (f" · cohort {pop.cohort}" if pop.cohort else "")
         + f" · {len(pop.people)} residents", "",
         f"**{len(live)} of {len(links)} chains reach the engine.** A chain is one "
         f"heuristic, through the persona field it writes, through an effect that "
         f"consumes that field, to a canonical output and the engine's own name for "
         f"it.", "",
         "The label on a chain is its **weakest link**. A value read off a sourced "
         "distribution at a quantile decided by an invented ordering is INVENTED — "
         "reporting it as SOURCED would launder a guess into a citation.", ""]

    if by_label:
        L += ["| end-to-end evidence | chains |", "|---|---|"]
        for lab in ("SOURCED", "ESTIMATE", "INVENTED"):
            if lab in by_label:
                L.append(f"| {lab} | {by_label[lab]} |")
        L.append("")

    L += ["## Chains that reach the engine", "",
          "| heuristic | writes | effect | how | output | engine field | "
          "weakest link |", "|---|---|---|---|---|---|---|"]
    for x in live:
        L.append(
            f"| `{x.heuristic}` {x.heuristic_name} | `{x.field.split('.', 1)[-1]}` "
            f"| `{x.effect}` | {x.effect_how} | {x.output} | `{x.engine_field}` "
            f"| **{x.chain_evidence}** |")
    L.append("")

    if dead:
        L += ["## Chains that stop short", "",
              "Each of these is a heuristic that currently changes nothing the engine "
              "does. That is worth knowing per row rather than in aggregate: some are "
              "waiting on the engine, and some on a number nobody has published.", "",
              "| heuristic | writes | stops because |", "|---|---|---|"]
        for x in dead:
            L.append(f"| `{x.heuristic}` {x.heuristic_name} "
                     f"| `{x.field.split('.', 1)[-1]}` | {x.blocked_because} |")
        L.append("")

    if pop.marginals:
        L += ["## Did the published distributions survive?", "",
              "The quantile mechanism claims the persona decides the ordering while "
              "the literature keeps the shape. This is that claim, measured.", "",
              "| output | reference | published mean | realized | |",
              "|---|---|---|---|---|"]
        for m in pop.marginals:
            mark = "ok" if m["within_1pc"] else "**OFF**"
            L.append(f"| {m['output']} | `{m['reference']}` | {m['published_mean']} "
                     f"| {m['realized_mean']} {m['unit']} | {mark} |")
        L.append("")

    blocked = adapter.unsupported
    if blocked:
        L += [f"## What {adapter.name} cannot use", "",
              "Outputs the compiler produces that this engine has nowhere to put. "
              "Listed rather than dropped, so the gap is attributable to the engine "
              "rather than looking like a gap in the model.", ""]
        for oid, why in sorted(blocked.items()):
            L.append(f"- **{oid}** — {why}")
        L.append("")
    return "\n".join(L)
