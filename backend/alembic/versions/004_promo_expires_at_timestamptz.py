"""promo_codes.expires_at -> timestamptz

Revision ID: 004
Revises: 003
Create Date: 2026-08-24
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing values are UTC-naive; reinterpret them as UTC.
    op.execute(
        """
        ALTER TABLE promo_codes
        ALTER COLUMN expires_at
        TYPE TIMESTAMP WITH TIME ZONE
        USING expires_at AT TIME ZONE 'UTC'
        """
    )


def downgrade() -> None:
    # Strip tz by converting back to naive UTC wall time.
    op.execute(
        """
        ALTER TABLE promo_codes
        ALTER COLUMN expires_at
        TYPE TIMESTAMP WITHOUT TIME ZONE
        USING expires_at AT TIME ZONE 'UTC'
        """
    )
