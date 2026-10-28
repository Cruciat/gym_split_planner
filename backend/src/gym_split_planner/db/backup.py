"""Backup giornaliero del database SQLite (ADR 0003, NF5).

Usa l'API di backup di SQLite (la stessa di ``.backup`` nella riga di comando):
la copia è coerente anche mentre l'app scrive. Un backup al giorno, con la data nel
nome; si conservano gli ultimi ``keep``.
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy.engine import make_url

logger = logging.getLogger(__name__)

PREFIX = "gym_split_planner-"
SUFFIX = ".db"


@dataclass(frozen=True)
class BackupResult:
    """Esito di un controllo giornaliero."""

    created: Path | None
    """Backup creato ora, ``None`` se quello del giorno c'era già."""
    removed: tuple[Path, ...]
    """Backup più vecchi eliminati dalla rotazione."""


def sqlite_path(database_url: str) -> Path | None:
    """Percorso del file SQLite, ``None`` se il database non è un file SQLite."""
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or url.database in (None, "", ":memory:"):
        return None
    return Path(url.database)


def backup_name(day: date) -> str:
    return f"{PREFIX}{day.isoformat()}{SUFFIX}"


def list_backups(backup_dir: Path) -> list[Path]:
    """Backup presenti, dal più vecchio al più recente (l'ordine dei nomi è quello delle date)."""
    if not backup_dir.is_dir():
        return []
    return sorted(backup_dir.glob(f"{PREFIX}????-??-??{SUFFIX}"))


def create_backup(database: Path, destination: Path) -> None:
    """Copia coerente del database in ``destination`` (scritta prima in un file temporaneo)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(".partial")
    source = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        target = sqlite3.connect(partial)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
    partial.replace(destination)


def run_daily_backup(database: Path, backup_dir: Path, today: date, keep: int) -> BackupResult:
    """Crea il backup del giorno se manca, poi elimina i più vecchi oltre ``keep``."""
    destination = backup_dir / backup_name(today)
    created: Path | None = None
    if not destination.exists() and database.exists():
        create_backup(database, destination)
        created = destination
        logger.info("Backup del database creato: %s", destination)

    backups = list_backups(backup_dir)
    removed = tuple(backups[: max(len(backups) - keep, 0)])
    for old in removed:
        old.unlink()
        logger.info("Backup eliminato dalla rotazione: %s", old)
    return BackupResult(created=created, removed=removed)
