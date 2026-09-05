from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.domain.commission import (
    CommissionAdjustment,
    CommissionEntry,
    CommissionPlan,
    CommissionPlanType,
    CommissionStatus,
    CommissionTier,
)


def plan(kind, **kwargs):
    return CommissionPlan(
        tenant_id="t1", name="Standard", plan_type=kind,
        period_start=date(2026, 1, 1), period_end=date(2026, 12, 31), **kwargs
    )


def test_fixed_percentage():
    assert plan(CommissionPlanType.FIXED_PERCENTAGE, base_rate_percent=Decimal("5")).calculate(Decimal("10000")) == Decimal("500")


def test_base_plus_accelerator():
    p = plan(CommissionPlanType.BASE_PLUS_ACCELERATOR, base_rate_percent=Decimal("5"), accelerator_rate_percent=Decimal("2"), threshold=Decimal("10000"))
    assert p.calculate(Decimal("10000")) == Decimal("700")


def test_tiered_uses_highest_reached_rate():
    p = plan(CommissionPlanType.TIERED, tiers=[CommissionTier(Decimal("0"), Decimal("2")), CommissionTier(Decimal("10000"), Decimal("5"))])
    assert p.calculate(Decimal("20000")) == Decimal("1000")


def test_progressive_tiers():
    p = plan(CommissionPlanType.PROGRESSIVE, tiers=[CommissionTier(Decimal("0"), Decimal("2")), CommissionTier(Decimal("10000"), Decimal("5"))])
    assert p.calculate(Decimal("20000")) == Decimal("700")


def test_negative_basis_rejected():
    p = plan(CommissionPlanType.FIXED_PERCENTAGE, base_rate_percent=Decimal("5"))
    with pytest.raises(ValueError):
        p.calculate(Decimal("-1"))


def test_tiers_must_be_ordered():
    with pytest.raises(ValueError):
        plan(CommissionPlanType.TIERED, tiers=[CommissionTier(Decimal("100"), Decimal("5")), CommissionTier(Decimal("0"), Decimal("2"))])


def test_adjustment_changes_total():
    entry = CommissionEntry("t1", "rep1", uuid4(), date(2026, 1, 1), date(2026, 1, 31), Decimal("10000"), Decimal("500"), adjustments=[CommissionAdjustment(Decimal("-50"), "Credit")])
    assert entry.adjusted_amount == Decimal("450")


def test_adjustment_requires_reason_and_nonzero_amount():
    with pytest.raises(ValueError):
        CommissionAdjustment(Decimal("0"), "x")
    with pytest.raises(ValueError):
        CommissionAdjustment(Decimal("10"), "")


def test_entry_validates_period_and_values():
    with pytest.raises(ValueError):
        CommissionEntry("t1", "rep1", uuid4(), date(2026, 2, 1), date(2026, 1, 1), Decimal("1"), Decimal("1"))
    with pytest.raises(ValueError):
        CommissionEntry("t1", "rep1", uuid4(), date(2026, 1, 1), date(2026, 1, 31), Decimal("-1"), Decimal("1"))
