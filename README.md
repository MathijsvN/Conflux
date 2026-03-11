# Conflux

Conflux is a translation toolkit for Stream Reasoning (SR) frameworks. It provides semantics‑preserving mappings between DatalogMTL, LARS (and later RTEC, RSP-QL), enabling exchange and reuse of temporal rules and datasets across heterogeneous SR systems.

## Status

- Initial focus: DatalogMTL ↔ LARS
- Language-agnostic IR + plugin registry for translators
- CLI: `conflux translate --from DatalogMTL --to LARS ...`

## Quick start

```bash
pipx install -e .
conflux --help
```

## Current Functionality

### Translators

- **DatalogMTL → LARS** (stable)
  - Dataset conversion: temporal facts with intervals `P(args)@[a,b]` → time-indexed streams
  - Program/rule translation (preliminary)
  - Preserves semantic equivalence across both datasets and temporal rule structures

### Utilities

- **Data Comparison** (`conflux/utils/data_comparison.py`)
  - Parse DatalogMTL and LARS data files
  - Semantic equivalence checking between output datasets
  - Detailed diff reporting when datasets diverge (for debugging translation issues)

### Testing

- Unit tests for dataset comparison (`tests/comparison/test_data_diff.py`)
- Vaccination example tests (`tests/utils/test_data_comparison.py`)
- Convenience runner: `python run_comparison_tests.py`

## Known Limitations & TODOs

- [ ] **LARS → DatalogMTL translator** not yet implemented (`conflux/translators/datalogmtl_lars/lars_to_mtl.py`)
- [ ] **Rule translation** currently basic; needs expansion for complex temporal formulas
- [ ] **RTEC and RSP-QL support** planned but not yet started
- [ ] **More comprehensive test coverage** for edge cases in time-windowing and temporal operators
- [ ] **Performance optimization** for large datasets during expansion

## File Structure

```
conflux/
├── core/          # IR, AST, registry, semantics
├── io/            # Parsers and emitters (DatalogMTL, LARS)
├── translators/   # Translation modules
│   └── datalogmtl_lars/
│       ├── mtl_to_lars.py (✓ implemented)
│       ├── lars_to_mtl.py (TODO)
│       └── ...
└── utils/         # Helpers (logging, diagnostics, data comparison)

tests/
├── comparison/    # Custom comparison and validation tests
├── data/          # Shared test datasets
├── output/        # Generated translation outputs
├── programs/      # Test rule files
└── utils/         # Test utilities and runners
```
