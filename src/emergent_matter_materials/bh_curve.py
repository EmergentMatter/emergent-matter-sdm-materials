"""Tabulated B-H curve data for soft-magnetic materials (v1.2.0).

`BHCurveData` stores a published (B, H) magnetization curve as paired
tuples, plus provenance fields matching the PropertyValue pattern
(s_source, s_condition, s_confidence, s_notes). It's a composite field
on `Electromagnetic` for materials where the FEM consumer needs the
full nonlinear curve, not just a single scalar μ_r.

Why a dedicated dataclass instead of two parallel tuples on
Electromagnetic:

  1. Provenance lives with the data. A B-H curve is a single sourced
     material property, not two loose arrays, and the catalog's
     philosophy is per-property provenance. Splitting it would force
     the citation into a neighboring field's s_notes, which the
     catalog explicitly doesn't do.
  2. Validator surface is cleaner. Length-match, monotonicity, and
     ferromagnetic-initial-slope checks belong on the composite, not
     reaching across two fields of the parent group.
  3. Matches the CrystalAnisotropy precedent (composite group of
     related multi-valued physics).

Why μ-vs-ν language matters in the validator:
For a B-H table, the physically relevant slope near the origin is
dB/dH = μ (permeability), not dH/dB = ν (reluctivity). Near origin
the inferred secant permeability ΔB/ΔH must be > μ₀ (ferromagnetic).
At high field the secant approaches μ₀ from above (saturation). The
final-slope check is a WARNING, not a hard failure: vendor tables
often stop before deep saturation.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Literal, get_args

#: `s_confidence` for a B-H curve is restricted to Tier 1 (see `PropertyValue`'s
#: source-priority hierarchy) -- a curve's provenance can't be looser than a
#: scalar property's.
_Tier1Confidence = Literal["measured", "datasheet", "standard"]

#: Runtime counterpart of `_Tier1Confidence`, derived with `get_args()` so it
#: can never drift from the Literal (STYLE.md: never hand-copy a Literal's
#: members into a separate tuple).
_TIER_1_CONFIDENCE: tuple[str, ...] = get_args(_Tier1Confidence)

#: Vacuum permeability μ₀ in H/m (= T·m/A = V·s/(A·m)). Used by the
#: ferromagnetic-initial-slope validator to distinguish soft-magnetic
#: materials from accidental non-magnetic curve entries.
MU_0_H_per_m: float = 4.0e-7 * math.pi

#: H threshold (A/m) above which we expect the final secant
#: permeability to be approaching μ₀ from above. Below this threshold
#: we suppress the final-slope warning because the table may legitimately
#: stop before deep saturation. 50,000 A/m corresponds roughly to the
#: well-saturated regime for silicon steels and Hiperco-class alloys.
_FINAL_SLOPE_WARN_H_THRESHOLD: float = 5.0e4

#: Multiplier on μ₀ above which the final secant slope triggers a warning
#: (i.e. ΔB/ΔH > _N · μ₀ at high H means saturation hasn't really set in).
_FINAL_SLOPE_WARN_RATIO: float = 2.0


@dataclass(frozen=True)
class BHCurveData:
    """A tabulated DC (or quasi-static) magnetization curve for a soft-
    magnetic material.

    Stored as paired ascending tables in SI: B in tesla, H in A/m. The
    catalog uses these directly: consumers (e.g. magnetostatic FEM)
    typically fit a monotonicity-preserving interpolant (PCHIP on ν =
    H/B is the canonical choice) at load time and evaluate ν(||B||)
    inside the FE constitutive law.

    Convention: tables trace the INITIAL magnetization (virgin / normal
    magnetization curve) unless `s_condition` states otherwise.
    Hysteresis loops are NOT stored at this schema level (different
    consumer; deferred to a future schema bump if a downstream solver
    needs them).

    Anisotropic materials (cold-rolled non-oriented electrical steel,
    grain-oriented silicon steel) must record direction in `s_condition`
    (e.g. "rolling direction" vs "transverse" vs "isotropic Epstein
    average"). v1.2 stores a SINGLE direction's curve per material;
    multi-direction storage is deferred until a downstream optimizer
    needs the tensor.

    Provenance attribution:
      - `s_source` cites the Tier-1 primary (vendor TDS, national
        standard, or industry compendium with vendor backing).
      - `s_condition` records DC vs AC frequency, temperature, gauge,
        annealing state, specimen orientation, test standard, and any
        other measurement context.
      - `s_confidence` is Tier-1 only (measured / datasheet / standard).
      - `s_notes` carries cross-references, conversion notes, and
        consumer warnings.
      - `s_digitization_method` is EMPTY for table-published curves.
        It is set ONLY when the curve was digitized from a graph (e.g.
        "WebPlotDigitizer on Metglas POWERLITE Figure 3, 12 points;
        approximate, ±3% on B-axis from grid resolution"). Mixing
        graph-digitized data with table-published data without this
        marker would corrupt downstream uncertainty budgets.

    Validation (`__post_init__`):
      1. `d_B_table_T` and `d_H_table_A_m` have equal length, ≥ 3 points.
      2. Both tables strictly ascending after the origin.
      3. Both start at ≥ 0 (origin allowed; below-origin = unphysical
         for a virgin curve).
      4. Initial secant permeability ΔB/ΔH > μ₀ over the first non-
         origin interval: material is ferromagnetic at low field.
         (Equivalently the initial secant reluctivity ΔH/ΔB < 1/μ₀.)
      5. Final secant permeability is a WARNING (not error): if H_max
         is in the saturation regime (>= 5e4 A/m for silicon steel /
         Hiperco class) AND the final secant slope is still > 2·μ₀,
         warn that the table may not span deep saturation.
      6. `s_confidence` must be Tier 1.
    """

    d_B_table_T: tuple[float, ...]
    d_H_table_A_m: tuple[float, ...]
    s_source: str
    s_condition: str
    s_confidence: _Tier1Confidence
    s_notes: str = ""
    # Set ONLY for graph-derived (non-table-published) curves. Empty
    # string means the curve was transcribed from a numeric vendor table.
    s_digitization_method: str = ""

    def __post_init__(self) -> None:
        n_B = len(self.d_B_table_T)
        n_H = len(self.d_H_table_A_m)

        # ── (1) Shape + length
        if n_B != n_H:
            raise ValueError(
                f"BHCurveData: table length mismatch, "
                f"|d_B_table_T| = {n_B}, |d_H_table_A_m| = {n_H}"
            )
        if n_B < 3:
            raise ValueError(f"BHCurveData: need at least 3 points to fit a curve, got {n_B}")

        # ── (2) Strict ascent
        if any(b1 <= b0 for b0, b1 in zip(self.d_B_table_T, self.d_B_table_T[1:], strict=False)):
            raise ValueError(
                f"BHCurveData: d_B_table_T must be strictly ascending. Got {self.d_B_table_T}"
            )
        if any(
            h1 <= h0 for h0, h1 in zip(self.d_H_table_A_m, self.d_H_table_A_m[1:], strict=False)
        ):
            raise ValueError(
                f"BHCurveData: d_H_table_A_m must be strictly ascending. Got {self.d_H_table_A_m}"
            )

        # ── (3) Non-negative start (origin allowed)
        if self.d_B_table_T[0] < 0.0:
            raise ValueError(
                f"BHCurveData: d_B_table_T must start at >= 0 "
                f"(virgin curve; origin allowed), got {self.d_B_table_T[0]}"
            )
        if self.d_H_table_A_m[0] < 0.0:
            raise ValueError(
                f"BHCurveData: d_H_table_A_m must start at >= 0 "
                f"(virgin curve; origin allowed), got {self.d_H_table_A_m[0]}"
            )

        # ── (4) Initial secant permeability ΔB/ΔH > μ₀ on the first
        #       non-origin interval. Equivalently the initial secant
        #       reluctivity ΔH/ΔB < 1/μ₀.
        #
        # If the table starts at literal (0, 0) we skip that point to
        # avoid 0/0 in the secant; otherwise use the first interval.
        i0 = 1 if (self.d_B_table_T[0] == 0.0 and self.d_H_table_A_m[0] == 0.0) else 0
        if i0 + 1 >= n_B:
            raise ValueError(
                "BHCurveData: need at least one non-origin interval to "
                "validate ferromagnetic initial slope"
            )
        d_dH_init = self.d_H_table_A_m[i0 + 1] - self.d_H_table_A_m[i0]
        if d_dH_init <= 0.0:
            # Already caught by (2), but defensive in case of future edits.
            raise ValueError("BHCurveData: degenerate ΔH on initial interval")
        d_mu_init = (self.d_B_table_T[i0 + 1] - self.d_B_table_T[i0]) / d_dH_init
        if d_mu_init <= MU_0_H_per_m:
            raise ValueError(
                f"BHCurveData: initial secant permeability ΔB/ΔH = "
                f"{d_mu_init:.3e} H/m is <= μ₀ ({MU_0_H_per_m:.3e}); "
                f"material is not ferromagnetic at low field? "
                f"Equivalently, initial reluctivity ΔH/ΔB = "
                f"{1.0 / d_mu_init:.3e} >= 1/μ₀ ({1.0 / MU_0_H_per_m:.3e})."
            )

        # ── (5) Final secant permeability: warning, not error.
        #       Vendor tables often stop before deep saturation; if the
        #       max H IS in the saturation regime AND the final slope
        #       is still well above μ₀, warn so the consumer knows the
        #       table may need conservative extrapolation.
        d_dH_final = self.d_H_table_A_m[-1] - self.d_H_table_A_m[-2]
        if d_dH_final > 0.0:
            d_mu_final = (self.d_B_table_T[-1] - self.d_B_table_T[-2]) / d_dH_final
            if (
                self.d_H_table_A_m[-1] >= _FINAL_SLOPE_WARN_H_THRESHOLD
                and d_mu_final > _FINAL_SLOPE_WARN_RATIO * MU_0_H_per_m
            ):
                warnings.warn(
                    f"BHCurveData: final secant permeability ΔB/ΔH = "
                    f"{d_mu_final:.3e} H/m is > {_FINAL_SLOPE_WARN_RATIO}·μ₀ "
                    f"at H = {self.d_H_table_A_m[-1]:.1e} A/m; table may "
                    f"not span deep saturation. Downstream consumers "
                    f"extrapolating beyond this point should clamp μ → μ₀ "
                    f"asymptotically.",
                    stacklevel=2,
                )

        # ── (6) Tier-1 confidence gate (Literal already restricts type;
        #       this catches runtime construction with a wider string).
        if self.s_confidence not in _TIER_1_CONFIDENCE:
            raise ValueError(
                f"BHCurveData.s_confidence must be Tier 1 "
                f"(measured / datasheet / standard), got "
                f"{self.s_confidence!r}"
            )

        # ── Provenance gate: s_source must be non-empty (matches the
        #    catalog-wide provenance gate enforced by the test suite).
        if not self.s_source.strip():
            raise ValueError("BHCurveData.s_source must be a non-empty Tier-1 citation")


__all__ = ["BHCurveData", "MU_0_H_per_m"]
