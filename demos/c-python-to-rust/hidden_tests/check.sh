#!/usr/bin/env bash
# Ground truth for scenario C: the flawed port must diverge from legacy; the control must match 100%.
set -u
cd "$(dirname "$0")/.."
H=../../skills/verify-engineering/scripts/diff_harness.py
(cd rust_port && cargo build -q --release) && (cd control_rust && cargo build -q --release) || exit 2
CORPUS="$(mktemp -t scenario-c-corpus.XXXXXX)"
cat hidden_tests/hidden_corpus.tsv > "$CORPUS"
# big_ints.tsv probes the 4,300-digit int() limit. Python builds older than 3.9.14 / 3.10.7
# (for example Apple's /usr/bin/python3 3.9.6) don't have that limit, so the legacy behaviour differs there.
if python3 -c 'import sys; sys.exit(0 if hasattr(sys, "get_int_max_str_digits") else 1)'; then
  cat hidden_tests/big_ints.tsv >> "$CORPUS"
else
  echo "note: this Python has no int() digit limit; skipping big_ints.tsv" >&2
fi
python3 hidden_tests/gen_corpus.py 5000 11 >> "$CORPUS"
python3 "$H" --old "python3 legacy_python/normalize.py" --new "rust_port/target/release/normalize" \
  --inputs "$CORPUS" --max-examples 0 >/dev/null
flawed=$?
python3 "$H" --old "python3 legacy_python/normalize.py" --new "control_rust/target/release/normalize" \
  --inputs "$CORPUS" --max-examples 0 >/dev/null
control=$?
echo "flawed_port_exit=$flawed (expect 1)  control_exit=$control (expect 0)"
[ "$flawed" = 1 ] && [ "$control" = 0 ]
