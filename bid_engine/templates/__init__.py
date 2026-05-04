"""BidForge template generators — each template is a PDFGenerator subclass."""

from bid_engine.templates.bid_proposal import BidProposalGenerator
from bid_engine.templates.full_scope import FullScopeGenerator
from bid_engine.templates.bom_manpower import BOMManpowerGenerator
from bid_engine.templates.cost_summary import CostSummaryGenerator
from bid_engine.templates.technical_scope import TechnicalScopeGenerator

__all__ = [
    "BidProposalGenerator",
    "FullScopeGenerator",
    "BOMManpowerGenerator",
    "CostSummaryGenerator",
    "TechnicalScopeGenerator",
]
