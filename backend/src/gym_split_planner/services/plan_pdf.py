"""PDF della scheda (US-30; ADR 0008; API, § 6.10; wireframe, § 6).

Qui si prepara tutto ciò che il template mostra, già formattato: il template impagina
e basta. I numeri vengono dalla stessa vista della scheda che usa l'interfaccia
(``build_plan_view``), così schermo e carta non possono divergere.
"""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import Engine, select

from gym_split_planner.db.models import DailyRoutineItem, MuscleGroup
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.pdf.render import render_pdf
from gym_split_planner.services.plan_view import (
    DayData,
    PlanViewData,
    SlotData,
    SlotExerciseData,
    VolumeData,
)
from gym_split_planner.services.plans import get_plan
from gym_split_planner.services.settings import get_settings

TEMPLATE = "plan.html"
DEFAULT_WEEKS = 4

STATUS = {"below": "sotto", "within": "dentro", "above": "sopra"}
EN_DASH = "\N{EN DASH}"  # tra minimo e massimo della fascia, come nell'interfaccia
BLOCKS = {"neck": "Collo", "pelvis": "Bacino"}


@dataclass(frozen=True)
class PdfFile:
    """PDF pronto da scaricare."""

    filename: str
    content: bytes


@dataclass(frozen=True)
class Symbol:
    """Simbolo di un'etichetta accanto a un esercizio, con il richiamo alla nota."""

    icon: str
    name: str
    ref: int | None


@dataclass(frozen=True)
class Row:
    name: str
    symbols: tuple[Symbol, ...]
    optional: bool
    alternate: bool
    second: str | None
    second_symbols: tuple[Symbol, ...]
    note: str | None
    sets: int
    prescription: str
    rir: str
    rest: str
    empty: bool


@dataclass(frozen=True)
class Footnote:
    ref: int
    text: str


@dataclass(frozen=True)
class DayPage:
    name: str
    frequency: str
    minutes: str
    rows: tuple[Row, ...]
    footnotes: tuple[Footnote, ...]
    failure_note: bool
    stretches: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class VolumeRow:
    name: str
    volume: str
    band: str
    status: str
    overridden: bool


@dataclass(frozen=True)
class VolumeGroup:
    name: str
    rows: tuple[VolumeRow, ...]


@dataclass(frozen=True)
class RoutineBlock:
    name: str
    items: tuple[tuple[str, str, str], ...]


# --- Formati -----------------------------------------------------------------------------


def number(value: float) -> str:
    """Numero all'italiana con al più due decimali: ``12,5``."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def rest_text(seconds: int | None) -> str:
    """Recupero breve: ``90″``, ``2′``, ``2′30″``."""
    if seconds is None:
        return "—"
    if seconds < 120:
        return f"{seconds}″"
    minutes, rest = divmod(seconds, 60)
    return f"{minutes}′" if rest == 0 else f"{minutes}′{rest:02d}″"


def slug(text: str) -> str:
    """Nome di file in minuscole e trattini, senza accenti (ADR 0008)."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-") or "scheda"


def filename(plan_name: str, today: date) -> str:
    return f"{slug(plan_name)}-{today.isoformat()}.pdf"


def frequency_text(times: int) -> str:
    return "1 volta a settimana" if times == 1 else f"{times} volte a settimana"


# --- Pagine dei giorni ---------------------------------------------------------------------


class _Notes:
    """Richiami numerati delle note delle etichette di un giorno, senza doppioni."""

    def __init__(self) -> None:
        self.items: dict[str, int] = {}

    def symbols(self, exercise: SlotExerciseData | None) -> tuple[Symbol, ...]:
        if exercise is None:
            return ()
        result = []
        for badge in exercise.badges:
            ref = None
            if badge.note:
                text = f"{badge.name}: {badge.note}"
                ref = self.items.setdefault(text, len(self.items) + 1)
            result.append(Symbol(badge.symbol, badge.name, ref))
        return tuple(result)

    def footnotes(self) -> tuple[Footnote, ...]:
        return tuple(Footnote(ref, text) for text, ref in self.items.items())


def _row(slot: SlotData, notes: _Notes) -> Row:
    exercise = slot.exercise
    rir = slot.rir or "—"
    return Row(
        name=exercise.name if exercise else f"{slot.family.name}: nessun esercizio disponibile",
        symbols=notes.symbols(exercise),
        optional=slot.is_optional,
        alternate=slot.weekly_weight < 1,
        second=slot.second_exercise.name if slot.second_exercise else None,
        second_symbols=notes.symbols(slot.second_exercise),
        note=slot.note,
        sets=slot.sets,
        prescription=f"{slot.sets} × {slot.rep_min}-{slot.rep_max}",
        # Il cedimento all'ultima serie è già deciso dalla vista (impostazioni `effort`).
        rir=f"{rir}*" if slot.last_set_to_failure else rir,
        rest=rest_text(slot.rest_seconds),
        empty=exercise is None,
    )


def day_page(view: PlanViewData, day: DayData) -> DayPage:
    notes = _Notes()
    rows = tuple(_row(slot, notes) for slot in day.slots)
    minutes = [
        s.minutes
        for s in sorted(view.analysis.sessions, key=lambda s: s.session)
        if s.day_id == day.id
    ]
    return DayPage(
        name=day.name,
        frequency=frequency_text(day.times_per_week),
        minutes=" / ".join(f"~{round(m)}" for m in minutes) + " min" if minutes else "",
        rows=rows,
        footnotes=notes.footnotes(),
        failure_note=any(r.rir.endswith("*") for r in rows),
        stretches=tuple((s.name, s.dose) for s in day.stretches),
    )


# --- Pagina finale -------------------------------------------------------------------------


def volume_groups(volumes: Iterable[VolumeData], groups: dict[str, str]) -> tuple[VolumeGroup, ...]:
    """Volumi per gruppo muscolare, nell'ordine dei gruppi del catalogo."""
    by_group: dict[str, list[VolumeRow]] = {code: [] for code in groups}
    for v in volumes:
        band = (
            f"{number(v.weekly_min)}{EN_DASH}{number(v.weekly_max)}"
            if v.weekly_min is not None and v.weekly_max is not None
            else "—"
        )
        row = VolumeRow(
            name=v.name,
            volume=number(v.volume),
            band=band,
            status=STATUS.get(v.status or "", "—"),
            overridden=v.overridden,
        )
        by_group.setdefault(v.group_code, []).append(row)
    return tuple(
        VolumeGroup(groups.get(code, code), tuple(rows)) for code, rows in by_group.items() if rows
    )


def two_columns(
    groups: tuple[VolumeGroup, ...],
) -> tuple[tuple[VolumeGroup, ...], tuple[VolumeGroup, ...]]:
    """I gruppi divisi in due colonne di altezza simile, senza spezzare un gruppo.

    Due tabelle invece di una per gruppo: il riepilogo sta in una pagina e
    l'impaginazione costa meno (meno tabelle da misurare).
    """
    total = sum(len(g.rows) + 1 for g in groups)
    left: list[VolumeGroup] = []
    used = 0
    for group in groups:
        if used >= total / 2:
            break
        left.append(group)
        used += len(group.rows) + 1
    return tuple(left), groups[len(left) :]


def legend(view: PlanViewData) -> tuple[Symbol, ...]:
    """Simboli usati nella scheda, una volta ciascuno."""
    seen: dict[str, Symbol] = {}
    for day in view.days:
        for slot in day.slots:
            for exercise in (slot.exercise, slot.second_exercise):
                for badge in exercise.badges if exercise else ():
                    seen.setdefault(badge.code, Symbol(badge.symbol, badge.name, None))
    return tuple(seen.values())


# --- Documento -----------------------------------------------------------------------------


def plan_context(
    view: PlanViewData,
    settings: dict[str, Any],
    groups: dict[str, str],
    routine: tuple[RoutineBlock, ...],
    weeks: int,
    today: date,
) -> dict[str, Any]:
    """Tutto ciò che serve al template, già formattato."""
    days = tuple(day_page(view, day) for day in view.days)
    return {
        "name": view.name,
        "split": view.split.name if view.split else "Scheda personalizzata",
        "date": today.strftime("%d/%m/%Y"),
        "weeks": weeks,
        "warmup": settings.get("warmup_text", ""),
        "days": days,
        "volume_columns": two_columns(volume_groups(view.analysis.volumes, groups)),
        "legend": legend(view),
        "failure_note": any(d.failure_note for d in days),
        "any_optional": any(r.optional for d in days for r in d.rows),
        "any_overridden": any(v.overridden for v in view.analysis.volumes),
        "routine": routine,
    }


def _catalog_extras(engine: Engine) -> tuple[dict[str, str], tuple[RoutineBlock, ...]]:
    with make_session_factory(engine)() as session:
        groups = dict(
            session.execute(
                select(MuscleGroup.code, MuscleGroup.name).order_by(MuscleGroup.sort_order)
            ).all()
        )
        items = session.scalars(select(DailyRoutineItem).order_by(DailyRoutineItem.position))
        blocks: dict[str, list[tuple[str, str, str]]] = {}
        for item in items:
            blocks.setdefault(item.block.value, []).append((item.name, item.dose, item.purpose))
    routine = tuple(
        RoutineBlock(BLOCKS.get(block, block), tuple(rows)) for block, rows in blocks.items()
    )
    return groups, routine


def plan_pdf(
    engine: Engine, plan_id: int, weeks: int = DEFAULT_WEEKS, today: date | None = None
) -> PdfFile:
    """Il PDF della scheda; ``NotFoundError`` se non esiste."""
    today = today or date.today()
    view = get_plan(engine, plan_id)
    groups, routine = _catalog_extras(engine)
    context = plan_context(view, get_settings(engine), groups, routine, weeks, today)
    return PdfFile(filename=filename(view.name, today), content=render_pdf(TEMPLATE, **context))
