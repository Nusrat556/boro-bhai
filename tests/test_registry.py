import unittest

from app.agent import route_task, run_agent
from tools.registry import build_registry


class ToolRegistryTests(unittest.TestCase):
    def test_calculator_registered(self):
        registry = build_registry()
        self.assertIn("calculator", registry.list_tools())
        self.assertTrue(callable(registry.get("calculator")))

    def test_all_primary_tools_registered(self):
        registry = build_registry()
        for name in ("calculator", "text_file", "csv", "pdf"):
            self.assertIn(name, registry.list_tools())
            self.assertTrue(callable(registry.get(name)))

    def test_route_task_for_calculator(self):
        self.assertEqual(route_task("What is 25 * 4?"), "calculator")

    def test_route_task_for_txt_file(self):
        self.assertEqual(route_task("Please read data/example.txt and summarize it."), "text_file")

    def test_route_task_for_csv_file(self):
        self.assertEqual(route_task("Analyze data/sample.csv for missing values."), "csv")

    def test_route_task_for_pdf_file(self):
        self.assertEqual(route_task("Read data/sample.pdf and summarize the text."), "pdf")

    def test_route_task_for_normal_conversation(self):
        self.assertEqual(route_task("What is the capital of France?"), "llm")

    def test_route_task_rejects_blank_input(self):
        with self.assertRaises(ValueError):
            route_task("   ")

    def test_run_agent_rejects_blank_input(self):
        with self.assertRaises(ValueError):
            run_agent("   ")

    def test_unknown_request_routes_to_llm(self):
        self.assertEqual(route_task("Tell me a joke about robots."), "llm")


if __name__ == "__main__":
    unittest.main()
