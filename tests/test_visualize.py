import matplotlib

matplotlib.use("Agg")  # headless test environment

from propro.core.visualize import plot_amino_acid_composition, plot_net_charge_vs_ph


def test_plot_net_charge_vs_ph_returns_axes(sample_overview):
    ax = plot_net_charge_vs_ph(sample_overview)
    assert ax.get_xlabel() == "pH"
    assert ax.get_ylabel() == "Net charge"


def test_plot_amino_acid_composition_returns_axes(sample_overview):
    ax = plot_amino_acid_composition(sample_overview)
    assert ax.get_xlabel() == "Residue"
