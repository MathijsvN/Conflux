from conflux.core.ast import Atom, UnaryTemporalAtom, BinaryTemporalAtom, Rule, ProgramIR
from typing import Any, List


# ======================================================================
# Public API
# ======================================================================

def emit_lars_program(ir: ProgramIR) -> str:
    """
    Convert a ProgramIR into a textual LASER/LARS program.
    """
    lines = []
    for rule in ir.rules:
        lines.append(emit_rule(rule))
    return "\n".join(lines)


def emit_rule(rule: Rule) -> str:
    head_s = emit_formula(rule.head)
    if not rule.body:
        return f"{head_s}."
    body_s = ", ".join(emit_formula(lit) for lit in rule.body)
    return f"{head_s} :- {body_s}."


# ======================================================================
# Formula emitter
# ======================================================================

def emit_formula(node: Any) -> str:
    """
    Emit any LARS formula:
      - Atom
      - UnaryTemporalAtom (Boxminus, Boxplus, Diamondminus, Diamondplus)
      - BinaryTemporalAtom
      - dict forms produced by theta (time_win, box, diamond, until, since)
    """
    # -----------------------------
    # Relational atom
    # -----------------------------
    if isinstance(node, Atom):
        if node.args:
            args_s = ",".join(node.args)
            return f"{node.pred}({args_s})"
        return f"{node.pred}"

    # -----------------------------
    # Unary temporal operator
    # -----------------------------
    if isinstance(node, UnaryTemporalAtom):
        kind = node.kind.lower()
        a, b = node.interval
        child_s = emit_formula(node.child)

        if kind == "boxminus":
            return f"time_win({b},0,1, box({child_s}))"

        if kind == "diamondminus":
            return f"time_win({b},0,1, diamond({child_s}))"

        if kind == "boxplus":
            return f"time_win({b},0,1, box({child_s}))"

        if kind == "diamondplus":
            return f"time_win({b},0,1, diamond({child_s}))"

        raise ValueError(f"Unsupported UnaryTemporalAtom kind: {kind}")

    # -----------------------------
    # Binary temporal operator
    # -----------------------------
    if isinstance(node, BinaryTemporalAtom):
        kind = node.kind.lower()
        a, b = node.interval
        left_s = emit_formula(node.left)
        right_s = emit_formula(node.right)

        if kind == "until":
            # LASER does not have native UNTIL; represented as struct
            return f"until({left_s}, {right_s}, {a}, {b})"

        if kind == "since":
            return f"since({left_s}, {right_s}, {a}, {b})"

        raise ValueError(f"Unsupported BinaryTemporalAtom kind: {kind}")

    # -----------------------------
    # Dictionary nodes from theta
    # -----------------------------
    if isinstance(node, dict):
        op = node.get("op")

        # time_win
        if op == "time_win":
            length = node["length"]
            offset = node["offset"]
            hop = node["hop"]
            inner_s = emit_formula(node["inner"])
            return f"time_win({length},{offset},{hop}, {inner_s})"

        # box
        if op == "box":
            child_s = emit_formula(node["child"])
            return f"box({child_s})"

        # diamond
        if op == "diamond":
            child_s = emit_formula(node["child"])
            return f"diamond({child_s})"

        # until
        if op == "until":
            left_s = emit_formula(node["left"])
            right_s = emit_formula(node["right"])
            a = node["a"]
            b = node["b"]
            return f"until({left_s}, {right_s}, {a}, {b})"

        # since
        if op == "since":
            left_s = emit_formula(node["left"])
            right_s = emit_formula(node["right"])
            a = node["a"]
            b = node["b"]
            return f"since({left_s}, {right_s}, {a}, {b})"

        raise ValueError(f"Unknown dict op in LARS IR: {op}")

    # -----------------------------
    # Unknown node type
    # -----------------------------
    raise TypeError(f"Unsupported LARS formula node type: {type(node)}")