import os
import tempfile
import unittest

from app.agent import create_plan, execute_plan, route_task
from rag.vector_store import VectorStore
from tools.rag_tool import rag_query


class RAGAndPlanningTests(unittest.TestCase):
    def test_vector_store_search_returns_relevant_chunks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(os.path.join(tmpdir, "rag_store.json"))
            store.add_document("Python is a high-level programming language used for automation and AI.", "notes.txt")
            results = store.search("What is Python used for?", top_k=3)

            self.assertTrue(results)
            self.assertGreater(results[0]["score"], 0.0)

    def test_rag_tool_returns_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "rag_store.json")
            os.environ["BORO_BHAI_RAG_STORE"] = store_path
            store = VectorStore(store_path)
            store.add_document("AI agents use planning, tools, and memory to complete tasks.", "notes.txt")
            try:
                result = rag_query("How do AI agents work?", top_k=3)
                self.assertTrue(result.success)
                self.assertIn("matches", result.result)
                self.assertIn("context", result.result)
            finally:
                os.environ.pop("BORO_BHAI_RAG_STORE", None)

    def test_route_task_uses_planner_for_multi_step_requests(self):
        route = route_task("Build a plan for researching AI agents and then synthesizing the findings.")
        self.assertEqual(route, "planner")

    def test_create_plan_and_execute_plan(self):
        plan = create_plan("Research AI agents, then summarize the findings for a job application.")
        self.assertGreaterEqual(len(plan["steps"]), 2)

        executed = execute_plan(plan)
        self.assertTrue(executed["success"])
        self.assertTrue(executed["steps"])


if __name__ == "__main__":
    unittest.main()
