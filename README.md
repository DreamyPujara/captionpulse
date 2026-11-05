# CaptionPulse

CaptionPulse is a small offline debugger for developers building live-caption UI. It analyzes supplied synthetic reference words and caption events; it does not record audio, call a network service, or claim real-world accuracy.

## User problem

When a caption demo feels bad, it is hard to tell whether the issue is word mistakes, excessive partial-caption churn, or captions appearing late. CaptionPulse reports all three from one JSON fixture.

## Demo

```bash
python tool.py examples/tiny_caption_session.json
```

Output includes:

- `word_error_rate` plus alignment evidence for each equal/substitute/delete/insert decision
- `partial_revision_count` for changed non-final captions before finalization
- `display_delay_ms` p50, p90, max, and sample count from final word end times

## Input shape

```json
{"reference":["hello","world"],"events":[{"emitted_ms":300,"text":"hello","final":false},{"emitted_ms":900,"text":"hello word","final":true,"words":[{"word":"hello","end_ms":400},{"word":"word","end_ms":700}]}]}
```

## Metrics

WER is `(substitutions + deletions + insertions) / reference_word_count`. Percentiles use linear interpolation over delay samples. If no reference words or delay samples exist, the relevant value is `null`.

## Tradeoffs and non-goals

This first version intentionally accepts a simple JSON file only. It does not stream events, align timestamps to references, parse vendor formats, evaluate audio, store personal data, or make network calls.

## AI assistance

This code and documentation were generated with AI assistance. Review the implementation and run the tests before using it in a workflow.
