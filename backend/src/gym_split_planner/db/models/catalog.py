"""Tabelle del catalogo (modello dati, § 3)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gym_split_planner.db.base import Base
from gym_split_planner.db.types import UtcDateTime, flag, text_enum, utc_now
from gym_split_planner.domain.enums import (
    Confidence,
    Kind,
    Level,
    Priority,
    RoutineBlock,
    Stretch,
    TagColor,
    TagEffect,
)


class MuscleGroup(Base):
    """Gruppo muscolare (§ 3.1): petto, spalle, tricipiti…"""

    __tablename__ = "muscle_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    sort_order: Mapped[int] = mapped_column(Integer)

    muscles: Mapped[list["Muscle"]] = relationship(back_populates="group")


class Muscle(Base):
    """Muscolo con priorità e fascia obiettivo del catalogo (§ 3.2)."""

    __tablename__ = "muscle"
    __table_args__ = (
        CheckConstraint(
            "(priority = 'none' AND weekly_min IS NULL AND weekly_max IS NULL)"
            " OR (priority <> 'none' AND weekly_min IS NOT NULL AND weekly_max IS NOT NULL"
            " AND weekly_min >= 0 AND weekly_min < weekly_max)",
            name="band",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    short_name: Mapped[str] = mapped_column(String(40))
    muscle_group_id: Mapped[int] = mapped_column(ForeignKey("muscle_group.id", ondelete="RESTRICT"))
    priority: Mapped[Priority] = mapped_column(text_enum(Priority, "priority"))
    weekly_min: Mapped[float | None] = mapped_column(Float)
    weekly_max: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer)

    group: Mapped[MuscleGroup] = relationship(back_populates="muscles")


class Equipment(Base):
    """Attrezzo (§ 3.3): macchina, cavi, pesi liberi, corpo libero."""

    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    sort_order: Mapped[int] = mapped_column(Integer)


class MovementFamily(Base):
    """Famiglia di movimento: esercizi intercambiabili in uno slot (§ 3.4, ADR 0006)."""

    __tablename__ = "movement_family"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    muscle_group_id: Mapped[int] = mapped_column(ForeignKey("muscle_group.id", ondelete="RESTRICT"))
    sort_order: Mapped[int] = mapped_column(Integer)

    group: Mapped[MuscleGroup] = relationship()


class Exercise(Base):
    """Esercizio del catalogo (§ 3.5)."""

    __tablename__ = "exercise"
    __table_args__ = (
        CheckConstraint(
            "secondary_family_id IS NULL OR secondary_family_id <> primary_family_id",
            name="secondary_family",
        ),
        CheckConstraint("family_rank >= 1", name="family_rank"),
        Index("ix_exercise_primary_family_id", "primary_family_id"),
        Index("ix_exercise_secondary_family_id", "secondary_family_id"),
        Index("ix_exercise_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    primary_family_id: Mapped[int] = mapped_column(
        ForeignKey("movement_family.id", ondelete="RESTRICT")
    )
    secondary_family_id: Mapped[int | None] = mapped_column(
        ForeignKey("movement_family.id", ondelete="SET NULL")
    )
    family_rank: Mapped[int] = mapped_column(Integer)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id", ondelete="RESTRICT"))
    equipment_detail: Mapped[str | None] = mapped_column(String(120))
    kind: Mapped[Kind] = mapped_column(text_enum(Kind, "kind"))
    stretch: Mapped[Stretch] = mapped_column(text_enum(Stretch, "stretch"))
    stretch_note: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[Confidence] = mapped_column(text_enum(Confidence, "confidence"))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(flag("is_active"), default=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now, onupdate=utc_now)

    primary_family: Mapped[MovementFamily] = relationship(foreign_keys=[primary_family_id])
    secondary_family: Mapped[MovementFamily | None] = relationship(
        foreign_keys=[secondary_family_id]
    )
    equipment: Mapped[Equipment] = relationship()
    muscles: Mapped[list["ExerciseMuscle"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan", passive_deletes=True
    )
    tags: Mapped[list["ExerciseTag"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan", passive_deletes=True
    )
    sources: Mapped[list["Source"]] = relationship(secondary="exercise_source")


class ExerciseMuscle(Base):
    """Coinvolgimento di un muscolo in un esercizio, primario o secondario (§ 3.6)."""

    __tablename__ = "exercise_muscle"
    __table_args__ = (Index("ix_exercise_muscle_muscle_id", "muscle_id"),)

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True
    )
    muscle_id: Mapped[int] = mapped_column(
        ForeignKey("muscle.id", ondelete="RESTRICT"), primary_key=True
    )
    level: Mapped[Level] = mapped_column(text_enum(Level, "level"))
    note: Mapped[str | None] = mapped_column(Text)

    exercise: Mapped[Exercise] = relationship(back_populates="muscles")
    muscle: Mapped[Muscle] = relationship()


class Source(Base):
    """Fonte della ricerca (§ 3.7)."""

    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(120))
    url: Mapped[str | None] = mapped_column(String(500))
    reliability: Mapped[str | None] = mapped_column(String(60))
    used_for: Mapped[str | None] = mapped_column(Text)


class ExerciseSource(Base):
    """Collegamento tra esercizio e fonte (§ 3.7)."""

    __tablename__ = "exercise_source"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("source.id", ondelete="CASCADE"), primary_key=True
    )


class Tag(Base):
    """Etichetta con effetto sul punteggio (§ 3.9, ADR 0014)."""

    __tablename__ = "tag"
    __table_args__ = (
        CheckConstraint("points >= 0", name="points_non_negative"),
        CheckConstraint(
            "effect NOT IN ('bonus', 'penalty') OR points > 0", name="points_for_effect"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    symbol: Mapped[str] = mapped_column(String(40))
    color: Mapped[TagColor] = mapped_column(text_enum(TagColor, "color"))
    effect: Mapped[TagEffect] = mapped_column(text_enum(TagEffect, "effect"))
    points: Mapped[float] = mapped_column(Float, default=0)
    show_badge: Mapped[bool] = mapped_column(flag("show_badge"), default=True)
    sort_order: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now, onupdate=utc_now)


class ExerciseTag(Base):
    """Assegnazione di un'etichetta a un esercizio, con nota propria (§ 3.9)."""

    __tablename__ = "exercise_tag"
    __table_args__ = (Index("ix_exercise_tag_tag_id", "tag_id"),)

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True)
    note: Mapped[str | None] = mapped_column(Text)

    exercise: Mapped[Exercise] = relationship(back_populates="tags")
    tag: Mapped[Tag] = relationship()


class StretchExercise(Base):
    """Esercizio di stretching proposto a fine seduta (§ 3.8)."""

    __tablename__ = "stretch"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    targets: Mapped[str] = mapped_column(String(200))
    instructions: Mapped[str | None] = mapped_column(Text)
    dose: Mapped[str] = mapped_column(String(120))
    confidence: Mapped[Confidence | None] = mapped_column(text_enum(Confidence, "confidence"))
    note: Mapped[str | None] = mapped_column(Text)


class DailyRoutineItem(Base):
    """Voce del mini-allenamento quotidiano per collo e bacino (§ 3.8)."""

    __tablename__ = "daily_routine_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    block: Mapped[RoutineBlock] = mapped_column(text_enum(RoutineBlock, "block"))
    position: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(200))
    dose: Mapped[str] = mapped_column(String(120))
    purpose: Mapped[str] = mapped_column(String(200))
    confidence: Mapped[Confidence] = mapped_column(text_enum(Confidence, "confidence"))
