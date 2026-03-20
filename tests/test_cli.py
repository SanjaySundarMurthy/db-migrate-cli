"""Tests for db_migrate_cli.cli."""
import os
import pytest
from click.testing import CliRunner
from db_migrate_cli.cli import main
from db_migrate_cli.demo import create_demo_project


@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def demo_files(tmp_path):
    return create_demo_project(str(tmp_path / "demo"))


class TestCLI:
    def test_version(self, runner):
        r = runner.invoke(main, ["--version"])
        assert r.exit_code == 0
        assert "1.0.0" in r.output

    def test_help(self, runner):
        r = runner.invoke(main, ["--help"])
        assert r.exit_code == 0
        assert "db-migrate-cli" in r.output

    def test_status(self, runner, demo_files):
        r = runner.invoke(main, ["status", demo_files["migrations_dir"]])
        assert r.exit_code == 0
        assert "Migration Status" in r.output

    def test_status_json(self, runner, demo_files, tmp_path):
        out = str(tmp_path / "status.json")
        r = runner.invoke(main, ["status", demo_files["migrations_dir"], "-f", "json", "-o", out])
        assert r.exit_code == 0
        assert os.path.exists(out)

    def test_drift(self, runner, demo_files):
        r = runner.invoke(main, ["drift", demo_files["expected"], demo_files["actual"]])
        assert r.exit_code == 0
        assert "Drift" in r.output

    def test_drift_verbose(self, runner, demo_files):
        r = runner.invoke(main, ["drift", demo_files["expected"], demo_files["actual"], "-v"])
        assert r.exit_code == 0

    def test_drift_fail_on(self, runner, demo_files):
        r = runner.invoke(main, ["drift", demo_files["expected"], demo_files["actual"], "--fail-on", "critical"])
        assert r.exit_code == 1

    def test_drift_json(self, runner, demo_files, tmp_path):
        out = str(tmp_path / "drift.json")
        r = runner.invoke(main, ["drift", demo_files["expected"], demo_files["actual"], "-f", "json", "-o", out])
        assert r.exit_code == 0
        assert os.path.exists(out)

    def test_audit(self, runner, demo_files):
        r = runner.invoke(main, ["audit", demo_files["migrations_dir"]])
        assert r.exit_code == 0
        assert "Migration Quality" in r.output

    def test_audit_verbose(self, runner, demo_files):
        r = runner.invoke(main, ["audit", demo_files["migrations_dir"], "-v"])
        assert r.exit_code == 0

    def test_demo(self, runner, tmp_path):
        r = runner.invoke(main, ["demo", "-d", str(tmp_path / "demo-out")])
        assert r.exit_code == 0
        assert "Demo complete" in r.output

    def test_demo_verbose(self, runner, tmp_path):
        r = runner.invoke(main, ["demo", "-v", "-d", str(tmp_path / "dv")])
        assert r.exit_code == 0

    def test_rules(self, runner):
        r = runner.invoke(main, ["rules"])
        assert r.exit_code == 0
        assert "MIG-001" in r.output
        assert "10 rules" in r.output
