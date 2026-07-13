"""Initial schema baseline (vacía: valida el pipeline Alembic).

Revision ID: 001_initial
Revises:
Create Date: 2026-07-13

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline: sin tablas aún. Las entidades (tenant, user, …) vendrán después.
    pass


def downgrade() -> None:
    pass
