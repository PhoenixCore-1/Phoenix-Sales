"""SQLite persistence adapter for Sales Solutions."""

import json
import sqlite3
from datetime import datetime
from uuid import UUID

from phoenix_sales.domain.solution import Solution, SolutionComponent, SolutionComponentType, SolutionStatus


class SQLiteSolutionRepository:
    """Persist Solutions and their nested components in SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._create_schema()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS solutions (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,
                name TEXT NOT NULL,
                requirement TEXT NOT NULL,
                application TEXT NOT NULL,
                version INTEGER NOT NULL,
                project_id TEXT,
                site_id TEXT,
                technical_parameters TEXT NOT NULL,
                constraints TEXT NOT NULL,
                compliance_requirements TEXT NOT NULL,
                technical_rationale TEXT,
                commercial_rationale TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS solution_components (
                solution_id TEXT NOT NULL,
                component_index INTEGER NOT NULL,
                component_type TEXT NOT NULL,
                item_id TEXT NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                alternative_group TEXT,
                is_recommended INTEGER NOT NULL,
                PRIMARY KEY (solution_id, component_index),
                FOREIGN KEY (solution_id) REFERENCES solutions(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_solutions_tenant_opportunity
                ON solutions(tenant_id, opportunity_id);
            CREATE INDEX IF NOT EXISTS idx_solutions_tenant_id
                ON solutions(tenant_id, id);
            """
        )
        self._connection.commit()

    def save(self, solution: Solution) -> Solution:
        self._connection.execute(
            """
            INSERT INTO solutions (
                id, tenant_id, opportunity_id, name, requirement, application,
                version, project_id, site_id, technical_parameters, constraints,
                compliance_requirements, technical_rationale, commercial_rationale,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                tenant_id=excluded.tenant_id,
                opportunity_id=excluded.opportunity_id,
                name=excluded.name,
                requirement=excluded.requirement,
                application=excluded.application,
                version=excluded.version,
                project_id=excluded.project_id,
                site_id=excluded.site_id,
                technical_parameters=excluded.technical_parameters,
                constraints=excluded.constraints,
                compliance_requirements=excluded.compliance_requirements,
                technical_rationale=excluded.technical_rationale,
                commercial_rationale=excluded.commercial_rationale,
                status=excluded.status,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at
            """,
            self._solution_row(solution),
        )
        self._connection.execute("DELETE FROM solution_components WHERE solution_id = ?", (str(solution.id),))
        self._connection.executemany(
            """
            INSERT INTO solution_components (
                solution_id, component_index, component_type, item_id, description,
                quantity, unit, alternative_group, is_recommended
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(solution.id), index, component.component_type.value,
                    component.item_id, component.description, component.quantity,
                    component.unit, component.alternative_group, int(component.is_recommended),
                )
                for index, component in enumerate(solution.components)
            ],
        )
        self._connection.commit()
        return solution

    def get(self, tenant_id: str, solution_id: UUID) -> Solution | None:
        row = self._connection.execute(
            "SELECT * FROM solutions WHERE tenant_id = ? AND id = ?",
            (tenant_id, str(solution_id)),
        ).fetchone()
        return self._from_row(row) if row else None

    def list_by_opportunity(self, tenant_id: str, opportunity_id: UUID) -> list[Solution]:
        rows = self._connection.execute(
            "SELECT * FROM solutions WHERE tenant_id = ? AND opportunity_id = ? ORDER BY version, created_at",
            (tenant_id, str(opportunity_id)),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, tenant_id: str, solution_id: UUID) -> None:
        self._connection.execute(
            "DELETE FROM solutions WHERE tenant_id = ? AND id = ?",
            (tenant_id, str(solution_id)),
        )
        self._connection.commit()

    @staticmethod
    def _solution_row(solution: Solution) -> tuple:
        return (
            str(solution.id), solution.tenant_id, str(solution.opportunity_id),
            solution.name, solution.requirement, solution.application, solution.version,
            solution.project_id, solution.site_id, json.dumps(solution.technical_parameters),
            json.dumps(solution.constraints), json.dumps(solution.compliance_requirements),
            solution.technical_rationale, solution.commercial_rationale, solution.status.value,
            solution.created_at.isoformat(), solution.updated_at.isoformat(),
        )

    def _from_row(self, row: sqlite3.Row | tuple) -> Solution:
        data = dict(row) if isinstance(row, sqlite3.Row) else {
            "id": row[0], "tenant_id": row[1], "opportunity_id": row[2], "name": row[3],
            "requirement": row[4], "application": row[5], "version": row[6], "project_id": row[7],
            "site_id": row[8], "technical_parameters": row[9], "constraints": row[10],
            "compliance_requirements": row[11], "technical_rationale": row[12],
            "commercial_rationale": row[13], "status": row[14], "created_at": row[15], "updated_at": row[16],
        }
        component_rows = self._connection.execute(
            "SELECT component_type, item_id, description, quantity, unit, alternative_group, is_recommended "
            "FROM solution_components WHERE solution_id = ? ORDER BY component_index",
            (data["id"],),
        ).fetchall()
        components = [
            SolutionComponent(
                component_type=SolutionComponentType(r[0]), item_id=r[1], description=r[2],
                quantity=r[3], unit=r[4], alternative_group=r[5], is_recommended=bool(r[6]),
            )
            for r in component_rows
        ]
        return Solution(
            tenant_id=data["tenant_id"], opportunity_id=UUID(data["opportunity_id"]),
            name=data["name"], requirement=data["requirement"], application=data["application"],
            id=UUID(data["id"]), version=data["version"], project_id=data["project_id"],
            site_id=data["site_id"], technical_parameters=json.loads(data["technical_parameters"]),
            constraints=json.loads(data["constraints"]), compliance_requirements=json.loads(data["compliance_requirements"]),
            components=components, technical_rationale=data["technical_rationale"],
            commercial_rationale=data["commercial_rationale"], status=SolutionStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]), updated_at=datetime.fromisoformat(data["updated_at"]),
        )
