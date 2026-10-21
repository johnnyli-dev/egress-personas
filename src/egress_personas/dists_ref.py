"""Reference distributions, and reading a value off one at a given quantile.

A distribution here is a **published fit**, not an engine's setting. Lovreglio et al.
(2019) fitted residential pre-movement to a Weibull; that is a fact about the
literature, and an engine that uses it is downstream of the paper rather than the
source of it. So the parameters live on the Sheet with their citation, and this module
only does the arithmetic.

Why quantiles. A persona could be given an absolute pre-movement time, but that would
throw away a distribution fitted to 149 and 78 observations and substitute a guess. So
the compiler does something narrower and more defensible: the distribution keeps the
shape of the population, and the persona decides **where in it a given resident sits**.
The marginal comes out identical — there is a test — while who is early and who is late
becomes something the model explains.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

FAMILIES = ("weibull", "uniform", "normal", "lognormal", "triangular",
            "bernoulli", "empirical_curve", "const")


@dataclass(frozen=True)
class Reference:
    """One reference distribution, as the Sheet states it."""

    id: str
    name: str
    family: str
    unit: str
    params: tuple[float | None, ...]
    curve: tuple[tuple[float, float], ...] = ()
    applies_when: str = ""
    evidence: str = "INVENTED"
    sources: tuple[str, ...] = ()
    finding: str = ""

    def ppf(self, q: float) -> Any:
        """The value at quantile `q`. A higher quantile is always a *larger* value."""
        q = min(max(float(q), 1e-9), 1.0 - 1e-9)
        p = self.params
        f = self.family
        if f == "const":
            return float(p[0])
        if f == "uniform":
            return float(p[0]) + q * (float(p[1]) - float(p[0]))
        if f == "weibull":
            return float(p[0]) * ((-math.log(1.0 - q)) ** (1.0 / float(p[1])))
        if f == "normal":
            return float(p[0]) + float(p[1]) * _probit(q)
        if f == "lognormal":
            return math.exp(float(p[0]) + float(p[1]) * _probit(q))
        if f == "triangular":
            lo, mode, hi = float(p[0]), float(p[1]), float(p[2])
            c = (mode - lo) / (hi - lo) if hi > lo else 0.0
            if q < c:
                return lo + math.sqrt(q * (hi - lo) * (mode - lo))
            return hi - math.sqrt((1.0 - q) * (hi - lo) * (hi - mode))
        if f == "bernoulli":
            # True for the top `p` of the range, so the share is exactly `p` and which
            # residents it is becomes the compiler's business.
            return q >= 1.0 - float(p[0])
        if f == "empirical_curve":
            return self._curve_ppf(q)
        raise ValueError(f"unknown distribution family {f!r}")

    def _curve_ppf(self, q: float) -> float:
        """Invert a measured [value, share-at-or-below] curve.

        The curve is stated the way such things are published — the share of people who
        turn back at or below a visibility, say — so a higher quantile means a more
        tolerant resident and the share argument runs the other way.
        """
        if not self.curve:
            return 0.0
        u = 1.0 - q
        pts = self.curve
        if u >= pts[0][1]:
            return pts[0][0]
        for (v0, s0), (v1, s1) in zip(pts, pts[1:]):
            if u >= s1:
                return v0 + (v1 - v0) * (s0 - u) / max(s0 - s1, 1e-9)
        return pts[-1][0]

    def mean_estimate(self, n: int = 4000) -> float | None:
        """The mean by quadrature on the quantile, for the report and the tests."""
        try:
            vals = [self.ppf((i + 0.5) / n) for i in range(n)]
        except (ValueError, TypeError, IndexError):
            return None
        nums = [float(v) for v in vals if isinstance(v, (int, float, bool))]
        return sum(nums) / len(nums) if nums else None


def _probit(q: float) -> float:
    """Inverse standard normal CDF, Acklam's rational approximation."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if q < pl:
        r = math.sqrt(-2 * math.log(q))
        return (((((c[0]*r+c[1])*r+c[2])*r+c[3])*r+c[4])*r+c[5]) / \
               ((((d[0]*r+d[1])*r+d[2])*r+d[3])*r+1)
    if q > ph:
        r = math.sqrt(-2 * math.log(1 - q))
        return -(((((c[0]*r+c[1])*r+c[2])*r+c[3])*r+c[4])*r+c[5]) / \
                ((((d[0]*r+d[1])*r+d[2])*r+d[3])*r+1)
    r = q - 0.5
    s = r * r
    return (((((a[0]*s+a[1])*s+a[2])*s+a[3])*s+a[4])*s+a[5])*r / \
           (((((b[0]*s+b[1])*s+b[2])*s+b[3])*s+b[4])*s+1)
