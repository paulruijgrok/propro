"""Tests for propro.interfaces.pdf_reports.sequence_overview_pdf.

Builds a ProteinOverview by hand (same pattern as tests/conftest.py) so this
doesn't require BioPython — it only exercises PDF assembly, not the underlying
property calculations.
"""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")  # headless test environment

from propro.core.properties import ProteinOverview  # noqa: E402
from propro.interfaces.pdf_reports.sequence_overview_pdf import (  # noqa: E402
    _wrapped,
    generate_sequence_overview_pdf,
)


def _make_overview(**overrides) -> ProteinOverview:
    seq = "MKTVWCCYHDEKAGRSTPLNQIF"
    aa_counts = {aa: seq.count(aa) for aa in set(seq)}
    length = len(seq)
    aa_percent = {aa: 100.0 * n / length for aa, n in aa_counts.items()}
    mw = 2650.3
    ext_red, ext_ox = 6990.0, 7115.0

    defaults = dict(
        id="test_peptide",
        description="synthetic test sequence",
        length=length,
        n_ambiguous_residues=0,
        position_start=1,
        position_end=length,
        is_contiguous=True,
        n_flank=10,
        first_residues=list(zip(range(1, 11), seq[:10])),
        last_residues=list(zip(range(length - 9, length + 1), seq[-10:])),
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
    defaults.update(overrides)
    return ProteinOverview(**defaults)


def test_wrapped_short_value_is_single_line():
    lines = _wrapped("Label: ", "short value")
    assert lines == ["Label: short value"]


def test_wrapped_long_value_indents_continuation():
    long_value = "x" * 80
    lines = _wrapped("Label: ", long_value, width=20)
    assert len(lines) > 1
    assert lines[0].startswith("Label: ")
    assert all(line.startswith(" " * len("Label: ")) for line in lines[1:])


def test_generates_single_page_pdf(tmp_path):
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    overview = _make_overview()
    out = generate_sequence_overview_pdf(overview, str(tmp_path / "out.pdf"))

    assert Path(out).exists()
    assert Path(out).stat().st_size > 0
    reader = PdfReader(out)
    assert len(reader.pages) == 1


def test_handles_long_description_and_ambiguous_note_without_crashing(tmp_path):
    overview = _make_overview(
        id="a_fairly_long_test_identifier_for_stress_testing",
        description="A deliberately long description to stress-test text wrapping in the properties panel.",
        n_ambiguous_residues=2,
        notes=["2 ambiguous/non-standard residue(s) excluded from calculations."],
    )
    out = generate_sequence_overview_pdf(overview, str(tmp_path / "out_long.pdf"))
    assert Path(out).exists() and Path(out).stat().st_size > 0


def test_handles_no_charge_data(tmp_path):
    overview = _make_overview(
        molecular_weight=None, isoelectric_point=None, instability_index=None,
        instability_class=None, extinction_coefficient_reduced=None,
        extinction_coefficient_oxidized=None, absorbance_1mgml_reduced=None,
        absorbance_1mgml_oxidized=None, net_charge_by_ph=[], net_charge_ph7=None,
    )
    out = generate_sequence_overview_pdf(overview, str(tmp_path / "out_nodata.pdf"))
    assert Path(out).exists() and Path(out).stat().st_size > 0
