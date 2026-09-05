"""SQLite tenant-scoped persistence for Sales Quotes."""

import sqlite3
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from phoenix_sales.domain.quote import Quote, QuoteLine, QuoteStatus


class SQLiteQuoteRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self._connection.executescript("""
        CREATE TABLE IF NOT EXISTS quotes (
            id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, customer_id TEXT NOT NULL,
            opportunity_id TEXT NOT NULL, quote_number TEXT NOT NULL, currency TEXT NOT NULL,
            valid_until TEXT NOT NULL, contact_id TEXT, project_id TEXT, solution_id TEXT,
            version INTEGER NOT NULL, status TEXT NOT NULL, payment_terms TEXT,
            delivery_terms TEXT, customer_reference TEXT, internal_reference TEXT,
            notes TEXT, branch_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            UNIQUE(tenant_id, quote_number, version)
        );
        CREATE TABLE IF NOT EXISTS quote_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT, quote_id TEXT NOT NULL,
            item_id TEXT NOT NULL, description TEXT NOT NULL, quantity TEXT NOT NULL,
            unit TEXT NOT NULL, unit_price TEXT NOT NULL, discount_percent TEXT NOT NULL,
            unit_cost TEXT, FOREIGN KEY(quote_id) REFERENCES quotes(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_quotes_tenant_customer ON quotes(tenant_id, customer_id);
        CREATE INDEX IF NOT EXISTS idx_quotes_tenant_opportunity ON quotes(tenant_id, opportunity_id);
        CREATE INDEX IF NOT EXISTS idx_quotes_tenant_branch ON quotes(tenant_id, branch_id);
        CREATE INDEX IF NOT EXISTS idx_quote_lines_quote ON quote_lines(quote_id);
        """)
        self._connection.commit()

    def save(self, quote: Quote) -> Quote:
        self._connection.execute("""
            INSERT INTO quotes (id, tenant_id, customer_id, opportunity_id, quote_number, currency,
                valid_until, contact_id, project_id, solution_id, version, status, payment_terms,
                delivery_terms, customer_reference, internal_reference, notes, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET tenant_id=excluded.tenant_id, customer_id=excluded.customer_id,
                opportunity_id=excluded.opportunity_id, quote_number=excluded.quote_number,
                currency=excluded.currency, valid_until=excluded.valid_until, contact_id=excluded.contact_id,
                project_id=excluded.project_id, solution_id=excluded.solution_id, version=excluded.version,
                status=excluded.status, payment_terms=excluded.payment_terms, delivery_terms=excluded.delivery_terms,
                customer_reference=excluded.customer_reference, internal_reference=excluded.internal_reference,
                notes=excluded.notes, branch_id=excluded.branch_id, updated_at=excluded.updated_at
        """, (str(quote.id), quote.tenant_id, quote.customer_id, str(quote.opportunity_id), quote.quote_number,
              quote.currency, quote.valid_until.isoformat(), quote.contact_id, quote.project_id,
              str(quote.solution_id) if quote.solution_id else None, quote.version, quote.status.value,
              quote.payment_terms, quote.delivery_terms, quote.customer_reference, quote.internal_reference,
              quote.notes, quote.branch_id, quote.created_at.isoformat(), quote.updated_at.isoformat()))
        self._connection.execute("DELETE FROM quote_lines WHERE quote_id = ?", (str(quote.id),))
        for line in quote.lines:
            self._connection.execute("""INSERT INTO quote_lines
                (quote_id, item_id, description, quantity, unit, unit_price, discount_percent, unit_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(quote.id), line.item_id, line.description, str(line.quantity), line.unit,
                 str(line.unit_price), str(line.discount_percent),
                 str(line.unit_cost) if line.unit_cost is not None else None))
        self._connection.commit()
        return quote

    def get(self, tenant_id: str, quote_id: UUID) -> Quote | None:
        row = self._connection.execute("SELECT * FROM quotes WHERE tenant_id = ? AND id = ?", (tenant_id, str(quote_id))).fetchone()
        return self._from_row(row) if row else None

    def list_by_customer(self, tenant_id: str, customer_id: str) -> list[Quote]:
        rows = self._connection.execute("SELECT * FROM quotes WHERE tenant_id = ? AND customer_id = ? ORDER BY created_at", (tenant_id, customer_id)).fetchall()
        return [self._from_row(row) for row in rows]

    def list_by_opportunity(self, tenant_id: str, opportunity_id: UUID) -> list[Quote]:
        rows = self._connection.execute("SELECT * FROM quotes WHERE tenant_id = ? AND opportunity_id = ? ORDER BY version", (tenant_id, str(opportunity_id))).fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, tenant_id: str, quote_id: UUID) -> None:
        self._connection.execute("DELETE FROM quotes WHERE tenant_id = ? AND id = ?", (tenant_id, str(quote_id)))
        self._connection.commit()

    def _from_row(self, row: sqlite3.Row) -> Quote:
        line_rows = self._connection.execute("SELECT * FROM quote_lines WHERE quote_id = ? ORDER BY id", (row["id"],)).fetchall()
        lines = [QuoteLine(row["item_id"], row["description"], Decimal(row["quantity"]), row["unit"], Decimal(row["unit_price"]), Decimal(row["discount_percent"]), Decimal(row["unit_cost"]) if row["unit_cost"] is not None else None) for row in line_rows]
        return Quote(
            tenant_id=row["tenant_id"], customer_id=row["customer_id"], opportunity_id=UUID(row["opportunity_id"]),
            quote_number=row["quote_number"], currency=row["currency"], valid_until=date.fromisoformat(row["valid_until"]),
            id=UUID(row["id"]), contact_id=row["contact_id"], project_id=row["project_id"],
            solution_id=UUID(row["solution_id"]) if row["solution_id"] else None, version=row["version"],
            status=QuoteStatus(row["status"]), payment_terms=row["payment_terms"], delivery_terms=row["delivery_terms"],
            customer_reference=row["customer_reference"], internal_reference=row["internal_reference"], notes=row["notes"],
            branch_id=row["branch_id"], lines=lines, created_at=datetime.fromisoformat(row["created_at"]), updated_at=datetime.fromisoformat(row["updated_at"]),
        )
