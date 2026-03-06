import os
import argparse

# Import the reusable function you wrote.
# If you placed it in another file/module, adjust this import accordingly.
from tests.utils.runners import test_mtl_dataset_to_lars


def main():
    parser = argparse.ArgumentParser(
        description="Run the DatalogMTL → LARS translation for the vaccination example."
    )
    parser.add_argument(
        "--in",
        dest="input_path",
        default="tests/data/datalogmtl/vaccination_data.txt",
        help="Path to the DatalogMTL dataset file (default: tests/data/datalogmtl/vaccination_data.txt)",
    )
    parser.add_argument(
        "--dir",
        dest="output_dir",
        default="tests/output/datalogmtl_to_lars",
        help="Output directory for the generated LARS file (default: tests/output/datalogmtl_to_lars)",
    )
    parser.add_argument(
        "--out",
        dest="output_filename",
        default="vaccination_lars.txt",
        help="Output filename (default: vaccination_lars.txt)",
    )

    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, args.output_filename)

    # Call your reusable translator+writer function
    test_mtl_dataset_to_lars(
        input_path=args.input_path,
        output_path=output_path,
        output_dir=args.output_dir,
    )

    print(f"\n✅ Done. Wrote LARS output to: {output_path}\n")


if __name__ == "__main__":
    main()

# #  Default paths
# python tests/test_files/run_vaccination_example.py

# # Custom paths
# python tests/test_files/run_vaccination_example.py \
#   --in tests/data/datalogmtl/vaccination_data.txt \
#   --dir tests/output/datalogmtl_to_lars \
#   --out vaccination_lars.txt
