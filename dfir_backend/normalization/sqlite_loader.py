"""Starter script to load flattened CSV events into SQLite tables.

This script is intentionally minimal and focuses on structure. Future work will
add schema creation, batching, and normalization logic that aligns with the
Phase 1 event schema.
"""

import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence


# TODO: move table/column definitions to a shared schema module
DEFAULT_TABLE = "normalized_events"


def create_table(conn: sqlite3.Connection, columns: Sequence[str]) -> None:
    """Create a table with basic TEXT columns for flattened data."""
    placeholders = ", ".join(f"{col} TEXT" for col in columns)
    conn.execute(f"CREATE TABLE IF NOT EXISTS {DEFAULT_TABLE} ({placeholders});")


def insert_rows(conn: sqlite3.Connection, columns: Sequence[str], rows: Iterable[Sequence[str]]) -> None:
    """Insert rows into the SQLite table."""
    placeholders = ", ".join(["?"] * len(columns))
    conn.executemany(f"INSERT INTO {DEFAULT_TABLE} ({', '.join(columns)}) VALUES ({placeholders});", rows)
    conn.commit()


def load_csv(path: Path):
    """Yield rows from a CSV file as lists of strings."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        headers = next(reader)
        yield headers
        for row in reader:
            yield row


def main() -> None:
    parser = argparse.ArgumentParser(description="Load flattened CSV logs into SQLite for analysis.")
    parser.add_argument("csv_path", type=Path, help="Path to flattened CSV file.")
    parser.add_argument("sqlite_path", type=Path, help="Destination SQLite database file.")
    args = parser.parse_args()

    # TODO: integrate with a schema registry so column types and indexes are aligned
    # with the normalization plan (timestamp, actor, ip, action, resource, status).
    rows = load_csv(args.csv_path)
    headers = next(rows)

    conn = sqlite3.connect(args.sqlite_path)
    try:
        create_table(conn, headers)
        insert_rows(conn, headers, rows)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
