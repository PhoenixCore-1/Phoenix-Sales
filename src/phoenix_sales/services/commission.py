"""Application boundary for Basic Commissions."""

from __future__ import annotations

from uuid import UUID

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.commission import CommissionEntry, CommissionPlan, CommissionStatus
from phoenix_sales.persistence.commission_repository import CommissionRepository


class CommissionService:
    CREATE_PLAN = "sales.commission.plan.create"
    READ = "sales.commission.read"
    CREATE_ENTRY = "sales.commission.entry.create"
    UPDATE = "sales.commission.update"
    APPROVE = "sales.commission.approve"
    PAYMENT = "sales.commission.payment"
    ADJUST = "sales.commission.adjust"

    def __init__(self, context: RequestContext, repository: CommissionRepository) -> None:
        self.context = context
        self.repository = repository

    def create_plan(self, plan: CommissionPlan) -> CommissionPlan:
        self._require(self.CREATE_PLAN)
        self._tenant(plan.tenant_id)
        if self.repository.get_plan(plan.tenant_id, plan.id) is not None:
            raise ValueError("commission plan already exists")
        self.repository.save_plan(plan)
        return plan

    def get_plan(self, plan_id: UUID) -> CommissionPlan:
        self._require(self.READ)
        plan = self.repository.get_plan(self.context.tenant.tenant_id, plan_id)
        if plan is None:
            raise KeyError("commission plan not found")
        return plan

    def list_plans(self) -> list[CommissionPlan]:
        self._require(self.READ)
        return self.repository.list_plans(self.context.tenant.tenant_id)

    def calculate_entry(self, salesperson_id: str, plan_id: UUID, basis) -> CommissionEntry:
        self._require(self.CREATE_ENTRY)
        plan = self.get_plan(plan_id)
        amount = plan.calculate(basis)
        entry = CommissionEntry(
            tenant_id=self.context.tenant.tenant_id,
            salesperson_id=salesperson_id,
            plan_id=plan.id,
            period_start=plan.period_start,
            period_end=plan.period_end,
            basis=basis,
            commission_amount=amount,
            status=CommissionStatus.CALCULATED,
        )
        self.repository.save_entry(entry)
        return entry

    def get_entry(self, entry_id: UUID) -> CommissionEntry:
        self._require(self.READ)
        entry = self.repository.get_entry(self.context.tenant.tenant_id, entry_id)
        if entry is None:
            raise KeyError("commission entry not found")
        return entry

    def list_entries(self, salesperson_id: str | None = None) -> list[CommissionEntry]:
        self._require(self.READ)
        return self.repository.list_entries(self.context.tenant.tenant_id, salesperson_id)

    def approve(self, entry_id: UUID) -> CommissionEntry:
        self._require(self.APPROVE)
        entry = self.get_entry(entry_id)
        if entry.status not in {CommissionStatus.CALCULATED, CommissionStatus.ADJUSTED}:
            raise ValueError("commission entry is not ready for approval")
        entry.status = CommissionStatus.APPROVED
        self.repository.save_entry(entry)
        return entry

    def mark_payment_pending(self, entry_id: UUID) -> CommissionEntry:
        self._require(self.PAYMENT)
        entry = self.get_entry(entry_id)
        if entry.status is not CommissionStatus.APPROVED:
            raise ValueError("commission entry must be approved before payment")
        entry.status = CommissionStatus.PAYMENT_PENDING
        self.repository.save_entry(entry)
        return entry

    def mark_paid(self, entry_id: UUID) -> CommissionEntry:
        self._require(self.PAYMENT)
        entry = self.get_entry(entry_id)
        if entry.status is not CommissionStatus.PAYMENT_PENDING:
            raise ValueError("commission entry must be payment pending before paid")
        entry.status = CommissionStatus.PAID
        self.repository.save_entry(entry)
        return entry

    def add_adjustment(self, entry_id: UUID, adjustment) -> CommissionEntry:
        self._require(self.ADJUST)
        entry = self.get_entry(entry_id)
        if entry.status in {CommissionStatus.PAID, CommissionStatus.CANCELLED}:
            raise ValueError("paid or cancelled commission cannot be adjusted")
        entry.adjustments.append(adjustment)
        entry.status = CommissionStatus.ADJUSTED
        self.repository.save_entry(entry)
        return entry

    def _tenant(self, tenant_id: str) -> None:
        if tenant_id != self.context.tenant.tenant_id:
            raise PermissionError("cross-tenant access denied")

    def _require(self, permission: str) -> None:
        if not self.context.has_permission(permission):
            raise PermissionError(f"missing permission: {permission}")
