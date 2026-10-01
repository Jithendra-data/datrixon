# Source contracts and schema drift

`governance/contracts/sources.json` contains versioned definitions for all 14 synthetic CSV sources. It fixes columns, type, nullable rules, composite grain, owner, sensitivity and relevant allowed categories. The pipeline records the source contract version in the generation manifest; reuse checks that version and still validates every source.

`inspect_frame` emits issue kind, detail and INFO/WARNING/BREAKING-compatible severity. The implemented strict policy treats added/removed/renamed columns, incompatible types, required nulls, invalid categories, duplicate keys and version mismatch as BREAKING. Optional configured null-rate thresholds produce WARNING. There is no statistical drift claim or inferred schema approval.

Contracts were created from the reviewed V1 generator and source columns, then checked into version control. They are not inferred anew from each incoming batch. Runtime validation compares incoming data against that fixed contract, preventing a corrupt input from redefining its own schema.

```bash
python -m governance.validate --source data/raw
python -m unittest discover -s tests -p 'test_governance.py' -v
```

Version changes require coordinated source/consumer review, compatibility tests and definition history. This public synthetic runner is not a real producer handshake, schema registry service or live ERP connector. Future adapters must transmit their independently controlled version in a signed/authenticated batch manifest.
