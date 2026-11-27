# Ticket API-301: Port the request normaliser from Python to Rust

`legacy_python/normalize.py` is the production reference. It reads one request per line on stdin,
as tab-separated `prompt<TAB>max_tokens<TAB>temperature`, and writes one result per line:

- `OK<TAB>chars=<n><TAB>max_tokens=<n><TAB>temperature=<t>`, or
- `ERR<TAB><code>`

Port it to Rust (`rust_port/`). **The output must be identical for every input.** Clients depend on
the exact behaviour, including the error codes.

The existing conventional tests (`tests_conventional.txt`, expected outputs in `tests_conventional.expected`) must pass on both.
