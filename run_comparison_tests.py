"""Convenience script for running the comparison unit tests.

By default it executes the
`tests/utils/test_data_comparison.py` file and can filter down to the
vaccination example due to the -k expression.  This avoids having to type
pytest command line options manually.
"""

import sys
import pytest


def main():
    # run only the vaccination parse/compare test by default
    args = ["-q", "tests/utils/test_data_comparison.py", "-k", "test_parse_and_compare_vaccination_example"]
    exit_code = pytest.main(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
