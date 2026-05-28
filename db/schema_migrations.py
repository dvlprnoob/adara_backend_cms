from sqlalchemy import inspect, text


def ensure_installment_due_date_column(engine):
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("installments")}
    if "next_due_date" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE installments ADD COLUMN next_due_date DATE"))


def ensure_progress_warranty_columns(engine):
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("construction_progress")}

    with engine.begin() as connection:
        if "handover_date" not in columns:
            connection.execute(text("ALTER TABLE construction_progress ADD COLUMN handover_date DATE"))
        if "warranty_end_date" not in columns:
            connection.execute(text("ALTER TABLE construction_progress ADD COLUMN warranty_end_date DATE"))


def ensure_payment_rejection_reason_columns(engine):
    inspector = inspect(engine)
    targets = ("ipl", "installments")

    with engine.begin() as connection:
        for table in targets:
            columns = {column["name"] for column in inspector.get_columns(table)}
            if "rejection_reason" not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN rejection_reason VARCHAR"))
