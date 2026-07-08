#!/usr/bin/env python3
"""Sequence overview PDF — a one-page report for a protein sequence.

Renders, on a single page: key properties (position, summary, molecular
weight, pI, extinction coefficient, instability index), a net-charge-vs-pH
chart, and a full amino acid frequency table.

Lives in ``propro.interfaces.pdf_reports`` because a PDF is an output
platform, parallel to the ``gscripts`` (Google Sheets) and ``pymol``
interfaces. It applies to any sequence and builds only on ``propro.core``.

Usage
-----
As a library, on an existing ``ProteinOverview``::

    from propro.core.properties import compute_overview
    from propro.core.sequence import ProteinSequence
    from propro.interfaces.pdf_reports.sequence_overview_pdf import (
        generate_sequence_overview_pdf,
    )
    overview = compute_overview(ProteinSequence("MKT...", id="my_protein"))
    generate_sequence_overview_pdf(overview, "my_protein.pdf")

From the command line::

    python -m propro.interfaces.pdf_reports.sequence_overview_pdf --sequence MKT... --id my_protein
    python -m propro.interfaces.pdf_reports.sequence_overview_pdf --fasta sequences.fasta --outdir reports/

Requires propro to be importable (``pip install -e .`` from the repo root,
or run from a checkout with the repo root on ``PYTHONPATH``).
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt

# Allow running straight from a checkout without `pip install -e .`: fall
# back to adding the repo root (three levels up: pdf_reports -> interfaces ->
# propro -> repo root) to sys.path.
try:
    from propro.core.properties import ProteinOverview, compute_overview
except ImportError:  # pragma: no cover - exercised only outside an installed env
    _REPO_ROOT = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(_REPO_ROOT))
    from propro.core.properties import ProteinOverview, compute_overview

from propro.core.report import aa_frequency_dataframe
from propro.core.sequence import ProteinSequence
from propro.core.visualize import plot_net_charge_vs_ph

PAGE_SIZE = (8.5, 11)  # US Letter, inches, portrait


def _wrapped(label: str, value: str, width: int = 34) -> list:
    """Wrap `value` to `width` chars, indenting continuation lines under it."""
    indent = " " * len(label)
    wrapped = textwrap.wrap(value, width=width) or [""]
    return [f"{label}{wrapped[0]}"] + [f"{indent}{cont}" for cont in wrapped[1:]]


def _draw_key_properties(ax: plt.Axes, overview: ProteinOverview) -> None:
    ax.axis("off")
    lines = [
        f"Position:  residues {overview.position_start}-{overview.position_end}"
        + ("" if overview.is_contiguous else "  (non-contiguous numbering)"),
        *_wrapped("Summary:   ", overview.sequence_summary),
        "",
    ]
    if overview.molecular_weight is None:
        lines.append("Numeric properties unavailable (no standard-residue content).")
    else:
        lines += [
            f"Molecular weight:        {overview.molecular_weight:,.2f} Da",
            f"Isoelectric point (pI):  {overview.isoelectric_point:.2f}",
            "",
            "Extinction coefficient (280 nm):",
            f"  Cys reduced:   {overview.extinction_coefficient_reduced:,.0f} M-1cm-1",
            f"    A280 (1 mg/mL) = {overview.absorbance_1mgml_reduced:.3f}",
            f"  Cys oxidized:  {overview.extinction_coefficient_oxidized:,.0f} M-1cm-1",
            f"    A280 (1 mg/mL) = {overview.absorbance_1mgml_oxidized:.3f}",
            "",
            f"Instability index:  {overview.instability_index:.2f} ({overview.instability_class})",
            "",
            f"Net charge at pH 7.0:  {overview.net_charge_ph7:+.2f}",
        ]
    if overview.n_ambiguous_residues:
        lines.append("")
        lines += _wrapped("", f"({overview.n_ambiguous_residues} ambiguous residue(s) excluded from the above)")

    # Shrink to fit if there's an unusually long description/notes block —
    # the panel has a fixed height, but content length varies (long ids,
    # descriptions, and ambiguous-residue notes all add lines).
    fontsize, linespacing = (9.5, 1.6) if len(lines) <= 16 else (8.0, 1.3)

    ax.text(
        0.0, 1.0, "\n".join(lines),
        transform=ax.transAxes, ha="left", va="top",
        fontsize=fontsize, family="monospace", linespacing=linespacing,
    )


def _draw_aa_table(ax: plt.Axes, overview: ProteinOverview) -> None:
    ax.axis("off")
    df = aa_frequency_dataframe(overview)
    half = len(df) // 2 + len(df) % 2
    left, right = df.iloc[:half].reset_index(drop=True), df.iloc[half:].reset_index(drop=True)

    rows = []
    for i in range(len(left)):
        row = [left.loc[i, "residue"], int(left.loc[i, "count"]), f"{left.loc[i, 'percent']:.2f}%"]
        if i < len(right):
            row += [right.loc[i, "residue"], int(right.loc[i, "count"]), f"{right.loc[i, 'percent']:.2f}%"]
        else:
            row += ["", "", ""]
        rows.append(row)

    col_labels = ["AA", "Count", "%", "AA", "Count", "%"]
    table = ax.table(
        cellText=rows, colLabels=col_labels, loc="upper center", cellLoc="center",
        colWidths=[0.10, 0.13, 0.10, 0.10, 0.13, 0.10],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1, 1.35)
    for (row_i, _col_i), cell in table.get_celld().items():
        if row_i == 0:
            cell.set_facecolor("#e8e8e8")
            cell.set_text_props(weight="bold")
    ax.set_title("Amino acid frequencies", fontsize=10, loc="left", pad=14)


def generate_sequence_overview_pdf(
    overview: ProteinOverview,
    output_path: str,
    n_ph_ticks: int = 5,
) -> str:
    """Render a one-page sequence overview PDF for ``overview``.

    Parameters
    ----------
    overview:
        A :class:`~propro.core.properties.ProteinOverview`, e.g. from
        :func:`propro.core.properties.compute_overview`.
    output_path:
        Where to write the PDF.
    n_ph_ticks:
        Passed through to the charge-vs-pH chart (kept for API symmetry with
        ``print_report``; currently unused by the plot itself).

    Returns
    -------
    str
        ``output_path``, for convenient chaining.
    """
    fig = plt.figure(figsize=PAGE_SIZE)
    gs = fig.add_gridspec(
        3, 2, height_ratios=[0.08, 0.46, 0.46], width_ratios=[0.52, 0.48], hspace=0.25, wspace=0.35
    )

    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis("off")
    title = f"Sequence overview: {overview.id}"
    ax_title.text(0.0, 0.8, title, transform=ax_title.transAxes, ha="left", va="top",
                  fontsize=16, weight="bold")
    if overview.description:
        ax_title.text(0.0, 0.25, overview.description, transform=ax_title.transAxes,
                       ha="left", va="top", fontsize=10, style="italic", color="dimgray")

    ax_props = fig.add_subplot(gs[1, 0])
    _draw_key_properties(ax_props, overview)

    ax_chart = fig.add_subplot(gs[1, 1])
    if overview.net_charge_by_ph:
        plot_net_charge_vs_ph(overview, ax=ax_chart)
        ax_chart.set_title("Net charge vs. pH", fontsize=10)
        ax_chart.legend().remove() if ax_chart.get_legend() else None
    else:
        ax_chart.axis("off")
        ax_chart.text(0.5, 0.5, "No charge data\n(no standard-residue content)",
                      ha="center", va="center", fontsize=9, transform=ax_chart.transAxes)

    ax_table = fig.add_subplot(gs[2, :])
    _draw_aa_table(ax_table, overview)

    fig.text(
        0.02, 0.01,
        f"Generated by propro (propro/interfaces/pdf_reports/sequence_overview_pdf.py) — "
        f"{datetime.now():%Y-%m-%d %H:%M}",
        fontsize=6.5, color="gray",
    )

    fig.savefig(output_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    return output_path


def _default_output_name(seq_id: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in seq_id)
    return f"{safe}_overview.pdf"


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--sequence", help="Raw amino acid sequence.")
    src.add_argument("--fasta", help="Path to a FASTA file (one PDF per record).")
    parser.add_argument("--id", default=None, help="Sequence id (used with --sequence; ignored for --fasta).")
    parser.add_argument("--output", "-o", default=None, help="Output PDF path (single-sequence input only).")
    parser.add_argument("--outdir", default=".", help="Output directory (used with --fasta, or --sequence without --output).")
    parser.add_argument("--n-flank", type=int, default=10, help="Residues shown at each end in the summary line.")
    args = parser.parse_args(argv)

    proteins = []
    if args.sequence:
        proteins.append(ProteinSequence(args.sequence, id=args.id or "protein"))
    else:
        proteins.extend(ProteinSequence.from_fasta(args.fasta))

    outdir = Path(args.outdir)
    for protein in proteins:
        overview = compute_overview(protein, n_flank=args.n_flank)
        if args.output and len(proteins) == 1:
            out_path = args.output
        else:
            outdir.mkdir(parents=True, exist_ok=True)
            out_path = str(outdir / _default_output_name(protein.id))
        generate_sequence_overview_pdf(overview, out_path)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
