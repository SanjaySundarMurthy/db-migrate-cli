# 🗄️ db-migrate-cli

**Database Schema Migration Runner with Drift Detection**

A Python CLI tool that manages database migrations, detects schema drift between expected and actual states, and audits migration quality with 10 rules.

## Features

| Command | What It Does |
|---------|-------------|
| `db-migrate-cli status` | Show migration file status and history |
| `db-migrate-cli drift` | Detect schema drift between expected and actual |
| `db-migrate-cli audit` | Audit migration files for quality (10 rules) |
| `db-migrate-cli demo` | Run full demo with sample data |
| `db-migrate-cli rules` | List all migration quality rules |

## Installation

```bash
git clone https://github.com/sanjaysundarmurthy/db-migrate-cli.git
cd db-migrate-cli
pip install -e .
```

## Quick Start

```bash
db-migrate-cli demo -v
db-migrate-cli drift expected-schema.yaml actual-schema.yaml -v
db-migrate-cli audit ./migrations -v
db-migrate-cli status ./migrations
```

## Drift Detection

Compares expected schema (from YAML/migrations) against actual database state:
- Missing/extra tables, columns, indexes
- Type mismatches, nullable differences, default value changes
- Severity scoring: CRITICAL → LOW with grade A+ to F

## Migration Quality Rules (10)

| Rule | Severity | Description |
|------|----------|-------------|
| MIG-001 | CRITICAL | Migration missing DOWN section |
| MIG-002 | HIGH | DROP TABLE without IF EXISTS |
| MIG-003 | HIGH | Destructive column drop |
| MIG-004 | MEDIUM | No transaction wrapping |
| MIG-005 | MEDIUM | Data manipulation in schema migration |
| MIG-006 | LOW | Migration file exceeds 100 lines |
| MIG-007 | HIGH | CREATE TABLE without primary key |
| MIG-008 | MEDIUM | Non-sequential migration version |
| MIG-009 | LOW | Name contains special characters |
| MIG-010 | INFO | CREATE INDEX without CONCURRENTLY |

## Export Formats

Terminal (Rich), JSON, HTML

## License

MIT
