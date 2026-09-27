"""`applies_to`: a deliberately tiny, total filter language.

    expr := term ("and" term)*
    term := attribute op value
    op   := == | != | < | <= | > | >= | in | not in
    value := number | 'quoted string' | bareword | [a, b, c] | TRUE | FALSE

No `or`, no parentheses, no arithmetic, no negation beyond `!=` / `not in`.

`or` is always expressible as two rows, and two rows are separately citable,
separately toggleable, and checkable by eye — which is what a parameter registry
wants. Parentheses are where sheet-authored predicates stop being reviewable.

An empty expression matches everyone. A comparison against a missing attribute is
false, and the caller is told, rather than the row quietly matching nobody.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Any

OPS = ("not in", "in", "<=", ">=", "==", "!=", "<", ">")

_TOKEN = re.compile(
    r"""\s*(?:
        (?P<lbracket>\[) | (?P<rbracket>\]) | (?P<comma>,)
      | (?P<op>not\s+in\b|\bin\b|<=|>=|==|!=|<|>)
      | (?P<and>\band\b)
      | (?P<or>\bor\b|\|\||&&)
      | (?P<paren>[()])
      | (?P<arith>[+*/%^])
      | (?P<string>'[^']*'|"[^"]*")
      | (?P<number>-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)
      | (?P<word>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<bad>\S)
    )""",
    re.VERBOSE,
)

_TRUE = {"true", "yes", "y", "1"}
_FALSE = {"false", "no", "n", "0"}


class FilterError(ValueError):
    """A problem in an applies_to expression, phrased for whoever typed it."""


@dataclass(frozen=True)
class Clause:
    attr: str
    op: str
    value: Any

    def __str__(self) -> str:
        v = self.value
        shown = f"[{', '.join(map(str, v))}]" if isinstance(v, list) else str(v)
        return f"{self.attr} {self.op} {shown}"


@dataclass(frozen=True)
class Predicate:
    clauses: tuple[Clause, ...]

    def __bool__(self) -> bool:
        return bool(self.clauses)

    def __str__(self) -> str:
        return " and ".join(str(c) for c in self.clauses) or "(everyone)"

    @property
    def attrs(self) -> set[str]:
        return {c.attr for c in self.clauses}


def _tokens(expr: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    pos = 0
    while pos < len(expr):
        m = _TOKEN.match(expr, pos)
        if not m or m.end() == pos:
            if expr[pos:].strip() == "":
                break
            raise FilterError(f"cannot read {expr[pos:].strip()!r}")
        pos = m.end()
        kind = m.lastgroup
        text = m.group(kind)
        if kind == "or":
            raise FilterError(
                f"{text!r} is not supported — write two rows instead, so each can "
                "carry its own source and be switched off on its own"
            )
        if kind == "paren":
            raise FilterError("parentheses are not supported — keep each row to a flat 'and' chain")
        if kind == "arith":
            raise FilterError(f"arithmetic ({text!r}) is not supported in applies_to")
        if kind == "bad":
            raise FilterError(f"cannot read {text!r}")
        out.append((kind, text))
    return out


def _literal(text: str, kind: str) -> Any:
    if kind == "number":
        return float(text) if ("." in text or "e" in text.lower()) else int(text)
    if kind == "string":
        return text[1:-1]
    low = text.lower()
    if low in _TRUE:
        return True
    if low in _FALSE:
        return False
    return text


def parse(expr: str, known: set[str] | None = None) -> Predicate:
    """Parse `expr`. With `known`, an unknown attribute raises with a suggestion."""
    if expr is None or not expr.strip():
        return Predicate(())

    toks = _tokens(expr)
    clauses: list[Clause] = []
    i = 0
    while i < len(toks):
        if toks[i][0] != "word":
            raise FilterError(f"expected an attribute name, found {toks[i][1]!r}")
        attr = toks[i][1]
        if known is not None and attr not in known:
            close = difflib.get_close_matches(attr, sorted(known), n=1, cutoff=0.6)
            hint = f" — did you mean {close[0]!r}?" if close else ""
            raise FilterError(
                f"unknown attribute {attr!r}{hint} "
                f"(readable attributes are the Attributes registry; {len(known)} defined)"
            )
        i += 1
        if i >= len(toks) or toks[i][0] != "op":
            found = toks[i][1] if i < len(toks) else "end of expression"
            raise FilterError(
                f"{attr}: expected one of {', '.join(OPS)}, found {found!r}"
            )
        op = re.sub(r"\s+", " ", toks[i][1])
        i += 1
        if i >= len(toks):
            raise FilterError(f"{attr} {op}: expected a value")

        if toks[i][0] == "lbracket":
            i += 1
            items: list[Any] = []
            while i < len(toks) and toks[i][0] != "rbracket":
                if toks[i][0] == "comma":
                    i += 1
                    continue
                items.append(_literal(toks[i][1], toks[i][0]))
                i += 1
            if i >= len(toks):
                raise FilterError(f"{attr} {op} [...]: missing closing ']'")
            i += 1
            if op not in ("in", "not in"):
                raise FilterError(f"{attr}: a list needs 'in' or 'not in', not {op!r}")
            value: Any = items
        else:
            value = _literal(toks[i][1], toks[i][0])
            i += 1
            if op in ("in", "not in") and not isinstance(value, list):
                value = [value]

        clauses.append(Clause(attr, op, value))

        if i < len(toks):
            if toks[i][0] != "and":
                raise FilterError(f"expected 'and' between conditions, found {toks[i][1]!r}")
            i += 1
            if i >= len(toks):
                raise FilterError("expression ends with 'and'")

    return Predicate(tuple(clauses))


def _cmp(op: str, left: Any, right: Any) -> bool:
    if op == "in":
        return left in right
    if op == "not in":
        return left not in right
    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    try:
        if op == "<":
            return left < right
        if op == "<=":
            return left <= right
        if op == ">":
            return left > right
        if op == ">=":
            return left >= right
    except TypeError:
        return False
    raise FilterError(f"unknown operator {op!r}")


def matches(pred: Predicate, attrs: dict[str, Any], missing: set[str] | None = None) -> bool:
    """True when every clause holds. A clause on a missing attribute is false."""
    for c in pred.clauses:
        if c.attr not in attrs or attrs[c.attr] is None:
            if missing is not None:
                missing.add(c.attr)
            return False
        if not _cmp(c.op, attrs[c.attr], c.value):
            return False
    return True
