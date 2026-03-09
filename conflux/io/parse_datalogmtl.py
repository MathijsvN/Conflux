# conflux/io/parse_datalogmtl.py
from typing import List, Optional

from conflux.core.ast import (
    Atom,
    UnaryTemporalAtom,
    BinaryTemporalAtom,
    Rule,
)

# ============================================================
# PUBLIC API
# ============================================================

def parse_datalogmtl_program(path: str) -> List[Rule]:
    """
    Read a DatalogMTL rule file and return Rule IR objects.
    Ignores empty lines and lines starting with '#'.
    """
    rules: List[Rule] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            rules.append(parse_rule(line))
    return rules


# ============================================================
# RULE PARSING
# ============================================================

def parse_rule(line: str) -> Rule:
    """
    Parse a full rule:
        <head> :- <body>
    Head may itself be temporal (e.g., Boxplus[0,90]Immune(X)).
    """
    if ":-" not in line:
        raise ValueError(f"Invalid rule (no ':-'): {line}")

    head_part, body_part = line.split(":-", 1)
    head = parse_literal(head_part.strip())

    # Body: split only on top-level commas (ignore commas inside () or [])
    body_literals = [p.strip() for p in _split_top_level_commas(body_part)]
    body_nodes = [parse_literal(p) for p in body_literals if p]
    return Rule(head=head, body=body_nodes)


# ============================================================
# LITERAL PARSER (Since, Until, Box±, Diamond±, or Atom)
# ============================================================

def parse_literal(text: str):
    """
    Parse one literal that is:
      - Binary temporal:  part1 Since[a,b] part2 | part1 Until[a,b] part2
      - Unary temporal:   Boxplus[a,b] child | Boxminus[a,b] child
                          Diamondplus[a,b] child | Diamondminus[a,b] child
      - Atom:             p | p(X) | ns:Pred(A,B) (zero-arity allowed)

    Assumptions:
      - 'part*' fragments do NOT contain temporal operator keywords.
      - No requirement for whitespace anywhere.
    """
    s = text.strip()

    # 1) Binary (infix) — try Since then Until
    node = _try_parse_binary(s, "Since")
    if node is not None:
        return node
    node = _try_parse_binary(s, "Until")
    if node is not None:
        return node

    # 2) Unary (prefix) — support all four
    for op in ("Boxplus", "Boxminus", "Diamondplus", "Diamondminus"):
        node = _try_parse_unary_prefix(s, op)
        if node is not None:
            return node

    # 3) Fallback: relational atom
    return parse_atom(s)


# ============================================================
# BINARY HELPERS
# ============================================================

def _try_parse_binary(text: str, op: str) -> Optional[BinaryTemporalAtom]:
    """
    Parse:  part1 <op>[a,b] part2
    with optional spaces around the interval and no constraints on part1/part2
    except that they do not contain temporal operator keywords (by assumption).
    """
    low = text.lower()
    op_low = op.lower()
    # Accept optional spaces before '['
    # Find the keyword first
    k = low.find(op_low)
    if k == -1:
        return None

    # After the keyword, skip whitespace to the '['
    i = k + len(op)
    while i < len(text) and text[i].isspace():
        i += 1
    if i >= len(text) or text[i] != "[":
        # Not a proper binary form — let other parsers try
        return None

    left_text = text[:k].strip()
    if not left_text:
        # Not valid — leave for other parsers / better error later
        return None

    br_open = i
    br_close = text.find("]", br_open + 1)
    if br_close == -1:
        raise ValueError(f"Malformed {op} (missing ']'): {text}")

    a, b = _parse_interval_pair(text[br_open + 1 : br_close])

    right_text = text[br_close + 1 :].strip()
    if not right_text:
        raise ValueError(f"Malformed {op} expression (missing right operand): {text}")

    return BinaryTemporalAtom(
        kind=op_low,
        interval=(a, b),
        left=parse_literal(left_text),
        right=parse_literal(right_text),
    )


# ============================================================
# UNARY HELPERS
# ============================================================

def _try_parse_unary_prefix(text: str, op: str) -> Optional[UnaryTemporalAtom]:
    """
    Parse:  <op>[a,b] child
    Operator must be at the start (prefix). Optional spaces before '['.
    """
    s = text.lstrip()
    op_low = op.lower()
    if not s.lower().startswith(op_low):
        return None

    i = len(op)  # after the operator
    while i < len(s) and s[i].isspace():
        i += 1
    if i >= len(s) or s[i] != "[":
        return None

    br_open = i
    br_close = s.find("]", br_open + 1)
    if br_close == -1:
        raise ValueError(f"Malformed {op} interval (missing ']'): {text}")

    a, b = _parse_interval_pair(s[br_open + 1 : br_close])

    child_text = s[br_close + 1 :].strip()
    if not child_text:
        raise ValueError(f"Malformed {op} expression (missing child): {text}")

    return UnaryTemporalAtom(
        kind=op_low,
        interval=(a, b),
        child=parse_literal(child_text),
    )


# ============================================================
# ATOMS & SPLITTING
# ============================================================

def parse_atom(text: str) -> Atom:
    """
    Accepts:
      - zero-arity: p | ns:Flag
      - with args:  p(X) | ns:Pred(A,B)
    If '(' appears, require one well-formed arglist ending at the tail.
    """
    s = text.strip()
    if "(" not in s:
        if not s:
            raise ValueError("Empty atom")
        return Atom(pred=s, args=[])

    lpar = s.find("(")
    rpar = _find_matching_paren(s, lpar)
    if rpar != len(s) - 1:
        raise ValueError(f"Invalid atom syntax: {text}")

    pred = s[:lpar].strip()
    args_raw = s[lpar + 1 : rpar].strip()
    args = [] if not args_raw else [a.strip() for a in _split_args(args_raw)]

    if not pred:
        raise ValueError(f"Invalid atom (missing predicate): {text}")

    return Atom(pred=pred, args=args)


def _split_top_level_commas(s: str) -> List[str]:
    """
    Split by commas that are NOT inside (...) or [...].

    Example:
        "A(X),B(Y[1,2]),C"  -->  ["A(X)", "B(Y[1,2])", "C"]
    """
    out: List[str] = []
    buf: List[str] = []
    par = 0  # parentheses depth
    brk = 0  # bracket depth

    for ch in s:
        if ch == "(":
            par += 1
        elif ch == ")":
            par -= 1
        elif ch == "[":
            brk += 1
        elif ch == "]":
            brk -= 1

        # split only on commas at top level
        if ch == "," and par == 0 and brk == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)

    if buf:
        out.append("".join(buf).strip())
    return out


def _split_args(s: str) -> List[str]:
    """
    Split a function/atom argument list by commas that are not nested in
    sub-argument lists.

    Example:
        "X, f(Y,Z), g(h(1,2),3)"  -->  ["X", "f(Y,Z)", "g(h(1,2),3)"]
    """
    out: List[str] = []
    buf: List[str] = []
    depth = 0
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1

        if ch == "," and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf).strip())
    return out


def _find_matching_paren(s: str, i_open: int) -> int:
    """Return index of matching ')' for '(' at i_open, or -1 if mismatched."""
    if i_open < 0 or i_open >= len(s) or s[i_open] != "(":
        return -1
    depth = 1
    for j in range(i_open + 1, len(s)):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    return -1


def _parse_interval_pair(s: str) -> tuple[int, int]:
    """
    Parse the inside of an interval specification '[a,b]' (without the brackets),
    allowing spaces. Returns (a, b) as integers.

    Raises:
        ValueError if the format is invalid or bounds are not integers.
    """
    parts = [p.strip() for p in s.split(",")]
    if len(parts) != 2:
        raise ValueError(f"Invalid interval '[{s}]' — expected 'a,b'")
    try:
        a = int(parts[0])
        b = int(parts[1])
    except ValueError as e:
        raise ValueError(f"Interval bounds must be integers in '[{s}]'") from e
    return a, b