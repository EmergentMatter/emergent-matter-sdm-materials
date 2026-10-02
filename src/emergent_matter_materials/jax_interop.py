"""JAX interop: materialize a Material as a JAX-friendly pytree.

The materials catalog is plain Python by design: discrete material choice
is the optimizer's problem via SIMP-style continuous relaxation, not
something the catalog itself should be JAX-traceable for (see CLAUDE.md's
"JAX integration" section). But once an optimizer has picked a
material, or wants to interpolate properties between two materials in
a continuous-relaxation mixing field: it usually wants the numeric
fields packed into a `jnp` pytree.

``to_jax_pytree(material, s_missing=...)`` does this conversion in one
call, with an explicit policy for absent property groups / fields.

**Why a missing-policy parameter exists.**
A material's optional fields (NdFeB has no yield_stress in the
traditional sense, PLA has no remanence) get represented as ``None``
in the catalog. When converting to a JAX pytree, that ``None`` is a
landmine: JAX doesn't like mixing None and jnp arrays in a pytree
the optimizer expects to be all-numeric. The three policies trade
off different failure modes:

- ``"error"`` (default): raise ``ValueError`` if any field on a
  populated group is None. Right for an optimizer context that
  requires the data: better a loud failure than silent corruption.
- ``"omit"``: drop None fields from the output pytree entirely.
  Output shape varies per material; downstream consumers must handle
  the absence. Useful for general introspection.
- ``"nan"``: fill missing fields with ``jnp.nan``. Output shape is
  identical across materials, so consumers can build a missing-mask
  themselves. Useful for analysis where pytree shape stability
  matters but you want to flag missingness.

**NEVER silently zero.** Zero saturation flux is "this material has
no magnetic core capability", which is wrong for, say, iron. The
``"error"`` default exists precisely to make this footgun loud.

JAX is lazy-imported inside ``to_jax_pytree``: consumers without
JAX installed pay no import cost.
"""

from __future__ import annotations

from dataclasses import fields
from typing import TYPE_CHECKING, Any, Literal, get_args

if TYPE_CHECKING:
    from emergent_matter_materials.material import Material


MissingPolicy = Literal["omit", "nan", "error"]

#: Runtime counterpart of `MissingPolicy`, derived with `get_args()` so it
#: can never drift from the Literal (STYLE.md: never hand-copy a Literal's
#: members into a separate tuple).
_VALID_MISSING_POLICIES: tuple[str, ...] = get_args(MissingPolicy)

_GROUP_NAMES: tuple[str, ...] = ("structural", "electromagnetic", "thermal", "manufacturing")


def to_jax_pytree(
    m: Material,
    *,
    s_missing: MissingPolicy = "error",
) -> dict[str, Any]:
    """Materialize a Material's numeric fields as a JAX-friendly pytree.

    Returns a nested ``dict[str, dict[str, jnp.ndarray]]`` keyed by group
    name → field name → scalar ``jnp.ndarray``. Manufacturing's
    ``ProcessFit`` per-process structure is flattened with keys like
    ``"manufacturing.FFF_PLA.shrinkage_linear"`` to keep the output
    a flat-ish two-level pytree (JAX-pytree-friendly).

    Args:
        m: The Material to convert.
        s_missing: How to handle absent fields. See module docstring.

    Returns:
        Nested dict pytree. Only numeric ``d_value`` fields land in
        the output: provenance metadata (``s_source``, ``s_units``,
        etc.) stays on the catalog side.

    Raises:
        ValueError: ``s_missing="error"`` and a populated group has a
            None field.
        ModuleNotFoundError: ``jax`` is not installed (lazy-imported here).
    """
    try:
        import jax.numpy as jnp
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "JAX not installed. Install with: uv sync --extra jax  (or: pip install jax)"
        ) from e

    if s_missing not in _VALID_MISSING_POLICIES:
        raise ValueError(
            f"to_jax_pytree(s_missing=...) must be 'omit', 'nan', or 'error', got {s_missing!r}"
        )

    out: dict[str, Any] = {}

    for s_group_name in _GROUP_NAMES:
        group = getattr(m, s_group_name)
        if group is None:
            # Group entirely absent. "omit" drops it, "nan" leaves it out
            # too (because we can't enumerate which fields would have been
            # present), "error" raises if the consumer wanted required data.
            if s_missing == "error":
                # Don't raise here: groups being None is fine; only
                # raising on FIELDS being None within a populated group.
                # This pattern lets a consumer call to_jax_pytree on
                # materials with partial coverage without false alarms.
                pass
            continue

        if s_group_name == "manufacturing":
            out["manufacturing"] = _manufacturing_subtree(group, s_missing, jnp)
            continue

        # Standard PropertyValue-field group
        group_dict: dict[str, Any] = {}
        for f in fields(group):
            pv = getattr(group, f.name)
            if pv is None:
                if s_missing == "error":
                    raise ValueError(
                        f"to_jax_pytree(s_missing='error'): "
                        f"{type(group).__name__}.{f.name} is None on "
                        f"material {m.s_id!r}. "
                        f"Use s_missing='omit' or 'nan' to allow."
                    )
                if s_missing == "omit":
                    continue
                # s_missing == "nan"
                group_dict[f.name] = jnp.nan
            elif isinstance(pv, (tuple, list)):
                # Collection-valued composite field, e.g.
                # Electromagnetic.rotational_loss_models (tuple of
                # RotationalLossData, v1.x scaffold). Per the rotational-loss
                # Phase 0B integration decision these are NOT flattened into
                # the pytree: different record forms (curve / ratio /
                # model_coefficients) expose different d_* fields, so generic
                # flattening is unsafe. Skipped regardless of s_missing (the
                # common case is the default empty tuple, which contributes
                # nothing anyway). This guard must precede the composite branch
                # below: fields(<tuple>) would raise.
                continue
            elif not hasattr(pv, "d_value"):
                # Composite multi-valued field (e.g. BHCurveData with paired
                # B/H tables, added v1.2.0). Duck-typed: PropertyValue has
                # d_value (a scalar); composites don't. Flatten the
                # composite into a sub-dict of jnp arrays, recursing one
                # level deep for any `d_*` tuple/list/array fields.
                composite_dict: dict[str, Any] = {}
                for cf in fields(pv):
                    if not cf.name.startswith("d_"):
                        continue  # skip s_source / s_condition / etc.
                    cv = getattr(pv, cf.name)
                    composite_dict[cf.name] = jnp.asarray(cv)
                group_dict[f.name] = composite_dict
            else:
                group_dict[f.name] = jnp.asarray(pv.d_value)

        if group_dict:
            out[s_group_name] = group_dict

    return out


def _manufacturing_subtree(
    mfg: Any,  # Manufacturing, but avoid runtime import
    s_missing: str,
    jnp: Any,
) -> dict[str, Any]:
    """Flatten Manufacturing.process_fit into a JAX pytree.

    Each ProcessFit becomes a nested dict under its process key. Top-
    level keys: process names. Bottom level: field name → jnp scalar.
    """
    out: dict[str, Any] = {}
    if not mfg.process_fit:
        return out

    for s_proc, fit in mfg.process_fit.items():
        proc_dict: dict[str, Any] = {}
        for f in fields(fit):
            pv = getattr(fit, f.name)
            if pv is None:
                if s_missing == "error":
                    raise ValueError(
                        f"to_jax_pytree(s_missing='error'): "
                        f"ProcessFit({s_proc!r}).{f.name} is None. "
                        f"Use s_missing='omit' or 'nan' to allow."
                    )
                if s_missing == "omit":
                    continue
                proc_dict[f.name] = jnp.nan
            else:
                proc_dict[f.name] = jnp.asarray(pv.d_value)
        if proc_dict:
            out[s_proc] = proc_dict

    return out


__all__ = [
    "MissingPolicy",
    "to_jax_pytree",
]
