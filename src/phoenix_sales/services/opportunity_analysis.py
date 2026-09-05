"""Application service for deterministic Sales Copilot opportunity analysis."""

from phoenix_sales.domain.copilot_context import SalesCopilotContextPackage
from phoenix_sales.domain.opportunity_analysis import OpportunityAnalysis


class OpportunityAnalysisService:
    PERMISSION = "sales.copilot.opportunity_analysis"

    def __init__(self, context) -> None:
        self.context = context

    def analyse(self, package: SalesCopilotContextPackage) -> OpportunityAnalysis:
        if not self.context.has_permission(self.PERMISSION):
            raise PermissionError(f"missing permission: {self.PERMISSION}")
        if package.tenant_id != self.context.tenant.tenant_id:
            raise PermissionError("cross-tenant access denied")
        if package.user_id != self.context.user.user_id:
            raise PermissionError("request user does not match authenticated user")
        return OpportunityAnalysis.from_context(package)
