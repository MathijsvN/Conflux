import os
from conflux.core.ast import ProgramIR
from conflux.translators.datalogmtl_lars.mtl_to_lars import MtlToLars
from typing import Dict, List
from conflux.core.ast import Atom

def load_datalogmtl_dataset(path: str) -> Dict[int, List[Atom]]:
    facts: Dict[int, List[Atom]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):  # comments or blank lines
                continue
            atom_part, interval_part = line.split("@")
            interval_part = interval_part.replace("[", "").replace("]", "").replace("@", "")
            a_str, b_str = interval_part.split(",")
            a, b = int(a_str), int(b_str)

            pred_name = atom_part.split("(")[0].strip()
            args_part = atom_part[len(pred_name):].strip().lstrip("(").rstrip(")")
            args = [a_.strip() for a_ in args_part.split(",")] if args_part else []

            atom = Atom(pred=pred_name, args=args, interval=(a, b))
            facts.setdefault(a, []).append(atom)
    return facts

def condense_stream_lines(lines: list[str], *, min_run: int = 6) -> list[str]:
    """
    Condense consecutive lines with identical payloads into ranges.
    Expects lines of the form:  "<t>: <payload>"
    Returns lines where long runs (len >= min_run) become "<t0–t1>: <payload>".

    Example input lines (sorted by t):
      "182: nosympt(ben)"
      "183: nosympt(ben)"
      ...
      "199: nosympt(ben)"
      "200: vaccinated(ben), nosympt(ben)"
      "201: nosympt(ben)"
      ...
      "320: nosympt(ben)"
    """
    def parse(line: str):
        # split once on ":", keep payload as-is
        left, right = line.split(":", 1)
        t = int(left.strip())
        payload = right.strip()
        return t, payload

    # Parse all
    parsed = [parse(l) for l in lines]
    if not parsed:
        return []

    out: list[str] = []
    i = 0
    n = len(parsed)

    while i < n:
        t0, payload0 = parsed[i]
        j = i + 1
        # advance while times are consecutive AND payload identical
        while j < n and parsed[j][0] == parsed[j-1][0] + 1 and parsed[j][1] == payload0:
            j += 1
        run_len = j - i
        if run_len >= min_run:
            t1 = parsed[j-1][0]
            out.append(f"{t0}–{t1}: {payload0}")
        else:
            # emit individually
            for k in range(i, j):
                tk, _ = parsed[k]
                out.append(f"{tk}: {payload0}")
        i = j

    return out

def test_mtl_dataset_to_lars(input_path: str,
                             output_path: str,
                             output_dir: str = "tests/output/datalogmtl_to_lars") -> None:
    os.makedirs(output_dir, exist_ok=True)

    ir = ProgramIR()
    ir.extensional_facts = load_datalogmtl_dataset(input_path)

    translator = MtlToLars()
    result_ir = translator.translate(ir)

    lines = []
    for t in sorted(result_ir.extensional_facts.keys()):
        entries = []
        for atom in result_ir.extensional_facts[t]:
            pred = atom.pred.lower()
            args_s = ",".join(a.lower() for a in atom.args)
            entries.append(f"{pred}({args_s})")
        lines.append(f"{t}: " + ", ".join(entries))

    lines = condense_stream_lines(lines, min_run=6)

    print("\n===== LARS OUTPUT =====")
    for line in lines:
        print(line)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    assert len(lines) > 0