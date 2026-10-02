"""Tests for temp_coeff_coercivity α(HcJ): Magnet Coercivity Temp-Coeff Sprint.

Schema field + per-grade values verified directly from the Arnold per-grade
PDFs in the v1.8.0 source-verification pass (NOT from prior docstring
narrative). Cross-checked against Shin-Etsu sheets.
"""

from __future__ import annotations

import pytest

from emergent_matter_materials import Electromagnetic, get, get_material
from emergent_matter_materials.accessors import _PROPERTY_MAP
from emergent_matter_materials.property_value import PropertyValue as PV

# ── schema ──────────────────────────────────────────────────────────────────


def test_field_and_accessor():
    em = Electromagnetic(
        temp_coeff_coercivity=PV(
            d_value=-6.2e-3, s_units="1/K", s_source="x", s_confidence="datasheet"
        ),
    )
    assert em.d_temp_coeff_coercivity_per_K == pytest.approx(-6.2e-3)


def test_accessor_raises_when_absent():
    with pytest.raises(ValueError, match="temp_coeff_coercivity"):
        _ = Electromagnetic().d_temp_coeff_coercivity_per_K


def test_units_enforced():
    with pytest.raises(ValueError):
        Electromagnetic(
            temp_coeff_coercivity=PV(
                d_value=-6.2e-3,
                s_units="%/degC",  # wrong
                s_source="x",
                s_confidence="datasheet",
            ),
        )


def test_short_name_in_property_map():
    assert _PROPERTY_MAP["alpha_HcJ"] == ("electromagnetic", "temp_coeff_coercivity")


# ── per-grade values (verified from Arnold PDFs) ────────────────

# %/degC ÷ 100 = /K fraction. All measured over the grade's own T-range.
_EXPECTED = {
    "ndfeb_n35": -6.2e-3,  # -0.62 %/degC, 20-80 C   (N35 Rev. 210607)
    "ndfeb_n42": -6.2e-3,  # -0.62 %/degC, 20-80 C   (N42 Rev. 210607)
    "ndfeb_n50": -6.2e-3,  # -0.62 %/degC, 20-80 C   (N50 Rev. 210802)
    "ndfeb_n42sh": -5.5e-3,  # -0.55 %/degC, 20-150 C  (N42SH Rev. 020821)
    "ndfeb_n42uh": -5.1e-3,  # -0.51 %/degC, 20-180 C  (N42UH Rev. 210607)
    "ndfeb_n42eh": -4.2e-3,  # -0.42 %/degC, 20-200 C  (N42EH Rev. 151021a)
    "smco_2_17": -2.4e-3,  # -0.24 %/degC, 20-150 C  (Recoma 28 Rev. 131025)
}


@pytest.mark.parametrize("s_id,expected", sorted(_EXPECTED.items()))
def test_magnet_alpha_hcj_value(s_id, expected):
    assert get(s_id, "alpha_HcJ") == pytest.approx(expected, rel=1e-9)
    pv = get_material(s_id).electromagnetic.temp_coeff_coercivity
    assert pv.s_confidence == "datasheet"
    assert pv.s_units == "1/K"
    # provenance must cite the verified Arnold source + the direct-read pass
    assert "v1.8.0" in pv.s_source
    assert ("Arnold" in pv.s_source) or ("Recoma" in pv.s_source)


def test_alpha_hcj_more_negative_than_alpha_br():
    """Physical sanity: |α(HcJ)| >> |α(Br)| for every magnet (HcJ degrades
    with temperature far faster than Br: the whole reason this field matters)."""
    for s_id in _EXPECTED:
        a_hcj = get(s_id, "alpha_HcJ")
        a_br = get(s_id, "alpha_Br")
        assert a_hcj < a_br < 0.0, s_id
        assert abs(a_hcj) > abs(a_br), s_id


def test_coercivity_class_ordering():
    """Higher-coercivity NdFeB grades have less-negative α(HcJ)
    (plain < SH < UH < EH in thermal stability); SmCo best of all."""
    plain = get("ndfeb_n42", "alpha_HcJ")
    sh = get("ndfeb_n42sh", "alpha_HcJ")
    uh = get("ndfeb_n42uh", "alpha_HcJ")
    eh = get("ndfeb_n42eh", "alpha_HcJ")
    smco = get("smco_2_17", "alpha_HcJ")
    assert plain < sh < uh < eh < smco < 0.0


def test_absent_on_non_magnets():
    """α(HcJ) is N/A for soft-magnetic / conductor materials: must stay None."""
    for s_id in ("m19_silicon_steel", "hiperco_50", "pure_copper", "aluminum_1350_ec"):
        em = get_material(s_id).electromagnetic
        if em is not None:
            assert em.temp_coeff_coercivity is None


def test_coverage_exactly_the_seven_magnets():
    """Exactly the 7 permanent magnets carry α(HcJ); nothing else does."""
    from emergent_matter_materials import list_materials

    populated = set()
    for s_id in list_materials():
        em = get_material(s_id).electromagnetic
        if em is not None and em.temp_coeff_coercivity is not None:
            populated.add(s_id)
    assert populated == set(_EXPECTED)
