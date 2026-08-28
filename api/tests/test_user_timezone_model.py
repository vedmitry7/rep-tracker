import importlib

import sqlalchemy as sa

from api.app.models import User


def test_user_timezone_column_is_required() -> None:
    column = User.__table__.c.timezone

    assert isinstance(column.type, sa.String)
    assert column.nullable is False


def test_timezone_migration_backfills_and_removes_default(
    monkeypatch,
) -> None:
    migration = importlib.import_module(
        "api.alembic.versions.20260827_06_add_timezone_to_users"
    )
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        migration.op,
        "add_column",
        lambda table, column: calls.append(("add", (table, column))),
    )
    monkeypatch.setattr(
        migration.op,
        "alter_column",
        lambda table, column, **kwargs: calls.append(
            ("alter", (table, column, kwargs))
        ),
    )

    migration.upgrade()

    added = calls[0][1][1]
    assert calls[0][0] == "add"
    assert calls[0][1][0] == "users"
    assert added.name == "timezone"
    assert added.nullable is False
    assert added.server_default.arg == "Europe/Moscow"
    assert calls[1] == (
        "alter",
        ("users", "timezone", {"server_default": None}),
    )
