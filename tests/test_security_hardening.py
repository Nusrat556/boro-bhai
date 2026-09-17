import io
import os
import unittest
from unittest.mock import patch

from app.agent import create_plan, execute_plan, run_agent
from api.service import handle_upload
from config import Settings


class SecurityHardeningTests(unittest.TestCase):
    def test_settings_reject_invalid_environment(self):
        with patch.dict(os.environ, {"BORO_BHAI_ENV": "staging"}, clear=False):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_run_agent_rejects_empty_task(self):
        with self.assertRaises(ValueError):
            run_agent("   ")

    def test_planner_execution_is_bounded(self):
        plan = create_plan("Research AI agents, track current news, and compare requirements for a product manager role.")
        self.assertLessEqual(len(plan["steps"]), 4)

        executed = execute_plan(plan)
        self.assertTrue(executed["success"])
        self.assertLessEqual(len(executed["steps"]), 4)

    def test_handle_upload_rejects_path_traversal(self):
        file_storage = io.BytesIO(b"hello world")
        file_storage.filename = "../../secret.txt"
        with self.assertRaises(ValueError):
            handle_upload(file_storage)

    def test_handle_upload_rejects_invalid_extension(self):
        file_storage = io.BytesIO(b"hello")
        file_storage.filename = "notes.exe"
        with self.assertRaises(ValueError):
            handle_upload(file_storage)

    def test_handle_upload_rejects_oversized_file(self):
        from api import service

        file_storage = io.BytesIO(b"x" * (service.MAX_UPLOAD_BYTES + 1))
        file_storage.filename = "large.txt"
        with self.assertRaises(ValueError):
            handle_upload(file_storage)


if __name__ == "__main__":
    unittest.main()
