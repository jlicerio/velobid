"""Pricing engine — auto-populate line items from takeoff data and labor rates."""

from bid_engine.models import Bid, LineItem, PricingContext, TradeConfig


class PricingEngine:
    """Computes costs, applies multipliers, and calculates bid totals."""

    def __init__(self, context: PricingContext) -> None:
        self.context = context

    def apply_labor_rate(self, line_item: LineItem) -> LineItem:
        """Given a line item with quantity and labor_factor, compute labor cost and hours.

        The `labor_factor` string is expected to be in the format "X hrs/unit" or
        "X hrs/lb", etc. E.g., "25 lbs/hr", "1.0 hrs/unit".
        """
        factor_str = line_item.labor_factor
        if not factor_str:
            return line_item

        li = line_item
        rate = self.context.labor_rate

        if "hrs/unit" in factor_str or "hrs per unit" in factor_str:
            try:
                hrs_per_unit = float(factor_str.split()[0])
                li.labor_hours = round(li.quantity * hrs_per_unit, 1)
                li.unit_cost_labor = round(hrs_per_unit * rate, 2)
            except (ValueError, IndexError):
                pass

        elif "hrs/LF" in factor_str or "hrs per LF" in factor_str:
            try:
                hrs_per_lf = float(factor_str.split()[0])
                li.labor_hours = round(li.quantity * hrs_per_lf, 1)
                li.unit_cost_labor = round(hrs_per_lf * rate, 2)
            except (ValueError, IndexError):
                pass

        elif "hrs/lb" in factor_str or "hrs per lb" in factor_str:
            try:
                hrs_per_lb = float(factor_str.split()[0])
                li.labor_hours = round(li.quantity * hrs_per_lb, 1)
                li.unit_cost_labor = round(hrs_per_lb * rate, 2)
            except (ValueError, IndexError):
                pass

        elif "hrs/drop" in factor_str or "hrs per drop" in factor_str:
            try:
                hrs_per_drop = float(factor_str.split()[0])
                li.labor_hours = round(li.quantity * hrs_per_drop, 1)
                li.unit_cost_labor = round(hrs_per_drop * rate, 2)
            except (ValueError, IndexError):
                pass

        elif "hrs/circuit" in factor_str or "hrs per circuit" in factor_str:
            try:
                hrs_per_circuit = float(factor_str.split()[0])
                li.labor_hours = round(li.quantity * hrs_per_circuit, 1)
                li.unit_cost_labor = round(hrs_per_circuit * rate, 2)
            except (ValueError, IndexError):
                pass

        elif "hrs total" in factor_str or "lot" in factor_str.lower():
            try:
                total_hrs = float(factor_str.split()[0])
                li.labor_hours = total_hrs
                li.unit_cost_labor = round((total_hrs * rate) / max(li.quantity, 1), 2)
            except (ValueError, IndexError):
                pass

        return li

    def price_line_item(self, li: LineItem) -> LineItem:
        """Apply labor rate and return fully-priced line item."""
        li = self.apply_labor_rate(li)
        return li

    def price_bid(self, bid: Bid) -> Bid:
        """Price all line items in a bid and recalculate totals."""
        priced_items = [self.price_line_item(li) for li in bid.line_items]
        bid.line_items = priced_items
        return bid

    def recalculate_totals(self, bid: Bid) -> Bid:
        """Recalculate all derived totals on a bid after line item changes."""
        _ = bid.total_material
        _ = bid.total_labor
        _ = bid.total_direct_cost
        _ = bid.contingency_amount
        _ = bid.overhead_profit_amount
        _ = bid.total_bid_amount
        _ = bid.total_labor_hours
        return bid

    def apply_complexity_multipliers(self, bid: Bid) -> Bid:
        """Apply trade-specific complexity multipliers to appropriate line items.

        Complexity multipliers are defined per-trade in the trade config. They
        adjust labor hours for conditions like mezzanine access, climate, or
        seismic bracing requirements.
        """
        multipliers = {
            m["name"].lower(): m["adjustment"] for m in self.context.trade.complexity_multipliers
        }

        for li in bid.line_items:
            category = li.cost_code.split("-")[1] if "-" in li.cost_code else ""

            for mult_name, mult_value in multipliers.items():
                if mult_name in ["mezzanine access", "seismic/code"]:
                    li.labor_hours = round(li.labor_hours * mult_value, 1)
                elif mult_name == "south texas climate":
                    if "insulation" in li.description.lower() or "duct" in li.description.lower():
                        li.labor_hours = round(li.labor_hours * mult_value, 1)

        return bid
