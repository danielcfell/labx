"""Create patients table (multi-tenant).

Revision ID: 002_patients
Revises: 001_initial
Create Date: 2026-07-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_patients"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("identification", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_patients_tenant_email"),
    )
    op.create_index("ix_patients_tenant_id", "patients", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_patients_tenant_id", table_name="patients")
    op.drop_table("patients")
