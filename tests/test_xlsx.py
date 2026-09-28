"""Getting the snapshot into Google Sheets, and back out unchanged.

The upload is the step most likely to corrupt the data — a paste landing one column
over is exactly the failure this package spends its validator on — so the workbook has
to carry the content across without touching it. The test that matters is the last one:
the content hash must survive a round trip, because that hash is what a generated
population names as the revision it came from.
"""

from __future__ import annotations

import csv
import io

import pytest

from egress_personas.sheet import sheet_id_from
from egress_personas.tables import TABS, content_hash, load_dir, read_csv_text
from egress_personas.validate import VOCAB_OF, problems

openpyxl = pytest.importorskip("openpyxl")


@pytest.fixture(scope="module")
def workbook(tmp_path_factory, data_dir):
    from egress_personas.xlsx import write_workbook
    path = tmp_path_factory.mktemp("sheet") / "model.xlsx"
    write_workbook(data_dir, path)
    return openpyxl.load_workbook(path)


def as_tabs(wb):
    """Every declared tab as CSV, the way `pull` would receive it."""
    out = {}
    for name in TABS:
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        for row in wb[name.capitalize()].iter_rows(values_only=True):
            w.writerow(["" if v is None else str(v) for v in row])
        out[name] = read_csv_text(name, buf.getvalue())
    return out


def test_every_declared_tab_is_present_and_named_for_the_pull(workbook):
    for name in TABS:
        assert name.capitalize() in workbook.sheetnames


def test_a_round_trip_through_the_workbook_changes_nothing(workbook, data_dir):
    """Upload this, pull it back, and a run keeps the same id."""
    assert content_hash(as_tabs(workbook)) == load_dir(data_dir).snapshot["content_hash"]


def test_the_round_tripped_snapshot_still_validates(workbook):
    from egress_personas.tables import Tables
    assert problems(Tables(as_tabs(workbook), {})) == []


def test_no_row_loses_a_column_on_the_way_through(workbook, data_dir):
    original = load_dir(data_dir)
    for name, tab in as_tabs(workbook).items():
        assert len(tab) == len(original[name]), name
        for i, row in enumerate(tab.rows):
            assert tab.widths[i] >= len(tab.columns), (name, i)


def test_the_header_row_stays_put_when_scrolling(workbook):
    for name in TABS:
        assert workbook[name.capitalize()].freeze_panes == "A2"


def test_every_controlled_column_gets_a_dropdown(workbook):
    lists = workbook["Lists"]
    vocab_col = {c.value: c.column_letter for c in lists[1] if c.value}
    for (tab, column), vocab in VOCAB_OF.items():
        ws = workbook[tab.capitalize()]
        header = [c.value for c in ws[1]]
        if column not in header or vocab not in vocab_col:
            continue
        letter = ws.cell(row=1, column=header.index(column) + 1).column_letter
        refs = [dv for dv in ws.data_validations.dataValidation
                if f"{letter}2" in str(dv.sqref)]
        assert refs, f"{tab}.{column} has no dropdown"
        assert f"Lists!${vocab_col[vocab]}$2" in refs[0].formula1


def test_no_dropdown_points_at_an_empty_or_gappy_range(workbook):
    lists = workbook["Lists"]
    for name in workbook.sheetnames:
        for dv in workbook[name].data_validations.dataValidation:
            ref = dv.formula1.lstrip("=").split("!", 1)[1].replace("$", "")
            cells = [c for row in lists[ref] for c in row]
            assert cells, dv.formula1
            assert all(c.value for c in cells), dv.formula1


def test_the_lists_tab_is_not_one_the_generator_reads(workbook):
    assert "Lists" not in {t.capitalize() for t in TABS}
    assert "READ ME" not in {t.capitalize() for t in TABS}


def test_a_missing_snapshot_says_what_to_run(tmp_path):
    from egress_personas.xlsx import write_workbook
    with pytest.raises(FileNotFoundError) as e:
        write_workbook(tmp_path, tmp_path / "x.xlsx")
    assert "personas init-data" in str(e.value)


# ── finding the sheet ───────────────────────────────────────────────────────

@pytest.mark.parametrize("given", [
    "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/edit#gid=0",
    "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345",
    "1AbCdEfGhIjKlMnOpQrStUvWxYz012345",
    "  1AbCdEfGhIjKlMnOpQrStUvWxYz012345  ",
])
def test_the_sheet_id_comes_out_of_whatever_was_pasted(given):
    assert sheet_id_from(given) == "1AbCdEfGhIjKlMnOpQrStUvWxYz012345"


@pytest.mark.parametrize("given", ["", "not a sheet", "https://example.com/x", "abc"])
def test_something_that_is_not_a_sheet_says_what_one_looks_like(given):
    with pytest.raises(ValueError) as e:
        sheet_id_from(given)
    assert "docs.google.com/spreadsheets/d/" in str(e.value)


def test_the_pull_url_pins_the_header_row(workbook):
    """Left to itself the endpoint guesses how many leading rows are headers, and a
    guess of nought or two shifts every value in the tab."""
    from egress_personas.sheet import GVIZ
    assert "headers=1" in GVIZ
