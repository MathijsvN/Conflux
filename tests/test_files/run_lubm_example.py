import os
import argparse
from pathlib import Path

# Dataset translator (your reusable function)
from tests.utils.runners import test_mtl_dataset_to_lars

# Program parsing + emitting
from conflux.io.parse_datalogmtl import parse_datalogmtl_program
from conflux.translators.datalogmtl_lars.mtl_to_lars import MtlToLars
from conflux.io.emit_lars import emit_lars_program

from conflux.core.ast import ProgramIR


def main():
    parser = argparse.ArgumentParser(
        description="Run the DatalogMTL → LARS translation for the LUBM example (data + program)."
    )

    # DATASET INPUT
    parser.add_argument(
        "--data",
        dest="dataset_path",
        default="tests/data/datalogmtl/lubm_10^2.txt",
        help="Path to the LUBM DatalogMTL dataset file.",
    )

    # PROGRAM INPUT
    parser.add_argument(
        "--program",
        dest="program_path",
        default="tests/programs/datalogmtl/lubm_program.txt",
        help="Path to the LUBM DatalogMTL program file (set of rules).",
    )

    # OUTPUT DIRECTORY
    parser.add_argument(
        "--dir",
        dest="output_dir",
        default="tests/output/datalogmtl_to_lars",
        help="Directory for LARS output files.",
    )

    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ===================================================================
    # A. TRANSLATE THE DATASET
    # ===================================================================
    data_out_path = output_dir / "lubm_lars_data.txt"

    print("\n=== Translating DATASET (LUBM) ===\n")
    test_mtl_dataset_to_lars(
        input_path=args.dataset_path,
        output_path=str(data_out_path),
        output_dir=str(output_dir),
    )
    print(f"✓ Dataset translation written to: {data_out_path}")

    # ===================================================================
    # B. TRANSLATE THE PROGRAM (RULE SET)
    # ===================================================================
    print("\n=== Translating PROGRAM (LUBM) ===\n")

    # 1) Parse program (DatalogMTL → IR)
    program_rules = parse_datalogmtl_program(args.program_path)

    # 2) Build a ProgramIR (rules only)
    program_ir = ProgramIR()
    program_ir.rules = program_rules
    program_ir.extensional_facts = {}

    # 3) Translate program IR → LARS IR
    translator = MtlToLars()
    translated_program = translator.translate(program_ir)

    # 4) Emit LASER syntax
    lars_program_text = emit_lars_program(translated_program)
    program_out_path = output_dir / "lubm_lars_program.txt"

    with open(program_out_path, "w", encoding="utf-8") as f:
        f.write(lars_program_text + "\n")

    print(lars_program_text)
    print(f"\n✓ Program translation written to: {program_out_path}\n")

    print("\n=== DONE! ===\n")


if __name__ == "__main__":
    main()