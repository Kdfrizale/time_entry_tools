import unittest

from time_entry_tools.workrecord import roundHoursForLibrary


class MyTestCase(unittest.TestCase):
    def test_rounding_for_library_Same_Number(self):
        self.assertEqual("1.0h", roundHoursForLibrary(1.0))

    def test_rounding_for_library_Round_Down(self):
        self.assertEqual("1.0h", roundHoursForLibrary(1.12))

    def test_rounding_for_library_Round_Up(self):
        self.assertEqual("1.25h", roundHoursForLibrary(1.13))

    def test_rounding_for_library_Round_Up_Borderline(self):
        self.assertEqual("1.25h", roundHoursForLibrary(1.126))

    def test_rounding_for_library_Round_Down_to_zeroth_quarter(self):
        self.assertEqual("5.0h", roundHoursForLibrary(5.1))

    def test_rounding_for_library_Round_Rown_to_first_quarter(self):
        self.assertEqual("7.25h", roundHoursForLibrary(7.31))

    def test_rounding_for_library_Round_Rown_to_second_quarter(self):
        self.assertEqual("3.5h", roundHoursForLibrary(3.62))

    def test_rounding_for_library_Round_Rown_to_third_quarter(self):
        self.assertEqual("0.75h", roundHoursForLibrary(0.8))

    def test_rounding_for_library_Round_Up_to_first_quarter(self):
        self.assertEqual("9.25h", roundHoursForLibrary(9.21))

    def test_rounding_for_library_Round_Up_to_second_quarter(self):
        self.assertEqual("4.5h", roundHoursForLibrary(4.45))

    def test_rounding_for_library_Round_Up_to_third_quarter(self):
        self.assertEqual("8.75h", roundHoursForLibrary(8.66))

    def test_rounding_for_library_Round_Up_to_zeroth_quarter(self):
        self.assertEqual("6.0h", roundHoursForLibrary(5.88))

    def test_rounding_for_library_Long_Decimal_Input(self):
        self.assertEqual("1.25h", roundHoursForLibrary(1.177777777777777777777777))

    def test_rounding_for_library_Large_Input(self):
        self.assertEqual("234.75h", roundHoursForLibrary(234.68))

    def test_rounding_for_library_Negative_Input(self):
        self.assertEqual("-1.0h", roundHoursForLibrary(-1))

    def test_rounding_for_library_Zero_Input(self):
        self.assertEqual("0.0h", roundHoursForLibrary(0))


if __name__ == '__main__':
    unittest.main()
