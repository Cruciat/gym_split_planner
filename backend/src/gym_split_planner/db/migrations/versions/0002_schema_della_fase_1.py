"""Schema della fase 1: catalogo, split, schede, impostazioni (modello dati v0.2).

Revisione: 0002
Precedente: 0001
Creata il: 2026-10-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_setting",
        sa.Column("key", sa.String(length=60), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_app_setting")),
    )
    op.create_table(
        "daily_routine_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "block",
            sa.Enum("neck", "pelvis", name="block", native_enum=False, create_constraint=True),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("dose", sa.String(length=120), nullable=False),
        sa.Column("purpose", sa.String(length=200), nullable=False),
        sa.Column(
            "confidence",
            sa.Enum(
                "solid",
                "limited",
                "opinion",
                name="confidence",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_routine_item")),
        sa.UniqueConstraint("position", name=op.f("uq_daily_routine_item_position")),
    )
    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment")),
        sa.UniqueConstraint("code", name=op.f("uq_equipment_code")),
    )
    op.create_table(
        "muscle_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_muscle_group")),
        sa.UniqueConstraint("code", name=op.f("uq_muscle_group_code")),
    )
    op.create_table(
        "source",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("kind", sa.String(length=120), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("reliability", sa.String(length=60), nullable=True),
        sa.Column("used_for", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source")),
        sa.UniqueConstraint("code", name=op.f("uq_source_code")),
    )
    op.create_table(
        "split_template",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_builtin", sa.Boolean(create_constraint=True, name="is_builtin"), nullable=False
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_split_template")),
        sa.UniqueConstraint("code", name=op.f("uq_split_template_code")),
    )
    op.create_table(
        "stretch",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("targets", sa.String(length=200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("dose", sa.String(length=120), nullable=False),
        sa.Column(
            "confidence",
            sa.Enum(
                "solid",
                "limited",
                "opinion",
                name="confidence",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stretch")),
        sa.UniqueConstraint("code", name=op.f("uq_stretch_code")),
    )
    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column(
            "color",
            sa.Enum(
                "neutral",
                "info",
                "success",
                "warning",
                "danger",
                name="color",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "effect",
            sa.Enum(
                "none",
                "bonus",
                "penalty",
                "exclude",
                name="effect",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("points", sa.Float(), nullable=False),
        sa.Column(
            "show_badge", sa.Boolean(create_constraint=True, name="show_badge"), nullable=False
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=20), nullable=False),
        sa.Column("updated_at", sa.String(length=20), nullable=False),
        sa.CheckConstraint(
            "effect NOT IN ('bonus', 'penalty') OR points > 0",
            name=op.f("ck_tag_points_for_effect"),
        ),
        sa.CheckConstraint("points >= 0", name=op.f("ck_tag_points_non_negative")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tag")),
        sa.UniqueConstraint("code", name=op.f("uq_tag_code")),
        sa.UniqueConstraint("name", name=op.f("uq_tag_name")),
    )
    op.create_table(
        "day_template",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("split_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("times_per_week", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "times_per_week BETWEEN 1 AND 3", name=op.f("ck_day_template_times_per_week")
        ),
        sa.ForeignKeyConstraint(
            ["split_id"],
            ["split_template.id"],
            name=op.f("fk_day_template_split_id_split_template"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_day_template")),
        sa.UniqueConstraint("split_id", "code", name=op.f("uq_day_template_split_id_code")),
        sa.UniqueConstraint("split_id", "position", name=op.f("uq_day_template_split_id_position")),
    )
    op.create_table(
        "movement_family",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("muscle_group_id", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["muscle_group_id"],
            ["muscle_group.id"],
            name=op.f("fk_movement_family_muscle_group_id_muscle_group"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_movement_family")),
        sa.UniqueConstraint("code", name=op.f("uq_movement_family_code")),
        sa.UniqueConstraint("name", name=op.f("uq_movement_family_name")),
    )
    op.create_table(
        "muscle",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("short_name", sa.String(length=40), nullable=False),
        sa.Column("muscle_group_id", sa.Integer(), nullable=False),
        sa.Column(
            "priority",
            sa.Enum(
                "priority",
                "standard",
                "none",
                name="priority",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("weekly_min", sa.Float(), nullable=True),
        sa.Column("weekly_max", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "(priority = 'none' AND weekly_min IS NULL AND weekly_max IS NULL) OR (priority <> 'none' AND weekly_min IS NOT NULL AND weekly_max IS NOT NULL AND weekly_min >= 0 AND weekly_min < weekly_max)",
            name=op.f("ck_muscle_band"),
        ),
        sa.ForeignKeyConstraint(
            ["muscle_group_id"],
            ["muscle_group.id"],
            name=op.f("fk_muscle_muscle_group_id_muscle_group"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_muscle")),
        sa.UniqueConstraint("code", name=op.f("uq_muscle_code")),
    )
    op.create_table(
        "plan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("split_template_id", sa.Integer(), nullable=True),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(create_constraint=True, name="is_active"), nullable=False
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=20), nullable=False),
        sa.Column("updated_at", sa.String(length=20), nullable=False),
        sa.CheckConstraint("revision >= 1", name=op.f("ck_plan_revision")),
        sa.ForeignKeyConstraint(
            ["split_template_id"],
            ["split_template.id"],
            name=op.f("fk_plan_split_template_id_split_template"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan")),
    )
    with op.batch_alter_table("plan", schema=None) as batch_op:
        batch_op.create_index(
            "uq_plan_single_active",
            ["is_active"],
            unique=True,
            sqlite_where=sa.text("is_active = 1"),
        )

    op.create_table(
        "day_template_stretch",
        sa.Column("day_template_id", sa.Integer(), nullable=False),
        sa.Column("stretch_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["day_template_id"],
            ["day_template.id"],
            name=op.f("fk_day_template_stretch_day_template_id_day_template"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["stretch_id"],
            ["stretch.id"],
            name=op.f("fk_day_template_stretch_stretch_id_stretch"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "day_template_id", "stretch_id", name=op.f("pk_day_template_stretch")
        ),
    )
    op.create_table(
        "exercise",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("primary_family_id", sa.Integer(), nullable=False),
        sa.Column("secondary_family_id", sa.Integer(), nullable=True),
        sa.Column("family_rank", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("equipment_detail", sa.String(length=120), nullable=True),
        sa.Column(
            "kind",
            sa.Enum(
                "compound", "isolation", name="kind", native_enum=False, create_constraint=True
            ),
            nullable=False,
        ),
        sa.Column(
            "stretch",
            sa.Enum(
                "high", "medium", "low", name="stretch", native_enum=False, create_constraint=True
            ),
            nullable=False,
        ),
        sa.Column("stretch_note", sa.Text(), nullable=True),
        sa.Column(
            "confidence",
            sa.Enum(
                "solid",
                "limited",
                "opinion",
                name="confidence",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(create_constraint=True, name="is_active"), nullable=False
        ),
        sa.Column("created_at", sa.String(length=20), nullable=False),
        sa.Column("updated_at", sa.String(length=20), nullable=False),
        sa.CheckConstraint("family_rank >= 1", name=op.f("ck_exercise_family_rank")),
        sa.CheckConstraint(
            "secondary_family_id IS NULL OR secondary_family_id <> primary_family_id",
            name=op.f("ck_exercise_secondary_family"),
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["equipment.id"],
            name=op.f("fk_exercise_equipment_id_equipment"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["primary_family_id"],
            ["movement_family.id"],
            name=op.f("fk_exercise_primary_family_id_movement_family"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["secondary_family_id"],
            ["movement_family.id"],
            name=op.f("fk_exercise_secondary_family_id_movement_family"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exercise")),
        sa.UniqueConstraint("code", name=op.f("uq_exercise_code")),
        sa.UniqueConstraint("name", name=op.f("uq_exercise_name")),
    )
    with op.batch_alter_table("exercise", schema=None) as batch_op:
        batch_op.create_index("ix_exercise_is_active", ["is_active"], unique=False)
        batch_op.create_index("ix_exercise_primary_family_id", ["primary_family_id"], unique=False)
        batch_op.create_index(
            "ix_exercise_secondary_family_id", ["secondary_family_id"], unique=False
        )

    op.create_table(
        "plan_day",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("times_per_week", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "times_per_week BETWEEN 1 AND 3", name=op.f("ck_plan_day_times_per_week")
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plan.id"], name=op.f("fk_plan_day_plan_id_plan"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_day")),
        sa.UniqueConstraint("plan_id", "position", name=op.f("uq_plan_day_plan_id_position")),
    )
    op.create_table(
        "slot_template",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("day_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("default_sets", sa.Integer(), nullable=False),
        sa.Column("rep_min", sa.Integer(), nullable=False),
        sa.Column("rep_max", sa.Integer(), nullable=False),
        sa.Column(
            "is_optional", sa.Boolean(create_constraint=True, name="is_optional"), nullable=False
        ),
        sa.Column("weekly_weight", sa.Float(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "default_sets BETWEEN 1 AND 8", name=op.f("ck_slot_template_default_sets")
        ),
        sa.CheckConstraint(
            "rep_min >= 1 AND rep_max >= rep_min", name=op.f("ck_slot_template_reps")
        ),
        sa.CheckConstraint(
            "weekly_weight IN (0.5, 1)", name=op.f("ck_slot_template_weekly_weight")
        ),
        sa.ForeignKeyConstraint(
            ["day_id"],
            ["day_template.id"],
            name=op.f("fk_slot_template_day_id_day_template"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["family_id"],
            ["movement_family.id"],
            name=op.f("fk_slot_template_family_id_movement_family"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_slot_template")),
        sa.UniqueConstraint("day_id", "position", name=op.f("uq_slot_template_day_id_position")),
    )
    op.create_table(
        "exercise_muscle",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("muscle_id", sa.Integer(), nullable=False),
        sa.Column(
            "level",
            sa.Enum("P", "S", name="level", native_enum=False, create_constraint=True),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercise.id"],
            name=op.f("fk_exercise_muscle_exercise_id_exercise"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["muscle_id"],
            ["muscle.id"],
            name=op.f("fk_exercise_muscle_muscle_id_muscle"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("exercise_id", "muscle_id", name=op.f("pk_exercise_muscle")),
    )
    with op.batch_alter_table("exercise_muscle", schema=None) as batch_op:
        batch_op.create_index("ix_exercise_muscle_muscle_id", ["muscle_id"], unique=False)

    op.create_table(
        "exercise_source",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercise.id"],
            name=op.f("fk_exercise_source_exercise_id_exercise"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["source.id"],
            name=op.f("fk_exercise_source_source_id_source"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("exercise_id", "source_id", name=op.f("pk_exercise_source")),
    )
    op.create_table(
        "exercise_tag",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercise.id"],
            name=op.f("fk_exercise_tag_exercise_id_exercise"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"], ["tag.id"], name=op.f("fk_exercise_tag_tag_id_tag"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("exercise_id", "tag_id", name=op.f("pk_exercise_tag")),
    )
    with op.batch_alter_table("exercise_tag", schema=None) as batch_op:
        batch_op.create_index("ix_exercise_tag_tag_id", ["tag_id"], unique=False)

    op.create_table(
        "plan_day_stretch",
        sa.Column("plan_day_id", sa.Integer(), nullable=False),
        sa.Column("stretch_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_day_id"],
            ["plan_day.id"],
            name=op.f("fk_plan_day_stretch_plan_day_id_plan_day"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["stretch_id"],
            ["stretch.id"],
            name=op.f("fk_plan_day_stretch_stretch_id_stretch"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("plan_day_id", "stretch_id", name=op.f("pk_plan_day_stretch")),
    )
    op.create_table(
        "plan_slot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_day_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=True),
        sa.Column("second_exercise_id", sa.Integer(), nullable=True),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("rep_min", sa.Integer(), nullable=False),
        sa.Column("rep_max", sa.Integer(), nullable=False),
        sa.Column(
            "is_optional", sa.Boolean(create_constraint=True, name="is_optional"), nullable=False
        ),
        sa.Column("weekly_weight", sa.Float(), nullable=False),
        sa.Column("locked", sa.Boolean(create_constraint=True, name="locked"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.CheckConstraint("rep_min >= 1 AND rep_max >= rep_min", name=op.f("ck_plan_slot_reps")),
        sa.CheckConstraint(
            "second_exercise_id IS NULL OR second_exercise_id <> exercise_id",
            name=op.f("ck_plan_slot_second_exercise"),
        ),
        sa.CheckConstraint("sets BETWEEN 1 AND 8", name=op.f("ck_plan_slot_sets")),
        sa.CheckConstraint("weekly_weight IN (0.5, 1)", name=op.f("ck_plan_slot_weekly_weight")),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercise.id"],
            name=op.f("fk_plan_slot_exercise_id_exercise"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["family_id"],
            ["movement_family.id"],
            name=op.f("fk_plan_slot_family_id_movement_family"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["plan_day_id"],
            ["plan_day.id"],
            name=op.f("fk_plan_slot_plan_day_id_plan_day"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["second_exercise_id"],
            ["exercise.id"],
            name=op.f("fk_plan_slot_second_exercise_id_exercise"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_slot")),
        sa.UniqueConstraint(
            "plan_day_id", "position", name=op.f("uq_plan_slot_plan_day_id_position")
        ),
    )


def downgrade() -> None:
    op.drop_table("plan_slot")
    op.drop_table("plan_day_stretch")
    with op.batch_alter_table("exercise_tag", schema=None) as batch_op:
        batch_op.drop_index("ix_exercise_tag_tag_id")

    op.drop_table("exercise_tag")
    op.drop_table("exercise_source")
    with op.batch_alter_table("exercise_muscle", schema=None) as batch_op:
        batch_op.drop_index("ix_exercise_muscle_muscle_id")

    op.drop_table("exercise_muscle")
    op.drop_table("slot_template")
    op.drop_table("plan_day")
    with op.batch_alter_table("exercise", schema=None) as batch_op:
        batch_op.drop_index("ix_exercise_secondary_family_id")
        batch_op.drop_index("ix_exercise_primary_family_id")
        batch_op.drop_index("ix_exercise_is_active")

    op.drop_table("exercise")
    op.drop_table("day_template_stretch")
    with op.batch_alter_table("plan", schema=None) as batch_op:
        batch_op.drop_index("uq_plan_single_active", sqlite_where=sa.text("is_active = 1"))

    op.drop_table("plan")
    op.drop_table("muscle")
    op.drop_table("movement_family")
    op.drop_table("day_template")
    op.drop_table("tag")
    op.drop_table("stretch")
    op.drop_table("split_template")
    op.drop_table("source")
    op.drop_table("muscle_group")
    op.drop_table("equipment")
    op.drop_table("daily_routine_item")
    op.drop_table("app_setting")
