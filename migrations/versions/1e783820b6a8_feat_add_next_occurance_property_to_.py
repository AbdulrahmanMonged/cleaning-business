"""feat: add next_occurance_property to appointments

Revision ID: 1e783820b6a8
Revises: 3d93048e2663
Create Date: 2026-08-02 11:44:41.418911

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "1e783820b6a8"
down_revision: Union[str, Sequence[str], None] = "3d93048e2663"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "appointments",
        sa.Column("next_occurence_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "appointments", sa.Column("parent_appointment_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_appointments_parent_appointment_id",
        "appointments",
        "appointments",
        ["parent_appointment_id"],
        ["id"],
    )
    op.create_index(
        "ix_appointments_parent_appointment_id",
        "appointments",
        ["parent_appointment_id"],
    )

    op.create_index(
        "ix_appointments_recurring_due",
        "appointments",
        ["is_recurred", "next_occurence_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_appointments_recurring_due", table_name="appointments")
    op.drop_index("ix_appointments_parent_appointment_id", table_name="appointments")
    op.drop_constraint(
        "fk_appointments_parent_appointment_id", "appointments", type_="foreign_key"
    )
    op.drop_column("appointments", "parent_appointment_id")
    op.drop_column("appointments", "next_occurence_at")
