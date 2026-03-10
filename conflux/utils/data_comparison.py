# conflux/utils/data_comparison.py

from typing import Set, Tuple
import re


def parse_datalogmtl_data(path: str) -> Set[Tuple[int, str]]:
    """
    Parse a DatalogMTL data file and return a set of (time, atom_str) pairs.
    Expands intervals [a,b] into individual times a to b.
    """
    facts: Set[Tuple[int, str]] = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "@" not in line:
                continue
            atom_part, interval_part = line.split("@", 1)
            interval_part = interval_part.strip().lstrip("[").rstrip("]")
            if "," not in interval_part:
                continue
            a_str, b_str = interval_part.split(",", 1)
            a, b = int(a_str.strip()), int(b_str.strip())

            # Normalize atom: lowercase pred, lowercase args
            pred = atom_part.split("(")[0].strip().lower()
            args_part = atom_part[len(pred):].strip().lstrip("(").rstrip(")")
            args = [arg.strip().lower() for arg in args_part.split(",")] if args_part else []
            atom_str = f"{pred}({','.join(args)})"

            for t in range(a, b + 1):
                facts.add((t, atom_str))
    return facts


def parse_lars_data(path: str) -> Set[Tuple[int, str]]:
    """
    Parse a LARS data file and return a set of (time, atom_str) pairs.
    Handles both single times and ranges like "182-199: atom".
    """
    facts: Set[Tuple[int, str]] = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            time_part, atoms_part = line.split(":", 1)
            time_part = time_part.strip()

            # Parse time range
            if "-" in time_part:
                start_str, end_str = time_part.split("-", 1)
                start_t = int(start_str.strip())
                end_t = int(end_str.strip())
                times = range(start_t, end_t + 1)
            else:
                times = [int(time_part)]

            # Parse atoms
            atoms_part = atoms_part.strip()
            if atoms_part:
                atom_strs = [a.strip() for a in atoms_part.split(",")]
                for atom_str in atom_strs:
                    # Normalize: already lowercase in output
                    for t in times:
                        facts.add((t, atom_str))
    return facts


def compare_data_semantics(dmtl_path: str, lars_path: str) -> bool:
    """
    Compare two data files semantically.
    Returns True if they represent the same temporal facts.
    """
    dmtl_facts = parse_datalogmtl_data(dmtl_path)
    lars_facts = parse_lars_data(lars_path)
    return dmtl_facts == lars_facts


def diff_fact_sets(dmtl_facts: Set[Tuple[int, str]], lars_facts: Set[Tuple[int, str]]) -> Tuple[Set[Tuple[int, str]], Set[Tuple[int, str]]]:
    """Return the differences between two fact sets.

    The returned tuple is ``(only_in_dmtl, only_in_lars)`` where each set
    contains time‑atom pairs that are missing from the other collection.
    """
    only_in_dmtl = dmtl_facts - lars_facts
    only_in_lars = lars_facts - dmtl_facts
    return only_in_dmtl, only_in_lars


def format_fact_set(facts: Set[Tuple[int, str]]) -> str:
    """Format a set of facts into a sorted, human-readable string."""
    if not facts:
        return "(none)"
    sorted_list = sorted(facts)
    return "\n".join(f"{t}: {atom}" for t, atom in sorted_list)


def compare_data_semantics_from_sets(dmtl_facts: Set[Tuple[int, str]], lars_facts: Set[Tuple[int, str]]) -> bool:
    """
    Compare two sets of facts directly.

    Returns ``True`` if they represent the same temporal facts.  When the
    sets differ a summary of the discrepancies is printed to standard output
    (useful for debugging tests or translation issues).
    """
    if dmtl_facts == lars_facts:
        return True

    only_in_dmtl, only_in_lars = diff_fact_sets(dmtl_facts, lars_facts)

    print("\n=== DATASET DIFFERENCES ===")
    print("Facts only in DatalogMTL dataset:")
    print(format_fact_set(only_in_dmtl))
    print("\nFacts only in LARS dataset:")
    print(format_fact_set(only_in_lars))
    print("=== END DIFFERENCES ===\n")

    return False