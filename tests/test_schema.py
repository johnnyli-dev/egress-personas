"""The output contract: the schema, plus the invariants a schema cannot state.

The structural ones matter because they are what the simulation's own loader will
assume (FireEgress-3dsim, crates/fe-core/src/sim.rs:390-396 reads a household as a
contiguous run of agents identified by the index of its first member). Getting them
right here is what keeps that a small change rather than a rewrite.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA = Path(__file__).resolve().parents[1] / "schema" / "persona.schema.json"


@pytest.fixture(scope="session")
def schema():
    return json.loads(SCHEMA.read_text())


def test_the_committed_schema_matches_the_field_registry(schema):
    """The schema is generated from persona.FIELDS, so it cannot drift - unless
    somebody forgets to regenerate it, which is what this catches."""
    from egress_personas.schema import build_schema
    assert schema == build_schema(), (
        "schema/persona.schema.json is stale; run `personas schema "
        "--out-file schema/persona.schema.json`"
    )


def test_the_output_validates(schema, population_json):
    jsonschema.Draft202012Validator(schema).validate(population_json)


def test_indices_are_dense_and_ordered(population_json):
    idx = [p["index"] for p in population_json["personas"]]
    assert idx == list(range(len(idx)))


def test_households_are_contiguous_runs_named_by_their_first_member(population_json):
    people = population_json["personas"]
    for h in population_json["households"]:
        members = h["member_indices"]
        assert members == list(range(members[0], members[0] + len(members))), h["id"]
        assert h["first_index"] == members[0]
        for i in members:
            assert people[i]["household"] == h["id"]
            expected = h["first_index"] if len(members) > 1 else None
            assert people[i]["household_index"] == expected, people[i]["key"]


def test_somebody_living_alone_has_no_household_index(population_json):
    sizes = {h["id"]: h["size"] for h in population_json["households"]}
    for p in population_json["personas"]:
        if sizes[p["household"]] == 1:
            assert p["household_index"] is None


def test_escort_links_are_symmetric_and_correctly_typed(population_json):
    by_key = {p["key"]: p for p in population_json["personas"]}
    for p in population_json["personas"]:
        partner = p["sim"].get("escorted_by")
        if partner:
            assert p["sim"]["mobility"] == "wheelchair"
            other = by_key[partner]
            assert other["sim"]["escorts"] == p["key"]
            assert other["sim"]["agent_type"] == "caregiver"
            assert other["situation"]["sim_floor"] == p["situation"]["sim_floor"]


def test_every_tie_endpoint_resolves(population_json):
    keys = {p["key"] for p in population_json["personas"]}
    groups = {g["id"] for g in population_json["groups"]}
    for p in population_json["personas"]:
        for t in p["ties"]:
            assert t["to"] in keys or t["to"] in groups, t
            assert t["to"] != p["key"], "no self-ties"


def test_floors_are_within_the_scenario(population_json):
    n = population_json["meta"]["scenario"]["num_floors"]
    for p in population_json["personas"]:
        f = p["situation"]["sim_floor"]
        assert 0 < f < n, (p["key"], f)
        assert p["situation"]["home_tile"][0] == f


def test_agent_types_are_the_simulations_own_spellings(population_json):
    allowed = set(population_json["vocab"]["sim_agent_type"])
    assert allowed >= {"adult", "child", "elderly", "wheelchair", "caregiver"}
    for p in population_json["personas"]:
        assert p["sim"]["agent_type"] in allowed
        assert p["sim"]["gender"] in population_json["vocab"]["sex"]


def test_a_wheelchair_user_cannot_use_the_stairs(population_json):
    for p in population_json["personas"]:
        if p["sim"]["mobility"] == "wheelchair":
            assert p["body"]["can_use_stairs"] is False
        else:
            assert p["body"]["can_use_stairs"] is True


def test_at_most_one_household_to_a_flat(population_json):
    seen: dict[str, str] = {}
    for h in population_json["households"]:
        assert h["unit"] not in seen, (h["unit"], seen.get(h["unit"]), h["id"])
        seen[h["unit"]] = h["id"]


def test_pre_movement_is_left_to_the_simulation(population_json):
    """The sheet's pre-movement figure is a review midpoint; the simulation fits the
    distribution from 149 and 78 observations. Emitting a constant would be a
    regression, so the row that would do it is parked and switched off."""
    for p in population_json["personas"]:
        assert "delay_s" not in p["body"]


def test_body_carries_only_fields_the_registry_knows(population_json):
    from egress_personas.persona import FIELDS
    known = {p.split(".", 1)[1] for p in FIELDS if p.startswith("body.")}
    known |= {"can_use_stairs", "limiting_condition"}
    for p in population_json["personas"]:
        assert set(p["body"]) <= known, set(p["body"]) - known
