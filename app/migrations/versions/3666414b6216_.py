"""empty message

Revision ID: 3666414b6216
Revises: 863b3ba12758
Create Date: 2020-03-29 00:06:40.536473

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3666414b6216'
down_revision = '863b3ba12758'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artists', sa.Column('created_time', sa.DateTime(), nullable=True))
    op.add_column('venues', sa.Column('created_time', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venues', 'created_time')
    op.drop_column('artists', 'created_time')
    # ### end Alembic commands ###
