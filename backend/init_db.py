from sqlalchemy import inspect

from app.core.database import SessionLocal, engine
from app.models import Base
from app.seed.seed_data import seed_all


def main() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = {
        table.name
        for table in Base.metadata.sorted_tables
    }
    missing_tables = sorted(expected_tables - existing_tables)

    if missing_tables:
        raise RuntimeError(
            "Database schema is not initialized. "
            "Run `alembic upgrade head` first. "
            f"Missing tables: {', '.join(missing_tables)}"
        )

    with SessionLocal() as db:
        seed_all(db)

    print("Seed data inserted.")


if __name__ == "__main__":
    main()
