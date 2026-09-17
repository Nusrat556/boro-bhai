import unittest

from tools.calculator import calculate


class CalculatorTests(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(calculate("2 + 3"), 5)

    def test_multiplication(self):
        self.assertEqual(calculate("12 * 5"), 60)

    def test_division(self):
        self.assertEqual(calculate("10 / 2"), 5)

    def test_power(self):
        self.assertEqual(calculate("2 ** 3"), 8)

    def test_invalid_expression(self):
        with self.assertRaises(ValueError):
            calculate("2 + x")

    def test_division_by_zero(self):
        with self.assertRaises(ValueError):
            calculate("5 / 0")


if __name__ == "__main__":
    unittest.main()
