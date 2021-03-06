"""empty message

Revision ID: cf01d7b9f9ea
Revises: 0c38eeb84e2f
Create Date: 2020-03-25 14:36:20.707635

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf01d7b9f9ea'
down_revision = '0c38eeb84e2f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venues', sa.Column('seeking_description', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venues', 'seeking_description')
    # ### end Alembic commands ###
