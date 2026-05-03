"""unique email on user

Revision ID: 7720f4b04331
Revises: 754575559a92
Create Date: 2026-05-03 14:21:05.636283

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7720f4b04331'
down_revision = '754575559a92'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_user_email', ['email'])


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_email', type_='unique')
