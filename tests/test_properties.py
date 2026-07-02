"""Tests for the BioPython-backed property engine.

These require BioPython, so the module is skipped (not failed) in
environments where it isn't installed: ``pip install biopython`` to run it.
"""

import pytest

pytest.importorskip("Bio")

from propro.core.properties import INSTABILITY_THRESHOLD, compute_overview
from propro.core.sequence import ProteinSequence

# Chicken egg-white lysozyme C (UniProt P00698, mature chain) — a standard
# reference sequence with well-documented ProtParam-style properties.
LYSOZYME = (
    "KVFGRCELAAAMKRHGLDNYRGYSLGNWVCAAKFESNFNTQATNRNTDGSTDYGILQINSRWWCNDGRTPGSRNLCNIPCSAL"
    "LSSDITASVNCAKKIVSDGNGMNAWVAWRNRCKGTDVQAWIRGCRL"
)


def test_length_and_position_range():
    protein = ProteinSequence(LYSOZYME, id="lysozyme")
    overview = compute_overview(protein)
    assert overview.length == len(LYSOZYME)
    assert overview.position_start == 1
    assert overview.position_end == len(LYSOZYME)


def test_molecular_weight_in_expected_range():
    # Lysozyme C is ~14.3 kDa; allow a generous window since exact average
    # mass tables vary slightly by source.
    overview = compute_overview(ProteinSequence(LYSOZYME, id="lysozyme"))
    assert 14000 < overview.molecular_weight < 14700


def test_pi_is_basic():
    # Lysozyme is a well-known basic protein (pI ~ 9-11).
    overview = compute_overview(ProteinSequence(LYSOZYME, id="lysozyme"))
    assert 8.5 < overview.isoelectric_point < 11.5


def test_instability_classification_matches_threshold():
    overview = compute_overview(ProteinSequence(LYSOZYME, id="lysozyme"))
    expected = "stable" if overview.instability_index <= INSTABILITY_THRESHOLD else "unstable"
    assert overview.instability_class == expected


def test_extinction_coefficient_oxidized_gte_reduced():
    overview = compute_overview(ProteinSequence(LYSOZYME, id="lysozyme"))
    assert overview.extinction_coefficient_oxidized >= overview.extinction_coefficient_reduced


def test_absorbance_equals_extinction_over_mw():
    overview = compute_overview(ProteinSequence(LYSOZYME, id="lysozyme"))
    assert overview.absorbance_1mgml_reduced == pytest.approx(
        overview.extinction_coefficient_reduced / overview.molecular_weight
    )
    assert overview.absorbance_1mgml_oxidized == pytest.approx(
        overview.extinction_coefficient_oxidized / overview.molecular_weight
    )


def test_aa_counts_sum_to_length():
    overview = compute_overview(ProteinSequence(LYSOZYME, id="lysozyme"))
    assert sum(overview.aa_counts.values()) == overview.length


def test_charge_decreases_with_increasing_ph():
    # Net charge vs. pH is monotonically non-increasing for a titration curve.
    overview = compute_overview(ProteinSequence(LYSOZYME, id="lysozyme"), ph_step=1.0)
    charges = [c for _, c in overview.net_charge_by_ph]
    assert all(a >= b - 1e-6 for a, b in zip(charges, charges[1:]))


def test_charge_near_zero_at_pi():
    overview = compute_overview(ProteinSequence(LYSOZYME, id="lysozyme"), ph_step=0.1)
    pi = overview.isoelectric_point
    closest_charge = min(overview.net_charge_by_ph, key=lambda pc: abs(pc[0] - pi))[1]
    assert abs(closest_charge) < 0.5


def test_ambiguous_residues_excluded_and_noted():
    protein = ProteinSequence("MKXTVW", id="has-x")
    overview = compute_overview(protein)
    assert overview.n_ambiguous_residues == 1
    assert overview.length == 6
    assert any("ambiguous" in note for note in overview.notes)


def test_n_flank_respects_short_sequences():
    protein = ProteinSequence("MKT", id="short")
    overview = compute_overview(protein, n_flank=10)
    assert overview.n_flank == 3
    assert "".join(aa for _, aa in overview.first_residues) == "MKT"
