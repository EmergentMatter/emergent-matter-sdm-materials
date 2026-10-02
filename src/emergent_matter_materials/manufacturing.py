"""Manufacturing property group.

Captures **intrinsic / process-family** manufacturing guidance for a
material: what processes can produce it, what nominal feature sizes
those processes typically achieve, what shrinkage to plan for, what
anisotropy the as-printed part will show.

**NOT a machine-specific preset.**
Min wall thickness, layer height, anisotropy factor, and overhang
limits are never purely material properties: they're material ×
process × machine × geometry. The values in ``ProcessFit`` are
**process-family defaults** equivalent to "Shigley's recommended
clearances": a starting point that a designer or optimizer uses
before machine-specific calibration. Machine-tuned presets (Formlabs
Fuse 1+ Nylon at 30 W, Prusa Core One+ PLA at 0.2 mm, Bambu X1 settings)
belong in ``emergent-matter-sdm-processes``, which consumes these
defaults and overrides them per machine.

**Process keys.**
``Manufacturing.process_fit`` is keyed by a short process identifier
matching what consumers typically pass through (and what
``emergent-matter-sdm-processes`` resolves against). Conventions:

- ``"FFF_PLA"``, ``"FFF_PETG"``, ``"FFF_ABS"``, ``"FFF_NYLON"``,
  ``"FFF_PEEK"``: fused filament fabrication, family by feed material
- ``"SLS_PA12"``, ``"SLS_PA11"``: selective laser sintering, by polymer
- ``"MJF_PA12"``: multi jet fusion
- ``"SLA_TOUGH"``, ``"SLA_RIGID"``: stereolithography, by resin family
- ``"CNC_BILLET"``, ``"CNC_TUBE"``: subtractive
- ``"CASTING_SAND"``, ``"CASTING_DIE"``, ``"CASTING_INVESTMENT"``
- ``"FORGING"``, ``"SHEET_METAL"``, ``"EDM_WIRE"``
"""

from __future__ import annotations

from dataclasses import dataclass, field

from emergent_matter_materials.property_value import PropertyValue
from emergent_matter_materials.validation import _validate_group_units


@dataclass(frozen=True)
class ProcessFit:
    """Process-family default values, NOT a machine constraint.

    See module docstring on the material × process × machine ×
    geometry distinction. Treat these as the starting point a designer
    or optimizer uses before machine-specific calibration.
    """

    # All fields optional under v0.2.0 "Tier 1 only" policy
    shrinkage_linear: PropertyValue | None = None  # dimensionless fraction
    min_wall_thickness: PropertyValue | None = None  # m
    min_feature_size: PropertyValue | None = None  # m
    anisotropy_factor_z_vs_xy: PropertyValue | None = None
    max_unsupported_overhang: PropertyValue | None = None  # degrees
    typical_layer_height: PropertyValue | None = None  # m

    def __post_init__(self) -> None:
        _validate_group_units(
            self,
            group_fields={
                "shrinkage_linear",
                "min_wall_thickness",
                "min_feature_size",
                "anisotropy_factor_z_vs_xy",
                "max_unsupported_overhang",
                "typical_layer_height",
            },
            b_optional=True,
        )

        # Shrinkage in [0, 0.10], only if present
        if self.shrinkage_linear is not None and not (0.0 <= self.shrinkage_linear.d_value <= 0.10):
            raise ValueError(
                f"shrinkage_linear must be in [0.0, 0.10], "
                f"got {self.shrinkage_linear.d_value} "
                f"(value > 0.10 is almost certainly a unit error: "
                f"did you mean 0.005 instead of 5.0?)"
            )

        # Anisotropy factor in (0, 1]: Z direction is at-best as
        # strong as XY (factor=1.0); usually weaker (factor<1).
        if self.anisotropy_factor_z_vs_xy is not None:
            f_val = self.anisotropy_factor_z_vs_xy.d_value
            if not (0.0 < f_val <= 1.0):
                raise ValueError(
                    f"anisotropy_factor_z_vs_xy must be in (0.0, 1.0], "
                    f"got {f_val} "
                    f"(Z is never STRONGER than XY in additive processes)"
                )

        # Overhang angle in [0, 90]
        if self.max_unsupported_overhang is not None:
            angle = self.max_unsupported_overhang.d_value
            if not (0.0 <= angle <= 90.0):
                raise ValueError(
                    f"max_unsupported_overhang must be in [0, 90] degrees, got {angle}"
                )

        # Positivity for sizes
        for f_name in ("min_wall_thickness", "min_feature_size", "typical_layer_height"):
            pv = getattr(self, f_name)
            if pv is not None and pv.d_value <= 0.0:
                raise ValueError(f"ProcessFit.{f_name} must be positive, got {pv.d_value}")


@dataclass(frozen=True)
class Manufacturing:
    """Material's intrinsic / process-family manufacturing guidance.

    See ``ProcessFit`` docstring on the machine-constraint distinction.
    """

    s_recommended_processes: tuple[str, ...]
    process_fit: dict[str, ProcessFit] = field(default_factory=dict)
    b_post_processing_required: bool = False  # annealing, magnetization, polishing

    def __post_init__(self) -> None:
        # Sanity: every key in process_fit should be in
        # s_recommended_processes (and ideally vice-versa, but
        # we allow a process to be listed without a ProcessFit entry
        # for v0.1: fits will be filled in over time)
        for s_key in self.process_fit:
            if s_key not in self.s_recommended_processes:
                raise ValueError(
                    f"Manufacturing.process_fit has key {s_key!r} that's "
                    f"not in s_recommended_processes "
                    f"{self.s_recommended_processes}"
                )

    # ── Hot-path accessors

    def fit_for(self, s_process: str) -> ProcessFit:
        """Return the ProcessFit for a given process key, or raise."""
        if s_process not in self.process_fit:
            raise ValueError(
                f"No ProcessFit for {s_process!r}. "
                f"Recommended processes: {self.s_recommended_processes}. "
                f"Available fits: {sorted(self.process_fit)}"
            )
        return self.process_fit[s_process]


__all__ = ["Manufacturing", "ProcessFit"]
