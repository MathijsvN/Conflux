import pytest

from conflux.io.emit_lars import emit_formula, emit_rule, emit_lars_program
from conflux.core.ast import Atom, UnaryTemporalAtom, BinaryTemporalAtom, Rule, ProgramIR


# ----------------------------------------------------------------------
# Atomic formulas
# ----------------------------------------------------------------------
def test_emit_atom_no_args():
    a = Atom(pred="p", args=[])
    assert emit_formula(a) == "p"


def test_emit_atom_with_args():
    a = Atom(pred="p", args=["X", "Y"])
    assert emit_formula(a) == "p(X,Y)"


# ----------------------------------------------------------------------
# Unary temporal operators (Boxminus, Diamondminus, Boxplus, Diamondplus)
# ----------------------------------------------------------------------
def test_emit_boxminus():
    inner = Atom(pred="s", args=["X"])
    node = UnaryTemporalAtom(kind="boxminus", interval=(0,5), child=inner)
    assert emit_formula(node) == "time_win(5,0,1, box(s(X)))"


def test_emit_diamondminus():
    inner = Atom(pred="a", args=["X"])
    node = UnaryTemporalAtom(kind="diamondminus", interval=(0,2), child=inner)
    assert emit_formula(node) == "time_win(2,0,1, diamond(a(X)))"


def test_emit_boxplus():
    inner = Atom(pred="p", args=["X"])
    node = UnaryTemporalAtom(kind="boxplus", interval=(0,3), child=inner)
    assert emit_formula(node) == "time_win(3,0,1, box(p(X)))"


def test_emit_diamondplus():
    inner = Atom(pred="q", args=["X"])
    node = UnaryTemporalAtom(kind="diamondplus", interval=(0,4), child=inner)
    assert emit_formula(node) == "time_win(4,0,1, diamond(q(X)))"


# ----------------------------------------------------------------------
# Binary operators (Until, Since)
# ----------------------------------------------------------------------
def test_emit_until():
    left = Atom(pred="p", args=["X"])
    right = Atom(pred="q", args=["X"])
    node = BinaryTemporalAtom(kind="until", interval=(2,5), left=left, right=right)
    assert emit_formula(node) == "until(p(X), q(X), 2, 5)"


def test_emit_since():
    left = Atom(pred="p", args=["X"])
    right = Atom(pred="q", args=["X"])
    node = BinaryTemporalAtom(kind="since", interval=(1,3), left=left, right=right)
    assert emit_formula(node) == "since(p(X), q(X), 1, 3)"


# ----------------------------------------------------------------------
# Rule emission
# ----------------------------------------------------------------------
def test_emit_rule_single_unary():
    head = Atom(pred="r", args=["X"])
    body = [UnaryTemporalAtom(kind="boxminus", interval=(0,5),
                      child=Atom(pred="s", args=["X"]))]
    rule = Rule(head=head, body=body)

    out = emit_rule(rule)
    assert out == "r(X) :- time_win(5,0,1, box(s(X)))."


def test_emit_rule_multiple_literals():
    head = Atom(pred="r", args=["X"])
    body = [
        UnaryTemporalAtom(kind="boxminus", interval=(0,5), child=Atom(pred="s", args=["X"])),
        Atom(pred="p", args=["Y"])
    ]
    rule = Rule(head=head, body=body)

    out = emit_rule(rule)
    assert out == "r(X) :- time_win(5,0,1, box(s(X))), p(Y)."


# ----------------------------------------------------------------------
# Program emission
# ----------------------------------------------------------------------
def test_emit_lars_program():
    head1 = Atom(pred="r", args=["X"])
    rule1 = Rule(head1, [Atom(pred="p", args=["X"])])

    head2 = Atom(pred="a", args=["Y"])
    rule2 = Rule(head2, [UnaryTemporalAtom(kind="diamondminus", interval=(0,2),
                                   child=Atom(pred="b", args=["Y"]))])

    ir = ProgramIR(rules=[rule1, rule2])

    out = emit_lars_program(ir)
    lines = out.split("\n")

    assert lines[0] == "r(X) :- p(X)."
    assert lines[1] == "a(Y) :- time_win(2,0,1, diamond(b(Y)))."