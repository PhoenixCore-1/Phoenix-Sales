"""SQLite persistence adapter for Sales opportunities."""

import sqlite3
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from phoenix_sales.domain.opportunity import Opportunity, OpportunityStage


class SQLiteOpportunityRepository:
    """Persist opportunities in a tenant-scoped SQLite database."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                owner_user_id TEXT NOT NULL,
                contact_id TEXT,
                requirement TEXT,
                application TEXT,
                estimated_value TEXT,
                estimated_margin TEXT,
                close_date TEXT,
                stage TEXT NOT NULL,
                probability TEXT NOT NULL,
                source TEXT,
                project_id TEXT,
                competitor TEXT,
                current_solution TEXT,
                lost_reason TEXT,
                outcome_reason TEXT,
                deferred_until TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS ix_opportunities_tenant_customer "
            "ON opportunities (tenant_id, customer_id)"
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS ix_opportunities_tenant_owner "
            "ON opportunities (tenant_id, owner_user_id)"
        )
        self._connection.commit()

    def save(self, opportunity: Opportunity) -> Opportunity:
        self._connection.execute(
            """
            INSERT INTO opportunities (
                id, tenant_id, name, customer_id, owner_user_id, contact_id,
                requirement, application, estimated_value, estimated_margin,
                close_date, stage, probability, source, project_id, competitor,
                current_solution, lost_reason, outcome_reason, deferred_until,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                tenant_id=excluded.tenant_id,
                name=excluded.name,
                customer_id=excluded.customer_id,
                owner_user_id=excluded.owner_user_id,
                contact_id=excluded.contact_id,
                requirement=excluded.requirement,
                application=excluded.application,
                estimated_value=excluded.estimated_value,
                estimated_margin=excluded.estimated_margin,
                close_date=excluded.close_date,
                stage=excluded.stage,
                probability=excluded.probability,
                source=excluded.source,
                project_id=excluded.project_id,
                competitor=excluded.competitor,
                current_solution=excluded.current_solution,
                lost_reason=excluded.lost_reason,
                outcome_reason=excluded.outcome_reason,
                deferred_until=excluded.deferred_until,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at
            """,
            self._to_row(opportunity),
        )
        self._connection.commit()
        return opportunity

    def get(self, tenant_id: str, opportunity_id: UUID) -> Opportunity | None:
        row = self._connection.execute(
            "SELECT * FROM opportunities WHERE tenant_id = ? AND id = ?",
            (tenant_id, str(opportunity_id)),
        ).fetchone()
        return self._from_row(row) if row else None

    def list_by_customer(self, tenant_id: str, customer_id: str) -> list[Opportunity]:
        rows = self._connection.execute(
            "SELECT * FROM opportunities WHERE tenant_id = ? AND customer_id = ? ORDER BY created_at",
            (tenant_id, customer_id),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def list_by_owner(self, tenant_id: str, owner_user_id: str) -> list[Opportunity]:
        rows = self._connection.execute(
            "SELECT * FROM opportunities WHERE tenant_id = ? AND owner_user_id = ? ORDER BY created_at",
            (tenant_id, owner_user_id),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, tenant_id: str, opportunity_id: UUID) -> None:
        self._connection.execute(
            "DELETE FROM opportunities WHERE tenant_id = ? AND id = ?",
            (tenant_id, str(opportunity_id)),
        )
        self._connection.commit()

    @staticmethod
    def _to_row(opportunity: Opportunity) -> tuple[object, ...]:
        return (
            str(opportunity.id), opportunity.tenant_id, opportunity.name,
            opportunity.customer_id, opportunity.owner_user_id, opportunity.contact_id,
            opportunity.requirement, opportunity.application,
            str(opportunity.estimated_value) if opportunity.estimated_value is not None else None,
            str(opportunity.estimated_margin) if opportunity.estimated_margin is not None else None,
            opportunity.close_date.isoformat() if opportunity.close_date else None,
            opportunity.stage.value, str(opportunity.probability), opportunity.source,
            opportunity.project_id, opportunity.competitor, opportunity.current_solution,
            opportunity.lost_reason, opportunity.outcome_reason,
            opportunity.deferred_until.isoformat() if opportunity.deferred_until else None,
            opportunity.created_at.isoformat(), opportunity.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Opportunity:
        def dec(value: str | None) -> Decimal | None:
            return Decimal(value) if value is not None else None

        def dt(value: str) -> datetime:
            return datetime.fromisoformat(value)

        def d(value: str | None) -> date | None:
            return date.fromisoformat(value) if value else None

        return Opportunity(
            id=UUID(row["id"]), tenant_id=row["tenant_id"], name=row["name"],
            customer_id=row["customer_id"], owner_user_id=row["owner_user_id"],
            contact_id=row["contact_id"], requirement=row["requirement"],
            application=row["application"], estimated_value=dec(row["estimated_value"]),
            estimated_margin=dec(row["estimated_margin"]), close_date=d(row["close_date"]),
            stage=OpportunityStage(row["stage"]), probability=Decimal(row["probability"]),
            source=row["source"], project_id=row["project_id"], competitor=row["competitor"],
            current_solution=row["current_solution"], lost_reason=row["lost_reason"],
            outcome_reason=row["outcome_reason"], deferred_until=d(row["deferred_until"]),
            created_at=dt(row["created_at"]), updated_at=dt(row["updated_at"]),
        )
