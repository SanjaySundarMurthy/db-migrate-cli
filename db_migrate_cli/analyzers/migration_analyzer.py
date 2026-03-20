"""Migration quality analyzer — check migration files for best practices."""
from __future__ import annotations
import re
from typing import List

from db_migrate_cli.models import Migration, MigrationStatus


MIGRATION_RULES = [
    {"id": "MIG-001", "severity": "CRITICAL", "desc": "Migration missing DOWN section (no rollback)"},
    {"id": "MIG-002", "severity": "HIGH", "desc": "DROP TABLE without IF EXISTS"},
    {"id": "MIG-003", "severity": "HIGH", "desc": "ALTER TABLE dropping column (destructive)"},
    {"id": "MIG-004", "severity": "MEDIUM", "desc": "No transaction wrapping (missing BEGIN/COMMIT)"},
    {"id": "MIG-005", "severity": "MEDIUM", "desc": "Raw data manipulation in schema migration"},
    {"id": "MIG-006", "severity": "LOW", "desc": "Migration file exceeds 100 lines"},
    {"id": "MIG-007", "severity": "HIGH", "desc": "CREATE TABLE without primary key"},
    {"id": "MIG-008", "severity": "MEDIUM", "desc": "Non-sequential migration version"},
    {"id": "MIG-009", "severity": "LOW", "desc": "Migration name contains special characters"},
    {"id": "MIG-010", "severity": "INFO", "desc": "CREATE INDEX without CONCURRENTLY (may lock table)"},
]


from dataclasses import dataclass


@dataclass
class MigrationIssue:
    rule_id: str
    severity: str
    message: str
    migration: str
    suggestion: str = ""


def analyze_migrations(migrations: List[Migration]) -> List[MigrationIssue]:
    """Analyze migration files for quality issues."""
    issues: List[MigrationIssue] = []

    prev_version = None
    for mig in migrations:
        mig_name = mig.display_name

        # MIG-001: No rollback
        if not mig.down_sql.strip():
            issues.append(MigrationIssue(
                rule_id="MIG-001", severity="CRITICAL",
                message=f"Migration '{mig_name}' has no DOWN section",
                migration=mig_name,
                suggestion="Add -- DOWN section with rollback SQL",
            ))

        # MIG-002: DROP without IF EXISTS
        if re.search(r'DROP\s+TABLE\s+(?!IF\s+EXISTS)', mig.up_sql, re.IGNORECASE):
            issues.append(MigrationIssue(
                rule_id="MIG-002", severity="HIGH",
                message=f"DROP TABLE without IF EXISTS in '{mig_name}'",
                migration=mig_name,
                suggestion="Use DROP TABLE IF EXISTS for safety",
            ))

        # MIG-003: Dropping columns
        if re.search(r'ALTER\s+TABLE\s+\w+\s+DROP\s+COLUMN', mig.up_sql, re.IGNORECASE):
            issues.append(MigrationIssue(
                rule_id="MIG-003", severity="HIGH",
                message=f"Destructive column drop in '{mig_name}'",
                migration=mig_name,
                suggestion="Consider a multi-step migration: deprecate, migrate data, then drop",
            ))

        # MIG-004: No transaction
        up_upper = mig.up_sql.upper()
        if "BEGIN" not in up_upper and "TRANSACTION" not in up_upper:
            issues.append(MigrationIssue(
                rule_id="MIG-004", severity="MEDIUM",
                message=f"No transaction wrapping in '{mig_name}'",
                migration=mig_name,
                suggestion="Wrap DDL in BEGIN/COMMIT for atomicity",
            ))

        # MIG-005: Data manipulation
        if re.search(r'\b(INSERT|UPDATE|DELETE)\b', mig.up_sql, re.IGNORECASE):
            issues.append(MigrationIssue(
                rule_id="MIG-005", severity="MEDIUM",
                message=f"Data manipulation in schema migration '{mig_name}'",
                migration=mig_name,
                suggestion="Separate data migrations from schema migrations",
            ))

        # MIG-006: Long migration
        line_count = len(mig.up_sql.splitlines()) + len(mig.down_sql.splitlines())
        if line_count > 100:
            issues.append(MigrationIssue(
                rule_id="MIG-006", severity="LOW",
                message=f"Migration '{mig_name}' is {line_count} lines",
                migration=mig_name,
                suggestion="Break large migrations into smaller steps",
            ))

        # MIG-007: CREATE TABLE without PK
        for match in re.finditer(r'CREATE\s+TABLE\s+\w+\s*\((.*?)\);',
                                  mig.up_sql, re.DOTALL | re.IGNORECASE):
            body = match.group(1).upper()
            if "PRIMARY KEY" not in body:
                issues.append(MigrationIssue(
                    rule_id="MIG-007", severity="HIGH",
                    message=f"CREATE TABLE without PRIMARY KEY in '{mig_name}'",
                    migration=mig_name,
                    suggestion="Always define a primary key on tables",
                ))

        # MIG-008: Non-sequential version
        if prev_version is not None:
            try:
                if int(mig.version) != int(prev_version) + 1:
                    issues.append(MigrationIssue(
                        rule_id="MIG-008", severity="MEDIUM",
                        message=f"Non-sequential version gap: {prev_version} → {mig.version}",
                        migration=mig_name,
                        suggestion="Use sequential version numbers",
                    ))
            except ValueError:
                pass
        prev_version = mig.version

        # MIG-009: Special chars in name
        if not re.match(r'^[a-z0-9_]+$', mig.name):
            issues.append(MigrationIssue(
                rule_id="MIG-009", severity="LOW",
                message=f"Migration name '{mig.name}' has special characters",
                migration=mig_name,
                suggestion="Use only lowercase letters, numbers, and underscores",
            ))

        # MIG-010: CREATE INDEX without CONCURRENTLY
        if re.search(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY)', mig.up_sql, re.IGNORECASE):
            issues.append(MigrationIssue(
                rule_id="MIG-010", severity="INFO",
                message=f"CREATE INDEX without CONCURRENTLY in '{mig_name}'",
                migration=mig_name,
                suggestion="Use CREATE INDEX CONCURRENTLY to avoid table locks",
            ))

    return issues
