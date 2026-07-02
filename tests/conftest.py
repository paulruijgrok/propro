"""Shared pytest fixtures.

``sample_overview`` builds a ProteinOverview by hand (no BioPython required)
so that report/visualize code can be exercised even in environments where
BioPython isn't installed. Properties-engine tests that actually need
BioPython (``test_properties.py``) skip themselves via
``pytest.importorskip("Bio")`` instead of depending on this fixture.
"""

import pytest

from propro.core.properties import ProteinOverview


@pytest.fixture
def sample_overview() -> ProteinOverview:
    # Hand-crafted, internally-consistent numbers for a fictitious 12-residue
    # peptide "MKTVWCCYHDEK" — not meant to be biologically precise, only
    # self-consistent enough to exercise formatting/plotting code paths.
    seq = "MKTVWCCYHDEK"
    aa_counts = {aa: seq.count(aa) for aa in set(seq)}
    length = len(seq)
    aa_percent = {aa: 100.0 * n / length for aa, n in aa_counts.items()}

    mw = 1465.7
    ext_red = 6990.0  # 1*Trp(5500) + 1*Tyr(1490)
    ext_ox = ext_red + 125.0  # one Cys-Cys pair

    return ProteinOverview(
        id="test-peptide",
        description="synthetic test sequence",
        length=length,
        n_ambiguous_residues=0,
        position_start=1,
        position_end=length,
        is_contiguous=True,
        n_flank=5,
        first_residues=list(zip(range(1, 6), seq[:5])),
        last_residues=list(zip(range(length - 4, length + 1), seq[-5:])),
        molecular_weight=mw,
        isoelectric_point=8.25,
        instability_index=30.36,
        instability_class="stable",
        extinction_coefficient_reduced=ext_red,
        extinction_coefficient_oxidized=ext_ox,
        absorbance_1mgml_reduced=ext_red / mw,
        absorbance_1mgml_oxidized=ext_ox / mw,
        aa_counts=aa_counts,
        aa_percent=aa_percent,
        net_charge_by_ph=[(float(ph) / 2, 6.0 - 0.4 * ph) for ph in range(0, 29)],
        net_charge_ph7=1.2,
        notes=[],
    )
