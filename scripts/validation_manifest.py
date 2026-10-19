"""Generate the catalog source-validation manifest.

Walks every Material in MATERIALS and emits two files:

1. build/validation_manifest/validation_manifest_v<catalog>.csv: one row per PropertyValue, with
   the full catalog state (id / group / field / value / units / condition
   / confidence / source / notes) + extracted source URL(s).

2. build/validation_manifest/validation_manifest_v<catalog>_by_source.md: same data grouped by
   source URL, so a reviewer can claim one URL and check every
   PV that cites it.

This is the input to a round-trip source validation run. After reviewers return
structured findings, the manifest gets re-emitted with a `status`
column (VERIFIED / MISMATCH / SOURCE_DOESNT_PUBLISH / UNVERIFIABLE) +
the source-published value for any non-VERIFIED row.

Usage:
    uv run python scripts/validation_manifest.py
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import fields
from pathlib import Path
from typing import Any

from emergent_matter_materials import MATERIALS, __catalog_version__
from emergent_matter_materials.property_value import PropertyValue

_URL_RE = re.compile(r"https?://[^\s)>,;]+")
_GROUPS = ("structural", "electromagnetic", "thermal", "crystal_anisotropy")


def _extract_urls(s: str) -> list[str]:
    """Pull all URLs out of a source-citation string."""
    return _URL_RE.findall(s or "")


def _group_pvs(grp: Any) -> Iterable[tuple[str, PropertyValue]]:
    """Yield (field label, PropertyValue) for a group's scalars, table rows, and flow points.

    Table rows and flow points each cite their own source, so each gets its
    own manifest row; the label carries the row's temperature (and plastic
    strain) so a reviewer can find it.
    """
    for f in fields(grp):
        pv = getattr(grp, f.name)
        if isinstance(pv, PropertyValue):
            yield f.name, pv
    for s_slot, table in getattr(grp, "temperature_tables", {}).items():
        for point in table.points:
            yield f"{s_slot}@{point.d_temperature_C}C", point.value
    flow_curve = getattr(grp, "flow_curve", None)
    if flow_curve is not None:
        for point in flow_curve.points:
            yield (
                f"flow_curve@{point.d_temperature_C}C,eps_p={point.d_plastic_strain}",
                point.stress,
            )


def _walk_pvs() -> Iterable[dict]:
    """Yield one dict per populated PropertyValue across the catalog."""
    for s_id in sorted(MATERIALS):
        m = MATERIALS[s_id]
        for s_group in _GROUPS:
            grp = getattr(m, s_group, None)
            if grp is None:
                continue
            for s_field, pv in _group_pvs(grp):
                urls = _extract_urls(pv.s_source)
                yield {
                    "material_id": s_id,
                    "material_spec": m.s_specification,
                    "group": s_group,
                    "field": s_field,
                    "d_value": pv.d_value,
                    "s_units": pv.s_units,
                    "s_condition": pv.s_condition,
                    "s_confidence": pv.s_confidence,
                    "s_source": pv.s_source,
                    "s_notes": pv.s_notes,
                    "source_urls": " | ".join(urls) if urls else "",
                    "has_url": bool(urls),
                }


def _primary_url(urls_str: str) -> str:
    """Pick the canonical URL for grouping: the first one in the source."""
    if not urls_str:
        return "(no URL: printed/paywalled source)"
    return urls_str.split(" | ")[0]


def write_csv(rows: list[dict], dest: Path) -> None:
    cols = [
        "material_id",
        "group",
        "field",
        "d_value",
        "s_units",
        "s_condition",
        "s_confidence",
        "material_spec",
        "source_urls",
        "has_url",
        "s_source",
        "s_notes",
    ]
    with dest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_by_source_md(rows: list[dict], dest: Path) -> None:
    """One section per unique primary URL: reviewers claim a URL + verify all PVs under it."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        buckets[_primary_url(r["source_urls"])].append(r)

    n_total = sum(len(v) for v in buckets.values())
    n_url = sum(len(v) for k, v in buckets.items() if k.startswith("http"))
    n_no_url = sum(len(v) for k, v in buckets.items() if not k.startswith("http"))

    lines: list[str] = []
    lines.append("# Validation manifest: v0.7.2 sweep")
    lines.append("")
    lines.append(f"- catalog version: `{__catalog_version__}`")
    lines.append(f"- total PropertyValues: **{n_total}**")
    lines.append(f"- PVs with fetchable URL: **{n_url}**")
    lines.append(f"- PVs without URL (printed/paywalled source): **{n_no_url}**")
    lines.append(
        f"- unique sources to fetch: **{sum(1 for k in buckets if k.startswith('http'))}**"
    )
    lines.append("")
    lines.append("## How to use")
    lines.append("")
    lines.append(
        "Each section below is one **source URL**. A reviewer claims one "
        "section, opens the URL, locates the source row for every PV "
        "listed under that section, and reports back per-PV: "
        "**VERIFIED** (catalog matches source), **MISMATCH** (record actual source "
        "value), **SOURCE_DOESNT_PUBLISH** (record what the source publishes "
        "instead), or **UNVERIFIABLE** (paywall / 404 / etc.)."
    )
    lines.append("")
    lines.append(
        "Read-only audit: do NOT edit catalog files. Corrections "
        "happen in the triage phase after all reviewers return."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sort: URLs first (alphabetical), then no-URL last
    sorted_keys = sorted(
        buckets.keys(),
        key=lambda k: (not k.startswith("http"), k.lower()),
    )
    for k in sorted_keys:
        rows_here = sorted(buckets[k], key=lambda r: (r["material_id"], r["group"], r["field"]))
        lines.append(f"## {k}")
        lines.append("")
        lines.append(f"- PVs claiming this source: **{len(rows_here)}**")
        lines.append("")
        lines.append("| material_id | group | field | value | units | condition | confidence |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in rows_here:
            cond = (r["s_condition"] or "").replace("|", "/")[:60]
            lines.append(
                f"| `{r['material_id']}` | {r['group']} | `{r['field']}` | "
                f"{r['d_value']:.4g} | `{r['s_units']}` | {cond} | "
                f"{r['s_confidence']} |"
            )
        lines.append("")
        # Show the s_source verbatim for traceability: the reviewer needs the
        # exact citation language to know what row to look for.
        lines.append("**Full source citations (verbatim from catalog):**")
        lines.append("")
        seen_sources: set[str] = set()
        for r in rows_here:
            if r["s_source"] in seen_sources:
                continue
            seen_sources.add(r["s_source"])
            # Compact rendering: collapse multi-line citation
            cite = " ".join(r["s_source"].split())
            lines.append(f"- {cite}")
        lines.append("")
        lines.append("---")
        lines.append("")

    dest.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    docs = repo_root / "build" / "validation_manifest"
    docs.mkdir(parents=True, exist_ok=True)

    rows = list(_walk_pvs())

    csv_path = docs / f"validation_manifest_v{__catalog_version__}.csv"
    md_path = docs / f"validation_manifest_v{__catalog_version__}_by_source.md"

    write_csv(rows, csv_path)
    write_by_source_md(rows, md_path)

    print(f"Wrote {csv_path.relative_to(repo_root)}: {len(rows)} PropertyValues")
    print(f"Wrote {md_path.relative_to(repo_root)}: grouped by source URL")

    # Summary stats
    n_url = sum(1 for r in rows if r["has_url"])
    print(f"  with URL:    {n_url}/{len(rows)}")
    print(f"  without URL: {len(rows) - n_url}/{len(rows)} (printed books, paywalled, standards)")


if __name__ == "__main__":
    main()
