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


def cmd_pull(args: argparse.Namespace) -> int:
    from .sheet import pull
    from .validate import problems
    token = None
    if args.token_file:
        token = Path(args.token_file).read_text().strip()
    meta = pull(args.sheet_id, args.data, token=token, only=args.tab or None)
    print(f"pulled {len(meta['tabs'])} tab(s) from {args.sheet_id} at {meta['pulled_at']}")
    probs = problems(_load(args.data))
    if probs:
        print(f"\n{len(probs)} problem(s) in the new snapshot:", file=sys.stderr)
        for p in probs:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("no problems.")
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
    tables = _checked(args.data)
    pop = sample(tables, args.scenario, args.seed)
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
    pop = sample(tables, args.scenario, args.seed)
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
    pop = sample(tables, args.scenario, args.seed)
    text = compare(pop, args.against)
    if args.out_file:
        Path(args.out_file).write_text(text, encoding="utf-8")
        print(f"wrote {args.out_file}")
    else:
        print(text)
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

    p = sub.add_parser("init-data", help="write a starting set of tabs into data/")
    common(p)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init_data)

    p = sub.add_parser("pull", help="snapshot the Google Sheet into data/")
    common(p)
    p.add_argument("--sheet-id", required=True)
    p.add_argument("--tab", action="append", help="only this tab (repeatable)")
    p.add_argument("--token-file", help="file holding an OAuth access token")
    p.set_defaults(fn=cmd_pull)

    p = sub.add_parser("validate", help="check the snapshot and say where it is wrong")
    common(p)
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("build", help="sample a population and write it out")
    common(p)
    scen(p)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--generated-at", help="fix the timestamp, for reproducible output")
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

    p = sub.add_parser("schema", help="print the population JSON Schema")
    p.add_argument("--out-file")
    p.set_defaults(fn=cmd_schema)

    p = sub.add_parser("fields", help="list the writable fields and readable attributes")
    p.set_defaults(fn=cmd_fields)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
