import pytest
from conflux.utils import data_comparison


def test_identical_sets():
    # two sets with the same elements in different order should compare equal
    set1 = {(1, "p(a)"), (2, "q(b)")}
    set2 = {(2, "q(b)"), (1, "p(a)")}
    assert data_comparison.compare_data_semantics_from_sets(set1, set2)


def test_different_sets(capsys):
    # when the sets differ the comparison returns False and prints diffs
    set1 = {(1, "p(a)")}
    set2 = {(1, "p(a)"), (2, "r(c)")}
    assert not data_comparison.compare_data_semantics_from_sets(set1, set2)
    output = capsys.readouterr().out
    assert "Facts only in DatalogMTL dataset" in output
    assert "Facts only in LARS dataset" in output


def test_parse_and_compare_files(tmp_path):
    # sanity check using temporary files rather than repo fixtures
    dmtl_content = "p(a)@[1,2]\n"
    lars_content = "1-2: p(a)\n"
    dmtl_file = tmp_path / "a.txt"
    lars_file = tmp_path / "b.txt"
    dmtl_file.write_text(dmtl_content, encoding="utf-8")
    lars_file.write_text(lars_content, encoding="utf-8")

    assert data_comparison.compare_data_semantics(str(dmtl_file), str(lars_file))
