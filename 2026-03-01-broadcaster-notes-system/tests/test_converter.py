from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from broadcaster_notes.converter import convert_text, detect_entities, write_markdown


SAMPLE_TEXT = """Friday Prep
Head Coach Marcus Freeman met with Assistant Coach James Laurinaitis on March 1, 2026.
Notre Dame University hosts USC on 09/03/2026.
Marcus Freeman, head coach, said the defensive depth improved.
"""


class ConverterTests(unittest.TestCase):
    def test_detect_entities_by_type(self) -> None:
        entities = detect_entities(SAMPLE_TEXT)
        pairs = {(entity.kind, entity.normalized) for entity in entities}
        self.assertIn(("coach", "Marcus Freeman"), pairs)
        self.assertIn(("coach", "James Laurinaitis"), pairs)
        self.assertIn(("school", "Notre Dame University"), pairs)
        self.assertIn(("school", "USC"), pairs)
        self.assertIn(("date", "2026-03-01"), pairs)
        self.assertIn(("date", "2026-09-03"), pairs)
        self.assertIn(("role", "Head Coach"), pairs)
        self.assertIn(("role", "Assistant Coach"), pairs)

    def test_convert_text_renders_frontmatter_and_backlinks(self) -> None:
        markdown = convert_text(SAMPLE_TEXT, source="google-docs-export")
        self.assertIn('source: "google-docs-export"', markdown)
        self.assertIn('  - "Marcus Freeman"', markdown)
        self.assertIn("[[Marcus Freeman]]", markdown)
        self.assertIn("[[Head Coach]]", markdown)
        self.assertIn("[[2026-03-01|March 1, 2026]]", markdown)
        self.assertIn("[[Notre Dame University]]", markdown)

    def test_write_markdown_creates_expected_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_markdown(SAMPLE_TEXT, Path(tmpdir))
            self.assertTrue(output.exists())
            self.assertEqual(output.name, "friday-prep.md")


if __name__ == "__main__":
    unittest.main()