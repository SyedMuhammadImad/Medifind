"""Reviewed name spellings; no clinical relationships or inventory alteration."""

from alembic import op

revision = "0003_p2_aliases"
down_revision = "0002_p1_core"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE name_aliases (
        id uuid PRIMARY KEY,
        normalized_name text NOT NULL UNIQUE
          CHECK(length(btrim(normalized_name)) BETWEEN 1 AND 200),
        alias text NOT NULL CHECK(length(btrim(alias)) BETWEEN 1 AND 200),
        alias_type text NOT NULL
          CHECK(alias_type IN ('ingredient_abbreviation','combination_abbreviation')),
        language text NOT NULL CHECK(language='en'),
        source_sha256 varchar(64) NOT NULL REFERENCES source_artifacts(sha256),
        review_status text NOT NULL CHECK(review_status='approved_source_spelling_not_clinical'),
        provenance jsonb NOT NULL CHECK(jsonb_typeof(provenance)='object'),
        reviewed_at timestamptz NOT NULL,
        imported_at timestamptz NOT NULL DEFAULT clock_timestamp())""")
    op.execute("""CREATE TABLE name_alias_targets (
        alias_id uuid NOT NULL REFERENCES name_aliases(id) ON DELETE CASCADE,
        product_id uuid NOT NULL REFERENCES products(id),
        PRIMARY KEY(alias_id,product_id))""")
    op.execute("CREATE INDEX alias_targets_product_idx ON name_alias_targets(product_id)")


def downgrade():
    op.drop_table("name_alias_targets")
    op.drop_table("name_aliases")
