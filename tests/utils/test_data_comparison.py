import tempfile
import os
from conflux.utils import data_comparison


def test_parse_and_compare_vaccination_example(tmp_path):
    # use existing files from the repo
    dmtl_path = os.path.join("tests", "comparison", "data", "datalogmtl", "vaccination_dmtl_data.txt")
    lars_path = os.path.join("tests", "comparison", "data", "lars", "vaccination_lars_data.txt")

    # parse individually and compare sets
    dmtl_facts = data_comparison.parse_datalogmtl_data(dmtl_path)
    lars_facts = data_comparison.parse_lars_data(lars_path)
    assert data_comparison.compare_data_semantics_from_sets(dmtl_facts, lars_facts)
    assert data_comparison.compare_data_semantics(dmtl_path, lars_path)

    # provide explicit confirmation for humans running the test
    print("Vaccination example datasets are semantically equivalent.")


def test_diff_outputs():
    # create two simple in-memory sets with a difference
    set1 = {(1, "p(a)"), (2, "q(b)")}
    set2 = {(1, "p(a)"), (3, "r(c)")}
    only1, only2 = data_comparison.diff_fact_sets(set1, set2)
    assert only1 == {(2, "q(b)")}
    assert only2 == {(3, "r(c)")}

    # ensure formatting doesn't raise
    formatted = data_comparison.format_fact_set(only1)
    assert "2: q(b)" in formatted

    # comparison function should return False and print differences
    assert not data_comparison.compare_data_semantics_from_sets(set1, set2)
