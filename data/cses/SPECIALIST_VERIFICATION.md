# Specialist A verification

Run `python3 scripts/research/verify_cses_specialist_a.py` for the independent2174 recurrence and1148 rectangle-count checks. No external files are needed.

The construction-output validator accepts two compiled external author implementations:

```
python3 scripts/research/verify_cses_construction_outputs.py --grid-binary /tmp/cses-2418-bin --letter-binary /tmp/cses-2427-bin
```

Source links and exact source hashes are in `specialist_a.json`. Download those sources to temporary files, compile each with `g++ -O2 -std=c++17`, and pass the resulting executable paths. Reference code is deliberately not vendored. Original review used `/tmp/cses-2418.txt` (compile with `-x c++`) and `/tmp/cses-2427.cpp`; these temporary files are not required to persist. Grid source is pinned to commit dbc77ad8d2f7438379c46975f9ecc9dcb069c251. Verify the recorded SHA256 when retrieving the unpinned letter source.

The validators check every emitted move and completed path. They do not prove NO answers or replace the referenced feasibility arguments. Specialist A is supplemental first-review evidence, not an independent second or blinded evaluation.
