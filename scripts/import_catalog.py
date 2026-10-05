"""Import the retained qualified sample; never scrape or generate medicine facts."""

import argparse

from medifind.aliases import import_aliases
from medifind.catalog import ImportConflict, import_qualified_expansion, import_qualified_sample
from medifind.config import Settings
from medifind.database import make_engine, readiness
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--p2", action="store_true", help="Import reviewed P2 expansion then its aliases"
    )
    args = parser.parse_args()
    engine = make_engine(Settings().database_url.get_secret_value())
    try:
        if readiness(engine) != "ready":
            raise ValueError("Apply current migrations before catalog import")
        result = import_qualified_expansion(engine) if args.p2 else import_qualified_sample(engine)
        print(f"Catalog import: {result['inserted']} inserted, {result['unchanged']} unchanged.")
        print("Source transcription only; no clinical equivalence or real stock is established.")
        if args.p2:
            aliases = import_aliases(engine)
            print(
                f"Reviewed source aliases: {aliases['inserted']} inserted, "
                f"{aliases['unchanged']} unchanged."
            )
    except (ValidationError, ImportConflict, ValueError, OSError):
        raise SystemExit(
            "Catalog rejected: inspect source qualification/conflicts; nothing overwritten"
        ) from None
    except SQLAlchemyError:
        raise SystemExit(
            "Catalog storage operation failed; no database details displayed"
        ) from None
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
