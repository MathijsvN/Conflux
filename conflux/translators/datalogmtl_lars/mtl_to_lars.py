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

        # ------------------------------------------------------------------
        # Translate rules 
        # ------------------------------------------------------------------
        lars_ir.rules = []
        for rule in ir.rules:
            lars_rule = self._translate_rule(rule)
            lars_ir.rules.append(lars_rule)
                

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
    # (C1) RULE TRANSLATION
    # ----------------------------------------------------------------------
    def _translate_rule(self, rule):
        """
        Translate a DatalogMTL rule into a LARS rule.
        rule.head and rule.body contain IR nodes.
        We translate each literal using θ, which we will implement later.
        """
        head_lars = self._theta_formula(rule.head)

        body_lars = []
        for lit in rule.body:
            body_lars.append(self._theta_formula(lit))

        # Recreate a LARS rule in IR form
        from conflux.core.ast import Rule
        return Rule(head=head_lars, body=body_lars)
    
    # ----------------------------------------------------------------------
    # (C) TRANSLATION HELPERS
    # ----------------------------------------------------------------------
    def _theta_atom(self, atom: Atom) -> Atom:
        """
        θ mapping for relational atoms.
        (Currently identity: rename predicate or constants here if needed.)
        """
        return Atom(pred=atom.pred.lower(), args=atom.args)
    
    def _theta_formula(self, node):
        """
        θ-translation for:
            - relational atoms
            - unary temporal operators (Boxminus, Diamondminus, Boxplus, Diamondplus)
            - binary temporal operators (Until, Since)

        The output is a LARS/laser-style IR tree that the emitter will later turn into:
            time_win(b,0,1, box(φ))
            time_win(b,0,1, diamond(φ))
            etc.
        """

        # -----------------------
        # CASE 1: Relational atom
        # -----------------------
        if isinstance(node, Atom):
            return self._theta_atom(node)

        # -----------------------
        # CASE 2: Unary metric operators
        # -----------------------
        from conflux.core.ast import UnaryTemporalAtom, BinaryTemporalAtom

        if isinstance(node, UnaryTemporalAtom):
            kind = node.kind.lower()
            a, b = node.interval
            child = self._theta_formula(node.child)

            # ----- Boxminus -----
            if kind == "boxminus":
                # always in the past window
                return {
                    "op": "time_win",
                    "length": b,
                    "offset": 0,
                    "hop": 1,
                    "inner": {"op": "box", "child": child},
                }

            # ----- Diamondminus -----
            if kind == "diamondminus":
                return {
                    "op": "time_win",
                    "length": b,
                    "offset": 0,
                    "hop": 1,
                    "inner": {"op": "diamond", "child": child},
                }

            # ----- Boxplus (future always) -----
            if kind == "boxplus":
                # LASER uses time_win the same way for future windows
                return {
                    "op": "time_win",
                    "length": b,
                    "offset": 0,
                    "hop": 1,
                    "inner": {"op": "box", "child": child},
                }

            # ----- Diamondplus (future eventually) -----
            if kind == "diamondplus":
                return {
                    "op": "time_win",
                    "length": b,
                    "offset": 0,
                    "hop": 1,
                    "inner": {"op": "diamond", "child": child},
                }

            raise NotImplementedError(f"Unary temporal operator not implemented: {kind}")

        # -----------------------
        # CASE 3: Binary operators (Until, Since)
        # -----------------------
        if isinstance(node, BinaryTemporalAtom):
            kind = node.kind.lower()
            a, b = node.interval
            left = self._theta_formula(node.left)
            right = self._theta_formula(node.right)

            if kind == "until":
                # α U[a,b] β  ≈  ∃t in window: β AND α holds until that t
                return {
                    "op": "until",
                    "length": b,
                    "offset": 0,
                    "hop": 1,
                    "a": a,
                    "b": b,
                    "left": left,
                    "right": right,
                }

            if kind == "since":
                return {
                    "op": "since",
                    "length": b,
                    "offset": 0,
                    "hop": 1,
                    "a": a,
                    "b": b,
                    "left": left,
                    "right": right,
                }

            raise NotImplementedError(f"Binary temporal operator not implemented: {kind}")

        # -----------------------
        # FALLBACK
        # -----------------------
        raise TypeError(f"Unsupported IR node type: {type(node)}")



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
    
    