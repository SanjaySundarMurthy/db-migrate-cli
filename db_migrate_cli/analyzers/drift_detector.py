"""Schema drift detector — compare expected vs actual schema."""
from __future__ import annotations
from typing import List

from db_migrate_cli.models import (
    Column, DriftIssue, DriftReport, DriftSeverity, DriftType,
    ObjectType, SchemaSnapshot, Table,
)


def detect_drift(expected: SchemaSnapshot, actual: SchemaSnapshot) -> DriftReport:
    """Compare two schema snapshots and return drift issues."""
    issues: List[DriftIssue] = []

    expected_names = set(t.name for t in expected.tables)
    actual_names = set(t.name for t in actual.tables)

    # Missing tables (in expected but not actual)
    for name in sorted(expected_names - actual_names):
        issues.append(DriftIssue(
            drift_type=DriftType.MISSING_TABLE,
            severity=DriftSeverity.CRITICAL,
            object_type=ObjectType.TABLE,
            object_name=name,
            message=f"Table '{name}' exists in schema but missing in database",
            expected="exists",
            actual="missing",
            suggestion=f"Run pending migrations or CREATE TABLE {name}",
        ))

    # Extra tables (in actual but not expected)
    for name in sorted(actual_names - expected_names):
        issues.append(DriftIssue(
            drift_type=DriftType.EXTRA_TABLE,
            severity=DriftSeverity.HIGH,
            object_type=ObjectType.TABLE,
            object_name=name,
            message=f"Table '{name}' exists in database but not in schema",
            expected="missing",
            actual="exists",
            suggestion=f"Add migration for table '{name}' or drop it",
        ))

    # Compare shared tables
    for name in sorted(expected_names & actual_names):
        exp_table = expected.get_table(name)
        act_table = actual.get_table(name)
        if exp_table and act_table:
            issues.extend(_compare_tables(exp_table, act_table))

    return DriftReport(expected_schema=expected, actual_schema=actual, issues=issues)


def _compare_tables(expected: Table, actual: Table) -> List[DriftIssue]:
    """Compare columns and indexes of two tables."""
    issues: List[DriftIssue] = []
    tname = expected.name

    exp_cols = {c.name: c for c in expected.columns}
    act_cols = {c.name: c for c in actual.columns}

    # Missing columns
    for col_name in sorted(set(exp_cols) - set(act_cols)):
        col = exp_cols[col_name]
        issues.append(DriftIssue(
            drift_type=DriftType.MISSING_COLUMN,
            severity=DriftSeverity.HIGH,
            object_type=ObjectType.COLUMN,
            object_name=f"{tname}.{col_name}",
            message=f"Column '{col_name}' missing from table '{tname}'",
            expected=f"{col.data_type}",
            actual="missing",
            suggestion=f"ALTER TABLE {tname} ADD COLUMN {col_name} {col.data_type}",
        ))

    # Extra columns
    for col_name in sorted(set(act_cols) - set(exp_cols)):
        issues.append(DriftIssue(
            drift_type=DriftType.EXTRA_COLUMN,
            severity=DriftSeverity.MEDIUM,
            object_type=ObjectType.COLUMN,
            object_name=f"{tname}.{col_name}",
            message=f"Extra column '{col_name}' in table '{tname}' not in schema",
            expected="missing",
            actual=f"{act_cols[col_name].data_type}",
            suggestion=f"Add column to schema or ALTER TABLE {tname} DROP COLUMN {col_name}",
        ))

    # Compare shared columns
    for col_name in sorted(set(exp_cols) & set(act_cols)):
        exp_col = exp_cols[col_name]
        act_col = act_cols[col_name]

        if exp_col.data_type.lower() != act_col.data_type.lower():
            issues.append(DriftIssue(
                drift_type=DriftType.TYPE_MISMATCH,
                severity=DriftSeverity.HIGH,
                object_type=ObjectType.COLUMN,
                object_name=f"{tname}.{col_name}",
                message=f"Type mismatch for '{tname}.{col_name}'",
                expected=exp_col.data_type,
                actual=act_col.data_type,
                suggestion=f"ALTER TABLE {tname} ALTER COLUMN {col_name} TYPE {exp_col.data_type}",
            ))

        if exp_col.nullable != act_col.nullable:
            issues.append(DriftIssue(
                drift_type=DriftType.NULLABLE_DIFF,
                severity=DriftSeverity.MEDIUM,
                object_type=ObjectType.COLUMN,
                object_name=f"{tname}.{col_name}",
                message=f"Nullable mismatch for '{tname}.{col_name}'",
                expected=f"nullable={exp_col.nullable}",
                actual=f"nullable={act_col.nullable}",
                suggestion="Update column nullability constraint",
            ))

        exp_def = str(exp_col.default or "").lower()
        act_def = str(act_col.default or "").lower()
        if exp_def != act_def:
            issues.append(DriftIssue(
                drift_type=DriftType.DEFAULT_DIFF,
                severity=DriftSeverity.LOW,
                object_type=ObjectType.COLUMN,
                object_name=f"{tname}.{col_name}",
                message=f"Default value mismatch for '{tname}.{col_name}'",
                expected=str(exp_col.default),
                actual=str(act_col.default),
                suggestion="Update column default value",
            ))

    # Compare indexes
    exp_idx = {i.name: i for i in expected.indexes}
    act_idx = {i.name: i for i in actual.indexes}

    for idx_name in sorted(set(exp_idx) - set(act_idx)):
        issues.append(DriftIssue(
            drift_type=DriftType.INDEX_MISSING,
            severity=DriftSeverity.MEDIUM,
            object_type=ObjectType.INDEX,
            object_name=f"{tname}.{idx_name}",
            message=f"Index '{idx_name}' missing from table '{tname}'",
            expected="exists",
            actual="missing",
            suggestion=f"CREATE INDEX {idx_name} ON {tname}(...)",
        ))

    for idx_name in sorted(set(act_idx) - set(exp_idx)):
        issues.append(DriftIssue(
            drift_type=DriftType.INDEX_EXTRA,
            severity=DriftSeverity.LOW,
            object_type=ObjectType.INDEX,
            object_name=f"{tname}.{idx_name}",
            message=f"Extra index '{idx_name}' on table '{tname}'",
            expected="missing",
            actual="exists",
            suggestion="Add index to schema or drop it",
        ))

    return issues
