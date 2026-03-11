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
# Unary temporal operators (support both Laser1 and Laser2 syntax)
# ----------------------------------------------------------------------
@pytest.mark.parametrize("kind,interval,child,expected1,expected2", [
    ("boxminus", (0, 5), Atom(pred="s", args=["X"]),
     "time_win(5,0,1, box(s(X)))", "[$, 5] [B] s(X)"),
    ("diamondminus", (0, 2), Atom(pred="a", args=["X"]),
     "time_win(2,0,1, diamond(a(X)))", "[$, 2] [D] a(X)"),
])
def test_emit_unary_temporal(kind, interval, child, expected1, expected2):
    node = UnaryTemporalAtom(kind=kind, interval=interval, child=child)
    assert emit_formula(node, target="laser1") == expected1
    assert emit_formula(node, target="laser2") == expected2


# ----------------------------------------------------------------------
# Binary operators (Until, Since) - Not supported in Laser1/Laser2
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Rule emission
# ----------------------------------------------------------------------
@pytest.mark.parametrize("target,expected_single,expected_multi", [
    ("laser1",
     "r(X) :- time_win(5,0,1, box(s(X)))",
     "r(X) :- time_win(5,0,1, box(s(X))) and p(Y)"),
    ("laser2",
     "r(X) :- [$, 5] [B] s(X)",
     "r(X) :- [$, 5] [B] s(X) and p(Y)"),
])
def test_emit_rule_variants(target, expected_single, expected_multi):
    head = Atom(pred="r", args=["X"])
    body = [UnaryTemporalAtom(kind="boxminus", interval=(0, 5), child=Atom(pred="s", args=["X"]))]
    rule = Rule(head=head, body=body)
    assert emit_rule(rule, target=target) == expected_single

    rule2 = Rule(head=head, body=[
        UnaryTemporalAtom(kind="boxminus", interval=(0, 5), child=Atom(pred="s", args=["X"])),
        Atom(pred="p", args=["Y"])
    ])
    assert emit_rule(rule2, target=target) == expected_multi


# ----------------------------------------------------------------------
# Program emission
# ----------------------------------------------------------------------
@pytest.mark.parametrize("target,first,second", [
    ("laser1", "r(X) :- p(X)", "a(Y) :- time_win(2,0,1, diamond(b(Y)))"),
    ("laser2", "r(X) :- p(X)", "a(Y) :- [$, 2] [D] b(Y)")
])
def test_emit_lars_program(target, first, second):
    head1 = Atom(pred="r", args=["X"])
    rule1 = Rule(head1, [Atom(pred="p", args=["X"])])

    head2 = Atom(pred="a", args=["Y"])
    rule2 = Rule(head2, [UnaryTemporalAtom(kind="diamondminus", interval=(0, 2),
                                   child=Atom(pred="b", args=["Y"]))])

    ir = ProgramIR(rules=[rule1, rule2])

    out = emit_lars_program(ir, target=target)
    lines = out.split("\n")

    assert lines[0] == first
    assert lines[1] == second