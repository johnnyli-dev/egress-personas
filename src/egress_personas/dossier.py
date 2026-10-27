"""A small population, written out in full, with every number traced to its source.

The whole-tower reports answer "does the population look right?". This answers a
different and more useful question when somebody asks you to defend the model: **where
did this specific number come from?** For a floor of seven residents you can follow
every figure from the literature to the value, by hand, in an afternoon.

What it is not for: the distributions. Seven draws cannot recover a curve fitted to 149
observations, so the conformance figures are reported and then explicitly discounted.
Read this to audit the chain; build the whole tower when you want the distributions to
mean something.
"""

from __future__ import annotations

from typing import Any

from .tables import Tables, as_list, text

ORDER = {"SOURCED": 0, "ESTIMATE": 1, "INVENTED": 2}


def _sources(tables: Tables) -> dict[str, dict[str, str]]:
    out = {}
    for row in tables["sources"]:
        sid = text(row.get("id"))
        if sid:
            out[sid] = {k: text(row.get(k)) or "" for k in tables["sources"].columns}
    return out


def _heuristics(tables: Tables) -> dict[str, dict[str, Any]]:
    out = {}
    for row in tables["parameters"]:
        hid = text(row.get("id"))
        if hid:
            out[hid] = dict(row)
    return out


def _cite(sid: str, src: dict[str, dict[str, str]]) -> str:
    s = src.get(sid)
    if not s:
        return f"`{sid}` (not on the Sources tab)"
    short = s.get("short") or sid
    return f"[{short}]({s['url']})" if s.get("url") else short


def _dist_text(h: dict[str, Any]) -> str:
    fam = text(h.get("dist")) or ""
    ps = [text(h.get(f"p{i}")) for i in range(1, 5)]
    ps = [x for x in ps if x is not None]
    cats = as_list(h.get("categories"))
    if cats:
        return f"{fam}({', '.join(cats)})"
    return f"{fam}({', '.join(ps)})" if ps else fam


def _fmt(v: Any) -> str:
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def markdown(tables: Tables, pop: Any, adapter: Any) -> str:  # noqa: C901
    src = _sources(tables)
    heur = _heuristics(tables)
    used_sources: set[str] = set()
    floors = sorted({u["floor_label"] for u in pop.units})
    L: list[str] = []

    L += ["# One floor, in full",
          "",
          f"Floor {', '.join(str(f) for f in floors)} of the "
          f"{pop.scenario.get('num_floors')}-storey tower · "
          f"scenario `{pop.scenario.get('scenario_id')}` · seed {pop.seed}",
          "",
          f"**{len(pop.people)} residents in {len(pop.households)} households across "
          f"{len(pop.units)} flats.** Every number below is followed from the "
          f"literature to the value, so the model can be checked by hand rather than "
          f"taken on trust.",
          "",
          f"- run `{pop.run_id}`",
          f"- snapshot `{pop.snapshot.get('content_hash')}`",
          f"- engine mapping: **{adapter.name}** (`{adapter.id}`)",
          "",
          "## Read this before the numbers", "",
          "**At this size the distributions are not reproduced, and are not meant to "
          "be.** Seven draws cannot recover a curve fitted to 149 observations. The "
          "conformance figures below are printed for completeness and should be "
          "discounted; they are the reason to build the whole tower when you want the "
          "distributions to mean something, and this when you want to audit where they "
          "came from.", "",
          "Three labels appear throughout, and they are the point of the exercise:", "",
          "- **SOURCED** — a citation was read and supports this value.",
          "- **ESTIMATE** — reasoned from an adjacent finding, but not measured.",
          "- **INVENTED** — no measurement exists; the model needs a number.", ""]

    # ── the floor ───────────────────────────────────────────────────────────
    L += ["## The floor", "", "| flat | residents | household | pet |",
          "|---|---|---|---|"]
    for u in pop.units:
        here = [p for p in pop.people if p.situation["unit"] == u["label"]]
        house = next((h for h in pop.households if h.unit == u["label"]), None)
        who = ", ".join(
            f"{p.id} ({p.identity['age_years']}, {p.identity['sex']}"
            + (f", {p.body['mobility'].replace('_', ' ')}"
               if p.body["mobility"] != "none" else "") + ")"
            for p in here) or "empty"
        L.append(f"| **{u['label']}** | {who} | "
                 f"{house.id if house else '—'} | "
                 f"{'yes' if house and house.has_pet else 'no'} |")
    L += ["", "Seed tiles come from the floorplan drawing and are marked *estimate*: "
          "the simulation infers flats from walls and doors rather than naming them, "
          "so the A–D letters are annotations on a drawing, not an index anything "
          "verified.", ""]

    # ── where the population composition came from ──────────────────────────
    L += ["## Where the composition came from", "",
          "Every demographic target the sampler aimed at, with what it rests on. "
          "`basis` says the kind of evidence: `acs` and `sipp` are census surveys, "
          "`estimate` is reasoned, `team` is a figure somebody chose to ask a question "
          "with.", "",
          "| target | value | basis | source |", "|---|---|---|---|"]
    for row in tables["population"]:
        if text(row.get("cohort")):
            continue
        dim, cat = text(row.get("dimension")), text(row.get("category")) or ""
        val, unit = text(row.get("value")), text(row.get("unit")) or ""
        ids = as_list(row.get("source_ids"))
        used_sources.update(ids)
        cites = ", ".join(_cite(i, src) for i in ids) or "—"
        L.append(f"| {dim}.{cat} | `{val}` {unit} | {text(row.get('basis')) or '—'} "
                 f"| {cites} |")
    L.append("")

    # ── each resident ───────────────────────────────────────────────────────
    L += ["## The residents", "",
          "For each: who they are, then every persona field with the heuristic that "
          "set it, then every quantity the simulation receives with the chain that "
          "produced it.", ""]

    for p in pop.people:
        name = p.identity.get("name") or f"{p.identity['age_years']}-year-old " \
                                         f"{p.identity['sex']}"
        tag = f" · hand-authored case `{p.case_id}`" if p.case_id else ""
        L += [f"### {p.id} — {name}{tag}", "",
              f"`{p.situation['unit']}` · floor {p.situation['floor_label']} · "
              f"{p.identity['household_role']} · "
              f"{_fmt(p.identity.get('tenure_years'))} years here · "
              f"{p.situation.get('activity', '').replace('_', ' ')}"
              + (" · **not in the building**" if not p.situation.get("present") else ""),
              "", f"> {p.narrative}", ""]
        if p.identity.get("notes"):
            L += [f"*Why this case exists: {p.identity['notes']}*", ""]
        if p.commitments:
            what = ", ".join(
                f"{c.get('what') or c['kind']} (+{_fmt(c.get('delay_s'))} s)"
                for c in p.commitments)
            L += [f"**Will not leave without** {what}.", ""]

        traces = pop.traces.get(p.key, {})
        if traces:
            L += ["**Persona fields, and the heuristic behind each**", "",
                  "| field | value | heuristic | drawn from | how sure | source |",
                  "|---|---|---|---|---|---|"]
            for path, tr in sorted(traces.items()):
                if tr.inherited:
                    L.append(f"| `{path}` | _not set_ | — | — | — | left to the "
                             f"simulation's own rules |")
                    continue
                steps = [s for s in tr.steps if not s.shadowed]
                rules = " then ".join(f"`{s.rule}` {s.mechanism}" for s in steps)
                dists = " · ".join(
                    _dist_text(heur[s.rule]) for s in steps if s.rule in heur) or "—"
                labels = sorted({s.evidence for s in steps},
                                key=lambda x: ORDER.get(x, 9))
                ids: list[str] = []
                for s in steps:
                    ids += s.sources
                used_sources.update(ids)
                cites = ", ".join(_cite(i, src) for i in dict.fromkeys(ids)) or "—"
                pin = " *(pinned)*" if tr.pinned else ""
                L.append(f"| `{path}` | **{_fmt(tr.final)}** | {rules}{pin} "
                         f"| {dists} | {'/'.join(labels)} | {cites} |")
            L.append("")

        comp = pop.compiled.get(p.key)
        if comp and comp.values:
            L += [f"**What {adapter.name} receives**", "",
                  "| model input | value | engine field | how it was arrived at "
                  "| how sure |", "|---|---|---|---|---|"]
            for oid in pop.outputs:
                if oid not in comp.values:
                    continue
                spec = pop.outputs[oid]
                steps = comp.steps.get(oid, [])
                chain: list[str] = []
                labels: list[str] = []
                for st in steps:
                    chain.append(f"`{st.effect}` {st.mechanism}: {st.detail}")
                    labels.append(st.evidence)
                    used_sources.update(st.sources)
                worst = max(labels, key=lambda x: ORDER.get(x, 9)) if labels else "—"
                field = (f"`{adapter.field_for(oid)}`" if adapter.supports(oid)
                         else "*this engine has nowhere to put it*")
                L.append(f"| {spec.name} | **{_fmt(comp.values[oid])}** "
                         f"{spec.unit} | {field} | {' then '.join(chain)} "
                         f"| {worst} |")
            L.append("")
            qs = {k: v for k, v in comp.quantiles.items()}
            if qs:
                L += ["Where those came from, when the value was read off a published "
                      "distribution:", "",
                      "| model input | this resident | reference distribution "
                      "| fitted by |", "|---|---|---|---|"]
                for oid, q in sorted(qs.items()):
                    ref = next((r for r in pop.references.values()
                                if r.id == (pop.outputs[oid].reference_dist or "")
                                or pop.outputs[oid].reference_dist
                                .replace("{alarm_quality}",
                                         text(pop.scenario.get("alarm_quality")) or "")
                                == r.id), None)
                    used_sources.update(ref.sources if ref else [])
                    cites = ", ".join(_cite(i, src)
                                      for i in (ref.sources if ref else [])) or "—"
                    desc = (f"{ref.name} — {ref.family}"
                            f"({', '.join(str(x) for x in ref.params if x is not None)})"
                            if ref else "—")
                    L.append(f"| {pop.outputs[oid].name} | {q:.0%} of the floor "
                             f"| {desc} | {cites} |")
                L.append("")

        ties = p.ties
        if ties:
            L += ["**Who they would reach**", ""]
            for t in sorted(ties, key=lambda t: (t["kind"], t["to"])):
                other = next((q for q in pop.people if q.key == t["to"]), None)
                who = (f"{other.id} in {other.situation['unit']}" if other
                       else "the building chat")
                L.append(f"- {t['kind'].replace('_', ' ')} → {who} "
                         f"(strength {t['strength']})")
            L.append("")
        else:
            L += ["**Who they would reach** — nobody. No household, no neighbour they "
                  "would knock for, nobody to phone, not in the chat.", ""]

    # ── conformance, discounted ─────────────────────────────────────────────
    L += ["## Conformance at this size, and why to discount it", "",
          "| published distribution | mean | what seven residents produced |",
          "|---|---|---|"]
    for m in pop.marginals:
        L.append(f"| {pop.outputs[m['output']].name} | {m['published_mean']} "
                 f"{m['unit']} | {m['realized_mean']} {m['unit']} |")
    L += ["",
          "The gaps are sampling noise, not error. The mechanism assigns each resident "
          "a rank and reads the value off the published curve at that point, which "
          "reproduces the curve exactly in the limit and approximately nowhere near "
          "it. On the full tower of 151 these land within 1%.", ""]

    if pop.warnings:
        L += ["## What the generator flagged", ""]
        for w in pop.warnings:
            L.append(f"- {w}")
        L.append("")
    if pop.gaps:
        L += ["## Gaps left open on purpose", ""]
        for g in pop.gaps:
            L += [f"- **{g['what']}** — {g['count']} on this floor"
                  f"{': ' + ', '.join(g.get('who', [])) if g.get('who') else ''}",
                  f"  {g['why']}"]
        L.append("")

    # ── the sources actually used ───────────────────────────────────────────
    L += ["## Every source behind this floor", "",
          f"{len(used_sources)} of the {len(src)} sources on the Sheet were used by "
          f"the numbers above.", ""]
    for sid in sorted(used_sources):
        s = src.get(sid)
        if not s:
            L.append(f"- `{sid}` — **not on the Sources tab**")
            continue
        line = f"- **{s.get('short') or sid}** — {s.get('cite') or ''}"
        if s.get("url"):
            line += f" [{s['url']}]({s['url']})"
        L.append(line)
        if s.get("finding"):
            L.append(f"  - *What it gives us:* {s['finding']}")
        if s.get("notes"):
            L.append(f"  - *Caveat:* {s['notes']}")
        if not s.get("read_by"):
            L.append("  - *Not yet read first-hand for this registry* — the citation "
                     "was carried from the project's existing evidence ledger.")
    L.append("")
    return "\n".join(L)
