# conflux/translators/datalogmtl_lars/mtl_to_lars.py
from conflux.translators.base import Translator, SimpleReport
from conflux.core.ast import ProgramIR, Atom
from typing import Dict, List


class MtlToLars(Translator):
    """
    Translator for DatalogMTL → LARS datasets.
    This version only handles temporal facts of the form:

        P(c1,...,cn)@[a,b]

    and expands them into LARS interpretation streams:

        v_I(t) = { θ(P(c1,...,cn)) | t ∈ [a,b] }

    Later you can extend this class with rule translation.
    """

    name = "datalogmtl→lars"
    src = "DatalogMTL"
    dst = "LARS"

    # ----------------------------------------------------------------------
    # (A) MAIN ENTRY POINT
    # ----------------------------------------------------------------------
    def translate(self, ir: ProgramIR, *, options=None) -> ProgramIR:
        """
        Translate a DatalogMTL ProgramIR into a LARS ProgramIR.
        - We ignore rules for now.
        - We expand temporal facts over each time in [a,b].
        """
        lars_ir = ProgramIR()

        # Copy rules later if needed
        lars_ir.rules = []  # currently unused in your example

        # Expand extensional facts into time-indexed dictionary
        expanded_stream = self._expand_dataset(ir.extensional_facts)
        lars_ir.extensional_facts = expanded_stream

        return lars_ir

    # ----------------------------------------------------------------------
    # (B) SUPPORT CHECKER
    # ----------------------------------------------------------------------
    def check_support(self, ir):
        """
        For now we allow all datasets; more complex checks will be needed when
        you add metric rules or non-flat programs.
        """
        return SimpleReport(ok=True)

    # ----------------------------------------------------------------------
    # (C) TRANSLATION HELPERS
    # ----------------------------------------------------------------------
    def _theta_atom(self, atom: Atom) -> Atom:
        """
        θ mapping for relational atoms.
        (Currently identity: rename predicate or constants here if needed.)
        """
        return Atom(pred=atom.pred.lower(), args=atom.args)

    def _expand_dataset(self, dataset: Dict[int, List[Atom]]):
        """
        Expand DatalogMTL extensional facts:
            P(t1,...,tn)@[a,b]
        represented internally as extensional_facts[a] = [Atom(P(...), (a,b))]
        into LARS-style stream:
            stream[t] = { θ(P(...)) for all t in [a,b] }
        """
        stream: Dict[int, List[Atom]] = {}

        for start_time, facts in dataset.items():
            for f in facts:
                # Each Atom has args and may contain temporal interval info
                # We assume interval = (a, b) stored in f.args or metadata.
                # Conflux IR stores intervals in a tuple inside the Atom object.
                # For now, assume f has attributes: pred, args, interval
                if hasattr(f, "interval"):
                    a, b = f.interval
                else:
                    raise ValueError("DatalogMTL fact missing interval")

                for t in range(a, b + 1):
                    theta_f = self._theta_atom(f)
                    if t not in stream:
                        stream[t] = []
                    stream[t].append(theta_f)

        return stream