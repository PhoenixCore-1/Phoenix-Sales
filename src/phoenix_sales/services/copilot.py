"""Application boundary for Sales Copilot."""

from phoenix_sales.domain.copilot import CopilotRequest, CopilotResponse


class SalesCopilotPort:
    """Provider-independent port implemented by the Phoenix Core AI boundary."""

    def respond(self, request: CopilotRequest) -> CopilotResponse:
        raise NotImplementedError


class SalesCopilotService:
    READ_PERMISSION = "sales.copilot.use"

    def __init__(self, context, ai_port: SalesCopilotPort) -> None:
        self.context = context
        self.ai_port = ai_port

    def respond(self, request: CopilotRequest) -> CopilotResponse:
        if not self.context.has_permission(self.READ_PERMISSION):
            raise PermissionError(f"missing permission: {self.READ_PERMISSION}")
        if request.context.tenant_id != self.context.tenant.tenant_id:
            raise PermissionError("cross-tenant access denied")
        if request.context.user_id != self.context.user.user_id:
            raise PermissionError("request user does not match authenticated user")
        return self.ai_port.respond(request)
