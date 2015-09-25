"""empty message

Revision ID: 4dd09c440a0c
Revises: 59a9afbe4456
Create Date: 2015-09-21 20:51:58.823479

"""

# revision identifiers, used by Alembic.
revision = '4dd09c440a0c'
down_revision = '59a9afbe4456'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('contacts',
    sa.Column('contact_id', sa.Integer(), nullable=True),
    sa.Column('address_detail_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['address_detail_id'], ['address_detail.id'], ),
    sa.ForeignKeyConstraint(['contact_id'], ['contact.id'], )
    )
    op.drop_constraint(u'address_detail_ibfk_2', 'address_detail', type_='foreignkey')
    op.drop_column('address_detail', 'contact_id')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('address_detail', sa.Column('contact_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.create_foreign_key(u'address_detail_ibfk_2', 'address_detail', 'contact', ['contact_id'], ['id'])
    op.drop_table('contacts')
    ### end Alembic commands ###