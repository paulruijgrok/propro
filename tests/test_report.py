from propro.core.report import (
    aa_frequency_dataframe,
    charge_curve_dataframe,
    overview_to_dataframe,
    overview_to_markdown,
    print_report,
)


def test_aa_frequency_dataframe_includes_all_20_standard(sample_overview, capsys=None):
    df = aa_frequency_dataframe(sample_overview)
    assert len(df) >= 20  # 20 standard AAs, ambiguous ones appended if present
    assert set("ACDEFGHIKLMNPQRSTVWY").issubset(set(df["residue"]))
    assert df["count"].sum() == sample_overview.length


def test_aa_frequency_percentages_sum_to_100(sample_overview):
    df = aa_frequency_dataframe(sample_overview)
    # Individual percentages are rounded to 2 dp for display, so the sum can
    # be off by a small rounding artifact rather than landing on exactly 100.
    assert abs(df["percent"].sum() - 100.0) < 0.1


def test_charge_curve_dataframe_shape(sample_overview):
    df = charge_curve_dataframe(sample_overview)
    assert list(df.columns) == ["pH", "net_charge"]
    assert len(df) == len(sample_overview.net_charge_by_ph)


def test_overview_to_dataframe_has_key_properties(sample_overview):
    df = overview_to_dataframe(sample_overview)
    props = set(df["property"])
    for expected in [
        "molecular_weight_da",
        "isoelectric_point",
        "instability_index",
        "instability_class",
        "extinction_coefficient_reduced_M-1cm-1",
        "extinction_coefficient_oxidized_M-1cm-1",
        "absorbance_280nm_1mgml_reduced",
        "absorbance_280nm_1mgml_oxidized",
    ]:
        assert expected in props


def test_overview_to_markdown_contains_id(sample_overview):
    md = overview_to_markdown(sample_overview)
    assert sample_overview.id in md
    assert "Amino acid frequencies" in md


def test_print_report_runs_without_error(sample_overview, capsys):
    print_report(sample_overview)
    captured = capsys.readouterr()
    assert sample_overview.id in captured.out
    assert "Instability index" in captured.out
    assert "stable" in captured.out
