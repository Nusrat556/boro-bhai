import os
import tempfile
import unittest

from app.agent import _build_memory_context
from memory.database import get_recent_memories, get_relevant_context, initialize_db, save_memory


class MemoryTests(unittest.TestCase):
    def test_save_and_retrieve_memory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test_memory.db")
            connection = initialize_db(db_path)
            connection.close()
            save_memory("What is AI?", "AI is intelligence in software.", db_path)
            memories = get_recent_memories(limit=5, db_path=db_path)
            self.assertEqual(len(memories), 1)
            self.assertIn("What is AI?", memories[0]["user_input"])
            self.assertIn("AI is intelligence in software.", memories[0]["agent_response"])

    def test_empty_memory_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "empty_memory.db")
            connection = initialize_db(db_path)
            connection.close()
            self.assertEqual(get_recent_memories(limit=5, db_path=db_path), [])
            self.assertEqual(get_relevant_context("hello there", db_path=db_path), [])

    def test_multiple_conversations_are_retrieved(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "multi_memory.db")
            connection = initialize_db(db_path)
            connection.close()
            save_memory("What is the capital of France?", "Paris is the capital of France.", db_path)
            save_memory("What is 2 + 2?", "4.", db_path)
            save_memory("Tell me a joke.", "Why did the robot cross the road? To get to the other side.", db_path)
            memories = get_recent_memories(limit=10, db_path=db_path)
            self.assertEqual(len(memories), 3)
            self.assertIn("Tell me a joke.", memories[0]["user_input"])
            self.assertIn("What is the capital of France?", memories[-1]["user_input"])

    def test_relevant_context_uses_topic_similarity(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "context_memory.db")
            connection = initialize_db(db_path)
            connection.close()
            save_memory("What is the capital of France?", "Paris is the capital of France.", db_path)
            save_memory("What is 2 + 2?", "4.", db_path)
            context = get_relevant_context("Tell me more about France's capital city.", db_path=db_path)
            self.assertTrue(context)
            self.assertIn("capital of France", context[0]["user_input"])

    def test_agent_builds_memory_context_string(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "agent_context.db")
            connection = initialize_db(db_path)
            connection.close()
            save_memory("What is my favorite color?", "Your favorite color is blue.", db_path)
            context = _build_memory_context("What was my favorite color again?", db_path=db_path)
            self.assertIn("favorite color", context.lower())
            self.assertIn("blue", context.lower())
    def test_same_session_retrieves_name_memory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "session_memory.db")
            connection = initialize_db(db_path)
            connection.close()
            save_memory("i am jonayed", "Nice to meet you, Jonayed.", db_path=db_path, session_id="session-123")
            context = get_relevant_context("what was my name?", db_path=db_path, session_id="session-123")
            self.assertTrue(context)
            self.assertIn("jonayed", context[0]["user_input"].lower())

if __name__ == "__main__":
    unittest.main()
