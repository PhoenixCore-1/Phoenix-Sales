from datetime import date
from decimal import Decimal

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.commission import CommissionAdjustment, CommissionPlan, CommissionPlanType, CommissionStatus
from phoenix_sales.persistence.commission_repository import InMemoryCommissionRepository
from phoenix_sales.services.commission import CommissionService


def context(permissions):
    return RequestContext(
        tenant=TenantContext("t1"), user=UserContext("u1"),
        permissions=PermissionContext(frozenset(permissions)), entitlements=frozenset()
    )


def plan():
    return CommissionPlan("t1", "Standard", CommissionPlanType.FIXED_PERCENTAGE,
        date(2026, 1, 1), date(2026, 12, 31), base_rate_percent=Decimal("5"))


def test_plan_and_entry_persist():
    repo = InMemoryCommissionRepository()
    svc = CommissionService(context({"sales.commission.plan.create", "sales.commission.read", "sales.commission.entry.create"}), repo)
    p = svc.create_plan(plan())
    e = svc.calculate_entry("rep1", p.id, Decimal("10000"))
    assert svc.get_plan(p.id).id == p.id
    assert svc.get_entry(e.id).commission_amount == Decimal("500")


def test_tenant_isolation():
    repo = InMemoryCommissionRepository()
    svc = CommissionService(context({"sales.commission.plan.create"}), repo)
    with pytest.raises(PermissionError):
        svc.create_plan(CommissionPlan("t2", "Other", CommissionPlanType.FIXED_PERCENTAGE, date(2026,1,1), date(2026,12,31), base_rate_percent=Decimal("5")))


def test_approval_and_payment_lifecycle():
    repo = InMemoryCommissionRepository()
    permissions = {"sales.commission.plan.create", "sales.commission.entry.create", "sales.commission.read", "sales.commission.approve", "sales.commission.payment"}
    svc = CommissionService(context(permissions), repo)
    e = svc.calculate_entry("rep1", svc.create_plan(plan()).id, Decimal("10000"))
    assert e.status is CommissionStatus.CALCULATED
    svc.approve(e.id)
    svc.mark_payment_pending(e.id)
    svc.mark_paid(e.id)
    assert svc.get_entry(e.id).status is CommissionStatus.PAID


def test_adjustment_updates_entry():
    repo = InMemoryCommissionRepository()
    permissions = {"sales.commission.plan.create", "sales.commission.entry.create", "sales.commission.read", "sales.commission.adjust"}
    svc = CommissionService(context(permissions), repo)
    e = svc.calculate_entry("rep1", svc.create_plan(plan()).id, Decimal("10000"))
    svc.add_adjustment(e.id, CommissionAdjustment(Decimal("-50"), "Customer credit"))
    assert svc.get_entry(e.id).adjusted_amount == Decimal("450")
    assert svc.get_entry(e.id).status is CommissionStatus.ADJUSTED


def test_paid_entry_cannot_be_adjusted():
    repo = InMemoryCommissionRepository()
    permissions = {"sales.commission.plan.create", "sales.commission.entry.create", "sales.commission.read", "sales.commission.approve", "sales.commission.payment", "sales.commission.adjust"}
    svc = CommissionService(context(permissions), repo)
    e = svc.calculate_entry("rep1", svc.create_plan(plan()).id, Decimal("10000"))
    svc.approve(e.id); svc.mark_payment_pending(e.id); svc.mark_paid(e.id)
    with pytest.raises(ValueError):
        svc.add_adjustment(e.id, CommissionAdjustment(Decimal("-10"), "Late credit"))
