"""The JSON Schema for a population file, built from the field registry.

Generated rather than hand-written, so it cannot drift from `persona.FIELDS`. The
structural invariants a schema cannot state — household contiguity, symmetric
escort links, dense indices — are checked in tests instead.
"""

from __future__ import annotations

from typing import Any

from .persona import FIELDS

DTYPE = {"float": "number", "int": "integer", "bool": "boolean",
         "enum": "string", "str": "string"}


def _field_schema(path: str) -> dict[str, Any]:
    spec = FIELDS[path]
    out: dict[str, Any] = {"type": DTYPE[spec.dtype]}
    if spec.dtype in ("float", "int"):
        if spec.lo is not None:
            out["minimum"] = spec.lo
        if spec.hi is not None:
            out["maximum"] = spec.hi
    if spec.what:
        out["description"] = spec.what
    if spec.unit:
        out["x-unit"] = spec.unit
    return out


def _block(prefix: str) -> dict[str, Any]:
    props = {
        path.split(".", 1)[1]: _field_schema(path)
        for path in FIELDS if path.startswith(prefix + ".")
    }
    return {"type": "object", "additionalProperties": False, "properties": props}


def build_schema() -> dict[str, Any]:
    body = _block("body")
    # The simulation derives these from `mobility`; they ride along in `body` because
    # they are what its loader wants, but they are not parameter-writable.
    body["properties"].update({
        "can_use_stairs": {"type": "boolean"},
        "limiting_condition": {"type": "boolean"},
    })

    situation = _block("situation")
    situation["properties"].update({
        "unit": {"type": "string"},
        "floor_label": {"type": "integer"},
        "sim_floor": {"type": "integer", "minimum": 0},
        "home_tile": {"type": "array", "items": {"type": "integer"},
                      "minItems": 3, "maxItems": 3,
                      "description": "[sim_floor, x, y], matching the simulation's "
                                     "Agent::home"},
        "present": {"type": "boolean"},
        "asleep": {"type": "boolean"},
        "activity": {"type": "string"},
    })

    persona = {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "key", "index", "identity", "sim", "body", "situation",
                     "knowledge", "dispositions", "commitments", "ties", "household",
                     "narrative"],
        "properties": {
            "id": {"type": "string", "pattern": "^P[0-9]{4,}$"},
            "key": {"type": "string",
                    "pattern": "^(case:[A-Za-z0-9_.-]+|synth:[A-Za-z0-9]+:[0-9]+)$",
                    "description": "Stable identity. Every random draw for this "
                                   "persona is keyed by it, so it must never be "
                                   "reused or renumbered."},
            "index": {"type": "integer", "minimum": 0},
            "case_id": {"type": ["string", "null"]},
            "identity": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "age_years": {"type": "integer", "minimum": 0, "maximum": 120},
                    "age_band": {"type": "string"},
                    "sex": {"enum": ["female", "male", "other"]},
                    "household_role": {"type": "string"},
                    "tenure_years": {"type": ["number", "null"], "minimum": 0},
                },
                "required": ["age_years", "sex", "household_role"],
            },
            "sim": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "agent_type": {"enum": ["adult", "child", "elderly", "athletic",
                                            "wheelchair", "visitor", "caregiver"]},
                    "gender": {"enum": ["female", "male", "other"]},
                    "mobility": {"enum": ["none", "ambulatory_difficulty",
                                          "walker_cane", "wheelchair"]},
                    "escorts": {"type": ["string", "null"]},
                    "escorted_by": {"type": ["string", "null"]},
                },
                "required": ["agent_type", "gender", "mobility"],
            },
            "body": body,
            "situation": situation,
            "knowledge": _block("knowledge"),
            "dispositions": _block("dispositions"),
            "commitments": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "kind": {"type": "string"}, "what": {"type": "string"},
                        "where": {"type": "string"},
                        "delay_s": {"type": ["number", "null"], "minimum": 0},
                        "abandon_probability": {"type": ["number", "null"],
                                                "minimum": 0, "maximum": 1},
                    },
                    "required": ["kind", "what"],
                },
            },
            "ties": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "to": {"type": "string"},
                        "kind": {"enum": ["household", "knock", "phone", "group_chat"]},
                        "strength": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["to", "kind", "strength"],
                },
            },
            "household": {"type": "string"},
            "household_index": {
                "type": ["integer", "null"], "minimum": 0,
                "description": "Index of the household's first member, or null for "
                               "somebody living alone. Mirrors the simulation's own "
                               "Agent::household.",
            },
            "narrative": {"type": "string"},
            "notes": {"type": "string"},
        },
    }

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/URAP/egress-personas/schema/persona.schema.json",
        "title": "Egress persona population",
        "description": (
            "A sampled population for the fire-egress simulation. Every field of "
            "`body` is optional: absent means the simulation's own rules decide it."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "meta", "vocab", "units", "households",
                     "groups", "personas"],
        "properties": {
            "schema_version": {"type": "string"},
            "meta": {"type": "object"},
            "vocab": {"type": "object"},
            "units": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "label": {"type": "string"},
                        "floor_label": {"type": "integer"},
                        "sim_floor": {"type": "integer", "minimum": 0},
                        "letter": {"type": "string"},
                        "seed_tile": {"type": "array", "items": {"type": "integer"},
                                      "minItems": 2, "maxItems": 2},
                        "seed_tile_confidence": {"enum": ["sourced", "estimate",
                                                          "unverified"]},
                        "state": {"enum": ["occupied", "vacant", "all_absent"]},
                        "household": {"type": ["string", "null"]},
                    },
                    "required": ["label", "floor_label", "sim_floor", "state"],
                },
            },
            "households": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string"},
                        "unit": {"type": "string"},
                        "floor_label": {"type": "integer"},
                        "sim_floor": {"type": "integer"},
                        "size": {"type": "integer", "minimum": 1},
                        "first_index": {"type": "integer", "minimum": 0},
                        "member_indices": {"type": "array",
                                           "items": {"type": "integer"}},
                        "members": {"type": "array", "items": {"type": "string"}},
                        "has_pet": {"type": "boolean"},
                        "pinned": {"type": "boolean"},
                    },
                    "required": ["id", "unit", "size", "first_index",
                                 "member_indices", "members"],
                },
            },
            "groups": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string"}, "kind": {"type": "string"},
                        "members": {"type": "array", "items": {"type": "string"}},
                        "evidence": {"enum": ["SOURCED", "ESTIMATE", "INVENTED"]},
                        "sources": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["id", "kind", "members"],
                },
            },
            "personas": {"type": "array", "items": persona},
        },
    }
