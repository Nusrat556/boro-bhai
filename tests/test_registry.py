import unittest
from unittest.mock import Mock, patch

from app.agent import route_task, run_agent
from tools.registry import build_registry
from tools.web_search import web_search


class ToolRegistryTests(unittest.TestCase):
    def test_calculator_registered(self):
        registry = build_registry()
        self.assertIn("calculator", registry.list_tools())
        self.assertTrue(callable(registry.get("calculator")))

    def test_all_primary_tools_registered(self):
        registry = build_registry()
        for name in ("calculator", "text_file", "csv", "pdf", "web_search"):
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

    def test_route_task_for_web_search(self):
        self.assertEqual(route_task("What are the latest AI news updates today?"), "web_search")

    def test_route_task_rejects_blank_input(self):
        with self.assertRaises(ValueError):
            route_task("   ")

    def test_run_agent_rejects_blank_input(self):
        with self.assertRaises(ValueError):
            run_agent("   ")

    def test_unknown_request_routes_to_llm(self):
        self.assertEqual(route_task("Tell me a joke about robots."), "llm")

    @patch("tools.web_search.urllib.request.urlopen")
    def test_web_search_tool_returns_success(self, mock_urlopen):
        mock_response = Mock()
        mock_response.read.return_value = b'''<html>
            <a class="result-link" href="https://example.com/ai-news">AI News</a>
            <a class="result-link" href="https://example.com/ai-latest">AI Latest</a>
        </html>'''
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = web_search("latest AI news")
        self.assertTrue(result.success)
        self.assertEqual(result.tool_name, "web_search")
        self.assertEqual(len(result.result), 2)
        self.assertIn("AI News", result.result[0]["title"])

    def test_web_search_rejects_invalid_query(self):
        result = web_search("   ")
        self.assertFalse(result.success)
        self.assertIn("Invalid", result.error)

    @patch("tools.web_search.urllib.request.urlopen", side_effect=TimeoutError("timed out"))
    def test_web_search_handles_timeout(self, _mock_urlopen):
        result = web_search("latest AI news")
        self.assertFalse(result.success)
        self.assertIn("timed out", result.error.lower())


if __name__ == "__main__":
    unittest.main()
