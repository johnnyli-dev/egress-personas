"""Sampling a persona and reading them, in the terminal and on a page.

The card is the human check on the generator: if the sampled people read like noise,
no amount of target conformance makes the population useful.
"""

from __future__ import annotations

import json
import re

import pytest

from egress_personas.explore import payload, render
from egress_personas.sample import sample
from egress_personas.show import FILTERS, pick, render as render_show, summary
from egress_personas.tables import load_dir


def test_every_subset_is_described_and_countable(population):
    text = summary(population)
    for name, (what, _) in FILTERS.items():
        assert name in text
        assert what in text


def test_picking_by_id_key_and_case_all_find_the_same_person(population):
    case = next(p for p in population.people if p.case_id == "C01")
    for handle in (case.id, case.key, "C01"):
        assert pick(population, persona_id=handle) == [case]


def test_an_unknown_handle_says_what_a_handle_looks_like(population):
    with pytest.raises(KeyError) as e:
        pick(population, persona_id="nobody")
    assert "P0041" in e.value.args[0]


def test_an_unknown_filter_lists_the_real_ones(population):
    with pytest.raises(KeyError) as e:
        pick(population, which="tall")
    assert "isolated" in e.value.args[0]


def test_sampling_is_reproducible_and_without_replacement(population):
    a = pick(population, which="older", count=5, seed=7)
    b = pick(population, which="older", count=5, seed=7)
    assert [p.key for p in a] == [p.key for p in b]
    assert len({p.key for p in a}) == 5
    c = pick(population, which="older", count=5, seed=8)
    assert [p.key for p in a] != [p.key for p in c]


def test_every_filter_returns_only_members_of_its_subset(population):
    for name, (_, test) in FILTERS.items():
        got = pick(population, which=name, count=200)
        assert all(test(p) for p in got), name
        assert len(got) == sum(1 for p in population.people if test(p)), name


def test_filtering_by_floor_and_unit(population):
    on_14 = pick(population, floor=14, count=99)
    assert on_14 and all(p.situation["floor_label"] == 14 for p in on_14)
    in_14a = pick(population, unit="14a", count=99)
    assert in_14a and all(p.situation["unit"] == "14A" for p in in_14a)


def test_the_card_names_the_person_their_flat_and_their_ties(population):
    case = next(p for p in population.people if p.case_id == "C01")
    text = render_show(population, case)
    assert case.id in text
    assert "18C" in text
    assert "walker_cane" in text
    assert "connections" in text
    assert "where the numbers come from" in text
    assert "proulx1995" in text or "nist_ncstar_1_7" in text


def test_an_isolated_resident_is_shown_as_having_nobody(population):
    alone = [p for p in population.people if not p.ties]
    assert alone
    text = render_show(population, alone[0])
    assert "none." in text
    assert "no neighbour they would knock for" in text


def test_the_card_never_leaks_a_none(population):
    for person in population.people:
        text = render_show(population, person)
        assert "None" not in text, person.key
        assert not re.search(r"\bnan\b", text), person.key


def test_provenance_can_be_left_out(population):
    case = next(p for p in population.people if p.case_id)
    assert "where the numbers come from" not in render_show(
        population, case, provenance=False)


# ── the page ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def page_payload(data_dir):
    tables = load_dir(data_dir)
    return payload(sample(tables, "night_fire12", 1234), tables,
                   generated_at="2026-01-01T00:00:00+00:00")


def test_the_page_carries_everything_it_needs(page_payload):
    d = page_payload
    assert set(d) >= {"meta", "units", "households", "groups", "people", "prov",
                      "sources", "rules", "subsets"}
    assert len(d["people"]) == len(d["prov"])
    assert d["subsets"]["isolated"]["keys"]
    assert d["sources"] and d["rules"]


def test_every_provenance_entry_resolves_to_a_rule_and_a_source(page_payload):
    d = page_payload
    for key, fields in d["prov"].items():
        for path, f in fields.items():
            if f.get("inherited"):
                continue
            for step in f["chain"]:
                assert step["r"] in d["rules"] or step["r"] in ("case", "default"), step
                assert step["ev"] in ("SOURCED", "ESTIMATE", "INVENTED")
            for sid in f["src"]:
                assert sid in d["sources"], (key, path, sid)


def test_every_tie_endpoint_on_the_page_resolves(page_payload):
    keys = {p["key"] for p in page_payload["people"]}
    groups = {g["id"] for g in page_payload["groups"]}
    for p in page_payload["people"]:
        for t in p["ties"]:
            assert t["to"] in keys or t["to"] in groups


def test_the_page_embeds_its_data_and_leaves_no_placeholder(data_dir):
    tables = load_dir(data_dir)
    pop = sample(tables, "night_fire12", 1234)
    html = render(pop, tables, generated_at="2026-01-01T00:00:00+00:00")
    assert "__PAYLOAD__" not in html
    assert "<!doctype html>" in html
    assert html.count("<script") == 2
    # A JSON island must not carry the sequence that would end its own script tag.
    island = html.split('type="application/json">', 1)[1].split("</script>", 1)[0]
    assert "</" not in island
    assert json.loads(island.replace("<\\/", "</"))["people"]


def test_the_page_body_alone_has_no_document_wrapper(data_dir):
    """What gets published is the page content; the host supplies the document."""
    tables = load_dir(data_dir)
    pop = sample(tables, "night_fire12", 1234)
    body = render(pop, tables, standalone=False,
                  generated_at="2026-01-01T00:00:00+00:00")
    assert body.lstrip().startswith("<title>")
    assert "<!doctype" not in body.lower()
    # Matched with a delimiter, so <header> does not read as <head>.
    for tag in ("html", "head", "body"):
        assert not re.search(rf"<{tag}[\s>]", body, re.I), tag


def test_the_page_defines_every_colour_before_any_theme_block(data_dir):
    """A token defined only inside a dark-mode block never applies in the default
    'system' theme, which is the classic unreadable-artifact bug."""
    tables = load_dir(data_dir)
    body = render(sample(tables, "night_fire12", 1234), tables, standalone=False)
    css = body.split("<style>", 1)[1].split("</style>", 1)[0]
    base = css.split("@media", 1)[0]
    declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", base))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", css))
    assert used <= declared, used - declared
    for block in re.findall(r"@media \(prefers-color-scheme: dark\)(.*?)\n}", css, re.S):
        for token in re.findall(r"(--[a-z0-9-]+)\s*:", block):
            assert token in declared, token
    assert 'body {' in css or 'body{' in css
    assert "background: var(--paper)" in css
