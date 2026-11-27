import os

import pytest

import wallet


@pytest.fixture
def db():
    d = wallet.connect()
    d.executemany("INSERT INTO accounts VALUES (?, ?)", [("alice", 100), ("bob", 20)])
    return d


def test_transfer_moves_money(db):
    wallet.transfer(db, "alice", "bob", 30)
    assert wallet.balance(db, "alice") == 70
    assert wallet.balance(db, "bob") == 50


def test_transfer_writes_audit_line(db):
    wallet.transfer(db, "alice", "bob", 5)
    assert db.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 1


def test_insufficient_funds(db):
    with pytest.raises(ValueError):
        wallet.transfer(db, "bob", "alice", 999)


def test_non_positive_amount(db):
    with pytest.raises(ValueError):
        wallet.transfer(db, "alice", "bob", 0)


def test_statement_dotdot_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(wallet, "STATEMENTS_ROOT", str(tmp_path))
    (tmp_path / "alice").mkdir()
    with pytest.raises(PermissionError):
        wallet.read_statement("alice", "../bob/2026-10.txt")


def test_statement_read(tmp_path, monkeypatch):
    monkeypatch.setattr(wallet, "STATEMENTS_ROOT", str(tmp_path))
    (tmp_path / "alice").mkdir()
    (tmp_path / "alice" / "2026-10.txt").write_text("ok")
    assert wallet.read_statement("alice", "2026-10.txt") == "ok"
