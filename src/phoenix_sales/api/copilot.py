"""Sales Copilot application commands."""

from dataclasses import dataclass

from phoenix_sales.domain.copilot import CopilotRequest, CopilotResponse
from phoenix_sales.services.copilot import SalesCopilotService


@dataclass(frozen=True)
class AskSalesCopilotCommand:
    request: CopilotRequest


class SalesCopilotApplication:
    def __init__(self, service: SalesCopilotService) -> None:
        self.service = service

    def respond(self, command: AskSalesCopilotCommand) -> CopilotResponse:
        return self.service.respond(command.request)
