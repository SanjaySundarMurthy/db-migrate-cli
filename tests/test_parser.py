"""Tests for db_migrate_cli.parser."""
import os
import pytest
from db_migrate_cli.parser import (
    parse_migrations_dir, parse_migration_file, parse_schema_yaml,
    build_schema_from_migrations,
)


class TestParseMigrations:
    def test_parse_dir(self, migration_dir):
        migs = parse_migrations_dir(migration_dir)
        assert len(migs) == 2
        assert migs[0].version == "001"
        assert migs[1].version == "002"

    def test_parse_nonexistent(self):
        assert parse_migrations_dir("/nonexistent") == []

    def test_parse_single_file(self, migration_dir):
        path = os.path.join(migration_dir, "V001_create_users.sql")
        mig = parse_migration_file(path)
        assert mig is not None
        assert mig.name == "create_users"
        assert "CREATE TABLE" in mig.up_sql
        assert "DROP TABLE" in mig.down_sql
        assert len(mig.checksum) == 16

    def test_parse_file_invalid_name(self, tmp_path):
        bad = tmp_path / "bad_name.sql"
        bad.write_text("-- UP\nSELECT 1;\n-- DOWN\n")
        assert parse_migration_file(str(bad)) is None


class TestParseSchemaYaml:
    def test_parse_schema(self, demo_paths):
        schema = parse_schema_yaml(demo_paths["expected"])
        assert len(schema.tables) >= 3
        users = schema.get_table("users")
        assert users is not None
        assert any(c.primary_key for c in users.columns)

    def test_build_from_migrations(self, migration_dir):
        migs = parse_migrations_dir(migration_dir)
        schema = build_schema_from_migrations(migs)
        assert len(schema.tables) == 2
        assert schema.get_table("users") is not None
