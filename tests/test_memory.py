import os
import tempfile
import unittest

from memory.database import get_recent_memories, initialize_db, save_memory


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


if __name__ == "__main__":
    unittest.main()
