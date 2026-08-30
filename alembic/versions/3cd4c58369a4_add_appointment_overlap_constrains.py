"""add appointment overlap constrains

Revision ID: 3cd4c58369a4
Revises: e449e31e7497
Create Date: 2026-08-29 00:06:47.724281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '3cd4c58369a4'
down_revision: Union[str, Sequence[str], None] = 'e449e31e7497'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS btree_gist"
    )

    op.execute("""
        ALTER TABLE appointments
        ADD CONSTRAINT no_barber_appointment_overlap
        EXCLUDE USING gist (
            barber_id WITH =,
            tstzrange(start_at, end_at, '[)') WITH &&
        )
        WHERE (status = 'CONFIRMED')
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE appointments
        DROP CONSTRAINT no_barber_appointment_overlap
    """)