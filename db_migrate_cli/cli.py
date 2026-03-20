"""CLI entry point for db-migrate-cli."""
from __future__ import annotations
import sys
import click
from rich.console import Console

from db_migrate_cli import __version__

console = Console()


@click.group()
@click.version_option(__version__, prog_name="db-migrate-cli")
def main():
    """🗄️ db-migrate-cli — Database Schema Migration Runner with Drift Detection."""


@main.command()
@click.argument("migrations_dir", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True)
@click.option("-f", "--format", "fmt", type=click.Choice(["terminal", "json", "html"]), default="terminal")
@click.option("-o", "--output", "output_path", type=click.Path())
def status(migrations_dir: str, verbose: bool, fmt: str, output_path: str):
    """Show migration status and history."""
    from db_migrate_cli.parser import parse_migrations_dir
    from db_migrate_cli.reporters.terminal_reporter import print_migration_status
    from db_migrate_cli.reporters.export_reporter import export_json, export_html, migrations_to_dict

    migrations = parse_migrations_dir(migrations_dir)
    if not migrations:
        console.print("[yellow]No migrations found.[/yellow]")
        return

    if fmt == "terminal":
        print_migration_status(migrations, verbose=verbose)
    else:
        data = migrations_to_dict(migrations)
        if fmt == "json":
            p = output_path or "migration-status.json"
            export_json(data, p)
            console.print(f"[green]JSON saved to {p}[/green]")
        elif fmt == "html":
            p = output_path or "migration-status.html"
            export_html("Migration Status", data, p)
            console.print(f"[green]HTML saved to {p}[/green]")


@main.command()
@click.argument("expected_schema", type=click.Path(exists=True))
@click.argument("actual_schema", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True)
@click.option("-f", "--format", "fmt", type=click.Choice(["terminal", "json", "html"]), default="terminal")
@click.option("-o", "--output", "output_path", type=click.Path())
@click.option("--fail-on", type=click.Choice(["critical", "high", "medium", "low"]))
def drift(expected_schema: str, actual_schema: str, verbose: bool, fmt: str,
          output_path: str, fail_on: str):
    """Detect schema drift between expected and actual database state."""
    from db_migrate_cli.parser import parse_schema_yaml
    from db_migrate_cli.analyzers.drift_detector import detect_drift
    from db_migrate_cli.reporters.terminal_reporter import print_drift_report
    from db_migrate_cli.reporters.export_reporter import export_json, export_html, drift_report_to_dict

    expected = parse_schema_yaml(expected_schema)
    actual = parse_schema_yaml(actual_schema)
    report = detect_drift(expected, actual)

    if fmt == "terminal":
        print_drift_report(report, verbose=verbose)
    else:
        data = drift_report_to_dict(report)
        if fmt == "json":
            p = output_path or "drift-report.json"
            export_json(data, p)
            console.print(f"[green]JSON saved to {p}[/green]")
        elif fmt == "html":
            p = output_path or "drift-report.html"
            export_html("Schema Drift Report", data, p)
            console.print(f"[green]HTML saved to {p}[/green]")

    if fail_on and report.issues:
        sev_order = ["critical", "high", "medium", "low"]
        threshold = sev_order.index(fail_on)
        for issue in report.issues:
            if sev_order.index(issue.severity.value.lower()) <= threshold:
                sys.exit(1)


@main.command()
@click.argument("migrations_dir", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True)
@click.option("-f", "--format", "fmt", type=click.Choice(["terminal", "json"]), default="terminal")
@click.option("-o", "--output", "output_path", type=click.Path())
def audit(migrations_dir: str, verbose: bool, fmt: str, output_path: str):
    """Audit migration files for quality and best practices."""
    from db_migrate_cli.parser import parse_migrations_dir
    from db_migrate_cli.analyzers.migration_analyzer import analyze_migrations
    from db_migrate_cli.reporters.terminal_reporter import print_migration_issues
    from db_migrate_cli.reporters.export_reporter import export_json

    migrations = parse_migrations_dir(migrations_dir)
    issues = analyze_migrations(migrations)

    if fmt == "terminal":
        print_migration_issues(issues, verbose=verbose)
    else:
        data = {"issues": [{"rule_id": i.rule_id, "severity": i.severity,
                            "migration": i.migration, "message": i.message,
                            "suggestion": i.suggestion} for i in issues]}
        p = output_path or "migration-audit.json"
        export_json(data, p)
        console.print(f"[green]JSON saved to {p}[/green]")


@main.command()
@click.option("-v", "--verbose", is_flag=True)
@click.option("-d", "--dir", "demo_dir", default="db-migrate-demo")
def demo(verbose: bool, demo_dir: str):
    """Run a full demo with sample migrations and drift detection."""
    from db_migrate_cli.demo import create_demo_project
    from db_migrate_cli.parser import parse_migrations_dir, parse_schema_yaml
    from db_migrate_cli.analyzers.drift_detector import detect_drift
    from db_migrate_cli.analyzers.migration_analyzer import analyze_migrations
    from db_migrate_cli.reporters.terminal_reporter import (
        print_migration_status, print_drift_report, print_migration_issues,
    )

    console.print("\n[bold cyan]🎪 Creating demo migration project...[/bold cyan]\n")
    paths = create_demo_project(demo_dir)
    console.print(f"  📁 Demo files created in [bold]{demo_dir}/[/bold]\n")

    console.print("[bold]━━━ 1/3  Migration Status ━━━[/bold]")
    migrations = parse_migrations_dir(paths["migrations_dir"])
    print_migration_status(migrations, verbose=verbose)

    console.print("[bold]━━━ 2/3  Schema Drift Detection ━━━[/bold]")
    expected = parse_schema_yaml(paths["expected"])
    actual = parse_schema_yaml(paths["actual"])
    report = detect_drift(expected, actual)
    print_drift_report(report, verbose=verbose)

    console.print("[bold]━━━ 3/3  Migration Quality Audit ━━━[/bold]")
    issues = analyze_migrations(migrations)
    print_migration_issues(issues, verbose=verbose)

    console.print("[bold green]✅ Demo complete![/bold green]\n")


@main.command()
def rules():
    """List all migration quality rules."""
    from rich.table import Table as RichTable
    from db_migrate_cli.analyzers.migration_analyzer import MIGRATION_RULES

    table = RichTable(title="db-migrate-cli Migration Rules", show_header=True, header_style="bold cyan")
    table.add_column("Rule ID", style="dim", width=10)
    table.add_column("Severity", width=10)
    table.add_column("Description")
    for r in MIGRATION_RULES:
        c = {"CRITICAL": "red", "HIGH": "dark_orange", "MEDIUM": "yellow",
             "LOW": "cyan", "INFO": "dim"}.get(r["severity"], "white")
        table.add_row(r["id"], f"[{c}]{r['severity']}[/{c}]", r["desc"])
    console.print()
    console.print(table)
    console.print(f"\n  Total: {len(MIGRATION_RULES)} rules\n")


if __name__ == "__main__":
    main()
