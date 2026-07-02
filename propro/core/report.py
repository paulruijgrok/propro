"""Formatting/export helpers for :class:`propro.core.properties.ProteinOverview`.

Three output shapes are supported:

- :func:`print_report` — a human-readable text report, ordered the same way
  the properties are typically read off a wet-lab bench sheet.
- :func:`overview_to_dataframe` / :func:`aa_frequency_dataframe` /
  :func:`charge_curve_dataframe` — pandas DataFrames for programmatic use,
  spreadsheet export, or handing to ``propro.interfaces.gscripts``.
- :func:`overview_to_markdown` — a Markdown rendering for notebooks/reports.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd

from propro.core.properties import ProteinOverview
from propro.core.sequence import STANDARD_AA

# Fixed, conventional ordering for amino acid tables.
_AA_ORDER = list("ACDEFGHIKLMNPQRSTVWY")


def _ordered_aa_keys(overview: ProteinOverview) -> List[str]:
    """All standard amino acids (even if count 0) in a fixed order, followed
    by any ambiguous/non-standard residues actually observed."""
    extra = sorted(k for k in overview.aa_counts if k not in STANDARD_AA)
    return _AA_ORDER + extra


def aa_frequency_dataframe(overview: ProteinOverview) -> pd.DataFrame:
    """Amino acid composition as a DataFrame with columns: residue, count, percent."""
    keys = _ordered_aa_keys(overview)
    rows = [
        {
            "residue": aa,
            "count": overview.aa_counts.get(aa, 0),
            "percent": round(overview.aa_percent.get(aa, 0.0), 2),
        }
        for aa in keys
    ]
    return pd.DataFrame(rows)


def charge_curve_dataframe(overview: ProteinOverview) -> pd.DataFrame:
    """Net-charge-vs-pH curve as a DataFrame with columns: pH, net_charge."""
    return pd.DataFrame(overview.net_charge_by_ph, columns=["pH", "net_charge"])


def overview_to_dataframe(overview: ProteinOverview) -> pd.DataFrame:
    """Single-row summary of the scalar properties (everything except the
    amino acid table and the charge curve), as a tidy property/value table."""
    rows = [
        ("id", overview.id),
        ("length", overview.length),
        ("position_range", f"{overview.position_start}-{overview.position_end}"),
        ("is_contiguous", overview.is_contiguous),
        ("n_ambiguous_residues", overview.n_ambiguous_residues),
        ("molecular_weight_da", _round(overview.molecular_weight, 2)),
        ("isoelectric_point", _round(overview.isoelectric_point, 2)),
        ("instability_index", _round(overview.instability_index, 2)),
        ("instability_class", overview.instability_class),
        ("extinction_coefficient_reduced_M-1cm-1", _round(overview.extinction_coefficient_reduced, 0)),
        ("extinction_coefficient_oxidized_M-1cm-1", _round(overview.extinction_coefficient_oxidized, 0)),
        ("absorbance_280nm_1mgml_reduced", _round(overview.absorbance_1mgml_reduced, 3)),
        ("absorbance_280nm_1mgml_oxidized", _round(overview.absorbance_1mgml_oxidized, 3)),
        ("net_charge_pH7", _round(overview.net_charge_ph7, 2)),
    ]
    return pd.DataFrame(rows, columns=["property", "value"])


def overview_to_markdown(overview: ProteinOverview) -> str:
    lines = [f"# Protein overview: {overview.id}"]
    if overview.description:
        lines.append(f"_{overview.description}_")
    lines.append("")
    lines.append(overview_to_dataframe(overview).to_markdown(index=False))
    lines.append("")
    lines.append("## Amino acid frequencies")
    lines.append(aa_frequency_dataframe(overview).to_markdown(index=False))
    if overview.notes:
        lines.append("")
        lines.append("## Notes")
        for note in overview.notes:
            lines.append(f"- {note}")
    return "\n".join(lines)


def _round(value: Optional[float], ndigits: int) -> Optional[float]:
    return None if value is None else round(value, ndigits)


def print_report(overview: ProteinOverview, n_ph_points: int = 5) -> None:
    """Print a bench-sheet-style text report to stdout."""
    w = 62
    print("=" * w)
    print(f"Protein overview: {overview.id}")
    if overview.description:
        print(overview.description)
    print("=" * w)

    print(f"\nPosition\n  Residues {overview.position_start}-{overview.position_end}"
          f"{'' if overview.is_contiguous else ' (non-contiguous numbering)'}")

    print(f"\nSummary\n  {overview.sequence_summary}")
    if overview.n_ambiguous_residues:
        print(f"  {overview.n_ambiguous_residues} ambiguous/non-standard residue(s) present")

    if overview.molecular_weight is None:
        print("\nNumeric properties unavailable (no standard-residue content).")
    else:
        print(f"\nMolecular weight\n  {overview.molecular_weight:,.2f} Da")

        print(f"\nIsoelectric point (pI)\n  {overview.isoelectric_point:.2f}")

        print("\nExtinction coefficient (280 nm)")
        print(f"  Cys fully reduced:  {overview.extinction_coefficient_reduced:,.0f} M-1 cm-1"
              f"   |  A(280nm, 1 mg/mL) = {overview.absorbance_1mgml_reduced:.3f}")
        print(f"  Cys fully oxidized: {overview.extinction_coefficient_oxidized:,.0f} M-1 cm-1"
              f"   |  A(280nm, 1 mg/mL) = {overview.absorbance_1mgml_oxidized:.3f}")

        print(f"\nInstability index\n  {overview.instability_index:.2f} ({overview.instability_class})")

        print("\nAmino acid frequencies")
        aa_df = aa_frequency_dataframe(overview)
        for _, row in aa_df.iterrows():
            print(f"  {row['residue']}: {int(row['count']):>4d}  ({row['percent']:5.2f}%)")

        print(f"\nNet charge as a function of pH  (pH 7.0 -> {overview.net_charge_ph7:+.2f})")
        curve = overview.net_charge_by_ph
        step = max(1, len(curve) // (n_ph_points - 1)) if n_ph_points > 1 else len(curve)
        sample = curve[::step]
        if sample[-1] != curve[-1]:
            sample.append(curve[-1])
        for ph, charge in sample:
            print(f"  pH {ph:5.1f}: {charge:+7.2f}")

    if overview.notes:
        print("\nNotes")
        for note in overview.notes:
            print(f"  - {note}")
    print("=" * w)
