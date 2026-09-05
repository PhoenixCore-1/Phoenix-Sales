"""Application service for Sales Targets."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.target import SalesTarget, TargetScopeType, TargetStatus
from phoenix_sales.persistence.target_repository import SalesTargetRepository


class SalesTargetService:
    CREATE_PERMISSION = "sales.target.create"
    READ_PERMISSION = "sales.target.read"
    UPDATE_PERMISSION = "sales.target.update"
    APPROVE_PERMISSION = "sales.target.approve"
    ACTIVATE_PERMISSION = "sales.target.activate"
    CLOSE_PERMISSION = "sales.target.close"
    CANCEL_PERMISSION = "sales.target.cancel"

    def __init__(self, context: RequestContext, repository: SalesTargetRepository) -> None:
        self.context = context
        self.repository = repository

    def create(self, target: SalesTarget) -> SalesTarget:
        self._require(self.CREATE_PERMISSION)
        self._tenant(target.tenant_id)
        if self.repository.get(target.tenant_id, target.id) is not None:
            raise ValueError("target already exists")
        self.repository.save(target)
        return target

    def get(self, target_id: UUID) -> SalesTarget:
        self._require(self.READ_PERMISSION)
        target = self._get(target_id)
        return target

    def list_by_scope(self, scope_type: TargetScopeType, scope_id: str) -> list[SalesTarget]:
        self._require(self.READ_PERMISSION)
        return self.repository.list_by_scope(self.context.tenant.tenant_id, scope_type.value, scope_id)

    def list_by_period(self, period_start: date, period_end: date) -> list[SalesTarget]:
        self._require(self.READ_PERMISSION)
        if period_end < period_start:
            raise ValueError("period_end cannot be before period_start")
        return self.repository.list_by_period(self.context.tenant.tenant_id, period_start, period_end)

    def update(self, target_id: UUID, **changes: Any) -> SalesTarget:
        self._require(self.UPDATE_PERMISSION)
        target = self._get(target_id)
        if target.is_locked:
            raise ValueError("locked target cannot be changed")
        protected = {"id", "tenant_id", "status", "approved_by", "approved_at", "created_at", "updated_at"}
        if protected.intersection(changes):
            raise ValueError("protected target fields cannot be changed")
        for key, value in changes.items():
            if not hasattr(target, key):
                raise ValueError(f"unknown target field: {key}")
            setattr(target, key, value)
        target.__post_init__()
        target.updated_at = datetime.now(timezone.utc)
        self.repository.save(target)
        return target

    def approve(self, target_id: UUID) -> SalesTarget:
        self._require(self.APPROVE_PERMISSION)
        target = self._get(target_id)
        target.approve(self.context.user.user_id)
        self.repository.save(target)
        return target

    def activate(self, target_id: UUID) -> SalesTarget:
        self._require(self.ACTIVATE_PERMISSION)
        target = self._get(target_id)
        target.activate()
        self.repository.save(target)
        return target

    def close(self, target_id: UUID) -> SalesTarget:
        self._require(self.CLOSE_PERMISSION)
        target = self._get(target_id)
        target.close()
        self.repository.save(target)
        return target

    def cancel(self, target_id: UUID) -> SalesTarget:
        self._require(self.CANCEL_PERMISSION)
        target = self._get(target_id)
        target.cancel()
        self.repository.save(target)
        return target

    def _get(self, target_id: UUID) -> SalesTarget:
        target = self.repository.get(self.context.tenant.tenant_id, target_id)
        if target is None:
            raise KeyError("target not found")
        return target

    def _tenant(self, tenant_id: str) -> None:
        if tenant_id != self.context.tenant.tenant_id:
            raise PermissionError("cross-tenant access denied")

    def _require(self, permission: str) -> None:
        if not self.context.has_permission(permission):
            raise PermissionError(f"missing permission: {permission}")
