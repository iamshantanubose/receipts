"""The skill folder must satisfy the Agent Skills spec and stay portable across hosts."""
import os
import re

from conftest import SKILL

SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def frontmatter():
    text = open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md must start with YAML frontmatter"
    top = {}
    for line in m.group(1).splitlines():
        if line and not line.startswith(" "):
            k, _, v = line.partition(":")
            top[k.strip()] = v.strip()
    return top, text


def test_only_portable_fields():
    top, _ = frontmatter()
    assert set(top) <= SPEC_FIELDS, f"non-portable fields: {set(top) - SPEC_FIELDS}"


def test_name_rules():
    top, _ = frontmatter()
    name = top["name"]
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) and len(name) <= 64
    assert name == os.path.basename(SKILL)


def test_description_length():
    top, _ = frontmatter()
    assert 1 <= len(top["description"]) <= 1024


def test_skill_md_is_compact():
    _, text = frontmatter()
    assert len(text.splitlines()) < 500


def test_every_referenced_file_exists():
    _, text = frontmatter()
    for rel in re.findall(r"`((?:references|scripts|templates)/[\w./-]+)`", text):
        assert os.path.exists(os.path.join(SKILL, rel)), rel
    for ref in os.listdir(os.path.join(SKILL, "references")):
        body = open(os.path.join(SKILL, "references", ref), encoding="utf-8").read()
        for rel in re.findall(r"`((?:scripts|templates)/[\w.-]+\.\w+)", body):
            assert os.path.exists(os.path.join(SKILL, rel)), f"{ref} -> {rel}"


def test_versions_agree():
    import json
    root = os.path.dirname(os.path.dirname(SKILL))
    plugin = json.load(open(os.path.join(root, ".claude-plugin", "plugin.json"), encoding="utf-8"))["version"]
    market = json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json"), encoding="utf-8"))
    _, text = frontmatter()
    skill = re.search(r'^\s+version:\s*"([^"]+)"', text, re.M).group(1)
    changelog = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    latest = re.search(r"^## (\S+)", changelog, re.M).group(1)
    assert plugin == skill == latest == market["plugins"][0]["version"], (plugin, skill, latest)
    assert market["name"] == "receipts"
