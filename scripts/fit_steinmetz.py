"""Fit multi-point Steinmetz coefficients (v1.4.0 provenance script).

Produces the (alpha, beta) exponents stored on
``m270_35a_silicon_steel.electromagnetic.steinmetz`` and
``hiperco_50.electromagnetic.steinmetz``. Run it to reproduce:

    uv run python scripts/fit_steinmetz.py

Convention (v1.4.0, "grid-fitted exponents, anchor-derived k"):

1. Exponents (alpha, beta) come from an ordinary log-space least-squares
   fit of ln(P) = c + alpha*ln(f) + beta*ln(B) over the vendor's
   published multi-frequency loss grid (free intercept).
2. The stored k is then RE-DERIVED from the grade-defining reference
   point: k = P_ref / (f_ref^alpha * B_ref^beta). This keeps both
   catalog rules intact: k is computed in code (never hardcoded) and
   the SteinmetzData round-trip validator passes exactly at the anchor.
   The shift vs the free-fit intercept equals the fit's residual at the
   anchor point (reported below; ~1% for both materials, negligible
   against the single-power-law model error).
3. Residual statistics of the final (re-anchored) model over the source
   grid are reported and recorded in the catalog s_notes.

Data provenance (both grids transcribed from table-published vendor
PDFs read directly 2026-06-01 / re-verified 2026-06-10:
no graph digitization):

- M270-35A: Cogent Surahammars Bruks 'Typical data for SURA M270-35A'
  (June 2008) loss table, W/kg at 50/100/200/400 Hz. Fit window is
  restricted to the motor-relevant region f in [50, 400] Hz and
  B in [0.5, 1.8] T (B > 1.5 T rows are published at 50 Hz only).
  The 1000/2500 Hz columns and B < 0.5 T rows are deliberately
  EXCLUDED: a single Steinmetz power law cannot span 50-2500 Hz
  (effective alpha rises with eddy dominance), and the target
  machines operate at power frequencies.
- Hiperco 50: Carpenter E200 (Rev. v11-22) p.2 'AC CORE LOSS' table,
  0.014 in (0.355 mm) strip, Typical MAGNETIC anneal rows (matches the
  catalog hiperco_50 entry's condition): full 3x3 factorial,
  60/400/1000 Hz x 1.0/1.5/2.0 T.
"""

from __future__ import annotations

import math

# ── Source grids ────────────────────────────────────────────────────────────

# Cogent SURA M270-35A (June 2008), W/kg columns at 50/100/200/400 Hz.
# {f_Hz: [(B_T, P_W_per_kg), ...]}
M270_GRID: dict[float, list[tuple[float, float]]] = {
    50.0: [
        (0.5, 0.31),
        (0.6, 0.43),
        (0.7, 0.54),
        (0.8, 0.68),
        (0.9, 0.83),
        (1.0, 1.01),
        (1.1, 1.20),
        (1.2, 1.42),
        (1.3, 1.70),
        (1.4, 2.12),
        (1.5, 2.47),
        (1.6, 2.80),
        (1.7, 3.05),
        (1.8, 3.25),
    ],
    100.0: [
        (0.5, 0.80),
        (0.6, 1.06),
        (0.7, 1.38),
        (0.8, 1.73),
        (0.9, 2.10),
        (1.0, 2.51),
        (1.1, 2.98),
        (1.2, 3.51),
        (1.3, 4.15),
        (1.4, 4.97),
        (1.5, 5.92),
    ],
    200.0: [
        (0.5, 1.91),
        (0.6, 2.61),
        (0.7, 3.39),
        (0.8, 4.26),
        (0.9, 5.23),
        (1.0, 6.30),
        (1.1, 7.51),
        (1.2, 8.88),
        (1.3, 10.5),
        (1.4, 12.5),
        (1.5, 14.9),
    ],
    400.0: [
        (0.5, 4.94),
        (0.6, 6.84),
        (0.7, 9.00),
        (0.8, 11.4),
        (0.9, 14.2),
        (1.0, 17.3),
        (1.1, 20.9),
        (1.2, 24.9),
        (1.3, 29.5),
        (1.4, 35.4),
        (1.5, 41.8),
    ],
}
M270_REF = (50.0, 1.5, 2.47)  # grade-defining point, Cogent TYPICAL value
# (NOT the EN 10106 grade-max 2.70 stored in
# core_loss; see catalog s_notes)

# Carpenter Hiperco 50 E200 p.2, 0.014 in strip, Typical magnetic anneal.
HIPERCO_GRID: dict[float, list[tuple[float, float]]] = {
    60.0: [(1.0, 1.5), (1.5, 2.5), (2.0, 3.7)],
    400.0: [(1.0, 15.0), (1.5, 35.0), (2.0, 63.0)],
    1000.0: [(1.0, 60.0), (1.5, 160.0), (2.0, 340.0)],
}
HIPERCO_REF = (60.0, 1.5, 2.5)  # matches the existing hiperco_50 core_loss PV


# ── Fit machinery ───────────────────────────────────────────────────────────


def _flatten(grid: dict[float, list[tuple[float, float]]]):
    return [(f, B, P) for f, rows in grid.items() for (B, P) in rows]


def _solve3(A: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting for a 3x3 system."""
    M = [row[:] + [bi] for row, bi in zip(A, b, strict=False)]
    n = 3
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        for r in range(col + 1, n):
            fac = M[r][col] / M[col][col]
            for c in range(col, n + 1):
                M[r][c] -= fac * M[col][c]
    x = [0.0] * n
    for r in reversed(range(n)):
        x[r] = (M[r][n] - sum(M[r][c] * x[c] for c in range(r + 1, n))) / M[r][r]
    return x


def fit_free_lsq(grid) -> tuple[float, float, float]:
    """Free log-space LSQ: ln P = c + alpha ln f + beta ln B.

    Returns (c, alpha, beta).
    """
    pts = _flatten(grid)
    X = [(1.0, math.log(f), math.log(B)) for f, B, _ in pts]
    z = [math.log(P) for _, _, P in pts]
    # Normal equations (X^T X) p = X^T z
    A = [[sum(xi[r] * xi[c] for xi in X) for c in range(3)] for r in range(3)]
    b = [sum(xi[r] * zi for xi, zi in zip(X, z, strict=False)) for r in range(3)]
    c, alpha, beta = _solve3(A, b)
    return c, alpha, beta


def residuals(grid, k: float, alpha: float, beta: float):
    """Relative residuals of P_model = k f^alpha B^beta over the grid."""
    rels = []
    for f, B, P in _flatten(grid):
        P_model = k * f**alpha * B**beta
        rels.append((P_model - P) / P)
    n = len(rels)
    rms = math.sqrt(sum(r * r for r in rels) / n)
    worst = max(rels, key=abs)
    return n, rms, worst


def report(s_name: str, grid, ref: tuple[float, float, float]) -> None:
    f_ref, B_ref, P_ref = ref
    c, alpha, beta = fit_free_lsq(grid)
    k_free = math.exp(c)
    # Re-anchor k at the grade-defining reference point.
    k = P_ref / (f_ref**alpha * B_ref**beta)
    d_anchor_resid = k_free * f_ref**alpha * B_ref**beta / P_ref - 1.0
    n, rms, worst = residuals(grid, k, alpha, beta)
    print(f"== {s_name} ==")
    print(f"  n_points            = {n}")
    print(f"  alpha (grid LSQ)    = {alpha!r}")
    print(f"  beta  (grid LSQ)    = {beta!r}")
    print(f"  k_free (LSQ)        = {k_free!r}")
    print(f"  k (anchor-derived)  = {k!r}   <- stored; k = {P_ref}/({f_ref}^alpha * {B_ref}^beta)")
    print(f"  free-fit residual at anchor = {d_anchor_resid:+.2%}")
    print(f"  re-anchored model over grid: RMS rel err = {rms:.2%}, worst = {worst:+.2%}")
    print()


if __name__ == "__main__":
    report("m270_35a_silicon_steel (50-400 Hz x 0.5-1.8 T window)", M270_GRID, M270_REF)
    report("hiperco_50 (60/400/1000 Hz x 1.0/1.5/2.0 T factorial)", HIPERCO_GRID, HIPERCO_REF)
