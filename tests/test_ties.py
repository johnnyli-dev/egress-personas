"""The social graph: rates, scope, symmetry, and who is left out.

The last one matters most. A model in which everybody knows a neighbour has nothing to
say about the resident who has just moved in and knows nobody, and that resident is
one of the cases this project exists to look at.
"""

from __future__ import annotations

import pytest

from egress_personas.sample import sample
from egress_personas.tables import load_dir
from egress_personas.ties import connectedness, degree_summary

SEEDS = [1, 7, 1234, 4242, 99999]


@pytest.fixture(scope="module")
def runs(data_dir):
    tables = load_dir(data_dir)
    return [sample(tables, "night_fire12", s) for s in SEEDS]


def test_stated_rates_are_met_on_average(runs):
    per_rule: dict[str, list] = {}
    for pop in runs:
        for s in pop.tie_stats:
            per_rule.setdefault(s["rule"], []).append(s)
    for rule, stats in per_rule.items():
        stated = stats[0]["rate"]
        if stats[0]["rate_kind"] == "per_pair":
            got = sum(s["realized"] for s in stats) / len(stats)
        else:
            got = sum(s["realized_degree"] for s in stats) / len(stats)
        assert abs(got - stated) < max(0.15 * stated, 0.02), (rule, stated, got)


def test_symmetric_kinds_are_symmetric(runs):
    for pop in runs:
        by_key = {p.key: p for p in pop.people}
        for p in pop.people:
            for t in p.ties:
                if t["kind"] == "group_chat":
                    continue
                other = by_key[t["to"]]
                back = [u for u in other.ties
                        if u["to"] == p.key and u["kind"] == t["kind"]]
                assert back, (pop.seed, p.key, t)
                assert back[0]["strength"] == t["strength"]


def test_no_self_ties_and_no_duplicates(runs):
    for pop in runs:
        for p in pop.people:
            seen = set()
            for t in p.ties:
                assert t["to"] != p.key
                assert (t["to"], t["kind"]) not in seen, (p.key, t)
                seen.add((t["to"], t["kind"]))


def test_scope_is_respected(runs):
    for pop in runs:
        floor = {p.key: p.situation["floor_label"] for p in pop.people}
        household = {p.key: p.household for p in pop.people}
        for p in pop.people:
            for t in p.ties:
                if t["kind"] == "group_chat":
                    continue
                if t["kind"] == "household":
                    assert household[t["to"]] == p.household
                    continue
                if t["kind"] == "knock":
                    assert abs(floor[t["to"]] - floor[p.key]) <= 1, (p.key, t)


def test_children_are_tied_to_their_household_and_nothing_else(runs):
    """A three-year-old does not knock on a neighbour's door or telephone anybody."""
    for pop in runs:
        for p in pop.people:
            if p.identity["age_years"] >= 18:
                continue
            kinds = {t["kind"] for t in p.ties}
            assert kinds <= {"household"}, (pop.seed, p.key,
                                           p.identity["age_years"], kinds)


def test_household_ties_are_complete_within_a_flat(runs):
    for pop in runs:
        for h in pop.households:
            members = [p for p in pop.people if p.household == h.id]
            for a in members:
                tied = {t["to"] for t in a.ties if t["kind"] == "household"}
                assert tied == {b.key for b in members if b is not a}, h.id


def test_a_new_tenant_is_far_less_connected_than_an_established_one(runs):
    """The mechanism behind 'knows nobody in the building'."""
    new_deg, old_deg = [], []
    for pop in runs:
        for p in pop.people:
            if p.identity["age_years"] < 18:
                continue
            n = sum(1 for t in p.ties if t["kind"] in ("knock", "phone"))
            tenure = p.identity["tenure_years"] or 0
            (new_deg if tenure < 1 else old_deg).append(n)
    assert new_deg and old_deg
    mean_new = sum(new_deg) / len(new_deg)
    mean_old = sum(old_deg) / len(old_deg)
    assert mean_new < mean_old * 0.6, (mean_new, mean_old)


def test_some_residents_genuinely_know_nobody(runs):
    """If this ever hits zero, the model has lost the isolated resident.

    Isolation is probabilistic, so a long-standing resident can draw no ties by chance;
    what must hold is that the isolated skew new, which is the mechanism.
    """
    isolated_tenures, all_tenures = [], []
    for pop in runs:
        alone = [p for p in pop.people if not p.ties]
        assert alone, pop.seed
        isolated_tenures += [p.identity["tenure_years"] or 0 for p in alone]
        all_tenures += [p.identity["tenure_years"] or 0 for p in pop.people]
    mean_isolated = sum(isolated_tenures) / len(isolated_tenures)
    mean_all = sum(all_tenures) / len(all_tenures)
    assert mean_isolated < mean_all * 0.6, (mean_isolated, mean_all)


def test_connectedness_is_bounded_and_monotone():
    class P:
        def __init__(self, t):
            self.identity = {"tenure_years": t}
    vals = [connectedness(P(t), 3.0) for t in (0, 0.1, 1, 2, 3, 30)]
    assert vals[0] >= 0.15
    assert vals == sorted(vals)
    assert vals[-1] == 1.0
    assert connectedness(P(0.1), None) == 1.0  # no reference means no scaling


def test_the_graph_is_reproducible(data_dir):
    a = sample(load_dir(data_dir), "night_fire12", 1234)
    b = sample(load_dir(data_dir), "night_fire12", 1234)
    ta = {p.key: p.ties for p in a.people}
    tb = {p.key: p.ties for p in b.people}
    assert ta == tb


def test_degree_summary_reports_what_it_claims(population):
    d = degree_summary(population.people)
    n = len(population.people)
    for kind, stats in d.items():
        total = sum(1 for p in population.people for t in p.ties if t["kind"] == kind)
        assert abs(stats["mean_over_all"] - total / n) < 1e-3  # reported rounded
        assert 0 <= stats["share_with_any"] <= 1
