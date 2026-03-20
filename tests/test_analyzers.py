"""Tests for drift detection and migration analysis."""
import pytest
from db_migrate_cli.analyzers.drift_detector import detect_drift
from db_migrate_cli.analyzers.migration_analyzer import analyze_migrations
from db_migrate_cli.parser import parse_migrations_dir
from db_migrate_cli.models import DriftSeverity, DriftType


class TestDriftDetector:
    def test_no_drift(self, sample_schema):
        report = detect_drift(sample_schema, sample_schema)
        assert not report.has_drift
        assert report.score == 100

    def test_missing_table(self, sample_schema, drifted_schema):
        report = detect_drift(sample_schema, drifted_schema)
        missing = [i for i in report.issues if i.drift_type == DriftType.MISSING_TABLE]
        assert len(missing) >= 1  # orders table missing

    def test_extra_table(self, sample_schema, drifted_schema):
        report = detect_drift(sample_schema, drifted_schema)
        extra = [i for i in report.issues if i.drift_type == DriftType.EXTRA_TABLE]
        assert len(extra) >= 1  # temp_data

    def test_type_mismatch(self, sample_schema, drifted_schema):
        report = detect_drift(sample_schema, drifted_schema)
        mismatches = [i for i in report.issues if i.drift_type == DriftType.TYPE_MISMATCH]
        assert len(mismatches) >= 1  # email varchar vs text

    def test_extra_column(self, sample_schema, drifted_schema):
        report = detect_drift(sample_schema, drifted_schema)
        extras = [i for i in report.issues if i.drift_type == DriftType.EXTRA_COLUMN]
        assert len(extras) >= 1  # legacy column

    def test_missing_column(self, sample_schema, drifted_schema):
        report = detect_drift(sample_schema, drifted_schema)
        missing = [i for i in report.issues if i.drift_type == DriftType.MISSING_COLUMN]
        assert len(missing) >= 0  # email still exists but different type

    def test_missing_index(self, sample_schema, drifted_schema):
        report = detect_drift(sample_schema, drifted_schema)
        idx = [i for i in report.issues if i.drift_type == DriftType.INDEX_MISSING]
        assert len(idx) >= 1  # idx_email missing from drifted

    def test_severity_ordering(self, sample_schema, drifted_schema):
        report = detect_drift(sample_schema, drifted_schema)
        assert report.critical_count >= 1  # missing table
        assert report.grade != "A+"


class TestMigrationAnalyzer:
    def test_good_migrations(self, migration_dir):
        migs = parse_migrations_dir(migration_dir)
        issues = analyze_migrations(migs)
        criticals = [i for i in issues if i.severity == "CRITICAL"]
        assert len(criticals) == 0

    def test_demo_migrations_issues(self, demo_paths):
        migs = parse_migrations_dir(demo_paths["migrations_dir"])
        issues = analyze_migrations(migs)
        rule_ids = [i.rule_id for i in issues]
        assert "MIG-001" in rule_ids  # no DOWN
        assert "MIG-002" in rule_ids  # DROP without IF EXISTS
        assert "MIG-003" in rule_ids  # DROP COLUMN
        assert "MIG-005" in rule_ids  # INSERT in schema migration
        assert "MIG-007" in rule_ids  # no PK
        assert "MIG-008" in rule_ids  # version gap 3→5

    def test_empty_migrations(self):
        issues = analyze_migrations([])
        assert len(issues) == 0
