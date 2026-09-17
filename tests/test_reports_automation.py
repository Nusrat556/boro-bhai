import os
import tempfile
import unittest

from automation.scheduler import AutomationTask, create_automation_task, execute_automation_task
from reports.report_generator import (
    generate_career_report,
    generate_job_analysis_report,
    generate_markdown_report,
    generate_research_report,
    generate_skill_gap_report,
    generate_source_list,
)


class ReportsAutomationTests(unittest.TestCase):
    def test_generate_markdown_report_creates_file(self):
        report_path = generate_markdown_report(
            title="Weekly AI Notes",
            sections={
                "Highlights": ["Model quality is improving."],
                "Actions": ["Keep validating local tooling."],
            },
        )

        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("Weekly AI Notes", content)
        self.assertIn("Highlights", content)

    def test_generate_report_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(ValueError):
                generate_markdown_report(
                    title="Bad Path Report",
                    sections={"Notes": ["Should fail"]},
                    output_dir=os.path.join(tmp_dir, "..", "escape"),
                )

    def test_research_report_preserves_sources(self):
        report_path = generate_research_report(
            title="Remote AI Research",
            summary="AI agents are becoming more useful for structured tasks.",
            sources=[
                {"title": "AI Research Brief", "url": "https://example.com/ai-research"},
                {"title": "Job Market Snapshot", "url": "https://example.com/job-market"},
            ],
            findings=["Local agents can be modular and safe.", "Research should be grounded in source outputs."],
        )

        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("AI Research Brief", content)
        self.assertIn("https://example.com/ai-research", content)

    def test_failed_report_generation_raises_value_error(self):
        with self.assertRaises(ValueError):
            generate_markdown_report(title="", sections={"Notes": ["No title"]})

        with self.assertRaises(ValueError):
            generate_markdown_report(title="Missing sections", sections={})

    def test_automation_task_creation(self):
        task = create_automation_task(
            name="daily-tech-research",
            cadence="daily",
            task_type="technology_research",
            payload={"topic": "AI agents"},
        )

        self.assertIsInstance(task, AutomationTask)
        self.assertEqual(task.cadence, "daily")
        self.assertEqual(task.task_type, "technology_research")

    def test_invalid_schedule_is_rejected(self):
        with self.assertRaises(ValueError):
            create_automation_task(
                name="bad-schedule",
                cadence="monthly",
                task_type="career_report",
                payload={"goal": "test"},
            )

    def test_execution_failure_surfaces_error(self):
        task = create_automation_task(
            name="broken-task",
            cadence="weekly",
            task_type="career_report",
            payload={"job_title": None},
        )

        result = execute_automation_task(task)
        self.assertFalse(result["success"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
