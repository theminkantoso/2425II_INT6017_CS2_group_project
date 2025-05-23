"""<your_message>

Revision ID: 2b40af49af5f
Revises: 
Create Date: 2025-04-23 23:56:44.338132

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2b40af49af5f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "image_cache",
        sa.Column("hash_id", sa.String(length=255), nullable=False),
        sa.Column("pdf_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("hash_id", name=op.f("pk_image_cache")),
    )
    op.create_table(
        "item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_item")),
    )
    op.create_table(
        "text_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("text_encode", sa.Text(), nullable=False),
        sa.Column("pdf_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_text_cache")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("text_cache")
    op.drop_table("item")
    op.drop_table("image_cache")
    # ### end Alembic commands ###
