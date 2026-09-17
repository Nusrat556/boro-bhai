import unittest

from tools.registry import build_registry


class ToolRegistryTests(unittest.TestCase):
    def test_calculator_registered(self):
        registry = build_registry()
        self.assertIn("calculator", registry.list_tools())
        self.assertTrue(callable(registry.get("calculator")))


if __name__ == "__main__":
    unittest.main()
