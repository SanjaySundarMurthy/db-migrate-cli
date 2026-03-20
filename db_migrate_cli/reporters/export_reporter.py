"""JSON and HTML export reporters."""
from __future__ import annotations
import json
from datetime import datetime
from typing import Any, List

from db_migrate_cli.models import DriftReport, Migration


def export_json(data: dict, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=_json_default)


def drift_report_to_dict(report: DriftReport) -> dict:
    return {
        "drift_report": {
            "score": report.score, "grade": report.grade,
            "has_drift": report.has_drift,
            "expected_tables": len(report.expected_schema.tables),
            "actual_tables": len(report.actual_schema.tables),
            "issues": [
                {"type": i.drift_type.value, "severity": i.severity.value,
                 "object": i.object_name, "message": i.message,
                 "expected": i.expected, "actual": i.actual,
                 "suggestion": i.suggestion}
                for i in report.issues
            ],
            "summary": {"critical": report.critical_count, "high": report.high_count,
                        "medium": report.medium_count, "low": report.low_count},
        }
    }


def migrations_to_dict(migrations: List[Migration]) -> dict:
    return {
        "migrations": [
            {"version": m.version, "name": m.name, "status": m.status.value,
             "checksum": m.checksum,
             "applied_at": m.applied_at.isoformat() if m.applied_at else None}
            for m in migrations
        ]
    }


def export_html(title: str, data: dict, output_path: str) -> None:
    rows = _dict_to_rows(data)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title}</title>
<style>body{{font-family:system-ui;background:#0d1117;color:#c9d1d9;padding:20px}}
h1{{background:linear-gradient(135deg,#58a6ff,#3fb950);-webkit-background-clip:text;
-webkit-text-fill-color:transparent}}table{{border-collapse:collapse;width:100%;margin:20px 0}}
th{{background:#161b22;color:#58a6ff;padding:10px;text-align:left}}
td{{border-bottom:1px solid #21262d;padding:8px}}</style></head>
<body><h1>{title}</h1><table><tr><th>Key</th><th>Value</th></tr>{rows}</table>
<footer style="color:#484f58;margin-top:40px">db-migrate-cli v1.0.0</footer></body></html>"""
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"Not serializable: {type(obj)}")


def _dict_to_rows(data: dict, prefix: str = "") -> str:
    rows = []
    for k, v in data.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            rows.append(_dict_to_rows(v, key))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    rows.append(_dict_to_rows(item, f"{key}[{i}]"))
                else:
                    rows.append(f"<tr><td>{key}[{i}]</td><td>{_esc(item)}</td></tr>")
        else:
            rows.append(f"<tr><td>{key}</td><td>{_esc(v)}</td></tr>")
    return "\n".join(rows)


def _esc(v: Any) -> str:
    return str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
