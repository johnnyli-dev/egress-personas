"""Mapping canonical outputs onto a particular engine's field names.

An adapter is a mapping, not a model. Keeping it as data in `adapters/*.toml` rather
than as code is the point: the population is computed once, engine-independently, and
an engine we have not met yet needs a file rather than a patch. It also keeps the
question "which of our heuristics can *this* engine act on?" answerable, because an
adapter lists what it cannot use as explicitly as what it can.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Shipped adapters live beside the package root, so the repository is the catalogue.
DEFAULT_DIR = Path("adapters")


@dataclass
class Adapter:
    id: str
    name: str
    note: str = ""
    language: str = ""
    mapping: dict[str, dict[str, str]] = field(default_factory=dict)
    unsupported: dict[str, str] = field(default_factory=dict)
    path: Path | None = None

    def field_for(self, output_id: str) -> str | None:
        got = self.mapping.get(output_id)
        return got.get("field") if got else None

    def supports(self, output_id: str) -> bool:
        return output_id in self.mapping

    def render(self, values: dict[str, Any]) -> dict[str, Any]:
        """One resident's compiled values, under this engine's names."""
        out: dict[str, Any] = {}
        for output_id, value in values.items():
            name = self.field_for(output_id)
            if name is not None:
                out[name] = value
        return out


def load(path: Path) -> Adapter:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    head = data.get("adapter", {})
    return Adapter(
        id=head.get("id") or Path(path).stem,
        name=head.get("name") or Path(path).stem,
        note=(head.get("note") or "").strip(),
        language=head.get("language") or "",
        mapping=data.get("map", {}),
        unsupported=data.get("unsupported", {}),
        path=Path(path),
    )


def available(directory: Path | None = None) -> dict[str, Adapter]:
    d = Path(directory or DEFAULT_DIR)
    if not d.exists():
        return {}
    out = {}
    for f in sorted(d.glob("*.toml")):
        try:
            a = load(f)
        except (tomllib.TOMLDecodeError, OSError):
            continue
        out[a.id] = a
    return out


def resolve(name: str | None, directory: Path | None = None) -> Adapter:
    found = available(directory)
    if not found:
        raise FileNotFoundError(
            f"no adapters in {Path(directory or DEFAULT_DIR)}/. An adapter is a small "
            f"TOML file mapping canonical outputs to one engine's field names; "
            f"adapters/generic.toml is the identity mapping."
        )
    key = name or "generic"
    if key not in found:
        raise KeyError(
            f"no adapter {key!r}. Available: {', '.join(sorted(found))}."
        )
    return found[key]


def reach(adapter: Adapter, outputs: dict[str, Any], effects: list[Any],
          cover: dict[str, Any]) -> dict[str, Any]:
    """What this engine can and cannot act on, of what we produce.

    The end of the chain the whole pipeline exists to make visible: a heuristic reaches
    a persona field, an effect carries that field to a canonical output, and an adapter
    either hands that output to an engine or says it cannot.
    """
    produced = {e.output for e in effects}
    supported = {o for o in produced if adapter.supports(o)}
    blocked = {o for o in produced if not adapter.supports(o)}
    fields_via: dict[str, list[str]] = {}
    for f, hows in (cover.get("how") or {}).items():
        for how in hows:
            eid = how.split()[0]
            eff = next((e for e in effects if e.id == eid), None)
            if eff and eff.output in supported:
                fields_via.setdefault(f, []).append(f"{eid} → {eff.output}")
    return {
        "adapter": adapter.id,
        "adapter_name": adapter.name,
        "outputs_supported": sorted(supported),
        "outputs_blocked": sorted(blocked),
        "why_blocked": {o: adapter.unsupported.get(o, "not in this adapter's map")
                        for o in sorted(blocked)},
        "registry_fields_that_reach_this_engine": dict(sorted(fields_via.items())),
    }
