"""Tests for Pillar 5 Agent 0 — SOP Writer."""
import unittest
import os
import tempfile
from src.pillar5.sop_writer import (
    SOP,
    QualityGate,
    DefectCode,
    format_sop_markdown,
    generate_sop_filename,
    increment_version,
    trigger_check,
)
from src.pillar5.sop_writer_generator import create_sop, generate_sop_report


class TestSOPWriter(unittest.TestCase):
    def setUp(self):
        self.qg = [{'name': 'G1', 'criterion': 'PID approved', 'action_on_fail': 'Rework'}]
        self.dc = [{'code': 'S1', 'description': 'SOP not followed'}]

    def test_create_sop(self):
        sop = create_sop(
            process_name='Onboarding',
            description='Onboard clients',
            steps=['Send email', 'Schedule kick-off'],
            owner='Olivia',
            quality_gates=self.qg,
            defect_codes=self.dc,
            trigger_count=3,
        )
        self.assertEqual(sop.process_name, 'Onboarding')
        self.assertEqual(len(sop.steps), 2)
        self.assertEqual(len(sop.quality_gates), 1)
        self.assertEqual(sop.trigger_count, 3)
        self.assertIn('PID approved', sop.quality_gates[0].criterion)

    def test_required_fields(self):
        with self.assertRaises(ValueError) as ctx:
            create_sop(
                process_name='',
                description='Test',
                steps=['Step'],
                owner='Owner',
                quality_gates=self.qg,
            )
        self.assertIn('process_name', str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_sop(
                process_name='Test',
                description='',
                steps=['Step'],
                owner='Owner',
                quality_gates=self.qg,
            )
        self.assertIn('description', str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_sop(
                process_name='Test',
                description='Test',
                steps=[],
                owner='Owner',
                quality_gates=self.qg,
            )
        self.assertIn('steps', str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_sop(
                process_name='Test',
                description='Test',
                steps=['Step'],
                owner='',
                quality_gates=self.qg,
            )
        self.assertIn('owner', str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_sop(
                process_name='Test',
                description='Test',
                steps=['Step'],
                owner='Owner',
                quality_gates=[],
            )
        self.assertIn('quality_gate', str(ctx.exception))

    def test_trigger_check(self):
        sop = create_sop('Test', 'Desc', ['Step'], 'Owner', self.qg, trigger_count=2)
        self.assertIsNone(trigger_check(sop))

        sop2 = create_sop('Test', 'Desc', ['Step'], 'Owner', self.qg, trigger_count=3)
        msg = trigger_check(sop2)
        self.assertIsNotNone(msg)
        self.assertIn('ANDON', msg)

    def test_version_increment(self):
        self.assertEqual(increment_version('1.0'), '1.1')
        self.assertEqual(increment_version('2.5'), '2.6')
        self.assertEqual(increment_version('0.9'), '0.10')

    def test_format_sop_markdown(self):
        sop = create_sop(
            process_name='Onboarding',
            description='Onboard clients',
            steps=['Send email', 'Schedule kick-off'],
            owner='Olivia',
            quality_gates=self.qg,
            defect_codes=self.dc,
        )
        md = format_sop_markdown(sop)
        self.assertIn('SOP – Onboarding', md)
        self.assertIn('Owner: Olivia', md)
        self.assertIn('Send email', md)
        self.assertIn('PID approved', md)
        self.assertIn('S1', md)

    def test_generate_sop_filename(self):
        self.assertEqual(generate_sop_filename('Onboarding Process'), 'sop_onboarding_process.md')
        self.assertEqual(generate_sop_filename('Client Onboarding (v2)'), 'sop_client_onboarding__v2_.md')

    def test_generate_sop_report(self):
        sop = create_sop('Test', 'Desc', ['Step'], 'Owner', self.qg, trigger_count=3)
        # Without library path
        report = generate_sop_report(sop)
        self.assertIn('ANDON', report)
        self.assertIn('SOP – Test', report)

        # With library path (temp file)
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp_path = tmp.name
        report = generate_sop_report(sop, library_path=tmp_path)
        self.assertIn('SOP – Test', report)
        with open(tmp_path, 'r') as f:
            content = f.read()
            self.assertIn('SOP – Test', content)
        os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
