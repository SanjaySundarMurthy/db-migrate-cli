---
title: "🗄️ db-migrate-cli: Database Schema Migration Runner with Drift Detection"
published: true
description: "A Python CLI tool for managing database schema migrations, detecting schema drift, and auditing migration quality with 10 built-in rules."
tags: database, devops, python, cli
cover_image: ""
---

## The Problem

Database schema management is one of the hardest parts of application deployment. Migrations get applied inconsistently across environments, schema drift creeps in silently, and poorly written migrations cause outages. Teams need visibility into migration status, drift detection, and quality enforcement — without vendor lock-in.

## What I Built

**db-migrate-cli** — A Python CLI tool that provides:

- **Migration Status Tracking** — Parse and display migration state across environments
- **Schema Drift Detection** — Compare expected vs. actual schema with severity scoring
- **Migration Quality Audit** — 10 built-in rules (MIG-001 to MIG-010) for best practices
- **Rich Terminal Output** — Color-coded tables, panels, and severity indicators
- **Multi-Format Export** — JSON and HTML reports for CI/CD integration

## Architecture

```
db-migrate-cli/
├── db_migrate_cli/
│   ├── models.py           # Domain models (Migration, DriftIssue, SchemaSnapshot)
│   ├── parser.py           # SQL migration parser + YAML schema loader
│   ├── analyzers/
│   │   ├── drift_detector.py      # Schema comparison engine
│   │   └── migration_analyzer.py  # 10-rule quality analyzer
│   ├── reporters/
│   │   ├── terminal_reporter.py   # Rich terminal output
│   │   └── export_reporter.py     # JSON + HTML export
│   ├── cli.py              # Click CLI entry points
│   └── demo.py             # Demo project generator
└── tests/                  # 37 tests (100% pass)
```

## Drift Detection

The drift detector compares expected schema (from migrations) against actual schema (from database) and identifies 10 types of drift:

| Drift Type | Description |
|-----------|-------------|
| MISSING_TABLE | Table exists in expected but not in actual |
| EXTRA_TABLE | Table exists in actual but not in expected |
| MISSING_COLUMN | Column missing from actual table |
| EXTRA_COLUMN | Unexpected column in actual table |
| TYPE_MISMATCH | Column type differs between schemas |
| CONSTRAINT_DIFF | Constraint mismatch |
| INDEX_MISSING | Expected index not found |
| INDEX_EXTRA | Unexpected index found |
| DEFAULT_DIFF | Default value mismatch |
| NULLABLE_DIFF | Nullable constraint mismatch |

Each drift issue gets a severity (critical/high/medium/low) and the report produces a **drift score** (0-100) with a letter grade.

## Migration Audit Rules

```
MIG-001  No rollback section (DOWN block missing)
MIG-002  DROP without IF EXISTS (risky operation)
MIG-003  DROP COLUMN detected (data loss risk)
MIG-004  No transaction wrapper
MIG-005  DML in schema migration (data manipulation)
MIG-006  Migration file too long (>200 lines)
MIG-007  No primary key defined
MIG-008  Non-sequential version numbering
MIG-009  Special characters in migration name
MIG-010  CREATE INDEX without CONCURRENTLY
```

## Quick Start

```bash
pip install -e .

# Generate demo project
db-migrate-cli demo

# Check migration status
db-migrate-cli status --migrations-dir demo-project/migrations

# Detect schema drift
db-migrate-cli drift \
  --expected demo-project/expected-schema.yaml \
  --actual demo-project/actual-schema.yaml

# Audit migration quality
db-migrate-cli audit --migrations-dir demo-project/migrations

# Export as JSON
db-migrate-cli drift \
  --expected demo-project/expected-schema.yaml \
  --actual demo-project/actual-schema.yaml \
  --format json --output drift-report.json
```

## CI/CD Integration

Use `--fail-on` to fail pipelines on drift severity:

```yaml
- name: Schema Drift Check
  run: |
    db-migrate-cli drift \
      --expected schema/expected.yaml \
      --actual schema/actual.yaml \
      --fail-on high
```

## Test Results

```
37 passed in 1.49s
├── test_models.py      —  7 tests (enums, dataclasses, scoring)
├── test_parser.py      —  6 tests (SQL parsing, YAML loading)
├── test_analyzers.py   — 11 tests (drift detection, audit rules)
└── test_cli.py         — 13 tests (all CLI commands)
```

## Tech Stack

- **CLI Framework**: Click 8.x
- **Terminal UI**: Rich (tables, panels, colors)
- **Schema Format**: YAML
- **Migration Format**: SQL (V###_name.sql convention)
- **Testing**: pytest with Click's CliRunner

## Links

- **GitHub**: [db-migrate-cli](https://github.com/sanjaysundarmurthy/db-migrate-cli)
- **Part of**: DevOps CLI Tools Suite (Tool 6 of 14)

---

*Built as part of an ongoing series creating production-grade DevOps CLI tools in Python.*
