import unittest
from unittest.mock import patch

from tools.career_intelligence import analyze_skill_gap, career_intelligence, extract_job_requirements
from tools.research_synthesis import research_and_synthesize
from tools.result import ToolResult


class ResearchAndCareerTests(unittest.TestCase):
    @patch("tools.research_synthesis.generate_response")
    @patch("tools.research_synthesis.web_search")
    def test_research_synthesis_returns_answer_with_sources(self, mock_web_search, mock_generate_response):
        mock_web_search.return_value = ToolResult(
            True,
            "web_search",
            result=[
                {"title": "AI Research News", "url": "https://example.com/ai"},
                {"title": "Latest AI Trends", "url": "https://example.com/trends"},
            ],
        )
        mock_generate_response.return_value = "Summary: AI is evolving quickly.\n\nSources: AI Research News, Latest AI Trends"

        result = research_and_synthesize("latest AI trends")

        self.assertTrue(result.success)
        self.assertEqual(result.tool_name, "research_synthesis")
        self.assertEqual(len(result.result["sources"]), 2)
        self.assertEqual(result.result["sources"][0]["title"], "AI Research News")
        self.assertIn("https://example.com/ai", result.result["sources"][0]["url"])

    @patch("tools.research_synthesis.web_search")
    def test_research_synthesis_handles_no_results(self, mock_web_search):
        mock_web_search.return_value = ToolResult(False, "web_search", error="No results found")

        result = research_and_synthesize("really obscure query that should fail")

        self.assertFalse(result.success)
        self.assertIn("No results", result.error)

    def test_research_synthesis_rejects_invalid_query(self):
        result = research_and_synthesize("   ")
        self.assertFalse(result.success)
        self.assertIn("empty", result.error.lower())

    def test_extract_job_requirements(self):
        description = """
        Senior Python Developer
        We are hiring a Senior Python Developer with 5+ years of experience.
        Required skills: Python, SQL, AWS, Docker, REST APIs.
        Bachelor's degree preferred.
        Responsibilities include design, leadership, and data analysis.
        """

        result = extract_job_requirements(description)

        self.assertTrue(result.success)
        self.assertIn("Senior Python Developer", result.result["job_title"])
        self.assertIn("python", result.result["required_skills"])
        self.assertIn("aws", result.result["required_skills"])
        self.assertIn("experience", str(result.result["experience"]).lower())

    def test_analyze_skill_gap_reports_missing_and_partial_skills(self):
        job_text = """
        Data Scientist role requiring Python, SQL, machine learning, AWS, and communication.
        Experience with statistics and pandas is preferred.
        """
        user_skills = ["python", "sql", "communication"]

        result = analyze_skill_gap(job_text, user_skills)

        self.assertTrue(result.success)
        self.assertIn("python", result.result["matched_skills"])
        self.assertIn("aws", result.result["missing_skills"])
        self.assertIn("machine learning", result.result["missing_skills"])
        self.assertTrue(result.result["learning_priorities"])

    def test_career_intelligence_invalid_input(self):
        result = career_intelligence("   ")
        self.assertFalse(result.success)
        self.assertIn("empty", result.error.lower())


if __name__ == "__main__":
    unittest.main()
