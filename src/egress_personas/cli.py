"""`personas` — the command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__

DATA = Path("data")
OUT = Path("out")


def _load(data: Path):
    from .tables import load_dir
    return load_dir(data)


def _checked(data: Path):
    """Load the snapshot and refuse to go on if it has problems."""
    from .validate import problems
    tables = _load(data)
    probs = problems(tables)
    if probs:
        print(f"{len(probs)} problem(s) in {data}/ — nothing generated:\n",
              file=sys.stderr)
        for p in probs:
            print(f"  {p}", file=sys.stderr)
        raise SystemExit(1)
    return tables


def cmd_init_data(args: argparse.Namespace) -> int:
    from .seed import write
    written = write(args.data, force=args.force)
    if not written:
        print(f"{args.data}/ already has its tabs; --force to overwrite.")
        return 0
    for p in written:
        print(f"wrote {p}")
    print("\nUpload these as the eight tabs of a Google Sheet, then use "
          "`personas pull --sheet-id ...` to snapshot it back.")
    return 0


def cmd_init_sheet(args: argparse.Namespace) -> int:
    from .xlsx import describe, write_workbook
    try:
        path = write_workbook(args.data, args.out_file)
    except (RuntimeError, FileNotFoundError) as e:
        print(e, file=sys.stderr)
        return 1
    d = describe(args.data)
    print(f"wrote {path}")
    for tab, (rows, cols) in d["tabs"].items():
        print(f"  {tab:<12} {rows:>4} rows x {cols:>2} columns")
    print(f"  {'Lists':<12} {d.get('vocabs', 0):>4} vocabularies behind "
          f"{d.get('dropdowns', 0)} dropdowns")
    print("\nNext:")
    print("  1. Upload it to Google Drive and open it with Google Sheets")
    print("     (Drive keeps the tab names and the dropdowns).")
    print("  2. Share -> General access -> Anyone with the link -> Viewer.")
    print("  3. personas pull --sheet-url <the sheet's URL>")
    return 0


def cmd_pull(args: argparse.Namespace) -> int:
    from .sheet import pull, sheet_id_from
    from .validate import problems
    token = None
    if args.token_file:
        token = Path(args.token_file).read_text().strip()
    try:
        sheet_id = sheet_id_from(args.sheet_url or args.sheet_id or "")
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    try:
        meta, changes = pull(sheet_id, args.data, token=token,
                             only=args.tab or None, dry_run=args.check)
    except (RuntimeError, ValueError) as e:
        print(e, file=sys.stderr)
        return 1

    moved = [c for c in changes if c]
    if args.check:
        if not moved:
            print(f"data/ is up to date with {sheet_id}.")
            return 0
        print(f"data/ is behind the Sheet — {len(moved)} tab(s) differ:\n")
        for c in moved:
            print(f"  {c.tab.capitalize():<12} {c.summary()}")
            for line in c.detail():
                print(f"      {line}")
        print("\nRun `personas pull` to bring it up to date. Nothing was written.")
        return 1

    print(f"pulled {len(meta['tabs'])} tab(s) from {sheet_id} at {meta['pulled_at']}")
    if moved:
        for c in moved:
            print(f"  {c.tab.capitalize():<12} {c.summary()}")
            for line in c.detail():
                print(f"      {line}")
    else:
        print("  nothing changed.")
    probs = problems(_load(args.data))
    if probs:
        print(f"\n{len(probs)} problem(s) in the new snapshot:", file=sys.stderr)
        for p in probs:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("\nno problems." + ("  Commit the diff." if moved else ""))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from .validate import problems
    tables = _load(args.data)
    probs = problems(tables)
    print(f"snapshot {tables.snapshot.get('content_hash')}")
    for name, tab in tables.tabs.items():
        print(f"  {name:12} {len(tab):4} row(s)")
    if not probs:
        print("\nno problems.")
        return 0
    print(f"\n{len(probs)} problem(s):")
    for p in probs:
        print(f"  {p}")
    return 1


def cmd_build(args: argparse.Namespace) -> int:
    from .emit import write_all
    from .report import markdown
    from .sample import sample
    if args.pull:
        rc = cmd_pull(argparse.Namespace(
            data=args.data, sheet_url=args.pull, sheet_id=None,
            tab=None, token_file=args.token_file, check=False))
        if rc:
            return rc
        print()
    tables = _checked(args.data)
    pop = sample(tables, args.scenario, args.seed, cohort=args.cohort)
    paths = write_all(pop, args.out,
                      generated_at=args.generated_at,
                      report_text=markdown(pop))
    print(f"run {pop.run_id}")
    print(f"{len(pop.people)} residents, {len(pop.households)} households, "
          f"{sum(len(p.ties) for p in pop.people)} tie endpoints")
    for kind, path in paths.items():
        print(f"  {kind:11} {path}")
    off = [c for c in pop.conformance if c["within"] is False]
    if off:
        print(f"\n{len(off)} target(s) outside tolerance — see the report.")
    if pop.warnings:
        print(f"{len(pop.warnings)} warning(s) — see the report.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from .report import markdown
    from .sample import sample
    tables = _checked(args.data)
    pop = sample(tables, args.scenario, args.seed, cohort=args.cohort)
    text = markdown(pop)
    if args.out_file:
        Path(args.out_file).write_text(text, encoding="utf-8")
        print(f"wrote {args.out_file}")
    else:
        print(text)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    from .compare import compare
    from .sample import sample
    tables = _checked(args.data)
    pop = sample(tables, args.scenario, args.seed, cohort=args.cohort)
    text = compare(pop, args.against)
    if args.out_file:
        Path(args.out_file).write_text(text, encoding="utf-8")
        print(f"wrote {args.out_file}")
    else:
        print(text)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    from .sample import sample
    from .show import pick, render, summary
    tables = _checked(args.data)
    pop = sample(tables, args.scenario, args.seed, cohort=args.cohort)
    if args.list:
        print(summary(pop))
        return 0
    try:
        people = pick(pop, which=args.filter, persona_id=args.id, floor=args.floor,
                      unit=args.unit, count=args.count, seed=args.pick_seed)
    except KeyError as e:
        print(e.args[0], file=sys.stderr)
        return 1
    if not people:
        print("nothing matched. `personas show --list` shows what there is.",
              file=sys.stderr)
        return 1
    for i, person in enumerate(people):
        if i:
            print()
        print(render(pop, person, provenance=not args.no_provenance))
    return 0


def cmd_explore(args: argparse.Namespace) -> int:
    from .explore import write_explorer
    from .sample import sample
    tables = _checked(args.data)
    pop = sample(tables, args.scenario, args.seed, cohort=args.cohort)
    path = write_explorer(pop, args.out_file, tables=tables,
                          generated_at=args.generated_at)
    print(f"wrote {path}")
    print(f"{len(pop.people)} residents embedded. Open it in a browser.")
    return 0


def cmd_distributions(args: argparse.Namespace) -> int:
    import json as _json

    from .distributions import makeup
    from .report import distributions_markdown
    from .sample import sample
    tables = _checked(args.data)
    pop = sample(tables, args.scenario, args.seed, cohort=args.cohort)
    if args.json:
        text = _json.dumps(makeup(pop), indent=2)
    else:
        text = distributions_markdown(pop)
    if args.out_file:
        Path(args.out_file).write_text(text, encoding="utf-8")
        print(f"wrote {args.out_file}")
    else:
        print(text)
    return 0


def cmd_cohorts(args: argparse.Namespace) -> int:
    from .cohorts import build, markdown
    from .households import cohort_ids
    from .tables import text as _text
    tables = _checked(args.data)

    if args.list:
        tab = tables.get("cohorts")
        print("Buildings the Sheet describes, beyond the base one:\n")
        for row in (tab or []):
            cid = _text(row.get("cohort_id"))
            n = sum(1 for r in tables["population"]
                    if _text(r.get("cohort")) == cid)
            print(f"  {cid:<18} {_text(row.get('name')) or ''}")
            if _text(row.get("question")):
                print(f"  {'':<18} {_text(row.get('question'))}")
            print(f"  {'':<18} {n} target row(s) overridden\n")
        if not (tab and len(tab)):
            print("  none. Add a row to the Cohorts tab and give it Population rows.")
        return 0

    known = cohort_ids(tables)
    which = args.cohort or None
    if which:
        missing = [c for c in which if c not in known]
        if missing:
            print(f"unknown cohort(s) {', '.join(missing)}; the Sheet has "
                  f"{', '.join(known) or 'none'}", file=sys.stderr)
            return 1
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    columns = build(tables, args.scenario, seeds=seeds, which=which)
    text_out = markdown(columns, args.scenario, seeds)
    if args.out_file:
        Path(args.out_file).write_text(text_out, encoding="utf-8")
        print(f"wrote {args.out_file}")
        print(f"{len(columns)} building(s) x {len(seeds)} seed(s)")
    else:
        print(text_out)
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    from .schema import build_schema
    text = json.dumps(build_schema(), indent=2) + "\n"
    if args.out_file:
        Path(args.out_file).write_text(text, encoding="utf-8")
        print(f"wrote {args.out_file}")
    else:
        print(text, end="")
    return 0


def cmd_fields(args: argparse.Namespace) -> int:
    from .persona import ATTRS, FIELDS
    print("Writable fields — what a Parameters row may set as its `target`:\n")
    for path, s in FIELDS.items():
        d = "inherit" if s.default == "inherit" else s.default
        print(f"  {path:38} {s.dtype:6} {s.unit or '-':10} default={d}")
        if s.what:
            print(f"      {s.what}")
    print("\nReadable attributes — what a Parameters row may use in `applies_to`:\n")
    for name, a in ATTRS.items():
        print(f"  {name:20} {a.dtype:6} {a.what}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="personas",
        description="Persona schema and population sampler for the fire-egress project.",
    )
    ap.add_argument("--version", action="version", version=f"egress-personas {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--data", type=Path, default=DATA,
                       help="snapshot directory (default: data/)")

    def scen(p: argparse.ArgumentParser) -> None:
        p.add_argument("--scenario", default="night_fire12")
        p.add_argument("--seed", type=int, default=None,
                       help="default: the scenario's own default_seed")
        p.add_argument("--cohort", default=None,
                       help="build a cohort instead of the base building; "
                            "`personas cohorts --list` names them")

    p = sub.add_parser("init-data", help="write a starting set of tabs into data/")
    common(p)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init_data)

    p = sub.add_parser("init-sheet",
                       help="write one workbook to upload to Google Sheets")
    common(p)
    p.add_argument("--out-file", type=Path,
                   default=Path("Egress_Persona_Model.xlsx"))
    p.set_defaults(fn=cmd_init_sheet)

    p = sub.add_parser("pull", help="snapshot the Google Sheet into data/")
    common(p)
    p.add_argument("--sheet-url", help="the sheet's URL, straight from the address bar")
    p.add_argument("--sheet-id", help="the id alone, if you have it")
    p.add_argument("--tab", action="append", help="only this tab (repeatable)")
    p.add_argument("--token-file", help="file holding an OAuth access token")
    p.add_argument("--check", action="store_true",
                   help="say whether data/ is behind the Sheet and write nothing; "
                        "exits non-zero when it is")
    p.set_defaults(fn=cmd_pull)

    p = sub.add_parser("validate", help="check the snapshot and say where it is wrong")
    common(p)
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("build", help="sample a population and write it out")
    common(p)
    scen(p)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--generated-at", help="fix the timestamp, for reproducible output")
    p.add_argument("--pull", metavar="SHEET_URL",
                   help="refresh data/ from this Sheet first, then build from it")
    p.add_argument("--token-file", help="with --pull, an OAuth access token file")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("report", help="print the report for a sampled population")
    common(p)
    scen(p)
    p.add_argument("--out-file")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("compare", help="compare a sample against the archived roster")
    common(p)
    scen(p)
    p.add_argument("--against", type=Path,
                   default=Path("reference/legacy_roster_2026-09.csv"))
    p.add_argument("--out-file")
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("show", help="sample a persona and read them")
    common(p)
    scen(p)
    p.add_argument("--filter", default="all",
                   help="a subset to sample from; --list shows them all")
    p.add_argument("--id", help="a persona id (P0041), key (case:C01) or case id (C01)")
    p.add_argument("--floor", type=int, help="only this floor, as the building names it")
    p.add_argument("--unit", help="only this flat, e.g. 14A")
    p.add_argument("-n", "--count", type=int, default=1, help="how many to show")
    p.add_argument("--pick-seed", type=int,
                   help="which sample to draw; the same value always draws the same people")
    p.add_argument("--no-provenance", action="store_true",
                   help="leave out where each number came from")
    p.add_argument("--list", action="store_true",
                   help="count each subset instead of showing anybody")
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("explore",
                       help="write a self-contained page for browsing the population")
    common(p)
    scen(p)
    p.add_argument("--out-file", type=Path, default=None,
                   help="default: out/<scenario>-<seed>.explorer.html")
    p.add_argument("--generated-at", help="fix the timestamp, for reproducible output")
    p.set_defaults(fn=cmd_explore)

    p = sub.add_parser("distributions",
                       help="the makeup of the building: age, sex, mobility, tenure, "
                            "speed, ties")
    common(p)
    scen(p)
    p.add_argument("--json", action="store_true", help="as data rather than a report")
    p.add_argument("--out-file")
    p.set_defaults(fn=cmd_distributions)

    p = sub.add_parser("cohorts",
                       help="compare the base building against each cohort")
    common(p)
    p.add_argument("--scenario", default="night_fire12")
    p.add_argument("--cohort", action="append",
                   help="only this cohort (repeatable); default is all of them")
    p.add_argument("--seeds", type=int, default=5,
                   help="how many seeds per building (default 5)")
    p.add_argument("--first-seed", type=int, default=1)
    p.add_argument("--list", action="store_true",
                   help="name the cohorts and their questions instead of building them")
    p.add_argument("--out-file")
    p.set_defaults(fn=cmd_cohorts)

    p = sub.add_parser("schema", help="print the population JSON Schema")
    p.add_argument("--out-file")
    p.set_defaults(fn=cmd_schema)

    p = sub.add_parser("fields", help="list the writable fields and readable attributes")
    p.set_defaults(fn=cmd_fields)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
