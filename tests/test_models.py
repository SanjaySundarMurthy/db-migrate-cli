"""Tests for db_migrate_cli.models."""
from db_migrate_cli.models import *


class TestModels:
    def test_migration_display_name(self, sample_migration):
        assert sample_migration.display_name == "001_create_users"

    def test_schema_table_names(self, sample_schema):
        assert sample_schema.table_names == ["orders", "users"]

    def test_schema_get_table(self, sample_schema):
        assert sample_schema.get_table("users") is not None
        assert sample_schema.get_table("nonexistent") is None

    def test_drift_report_no_issues(self, sample_schema):
        report = DriftReport(expected_schema=sample_schema, actual_schema=sample_schema)
        assert report.score == 100
        assert report.grade == "A+"
        assert not report.has_drift

    def test_drift_report_with_issues(self, sample_schema):
        issues = [DriftIssue(DriftType.MISSING_TABLE, DriftSeverity.CRITICAL,
                             ObjectType.TABLE, "t", "msg")] * 3
        report = DriftReport(expected_schema=sample_schema, actual_schema=sample_schema, issues=issues)
        assert report.has_drift
        assert report.critical_count == 3
        assert report.score < 100

    def test_migration_plan(self):
        plan = MigrationPlan(
            pending=[Migration("1", "a", "", "")],
            applied=[Migration("2", "b", "", "", status=MigrationStatus.APPLIED)],
        )
        assert plan.total == 2

    def test_enum_values(self):
        assert MigrationStatus.PENDING.value == "pending"
        assert DriftSeverity.CRITICAL.value == "CRITICAL"
        assert DriftType.MISSING_TABLE.value == "missing_table"
