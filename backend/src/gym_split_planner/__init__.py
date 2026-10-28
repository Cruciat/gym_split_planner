"""Gym Split Planner: banca dati degli esercizi e creazione di schede di allenamento."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gym-split-planner")
except PackageNotFoundError:  # pragma: no cover - solo fuori da un'installazione
    __version__ = "0.0.0"
