import os
import sqlite3

STATEMENTS_ROOT = os.path.abspath("statements")


def connect(path=":memory:"):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, balance INTEGER NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS audit (line TEXT NOT NULL)")
    return db


def balance(db, account_id):
    row = db.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        raise KeyError(account_id)
    return row[0]


def transfer(db, src, dst, amount):
    if amount <= 0:
        raise ValueError("amount must be positive")
    with db:  # one transaction: commit on success, rollback on any exception
        if balance(db, src) < amount:
            raise ValueError("insufficient funds")
        db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, src))
        if balance(db, dst) is None:
            raise KeyError(dst)
        db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, dst))
        db.execute("INSERT INTO audit (line) VALUES (?)", (f"{src}->{dst}:{amount}",))


def read_statement(user_id, name):
    if not user_id or user_id in (".", "..") or os.sep in user_id or (os.altsep and os.altsep in user_id):
        raise PermissionError("bad user id")  # user_id must be a single plain folder name
    root = os.path.realpath(STATEMENTS_ROOT)
    base = os.path.realpath(os.path.join(root, user_id))
    target = os.path.realpath(os.path.join(base, name))
    if os.path.commonpath([base, target]) != base:
        raise PermissionError("outside statement folder")
    with open(target, encoding="utf-8") as f:
        return f.read()
