"""Validation logic for bids — SOV sum checks, data consistency."""

from dataclasses import dataclass, field
from bid_engine.models import Bid, LineItem


@dataclass
class ValidationError:
    """A single validation error."""

    field: str
    message: str


@dataclass
class ValidationResult:
    """Result of a validation pass — zero or more errors."""

    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add(self, field: str, message: str) -> None:
        self.errors.append(ValidationError(field=field, message=message))


class BidValidator:
    """Validates a Bid object for internal consistency and correctness."""

    @staticmethod
    def validate(bid: Bid) -> ValidationResult:
        """Run all validation checks on a bid.

        Returns a ValidationResult. Check `is_valid` before rendering.
        """
        result = ValidationResult()
        _check_line_items(result, bid)
        _check_markups(result, bid)
        _check_exclusions(result, bid)
        _check_labor_hours(result, bid)
        return result


def _check_line_items(result: ValidationResult, bid: Bid) -> None:
    """Validate line items sum correctly."""
    if not bid.line_items:
        result.add("line_items", "Bid has no line items")
        return

    computed_material = sum(li.total_material for li in bid.line_items)
    computed_labor = sum(li.total_labor for li in bid.line_items)
    computed_direct = computed_material + computed_labor

    if abs(computed_direct - bid.total_direct_cost) > 0.01:
        result.add(
            "total_direct_cost",
            f"Line item sum ({computed_direct:.2f}) != bid total_direct_cost ({bid.total_direct_cost:.2f})",
        )

    for i, li in enumerate(bid.line_items):
        if li.quantity < 0:
            result.add(f"line_items[{i}].quantity", f"Negative quantity: {li.quantity}")
        if li.unit_cost_material < 0:
            result.add(f"line_items[{i}].unit_cost_material", "Negative material unit cost")
        if li.unit_cost_labor < 0:
            result.add(f"line_items[{i}].unit_cost_labor", "Negative labor unit cost")


def _check_markups(result: ValidationResult, bid: Bid) -> None:
    """Validate markup percentages are within reasonable bounds."""
    if not (0 <= bid.contingency_pct <= 50):
        result.add("contingency_pct", f"Contingency {bid.contingency_pct}% outside 0-50% range")
    if not (0 <= bid.overhead_profit_pct <= 50):
        result.add("overhead_profit_pct", f"O&P {bid.overhead_profit_pct}% outside 0-50% range")

    expected_contingency = bid.total_direct_cost * (bid.contingency_pct / 100.0)
    if abs(expected_contingency - bid.contingency_amount) > 0.01:
        result.add(
            "contingency_amount",
            f"Computed contingency ({expected_contingency:.2f}) != stored ({bid.contingency_amount:.2f})",
        )

    expected_op = (bid.total_direct_cost + bid.contingency_amount) * (
        bid.overhead_profit_pct / 100.0
    )
    if abs(expected_op - bid.overhead_profit_amount) > 0.01:
        result.add(
            "overhead_profit_amount",
            f"Computed O&P ({expected_op:.2f}) != stored ({bid.overhead_profit_amount:.2f})",
        )

    expected_total = bid.total_direct_cost + bid.contingency_amount + bid.overhead_profit_amount
    if abs(expected_total - bid.total_bid_amount) > 0.01:
        result.add(
            "total_bid_amount",
            f"Computed total ({expected_total:.2f}) != stored ({bid.total_bid_amount:.2f})",
        )


def _check_exclusions(result: ValidationResult, bid: Bid) -> None:
    """Warn if exclusions list is empty (non-blocking)."""
    if not bid.exclusions:
        result.add("exclusions", "Bid has no exclusions — consider adding standard exclusions")


def _check_labor_hours(result: ValidationResult, bid: Bid) -> None:
    """Warn if labor hours seem unreasonable for the project size."""
    if bid.total_labor_hours > 0:
        sf_per_hour = bid.project.total_area_sf / bid.total_labor_hours
        if sf_per_hour < 5:
            result.add(
                "labor_hours",
                f"Very low SF/hour ratio ({sf_per_hour:.1f}) — verify labor hour estimates",
            )
