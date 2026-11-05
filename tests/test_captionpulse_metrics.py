import unittest

import tool


class CaptionPulseMetricsTest(unittest.TestCase):
    def test_wer_alignment_revision_and_delay_percentiles(self):
        doc = {
            "reference": ["hello", "world", "again"],
            "events": [
                {"emitted_ms": 100, "text": "helo", "final": False},
                {"emitted_ms": 200, "text": "hello wor", "final": False},
                {"emitted_ms": 250, "text": "hello wor", "final": False},
                {
                    "emitted_ms": 900,
                    "text": "hello word again",
                    "final": True,
                    "words": [
                        {"word": "hello", "end_ms": 300},
                        {"word": "word", "end_ms": 600},
                        {"word": "again", "end_ms": 800},
                    ],
                },
            ],
        }
        result = tool.analyze(doc)
        self.assertEqual(result["partial_revision_count"], 2)
        self.assertAlmostEqual(result["word_error_rate"], 1 / 3)
        self.assertEqual(result["error_counts"], {"substitutions": 1, "deletions": 0, "insertions": 0})
        self.assertEqual(result["alignment"][1], {"op": "substitute", "ref": "world", "hyp": "word"})
        self.assertEqual(result["display_delay_ms"]["count"], 3)
        self.assertEqual(result["display_delay_ms"]["p50"], 300)
        self.assertEqual(result["display_delay_ms"]["p90"], 540)
        self.assertEqual(result["display_delay_ms"]["max"], 600)

    def test_insertions_and_empty_delay_samples_are_explicit(self):
        result = tool.analyze({"reference": ["go"], "events": [{"text": "go now", "final": True}]})
        self.assertEqual(result["error_counts"]["insertions"], 1)
        self.assertEqual(result["word_error_rate"], 1.0)
        self.assertEqual(result["display_delay_ms"], {"count": 0, "p50": None, "p90": None, "max": None})


if __name__ == "__main__":
    unittest.main()
