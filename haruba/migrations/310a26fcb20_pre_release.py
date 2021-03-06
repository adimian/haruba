"""pre release

Revision ID: 310a26fcb20
Revises: 
Create Date: 2015-09-30 16:43:51.093624

"""

# revision identifiers, used by Alembic.
revision = '310a26fcb20'
down_revision = None
branch_labels = ('default',)
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('extensions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('extension', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('zone',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('path', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('zone')
    op.drop_table('extensions')
    ### end Alembic commands ###
