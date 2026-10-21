"""Compiling personas into quantities an egress model acts on.

The claim the whole mechanism rests on is in `test_the_published_marginal_survives`:
assigning a resident a *place* in a published distribution, rather than a value of our
own, leaves the population's distribution exactly as the paper fitted it. If that ever
fails, the compiler is inventing magnitudes rather than orderings and the citations on
its outputs stop meaning anything.
"""

from __future__ import annotations

import statistics

import pytest

from egress_personas import adapters, trace
from egress_personas import effects as fx
from egress_personas.dists_ref import Reference
from egress_personas.sample import sample
from egress_personas.tables import load_dir


@pytest.fixture(scope="module")
def tables(data_dir):
    return load_dir(data_dir)


# ── reading a value off a published distribution ────────────────────────────

@pytest.mark.parametrize("family,params,want", [
    ("weibull", (102.475, 0.767), 120.0),      # Lovreglio cluster 1, implied mean
    ("weibull", (724.617, 0.978), 732.0),      # cluster 2
    ("uniform", (40.0, 80.0), 60.0),
    ("normal", (1.20, 0.24), 1.20),
    ("bernoulli", (0.23,), 0.23),
])
def test_a_reference_reproduces_its_published_mean(family, params, want):
    r = Reference("r", "r", family, "", params + (None,) * (4 - len(params)))
    assert r.mean_estimate() == pytest.approx(want, rel=0.01)


def test_a_reference_ppf_is_monotone():
    for family, params in (("weibull", (102.475, 0.767)), ("uniform", (40.0, 80.0)),
                           ("normal", (1.2, 0.24)), ("lognormal", (0.0, 0.4))):
        r = Reference("r", "r", family, "", params + (None,) * (4 - len(params)))
        vals = [r.ppf(q / 20) for q in range(1, 20)]
        assert vals == sorted(vals), family


def test_a_measured_curve_inverts_the_way_it_was_published():
    """The curve states the share who turn back *at or below* a visibility, so a
    higher quantile has to mean a more tolerant resident, not a less tolerant one."""
    r = Reference("tb", "turn back", "empirical_curve", "m", (None,) * 4,
                  curve=((0.0, 0.63), (1.83, 0.385), (3.66, 0.24),
                         (9.14, 0.14), (18.3, 0.015)))
    vals = [r.ppf(q / 20) for q in range(1, 20)]
    assert vals == sorted(vals)
    assert r.ppf(0.05) == 0.0          # the least tolerant never press on
    assert r.ppf(0.99) > 10.0          # the most tolerant go a long way


def test_a_bernoulli_reference_preserves_its_share_exactly():
    r = Reference("b", "b", "bernoulli", "", (0.23, None, None, None))
    n = 10000
    hits = sum(bool(r.ppf((i + 0.5) / n)) for i in range(n))
    assert hits / n == pytest.approx(0.23, abs=0.001)


# ── the compile pass ────────────────────────────────────────────────────────

def test_the_three_tabs_load_and_agree(tables):
    outs, refs, effs = (fx.read_outputs(tables), fx.read_references(tables),
                        fx.read_effects(tables))
    assert outs and refs and effs
    for e in effs:
        assert e.output in outs, e.id
    for o in outs.values():
        if o.reference_dist and "{" not in o.reference_dist:
            assert o.reference_dist in refs, o.id


def test_only_one_quantile_effect_per_output(tables):
    """Two would rank different populations, and the published marginal would not
    survive — which is the one thing this mechanism is for."""
    from collections import Counter
    counts = Counter(e.output for e in fx.read_effects(tables)
                     if e.mechanism == "quantile")
    assert all(v == 1 for v in counts.values()), counts


def test_effects_apply_in_an_order_where_the_last_word_wins(tables):
    """A gate must be able to override whatever set a value, so it runs last; and a
    higher priority must survive, so it runs after a lower one."""
    effs = fx.read_effects(tables)
    mech = [e.mechanism for e in effs]
    assert mech.index("gate") == len(mech) - 1
    for a, b in zip(effs, effs[1:]):
        if a.mechanism == b.mechanism:
            assert (a.priority, a.id) <= (b.priority, b.id)


def test_the_published_marginal_survives(population):
    """The central claim: the persona decides the ordering, the literature keeps the
    shape. Measured against each reference's own published mean."""
    assert population.marginals
    for m in population.marginals:
        assert m["within_1pc"], m


def test_the_marginal_survives_across_seeds_and_cohorts(tables):
    for seed in (1, 99):
        for cohort in (None, "elderly_block", "student_block"):
            pop = sample(tables, "night_fire12", seed, cohort=cohort)
            for m in pop.marginals:
                assert m["within_1pc"], (seed, cohort, m)


def test_every_resident_gets_the_required_outputs(population):
    required = [o.id for o in population.outputs.values() if o.required]
    assert required
    for p in population.people:
        vals = population.compiled[p.key].values
        for oid in required:
            assert oid in vals, (p.key, oid)


def test_quantiles_are_uniform_which_is_why_the_marginal_holds(population):
    qs = [c.quantiles.get("premovement_time_s")
          for c in population.compiled.values()
          if c.quantiles.get("premovement_time_s") is not None]
    assert len(qs) > 100
    assert min(qs) > 0.0 and max(qs) < 1.0
    assert statistics.fmean(qs) == pytest.approx(0.5, abs=0.02)


def test_a_gate_overrides_the_quantile_that_set_the_value(population):
    """You cannot try a staircase you have never noticed, whatever your disposition."""
    blind = [p for p in population.people
             if p.knowledge.get("knows_second_stair") is False]
    assert blind
    for p in blind:
        c = population.compiled[p.key]
        assert c.values["tries_alternate_route"] is False
        kinds = [s.mechanism for s in c.steps["tries_alternate_route"]]
        assert kinds[-1] == "gate"


def test_a_direct_effect_carries_the_registry_value_across_unchanged(population):
    for p in population.people:
        if p.body.get("base_speed") is None:
            continue
        assert population.compiled[p.key].values["walk_speed_mps"] == pytest.approx(
            p.body["base_speed"], abs=0.002)


def test_which_published_fit_applies_is_a_property_of_the_building(tables):
    """Proulx's poor-alarm figure is a *building* mean that already includes the
    residents who could not hear it, so the fit is chosen by the scenario. Moving an
    individual to the other fit would count audibility twice."""
    good = sample(tables, "night_fire12", 1234)
    poor = sample(tables, "night_poor_alarm", 1234)
    mean = lambda pop: statistics.fmean(
        pop.compiled[p.key].values["premovement_time_s"] for p in pop.people)
    # Six times, which is the ratio between the two published fits.
    assert mean(poor) > mean(good) * 4


def test_not_hearing_the_alarm_puts_you_late_within_that_fit(tables):
    """Audibility belongs in the ordering, where it is the heaviest single term."""
    pop = sample(tables, "night_fire12", 1234)
    deaf = [p for p in pop.people if p.situation.get("alarm_audible") is False]
    heard = [p for p in pop.people if p.situation.get("alarm_audible") is not False]
    assert deaf and heard
    q = lambda group: statistics.fmean(
        pop.compiled[p.key].quantiles["premovement_time_s"] for p in group)
    assert q(deaf) > q(heard) + 0.2
    # And the population still reproduces the published fit, because moving somebody
    # later moved somebody else earlier.
    for m in pop.marginals:
        assert m["within_1pc"], m


def test_the_chain_is_labelled_by_its_weakest_link(population):
    """A value read off a sourced distribution at an invented ordering is invented."""
    assert fx._weakest("SOURCED", "INVENTED") == "INVENTED"
    assert fx._weakest("SOURCED", "ESTIMATE") == "ESTIMATE"
    assert fx._weakest("SOURCED", "SOURCED") == "SOURCED"
    for c in population.compiled.values():
        for steps in c.steps.values():
            for s in steps:
                assert s.evidence in ("SOURCED", "ESTIMATE", "INVENTED", "—")


def test_an_output_with_no_published_figure_is_reported_as_a_gap(population):
    """`route_confusion` has no reference distribution because none was found. It
    should be visible as a recorded gap, not silently produce nothing."""
    blocked = population.compiled.get("__blocked__")
    assert blocked
    text = " ".join(s.detail for s in blocked.steps["blocked"])
    assert "route_confusion" in text
    assert "no reference distribution" in text


def test_compiling_is_reproducible_and_seed_dependent(tables):
    a = sample(tables, "night_fire12", 7)
    b = sample(tables, "night_fire12", 7)
    c = sample(tables, "night_fire12", 8)
    pick = lambda pop: {k: v.values for k, v in pop.compiled.items()}
    assert pick(a) == pick(b)
    assert pick(a) != pick(c)


# ── adapters ────────────────────────────────────────────────────────────────

def test_the_shipped_adapters_load(population):
    found = adapters.available()
    assert {"generic", "fire_egress_3d"} <= set(found)
    for a in found.values():
        for oid in a.mapping:
            assert oid in population.outputs, (a.id, oid)
        for oid in a.unsupported:
            assert oid in population.outputs, (a.id, oid)


def test_an_adapter_renames_without_changing_a_value(population):
    a = adapters.resolve("fire_egress_3d")
    key = population.people[0].key
    vals = population.compiled[key].values
    out = a.render(vals)
    assert out["delay_s"] == vals["premovement_time_s"]
    assert out["base_speed"] == vals["walk_speed_mps"]
    # What it cannot use is dropped from the engine's file, not silently renamed.
    assert "gather_time_s" not in out
    assert "warns_n_neighbours" not in out


def test_an_adapter_says_why_it_cannot_use_something(population):
    a = adapters.resolve("fire_egress_3d")
    r = adapters.reach(a, population.outputs, population.effects, population.cover)
    assert r["outputs_blocked"]
    for oid in r["outputs_blocked"]:
        assert r["why_blocked"][oid]
        assert len(r["why_blocked"][oid]) > 20, oid


def test_the_generic_adapter_drops_nothing(population):
    a = adapters.resolve("generic")
    for oid in population.outputs:
        assert a.supports(oid), oid


def test_an_unknown_adapter_lists_the_real_ones():
    with pytest.raises(KeyError) as e:
        adapters.resolve("pathfinder")
    assert "generic" in str(e.value)


# ── the traceability view ───────────────────────────────────────────────────

def test_every_enabled_heuristic_appears_in_the_trace(tables, population):
    a = adapters.resolve("fire_egress_3d")
    links = trace.build(tables, population, a)
    from egress_personas.tables import as_bool, text
    enabled = {text(r.get("id")) for r in tables["parameters"]
               if as_bool(r.get("enabled")) is not False}
    assert {x.heuristic for x in links} == enabled


def test_a_chain_that_stops_short_says_why(tables, population):
    a = adapters.resolve("fire_egress_3d")
    links = trace.build(tables, population, a)
    dead = [x for x in links if not x.reaches_engine]
    assert dead
    for x in dead:
        assert x.blocked_because, x.heuristic


def test_the_trace_reports_the_weakest_link_not_the_flattering_one(tables, population):
    a = adapters.resolve("fire_egress_3d")
    links = trace.build(tables, population, a)
    for x in links:
        labels = [x.heuristic_evidence, x.effect_evidence, x.reference_evidence]
        assert x.chain_evidence == trace.weakest(*labels)
    # A sourced heuristic through an invented effect must not read as sourced.
    mixed = [x for x in links
             if x.heuristic_evidence == "SOURCED" and x.effect_evidence == "INVENTED"]
    for x in mixed:
        assert x.chain_evidence == "INVENTED"


def test_more_chains_reach_the_generic_target_than_one_engine(tables, population):
    g = trace.build(tables, population, adapters.resolve("generic"))
    f = trace.build(tables, population, adapters.resolve("fire_egress_3d"))
    assert sum(x.reaches_engine for x in g) > sum(x.reaches_engine for x in f)
