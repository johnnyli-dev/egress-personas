"""The distribution vocabulary a Parameters row may draw from.

Each distribution declares its parameter names, so the validator can say
"weibull takes 2 parameters (scale, shape); p3 is set" instead of silently
ignoring a column somebody filled in. Pure Python on top of rng.Pcg32 — no
numeric dependency.
"""

from __future__ import annotations

import math
from typing import Any

from .rng import Pcg32

# dist -> the names of p1..pN, in order. Empty tuple means "takes no p columns".
PARAMS: dict[str, tuple[str, ...]] = {
    "const": ("value",),
    "uniform": ("lo", "hi"),
    "normal": ("mean", "sd"),
    "trunc_normal": ("mean", "sd", "lo", "hi"),
    "lognormal": ("log_mean", "log_sd"),
    "weibull": ("scale", "shape"),
    "triangular": ("lo", "mode", "hi"),
    "bernoulli": ("p",),
    "categorical": (),
}

#: Distributions whose draw is a bool rather than a number.
BOOL_DISTS = frozenset({"bernoulli"})

#: Distributions whose draw is one of `categories` rather than a number.
CATEGORICAL_DISTS = frozenset({"categorical"})


def names() -> list[str]:
    return sorted(PARAMS)


def arity(dist: str) -> int:
    return len(PARAMS[dist])


def _standard_normal(rng: Pcg32) -> float:
    """Box-Muller, as the simulation does it (population.rs:201-207)."""
    u1 = max(rng.unit(), 1e-12)
    u2 = rng.unit()
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def sample(
    dist: str,
    params: list[float | None],
    rng: Pcg32,
    *,
    categories: list[str] | None = None,
    weights: list[float] | None = None,
) -> Any:
    """One draw. `params` is p1..p4 with None for the unused tail."""
    p = params

    if dist == "const":
        return float(p[0])
    if dist == "uniform":
        return rng.range_f(float(p[0]), float(p[1]))
    if dist == "normal":
        return float(p[0]) + float(p[1]) * _standard_normal(rng)
    if dist == "trunc_normal":
        mean, sd, lo, hi = float(p[0]), float(p[1]), float(p[2]), float(p[3])
        # Rejection, then clamp. Sampling is cheap and the bounds in practice sit
        # 2+ sd out, so the loop almost never runs twice; the clamp is only there
        # so a pathological row cannot hang the generator.
        for _ in range(64):
            v = mean + sd * _standard_normal(rng)
            if lo <= v <= hi:
                return v
        return min(max(mean, lo), hi)
    if dist == "lognormal":
        return math.exp(float(p[0]) + float(p[1]) * _standard_normal(rng))
    if dist == "weibull":
        scale, shape = float(p[0]), float(p[1])
        u = max(rng.unit(), 1e-12)
        return scale * ((-math.log(u)) ** (1.0 / shape))
    if dist == "triangular":
        lo, mode, hi = float(p[0]), float(p[1]), float(p[2])
        u = rng.unit()
        c = (mode - lo) / (hi - lo) if hi > lo else 0.0
        if u < c:
            return lo + math.sqrt(u * (hi - lo) * (mode - lo))
        return hi - math.sqrt((1.0 - u) * (hi - lo) * (hi - mode))
    if dist == "bernoulli":
        return rng.chance(float(p[0]))
    if dist == "categorical":
        cats = categories or []
        ws = weights or [1.0] * len(cats)
        if not cats:
            raise ValueError("categorical needs categories")
        return cats[rng.weighted(ws)]

    raise ValueError(f"unknown dist {dist!r}")


def mean_of(dist: str, params: list[float | None]) -> float | None:
    """Analytic mean where one exists, for the report and the tests. None otherwise."""
    p = params
    try:
        if dist == "const":
            return float(p[0])
        if dist == "uniform":
            return (float(p[0]) + float(p[1])) / 2.0
        if dist in ("normal", "trunc_normal"):
            return float(p[0])
        if dist == "lognormal":
            return math.exp(float(p[0]) + float(p[1]) ** 2 / 2.0)
        if dist == "weibull":
            return float(p[0]) * math.gamma(1.0 + 1.0 / float(p[1]))
        if dist == "triangular":
            return (float(p[0]) + float(p[1]) + float(p[2])) / 3.0
        if dist == "bernoulli":
            return float(p[0])
    except (TypeError, ValueError):
        return None
    return None
