import pytest

from propro.core.sequence import InvalidSequenceError, ProteinSequence


def test_default_positions_are_sequential():
    p = ProteinSequence("MKTV")
    assert p.positions == [1, 2, 3, 4]
    assert p.position_range == (1, 4)
    assert len(p) == 4


def test_whitespace_and_case_are_normalized():
    p = ProteinSequence(" mk\n tv ")
    assert p.sequence == "MKTV"


def test_custom_positions_preserved():
    p = ProteinSequence("MKTV", positions=[101, 102, 103, 104])
    assert p.position_range == (101, 104)
    assert p.is_contiguous


def test_non_contiguous_positions_detected():
    p = ProteinSequence("MKTV", positions=[1, 2, 5, 6])
    assert not p.is_contiguous


def test_mismatched_positions_length_raises():
    with pytest.raises(InvalidSequenceError):
        ProteinSequence("MKTV", positions=[1, 2, 3])


def test_invalid_character_raises():
    with pytest.raises(InvalidSequenceError):
        ProteinSequence("MK1V")


def test_ambiguous_allowed_by_default():
    p = ProteinSequence("MKXV")
    assert p.has_ambiguous_residues


def test_ambiguous_rejected_when_disallowed():
    with pytest.raises(InvalidSequenceError):
        ProteinSequence("MKXV", allow_ambiguous=False)


def test_empty_sequence_raises():
    with pytest.raises(InvalidSequenceError):
        ProteinSequence("   ")


def test_slice_by_position():
    p = ProteinSequence("MKTVWCCY", positions=[10, 11, 12, 13, 14, 15, 16, 17])
    sub = p.slice_by_position(12, 15)
    assert sub.sequence == "TVWC"
    assert sub.positions == [12, 13, 14, 15]
