"""Reference request normalizer (production behaviour)."""
import sys

MAX_TOKENS_LIMIT = 4096
MAX_PROMPT_CHARS = 20
# int() rejects strings with more than 4300 digits on CPython 3.11+ (and 3.9.14+/3.10.7+) by default.
# The limit is pinned here so the reference behaves the same on every interpreter version.
INT_MAX_STR_DIGITS = 4300


def parse_int(raw):
    if sum(c.isdecimal() for c in raw) > INT_MAX_STR_DIGITS:
        raise ValueError("integer string too long")
    return int(raw)


def normalize(line):
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 3:
        return "ERR\tbad_shape"
    prompt, max_tokens_raw, temp_raw = parts
    prompt = prompt.strip()
    if not prompt:
        return "ERR\tempty_prompt"
    if len(prompt) > MAX_PROMPT_CHARS:
        return "ERR\tprompt_too_long"
    try:
        max_tokens = parse_int(max_tokens_raw)
    except ValueError:
        return "ERR\tbad_max_tokens"
    if max_tokens < 1 or max_tokens > MAX_TOKENS_LIMIT:
        return "ERR\tmax_tokens_range"
    if temp_raw == "":
        temperature = 1.0
    else:
        try:
            temperature = float(temp_raw)
        except ValueError:
            return "ERR\tbad_temperature"
    if not 0.0 <= temperature <= 1.0:
        return "ERR\ttemperature_range"
    temperature = round(temperature, 1)
    return f"OK\tchars={len(prompt)}\tmax_tokens={max_tokens}\ttemperature={temperature:.1f}"


if __name__ == "__main__":
    for raw in sys.stdin:
        print(normalize(raw))
