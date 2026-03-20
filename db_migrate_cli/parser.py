"""Schema parser — parse SQL migration files and YAML schema definitions."""
from __future__ import annotations
import hashlib
import os
import re
from datetime import datetime
from typing import List, Optional, Tuple

import yaml

from db_migrate_cli.models import (
    Column, Index, Migration, MigrationStatus, SchemaSnapshot, Table,
)


def parse_migrations_dir(path: str) -> List[Migration]:
    """Parse all migration files from a directory.

    Expected naming: V001_create_users.sql or 001_create_users.sql
    Each file must contain -- UP and -- DOWN markers.
    """
    if not os.path.isdir(path):
        return []

    migrations = []
    for fname in sorted(os.listdir(path)):
        if not fname.endswith(".sql"):
            continue
        fpath = os.path.join(path, fname)
        migration = parse_migration_file(fpath)
        if migration:
            migrations.append(migration)
    return migrations


def parse_migration_file(path: str) -> Optional[Migration]:
    """Parse a single migration SQL file."""
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    basename = os.path.basename(path)
    match = re.match(r'^V?(\d+)[_-](.+)\.sql$', basename, re.IGNORECASE)
    if not match:
        return None

    version = match.group(1).zfill(3)
    name = match.group(2).replace("-", "_").replace(" ", "_")

    up_sql, down_sql = _split_up_down(content)
    checksum = hashlib.sha256(content.encode()).hexdigest()[:16]

    return Migration(
        version=version,
        name=name,
        up_sql=up_sql,
        down_sql=down_sql,
        checksum=checksum,
        file_path=path,
    )


def parse_schema_yaml(path: str) -> SchemaSnapshot:
    """Parse a schema definition from YAML."""
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    tables = []
    for tbl_data in data.get("tables", []):
        columns = []
        for col_data in tbl_data.get("columns", []):
            columns.append(Column(
                name=col_data["name"],
                data_type=col_data.get("type", "text"),
                nullable=col_data.get("nullable", True),
                default=col_data.get("default"),
                primary_key=col_data.get("primary_key", False),
                unique=col_data.get("unique", False),
                references=col_data.get("references"),
            ))
        indexes = []
        for idx_data in tbl_data.get("indexes", []):
            indexes.append(Index(
                name=idx_data["name"],
                columns=idx_data.get("columns", []),
                unique=idx_data.get("unique", False),
            ))
        tables.append(Table(
            name=tbl_data["name"],
            columns=columns,
            indexes=indexes,
            constraints=tbl_data.get("constraints", []),
        ))

    return SchemaSnapshot(
        tables=tables,
        views=data.get("views", []),
        functions=data.get("functions", []),
        captured_at=datetime.now(),
    )


def build_schema_from_migrations(migrations: List[Migration]) -> SchemaSnapshot:
    """Build a schema snapshot by analyzing CREATE TABLE statements in migrations."""
    tables = []
    for mig in migrations:
        if mig.status == MigrationStatus.ROLLED_BACK:
            continue
        extracted = _extract_tables_from_sql(mig.up_sql)
        tables.extend(extracted)
    return SchemaSnapshot(tables=tables, captured_at=datetime.now())


def load_migration_state(state_path: str) -> List[Migration]:
    """Load migration state from a YAML state file."""
    if not os.path.exists(state_path):
        return []
    with open(state_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not data:
        return []

    migrations = []
    for entry in data.get("migrations", []):
        migrations.append(Migration(
            version=entry["version"],
            name=entry.get("name", ""),
            up_sql="",
            down_sql="",
            status=MigrationStatus(entry.get("status", "applied")),
            applied_at=entry.get("applied_at"),
            checksum=entry.get("checksum", ""),
        ))
    return migrations


def save_migration_state(state_path: str, migrations: List[Migration]) -> None:
    """Save migration state to YAML."""
    data = {
        "migrations": [
            {
                "version": m.version,
                "name": m.name,
                "status": m.status.value,
                "applied_at": m.applied_at.isoformat() if m.applied_at else None,
                "checksum": m.checksum,
            }
            for m in migrations
        ]
    }
    os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as fh:
        yaml.dump(data, fh, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_up_down(content: str) -> Tuple[str, str]:
    """Split migration content into UP and DOWN sections."""
    up_match = re.search(r'--\s*UP\s*\n(.*?)(?=--\s*DOWN|\Z)', content, re.DOTALL | re.IGNORECASE)
    down_match = re.search(r'--\s*DOWN\s*\n(.*)', content, re.DOTALL | re.IGNORECASE)
    up_sql = up_match.group(1).strip() if up_match else content.strip()
    down_sql = down_match.group(1).strip() if down_match else ""
    return up_sql, down_sql


def _extract_tables_from_sql(sql: str) -> List[Table]:
    """Extract CREATE TABLE definitions from SQL."""
    tables = []
    pattern = re.compile(
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?\s*\((.*?)\);',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(sql):
        table_name = match.group(1)
        body = match.group(2)
        columns = _parse_column_defs(body)
        tables.append(Table(name=table_name, columns=columns))
    return tables


def _parse_column_defs(body: str) -> List[Column]:
    """Parse column definitions from CREATE TABLE body."""
    columns = []
    for line in body.split(","):
        line = line.strip()
        if not line or line.upper().startswith(("PRIMARY", "UNIQUE", "FOREIGN",
                                                "CONSTRAINT", "CHECK", "INDEX")):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        col_name = parts[0].strip('`"')
        col_type = parts[1].strip('`"')
        nullable = "NOT NULL" not in line.upper()
        pk = "PRIMARY KEY" in line.upper()
        unique = "UNIQUE" in line.upper() and not pk
        default = None
        def_match = re.search(r'DEFAULT\s+(.+?)(?:\s+|,|$)', line, re.IGNORECASE)
        if def_match:
            default = def_match.group(1).strip("'\"")
        ref = None
        ref_match = re.search(r'REFERENCES\s+(\w+)', line, re.IGNORECASE)
        if ref_match:
            ref = ref_match.group(1)
        columns.append(Column(
            name=col_name, data_type=col_type, nullable=nullable,
            primary_key=pk, unique=unique, default=default, references=ref,
        ))
    return columns
