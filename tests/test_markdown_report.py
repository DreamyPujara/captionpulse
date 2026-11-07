import unittest

import tool


class MarkdownReportTests(unittest.TestCase):
    def test_markdown_report_is_deterministic_and_explains_limits(self):
        report = tool.analyze({
            "reference": ["hello", "world", "again"],
            "events": [
                {"emitted_ms": 250, "text": "helo", "final": False},
                {"emitted_ms": 420, "text": "hello wor", "final": False},
                {
                    "emitted_ms": 900,
                    "text": "hello word again",
                    "final": True,
                    "words": [
                        {"word": "hello", "end_ms": 300},
                        {"word": "word", "end_ms": 620},
                        {"word": "again", "end_ms": 760},
                    ],
                },
            ],
        })

        markdown = tool.render_markdown(report)

        self.assertEqual(markdown, tool.render_markdown(report))
        self.assertIn("# CaptionPulse Report\n", markdown)
        self.assertIn("- Word error rate: 0.333", markdown)
        self.assertIn("- Display delay p50/p90/max ms: 280 / 536 / 600", markdown)
        self.assertIn("| substitute | world | word |", markdown)
        self.assertIn("does not evaluate audio", markdown)


if __name__ == "__main__":
    unittest.main()
