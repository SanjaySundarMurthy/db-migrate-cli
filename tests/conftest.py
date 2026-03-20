"""Shared fixtures for db-migrate-cli tests."""
import os
import pytest
import yaml

from db_migrate_cli.models import (
    Column, Index, Migration, MigrationStatus, SchemaSnapshot, Table,
)
from db_migrate_cli.demo import create_demo_project


@pytest.fixture
def tmp_yaml(tmp_path):
    def _write(data, name="data.yaml"):
        p = tmp_path / name
        with open(p, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return str(p)
    return _write


@pytest.fixture
def sample_migration():
    return Migration(version="001", name="create_users",
                     up_sql="CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);",
                     down_sql="DROP TABLE IF EXISTS users;", checksum="abc123")


@pytest.fixture
def sample_schema():
    return SchemaSnapshot(tables=[
        Table(name="users", columns=[
            Column(name="id", data_type="serial", primary_key=True, nullable=False),
            Column(name="email", data_type="varchar", nullable=False, unique=True),
        ], indexes=[Index(name="idx_email", columns=["email"])]),
        Table(name="orders", columns=[
            Column(name="id", data_type="serial", primary_key=True, nullable=False),
            Column(name="user_id", data_type="integer", nullable=False),
        ]),
    ])


@pytest.fixture
def drifted_schema():
    return SchemaSnapshot(tables=[
        Table(name="users", columns=[
            Column(name="id", data_type="serial", primary_key=True, nullable=False),
            Column(name="email", data_type="text", nullable=False),  # type mismatch
            Column(name="legacy", data_type="varchar"),  # extra column
        ]),  # missing index
        Table(name="temp_data", columns=[  # extra table
            Column(name="key", data_type="varchar"),
        ]),
    ])  # missing orders table


@pytest.fixture
def demo_paths(tmp_path):
    return create_demo_project(str(tmp_path / "demo"))


@pytest.fixture
def migration_dir(tmp_path):
    d = tmp_path / "migrations"
    d.mkdir()
    (d / "V001_create_users.sql").write_text(
        "-- UP\nCREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);\n-- DOWN\nDROP TABLE IF EXISTS users;\n")
    (d / "V002_create_orders.sql").write_text(
        "-- UP\nCREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL);\n-- DOWN\nDROP TABLE IF EXISTS orders;\n")
    return str(d)
