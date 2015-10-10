"""Class User remove now obsolete user_group field (already there as backref)


Revision ID: f88371d8c7e
Revises: 50f4fb2705a5
Create Date: 2015-10-09 20:20:11.414995

"""

# revision identifiers, used by Alembic.
revision = 'f88371d8c7e'
down_revision = '50f4fb2705a5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    pass


def downgrade():
    pass
