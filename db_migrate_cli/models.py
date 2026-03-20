"""Core data models for db-migrate-cli."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class MigrationStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DriftSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class DriftType(str, Enum):
    MISSING_TABLE = "missing_table"
    EXTRA_TABLE = "extra_table"
    MISSING_COLUMN = "missing_column"
    EXTRA_COLUMN = "extra_column"
    TYPE_MISMATCH = "type_mismatch"
    CONSTRAINT_DIFF = "constraint_diff"
    INDEX_MISSING = "index_missing"
    INDEX_EXTRA = "index_extra"
    DEFAULT_DIFF = "default_diff"
    NULLABLE_DIFF = "nullable_diff"


class ObjectType(str, Enum):
    TABLE = "table"
    COLUMN = "column"
    INDEX = "index"
    CONSTRAINT = "constraint"
    VIEW = "view"
    FUNCTION = "function"
    TRIGGER = "trigger"


@dataclass
class Column:
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False
    unique: bool = False
    references: Optional[str] = None


@dataclass
class Index:
    name: str
    columns: List[str] = field(default_factory=list)
    unique: bool = False


@dataclass
class Table:
    name: str
    columns: List[Column] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class SchemaSnapshot:
    tables: List[Table] = field(default_factory=list)
    views: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    captured_at: Optional[datetime] = None

    @property
    def table_names(self) -> List[str]:
        return sorted(t.name for t in self.tables)

    def get_table(self, name: str) -> Optional[Table]:
        for t in self.tables:
            if t.name == name:
                return t
        return None


@dataclass
class Migration:
    version: str
    name: str
    up_sql: str
    down_sql: str
    status: MigrationStatus = MigrationStatus.PENDING
    applied_at: Optional[datetime] = None
    checksum: str = ""
    file_path: str = ""

    @property
    def display_name(self) -> str:
        return f"{self.version}_{self.name}"


@dataclass
class DriftIssue:
    drift_type: DriftType
    severity: DriftSeverity
    object_type: ObjectType
    object_name: str
    message: str
    expected: str = ""
    actual: str = ""
    suggestion: str = ""


@dataclass
class DriftReport:
    expected_schema: SchemaSnapshot
    actual_schema: SchemaSnapshot
    issues: List[DriftIssue] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == DriftSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == DriftSeverity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == DriftSeverity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == DriftSeverity.LOW)

    @property
    def has_drift(self) -> bool:
        return len(self.issues) > 0

    @property
    def score(self) -> int:
        if not self.issues:
            return 100
        max_d = max(len(self.issues) * 10, 1)
        deductions = (self.critical_count * 10 + self.high_count * 7 +
                      self.medium_count * 4 + self.low_count * 2)
        return max(0, int(100 - (deductions / max_d) * 100))

    @property
    def grade(self) -> str:
        s = self.score
        if s >= 95: return "A+"
        if s >= 90: return "A"
        if s >= 80: return "B"
        if s >= 70: return "C"
        if s >= 60: return "D"
        return "F"


@dataclass
class MigrationPlan:
    pending: List[Migration] = field(default_factory=list)
    applied: List[Migration] = field(default_factory=list)
    failed: List[Migration] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.pending) + len(self.applied) + len(self.failed)
