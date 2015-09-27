"""empty message

Revision ID: 54313a77a2c6
Revises: 2ccecb4c1cb2
Create Date: 2015-09-19 17:04:31.524806

"""

# revision identifiers, used by Alembic.
revision = '54313a77a2c6'
down_revision = '2ccecb4c1cb2'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    ### end Alembic commands ###
    pass


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reports',
    sa.Column('report_id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('inserted', mysql.DATETIME(), nullable=True),
    sa.Column('report_json', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('report_id'),
    mysql_collate=u'utf8_bin',
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )
    op.create_table('celery_taskmeta',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('task_id', mysql.VARCHAR(collation=u'utf8_bin', length=255), nullable=True),
    sa.Column('status', mysql.VARCHAR(collation=u'utf8_bin', length=50), nullable=True),
    sa.Column('result', sa.BLOB(), nullable=True),
    sa.Column('date_done', mysql.DATETIME(), nullable=True),
    sa.Column('traceback', mysql.TEXT(collation=u'utf8_bin'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate=u'utf8_bin',
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )
    op.create_table('celery_tasksetmeta',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('taskset_id', mysql.VARCHAR(collation=u'utf8_bin', length=255), nullable=True),
    sa.Column('result', sa.BLOB(), nullable=True),
    sa.Column('date_done', mysql.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate=u'utf8_bin',
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )
    ### end Alembic commands ###
