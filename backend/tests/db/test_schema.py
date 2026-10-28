"""Migrazioni e modelli coincidono; le migrazioni si applicano e si annullano."""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect

from gym_split_planner.db import models  # noqa: F401
from gym_split_planner.db.base import Base
from gym_split_planner.db.engine import make_engine
from gym_split_planner.db.migrate import alembic_config, head_revision, upgrade_to_head

EXPECTED_TABLES = {
    "alembic_version",
    "app_setting",
    "daily_routine_item",
    "day_template",
    "day_template_stretch",
    "equipment",
    "exercise",
    "exercise_muscle",
    "exercise_source",
    "exercise_tag",
    "movement_family",
    "muscle",
    "muscle_group",
    "plan",
    "plan_day",
    "plan_day_stretch",
    "plan_slot",
    "slot_template",
    "source",
    "split_template",
    "stretch",
    "tag",
}


def test_migrated_schema_matches_models(tmp_path: Path) -> None:
    engine = make_engine(f"sqlite:///{tmp_path / 'db.sqlite'}")
    upgrade_to_head(engine)

    with engine.connect() as connection:
        context = MigrationContext.configure(
            connection, opts={"compare_type": True, "render_as_batch": True}
        )
        differences = compare_metadata(context, Base.metadata)

    assert differences == [], "Modelli cambiati senza migrazione: uv run alembic revision"
    assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES
    engine.dispose()


def test_migrations_downgrade_to_base_and_back(tmp_path: Path) -> None:
    engine = make_engine(f"sqlite:///{tmp_path / 'db.sqlite'}")
    upgrade_to_head(engine)

    config = alembic_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}

    upgrade_to_head(engine)
    assert head_revision() == "0002"
    assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES
    engine.dispose()
