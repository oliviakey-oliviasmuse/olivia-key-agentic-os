import unittest
from src.pillar4.case_study_writer import generate_case_study

class TestCaseStudyWriter(unittest.TestCase):

    def test_generate_basic(self):
        baseline = {'total': 14_000_000}
        outcome = {'total': 10_500_000}
        metrics = {'ftar': 95, 'nps': 60}
        cs = generate_case_study(
            client_name='Acme',
            engagement_name='Project',
            industry='aerospace',
            copq_baseline=baseline,
            copq_outcome=outcome,
            intervention='Test intervention',
            metrics=metrics,
        )
        self.assertIn('Acme', cs)
        self.assertIn('£14,000,000', cs)
        self.assertIn('£3,500,000', cs)  # reduction
        self.assertIn('95%', cs)
        self.assertIn('60', cs)

    def test_missing_baseline_raises(self):
        with self.assertRaises(ValueError) as ctx:
            generate_case_study(
                client_name='Acme',
                engagement_name='Project',
                industry='aerospace',
                copq_baseline=None,
                copq_outcome={'total': 10_000_000},
                intervention='Test',
                metrics={},
            )
        self.assertIn('CoPQ baseline and outcome required', str(ctx.exception))

    def test_missing_intervention_raises(self):
        with self.assertRaises(ValueError) as ctx:
            generate_case_study(
                client_name='Acme',
                engagement_name='Project',
                industry='aerospace',
                copq_baseline={'total': 14_000_000},
                copq_outcome={'total': 10_500_000},
                intervention='',
                metrics={},
            )
        self.assertIn('No intervention description', str(ctx.exception))

    def test_anonymise(self):
        baseline = {'total': 14_000_000}
        outcome = {'total': 10_500_000}
        metrics = {'ftar': 95, 'nps': 60}
        cs = generate_case_study(
            client_name='Acme Aerospace',
            engagement_name='Project',
            industry='aerospace manufacturing',
            copq_baseline=baseline,
            copq_outcome=outcome,
            intervention='Test',
            metrics=metrics,
            anonymise=True,
        )
        self.assertNotIn('Acme Aerospace', cs)
        self.assertIn('anonymised', cs)
        self.assertIn('the client\'s industry', cs)

    def test_include_quote(self):
        baseline = {'total': 14_000_000}
        outcome = {'total': 10_500_000}
        metrics = {'ftar': 95, 'nps': 60}
        cs = generate_case_study(
            client_name='Acme',
            engagement_name='Project',
            industry='aerospace',
            copq_baseline=baseline,
            copq_outcome=outcome,
            intervention='Test',
            metrics=metrics,
            client_quote='Great work!',
            include_quote=True,
        )
        self.assertIn('Great work!', cs)

    def test_exclude_quote(self):
        baseline = {'total': 14_000_000}
        outcome = {'total': 10_500_000}
        metrics = {'ftar': 95, 'nps': 60}
        cs = generate_case_study(
            client_name='Acme',
            engagement_name='Project',
            industry='aerospace',
            copq_baseline=baseline,
            copq_outcome=outcome,
            intervention='Test',
            metrics=metrics,
            client_quote='Great work!',
            include_quote=False,
        )
        self.assertNotIn('Great work!', cs)

    def test_lessons(self):
        baseline = {'total': 14_000_000}
        outcome = {'total': 10_500_000}
        metrics = {'ftar': 95, 'nps': 60}
        lessons = ['Lesson 1', 'Lesson 2']
        cs = generate_case_study(
            client_name='Acme',
            engagement_name='Project',
            industry='aerospace',
            copq_baseline=baseline,
            copq_outcome=outcome,
            intervention='Test',
            metrics=metrics,
            lessons=lessons,
        )
        self.assertIn('Lesson 1', cs)
        self.assertIn('Lesson 2', cs)

    def test_warning_when_metrics_missing(self):
        baseline = {'total': 14_000_000}
        outcome = {'total': 10_500_000}
        metrics = {}
        cs = generate_case_study(
            client_name='Acme',
            engagement_name='Project',
            industry='aerospace',
            copq_baseline=baseline,
            copq_outcome=outcome,
            intervention='Test',
            metrics=metrics,
        )
        self.assertIn('Warning', cs)

if __name__ == "__main__":
    unittest.main()
