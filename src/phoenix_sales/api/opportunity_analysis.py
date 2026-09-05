"""Application contract for Sales Copilot opportunity analysis."""

from dataclasses import dataclass

from phoenix_sales.domain.copilot_context import SalesCopilotContextPackage
from phoenix_sales.domain.opportunity_analysis import OpportunityAnalysis
from phoenix_sales.services.opportunity_analysis import OpportunityAnalysisService


@dataclass(frozen=True)
class AnalyseOpportunityCommand:
    context_package: SalesCopilotContextPackage


class OpportunityAnalysisApplication:
    def __init__(self, service: OpportunityAnalysisService) -> None:
        self.service = service

    def analyse(self, command: AnalyseOpportunityCommand) -> OpportunityAnalysis:
        return self.service.analyse(command.context_package)
