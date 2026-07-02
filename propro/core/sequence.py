"""Sequence container used throughout propro.

``ProteinSequence`` is a thin wrapper around a raw amino-acid sequence that
optionally carries per-residue numbering (e.g. numbering taken from a PDB
structure, or a custom scheme such as Kabat/IMGT numbering used later by
``propro.motifs.antibodies``). Every other module in ``propro.core`` takes a
``ProteinSequence`` as input rather than a bare string, so residue numbering
survives all the way through to reports and plots.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")
# Ambiguous / non-standard one-letter codes that occasionally show up in real
# sequences (X = unknown, B = Asx, Z = Glx, J = Leu/Ile, U = Selenocysteine,
# O = Pyrrolysine). These are accepted but flagged, since downstream property
# calculations (MW, pI, extinction coefficient, ...) are only defined for the
# standard 20 residues and will treat these approximately or ignore them.
AMBIGUOUS_AA = set("XBZJUO")


class InvalidSequenceError(ValueError):
    """Raised when a sequence contains characters that are not amino acids."""


@dataclass
class ProteinSequence:
    """A protein sequence plus optional metadata.

    Parameters
    ----------
    sequence:
        The amino-acid sequence, one-letter codes. Whitespace is stripped and
        the sequence is upper-cased on construction.
    id:
        Short identifier/name for the protein (e.g. a UniProt accession or a
        sample name). Defaults to ``"protein"``.
    positions:
        Optional per-residue numbering, same length as ``sequence``. Use this
        when the sequence numbering does not simply start at 1 (e.g. it was
        sliced out of a larger construct, has gaps from missing density in a
        structure, or follows an antibody numbering scheme). If omitted,
        residues are numbered sequentially starting at 1.
    description:
        Optional free-text description (e.g. copied from a FASTA header).
    """

    sequence: str
    id: str = "protein"
    positions: Optional[List[int]] = None
    description: str = ""
    allow_ambiguous: bool = True

    def __post_init__(self) -> None:
        self.sequence = "".join(self.sequence.split()).upper()
        if not self.sequence:
            raise InvalidSequenceError("Sequence is empty.")

        invalid = sorted(set(self.sequence) - STANDARD_AA - AMBIGUOUS_AA)
        if invalid:
            raise InvalidSequenceError(
                f"Sequence '{self.id}' contains non-amino-acid character(s): {invalid}"
            )

        ambiguous_present = sorted(set(self.sequence) & AMBIGUOUS_AA)
        if ambiguous_present and not self.allow_ambiguous:
            raise InvalidSequenceError(
                f"Sequence '{self.id}' contains ambiguous/non-standard residue(s) "
                f"{ambiguous_present}; set allow_ambiguous=True to proceed anyway."
            )

        if self.positions is None:
            self.positions = list(range(1, len(self.sequence) + 1))
        elif len(self.positions) != len(self.sequence):
            raise InvalidSequenceError(
                f"positions has length {len(self.positions)} but sequence has "
                f"length {len(self.sequence)}; they must match one-to-one."
            )

    def __len__(self) -> int:
        return len(self.sequence)

    def __str__(self) -> str:
        return self.sequence

    @property
    def has_ambiguous_residues(self) -> bool:
        return bool(set(self.sequence) & AMBIGUOUS_AA)

    @property
    def position_range(self) -> tuple:
        """(first, last) residue numbers covered by this sequence."""
        return (self.positions[0], self.positions[-1])

    @property
    def is_contiguous(self) -> bool:
        """True if positions increase by exactly 1 with no gaps."""
        return all(b - a == 1 for a, b in zip(self.positions, self.positions[1:]))

    def slice_by_position(self, start: int, end: int) -> "ProteinSequence":
        """Return the sub-sequence spanning residue numbers [start, end] (inclusive)."""
        idx = [i for i, p in enumerate(self.positions) if start <= p <= end]
        if not idx:
            raise ValueError(f"No residues found in position range [{start}, {end}].")
        sub_seq = "".join(self.sequence[i] for i in idx)
        sub_pos = [self.positions[i] for i in idx]
        return ProteinSequence(
            sequence=sub_seq,
            id=f"{self.id}[{start}-{end}]",
            positions=sub_pos,
            description=self.description,
            allow_ambiguous=self.allow_ambiguous,
        )

    @classmethod
    def from_fasta(cls, path: str, allow_ambiguous: bool = True) -> List["ProteinSequence"]:
        """Load one or more sequences from a FASTA file.

        Requires BioPython. Residue numbering is left as the default
        sequential 1..N since plain FASTA carries no positional metadata.
        """
        try:
            from Bio import SeqIO
        except ImportError as exc:  # pragma: no cover - exercised only without BioPython
            raise ImportError(
                "ProteinSequence.from_fasta requires BioPython. Install it with "
                "'pip install biopython'."
            ) from exc

        records = []
        for record in SeqIO.parse(path, "fasta"):
            records.append(
                cls(
                    sequence=str(record.seq),
                    id=record.id,
                    description=record.description,
                    allow_ambiguous=allow_ambiguous,
                )
            )
        if not records:
            raise ValueError(f"No sequences found in FASTA file: {path}")
        return records
