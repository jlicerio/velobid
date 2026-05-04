"""Tests for bid_engine validators and pricing engine."""

from datetime import date
import pytest

from bid_engine.models import (
    Project,
    Bidder,
    TradeConfig,
    Bid,
    LineItem,
    PricingContext,
)
from bid_engine.validators import BidValidator, ValidationResult
from bid_engine.pricing_engine import PricingEngine


@pytest.fixture
def hvac_trade() -> TradeConfig:
    data = {
        "division": 23,
        "name": "HVAC",
        "full_name": "Heating, Ventilating, and Air Conditioning",
        "default_region": "South Texas",
        "labor_rates": {
            "South Texas": {
                "burdened_rate": 75.0,
                "effective_date": "2026-01-01",
                "source": "test",
            },
        },
        "compliance_codes": [
            {"code_name": "2018 IMC", "description": "IMC", "applies_to": "all work"},
        ],
        "cost_codes": [{"code": "23-31-00", "description": "Sheet Metal"}],
        "equipment_categories": ["AHUs", "Ductwork"],
        "labor_factors": {
            "sheet_metal": {
                "Ductwork": {"unit": "lbs", "factor": 0.04, "unit_type": "hours per lb"},
            },
        },
        "material_rates": {},
        "complexity_multipliers": [
            {
                "name": "Mezzanine Access",
                "adjustment": 1.15,
                "applies_to": "equipment",
                "rationale": "test",
            },
        ],
        "default_exclusions": ["Permit fees"],
        "templates": {},
        "regional_adjustments": {},
    }
    return TradeConfig.from_dict(data)


@pytest.fixture
def project() -> Project:
    data = {
        "name": "Test Project",
        "address": "123 Test St",
        "city": "TestCity",
        "state": "TX",
        "zip_code": "78541",
        "total_area_sf": 7466.0,
        "occupancy_group": "A-3",
        "construction_type": "Type IIB",
        "governing_codes": {},
    }
    return Project.from_dict(data)


@pytest.fixture
def bidder() -> Bidder:
    return Bidder(
        company_name="Test Company",
        primary_contact="John Doe",
        contact_email="john@test.com",
        phone="(956) 000-0000",
        location="McAllen, TX",
    )


@pytest.fixture
def bid(hvac_trade, project, bidder) -> Bid:
    return Bid(
        project=project,
        bidder=bidder,
        trade=hvac_trade,
        region="South Texas",
        contingency_pct=5.0,
        overhead_profit_pct=15.0,
        bid_date=date(2026, 4, 17),
    )


class TestLineItem:
    def test_total_material(self):
        li = LineItem(
            cost_code="23-31-00",
            description="Ductwork",
            quantity=100,
            unit="lbs",
            unit_cost_material=4.0,
        )
        assert li.total_material == 400.0

    def test_total_labor_with_unit_cost(self):
        li = LineItem(
            cost_code="23-31-00",
            description="Ductwork",
            quantity=100,
            unit="lbs",
            unit_cost_labor=2.0,
        )
        assert li.total_labor == 200.0

    def test_total_phase(self):
        li = LineItem(
            cost_code="23-31-00",
            description="Ductwork",
            quantity=100,
            unit="lbs",
            unit_cost_material=4.0,
            unit_cost_labor=2.0,
        )
        assert li.total_phase == 600.0

    def test_negative_quantity_flagged(self, bid):
        li = LineItem(
            cost_code="23-31-00",
            description="Ductwork",
            quantity=-100,
            unit="lbs",
            unit_cost_material=4.0,
        )
        bid.line_items = [li]
        result = BidValidator.validate(bid)
        assert not result.is_valid
        assert any("Negative quantity" in e.message for e in result.errors)


class TestBidTotals:
    def test_direct_cost_sum(self, bid):
        bid.line_items = [
            LineItem(
                cost_code="23-31-00",
                description="Duct A",
                quantity=100,
                unit="lbs",
                unit_cost_material=4.0,
                unit_cost_labor=1.0,
                labor_hours=4,
            ),
            LineItem(
                cost_code="23-31-13",
                description="Duct B",
                quantity=50,
                unit="lbs",
                unit_cost_material=4.0,
                unit_cost_labor=1.0,
                labor_hours=2,
            ),
        ]
        assert bid.total_material == 600.0
        assert bid.total_labor == 150.0
        assert bid.total_direct_cost == 750.0

    def test_contingency_calculation(self, bid):
        bid.line_items = [
            LineItem(
                cost_code="23-31-00",
                description="Duct",
                quantity=100,
                unit="lbs",
                unit_cost_material=10.0,
                unit_cost_labor=0.0,
                labor_hours=0,
            ),
        ]
        assert bid.total_direct_cost == 1000.0
        assert bid.contingency_amount == 50.0

    def test_overhead_profit_calculation(self, bid):
        bid.line_items = [
            LineItem(
                cost_code="23-31-00",
                description="Duct",
                quantity=100,
                unit="lbs",
                unit_cost_material=10.0,
                unit_cost_labor=0.0,
                labor_hours=0,
            ),
        ]
        bid.contingency_pct = 10.0
        assert bid.contingency_amount == 100.0
        assert bid.overhead_profit_amount == 165.0  # (1000 + 100) * 15%

    def test_total_bid_amount(self, bid):
        bid.line_items = [
            LineItem(
                cost_code="23-31-00",
                description="Duct",
                quantity=100,
                unit="lbs",
                unit_cost_material=10.0,
                unit_cost_labor=0.0,
                labor_hours=0,
            ),
        ]
        assert bid.total_bid_amount == 1207.5  # 1000 + 50 (5%) + 157.5 (15% of 1050)


class TestBidValidator:
    def test_valid_bid(self, bid):
        bid.line_items = [
            LineItem(
                cost_code="23-31-00",
                description="Duct",
                quantity=100,
                unit="lbs",
                unit_cost_material=10.0,
                unit_cost_labor=5.0,
                labor_hours=4,
            ),
        ]
        bid.exclusions = ["City permit fees excluded"]
        result = BidValidator.validate(bid)
        assert result.is_valid

    def test_empty_bid_invalid(self, bid):
        result = BidValidator.validate(bid)
        assert not result.is_valid
        assert any("no line items" in e.message.lower() for e in result.errors)

    def test_missing_exclusions_warning(self, bid):
        bid.line_items = [
            LineItem(
                cost_code="23-31-00",
                description="Duct",
                quantity=100,
                unit="lbs",
                unit_cost_material=10.0,
                unit_cost_labor=5.0,
                labor_hours=4,
            ),
        ]
        bid.exclusions = []
        result = BidValidator.validate(bid)
        assert any("exclusions" in e.message.lower() for e in result.errors)

    def test_contingency_out_of_range(self, bid):
        bid.line_items = [
            LineItem(
                cost_code="23-31-00",
                description="Duct",
                quantity=100,
                unit="lbs",
                unit_cost_material=10.0,
                unit_cost_labor=5.0,
                labor_hours=4,
            ),
        ]
        bid.contingency_pct = 75.0
        result = BidValidator.validate(bid)
        assert not result.is_valid
        assert any("contingency" in e.message.lower() for e in result.errors)


class TestPricingEngine:
    def test_apply_labor_rate_per_unit(self, hvac_trade, project):
        ctx = PricingContext.from_trade_and_project(hvac_trade, project)
        engine = PricingEngine(ctx)

        li = LineItem(
            cost_code="23-31-00",
            description="AHU Setting",
            quantity=5,
            unit="ea",
            unit_cost_material=9000.0,
            labor_factor="8 hrs/unit",
        )
        result = engine.apply_labor_rate(li)
        assert result.labor_hours == 40.0
        assert result.unit_cost_labor == 600.0

    def test_apply_labor_rate_per_lb(self, hvac_trade, project):
        ctx = PricingContext.from_trade_and_project(hvac_trade, project)
        engine = PricingEngine(ctx)

        li = LineItem(
            cost_code="23-31-00",
            description="Ductwork",
            quantity=7500,
            unit="lbs",
            labor_factor="0.04 hrs/lb",
        )
        result = engine.apply_labor_rate(li)
        assert result.labor_hours == 300.0
        assert result.unit_cost_labor == 3.0  # 0.04 * 75

    def test_price_bid(self, hvac_trade, project):
        ctx = PricingContext.from_trade_and_project(hvac_trade, project)
        engine = PricingEngine(ctx)

        bid = Bid(
            project=project,
            bidder=Bidder(company_name="Test", primary_contact="T", contact_email="t@t.com"),
            trade=hvac_trade,
            region="South Texas",
        )
        bid.line_items = [
            LineItem(
                cost_code="23-31-00",
                description="Ductwork",
                quantity=7500,
                unit="lbs",
                labor_factor="0.04 hrs/lb",
                unit_cost_material=4.0,
            ),
        ]

        bid = engine.price_bid(bid)
        assert bid.line_items[0].labor_hours == 300.0
        assert bid.line_items[0].unit_cost_labor == 3.0

    def test_complexity_multiplier_mezzanine(self, hvac_trade, project):
        ctx = PricingContext.from_trade_and_project(hvac_trade, project)
        engine = PricingEngine(ctx)

        bid = Bid(
            project=project,
            bidder=Bidder(company_name="Test", primary_contact="T", contact_email="t@t.com"),
            trade=hvac_trade,
            region="South Texas",
        )
        bid.line_items = [
            LineItem(
                cost_code="23-05-29",
                description="Hangers",
                quantity=1,
                unit="lot",
                labor_hours=100,
                labor_factor="100 hrs/lot",
            ),
        ]

        bid = engine.apply_complexity_multipliers(bid)
        assert bid.line_items[0].labor_hours == 115.0  # 100 * 1.15


class TestSovSummary:
    def test_sov_summary_keys(self, bid):
        bid.line_items = [
            LineItem(
                cost_code="23-31-00",
                description="Duct",
                quantity=100,
                unit="lbs",
                unit_cost_material=10.0,
                unit_cost_labor=5.0,
                labor_hours=4,
            ),
        ]
        summary = bid.sov_summary()
        assert "total_material" in summary
        assert "total_labor" in summary
        assert "total_direct_cost" in summary
        assert "contingency" in summary
        assert "overhead_profit" in summary
        assert "total_bid_amount" in summary
        assert "total_labor_hours" in summary
