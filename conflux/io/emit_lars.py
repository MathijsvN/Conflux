# conflux/io/emit_lars.py

from typing import Any, List, Literal
from conflux.core.ast import Atom, UnaryTemporalAtom, BinaryTemporalAtom, Rule, ProgramIR

Target = Literal["laser1", "laser2"]


# ======================================================================
# Public API
# ======================================================================

def emit_lars_program(ir: ProgramIR, *, target: Target = "laser2") -> str:
    """
    Emit the entire LARS program in Laser1 or Laser2 syntax.

    Default = Laser2 (ARES-style), using:
        [B] φ, [D] φ, [$, n] φ, [#, n] φ, [@, T] φ

    Laser1 uses:
        time_win(...), box(...), diamond(...)
    """
    lines = []
    for rule in ir.rules:
        lines.append(emit_rule(rule, target=target))
    return "\n".join(lines)


def emit_rule(rule: Rule, *, target: Target = "laser2") -> str:
    head_s = emit_formula(rule.head, target=target)
    if not rule.body:
        return f"{head_s}."
    body_s = " and ".join(emit_formula(lit, target=target) for lit in rule.body)
    return f"{head_s} :- {body_s}"


# ======================================================================
# Formula emitter
# ======================================================================

def emit_formula(node: Any, *, target: Target = "laser2") -> str:
    """
    Emit any LARS formula:
        - Atom
        - UnaryTemporalAtom (Boxminus/plus, Diamondminus/plus)
        - BinaryTemporalAtom (Since/Until)
        - dict nodes produced by θ
    """

    # ---------------------------------------------------------
    # Relational atom
    # ---------------------------------------------------------
    if isinstance(node, Atom):
        return _emit_atom(node)

    # ---------------------------------------------------------
    # Unary temporal operators (Boxminus/plus, Diamondminus/plus)
    # ---------------------------------------------------------
    if isinstance(node, UnaryTemporalAtom):
        kind = node.kind.lower()
        a, b = node.interval
        inner = emit_formula(node.child, target=target)

        if target == "laser2":
            # Laser2 window operator:
            #   [$, b] [B] φ     (box)
            #   [$, b] [D] φ     (diamond)
            if kind.startswith("box"):
                return f"[$, {b}] [B] {paren(inner)}"
            if kind.startswith("diamond"):
                return f"[$, {b}] [D] {paren(inner)}"

        else:  # Laser1
            if kind.startswith("box"):
                return f"time_win({b},0,1, box({inner}))"
            if kind.startswith("diamond"):
                return f"time_win({b},0,1, diamond({inner}))"

        raise ValueError(f"Unsupported unary temporal operator: {kind}")

    # ---------------------------------------------------------
    # Binary temporal (Since / Until)
    # ---------------------------------------------------------
    if isinstance(node, BinaryTemporalAtom):
        kind = node.kind.lower()
        a, b = node.interval
        left_s = emit_formula(node.left, target=target)
        right_s = emit_formula(node.right, target=target)

        if kind == "since":
            # θ(φ1 S[a,b] φ2) = three conjuncts
            # 1. [$, b] [B] ([$, b-a] [D] R)
            part1 = f"[$, {b}] [B] ([$, {b-a}] [D] {right_s} && ([$, 0] [B] {left_s}) )"

            # # 2. [$, 0] [B] L          // “infinite” past window
            # part2 = f"[$, 0] [B] {left_s}"

            # 3. [$, a] [B] L
            part3 = f"[$, {a}] [B] {left_s}"

            # return f"{part1} && {part2} && {part3}"
            return f"{part1} && {part3}"


        if kind == "until":
            # θ(φ1 U[a,b] φ2) = three conjuncts (same as since, but future)
            # Laser2 lacks direct future windows, so we output the theoretical window form
            # without @-shift until the user specifies a convention.
            part1 = f"[$, {b}] [B] ([$, {b-a}] [D] {right_s})"
            part2 = f"[$, 0] [B] {left_s}"
            part3 = f"[$, {a}] [B] {left_s}"

            return f"{part1} && {part2} && {part3}"

        else :
            raise ValueError(f"Unsupported binary operator: {kind}")

    # ---------------------------------------------------------
    # Dictionary nodes produced by θ
    # ---------------------------------------------------------
    if isinstance(node, dict):
        op = node.get("op")

        # time window
        if op == "time_win":
            length = node["length"]
            offset = node.get("offset", 0)
            hop = node.get("hop", 1)
            inner_s = emit_formula(node["inner"], target=target)

            if target == "laser2":
                return f"[$, {length}] {paren(inner_s)}"
            else:
                return f"time_win({length},{offset},{hop}, {inner_s})"

        # box
        if op == "box":
            child_s = emit_formula(node["child"], target=target)
            if target == "laser2":
                return f"[B] {paren(child_s)}"
            else:
                return f"box({child_s})"

        # diamond
        if op == "diamond":
            child_s = emit_formula(node["child"], target=target)
            if target == "laser2":
                return f"[D] {paren(child_s)}"
            else:
                return f"diamond({child_s})"

        # tuple window (#, n)
        if op == "tuple_win":
            size = node["size"]
            child_s = emit_formula(node["child"], target=target)
            if target == "laser2":
                return f"[#, {size}] {paren(child_s)}"
            else:
                return f"tuple_win({size}, {child_s})"

        # time reference operator @
        if op == "at":
            time_s = node["time"]
            child_s = emit_formula(node["child"], target=target)
            if target == "laser2":
                return f"[@, {time_s}] {paren(child_s)}"
            else:
                return f"@({time_s}, {child_s})"

        # binary ops
        if op == "since":
            # print(("Node: ", node))
            left_s = emit_formula(node["left"], target=target)
            right_s = emit_formula(node["right"], target=target)
            a, b = node["a"], node["b"]

            # θ(φ1 S[a,b] φ2) = three conjuncts
            # 1. [$, b] [B] ([$, b-a] [D] R)
            part1 = f"[$, {b}] [B] ([$, {b-a}] [D] {right_s} && ([$, 0] [B] {left_s}) )"

            # # 2. [$, 0] [B] L          // “infinite” past window
            # part2 = f"[$, 0] [B] {left_s}"

            # 3. [$, a] [B] L
            part3 = f"[$, {a}] [B] {left_s}"

            # return f"{part1} && {part2} && {part3}"
            return f"{part1} && {part3}"


        if op == "until":
            left_s = emit_formula(node["left"], target=target)
            right_s = emit_formula(node["right"], target=target)
            a, b = node["a"], node["b"]
            return f"until({left_s}, {right_s}, {a}, {b})"

        raise ValueError(f"Unknown dict op: {op}")

    # ---------------------------------------------------------
    # Catch-all
    # ---------------------------------------------------------
    raise TypeError(f"Unsupported formula node type: {type(node)}")


# ======================================================================
# Helpers
# ======================================================================

def _emit_atom(atom: Atom) -> str:
    if atom.args:
        return f"{atom.pred}({','.join(atom.args)})"
    return atom.pred


def paren(s: str) -> str:
    """
    Add parentheses only when needed (complex forms).
    Laser2 examples usually omit parentheses for atoms:
        [B] Immune(X)
    But keep them for nested since/until or windows.
    """
    s = s.strip()

    # If it already begins with a modal/window or since/until, leave it bare.
    if (
        s.startswith("[") or
        s.startswith("since(") or
        s.startswith("until(") or
        s.startswith("@") or
        s.startswith("time_win(")
    ):
        return s

    # Atom or simple term — no parentheses needed.
    if "(" in s and s.endswith(")"):
        return s

    return s