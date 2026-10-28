"""Configurazione letta dalle variabili d'ambiente con prefisso ``GSP_``."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Impostazioni di avvio dell'applicazione.

    Sono impostazioni di processo (dove sono i dati, cosa servire). Le impostazioni
    funzionali modificabili dall'interfaccia stanno nel database (`app_setting`).
    """

    model_config = SettingsConfigDict(env_prefix="GSP_")

    database_url: str = "sqlite:///./data/gym_split_planner.db"
    """URL SQLAlchemy del database. Nel container: ``sqlite:////data/gym_split_planner.db``."""

    static_dir: Path | None = None
    """Cartella con il frontend compilato. Se assente, l'app serve solo l'API."""

    skip_seed: bool = False
    """Se vero, al primo avvio non carica i dati iniziali (per importare un'esportazione)."""

    backup_enabled: bool = True
    """Backup giornaliero del database SQLite (ADR 0003)."""

    backup_dir: Path | None = None
    """Cartella dei backup; se assente, ``backups`` accanto al file del database."""

    backup_keep: int = 14
    """Quanti backup giornalieri conservare."""

    backup_check_seconds: int = 3600
    """Ogni quanto controllare se il backup del giorno c'è già."""


@lru_cache
def get_settings() -> Settings:
    """Restituisce le impostazioni, lette una sola volta per processo."""
    return Settings()
