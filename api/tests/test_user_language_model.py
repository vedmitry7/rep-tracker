import importlib

import sqlalchemy as sa

from api.app.models import User


def test_user_language_column_is_required() -> None:
    column = User.__table__.c.language

    assert isinstance(column.type, sa.String)
    assert column.type.length == 2
    assert column.nullable is False
    assert column.server_default is None


def test_language_migration_backfills_ru_and_removes_default(monkeypatch) -> None:
    migration = importlib.import_module(
        "api.alembic.versions.20260827_08_add_language_to_users"
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
    assert calls[0][1][0] == "users"
    assert added.name == "language"
    assert added.nullable is False
    assert added.server_default.arg == "ru"
    assert calls[1] == (
        "alter",
        ("users", "language", {"server_default": None}),
    )
