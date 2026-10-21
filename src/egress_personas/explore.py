"""A self-contained page for browsing a sampled population.

The population JSON is a good contract and a poor thing to read. What you want to ask
of it — show me somebody, who would they knock for, who would reach them, where in the
tower do their ties live — is a question about a graph, and a graph wants drawing.

`write_explorer` embeds the population, a compact provenance index and the source list
into one HTML file with no external data, so it can be opened from disk, committed, or
sent to somebody who does not have the repository.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

from .sample import Population, VERSION
from .show import FILTERS
from .tables import Tables, text

TEMPLATE = Path(__file__).with_name("explorer.html")

#: Fields not worth an entry in the provenance index: they are derived, not drawn.
SKIP_PROV = ("mobility", "sim_agent_type", "can_use_stairs", "escorts", "escorted_by")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def payload(pop: Population, tables: Tables | None = None,
            generated_at: str | None = None) -> dict[str, Any]:
    """Everything the page needs, and nothing it does not."""
    from .emit import population_json

    js = population_json(pop, generated_at=generated_at or _now())

    # A compact provenance index: which rows produced each number, how sure we are, and
    # what to cite. The full sidecar is ten times this size and says the same thing at
    # a level of detail a page cannot show.
    prov: dict[str, dict[str, Any]] = {}
    for person in pop.people:
        fields: dict[str, Any] = {}
        for path, tr in sorted(pop.traces.get(person.key, {}).items()):
            name = path.split(".", 1)[1]
            if name in SKIP_PROV:
                continue
            if tr.inherited:
                fields[path] = {"inherited": True}
                continue
            steps = [s for s in tr.steps if not s.shadowed]
            fields[path] = {
                "v": tr.final,
                "pinned": tr.pinned or None,
                "chain": [{"r": s.rule, "m": s.mechanism, "ev": s.evidence}
                          for s in steps],
                "src": sorted({x for s in steps for x in s.sources}),
            }
        prov[person.key] = fields

    sources: dict[str, Any] = {}
    if tables is not None:
        for row in tables["sources"]:
            sid = text(row.get("id"))
            if sid:
                sources[sid] = {
                    "short": text(row.get("short")) or sid,
                    "cite": text(row.get("cite")) or "",
                    "url": text(row.get("url")) or "",
                }

    subsets = {
        name: {"what": what,
               "keys": [p.key for p in pop.people if test(p)]}
        for name, (what, test) in FILTERS.items()
    }

    rules = {}
    if tables is not None:
        for row in tables["parameters"]:
            rid = text(row.get("id"))
            if rid:
                rules[rid] = {
                    "name": text(row.get("name")) or rid,
                    "finding": text(row.get("finding")) or "",
                }

    # Every building's makeup, so the page can compare them without a second file.
    # Only the composition travels, not each cohort's personas: the distributions are a
    # few kilobytes each, where six full populations would be megabytes.
    from .distributions import makeup
    from .households import cohort_ids
    from .sample import sample as _sample

    makeups: list[dict[str, Any]] = [_slim(makeup(pop))]
    if tables is not None:
        for cid in cohort_ids(tables):
            try:
                other = _sample(tables, str(pop.scenario.get("scenario_id")),
                                pop.seed, cohort=cid)
            except (KeyError, ValueError):
                continue
            makeups.append(_slim(makeup(other)))

    # What a simulation actually gets, and the chain behind each number. This is the
    # half of the page that demonstrates the compile layer rather than the population.
    from . import adapters as ad
    from . import trace as tr

    adapter = None
    try:
        adapter = ad.resolve("fire_egress_3d")
    except (KeyError, FileNotFoundError):
        try:
            adapter = ad.resolve("generic")
        except (KeyError, FileNotFoundError):
            adapter = None

    model: dict[str, Any] = {}
    if pop.compiled and adapter is not None:
        links = tr.build(tables, pop, adapter) if tables is not None else []
        live = [x for x in links if x.reaches_engine]
        split: dict[str, int] = {}
        for x in live:
            split[x.chain_evidence] = split.get(x.chain_evidence, 0) + 1
        model = {
            "adapter": adapter.id,
            "adapter_name": adapter.name,
            "outputs": {
                oid: {
                    "name": o.name, "unit": o.unit, "dtype": o.dtype,
                    "phase": o.phase, "what": o.what,
                    "reference": o.reference_dist or "",
                    "engine_field": adapter.field_for(oid),
                    "engine_supports": adapter.supports(oid),
                    "blocked_because": adapter.unsupported.get(oid, ""),
                }
                for oid, o in pop.outputs.items()
            },
            "references": {
                r.id: {"name": r.name, "family": r.family,
                       "params": [x for x in r.params if x is not None],
                       "evidence": r.evidence, "sources": list(r.sources),
                       "finding": r.finding,
                       "published_mean": r.mean_estimate()}
                for r in pop.references.values()
            },
            "effects": {
                e.id: {"name": e.name, "output": e.output,
                       "mechanism": e.mechanism, "evidence": e.evidence,
                       "finding": e.finding,
                       "terms": [[n, w] for n, w in e.terms]}
                for e in pop.effects
            },
            "marginals": pop.marginals,
            "chains": {"reaching": len(live), "total": len(links), "split": split},
            "stops_short": [
                {"heuristic": x.heuristic, "name": x.heuristic_name,
                 "field": x.field.split(".", 1)[-1], "why": x.blocked_because}
                for x in links if not x.reaches_engine
            ],
            "per_persona": {
                p.key: {
                    "values": pop.compiled[p.key].values,
                    "quantiles": pop.compiled[p.key].quantiles,
                    "steps": {
                        oid: [{"effect": st.effect, "mechanism": st.mechanism,
                               "detail": st.detail, "evidence": st.evidence,
                               "sources": st.sources}
                              for st in steps]
                        for oid, steps in pop.compiled[p.key].steps.items()
                    },
                }
                for p in pop.people if p.key in pop.compiled
            },
        }

    return {
        "meta": js["meta"],
        "makeups": makeups,
        "model": model,
        "units": js["units"],
        "households": js["households"],
        "groups": js["groups"],
        "people": js["personas"],
        "prov": prov,
        "sources": sources,
        "rules": rules,
        "subsets": subsets,
        "theta": round(pop.theta, 4),
        "generator": f"egress-personas {VERSION}",
    }


def _slim(m: dict[str, Any]) -> dict[str, Any]:
    """A makeup trimmed to what a chart needs: the conformance prose is not drawn."""
    return {
        "cohort": m["cohort"],
        "cohort_name": m["cohort_name"],
        "question": m["question"],
        "residents": m["residents"],
        "households": m["households"],
        "distributions": m["distributions"],
        "crosstabs": m["crosstabs"],
        "egress_drivers": [
            {k: d[k] for k in ("key", "phase", "what", "value", "raw", "unit", "why")}
            for d in m["egress_drivers"]
        ],
    }


def render(pop: Population, tables: Tables | None = None, *,
           standalone: bool = True, generated_at: str | None = None) -> str:
    """The page. `standalone` wraps it in a document that opens from disk."""
    body = TEMPLATE.read_text(encoding="utf-8")
    blob = json.dumps(payload(pop, tables, generated_at), separators=(",", ":"))
    # A JSON island inside a script tag must not contain the closing sequence.
    blob = blob.replace("</", "<\\/")
    body = body.replace("__PAYLOAD__", blob)
    if not standalone:
        return body
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, "
        "viewport-fit=cover\">\n"
        "<style>\n"
        ":root{color-scheme:light dark;padding-top:env(safe-area-inset-top,0px);"
        "padding-bottom:env(safe-area-inset-bottom,0px)}\n"
        "body{margin:0;font:14px system-ui,sans-serif;background:#fafafa}\n"
        "img{max-width:100%}[hidden]{display:none!important}\n"
        "</style>\n</head>\n<body>\n" + body + "\n</body>\n</html>\n"
    )


def write_explorer(pop: Population, out_file: Path | None = None, *,
                   tables: Tables | None = None,
                   generated_at: str | None = None) -> Path:
    if out_file is None:
        out_file = Path("out") / (
            f"{pop.scenario.get('scenario_id')}-{pop.seed}.explorer.html")
    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(render(pop, tables, generated_at=generated_at),
                        encoding="utf-8")
    return out_file
