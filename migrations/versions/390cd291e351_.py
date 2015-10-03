"""empty message

Revision ID: 390cd291e351
Revises: 40c4b156b2ae
Create Date: 2015-10-03 17:59:55.841403

"""

# revision identifiers, used by Alembic.
revision = '390cd291e351'
down_revision = '40c4b156b2ae'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('nmap_report_meta', sa.Column('report_finished', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('nmap_report_meta', 'report_finished')
    ### end Alembic commands ###
