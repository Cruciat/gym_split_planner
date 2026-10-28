"""Revisione iniziale vuota: punto di partenza delle migrazioni.

Revisione: 0001
Precedente:
Creata il: 2026-10-28
"""

from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
