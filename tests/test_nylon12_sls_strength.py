"""Guards for the nylon12_sls strength decision (v1.9.1).

A downstream structural tool skips any material whose
structural group is missing youngs_modulus, yield_stress, OR density. SLS
PA12 has no Tier-1 yield: the Formlabs and EOS TDSs publish only an ultimate
tensile strength, and a real yield would sit *below* the UTS, so yield_stress
is intentionally None and the strength scalar lives in ultimate_tensile. These
tests lock that in so the mislabeled-yield field v0.7.2 removed is not
re-introduced by a well-meaning future edit.
"""

from __future__ import annotations

import dataclasses

from emergent_matter_materials import get_material


def test_ultimate_tensile_is_formlabs_50mpa():
    s = get_material("nylon12_sls").structural
    assert s.d_ultimate_tensile_Pa == 50e6
    pv = s.ultimate_tensile
    assert pv.s_units == "Pa"
    assert pv.s_confidence == "datasheet"
    assert "Formlabs" in pv.s_source


def test_yield_stress_intentionally_absent():
    # No Tier-1 yield exists for SLS PA12; UTS must not be copied into yield
    # (a true yield is below the UTS, so that would also overstate it).
    assert get_material("nylon12_sls").structural.yield_stress is None


def test_strength_scalar_present_for_consumers():
    # The FEM stress constraint can read a strength limit from ultimate_tensile
    # even though yield_stress is None (the documented fallback path).
    s = get_material("nylon12_sls").structural
    assert s.youngs_modulus is not None
    assert s.density is not None
    assert s.ultimate_tensile is not None


def test_a_stamp_belongs_to_one_entry():
    # Relabeling one material leaves the original and its siblings alone.
    nylon = get_material("nylon12_sls")
    relabeled = dataclasses.replace(nylon, s_catalog_version="9.9.9")
    assert relabeled.s_catalog_version == "9.9.9"
    assert nylon.s_catalog_version != "9.9.9"
    for sib in ("peek_unfilled", "pla_3dprint", "pei_ultem_1010"):
        assert get_material(sib).s_catalog_version != "9.9.9"
