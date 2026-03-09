# conflux/core/ast.py

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any


@dataclass
class Atom:
    """
    A predicate instance such as P(a,b,c).
    For DatalogMTL datasets, interval is stored as a tuple (a,b).
    """
    pred: str
    args: List[Any]
    interval: Tuple[int, int] = None  # Only used by DatalogMTL facts

@dataclass
class TemporalOp:
    """
    Base class for DatalogMTL temporal operators.
    Not used directly — extended by unary and binary operators.
    """
    kind: str   # e.g. "

@dataclass
class UnaryTemporalAtom(TemporalOp):
    """
    Unary temporal operator:
        Boxminus[a,b] φ
        Diamondminus[a,b] φ
        Boxplus[a,b] φ
        Diamondplus[a,b] φ
    """
    interval: tuple[int, int]
    child: any   # Atom, UnaryTemporalAtom, BinaryTemporalAtom

@dataclass
class BinaryTemporalAtom(TemporalOp):
    """
    Binary temporal operator with an interval [a,b],
    such as α U[a,b] β or α S[a,b] β.
    """
    interval: tuple[int, int]
    left: any   # α
    right: any  # β
@dataclass
class Rule:
    """
    Generic rule container (to be extended later for full LARS/MTL rule logic).
    Currently unused in dataset translation but needed for full Conflux support.
    """
    head: Any
    body: List[Any]


@dataclass
class ProgramIR:
    """
    The shared intermediate representation (IR) for all Conflux translations.

    - rules: list of Rule objects
    - extensional_facts: time-indexed dictionary of facts:
            time → [Atom, Atom, ...]
      For DatalogMTL input, these contain Atom(..., interval=(a,b)),
      which are then expanded by the translator.
    """

    rules: List[Rule] = field(default_factory=list)

    # DatalogMTL: extensional_facts maps "start interval" → list of Atom(interval=(a,b))
    # LARS: extensional_facts maps explicit time → list of Atom
    extensional_facts: Dict[int, List[Atom]] = field(default_factory=dict)