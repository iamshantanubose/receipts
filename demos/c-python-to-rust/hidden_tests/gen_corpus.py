#!/usr/bin/env python3
"""Seeded adversarial corpus for scenario C (synthetic; valid UTF-8 only). Usage: gen_corpus.py N SEED > out.tsv"""
import random
import sys

n, seed = int(sys.argv[1]), int(sys.argv[2])
r = random.Random(seed)
SP = [" ", "\t"[:0], " ", " ", "　", "\x1c", "\x1f", "\x0b", "\x85", " ", "\r", ""]
DIG = ["0123456789", "٠١٢٣٤٥٦٧٨٩", "０１２３４５６７８９", "०१२३४५६७८९", "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"]
WORDS = ["hi", "hello", "नमस्ते", "café", "日本語", "🚀🚀", "ééé", "x" * 20, "y" * 21, "", "  ", "a b", "\x1cz\x1c"]


def digits(k):
    d = r.choice(DIG) if r.random() < 0.2 else DIG[0]
    return "".join(r.choice(d) for _ in range(k))


def number(kind):
    k = r.choice([1, 1, 2, 3, 4, 5, 20, 25])
    s = digits(k)
    roll = r.random()
    if roll < 0.15 and len(s) > 1:
        i = r.randrange(0, len(s) + 1)
        s = s[:i] + r.choice(["_", "__"]) + s[i:]
    if kind == "float":
        if r.random() < 0.5:
            s = r.choice(["", digits(1), s]) + "." + r.choice(["", digits(1), digits(2), "_5", "5_"])
        if r.random() < 0.2:
            s += r.choice(["e", "E", "e-", "e+", "e_"]) + digits(r.choice([1, 2]))
        if r.random() < 0.05:
            s = r.choice(["nan", "NaN", "inf", "-inf", "Infinity", "n_an", "infinit"])
    if r.random() < 0.2:
        s = r.choice(["+", "-", "--", "+-"]) + s
    if r.random() < 0.2:
        s = r.choice(SP) + s + r.choice(SP)
    if r.random() < 0.03:
        s = r.choice(["abc", "1.5", "1e3", "0x10", "١.٥", "½", "²"])
    return s


out = []
for _ in range(n):
    p = r.choice(WORDS)
    if r.random() < 0.2:
        p = r.choice(SP) + p + r.choice(SP)
    temp = "" if r.random() < 0.1 else number("float")
    fields = [p, number("int"), temp]
    if r.random() < 0.02:
        fields = fields[:2]
    line = "\t".join(fields)
    out.append(line.replace("\n", " "))
sys.stdout.write("\n".join(out) + "\n")
