"""Application service for Phoenix Sales Quotes V1.0."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.quote import Quote, QuoteLine, QuoteStatus
from phoenix_sales.domain.quote_lifecycle import validate_transition


@dataclass(frozen=True)
class QuoteOutcome:
    """Customer response information captured against a quote."""

    reason: str | None = None


class QuoteService:
    """Coordinate quote commands while enforcing platform permissions."""

    CREATE_PERMISSION = "sales.quote.create"
    READ_PERMISSION = "sales.quote.read"
    UPDATE_PERMISSION = "sales.quote.update"
    TRANSITION_PERMISSION = "sales.quote.transition"

    def __init__(self, context: RequestContext) -> None:
        self._context = context
        self._quotes: dict[tuple[str, UUID], Quote] = {}

    def create_quote(self, quote: Quote) -> Quote:
        self._require(self.CREATE_PERMISSION)
        self._require_tenant(quote)
        if not quote.lines:
            raise ValueError("quote must contain at least one line")
        key = (quote.tenant_id, quote.id)
        if key in self._quotes:
            raise ValueError("quote already exists")
        self._quotes[key] = quote
        return quote

    def get_quote(self, quote_id: UUID) -> Quote | None:
        self._require(self.READ_PERMISSION)
        return self._quotes.get((self._context.tenant.tenant_id, quote_id))

    def update_quote(self, quote_id: UUID, **changes: object) -> Quote:
        self._require(self.UPDATE_PERMISSION)
        quote = self._get(quote_id)
        if quote.is_locked:
            raise ValueError("locked quote cannot be changed")
        protected = {"id", "tenant_id", "quote_number", "version", "status", "created_at", "updated_at", "lines"}
        invalid = set(changes) & protected
        if invalid:
            raise ValueError(f"protected quote fields cannot be changed: {sorted(invalid)}")
        for field_name, value in changes.items():
            if not hasattr(quote, field_name):
                raise ValueError(f"unknown quote field: {field_name}")
            setattr(quote, field_name, value)
        quote.updated_at = datetime.now(timezone.utc)
        return quote

    def add_line(self, quote_id: UUID, line: QuoteLine) -> Quote:
        self._require(self.UPDATE_PERMISSION)
        quote = self._get(quote_id)
        quote.add_line(line)
        return quote

    def transition(self, quote_id: UUID, target: QuoteStatus, outcome: QuoteOutcome | None = None) -> Quote:
        self._require(self.TRANSITION_PERMISSION)
        quote = self._get(quote_id)
        validate_transition(quote.status, target)
        if target is QuoteStatus.APPROVED and not quote.lines:
            raise ValueError("quote must contain at least one line before approval")
        if target in {QuoteStatus.REJECTED, QuoteStatus.CANCELLED} and outcome is not None and not (outcome.reason or "").strip():
            raise ValueError("outcome reason is required")
        quote.status = target
        quote.updated_at = datetime.now(timezone.utc)
        return quote

    def _get(self, quote_id: UUID) -> Quote:
        quote = self._quotes.get((self._context.tenant.tenant_id, quote_id))
        if quote is None:
            raise LookupError("quote not found")
        return quote

    def _require_tenant(self, quote: Quote) -> None:
        if quote.tenant_id != self._context.tenant.tenant_id:
            raise PermissionError("tenant access denied")

    def _require(self, permission: str) -> None:
        if not self._context.has_permission(permission):
            raise PermissionError(f"permission denied: {permission}")
