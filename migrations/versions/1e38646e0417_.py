"""empty message

Revision ID: 1e38646e0417
Revises: 4a9a1dc82e00
Create Date: 2015-10-04 03:08:25.555342

"""

# revision identifiers, used by Alembic.
revision = '1e38646e0417'
down_revision = '4a9a1dc82e00'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('last_login', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'last_login')
    ### end Alembic commands ###
