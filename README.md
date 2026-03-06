# Conflux

Conflux is a translation toolkit for Stream Reasoning (SR) frameworks. It provides bidirectional, semantics‑preserving mappings between DatalogMTL, LARS (and later RTEC, RSP-QL), enabling exchange and reuse of temporal rules and datasets across heterogeneous SR systems.

## Status

- Initial focus: DatalogMTL ↔ LARS
- Language-agnostic IR + plugin registry for translators
- CLI: `conflux translate --from DatalogMTL --to LARS ...`

## Quick start

```bash
pipx install -e .
conflux --help
```
