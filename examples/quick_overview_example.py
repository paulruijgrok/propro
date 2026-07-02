"""Example: quick biochemical overview of a protein sequence.

Run with:  python examples/quick_overview_example.py
Requires:  pip install -r requirements.txt
"""

from propro.core.properties import compute_overview
from propro.core.report import overview_to_dataframe, aa_frequency_dataframe, print_report
from propro.core.sequence import ProteinSequence
from propro.core.visualize import plot_net_charge_vs_ph

# Chicken egg-white lysozyme C (UniProt P00698, mature chain)
LYSOZYME = (
    "KVFGRCELAAAMKRHGLDNYRGYSLGNWVCAAKFESNFNTQATNRNTDGSTDYGILQINSRWWCNDGRTPGSRNLCNIPCSAL"
    "LSSDITASVNCAKKIVSDGNGMNAWVAWRNRCKGTDVQAWIRGCRL"
)


def main() -> None:
    protein = ProteinSequence(LYSOZYME, id="lysozyme_C", description="Chicken egg-white lysozyme C")
    overview = compute_overview(protein, n_flank=10)

    # 1. Console report
    print_report(overview)

    # 2. Tabular output (pandas), handy for exporting / passing to gscripts later
    print("\nSummary table:")
    print(overview_to_dataframe(overview).to_string(index=False))

    print("\nAmino acid frequency table:")
    print(aa_frequency_dataframe(overview).to_string(index=False))

    # 3. Plot
    ax = plot_net_charge_vs_ph(overview, save_path="lysozyme_net_charge_vs_ph.png")
    print("\nSaved plot to lysozyme_net_charge_vs_ph.png")


if __name__ == "__main__":
    main()
