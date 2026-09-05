from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.api.reporting import (
    ListPipelineLeakageQuery,
    ListReportValuesQuery,
    ListTargetActualQuery,
    RecordPipelineLeakageCommand,
    RecordReportValueCommand,
    ReportingApplication,
)
from phoenix_sales.domain.reporting import (
    PipelineLeakageSnapshot,
    ReportFilter,
    ReportValue,
    SalesReportDimension,
    SalesReportMetric,
    TargetActualVariance,
)
from phoenix_sales.persistence.reporting_repository import InMemoryReportingRepository
from phoenix_sales.services.reporting import ReportingService


def context(tenant="t1", permissions=frozenset({"sales.reporting.read", "sales.reporting.snapshot"})):
    return RequestContext(
        tenant=TenantContext(tenant),
        user=UserContext("u1"),
        permissions=PermissionContext(permissions),
        entitlements=frozenset(),
    )


def app(tenant="t1", permissions=frozenset({"sales.reporting.read", "sales.reporting.snapshot"})):
    return ReportingApplication(ReportingService(context(tenant, permissions), InMemoryReportingRepository()))


def test_record_and_list_report_values():
    repository = InMemoryReportingRepository()
    service = ReportingService(context(), repository)
    value = ReportValue(
        tenant_id="t1", metric=SalesReportMetric.REVENUE, value=Decimal("1000"),
        dimension=SalesReportDimension.BRANCH, dimension_id="b1", currency="ZAR"
    )
    service.record_value(value)
    assert service.list_values(ReportFilter(tenant_id="t1")) == [value]


def test_application_records_pipeline_leakage():
    repository = InMemoryReportingRepository()
    application = ReportingApplication(ReportingService(context(), repository))
    snapshot = PipelineLeakageSnapshot(tenant_id="t1", opportunity_id=uuid4(), estimated_value=Decimal("1000"))
    application.record_pipeline_leakage(RecordPipelineLeakageCommand(snapshot))
    assert application.list_pipeline_leakage(ListPipelineLeakageQuery("t1")) == [snapshot]


def test_target_actual_is_tenant_scoped():
    repository = InMemoryReportingRepository()
    service = ReportingService(context(), repository)
    result = TargetActualVariance(
        tenant_id="t1", target_value=Decimal("100"), actual_value=Decimal("90"),
        period_start=date(2026, 9, 1), period_end=date(2026, 9, 30),
        metric=SalesReportMetric.REVENUE, currency="ZAR"
    )
    service.record_target_actual(result)
    assert service.list_target_actual("t1") == [result]
    with pytest.raises(PermissionError):
        service.list_target_actual("t2")


def test_read_permission_required():
    repository = InMemoryReportingRepository()
    service = ReportingService(context(permissions=frozenset()), repository)
    with pytest.raises(PermissionError, match="sales.reporting.read"):
        service.list_values(ReportFilter(tenant_id="t1"))


def test_snapshot_permission_required():
    repository = InMemoryReportingRepository()
    service = ReportingService(context(permissions=frozenset({"sales.reporting.read"})), repository)
    value = ReportValue(tenant_id="t1", metric=SalesReportMetric.REVENUE, value=Decimal("100"))
    with pytest.raises(PermissionError, match="sales.reporting.snapshot"):
        service.record_value(value)


def test_cross_tenant_write_rejected():
    repository = InMemoryReportingRepository()
    service = ReportingService(context(), repository)
    value = ReportValue(tenant_id="t2", metric=SalesReportMetric.REVENUE, value=Decimal("100"))
    with pytest.raises(PermissionError, match="Cross-tenant"):
        service.record_value(value)


def test_pipeline_date_range_validated():
    repository = InMemoryReportingRepository()
    service = ReportingService(context(), repository)
    with pytest.raises(ValueError, match="observed_to"):
        service.list_pipeline_leakage("t1", observed_from=date(2026, 9, 30), observed_to=date(2026, 9, 1))
