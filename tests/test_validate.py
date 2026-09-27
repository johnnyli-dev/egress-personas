"""The validator is what makes the Sheet safe for somebody who does not write Python.

Each case here is a mistake a researcher can actually make in a spreadsheet, and the
assertion is on the *message*, not just that something failed: a problem nobody can
act on is barely better than silence.
"""

from __future__ import annotations

import pytest

from egress_personas.validate import problems


def messages(tables) -> str:
    return "\n".join(str(p) for p in problems(tables))


def test_the_committed_snapshot_has_no_problems(tables):
    assert problems(tables) == []


def test_unknown_enum_value_is_named_with_a_suggestion(mutate, edit_cell):
    t = mutate("parameters", lambda x: edit_cell(x, "P001", "phase", "ttse"))
    m = messages(t)
    assert "Parameters!C2" in m
    assert "'ttse' is not in Enums vocab 'phase'" in m
    assert "did you mean 'tts'" in m


def test_unknown_target_suggests_the_closest_field(mutate, edit_cell):
    t = mutate("parameters", lambda x: edit_cell(x, "P010", "target",
                                                 "dispositions.mill_tendancy"))
    m = messages(t)
    assert "unknown target 'dispositions.mill_tendancy'" in m
    assert "did you mean 'dispositions.mill_tendency'" in m


def test_a_sampler_owned_target_says_why_it_cannot_be_set(mutate, edit_cell):
    t = mutate("parameters", lambda x: edit_cell(x, "P001", "target",
                                                 "identity.age_years"))
    m = messages(t)
    assert "owned by the sampler" in m
    assert "Population target" in m


def test_unknown_applies_to_attribute_suggests_the_closest(mutate, edit_cell):
    t = mutate("parameters", lambda x: edit_cell(x, "P010", "applies_to",
                                                 "age_year >= 65"))
    m = messages(t)
    assert "unknown attribute 'age_year'" in m
    assert "did you mean 'age_years'" in m


def test_or_in_applies_to_is_refused_with_the_reason(mutate, edit_cell):
    t = mutate("parameters", lambda x: edit_cell(
        x, "P010", "applies_to", "age_years >= 65 or asleep == TRUE"))
    m = messages(t)
    assert "'or' is not supported" in m
    assert "two rows" in m


def test_applies_to_cannot_read_a_field_a_row_writes(mutate, edit_cell):
    """Otherwise a filter's answer would depend on the order rows were applied in."""
    t = mutate("parameters", lambda x: edit_cell(
        x, "P011", "applies_to", "mill_tendency >= 0.5"))
    m = messages(t)
    assert "unknown attribute 'mill_tendency'" in m


def test_wrong_dist_arity_names_the_parameter(mutate, edit_cell):
    t = mutate("parameters", lambda x: edit_cell(x, "P007", "p3", "0.7"))
    m = messages(t)
    assert "dist 'uniform' takes 2 parameter(s)" in m
    assert "would be ignored" in m


def test_missing_dist_parameter_names_what_it_should_be(mutate, edit_cell):
    t = mutate("parameters", lambda x: edit_cell(x, "P001", "p4", ""))
    m = messages(t)
    assert "dist 'trunc_normal' needs p4 = hi" in m


def test_dangling_source_id_is_caught(mutate, edit_cell):
    t = mutate("parameters", lambda x: edit_cell(x, "P010", "source_ids", "nist_ncstar"))
    m = messages(t)
    assert "unknown source 'nist_ncstar'" in m
    assert "Sources tab" in m


def test_duplicate_key_points_at_the_first_one(mutate, edit_cell):
    t = mutate("parameters", lambda x: edit_cell(x, "P002", "id", "P001"))
    m = messages(t)
    assert "duplicate id 'P001'" in m
    assert "first seen at Parameters!A2" in m


def test_case_in_an_unknown_unit_is_caught(mutate, edit_cell):
    t = mutate("cases", lambda x: edit_cell(x, "C01", "unit", "18Z"))
    m = messages(t)
    assert "unit '18Z' is not in the Building tab" in m


def test_a_household_cannot_span_two_flats(mutate, edit_cell):
    t = mutate("cases", lambda x: edit_cell(x, "C04", "unit", "14B"))
    m = messages(t)
    assert "a household lives in one flat" in m


def test_a_shifted_row_is_refused_rather_than_misread(mutate):
    """A row with a missing comma parses cleanly and means something else entirely.

    This is the failure that shifted seven Cases rows one column left during
    development, so it is the one worth a test of its own.
    """
    def eat_one_comma(text: str) -> str:
        lines = text.splitlines()
        for i, line in enumerate(lines[1:], start=1):
            if line.startswith("T030,") and line.endswith(",,"):
                lines[i] = line[:-1]
                break
        else:  # pragma: no cover - guards the fixture, not the code under test
            raise AssertionError("no row to narrow")
        return "\n".join(lines) + "\n"

    t = mutate("population", eat_one_comma)
    m = messages(t)
    assert "field(s) but the header declares" in m
    assert "shifted left" in m


def test_an_undeclared_column_is_an_error_not_a_shrug():
    from egress_personas.tables import read_csv_text
    with pytest.raises(ValueError) as e:
        read_csv_text("sources", "id,short,cite,favourite_colour\na,A,C,blue\n")
    assert "undeclared column(s) 'favourite_colour'" in str(e.value)
    assert "worse than" in str(e.value)


def test_shares_that_should_sum_to_one_are_checked(mutate, edit_cell):
    t = mutate("population", lambda x: edit_cell(x, "T021", "value", "0.50"))
    m = messages(t)
    assert "age_band shares sum to" in m


def test_a_formula_like_value_in_a_number_column_is_caught(mutate, edit_cell):
    t = mutate("population", lambda x: edit_cell(x, "T001", "value", "=AVERAGE(B2:B9)"))
    m = messages(t)
    assert "is not a number" in m


def test_two_set_rows_tied_on_priority_and_overlapping_is_an_error(mutate, edit_cell):
    """P002 and P003 both `set` base_speed; make their filters overlap."""
    t = mutate("parameters", lambda x: edit_cell(
        x, "P003", "applies_to", "mobility != wheelchair"))
    m = messages(t)
    assert "both 'set' body.base_speed at priority 100" in m
    assert "narrow one of them" in m


def test_non_overlapping_set_rows_at_one_priority_are_fine(tables):
    """Splitting a field by age band is the normal way to write these rows."""
    assert not any("both 'set'" in str(p) for p in problems(tables))
