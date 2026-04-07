import argparse
import json
import unittest

import cfbd_staff


def demo_args(**overrides):
    base = dict(
        demo=True,
        output=None,
        school="Alabama",
        year=2024,
        format="markdown",
        coach="Kalen",
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class TestCFBDStaffDemo(unittest.TestCase):
    def test_staff_demo(self):
        args = demo_args()
        text = cfbd_staff.command_staff(args)
        self.assertIn("Kalen DeBoer", text)
        self.assertIn("Head Coach", text)

    def test_history_demo(self):
        args = demo_args(coach="Grubb")
        text = cfbd_staff.command_history(args)
        self.assertIn("Ryan Grubb", text)
        self.assertIn("2023", text)

    def test_export_markdown(self):
        args = demo_args(format="markdown")
        text = cfbd_staff.command_export(args)
        self.assertIn("---", text)
        self.assertIn("# Alabama Coaching Staff 2024", text)
        self.assertIn("| Coach | Role | Hire Date |", text)

    def test_export_json(self):
        args = demo_args(format="json")
        text = cfbd_staff.command_export(args)
        data = json.loads(text)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_export_csv(self):
        args = demo_args(format="csv")
        text = cfbd_staff.command_export(args)
        self.assertIn("first_name", text.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
