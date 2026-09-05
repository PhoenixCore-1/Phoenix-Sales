"""SQLite persistence for Sales Orders."""

import json
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from phoenix_sales.domain.sales_order import SalesOrder, SalesOrderLine, SalesOrderStatus


class SQLiteSalesOrderRepository:
    """Tenant-scoped SQLite repository for Sales Orders."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sales_orders (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                order_number TEXT NOT NULL,
                currency TEXT NOT NULL,
                order_date TEXT NOT NULL,
                quote_id TEXT,
                quote_version INTEGER,
                opportunity_id TEXT,
                contact_id TEXT,
                project_id TEXT,
                solution_id TEXT,
                branch_id TEXT,
                status TEXT NOT NULL,
                payment_terms TEXT,
                delivery_terms TEXT,
                customer_reference TEXT,
                internal_reference TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (tenant_id, order_number)
            );
            CREATE TABLE IF NOT EXISTS sales_order_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
                item_id TEXT NOT NULL,
                description TEXT NOT NULL,
                quantity TEXT NOT NULL,
                unit TEXT NOT NULL,
                unit_price TEXT NOT NULL,
                discount_percent TEXT NOT NULL,
                ordered_quantity TEXT,
                allocated_quantity TEXT NOT NULL,
                fulfilled_quantity TEXT NOT NULL,
                backorder_quantity TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sales_orders_tenant_customer ON sales_orders(tenant_id, customer_id);
            CREATE INDEX IF NOT EXISTS idx_sales_orders_tenant_quote ON sales_orders(tenant_id, quote_id);
            CREATE INDEX IF NOT EXISTS idx_sales_orders_tenant_opportunity ON sales_orders(tenant_id, opportunity_id);
            CREATE INDEX IF NOT EXISTS idx_sales_order_lines_order ON sales_order_lines(order_id);
            """
        )
        self._connection.commit()

    def save(self, order: SalesOrder) -> SalesOrder:
        self._connection.execute(
            """
            INSERT INTO sales_orders
            (id, tenant_id, customer_id, order_number, currency, order_date, quote_id,
             quote_version, opportunity_id, contact_id, project_id, solution_id, branch_id,
             status, payment_terms, delivery_terms, customer_reference, internal_reference,
             notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                customer_id=excluded.customer_id, currency=excluded.currency,
                order_date=excluded.order_date, quote_id=excluded.quote_id,
                quote_version=excluded.quote_version, opportunity_id=excluded.opportunity_id,
                contact_id=excluded.contact_id, project_id=excluded.project_id,
                solution_id=excluded.solution_id, branch_id=excluded.branch_id,
                status=excluded.status, payment_terms=excluded.payment_terms,
                delivery_terms=excluded.delivery_terms, customer_reference=excluded.customer_reference,
                internal_reference=excluded.internal_reference, notes=excluded.notes,
                updated_at=excluded.updated_at
            """,
            (
                str(order.id), order.tenant_id, order.customer_id, order.order_number,
                order.currency, order.order_date.isoformat(), str(order.quote_id) if order.quote_id else None,
                order.quote_version, str(order.opportunity_id) if order.opportunity_id else None,
                order.contact_id, order.project_id, str(order.solution_id) if order.solution_id else None,
                order.branch_id, order.status.value, order.payment_terms, order.delivery_terms,
                order.customer_reference, order.internal_reference, order.notes,
                order.created_at.isoformat(), order.updated_at.isoformat(),
            ),
        )
        self._connection.execute("DELETE FROM sales_order_lines WHERE order_id = ?", (str(order.id),))
        for line in order.lines:
            self._connection.execute(
                """
                INSERT INTO sales_order_lines
                (order_id, item_id, description, quantity, unit, unit_price, discount_percent,
                 ordered_quantity, allocated_quantity, fulfilled_quantity, backorder_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(order.id), line.item_id, line.description, str(line.quantity), line.unit,
                    str(line.unit_price), str(line.discount_percent),
                    str(line.ordered_quantity) if line.ordered_quantity is not None else None,
                    str(line.allocated_quantity), str(line.fulfilled_quantity), str(line.backorder_quantity),
                ),
            )
        self._connection.commit()
        return order

    def get(self, tenant_id: str, order_id: UUID) -> SalesOrder | None:
        row = self._connection.execute(
            "SELECT * FROM sales_orders WHERE tenant_id = ? AND id = ?", (tenant_id, str(order_id))
        ).fetchone()
        return self._from_row(row) if row else None

    def list_by_customer(self, tenant_id: str, customer_id: str) -> list[SalesOrder]:
        rows = self._connection.execute(
            "SELECT * FROM sales_orders WHERE tenant_id = ? AND customer_id = ? ORDER BY order_date, order_number",
            (tenant_id, customer_id),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def list_by_quote(self, tenant_id: str, quote_id: UUID) -> list[SalesOrder]:
        rows = self._connection.execute(
            "SELECT * FROM sales_orders WHERE tenant_id = ? AND quote_id = ? ORDER BY order_number",
            (tenant_id, str(quote_id)),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def list_by_opportunity(self, tenant_id: str, opportunity_id: UUID) -> list[SalesOrder]:
        rows = self._connection.execute(
            "SELECT * FROM sales_orders WHERE tenant_id = ? AND opportunity_id = ? ORDER BY order_number",
            (tenant_id, str(opportunity_id)),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, tenant_id: str, order_id: UUID) -> None:
        self._connection.execute(
            "DELETE FROM sales_orders WHERE tenant_id = ? AND id = ?", (tenant_id, str(order_id))
        )
        self._connection.commit()

    def _from_row(self, row: sqlite3.Row | tuple) -> SalesOrder:
        data = dict(row) if isinstance(row, sqlite3.Row) else dict(zip(self._columns(), row))
        lines = self._connection.execute(
            "SELECT item_id, description, quantity, unit, unit_price, discount_percent, ordered_quantity, allocated_quantity, fulfilled_quantity, backorder_quantity FROM sales_order_lines WHERE order_id = ? ORDER BY id",
            (data["id"],),
        ).fetchall()
        return SalesOrder(
            tenant_id=data["tenant_id"], customer_id=data["customer_id"], order_number=data["order_number"],
            currency=data["currency"], order_date=date.fromisoformat(data["order_date"]), id=UUID(data["id"]),
            quote_id=UUID(data["quote_id"]) if data["quote_id"] else None, quote_version=data["quote_version"],
            opportunity_id=UUID(data["opportunity_id"]) if data["opportunity_id"] else None,
            contact_id=data["contact_id"], project_id=data["project_id"],
            solution_id=UUID(data["solution_id"]) if data["solution_id"] else None, branch_id=data["branch_id"],
            status=SalesOrderStatus(data["status"]), payment_terms=data["payment_terms"],
            delivery_terms=data["delivery_terms"], customer_reference=data["customer_reference"],
            internal_reference=data["internal_reference"], notes=data["notes"],
            lines=[SalesOrderLine(item_id=r[0], description=r[1], quantity=Decimal(r[2]), unit=r[3], unit_price=Decimal(r[4]), discount_percent=Decimal(r[5]), ordered_quantity=Decimal(r[6]) if r[6] is not None else None, allocated_quantity=Decimal(r[7]), fulfilled_quantity=Decimal(r[8]), backorder_quantity=Decimal(r[9])) for r in lines],
            created_at=datetime.fromisoformat(data["created_at"]), updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    @staticmethod
    def _columns() -> list[str]:
        return ["id", "tenant_id", "customer_id", "order_number", "currency", "order_date", "quote_id", "quote_version", "opportunity_id", "contact_id", "project_id", "solution_id", "branch_id", "status", "payment_terms", "delivery_terms", "customer_reference", "internal_reference", "notes", "created_at", "updated_at"]
