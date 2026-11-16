import json

from pw_sdk.testkit.cli import main
from pw_sdk.testkit.scaffold import scaffold

SPEC = "tests.test_adapter:DemoAdapter"


def test_check_update_then_pass(tmp_path, capsys):
    case = tmp_path / "one.json"
    case.write_text(json.dumps([{"id": "1", "phone": "+919812345678"}, {"id": "2", "test": True}]))
    assert main(["check", str(tmp_path), "--adapter", SPEC]) == 1
    assert main(["check", str(tmp_path), "--adapter", SPEC, "--update"]) == 0
    assert main(["check", str(tmp_path), "--adapter", SPEC]) == 0
    expected = json.loads((tmp_path / "one.expected.json").read_text())
    expected["items"][0]["value"]["ref"]["reference_id"] = "changed"
    (tmp_path / "one.expected.json").write_text(json.dumps(expected))
    assert main(["check", str(tmp_path), "--adapter", SPEC]) == 1
    assert "changed" in capsys.readouterr().out


def test_schema_command(tmp_path):
    assert main(["schema", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "customer_record.v1.json").exists()


def test_scaffold_new_client(tmp_path):
    target = scaffold("acme_travel", tmp_path)
    assert target.name == "acme-travel-adapter"
    adapter = (target / "acme_travel" / "adapter.py").read_text()
    assert "AcmeTravelCartAdapter" in adapter and "{{" not in adapter
    assert (target / "pyproject.toml").exists()
