"""Deterministic random draws, one independent stream per draw.

`Pcg32` is a port of the simulation's own generator (FireEgress-3dsim,
crates/fe-core/src/rng.rs): PCG32 XSH-RR 64/32. That file is deliberately
self-contained rather than pulling in a library, so that a seed keeps meaning the
same thing; this port is here for the same reason, and it is why this package
needs no numeric dependency.

The simulation gives each *subsystem* its own stream so that changing an agent
rule does not perturb the fire. We take the same idea one level finer: every
single draw gets its own stream, keyed by a content hash of a stable path. So
editing one persona cannot move another's numbers, and editing one parameter row
moves only the fields that row contributes to.
"""

from __future__ import annotations

import hashlib

_MASK64 = (1 << 64) - 1
_MASK32 = (1 << 32) - 1
_MULT = 6364136223846793005


class Pcg32:
    """PCG32 XSH-RR 64/32. Mirrors crates/fe-core/src/rng.rs."""

    __slots__ = ("state", "inc")

    def __init__(self, seed: int, stream: int) -> None:
        self.inc = ((stream << 1) | 1) & _MASK64
        self.state = 0
        self.next_u32()
        self.state = (self.state + (seed & _MASK64)) & _MASK64
        self.next_u32()

    def next_u32(self) -> int:
        old = self.state
        self.state = (old * _MULT + self.inc) & _MASK64
        xorshifted = (((old >> 18) ^ old) >> 27) & _MASK32
        rot = (old >> 59) & 31
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & _MASK32

    def unit(self) -> float:
        """Uniform in [0, 1)."""
        return self.next_u32() / 4294967296.0

    def range_f(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * self.unit()

    def chance(self, p: float) -> bool:
        if p <= 0.0:
            return False
        if p >= 1.0:
            return True
        return self.unit() < p

    def index(self, n: int) -> int:
        if n <= 0:
            raise ValueError("index(n) needs n > 0")
        return int(self.unit() * n) % n

    def weighted(self, weights: list[float]) -> int:
        """Index chosen in proportion to `weights`. All-zero weights is an error."""
        total = sum(w for w in weights if w > 0)
        if total <= 0:
            raise ValueError("weighted() needs at least one positive weight")
        r = self.unit() * total
        acc = 0.0
        for i, w in enumerate(weights):
            if w <= 0:
                continue
            acc += w
            if r < acc:
                return i
        # Only reachable through floating-point round-off on the last bucket.
        return max(i for i, w in enumerate(weights) if w > 0)


def stream_of(path: str) -> tuple[int, int]:
    """The (seed mask, stream) pair a draw path hashes to."""
    d = hashlib.blake2b(path.encode("utf-8"), digest_size=16).digest()
    return int.from_bytes(d[:8], "big"), int.from_bytes(d[8:], "big") | 1


def draw_rng(seed: int, path: str) -> Pcg32:
    """A generator of its own for `path`, reproducible from (seed, path) alone."""
    mask, stream = stream_of(path)
    return Pcg32((seed & _MASK64) ^ mask, stream)
