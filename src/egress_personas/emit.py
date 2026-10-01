"""Writing the population out.

Two files, deliberately. The population JSON is the contract a loader reads and
stays lean; the provenance JSON is where every number's derivation lives. The
simulation's config structs reject fields they do not declare, so a fat provenance
block inside each persona would force the Rust side to declare and carry a structure
it has no use for.

Every field of `body` is optional and absent means "the simulation's own rules
decide". That is what keeps a sheet that knows nothing about, say, stair recovery
from flattening a fitted distribution.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

from .persona import FIELDS
from .sample import Population, VERSION

SCHEMA_VERSION = "1.0.0"

#: Kept out of the `body` block the simulation reads: these are our bookkeeping.
BODY_INTERNAL = ("escorts", "escorted_by", "sim_agent_type", "mobility")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def population_json(pop: Population, *, generated_at: str | None = None) -> dict[str, Any]:
    people = pop.people
    counts = {
        "units": len(pop.units),
        "occupied_units": sum(1 for u in pop.units if u["state"] == "occupied"),
        "all_absent_units": sum(1 for u in pop.units if u["state"] == "all_absent"),
        "vacant_units": sum(1 for u in pop.units if u["state"] == "vacant"),
        "households": len(pop.households),
        "personas": len(people),
        "cases": sum(1 for p in people if p.case_id),
        "present": sum(1 for p in people if p.situation.get("present")),
        "absent": sum(1 for p in people if not p.situation.get("present")),
        "wheelchair": sum(1 for p in people if p.body.get("mobility") == "wheelchair"),
        "caregivers": sum(1 for p in people if p.body.get("escorts")),
        "unpaired_wheelchair": sum(
            g["count"] for g in pop.gaps
            if g["what"].startswith("a wheelchair user")),
    }
    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "generator": f"egress-personas {VERSION}",
            "generated_at": generated_at or _now(),
            "run_id": pop.run_id,
            # Deliberately no `pulled_at`: when the data is unchanged the output must
            # be too, and a fetch timestamp would churn every file on every pull.
            # data/snapshot.json keeps it.
            "snapshot": {
                "content_hash": pop.snapshot.get("content_hash"),
                "sheet_id": pop.snapshot.get("sheet_id"),
            },
            "cohort": {
                "id": pop.cohort or None,
                "name": pop.cohort_name or None,
                "question": pop.cohort_question or None,
                "includes_cases": pop.include_cases,
            },
            "scenario": {
                "id": pop.scenario.get("scenario_id"),
                "plan_id": pop.scenario.get("plan_id"),
                "building_json": pop.scenario.get("building_json") or None,
                "num_floors": int(pop.scenario.get("num_floors") or 0),
                "time_of_day": pop.scenario.get("time_of_day"),
                "alarm_quality": pop.scenario.get("alarm_quality"),
                "fire_floor_label": (int(pop.scenario["fire_floor_label"])
                                     if pop.scenario.get("fire_floor_label") else None),
            },
            "seed": pop.seed,
            "counts": counts,
        },
        "vocab": {
            "sim_agent_type": ["adult", "child", "elderly", "athletic", "wheelchair",
                               "visitor", "caregiver"],
            "sex": ["female", "male", "other"],
            "mobility": ["none", "ambulatory_difficulty", "walker_cane", "wheelchair"],
            "household_role": ["head", "partner", "child", "parent", "lodger",
                               "carer", "other"],
            "tie_kind": ["household", "knock", "phone", "group_chat"],
        },
        "units": [
            {
                "label": u["label"], "floor_label": u["floor_label"],
                "sim_floor": u["sim_floor"], "letter": u["letter"],
                "seed_tile": u["seed_tile"], "state": u["state"],
                "household": u["household"],
                "seed_tile_confidence": "estimate",
            }
            for u in pop.units
        ],
        "households": [
            {
                "id": h.id, "unit": h.unit, "floor_label": h.floor_label,
                "sim_floor": h.sim_floor, "size": len(h.members),
                "first_index": h.first_index, "member_indices": h.member_indices,
                "members": h.members, "has_pet": h.has_pet, "pinned": h.pinned,
            }
            for h in pop.households
        ],
        "groups": pop.groups,
        "personas": [_persona_json(p) for p in people],
    }
    return out


def _persona_json(p: Any) -> dict[str, Any]:
    body = {k: v for k, v in p.body.items()
            if k not in BODY_INTERNAL and v is not None}
    rec: dict[str, Any] = {
        "id": p.id,
        "key": p.key,
        "index": p.index,
        "case_id": p.case_id or None,
        "identity": {
            "name": p.identity.get("name"),
            "age_years": p.identity.get("age_years"),
            "age_band": p.identity.get("age_band"),
            "sex": p.identity.get("sex"),
            "household_role": p.identity.get("household_role"),
            "tenure_years": p.identity.get("tenure_years"),
        },
        "sim": {
            "agent_type": p.body.get("sim_agent_type"),
            "gender": p.identity.get("sex"),
            "mobility": p.body.get("mobility"),
            "escorts": p.body.get("escorts"),
            "escorted_by": p.body.get("escorted_by"),
        },
        "body": body,
        "situation": {
            "unit": p.situation.get("unit"),
            "floor_label": p.situation.get("floor_label"),
            "sim_floor": p.situation.get("sim_floor"),
            "home_tile": p.situation.get("home_tile"),
            "present": p.situation.get("present"),
            "asleep": p.situation.get("asleep"),
            "activity": p.situation.get("activity"),
            "alarm_audible": p.situation.get("alarm_audible"),
        },
        "knowledge": dict(sorted(p.knowledge.items())),
        "dispositions": dict(sorted(p.dispositions.items())),
        "commitments": p.commitments,
        "ties": p.ties,
        "household": p.household,
        "household_index": p.household_index,
        "narrative": p.narrative,
        "notes": p.identity.get("notes") or "",
    }
    return rec


def provenance_json(pop: Population) -> dict[str, Any]:
    agents: dict[str, Any] = {}
    for p in pop.people:
        fields: dict[str, Any] = {}
        for path, trace in sorted(pop.traces.get(p.key, {}).items()):
            if trace.inherited:
                fields[path] = {
                    "inherited": True,
                    "why": "no parameter row sets this, so the simulation's own "
                           "rules decide it and the field is not emitted",
                }
                continue
            fields[path] = {
                "final": trace.final,
                "clamped": trace.clamped,
                "pinned": trace.pinned,
                "unit": FIELDS[path].unit,
                "steps": [
                    {
                        "rule": s.rule, "mechanism": s.mechanism, "dist": s.dist,
                        "drawn": s.drawn, "result": s.result,
                        "evidence": s.evidence, "sources": s.sources,
                        "why": s.why, "draw_path": s.draw_path,
                        **({"shadowed": True} if s.shadowed else {}),
                    }
                    for s in trace.steps
                ],
            }
        agents[p.key] = fields
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": pop.run_id,
        "snapshot": {"content_hash": pop.snapshot.get("content_hash")},
        "seed": pop.seed,
        "derived": {
            "household_size_theta": round(pop.theta, 6),
            "household_size_weights": [round(w, 6) for w in pop.tilted],
            "occupancy_target_persons_per_flat": pop.targets.persons_per_flat,
            "child_slot_scale": round(pop.child_scale, 4),
            "tenure_band_scales": {k: round(v, 4)
                                   for k, v in sorted(pop.tenure_scales.items())},
        },
        "conformance": pop.conformance,
        "ties": pop.tie_stats,
        "repairs": pop.repairs,
        "gaps": pop.gaps,
        "warnings": pop.warnings,
        "notes": pop.notes,
        "not_applicable_to_this_scenario": pop.inapplicable,
        "parameters_matched": dict(sorted(pop.matched.items())),
        "personas": agents,
    }


def cards_markdown(pop: Population) -> str:
    lines = [
        f"# Persona cards — {pop.scenario.get('scenario_id')}, seed {pop.seed}",
        "",
        f"{len(pop.people)} residents. Rendered from the structured blocks, so the "
        f"same snapshot and seed give the same words.",
        "",
    ]
    floor = None
    for p in pop.people:
        f = p.situation.get("floor_label")
        if f != floor:
            floor = f
            lines += [f"## Floor {floor}", ""]
        who = p.identity.get("name") or p.id
        tag = f" _(case {p.case_id})_" if p.case_id else ""
        lines += [f"**{p.situation.get('unit')} — {who}**{tag}", "", p.narrative, ""]
    return "\n".join(lines)


def write_all(pop: Population, out_dir: Path, *, generated_at: str | None = None,
              report_text: str | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "-".join(x for x in (str(pop.scenario.get("scenario_id")),
                                pop.cohort or None, str(pop.seed)) if x)
    paths: dict[str, Path] = {}

    def dump(name: str, payload: Any) -> None:
        path = out_dir / name
        path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n",
                        encoding="utf-8")
        paths[name.split(".", 1)[1].rsplit(".", 1)[0]] = path

    dump(f"{stem}.personas.json", population_json(pop, generated_at=generated_at))
    dump(f"{stem}.provenance.json", provenance_json(pop))
    cards = out_dir / f"{stem}.cards.md"
    cards.write_text(cards_markdown(pop), encoding="utf-8")
    paths["cards"] = cards
    if report_text is not None:
        rep = out_dir / f"{stem}.report.md"
        rep.write_text(report_text, encoding="utf-8")
        paths["report"] = rep
    return paths
