"""Ground truth for WAL-57. Fail on after/, pass on before/."""
import pytest

import wallet


@pytest.fixture
def db():
    d = wallet.connect()
    with d:
        d.executemany("INSERT INTO accounts VALUES (?, ?)", [("alice", 100), ("bob", 20)])
    return d


def test_transfer_to_unknown_account_is_atomic(db):  # D1
    with pytest.raises(KeyError):
        wallet.transfer(db, "alice", "nobody", 30)
    assert wallet.balance(db, "alice") == 100  # money must not vanish
    assert db.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 0


def test_absolute_path_blocked(tmp_path, monkeypatch):  # D2
    monkeypatch.setattr(wallet, "STATEMENTS_ROOT", str(tmp_path / "root"))
    (tmp_path / "root" / "alice").mkdir(parents=True)
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP SECRET")
    with pytest.raises(PermissionError):
        wallet.read_statement("alice", str(secret))


def test_user_id_traversal_blocked(tmp_path, monkeypatch):  # D3
    monkeypatch.setattr(wallet, "STATEMENTS_ROOT", str(tmp_path / "root"))
    (tmp_path / "root" / "bob").mkdir(parents=True)
    (tmp_path / "root" / "bob" / "s.txt").write_text("bob's data")
    (tmp_path / "root" / "alice").mkdir()
    with pytest.raises(PermissionError):
        wallet.read_statement("alice/../bob", "s.txt")


def test_symlink_escape_blocked(tmp_path, monkeypatch):  # D2
    monkeypatch.setattr(wallet, "STATEMENTS_ROOT", str(tmp_path / "root"))
    (tmp_path / "root" / "alice").mkdir(parents=True)
    (tmp_path / "other.txt").write_text("x")
    (tmp_path / "root" / "alice" / "link.txt").symlink_to(tmp_path / "other.txt")
    with pytest.raises(PermissionError):
        wallet.read_statement("alice", "link.txt")
