"""new appointments index keys

Revision ID: 02341122aa7e
Revises: 1e783820b6a8
Create Date: 2026-09-16 15:23:28.653651

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "02341122aa7e"
down_revision: Union[str, Sequence[str], None] = "1e783820b6a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_index("ix_customer_id", "appointments", ["customer_id"])
    op.create_index("ix_cleaner_id_status", "appointments", ["cleaner_id", "status"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_customer_id", table_name="appointments")
    op.drop_index("ix_cleaner_id_status", table_name="appointments")
