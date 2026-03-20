"""Rich terminal reporter for db-migrate-cli."""
from __future__ import annotations
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from db_migrate_cli.models import (
    DriftReport, DriftSeverity, Migration, MigrationPlan, MigrationStatus,
)

console = Console()

_SEV_COLORS = {
    DriftSeverity.CRITICAL: "red", DriftSeverity.HIGH: "dark_orange",
    DriftSeverity.MEDIUM: "yellow", DriftSeverity.LOW: "cyan",
    DriftSeverity.INFO: "dim",
}
_SEV_ICONS = {
    DriftSeverity.CRITICAL: "🔴", DriftSeverity.HIGH: "🟠",
    DriftSeverity.MEDIUM: "🟡", DriftSeverity.LOW: "🔵",
    DriftSeverity.INFO: "⚪",
}
_STATUS_ICONS = {
    MigrationStatus.PENDING: "⏳", MigrationStatus.APPLIED: "✅",
    MigrationStatus.FAILED: "❌", MigrationStatus.ROLLED_BACK: "↩️",
}


def print_migration_status(migrations: List[Migration], verbose: bool = False) -> None:
    console.print()
    console.print(Panel.fit("[bold cyan]📋 Migration Status[/bold cyan]", border_style="cyan"))
    table = Table(show_header=True, header_style="bold")
    table.add_column("Version", style="dim", width=8)
    table.add_column("Name")
    table.add_column("Status", justify="center")
    table.add_column("Applied At")
    table.add_column("Checksum", style="dim", width=18)

    for m in migrations:
        icon = _STATUS_ICONS.get(m.status, "?")
        color = {"applied": "green", "pending": "yellow", "failed": "red",
                 "rolled_back": "dim"}.get(m.status.value, "white")
        applied = str(m.applied_at)[:19] if m.applied_at else "—"
        table.add_row(
            m.version, m.name, f"[{color}]{icon} {m.status.value}[/{color}]",
            applied, m.checksum or "—",
        )

    console.print(table)
    applied = sum(1 for m in migrations if m.status == MigrationStatus.APPLIED)
    pending = sum(1 for m in migrations if m.status == MigrationStatus.PENDING)
    console.print(f"\n  Applied: {applied}  |  Pending: {pending}  |  Total: {len(migrations)}")
    console.print()


def print_drift_report(report: DriftReport, verbose: bool = False) -> None:
    console.print()
    console.print(Panel.fit("[bold cyan]🔍 Schema Drift Report[/bold cyan]", border_style="cyan"))

    grade_color = "green" if report.grade in ("A+", "A") else \
                  "yellow" if report.grade in ("B", "C") else "red"

    exp_tables = len(report.expected_schema.tables)
    act_tables = len(report.actual_schema.tables)

    console.print(f"\n  Expected Tables: {exp_tables}  |  Actual Tables: {act_tables}")
    console.print(f"  Grade: [{grade_color}]{report.grade}[/{grade_color}]  ({report.score}/100)")
    console.print(f"\n  Drift Issues:")
    console.print(f"    {_SEV_ICONS[DriftSeverity.CRITICAL]} CRITICAL:  {report.critical_count}")
    console.print(f"    {_SEV_ICONS[DriftSeverity.HIGH]}     HIGH:  {report.high_count}")
    console.print(f"    {_SEV_ICONS[DriftSeverity.MEDIUM]}   MEDIUM:  {report.medium_count}")
    console.print(f"    {_SEV_ICONS[DriftSeverity.LOW]}      LOW:  {report.low_count}")

    if not report.has_drift:
        console.print("\n  [green]✅ No drift detected — schema is in sync![/green]")
    elif verbose:
        console.print()
        table = Table(show_header=True, header_style="bold dim", padding=(0, 1))
        table.add_column("Type", width=16)
        table.add_column("Sev", width=10)
        table.add_column("Object")
        table.add_column("Message")
        table.add_column("Suggestion", style="dim")
        for issue in report.issues:
            c = _SEV_COLORS.get(issue.severity, "white")
            table.add_row(
                issue.drift_type.value, f"[{c}]{issue.severity.value}[/{c}]",
                issue.object_name, issue.message, issue.suggestion,
            )
        console.print(table)

    console.print()


def print_migration_issues(issues: list, verbose: bool = False) -> None:
    console.print()
    console.print(Panel.fit("[bold cyan]🔎 Migration Quality Audit[/bold cyan]", border_style="cyan"))

    sev_counts = {}
    for i in issues:
        sev_counts[i.severity] = sev_counts.get(i.severity, 0) + 1

    console.print(f"\n  Total Issues: {len(issues)}")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        count = sev_counts.get(sev, 0)
        if count:
            console.print(f"    {sev}: {count}")

    if verbose and issues:
        console.print()
        table = Table(show_header=True, header_style="bold dim")
        table.add_column("Rule", style="dim", width=10)
        table.add_column("Sev", width=10)
        table.add_column("Migration")
        table.add_column("Message")
        for i in issues:
            c = {"CRITICAL": "red", "HIGH": "dark_orange", "MEDIUM": "yellow",
                 "LOW": "cyan", "INFO": "dim"}.get(i.severity, "white")
            table.add_row(i.rule_id, f"[{c}]{i.severity}[/{c}]", i.migration, i.message)
        console.print(table)

    console.print()
