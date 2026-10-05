"""P1 catalog, pharmacy ownership, opaque sessions and revision-protected stock."""

from alembic import op

revision = "0002_p1_core"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

DDL = [
    """CREATE TABLE currencies (
        code varchar(3) PRIMARY KEY CHECK(code ~ '^[A-Z]{3}$'),
        name text NOT NULL CHECK(length(btrim(name))>0))""",
    "INSERT INTO currencies(code,name) VALUES ('PKR','Pakistan rupee')",
    """CREATE TABLE source_artifacts (
        sha256 varchar(64) PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
        metadata jsonb NOT NULL CHECK (jsonb_typeof(metadata)='object'))""",
    """CREATE TABLE catalog_imports (
        id uuid PRIMARY KEY, manifest_hash varchar(64) NOT NULL UNIQUE
          CHECK (manifest_hash ~ '^[0-9a-f]{64}$'),
        document jsonb NOT NULL CHECK (jsonb_typeof(document)='object'),
        imported_at timestamptz NOT NULL DEFAULT clock_timestamp())""",
    """CREATE TABLE products (
        id uuid PRIMARY KEY,
        identity_hash varchar(64) NOT NULL UNIQUE CHECK (identity_hash ~ '^[0-9a-f]{64}$'),
        brand_name text NOT NULL CHECK (length(btrim(brand_name)) BETWEEN 1 AND 200),
        dosage_form text CHECK (dosage_form IS NULL OR
          length(btrim(dosage_form)) BETWEEN 1 AND 200),
        route text CHECK (route IS NULL OR length(btrim(route)) BETWEEN 1 AND 200),
        release_type text CHECK (release_type IS NULL OR
          length(btrim(release_type)) BETWEEN 1 AND 200),
        manufacturer text CHECK (manufacturer IS NULL OR
          length(btrim(manufacturer)) BETWEEN 1 AND 300),
        manufactured_for text CHECK (manufactured_for IS NULL OR
          length(btrim(manufactured_for)) BETWEEN 1 AND 300),
        pack_amount numeric, pack_unit text,
        CHECK ((pack_amount IS NULL AND pack_unit IS NULL) OR
          (pack_amount IS NOT NULL AND pack_unit IS NOT NULL AND pack_amount>0
            AND pack_amount NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
            AND length(btrim(pack_unit)) BETWEEN 1 AND 80)),
        page_sha256 varchar(64) NOT NULL REFERENCES source_artifacts(sha256),
        leaflet_sha256 varchar(64) NOT NULL REFERENCES source_artifacts(sha256),
        import_id uuid NOT NULL REFERENCES catalog_imports(id),
        source_record jsonb NOT NULL CHECK (jsonb_typeof(source_record)='object'),
        collected_at timestamptz NOT NULL,
        review_status text NOT NULL
          CHECK (review_status='source_transcription_not_clinical_review'),
        imported_at timestamptz NOT NULL DEFAULT clock_timestamp())""",
    """CREATE TABLE product_ingredients (
        product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        position integer NOT NULL CHECK(position>=0),
        name text NOT NULL CHECK(length(btrim(name)) BETWEEN 1 AND 200),
        salt_basis text CHECK(salt_basis IS NULL OR length(btrim(salt_basis)) BETWEEN 1 AND 200),
        amount numeric NOT NULL CHECK(amount>0 AND
          amount NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)),
        unit text NOT NULL CHECK(length(btrim(unit)) BETWEEN 1 AND 80),
        per_amount numeric NOT NULL CHECK(per_amount>0 AND
          per_amount NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)),
        per_unit text NOT NULL CHECK(length(btrim(per_unit)) BETWEEN 1 AND 80),
        PRIMARY KEY(product_id,position))""",
    """CREATE TABLE pharmacies (
        id uuid PRIMARY KEY,
        name text NOT NULL CHECK(length(btrim(name)) BETWEEN 1 AND 200),
        location_label text NOT NULL CHECK(length(btrim(location_label)) BETWEEN 1 AND 400),
        latitude numeric NOT NULL CHECK(latitude BETWEEN -90 AND 90),
        longitude numeric NOT NULL CHECK(longitude BETWEEN -180 AND 180),
        active boolean NOT NULL DEFAULT true, synthetic boolean NOT NULL DEFAULT true,
        revision bigint NOT NULL DEFAULT 1 CHECK(revision>0),
        created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT clock_timestamp())""",
    """CREATE TABLE pharmacy_users (
        id uuid PRIMARY KEY, pharmacy_id uuid NOT NULL REFERENCES pharmacies(id),
        username text NOT NULL UNIQUE CHECK(username ~ '^[a-z0-9][a-z0-9_.@+-]{2,79}$'),
        password_hash text NOT NULL CHECK(password_hash LIKE '$argon2id$%'),
        active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT clock_timestamp())""",
    """CREATE TABLE browser_sessions (
        token_hash varchar(64) PRIMARY KEY CHECK(token_hash ~ '^[0-9a-f]{64}$'),
        user_id uuid NOT NULL REFERENCES pharmacy_users(id) ON DELETE CASCADE,
        csrf_token varchar(64) NOT NULL CHECK(length(csrf_token)>=32),
        created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
        expires_at timestamptz NOT NULL CHECK(expires_at>created_at))""",
    """CREATE TABLE login_limits (
        key varchar(64) PRIMARY KEY CHECK(key ~ '^[0-9a-f]{64}$'),
        attempts integer NOT NULL CHECK(attempts>0), reset_at timestamptz NOT NULL)""",
    """CREATE TABLE inventory (
        id uuid PRIMARY KEY,
        pharmacy_id uuid NOT NULL REFERENCES pharmacies(id),
        product_id uuid NOT NULL REFERENCES products(id),
        quantity integer NOT NULL CHECK(quantity>=0),
        price numeric(12,2) NOT NULL CHECK(price>=0 AND price<='9999999999.99'::numeric
          AND price NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)),
        currency varchar(3) NOT NULL REFERENCES currencies(code) CHECK(currency ~ '^[A-Z]{3}$'),
        sale_basis text NOT NULL CHECK(sale_basis IN ('pack','unit')),
        stock_confirmed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
        revision bigint NOT NULL DEFAULT 1 CHECK(revision>0),
        created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
        UNIQUE(pharmacy_id,product_id))""",
    "CREATE INDEX products_page_idx ON products(page_sha256)",
    "CREATE INDEX products_leaflet_idx ON products(leaflet_sha256)",
    "CREATE INDEX products_import_idx ON products(import_id)",
    "CREATE INDEX users_pharmacy_idx ON pharmacy_users(pharmacy_id)",
    "CREATE INDEX sessions_user_idx ON browser_sessions(user_id)",
    "CREATE INDEX sessions_expiry_idx ON browser_sessions(expires_at)",
    "CREATE INDEX inventory_product_idx ON inventory(product_id)",
    "CREATE INDEX inventory_currency_idx ON inventory(currency)",
]


def upgrade():
    for statement in DDL:
        op.execute(statement)


def downgrade():
    for name in (
        "inventory",
        "login_limits",
        "browser_sessions",
        "pharmacy_users",
        "pharmacies",
        "product_ingredients",
        "products",
        "catalog_imports",
        "source_artifacts",
        "currencies",
    ):
        op.drop_table(name)
