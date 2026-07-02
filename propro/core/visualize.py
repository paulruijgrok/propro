"""Quick, customizable visualizations for protein properties.

Plotting functions accept an optional ``ax`` so they can be composed into
larger figures (e.g. a multi-panel summary of several proteins), and return
the ``Axes`` they drew on.
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt

from propro.core.properties import ProteinOverview


def plot_net_charge_vs_ph(
    overview: ProteinOverview,
    ax: Optional[plt.Axes] = None,
    mark_pi: bool = True,
    mark_ph7: bool = True,
    color: str = "tab:blue",
    save_path: Optional[str] = None,
) -> plt.Axes:
    """Plot net charge as a function of pH.

    Parameters
    ----------
    overview:
        A :class:`~propro.core.properties.ProteinOverview` (from
        :func:`propro.core.properties.compute_overview`).
    ax:
        Existing matplotlib Axes to draw on. A new figure/axes is created if
        omitted.
    mark_pi:
        If True, draw a vertical dashed line at the isoelectric point.
    mark_ph7:
        If True, mark the net charge at physiological pH (7.0).
    save_path:
        If given, save the figure to this path.
    """
    if not overview.net_charge_by_ph:
        raise ValueError(
            f"'{overview.id}' has no net-charge data (likely no standard-residue content)."
        )

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))

    ph_values = [p for p, _ in overview.net_charge_by_ph]
    charges = [c for _, c in overview.net_charge_by_ph]

    ax.axhline(0, color="grey", linewidth=0.8, linestyle="-")
    ax.plot(ph_values, charges, color=color, linewidth=2, label=overview.id)

    if mark_pi and overview.isoelectric_point is not None:
        ax.axvline(overview.isoelectric_point, color="tab:red", linestyle="--", linewidth=1)
        ax.annotate(
            f"pI {overview.isoelectric_point:.2f}",
            xy=(overview.isoelectric_point, 0),
            xytext=(3, 6),
            textcoords="offset points",
            color="tab:red",
            fontsize=9,
        )

    if mark_ph7 and overview.net_charge_ph7 is not None:
        ax.scatter([7.0], [overview.net_charge_ph7], color="black", zorder=5, s=25)
        ax.annotate(
            f"pH 7: {overview.net_charge_ph7:+.1f}",
            xy=(7.0, overview.net_charge_ph7),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xlabel("pH")
    ax.set_ylabel("Net charge")
    ax.set_title(f"Net charge vs. pH — {overview.id}")
    ax.set_xlim(min(ph_values), max(ph_values))
    ax.grid(alpha=0.3)

    if save_path:
        ax.figure.savefig(save_path, dpi=150, bbox_inches="tight")

    return ax


def plot_amino_acid_composition(
    overview: ProteinOverview,
    ax: Optional[plt.Axes] = None,
    color: str = "tab:blue",
    save_path: Optional[str] = None,
) -> plt.Axes:
    """Bar chart of amino acid composition (percent of sequence)."""
    from propro.core.report import aa_frequency_dataframe

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))

    df = aa_frequency_dataframe(overview)
    ax.bar(df["residue"], df["percent"], color=color)
    ax.set_xlabel("Residue")
    ax.set_ylabel("Percent of sequence")
    ax.set_title(f"Amino acid composition — {overview.id}")
    ax.grid(alpha=0.3, axis="y")

    if save_path:
        ax.figure.savefig(save_path, dpi=150, bbox_inches="tight")

    return ax
