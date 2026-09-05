"""Sales Order lifecycle rules."""

from phoenix_sales.domain.sales_order import SalesOrderStatus


ALLOWED_TRANSITIONS: dict[SalesOrderStatus, set[SalesOrderStatus]] = {
    SalesOrderStatus.DRAFT: {SalesOrderStatus.CONFIRMED, SalesOrderStatus.CANCELLED},
    SalesOrderStatus.CONFIRMED: {SalesOrderStatus.IN_PROCESS, SalesOrderStatus.ON_HOLD, SalesOrderStatus.BACKORDER, SalesOrderStatus.PARTIALLY_CANCELLED, SalesOrderStatus.CANCELLED},
    SalesOrderStatus.IN_PROCESS: {SalesOrderStatus.PARTIALLY_FULFILLED, SalesOrderStatus.FULFILLED, SalesOrderStatus.ON_HOLD, SalesOrderStatus.BACKORDER, SalesOrderStatus.PARTIALLY_CANCELLED, SalesOrderStatus.CANCELLED},
    SalesOrderStatus.PARTIALLY_FULFILLED: {SalesOrderStatus.IN_PROCESS, SalesOrderStatus.FULFILLED, SalesOrderStatus.ON_HOLD, SalesOrderStatus.BACKORDER, SalesOrderStatus.PARTIALLY_CANCELLED, SalesOrderStatus.CANCELLED},
    SalesOrderStatus.FULFILLED: {SalesOrderStatus.CLOSED},
    SalesOrderStatus.CLOSED: set(),
    SalesOrderStatus.ON_HOLD: {SalesOrderStatus.CONFIRMED, SalesOrderStatus.IN_PROCESS, SalesOrderStatus.CANCELLED},
    SalesOrderStatus.BACKORDER: {SalesOrderStatus.IN_PROCESS, SalesOrderStatus.PARTIALLY_FULFILLED, SalesOrderStatus.FULFILLED, SalesOrderStatus.ON_HOLD, SalesOrderStatus.PARTIALLY_CANCELLED, SalesOrderStatus.CANCELLED},
    SalesOrderStatus.PARTIALLY_CANCELLED: {SalesOrderStatus.IN_PROCESS, SalesOrderStatus.PARTIALLY_FULFILLED, SalesOrderStatus.FULFILLED, SalesOrderStatus.CLOSED},
    SalesOrderStatus.CANCELLED: set(),
}


def can_transition(current: SalesOrderStatus, target: SalesOrderStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def validate_transition(current: SalesOrderStatus, target: SalesOrderStatus) -> None:
    if not can_transition(current, target):
        raise ValueError(f"invalid sales order transition: {current.value} -> {target.value}")
