from datetime import date
from decimal import Decimal

import pytest

from phoenix_sales.domain.target import (
    SalesTarget,
    TargetMetric,
    TargetScopeType,
    TargetStatus,
)


def make_target(**overrides):
    values = {
        "tenant_id": "tenant-1",
        "metric": TargetMetric.REVENUE,
        "scope_type": TargetScopeType.SALESPERSON,
        "scope_id": "rep-1",
        "period_start": date(2026, 9, 1),
        "period_end": date(2026, 9, 30),
        "target_value": Decimal("500000"),
        "currency": "ZAR",
        "owner_id": "manager-1",
    }
    values.update(overrides)
    return SalesTarget(**values)


def test_creates_revenue_target():
    target = make_target()
    assert target.status is TargetStatus.DRAFT
    assert target.version == 1
    assert target.target_value == Decimal("500000")


def test_requires_currency_for_monetary_targets():
    with pytest.raises(ValueError, match="currency is required"):
        make_target(currency=None)


def test_margin_target_is_percentage():
    target = make_target(
        metric=TargetMetric.MARGIN,
        target_value=Decimal("25"),
        currency=None,
    )
    assert target.target_value == Decimal("25")


def test_margin_target_must_be_0_to_100():
    with pytest.raises(ValueError):
        make_target(metric=TargetMetric.MARGIN, target_value=Decimal("101"), currency=None)


def test_quote_conversion_target_must_be_0_to_100():
    with pytest.raises(ValueError):
        make_target(
            metric=TargetMetric.QUOTE_CONVERSION,
            target_value=Decimal("101"),
            currency=None,
        )


def test_rejects_invalid_period():
    with pytest.raises(ValueError, match="period_end"):
        make_target(period_start=date(2026, 10, 1), period_end=date(2026, 9, 30))


def test_rejects_negative_target():
    with pytest.raises(ValueError, match="negative"):
        make_target(target_value=Decimal("-1"))


def test_approval_records_approver_and_time():
    target = make_target()
    target.approve("manager-2")
    assert target.status is TargetStatus.APPROVED
    assert target.approved_by == "manager-2"
    assert target.approved_at is not None


def test_only_draft_can_be_approved():
    target = make_target()
    target.approve("manager-2")
    with pytest.raises(ValueError):
        target.approve("manager-3")


def test_approved_target_can_activate():
    target = make_target()
    target.approve("manager-2")
    target.activate()
    assert target.status is TargetStatus.ACTIVE


def test_active_target_can_close():
    target = make_target()
    target.approve("manager-2")
    target.activate()
    target.close()
    assert target.status is TargetStatus.CLOSED


def test_draft_and_approved_targets_can_cancel():
    draft = make_target()
    draft.cancel()
    assert draft.status is TargetStatus.CANCELLED

    approved = make_target()
    approved.approve("manager-2")
    approved.cancel()
    assert approved.status is TargetStatus.CANCELLED


def test_active_target_is_locked():
    target = make_target()
    target.approve("manager-2")
    target.activate()
    assert target.is_locked is True


def test_target_supports_all_planning_scopes():
    for scope in TargetScopeType:
        target = make_target(scope_type=scope, scope_id=f"{scope.value.lower()}-1")
        assert target.scope_type is scope
