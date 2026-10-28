"""Split predefiniti, schede e impostazioni globali (modello dati, § 4 e § 5)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gym_split_planner.db.base import Base
from gym_split_planner.db.models.catalog import Exercise, MovementFamily, StretchExercise
from gym_split_planner.db.types import UtcDateTime, flag, utc_now

_TIMES = "times_per_week BETWEEN 1 AND 3"
_REPS = "rep_min >= 1 AND rep_max >= rep_min"
_WEEKLY_WEIGHT = "weekly_weight IN (0.5, 1)"


# --- Split predefiniti ---------------------------------------------------------


class SplitTemplate(Base):
    """Split predefinito, modello da cui nascono le schede (§ 4.1)."""

    __tablename__ = "split_template"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    is_builtin: Mapped[bool] = mapped_column(flag("is_builtin"))
    sort_order: Mapped[int] = mapped_column(Integer)

    days: Mapped[list["DayTemplate"]] = relationship(
        back_populates="split",
        order_by="DayTemplate.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DayTemplate(Base):
    """Giorno di uno split, ripetuto da 1 a 3 volte a settimana (§ 4.2)."""

    __tablename__ = "day_template"
    __table_args__ = (
        UniqueConstraint("split_id", "code"),
        UniqueConstraint("split_id", "position"),
        CheckConstraint(_TIMES, name="times_per_week"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    split_id: Mapped[int] = mapped_column(ForeignKey("split_template.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer)
    times_per_week: Mapped[int] = mapped_column(Integer)

    split: Mapped[SplitTemplate] = relationship(back_populates="days")
    slots: Mapped[list["SlotTemplate"]] = relationship(
        back_populates="day",
        order_by="SlotTemplate.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    stretches: Mapped[list["DayTemplateStretch"]] = relationship(
        order_by="DayTemplateStretch.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SlotTemplate(Base):
    """Posto di un giorno dello split: chiede una famiglia di movimento (§ 4.3)."""

    __tablename__ = "slot_template"
    __table_args__ = (
        UniqueConstraint("day_id", "position"),
        CheckConstraint("default_sets BETWEEN 1 AND 8", name="default_sets"),
        CheckConstraint(_REPS, name="reps"),
        CheckConstraint(_WEEKLY_WEIGHT, name="weekly_weight"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    day_id: Mapped[int] = mapped_column(ForeignKey("day_template.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    family_id: Mapped[int] = mapped_column(ForeignKey("movement_family.id", ondelete="RESTRICT"))
    default_sets: Mapped[int] = mapped_column(Integer)
    rep_min: Mapped[int] = mapped_column(Integer)
    rep_max: Mapped[int] = mapped_column(Integer)
    is_optional: Mapped[bool] = mapped_column(flag("is_optional"), default=False)
    weekly_weight: Mapped[float] = mapped_column(Float, default=1.0)
    note: Mapped[str | None] = mapped_column(Text)

    day: Mapped[DayTemplate] = relationship(back_populates="slots")
    family: Mapped[MovementFamily] = relationship()


class DayTemplateStretch(Base):
    """Stretching di un giorno dello split (§ 3.8)."""

    __tablename__ = "day_template_stretch"

    day_template_id: Mapped[int] = mapped_column(
        ForeignKey("day_template.id", ondelete="CASCADE"), primary_key=True
    )
    stretch_id: Mapped[int] = mapped_column(
        ForeignKey("stretch.id", ondelete="RESTRICT"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer)

    stretch: Mapped[StretchExercise] = relationship()


# --- Schede ----------------------------------------------------------------------


class Plan(Base):
    """Scheda: istanza indipendente dallo split da cui nasce (§ 4.4, ADR 0006)."""

    __tablename__ = "plan"
    __table_args__ = (
        # Una sola scheda attiva: indice unico parziale (§ 7).
        Index(
            "uq_plan_single_active",
            "is_active",
            unique=True,
            sqlite_where=text("is_active = 1"),
        ),
        CheckConstraint("revision >= 1", name="revision"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    split_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("split_template.id", ondelete="SET NULL")
    )
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(flag("is_active"), default=False)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now, onupdate=utc_now)

    split_template: Mapped[SplitTemplate | None] = relationship()
    days: Mapped[list["PlanDay"]] = relationship(
        back_populates="plan",
        order_by="PlanDay.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PlanDay(Base):
    """Giorno di una scheda (§ 4.5)."""

    __tablename__ = "plan_day"
    __table_args__ = (
        UniqueConstraint("plan_id", "position"),
        CheckConstraint(_TIMES, name="times_per_week"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plan.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer)
    times_per_week: Mapped[int] = mapped_column(Integer)

    plan: Mapped[Plan] = relationship(back_populates="days")
    slots: Mapped[list["PlanSlot"]] = relationship(
        back_populates="day",
        order_by="PlanSlot.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    stretches: Mapped[list["PlanDayStretch"]] = relationship(
        order_by="PlanDayStretch.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PlanSlot(Base):
    """Posto di un giorno della scheda, con l'esercizio scelto (§ 4.6)."""

    __tablename__ = "plan_slot"
    __table_args__ = (
        UniqueConstraint("plan_day_id", "position"),
        CheckConstraint("sets BETWEEN 1 AND 8", name="sets"),
        CheckConstraint(_REPS, name="reps"),
        CheckConstraint(_WEEKLY_WEIGHT, name="weekly_weight"),
        CheckConstraint(
            "second_exercise_id IS NULL OR second_exercise_id <> exercise_id",
            name="second_exercise",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_day_id: Mapped[int] = mapped_column(ForeignKey("plan_day.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    family_id: Mapped[int] = mapped_column(ForeignKey("movement_family.id", ondelete="RESTRICT"))
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercise.id", ondelete="RESTRICT"))
    second_exercise_id: Mapped[int | None] = mapped_column(
        ForeignKey("exercise.id", ondelete="RESTRICT")
    )
    sets: Mapped[int] = mapped_column(Integer)
    rep_min: Mapped[int] = mapped_column(Integer)
    rep_max: Mapped[int] = mapped_column(Integer)
    is_optional: Mapped[bool] = mapped_column(flag("is_optional"), default=False)
    weekly_weight: Mapped[float] = mapped_column(Float, default=1.0)
    locked: Mapped[bool] = mapped_column(flag("locked"), default=False)
    note: Mapped[str | None] = mapped_column(Text)

    day: Mapped[PlanDay] = relationship(back_populates="slots")
    family: Mapped[MovementFamily] = relationship()
    exercise: Mapped[Exercise | None] = relationship(foreign_keys=[exercise_id])
    second_exercise: Mapped[Exercise | None] = relationship(foreign_keys=[second_exercise_id])


class PlanDayStretch(Base):
    """Stretching di un giorno della scheda, copiato dallo split (§ 3.8)."""

    __tablename__ = "plan_day_stretch"

    plan_day_id: Mapped[int] = mapped_column(
        ForeignKey("plan_day.id", ondelete="CASCADE"), primary_key=True
    )
    stretch_id: Mapped[int] = mapped_column(
        ForeignKey("stretch.id", ondelete="RESTRICT"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer)

    stretch: Mapped[StretchExercise] = relationship()


# --- Impostazioni globali ----------------------------------------------------------


class AppSetting(Base):
    """Impostazione globale in JSON (§ 5): pesi, tetto per seduta, durata, RIR…"""

    __tablename__ = "app_setting"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)
