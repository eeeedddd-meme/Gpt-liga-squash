"""Initial league schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(255), unique=True, nullable=False), sa.Column("role", sa.String(32), nullable=False, server_default="player"))

def downgrade():
    op.drop_table("users")
