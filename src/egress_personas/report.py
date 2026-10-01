"""The human read of a generated population.

Ordered so the things most likely to be wrong come first: parameters that matched
nobody (almost always a broken applies_to), then targets that missed, then the gaps
and repairs. Good news is further down.
"""

from __future__ import annotations

from . import ties as tie_mod
from .sample import Population


def _bar(x: float, width: int = 24, scale: float = 1.0) -> str:
    n = int(round(max(0.0, min(x / scale, 1.0)) * width))
    return "#" * n + "." * (width - n)


def markdown(pop: Population) -> str:  # noqa: C901 - a report is a list of sections
    people = pop.people
    n = max(len(people), 1)
    L: list[str] = []
    sc = pop.scenario

    L += [
        f"# {sc.get('scenario_id')} — seed {pop.seed}",
        "",
        f"- run `{pop.run_id}`",
        f"- snapshot `{pop.snapshot.get('content_hash')}`",
        f"- {sc.get('time_of_day')}, {sc.get('alarm_quality')} alarm, "
        f"fire on floor {sc.get('fire_floor_label') or '-'}, plan {sc.get('plan_id')}",
        f"- {len(people)} residents in {len(pop.households)} households across "
        f"{len(pop.units)} flats",
        "",
    ]

    unmatched = [w for w in pop.warnings if "matched no persona" in w]
    L += ["## Things to look at first", ""]
    if unmatched:
        L += [f"**{len(unmatched)} parameter row(s) matched nobody.** A row that matches "
              f"nobody is almost always a broken `applies_to`, not a row that does "
              f"nothing.", ""]
        L += [f"- {w}" for w in unmatched] + [""]
    by_cases = [c for c in pop.conformance
                if c["within"] is False and c.get("explained_by_cases")]
    missed = [c for c in pop.conformance
              if c["within"] is False and c.get("noise") is not True
              and not c.get("explained_by_cases")]
    noisy = [c for c in pop.conformance
             if c["within"] is False and c.get("noise") is True
             and not c.get("explained_by_cases")]
    if missed:
        L += [f"**{len(missed)} target(s) missed by more than sampling noise.** These "
              f"are the ones to act on.", ""]
        for c in missed:
            z = "" if c.get("z") is None else f", {abs(c['z']):.1f} standard errors out"
            L.append(f"- {c['dimension']}.{c['category']}: wanted {c['target']} "
                     f"±{c['tolerance']}, got {c['realized']}{z}")
        L.append("")
    if noisy:
        L += [f"{len(noisy)} target(s) are outside their tolerance but within two "
              f"standard errors of it — that is a small building, not a biased "
              f"sampler. One resident is "
              f"{1 / max(len(pop.people), 1) * 100:.1f} percentage points here.", ""]
        for c in noisy:
            L.append(f"- {c['dimension']}.{c['category']}: wanted {c['target']} "
                     f"±{c['tolerance']}, got {c['realized']} over "
                     f"{c['measured_over']} people (±{c['stderr']} per standard error)")
        L.append("")
    if by_cases:
        L += [f"{len(by_cases)} target(s) are outside tolerance **because of the "
              f"hand-authored cases**, and land inside it once those are taken out. "
              f"One authored persona is "
              f"{1 / max(len(pop.people), 1) * 100:.1f} percentage points of the "
              f"building, and rather more of a subgroup — so this is a decision "
              f"somebody made, not a fault in the sampler.", ""]
        for c in by_cases:
            L.append(f"- {c['dimension']}.{c['category']}: wanted {c['target']}, got "
                     f"{c['realized']} with the cases and "
                     f"{c['realized_excluding_cases']} without "
                     f"({c['cases_in_category']} of the {c['cases_in_base']} "
                     f"case personas in this group)")
        L.append("")
    if pop.gaps:
        L += ["**Gaps left open on purpose.**", ""]
        for g in pop.gaps:
            L += [f"- {g['what']} — {g['count']}: {', '.join(g.get('who', [])) or '-'}",
                  f"  {g['why']}"]
        L.append("")
    other = [w for w in pop.warnings if "matched no persona" not in w]
    if other:
        L += ["**Other warnings.**", ""] + [f"- {w}" for w in other] + [""]
    if pop.notes:
        L += ["**Notes.**", ""] + [f"- {w}" for w in pop.notes] + [""]
    if pop.inapplicable:
        L += [f"{len(pop.inapplicable)} parameter row(s) are gated on a scenario "
              f"setting this scenario does not have, so they correctly matched nobody:",
              ""] + [f"- {w}" for w in pop.inapplicable] + [""]
    if not (unmatched or missed or pop.gaps or other):
        L += ["Nothing. Every parameter matched somebody, every target landed inside "
              "its tolerance, and no gap was left open.", ""]

    L += ["## Targets against what was drawn", "",
          "| target | want | got | without cases | tol | over | s.e. | z | |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in pop.conformance:
        if c["within"] is None:
            mark = ""
        elif c["within"]:
            mark = "ok"
        elif c.get("noise") is True:
            mark = "noise"
        else:
            mark = "**OFF**"
        tol = "" if c["tolerance"] is None else f"±{c['tolerance']}"
        if c["within"] is False and c.get("explained_by_cases"):
            mark = "cases"
        excl = c.get("realized_excluding_cases")
        L.append(f"| {c['dimension']}.{c['category']} | {c['target']} | "
                 f"{c['realized']} | {excl if excl is not None else ''} | {tol} | "
                 f"{c.get('measured_over', '')} | "
                 f"{c.get('stderr') or ''} | {c.get('z') if c.get('z') is not None else ''} "
                 f"| {mark} |")
    L += ["",
          "`z` is how many standard errors the drawn share sits from its target, so a "
          "row marked `noise` is one where the building is too small to pin the share "
          "any tighter, and one marked `cases` is one the hand-authored personas moved. "
          "`**OFF**` means the sampler really is off.",
          ""]
    L += [f"Household sizes were tilted by theta = {pop.theta:.4f} to reach "
          f"{pop.targets.persons_per_flat} people per flat "
          f"({' / '.join(f'{w * 100:.1f}' for w in pop.tilted)} % for sizes 1-4). "
          f"Theta = 1 would mean the census weights already agreed with the occupancy "
          f"target; they do not, and this is where that disagreement is resolved.",
          ""]

    sizes: dict[int, int] = {}
    for h in pop.households:
        sizes[len(h.members)] = sizes.get(len(h.members), 0) + 1
    L += ["## Households", "", "| size | households | |", "|---|---|---|"]
    worst = max(sizes.values()) if sizes else 1
    for k in sorted(sizes):
        L.append(f"| {k} | {sizes[k]} | `{_bar(sizes[k], 20, worst)}` |")
    L.append("")

    L += ["## Who is in the building", "", "| | count | share |", "|---|---|---|"]
    types: dict[str, int] = {}
    for p in people:
        t = p.body.get("sim_agent_type", "?")
        types[t] = types.get(t, 0) + 1
    for t, c in sorted(types.items(), key=lambda kv: -kv[1]):
        L.append(f"| {t} | {c} | {c / n:.1%} |")
    mob: dict[str, int] = {}
    for p in people:
        m = p.body.get("mobility", "?")
        mob[m] = mob.get(m, 0) + 1
    for m, c in sorted(mob.items(), key=lambda kv: -kv[1]):
        if m != "none":
            L.append(f"| mobility: {m} | {c} | {c / n:.1%} |")
    L += [f"| asleep at t=0 | {sum(1 for p in people if p.situation.get('asleep'))} | "
          f"{sum(1 for p in people if p.situation.get('asleep')) / n:.1%} |",
          f"| cannot hear the alarm | "
          f"{sum(1 for p in people if p.situation.get('alarm_audible') is False)} | "
          f"{sum(1 for p in people if p.situation.get('alarm_audible') is False) / n:.1%} |",
          ""]

    L += ["## The makeup of the building", "",
          "Fuller distributions, crosstabs and what they do to an evacuation: "
          "`personas distributions`"
          + (f" --cohort {pop.cohort}" if pop.cohort else "") + ".", ""]
    from .distributions import distributions as _dists
    for key in ("age", "mobility", "base_speed", "ties"):
        d = _dists(pop)[key]
        bits = " · ".join(f"{k} {v}" for k, v in d.counts.items() if v)
        stat = f" (mean {d.mean:.2f} {d.unit})" if d.mean is not None else ""
        L.append(f"- **{d.name}**{stat}: {bits}")
    L.append("")

    L += ["## Floor by floor", ""]
    per_floor: dict[int, int] = {}
    for p in people:
        f = p.situation.get("floor_label")
        per_floor[f] = per_floor.get(f, 0) + 1
    worst = max(per_floor.values()) if per_floor else 1
    for f in sorted(per_floor):
        L.append(f"- floor {f:>2}: {per_floor[f]:>2}  `{_bar(per_floor[f], 20, worst)}`")
    L.append("")

    L += ["## Ties", "",
          "| rule | kind | scope | stated | as | realized rate | per person | "
          "eligible | edges |",
          "|---|---|---|---|---|---|---|---|---|"]
    for s in pop.tie_stats:
        kind = "per pair" if s.get("rate_kind") == "per_pair" else "per person"
        L.append(f"| {s['rule']} | {s['kind']} | {s['scope']} | {s['rate']} | {kind} | "
                 f"{s['realized']:.4f} | {s.get('realized_degree', '-')} | "
                 f"{s.get('eligible_people', '-')} | {s['edges']} |")
    L.append("")
    deg = tie_mod.degree_summary(people)
    L += ["| kind | mean ties per resident | most | share with any |",
          "|---|---|---|---|"]
    for kind, d in sorted(deg.items()):
        L.append(f"| {kind} | {d['mean_over_all']} | {int(d['max'])} | "
                 f"{d['share_with_any']:.1%} |")
    alone = sum(1 for p in people if not p.ties)
    L += ["", f"{alone} resident(s) have no tie of any kind — nobody in the flat, no "
          f"neighbour they would knock for, nobody to phone, not in the chat.", ""]

    L += ["## Parameters", "", "| id | target | matched | evidence |",
          "|---|---|---|---|"]
    ev: dict[str, str] = {}
    tgt: dict[str, str] = {}
    for p in people:
        for path, tr in pop.traces.get(p.key, {}).items():
            for s in tr.steps:
                ev.setdefault(s.rule, s.evidence)
                tgt.setdefault(s.rule, path)
    for rid in sorted(set(pop.matched) | set(ev)):
        L.append(f"| {rid} | {tgt.get(rid, '-')} | {pop.matched.get(rid, 0)} | "
                 f"{ev.get(rid, '-')} |")
    clamped = sum(1 for m in pop.traces.values() for t in m.values() if t.clamped)
    shadowed = sum(1 for m in pop.traces.values() for t in m.values()
                   for s in t.steps if s.shadowed)
    inherited = sorted({path for m in pop.traces.values()
                        for path, t in m.items() if t.inherited})
    L += ["",
          f"{clamped} value(s) hit a field bound; {shadowed} contribution(s) were "
          f"shadowed by a higher-priority `set` or by a hand-authored case.", ""]
    if inherited:
        L += [f"Left to the simulation's own rules (no row sets them): "
              f"{', '.join(inherited)}.", ""]

    if pop.repairs:
        L += ["## Repairs", "",
              "Deterministic nudges to bring a realized share inside tolerance. "
              "Hand-authored cases are never touched.", ""]
        for r in pop.repairs:
            L.append(f"- {r['who']}: {r['change']}")
        L.append("")

    L += ["## Three personas in full", ""]
    picks = [people[0], people[len(people) // 2], people[-1]] if len(people) >= 3 else people
    for p in picks:
        L += [f"### {p.id} — {p.situation.get('unit')} "
              f"({p.case_id or 'sampled'})", "", p.narrative, "",
              "| field | value | from |", "|---|---|---|"]
        for path, tr in sorted(pop.traces.get(p.key, {}).items()):
            if tr.inherited:
                L.append(f"| {path} | _inherited_ | the simulation's rules |")
                continue
            chain = " then ".join(
                f"{s.rule} {s.mechanism}" for s in tr.steps if not s.shadowed)
            L.append(f"| {path} | {tr.final} | {chain} |")
        L.append("")

    L += ["## A note on the seed tiles", "",
          "Each flat carries a seed tile rather than a flat index. The simulation has "
          "no unit names: it infers flats from walls and doors and numbers them "
          "row-major, and its own inspector finds twelve compartments on this plan, not "
          "four — so the A/B/C/D letters are annotations on a drawing, not an index we "
          "can rely on. Every `seed_tile` here is marked `estimate` for that reason.",
          ""]
    return "\n".join(L)

# ── the makeup of the building ───────────────────────────────────────────────

def _hist(counts: dict[str, int], width: int = 34) -> list[str]:
    """A bar per category, scaled to the largest, with the count and share beside it."""
    total = sum(counts.values()) or 1
    worst = max(counts.values()) if counts else 1
    out = []
    label_w = max((len(k) for k in counts), default=4)
    for k, v in counts.items():
        bar = "#" * int(round(v / worst * width)) if worst else ""
        out.append(f"  {k:<{label_w}}  {v:>4}  {v / total:>5.1%}  {bar}")
    return out


def _crosstab_md(ct: dict, label: str) -> list[str]:
    cols = ct["cols"]
    L = [f"| {label} | " + " | ".join(cols) + " | all |",
         "|" + "|".join(["---"] * (len(cols) + 2)) + "|"]
    for r in ct["rows"]:
        cells = [str(ct["cells"][r].get(c, 0) or "·") for c in cols]
        L.append(f"| {r} | " + " | ".join(cells) + f" | {ct['row_totals'][r]} |")
    totals = [str(sum(ct["cells"][r].get(c, 0) for r in ct["rows"])) for c in cols]
    L.append("| **all** | " + " | ".join(totals) + f" | {ct['total']} |")
    return L


def distributions_markdown(pop: Population) -> str:
    """The makeup of one building, on its own, as a page you can read."""
    from .distributions import crosstabs, distributions, egress_drivers

    which = pop.cohort_name if pop.cohort else "the base building"
    L = ["# What this building is made of", "",
         f"**{which}**"
         + (f" (`{pop.cohort}`)" if pop.cohort else "")
         + f" · {pop.scenario.get('scenario_id')} · seed {pop.seed}", ""]
    if pop.cohort_question:
        L += [f"> {pop.cohort_question}", ""]
    L += [f"{len(pop.people)} residents in {len(pop.households)} households across "
          f"{len(pop.units)} flats."
          + ("" if pop.include_cases
             else " The hand-authored cases are left out of this cohort, so what you "
                  "see is the distribution and nothing else."),
          ""]

    dists = distributions(pop)
    L += ["## Distributions", ""]
    for key in ("age", "age_band", "sex", "mobility", "agent_type", "household_size",
                "household_role", "tenure", "base_speed", "familiarity", "mill",
                "ties", "activity"):
        d = dists[key]
        head = f"**{d.name}**"
        stats = []
        if d.mean is not None:
            stats.append(f"mean {d.mean:.2f}")
        if d.median is not None:
            stats.append(f"median {d.median:.2f}")
        if d.p5 is not None and d.p95 is not None:
            stats.append(f"5th–95th {d.p5:.2f}–{d.p95:.2f}")
        if stats:
            head += f" — {', '.join(stats)} {d.unit}"
        L += [head, "", "```"] + _hist(d.counts) + ["```", ""]

    L += ["## Crosstabs", "",
          "A marginal share can be right while the joint distribution is wrong: the "
          "building can hold the right number of over-65s and the wrong number of them "
          "living alone.", ""]
    ct = crosstabs(pop)
    for key, label, note in (
        ("age_by_mobility", "age / mobility",
         "Mobility is drawn conditioned on age, so this table is where that shows."),
        ("age_by_sex", "age / sex", ""),
        ("age_by_living_alone", "age / household",
         "Somebody living alone has nobody in the flat to wake them or wait for them."),
        ("mobility_by_help", "mobility / help",
         "Of those who do not walk freely, who has somebody in the flat. The last "
         "column is the gap the simulation cannot close either."),
    ):
        L += [f"**{label}**", ""]
        if note:
            L += [note, ""]
        L += _crosstab_md(ct[key], label.split(" / ")[0]) + [""]

    L += ["## What this does to an evacuation", "",
          "Inputs to RSET, not RSET. Nothing here simulates anything; these are the "
          "quantities the simulation reads, grouped by which half of the split they "
          "land on.", "",
          "| | driver | value | why it matters |", "|---|---|---|---|"]
    for d in egress_drivers(pop):
        L.append(f"| {d['phase']} | {d['what']} | **{d['value']}** {d['unit']} "
                 f"| {d['why']} |")
    L.append("")
    return "\n".join(L)
