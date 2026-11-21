"""Liquids: working fluids and coolants, tabulated across their liquid range.

A liquid's properties change a lot over its working range (water's viscosity
falls by a factor of six between 0 C and 100 C), so every entry here carries
temperature tables, with a headline scalar at 20 C for flat lookups through
``get()``. Density lives in ``Structural``, and viscosity, conductivity and
specific heat live in ``Thermal``, the same slots a solid uses.

Water's numbers are copied from NIST Chemistry WebBook responses saved
verbatim under ``data/nist_webbook_water/``, and
``tests/test_water_nist_webbook.py`` checks every row against those files.
To change a value, refetch from NIST, replace the saved file, and update the
rows below. NIST reports specific heat in J/(g*K); the rows below write it as
the NIST digits times ``e3``, which is the exact conversion to J/(kg*K).
"""

from __future__ import annotations

from emergent_matter_materials.material import Material
from emergent_matter_materials.property_table import PropertyTable, TablePoint
from emergent_matter_materials.property_value import PropertyValue as _PV
from emergent_matter_materials.structural import Structural
from emergent_matter_materials.thermal import Thermal

_S_CATALOG_VERSION = "1.1.0"
_S_LAST_REVIEWED = "2026-11-20"

_NIST_WEBBOOK_WATER = (
    "NIST Chemistry WebBook, NIST Standard Reference Database 69, 'Thermophysical "
    "Properties of Fluid Systems', water (CAS 7732-18-5), isobaric data at "
    "0.101325 MPa, retrieved 2026-11-21T00:36Z (UTC) from "
)
#: The query that returned the 0.01 C row. NIST's isobar starts at the triple
#: point, so a 0 C start yields 0.01 C and then a grid offset by 0.01 C; only
#: that first row is used.
_URL_FROM_0C = (
    "https://webbook.nist.gov/cgi/fluid.cgi?Action=Data&Wide=on&ID=C7732185"
    "&Type=IsoBar&Digits=6&P=0.101325&THigh=100&TLow=0&TInc=5&RefState=DEF"
    "&TUnit=C&PUnit=MPa&DUnit=kg%2Fm3&HUnit=kJ%2Fkg&WUnit=m%2Fs&VisUnit=Pa*s&STUnit=N%2Fm"
)
#: The query that returned every row from 5 C to the boiling point.
_URL_FROM_5C = (
    "https://webbook.nist.gov/cgi/fluid.cgi?Action=Data&Wide=on&ID=C7732185"
    "&Type=IsoBar&Digits=6&P=0.101325&THigh=100&TLow=5&TInc=5&RefState=DEF"
    "&TUnit=C&PUnit=MPa&DUnit=kg%2Fm3&HUnit=kJ%2Fkg&WUnit=m%2Fs&VisUnit=Pa*s&STUnit=N%2Fm"
)

_IAPWS_95 = (
    "IAPWS-95 equation of state (Wagner and Pruss, J. Phys. Chem. Ref. Data 31, "
    "387 (2002), https://doi.org/10.1063/1.1461829)"
)
_IAPWS_2008_VISCOSITY = (
    "IAPWS 2008 viscosity formulation (Huber et al., J. Phys. Chem. Ref. Data 38, "
    "101 (2009), https://doi.org/10.1063/1.3088050)"
)
_IAPWS_2011_CONDUCTIVITY = (
    "IAPWS 2011 thermal conductivity formulation (Huber et al., J. Phys. Chem. Ref. "
    "Data 41, 033102 (2012), https://doi.org/10.1063/1.4738955)"
)

#: Slot to (NIST column, formulation, units, notes). The uncertainty statements
#: are the ones on the NIST results page; for the transport properties that
#: page gives no figure and refers to the IAPWS releases instead.
_COLUMNS: dict[str, tuple[str, str, str, str]] = {
    "density": (
        "Density (kg/m3)",
        _IAPWS_95,
        "kg/m^3",
        "NIST states the equation of state's density uncertainty as 0.0001% at "
        "1 atm in the liquid phase.",
    ),
    "dynamic_viscosity": (
        "Viscosity (Pa*s)",
        _IAPWS_2008_VISCOSITY,
        "Pa*s",
        "NIST gives no uncertainty figure on the results page and refers to the "
        "IAPWS release and the cited publication.",
    ),
    "thermal_conductivity": (
        "Therm. Cond. (W/m*K)",
        _IAPWS_2011_CONDUCTIVITY,
        "W/(m*K)",
        "NIST gives no uncertainty figure on the results page and refers to the "
        "IAPWS release and the cited publication.",
    ),
    "specific_heat": (
        "Cp (J/g*K)",
        _IAPWS_95,
        "J/(kg*K)",
        "Isobaric specific heat. NIST reports J/(g*K); multiplied by 1000 to "
        "J/(kg*K). NIST states the isobaric heat capacity uncertainty as 0.1% in "
        "the liquid.",
    ),
}

#: NIST rows at 0.101325 MPa, every one marked 'liquid' in NIST's Phase column.
#: The last row is saturated liquid at the normal boiling point; above it water
#: at this pressure is vapor, so the tables stop there.
# fmt: off
# Hand-aligned columns, NIST's digits as printed, so a row can be read against
# the saved file by eye; ruff format would collapse the alignment.
_WATER_ROWS: tuple[tuple[float, float, float, float, float, str], ...] = (
    # (T C,   rho kg/m^3, mu Pa*s,   k W/(m*K), cp J/(kg*K), query)
    (   0.01, 999.844,  0.00179113, 0.555675, 4.21941e3, _URL_FROM_0C),
    (    5.0, 999.967,  0.00151817, 0.567794, 4.20504e3, _URL_FROM_5C),
    (   10.0, 999.702,  0.00130590, 0.578777, 4.19516e3, _URL_FROM_5C),
    (   15.0, 999.103,  0.00113757, 0.588802, 4.18846e3, _URL_FROM_5C),
    (   20.0, 998.207,  0.00100160, 0.598012, 4.18405e3, _URL_FROM_5C),
    (   25.0, 997.048, 0.000890022, 0.606516, 4.18131e3, _URL_FROM_5C),
    (   30.0, 995.649, 0.000797222, 0.614392, 4.17982e3, _URL_FROM_5C),
    (   35.0, 994.033, 0.000719126, 0.621700, 4.17926e3, _URL_FROM_5C),
    (   40.0, 992.216, 0.000652729, 0.628486, 4.17941e3, _URL_FROM_5C),
    (   45.0, 990.213, 0.000595769, 0.634783, 4.18014e3, _URL_FROM_5C),
    (   50.0, 988.035, 0.000546516, 0.640621, 4.18134e3, _URL_FROM_5C),
    (   55.0, 985.693, 0.000503625, 0.646021, 4.18296e3, _URL_FROM_5C),
    (   60.0, 983.196, 0.000466035, 0.651000, 4.18495e3, _URL_FROM_5C),
    (   65.0, 980.551, 0.000432903, 0.655575, 4.18732e3, _URL_FROM_5C),
    (   70.0, 977.765, 0.000403548, 0.659758, 4.19007e3, _URL_FROM_5C),
    (   75.0, 974.843, 0.000377416, 0.663561, 4.19320e3, _URL_FROM_5C),
    (   80.0, 971.790, 0.000354051, 0.666994, 4.19675e3, _URL_FROM_5C),
    (   85.0, 968.611, 0.000333075, 0.670067, 4.20074e3, _URL_FROM_5C),
    (   90.0, 965.310, 0.000314175, 0.672789, 4.20521e3, _URL_FROM_5C),
    (   95.0, 961.888, 0.000297085, 0.675167, 4.21017e3, _URL_FROM_5C),
    (99.9743, 958.367, 0.000281658, 0.677201, 4.21564e3, _URL_FROM_5C),
)
# fmt: on

#: Catalog slots in the order of the value columns of ``_WATER_ROWS``.
_WATER_SLOTS: tuple[str, ...] = (
    "density",
    "dynamic_viscosity",
    "thermal_conductivity",
    "specific_heat",
)

#: Row used for the headline scalars that flat ``get()`` lookups return.
_D_HEADLINE_TEMPERATURE_C = 20.0


def _condition(d_temperature_C: float, b_saturated: bool) -> str:
    if b_saturated:
        return (
            f"{d_temperature_C} C, 0.101325 MPa, saturated liquid at the normal "
            f"boiling point (NIST Phase column: liquid)"
        )
    return f"{d_temperature_C} C, 0.101325 MPa, liquid (NIST Phase column: liquid)"


def _water_pv(s_slot: str, row: tuple[float, float, float, float, float, str]) -> _PV:
    s_column, s_formulation, s_units, s_notes = _COLUMNS[s_slot]
    d_temperature_C = row[0]
    return _PV(
        d_value=dict(zip(_WATER_SLOTS, row[1:5], strict=True))[s_slot],
        s_units=s_units,
        s_source=(
            _NIST_WEBBOOK_WATER
            + row[5]
            + f" -- column '{s_column}', row {d_temperature_C} C; computed by NIST from "
            + s_formulation
        ),
        s_condition=_condition(d_temperature_C, d_temperature_C == _WATER_ROWS[-1][0]),
        s_confidence="standard",
        s_notes=s_notes,
    )


def _water_table(s_slot: str) -> PropertyTable:
    return PropertyTable(
        points=tuple(
            TablePoint(d_temperature_C=row[0], value=_water_pv(s_slot, row)) for row in _WATER_ROWS
        ),
        s_table_notes=(
            "Liquid water at 0.101325 MPa from 0.01 C (the triple point, NIST's lower "
            "limit) to 99.9743 C (saturated liquid). Linear interpolation between "
            "rows about 5 C apart; value_at raises outside this range."
        ),
    )


def _water_headline(s_slot: str) -> _PV:
    (row,) = (r for r in _WATER_ROWS if r[0] == _D_HEADLINE_TEMPERATURE_C)
    return _water_pv(s_slot, row)


# ── Water ──────────────────────────────────────────────────────────────────

water = Material(
    s_id="water",
    s_description="Liquid water (ordinary water substance) at atmospheric pressure",
    s_category="liquid",
    s_specification=(
        "Ordinary water substance (H2O, CAS 7732-18-5), liquid at 0.101325 MPa, "
        "properties per the IAPWS-95, IAPWS 2008 viscosity and IAPWS 2011 thermal "
        "conductivity formulations as computed by NIST SRD 69"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        density=_water_headline("density"),
        temperature_tables={"density": _water_table("density")},
    ),
    thermal=Thermal(
        thermal_conductivity=_water_headline("thermal_conductivity"),
        specific_heat=_water_headline("specific_heat"),
        dynamic_viscosity=_water_headline("dynamic_viscosity"),
        temperature_tables={
            s_slot: _water_table(s_slot)
            for s_slot in ("thermal_conductivity", "specific_heat", "dynamic_viscosity")
        },
    ),
)


CATALOG: dict[str, Material] = {
    "water": water,
}


__all__ = ["CATALOG"]
