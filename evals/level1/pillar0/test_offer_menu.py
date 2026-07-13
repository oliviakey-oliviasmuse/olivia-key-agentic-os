import unittest
from src.pillar0.offer_menu import Offer, OfferMenu, VALID_FORMATS, VALID_ICP_FIT, to_yaml, from_yaml


class TestOffer(unittest.TestCase):
    def test_valid_offer(self):
        offer = Offer(
            name="Hidden Factory Audit",
            format="Diagnostic",
            price_floor=5000.0,
            price_range=(5000.0, 10000.0),
            icp_fit="Core",
            delivery_pillar="P4 – Delivery",
            description="2-week assessment with Control Plan handover.",
        )
        self.assertEqual(offer.name, "Hidden Factory Audit")
        self.assertEqual(offer.price_floor, 5000.0)

    def test_g1_missing_name(self):
        with self.assertRaises(ValueError) as ctx:
            Offer(
                name="",
                format="Diagnostic",
                price_floor=5000.0,
                price_range=(5000.0, 10000.0),
                icp_fit="Core",
                delivery_pillar="P4",
                description="Test",
            )
        self.assertIn("G1", str(ctx.exception))

    def test_g2_invalid_format(self):
        with self.assertRaises(ValueError) as ctx:
            Offer(
                name="Test",
                format="Invalid",
                price_floor=5000.0,
                price_range=(5000.0, 10000.0),
                icp_fit="Core",
                delivery_pillar="P4",
                description="Test",
            )
        self.assertIn("G2", str(ctx.exception))

    def test_g3_price_floor_zero(self):
        with self.assertRaises(ValueError) as ctx:
            Offer(
                name="Test",
                format="Diagnostic",
                price_floor=0.0,
                price_range=(5000.0, 10000.0),
                icp_fit="Core",
                delivery_pillar="P4",
                description="Test",
            )
        self.assertIn("G3", str(ctx.exception))

    def test_g3_price_floor_negative(self):
        with self.assertRaises(ValueError) as ctx:
            Offer(
                name="Test",
                format="Diagnostic",
                price_floor=-100.0,
                price_range=(5000.0, 10000.0),
                icp_fit="Core",
                delivery_pillar="P4",
                description="Test",
            )
        self.assertIn("G3", str(ctx.exception))

    def test_g4_invalid_price_range(self):
        with self.assertRaises(ValueError) as ctx:
            Offer(
                name="Test",
                format="Diagnostic",
                price_floor=5000.0,
                price_range=(10000.0, 5000.0),
                icp_fit="Core",
                delivery_pillar="P4",
                description="Test",
            )
        self.assertIn("G4", str(ctx.exception))

    def test_g4_equal_price_range(self):
        with self.assertRaises(ValueError) as ctx:
            Offer(
                name="Test",
                format="Diagnostic",
                price_floor=5000.0,
                price_range=(5000.0, 5000.0),
                icp_fit="Core",
                delivery_pillar="P4",
                description="Test",
            )
        self.assertIn("G4", str(ctx.exception))

    def test_g5_invalid_icp_fit(self):
        with self.assertRaises(ValueError) as ctx:
            Offer(
                name="Test",
                format="Diagnostic",
                price_floor=5000.0,
                price_range=(5000.0, 10000.0),
                icp_fit="Invalid",
                delivery_pillar="P4",
                description="Test",
            )
        self.assertIn("G5", str(ctx.exception))

    def test_g6_missing_delivery_pillar(self):
        with self.assertRaises(ValueError) as ctx:
            Offer(
                name="Test",
                format="Diagnostic",
                price_floor=5000.0,
                price_range=(5000.0, 10000.0),
                icp_fit="Core",
                delivery_pillar="",
                description="Test",
            )
        self.assertIn("G6", str(ctx.exception))

    def test_all_valid_formats(self):
        for fmt in VALID_FORMATS:
            offer = Offer(
                name=f"Test {fmt}",
                format=fmt,
                price_floor=1000.0,
                price_range=(1000.0, 2000.0),
                icp_fit="Core",
                delivery_pillar="P4",
                description="Test",
            )
            self.assertEqual(offer.format, fmt)

    def test_all_valid_icp_fits(self):
        for fit in VALID_ICP_FIT:
            offer = Offer(
                name=f"Test {fit}",
                format="Diagnostic",
                price_floor=1000.0,
                price_range=(1000.0, 2000.0),
                icp_fit=fit,
                delivery_pillar="P4",
                description="Test",
            )
            self.assertEqual(offer.icp_fit, fit)

    def test_default_discount_values(self):
        offer = Offer(
            name="Test",
            format="Diagnostic",
            price_floor=5000.0,
            price_range=(5000.0, 10000.0),
            icp_fit="Core",
            delivery_pillar="P4",
            description="Test",
        )
        self.assertEqual(offer.discount_max, 10.0)
        self.assertEqual(offer.discount_authority, "Owner")

    def test_custom_bundling_rules(self):
        offer = Offer(
            name="Test",
            format="Retainer",
            price_floor=5000.0,
            price_range=(5000.0, 10000.0),
            icp_fit="Core",
            delivery_pillar="P4",
            description="Test",
            bundling_rules=["Cannot bundle with Diagnostic"],
        )
        self.assertEqual(len(offer.bundling_rules), 1)
        self.assertIn("Cannot bundle with Diagnostic", offer.bundling_rules)


class TestOfferMenu(unittest.TestCase):
    def setUp(self):
        self.offer = Offer(
            name="Hidden Factory Audit",
            format="Diagnostic",
            price_floor=5000.0,
            price_range=(5000.0, 10000.0),
            icp_fit="Core",
            delivery_pillar="P4",
            description="Test",
        )
        self.menu = OfferMenu(offers=[self.offer])

    def test_get_offer_exists(self):
        result = self.menu.get_offer("Hidden Factory Audit")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Hidden Factory Audit")

    def test_get_offer_missing(self):
        result = self.menu.get_offer("Missing")
        self.assertIsNone(result)

    def test_validate_proposal_pass(self):
        result = self.menu.validate_proposal("Hidden Factory Audit", 7000.0)
        self.assertTrue(result["pass"])
        self.assertIsNone(result["reason"])

    def test_validate_proposal_at_floor(self):
        result = self.menu.validate_proposal("Hidden Factory Audit", 5000.0)
        self.assertTrue(result["pass"])

    def test_validate_proposal_fail_below_floor(self):
        result = self.menu.validate_proposal("Hidden Factory Audit", 4000.0)
        self.assertFalse(result["pass"])
        self.assertIn("below floor", result["reason"])

    def test_validate_proposal_m1_defect_code_context(self):
        result = self.menu.validate_proposal("Hidden Factory Audit", 4999.99)
        self.assertFalse(result["pass"])
        self.assertIn("4,999.99", result["reason"])
        self.assertIn("5,000.00", result["reason"])

    def test_validate_proposal_offer_not_found(self):
        result = self.menu.validate_proposal("Missing", 7000.0)
        self.assertFalse(result["pass"])
        self.assertIn("not found", result["reason"])

    def test_validate_invoice_pass(self):
        result = self.menu.validate_invoice("Hidden Factory Audit", 7000.0)
        self.assertTrue(result["pass"])

    def test_validate_invoice_at_floor(self):
        result = self.menu.validate_invoice("Hidden Factory Audit", 5000.0)
        self.assertTrue(result["pass"])

    def test_validate_invoice_fail_below_floor(self):
        result = self.menu.validate_invoice("Hidden Factory Audit", 4000.0)
        self.assertFalse(result["pass"])
        self.assertIn("below floor", result["reason"])
        self.assertIn("defect logged", result["reason"])

    def test_validate_invoice_m2_defect_amounts(self):
        result = self.menu.validate_invoice("Hidden Factory Audit", 3500.0)
        self.assertFalse(result["pass"])
        self.assertIn("3,500.00", result["reason"])
        self.assertIn("5,000.00", result["reason"])

    def test_validate_invoice_offer_not_found(self):
        result = self.menu.validate_invoice("Missing", 7000.0)
        self.assertFalse(result["pass"])
        self.assertIn("not found", result["reason"])

    def test_register_offer_valid(self):
        new_data = {
            "name": "CoPQ Retainer",
            "format": "Retainer",
            "price_floor": 10000.0,
            "price_range": (10000.0, 20000.0),
            "icp_fit": "Core",
            "delivery_pillar": "P4",
            "description": "Monthly CoPQ reduction retainer.",
        }
        new_offer = self.menu.register_offer(new_data)
        self.assertEqual(len(self.menu.offers), 2)
        self.assertEqual(new_offer.name, "CoPQ Retainer")
        self.assertIsNotNone(self.menu.get_offer("CoPQ Retainer"))

    def test_register_offer_duplicate_fails(self):
        with self.assertRaises(ValueError) as ctx:
            self.menu.register_offer({
                "name": "Hidden Factory Audit",
                "format": "Diagnostic",
                "price_floor": 5000.0,
                "price_range": (5000.0, 10000.0),
                "icp_fit": "Core",
                "delivery_pillar": "P4",
                "description": "Duplicate",
            })
        self.assertIn("already exists", str(ctx.exception))

    def test_register_offer_gate_validation_fires(self):
        with self.assertRaises(ValueError) as ctx:
            self.menu.register_offer({
                "name": "Bad Offer",
                "format": "Invalid",
                "price_floor": 5000.0,
                "price_range": (5000.0, 10000.0),
                "icp_fit": "Core",
                "delivery_pillar": "P4",
                "description": "Test",
            })
        self.assertIn("G2", str(ctx.exception))

    def test_multi_offer_menu(self):
        offer2 = Offer(
            name="CoPQ Retainer",
            format="Retainer",
            price_floor=10000.0,
            price_range=(10000.0, 20000.0),
            icp_fit="Core",
            delivery_pillar="P4",
            description="Monthly retainer.",
        )
        menu = OfferMenu(offers=[self.offer, offer2])
        self.assertEqual(len(menu.offers), 2)
        self.assertIsNotNone(menu.get_offer("CoPQ Retainer"))
        self.assertIsNotNone(menu.get_offer("Hidden Factory Audit"))

    def test_to_markdown_contains_offer(self):
        md = self.menu.to_markdown()
        self.assertIn("Hidden Factory Audit", md)
        self.assertIn("Diagnostic", md)
        self.assertIn("5,000", md)

    def test_to_markdown_version(self):
        md = self.menu.to_markdown()
        self.assertIn("Offer Menu", md)
        self.assertIn("1.0", md)

    def test_to_markdown_discount_policy(self):
        md = self.menu.to_markdown()
        self.assertIn("10.0%", md)
        self.assertIn("Owner", md)


class TestYAML(unittest.TestCase):
    def setUp(self):
        self.offer = Offer(
            name="Test Offer",
            format="Diagnostic",
            price_floor=5000.0,
            price_range=(5000.0, 10000.0),
            icp_fit="Core",
            delivery_pillar="P4",
            description="Test description.",
        )
        self.menu = OfferMenu(offers=[self.offer])

    def test_to_yaml_contains_name(self):
        yaml_str = to_yaml(self.menu)
        self.assertIn("name: Test Offer", yaml_str)

    def test_to_yaml_contains_price_floor(self):
        yaml_str = to_yaml(self.menu)
        self.assertIn("price_floor: 5000.0", yaml_str)

    def test_to_yaml_contains_version(self):
        yaml_str = to_yaml(self.menu)
        self.assertIn("version:", yaml_str)

    def test_from_yaml_roundtrip(self):
        yaml_str = to_yaml(self.menu)
        restored = from_yaml(yaml_str)
        self.assertEqual(len(restored.offers), 1)
        self.assertEqual(restored.offers[0].name, "Test Offer")
        self.assertEqual(restored.offers[0].price_floor, 5000.0)
        self.assertEqual(restored.offers[0].icp_fit, "Core")

    def test_from_yaml_literal(self):
        yaml_str = """
version: '1.0'
date: '2026-06-27'
global_discount_max: 10.0
global_discount_authority: Owner
offers:
- name: Test
  format: Diagnostic
  price_floor: 5000.0
  price_range: [5000.0, 10000.0]
  icp_fit: Core
  delivery_pillar: P4
  description: Test
  bundling_rules: []
  discount_max: 10.0
  discount_authority: Owner
"""
        menu = from_yaml(yaml_str)
        self.assertEqual(len(menu.offers), 1)
        self.assertEqual(menu.offers[0].name, "Test")
        self.assertEqual(menu.offers[0].price_floor, 5000.0)

    def test_from_yaml_multi_offer(self):
        yaml_str = """
version: '1.0'
date: '2026-06-27'
global_discount_max: 10.0
global_discount_authority: Owner
offers:
- name: Offer A
  format: Diagnostic
  price_floor: 5000.0
  price_range: [5000.0, 10000.0]
  icp_fit: Core
  delivery_pillar: P4
  description: First
  bundling_rules: []
  discount_max: 10.0
  discount_authority: Owner
- name: Offer B
  format: Retainer
  price_floor: 10000.0
  price_range: [10000.0, 20000.0]
  icp_fit: Adjacent
  delivery_pillar: P5
  description: Second
  bundling_rules: []
  discount_max: 10.0
  discount_authority: Owner
"""
        menu = from_yaml(yaml_str)
        self.assertEqual(len(menu.offers), 2)
        self.assertEqual(menu.offers[1].name, "Offer B")
        self.assertEqual(menu.offers[1].icp_fit, "Adjacent")


if __name__ == "__main__":
    unittest.main()
