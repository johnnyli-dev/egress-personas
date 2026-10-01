"""Cohorts: a building described as a question, and what changes when you ask it.

The point of a cohort is to vary the population and nothing else, so the tests here are
mostly about isolation — a cohort must move what it names and leave the rest alone — and
about the honesty of the comparison, which reports inputs to RSET and must not be read
as RSET.
"""

from __future__ import annotations

import pytest

from egress_personas.cohorts import build, markdown, rows_of
from egress_personas.distributions import crosstabs, distributions, egress_drivers
from egress_personas.households import cohort_ids, read_targets
from egress_personas.sample import sample
from egress_personas.tables import load_dir


@pytest.fixture(scope="module")
def tables(data_dir):
    return load_dir(data_dir)


def test_the_sheet_describes_cohorts_and_each_overrides_something(tables):
    ids = cohort_ids(tables)
    assert len(ids) >= 3
    for cid in ids:
        base = read_targets(tables)
        over = read_targets(tables, cid)
        assert over != base, cid


def test_an_unknown_cohort_says_which_ones_exist(tables):
    with pytest.raises(KeyError) as e:
        read_targets(tables, "penthouse_only")
    assert "elderly_block" in e.value.args[0]


def test_a_cohort_replaces_a_whole_dimension_not_half_of_one(tables):
    """Overriding three of six age bands would leave the shares summing to something
    other than one, so touching a dimension at all replaces it."""
    t = read_targets(tables, "elderly_block")
    assert abs(sum(t.age_weights.values()) - 1.0) < 0.02
    assert set(t.age_weights) == set(read_targets(tables).age_weights)


def test_a_cohort_leaves_alone_what_it_does_not_name(tables):
    base, over = read_targets(tables), read_targets(tables, "elderly_block")
    assert over.sex_weights == base.sex_weights
    assert over.wheelchair_share == base.wheelchair_share
    assert over.ambulatory_share == base.ambulatory_share


def test_mostly_elderly_actually_comes_out_mostly_elderly(tables):
    pop = sample(tables, "night_fire12", 3, cohort="elderly_block")
    older = sum(1 for p in pop.people if p.identity["age_years"] >= 65)
    assert older / len(pop.people) > 0.55


def test_conditioning_mobility_on_age_carries_through_on_its_own(tables):
    """The elderly cohort never names a mobility share. It gets one anyway, because
    mobility is drawn conditioned on age — which is the model working, not a second
    assumption."""
    base = sample(tables, "night_fire12", 3)
    old = sample(tables, "night_fire12", 3, cohort="elderly_block")

    def difficulty(pop):
        return sum(1 for p in pop.people
                   if p.body["mobility"] != "none") / len(pop.people)

    assert difficulty(old) > difficulty(base) * 1.5


def test_the_accessible_cohort_raises_the_wheelchair_share_and_the_gap_with_it(tables):
    pop = sample(tables, "night_fire12", 3, cohort="accessible_block")
    chairs = [p for p in pop.people if p.body["mobility"] == "wheelchair"]
    assert len(chairs) / len(pop.people) > 0.08
    # The gap is the finding: a one-person household has nobody in the flat to help.
    assert any(g["what"].startswith("a wheelchair user") for g in pop.gaps)


def test_a_cohort_can_ask_for_a_building_without_the_hand_authored_cases(tables):
    pop = sample(tables, "night_fire12", 3, cohort="elderly_block")
    assert pop.include_cases is False
    assert not [p for p in pop.people if p.case_id]
    assert sample(tables, "night_fire12", 3).include_cases is True


def test_a_cohort_run_is_reproducible_and_distinct_from_the_base(tables):
    a = sample(tables, "night_fire12", 7, cohort="families")
    b = sample(tables, "night_fire12", 7, cohort="families")
    base = sample(tables, "night_fire12", 7)
    assert a.run_id == b.run_id
    assert a.run_id != base.run_id
    other = sample(tables, "night_fire12", 7, cohort="student_block")
    assert other.run_id not in (a.run_id, base.run_id)


def test_cohort_output_lands_in_its_own_files(tables, tmp_path):
    from egress_personas.emit import write_all
    pop = sample(tables, "night_fire12", 3, cohort="families")
    paths = write_all(pop, tmp_path, generated_at="2026-01-01T00:00:00+00:00")
    assert all("families" in p.name for p in paths.values())


def test_the_population_records_which_building_it_is(tables):
    from egress_personas.emit import population_json
    pop = sample(tables, "night_fire12", 3, cohort="families")
    meta = population_json(pop, generated_at="2026-01-01T00:00:00+00:00")["meta"]
    assert meta["cohort"]["id"] == "families"
    assert meta["cohort"]["question"]
    assert meta["cohort"]["includes_cases"] is False


# ── the comparison ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def columns(tables):
    return build(tables, "night_fire12", seeds=[1, 2, 3])


def test_every_building_gets_a_column_including_the_base(columns, tables):
    assert columns[0].cohort == ""
    assert {c.cohort for c in columns[1:]} == set(cohort_ids(tables))
    for c in columns:
        assert len(c.runs) == 3


def test_every_driver_is_measured_for_every_building(columns):
    keys = {r["key"] for r in rows_of(columns)}
    assert keys
    for c in columns:
        assert set(c.drivers) >= keys
        for key in keys:
            assert len(c.drivers[key]) == 3


def test_the_comparison_separates_tts_from_tte(columns):
    phases = {r["phase"] for r in rows_of(columns)}
    assert {"TTS", "TTE"} <= phases


def test_the_comparison_says_it_is_not_an_evacuation_result(columns):
    text = markdown(columns, "night_fire12", [1, 2, 3])
    assert "inputs to RSET, not RSET" in text
    assert "Nothing here simulates an evacuation" in text
    assert "a difference smaller than the spread is not a difference" in text


def test_the_comparison_names_each_cohorts_question(columns):
    text = markdown(columns, "night_fire12", [1, 2, 3])
    for c in columns[1:]:
        assert c.question in text, c.cohort


def test_the_elderly_building_is_slower_and_the_student_one_faster(columns):
    by = {c.cohort: c for c in columns}
    base = by[""].mean("speed_mean")
    assert by["elderly_block"].mean("speed_mean") < base
    assert by["student_block"].mean("speed_mean") > base
    # The tail matters more than the mean, because a household moves at its slowest.
    assert by["elderly_block"].mean("speed_p5") < by[""].mean("speed_p5")


def test_bigger_households_leave_fewer_people_unwarned(columns):
    by = {c.cohort: c for c in columns}
    assert by["families"].mean("isolated") < by[""].mean("isolated")


def test_a_building_of_new_tenants_knows_less_of_it(columns):
    by = {c.cohort: c for c in columns}
    assert by["student_block"].mean("familiarity") < by[""].mean("familiarity")


# ── distributions ───────────────────────────────────────────────────────────

def test_every_distribution_counts_everybody(population):
    per_person = ("age", "age_band", "sex", "mobility", "agent_type",
                  "household_role", "tenure", "tenure_band", "base_speed")
    for key in per_person:
        d = distributions(population)[key]
        assert d.total == len(population.people), key
        assert sum(d.counts.values()) == d.total, key


def test_household_sizes_are_counted_over_households_not_residents(population):
    d = distributions(population)["household_size"]
    assert d.total == len(population.households)


def test_the_quantiles_bracket_the_mean(population):
    d = distributions(population)["base_speed"]
    assert d.low <= d.p5 <= d.median <= d.p95 <= d.high
    assert d.low <= d.mean <= d.high


def test_a_crosstab_adds_up_both_ways(population):
    for name, ct in crosstabs(population).items():
        assert sum(ct["row_totals"].values()) == ct["total"], name
        cells = sum(ct["cells"][r].get(c, 0) for r in ct["rows"] for c in ct["cols"])
        assert cells == ct["total"], name


def test_the_mobility_crosstab_covers_only_those_who_need_it(population):
    ct = crosstabs(population)["mobility_by_help"]
    assert ct["total"] == sum(1 for p in population.people
                              if p.body["mobility"] != "none")


def test_every_driver_carries_a_number_a_unit_and_a_reason(population):
    for d in egress_drivers(population):
        assert d["key"] and d["what"] and d["unit"]
        assert d["why"].endswith(".")
        assert d["phase"] in ("—", "TTS", "TTE")
        if d["value"] != "—":
            assert d["raw"] is not None, d["key"]


def test_the_drivers_count_only_people_who_are_in_the_building(population):
    present = sum(1 for p in population.people if p.situation["present"])
    row = next(d for d in egress_drivers(population) if d["key"] == "present")
    assert row["raw"] == present
