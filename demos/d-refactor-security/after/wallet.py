import os
import sqlite3

STATEMENTS_ROOT = os.path.abspath("statements")


def connect(path: str = ":memory:") -> sqlite3.Connection:
    db = sqlite3.connect(path, isolation_level=None)  # autocommit: simpler, no stale transactions
    db.execute("CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, balance INTEGER NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS audit (line TEXT NOT NULL)")
    return db


def balance(db: sqlite3.Connection, account_id: str) -> int:
    row = db.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        raise KeyError(account_id)
    return row[0]


def _move(db: sqlite3.Connection, account_id: str, delta: int) -> None:
    balance(db, account_id)  # raises KeyError for unknown accounts
    db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (delta, account_id))


def transfer(db: sqlite3.Connection, src: str, dst: str, amount: int) -> None:
    if amount <= 0:
        raise ValueError("amount must be positive")
    if balance(db, src) < amount:
        raise ValueError("insufficient funds")
    _move(db, src, -amount)
    _move(db, dst, +amount)
    db.execute("INSERT INTO audit (line) VALUES (?)", (f"{src}->{dst}:{amount}",))


def read_statement(user_id: str, name: str) -> str:
    path = os.path.join(STATEMENTS_ROOT, user_id, name)
    if ".." in name.split("/"):
        raise PermissionError("outside statement folder")
    with open(path, encoding="utf-8") as f:
        return f.read()
