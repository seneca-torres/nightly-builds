import io
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import quicklog


class QuicklogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.path = self.base / "2026-02-23.md"
        self.now = datetime(2026, 2, 23, 14, 5)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _read_text(self) -> str:
        return self.path.read_text(encoding="utf-8")

    def test_creates_new_file_with_template(self) -> None:
        quicklog._append_note(self.path, "First note", "event", self.now)
        content = self._read_text()
        self.assertTrue(self.path.exists())
        self.assertIn("# Daily Log — 2026-02-23", content)
        self.assertIn("## Summary", content)
        self.assertIn("*(no entries yet)*", content)
        self.assertIn("## Events", content)

    def test_appends_notes_with_timestamps(self) -> None:
        quicklog._append_note(self.path, "Timestamped note", "event", self.now)
        content = self._read_text()
        self.assertIn("### [2026-02-23] Event", content)
        self.assertIn("- [14:05] Timestamped note", content)

    def test_categories_create_sections(self) -> None:
        quicklog._append_note(self.path, "Idea note", "idea", self.now)
        content = self._read_text()
        self.assertIn("## Ideas", content)
        self.assertIn("### [2026-02-23] Idea", content)
        self.assertIn("- [14:05] Idea note", content)

    def test_list_returns_last_five_bullets(self) -> None:
        for i in range(7):
            now = self.now + timedelta(minutes=i)
            quicklog._append_note(self.path, f"note {i}", "event", now)
        buf = io.StringIO()
        with redirect_stdout(buf):
            quicklog._list_recent(self.path)
        output = buf.getvalue().strip().splitlines()
        expected = [
            "- [14:07] note 2",
            "- [14:08] note 3",
            "- [14:09] note 4",
            "- [14:10] note 5",
            "- [14:11] note 6",
        ]
        self.assertEqual(output, expected)

    def test_multiline_notes_are_indented(self) -> None:
        note = "Line one\nLine two\nLine three"
        quicklog._append_note(self.path, note, "event", self.now)
        content = self._read_text()
        self.assertIn("- [14:05] Line one", content)
        self.assertIn("  Line two", content)
        self.assertIn("  Line three", content)


if __name__ == "__main__":
    unittest.main()
