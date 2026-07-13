import unittest
from src.pillar7.product_pipeline import (
    ProductConcept,
    VALID_STATUSES,
    DEFAULT_EV_THRESHOLD,
    compute_pipeline_summary,
    generate_pipeline_report,
)
from src.pillar7.product_pipeline_generator import create_product, get_pipeline_report


class TestProductConceptGates(unittest.TestCase):

    def test_valid_product(self):
        p = ProductConcept(
            name='CoPQ Diagnostic Tool',
            launch_probability=0.75,
            projected_revenue_year1=30000,
        )
        self.assertEqual(p.name, 'CoPQ Diagnostic Tool')
        self.assertEqual(p.ev, 22500)
        self.assertTrue(p.meets_threshold)

    def test_g1_missing_name(self):
        with self.assertRaises(ValueError) as ctx:
            ProductConcept(name='', launch_probability=0.5, projected_revenue_year1=10000)
        self.assertIn('G1', str(ctx.exception))

    def test_g2_probability_out_of_range_high(self):
        with self.assertRaises(ValueError) as ctx:
            ProductConcept(name='x', launch_probability=1.5, projected_revenue_year1=10000)
        self.assertIn('G2', str(ctx.exception))

    def test_g2_probability_out_of_range_negative(self):
        with self.assertRaises(ValueError) as ctx:
            ProductConcept(name='x', launch_probability=-0.1, projected_revenue_year1=10000)
        self.assertIn('G2', str(ctx.exception))

    def test_g3_negative_revenue(self):
        with self.assertRaises(ValueError) as ctx:
            ProductConcept(name='x', launch_probability=0.5, projected_revenue_year1=-1000)
        self.assertIn('G3', str(ctx.exception))

    def test_g4_invalid_status(self):
        with self.assertRaises(ValueError) as ctx:
            ProductConcept(name='x', launch_probability=0.5, projected_revenue_year1=10000, status='Invalid')
        self.assertIn('G4', str(ctx.exception))

    def test_g4_case_sensitive_status(self):
        with self.assertRaises(ValueError) as ctx:
            ProductConcept(name='x', launch_probability=0.5, projected_revenue_year1=10000, status='concept')
        self.assertIn('G4', str(ctx.exception))


class TestProductConceptBoundaries(unittest.TestCase):

    def test_probability_boundary_zero(self):
        p = ProductConcept(name='x', launch_probability=0.0, projected_revenue_year1=50000)
        self.assertEqual(p.ev, 0.0)
        self.assertFalse(p.meets_threshold)

    def test_probability_boundary_one(self):
        p = ProductConcept(name='x', launch_probability=1.0, projected_revenue_year1=20000)
        self.assertEqual(p.ev, 20000.0)
        self.assertTrue(p.meets_threshold)

    def test_revenue_boundary_zero(self):
        p = ProductConcept(name='x', launch_probability=0.9, projected_revenue_year1=0)
        self.assertEqual(p.ev, 0.0)
        self.assertFalse(p.meets_threshold)

    def test_ev_exactly_at_threshold(self):
        # EV = 15000.0 exactly → PASS (>= threshold)
        p = ProductConcept(name='x', launch_probability=0.5, projected_revenue_year1=30000)
        self.assertEqual(p.ev, 15000.0)
        self.assertTrue(p.meets_threshold)

    def test_ev_just_below_threshold(self):
        p = ProductConcept(name='x', launch_probability=0.5, projected_revenue_year1=29998)
        self.assertFalse(p.meets_threshold)


class TestProductConceptStatuses(unittest.TestCase):

    def test_status_concept_default(self):
        p = ProductConcept(name='x', launch_probability=0.5, projected_revenue_year1=10000)
        self.assertEqual(p.status, 'Concept')

    def test_status_in_development(self):
        p = ProductConcept(name='x', launch_probability=0.5, projected_revenue_year1=10000, status='In Development')
        self.assertEqual(p.status, 'In Development')

    def test_status_launched(self):
        p = ProductConcept(name='x', launch_probability=1.0, projected_revenue_year1=50000, status='Launched')
        self.assertEqual(p.status, 'Launched')

    def test_status_dropped(self):
        p = ProductConcept(name='x', launch_probability=0.0, projected_revenue_year1=0, status='Dropped')
        self.assertEqual(p.status, 'Dropped')

    def test_all_valid_statuses_accepted(self):
        for s in VALID_STATUSES:
            p = ProductConcept(name='x', launch_probability=0.5, projected_revenue_year1=10000, status=s)
            self.assertEqual(p.status, s)


class TestEVComputation(unittest.TestCase):

    def test_ev_computation_below_threshold(self):
        p = ProductConcept(name='x', launch_probability=0.6, projected_revenue_year1=20000)
        self.assertEqual(p.ev, 12000)
        self.assertFalse(p.meets_threshold)

    def test_ev_computation_above_threshold(self):
        p = ProductConcept(name='x', launch_probability=0.8, projected_revenue_year1=25000)
        self.assertEqual(p.ev, 20000.0)
        self.assertTrue(p.meets_threshold)

    def test_custom_ev_threshold(self):
        p = ProductConcept(name='x', launch_probability=0.5, projected_revenue_year1=20000, ev_threshold=5000.0)
        self.assertEqual(p.ev, 10000.0)
        self.assertTrue(p.meets_threshold)

    def test_custom_ev_threshold_fail(self):
        p = ProductConcept(name='x', launch_probability=0.1, projected_revenue_year1=20000, ev_threshold=5000.0)
        self.assertEqual(p.ev, 2000.0)
        self.assertFalse(p.meets_threshold)


class TestPipelineSummary(unittest.TestCase):

    def test_pipeline_summary(self):
        products = [
            ProductConcept('A', 0.75, 30000),
            ProductConcept('B', 0.4, 20000),
            ProductConcept('C', 0.1, 10000),
        ]
        summary = compute_pipeline_summary(products)
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['total_ev'], 22500 + 8000 + 1000)
        self.assertEqual(summary['meeting_threshold'], 1)

    def test_pipeline_summary_empty(self):
        summary = compute_pipeline_summary([])
        self.assertEqual(summary['total'], 0)
        self.assertEqual(summary['total_ev'], 0)
        self.assertEqual(summary['meeting_threshold'], 0)

    def test_pipeline_summary_all_passing(self):
        products = [
            ProductConcept('A', 0.8, 30000),
            ProductConcept('B', 0.9, 20000),
        ]
        summary = compute_pipeline_summary(products)
        self.assertEqual(summary['meeting_threshold'], 2)

    def test_pipeline_summary_none_passing(self):
        products = [
            ProductConcept('A', 0.1, 10000),
            ProductConcept('B', 0.05, 5000),
        ]
        summary = compute_pipeline_summary(products)
        self.assertEqual(summary['meeting_threshold'], 0)


class TestPipelineReport(unittest.TestCase):

    def test_generate_report(self):
        products = [
            ProductConcept('A', 0.75, 30000),
            ProductConcept('B', 0.4, 20000),
        ]
        report = generate_pipeline_report(products)
        self.assertIn('Total products: 2', report)
        self.assertIn('A', report)
        self.assertIn('B', report)

    def test_empty_pipeline_report(self):
        report = generate_pipeline_report([])
        self.assertIn('No products in pipeline', report)

    def test_report_contains_pass_label(self):
        p = ProductConcept('High EV Product', 0.9, 25000)
        report = generate_pipeline_report([p])
        self.assertIn('PASS', report)

    def test_report_contains_below_threshold_label(self):
        p = ProductConcept('Low EV Product', 0.1, 5000)
        report = generate_pipeline_report([p])
        self.assertIn('BELOW THRESHOLD', report)

    def test_report_total_ev_format(self):
        products = [ProductConcept('A', 0.75, 30000)]
        report = generate_pipeline_report(products)
        self.assertIn('Total EV:', report)
        self.assertIn('£22,500.00', report)

    def test_report_products_meeting_threshold(self):
        products = [
            ProductConcept('A', 0.8, 30000),
            ProductConcept('B', 0.1, 5000),
        ]
        report = generate_pipeline_report(products)
        self.assertIn('Products meeting threshold: 1', report)


class TestProductPipelineGenerator(unittest.TestCase):

    def test_create_product_wrapper(self):
        p = create_product('Strategy Audit Tool', 0.7, 25000)
        self.assertEqual(p.name, 'Strategy Audit Tool')
        self.assertEqual(p.ev, 17500.0)
        self.assertTrue(p.meets_threshold)

    def test_get_pipeline_report_wrapper(self):
        products = [create_product('A', 0.8, 20000)]
        report = get_pipeline_report(products)
        self.assertIn('Total products: 1', report)
        self.assertIn('A', report)


if __name__ == "__main__":
    unittest.main()
