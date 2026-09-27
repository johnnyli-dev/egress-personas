"""The card an LLM would be conditioned on, and a human would read to judge the sampler."""

from __future__ import annotations

import re

from egress_personas.sample import sample
from egress_personas.tables import load_dir


def test_everybody_gets_a_card(population):
    for p in population.people:
        assert p.narrative
        assert p.narrative.endswith(".")
        assert len(p.narrative) > 60, p.key


def test_cards_are_stable_across_runs(data_dir):
    a = sample(load_dir(data_dir), "night_fire12", 1234)
    b = sample(load_dir(data_dir), "night_fire12", 1234)
    assert {p.key: p.narrative for p in a.people} == {p.key: p.narrative for p in b.people}


def test_no_card_leaks_a_placeholder_or_a_none(population):
    for p in population.people:
        text = p.narrative
        assert "None" not in text, p.key
        assert "{" not in text and "}" not in text, p.key
        assert not re.search(r"\b(nan|null|undefined)\b", text, re.I), p.key
        assert "  " not in text, p.key


def test_a_card_never_asserts_a_field_the_persona_lacks(population):
    for p in population.people:
        if "second staircase" in p.narrative:
            assert "knows_second_stair" in p.knowledge
        if "stair by habit" in p.narrative:
            assert p.knowledge.get("habitual_stair") in ("north", "south")
        if "false alarm" in p.narrative:
            assert p.knowledge.get("prior_false_alarms")


def test_the_card_says_where_they_are_when_it_starts(population):
    for p in population.people:
        assert ("At the moment the fire starts" in p.narrative
                or "not in the building" in p.narrative), p.key


def test_commitments_are_named_in_the_card(population):
    for p in population.people:
        if p.commitments and p.situation.get("present"):
            assert "will not leave without" in p.narrative, p.key


def test_the_authoring_note_stays_out_of_the_card(population):
    """`notes` says why a case exists; the card says who the person is. Mixing them
    would feed the team's own commentary to the model as if it were biography."""
    for p in population.people:
        if not p.case_id:
            continue
        note = p.identity.get("notes") or ""
        assert note, p.case_id
        assert note not in p.narrative
        assert "Tests the case" not in p.narrative


def test_an_isolated_resident_is_described_as_isolated(population):
    for p in population.people:
        if p.ties or not p.situation.get("present"):
            continue
        assert "know nobody else in the building" in p.narrative, p.key


def test_a_small_child_is_not_given_a_decision_making_style(population):
    for p in population.people:
        if p.identity["age_years"] < 12 and p.situation.get("present"):
            assert "too young to decide anything" in p.narrative, p.key
            assert "tend to act rather than confer" not in p.narrative


def test_verbs_agree_with_the_pronoun(population):
    """Every sentence after the first takes "they", so every verb is plural."""
    bad = ("They knows", "They tends", "They walks", "They uses", "They heads",
           "They shares", "They lives", "They takes", "They looks", "They barely knows")
    for p in population.people:
        for phrase in bad:
            assert phrase not in p.narrative, (p.key, phrase, p.narrative)
