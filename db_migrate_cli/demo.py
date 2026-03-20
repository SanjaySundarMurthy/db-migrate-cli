"""Demo data generator for db-migrate-cli."""
from __future__ import annotations
import os


def create_demo_project(base_dir: str) -> dict:
    """Create a demo migration project with intentional issues."""
    mig_dir = os.path.join(base_dir, "migrations")
    schema_dir = base_dir
    os.makedirs(mig_dir, exist_ok=True)

    paths = {}

    # Migration 1: Good migration
    paths["mig1"] = _write(os.path.join(mig_dir, "V001_create_users.sql"), """-- UP
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);

-- DOWN
DROP TABLE IF EXISTS users;
""")

    # Migration 2: Good migration
    paths["mig2"] = _write(os.path.join(mig_dir, "V002_create_orders.sql"), """-- UP
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- DOWN
DROP TABLE IF EXISTS orders;
""")

    # Migration 3: Bad — no DOWN, no PK, DROP without IF EXISTS
    paths["mig3"] = _write(os.path.join(mig_dir, "V003_create_logs.sql"), """-- UP
CREATE TABLE audit_logs (
    event_type VARCHAR(50),
    payload TEXT,
    created_at TIMESTAMP
);
DROP TABLE old_temp_data;
INSERT INTO audit_logs (event_type) VALUES ('migration_v3');

-- DOWN
""")

    # Migration 4: Bad — version gap, special chars, long
    paths["mig4"] = _write(os.path.join(mig_dir, "V005_add-user-fields.sql"), """-- UP
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN address TEXT;
ALTER TABLE users DROP COLUMN password_hash;
""" + "\n".join([f"-- line {i}" for i in range(100)]) + """

-- DOWN
ALTER TABLE users DROP COLUMN phone;
ALTER TABLE users DROP COLUMN address;
""")

    # Expected schema (what migrations should produce)
    paths["expected"] = _write(os.path.join(schema_dir, "expected-schema.yaml"), """tables:
  - name: users
    columns:
      - {name: id, type: serial, primary_key: true, nullable: false}
      - {name: email, type: varchar, nullable: false, unique: true}
      - {name: username, type: varchar, nullable: false}
      - {name: password_hash, type: varchar, nullable: false}
      - {name: created_at, type: timestamp, default: "now()"}
      - {name: updated_at, type: timestamp, default: "now()"}
      - {name: phone, type: varchar}
      - {name: address, type: text}
    indexes:
      - {name: idx_users_email, columns: [email]}
  - name: orders
    columns:
      - {name: id, type: serial, primary_key: true, nullable: false}
      - {name: user_id, type: integer, nullable: false, references: users}
      - {name: total_amount, type: decimal, nullable: false}
      - {name: status, type: varchar, default: "pending"}
      - {name: created_at, type: timestamp, default: "now()"}
    indexes:
      - {name: idx_orders_user_id, columns: [user_id]}
  - name: audit_logs
    columns:
      - {name: event_type, type: varchar}
      - {name: payload, type: text}
      - {name: created_at, type: timestamp}
  - name: products
    columns:
      - {name: id, type: serial, primary_key: true, nullable: false}
      - {name: name, type: varchar, nullable: false}
      - {name: price, type: decimal}
""")

    # Actual schema (what's actually in the "database" — with drift)
    paths["actual"] = _write(os.path.join(schema_dir, "actual-schema.yaml"), """tables:
  - name: users
    columns:
      - {name: id, type: serial, primary_key: true, nullable: false}
      - {name: email, type: text, nullable: false}
      - {name: username, type: varchar, nullable: false}
      - {name: password_hash, type: varchar, nullable: false}
      - {name: created_at, type: timestamp, default: "now()"}
      - {name: legacy_field, type: varchar}
    indexes:
      - {name: idx_users_email, columns: [email]}
  - name: orders
    columns:
      - {name: id, type: serial, primary_key: true, nullable: false}
      - {name: user_id, type: integer, nullable: false, references: users}
      - {name: total_amount, type: decimal, nullable: false}
      - {name: status, type: varchar, default: "pending"}
      - {name: created_at, type: timestamp, default: "now()"}
      - {name: discount_code, type: varchar}
    indexes:
      - {name: idx_orders_user_id, columns: [user_id]}
      - {name: idx_orders_status, columns: [status]}
  - name: audit_logs
    columns:
      - {name: event_type, type: varchar}
      - {name: payload, type: text}
      - {name: created_at, type: timestamp}
  - name: temp_cache
    columns:
      - {name: key, type: varchar}
      - {name: value, type: text}
""")

    paths["migrations_dir"] = mig_dir
    return paths


def _write(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path
