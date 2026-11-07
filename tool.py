import argparse
import json
import math
import re
import sys

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def words(text):
    return [m.group(0).lower() for m in WORD_RE.finditer(text or "")]


def align(ref, hyp):
    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0], back[i][0] = i, "delete"
    for j in range(1, m + 1):
        dp[0][j], back[0][j] = j, "insert"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                best = (dp[i - 1][j - 1], "equal")
            else:
                best = (dp[i - 1][j - 1] + 1, "substitute")
            for cand in ((dp[i - 1][j] + 1, "delete"), (dp[i][j - 1] + 1, "insert")):
                if cand[0] < best[0]:
                    best = cand
            dp[i][j], back[i][j] = best
    i, j, out = n, m, []
    while i or j:
        op = back[i][j]
        if op in ("equal", "substitute"):
            out.append({"op": op, "ref": ref[i - 1], "hyp": hyp[j - 1]})
            i -= 1; j -= 1
        elif op == "delete":
            out.append({"op": op, "ref": ref[i - 1], "hyp": None})
            i -= 1
        else:
            out.append({"op": op, "ref": None, "hyp": hyp[j - 1]})
            j -= 1
    out.reverse()
    counts = {"substitutions": 0, "deletions": 0, "insertions": 0}
    for item in out:
        if item["op"] == "substitute": counts["substitutions"] += 1
        if item["op"] == "delete": counts["deletions"] += 1
        if item["op"] == "insert": counts["insertions"] += 1
    return out, counts


def percentile(values, pct):
    if not values:
        return None
    vals = sorted(values)
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * pct / 100.0
    lo = math.floor(pos); hi = math.ceil(pos)
    if lo == hi:
        return vals[int(pos)]
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def revision_count(events):
    count, last_partial = 0, None
    for ev in events:
        text = " ".join(words(ev.get("text", "")))
        if ev.get("final"):
            last_partial = None
        elif text != last_partial:
            count += 1
            last_partial = text
    return count


def final_words_and_delays(events):
    final_text = ""
    delays = []
    for ev in events:
        if ev.get("final"):
            final_text = ev.get("text", "")
            emitted = ev.get("emitted_ms")
            for w in ev.get("words", []):
                if emitted is not None and "end_ms" in w:
                    delays.append(emitted - w["end_ms"])
    return words(final_text), delays


def analyze(doc):
    ref = [str(w).lower() for w in doc.get("reference", [])]
    events = doc.get("events", [])
    hyp, delays = final_words_and_delays(events)
    alignment, counts = align(ref, hyp)
    errors = counts["substitutions"] + counts["deletions"] + counts["insertions"]
    return {
        "reference_word_count": len(ref),
        "final_word_count": len(hyp),
        "word_error_rate": None if not ref else errors / len(ref),
        "error_counts": counts,
        "alignment": alignment,
        "partial_revision_count": revision_count(events),
        "display_delay_ms": {
            "count": len(delays),
            "p50": percentile(delays, 50),
            "p90": percentile(delays, 90),
            "max": max(delays) if delays else None,
        },
    }


def fmt(value):
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


def render_markdown(report):
    delay = report["display_delay_ms"]
    counts = report["error_counts"]
    lines = [
        "# CaptionPulse Report",
        "",
        "## Summary",
        "",
        f"- Reference words: {report['reference_word_count']}",
        f"- Final caption words: {report['final_word_count']}",
        f"- Word error rate: {fmt(report['word_error_rate'])}",
        f"- Partial revision count: {report['partial_revision_count']}",
        f"- Display delay samples: {delay['count']}",
        f"- Display delay p50/p90/max ms: {fmt(delay['p50'])} / {fmt(delay['p90'])} / {fmt(delay['max'])}",
        "",
        "## Error counts",
        "",
        f"- Substitutions: {counts['substitutions']}",
        f"- Deletions: {counts['deletions']}",
        f"- Insertions: {counts['insertions']}",
        "",
        "## Alignment evidence",
        "",
        "| op | reference | caption |",
        "| --- | --- | --- |",
    ]
    for item in report["alignment"]:
        lines.append(f"| {item['op']} | {item['ref'] or ''} | {item['hyp'] or ''} |")
    lines.extend([
        "",
        "## Assumptions and limitations",
        "",
        "- Input is a synthetic JSON fixture supplied by the developer.",
        "- Final-word delays are computed as final event emitted_ms minus each supplied word end_ms.",
        "- WER is text-only and does not evaluate audio or claim real-world caption accuracy.",
        "- The tool runs offline and makes no network calls.",
    ])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline caption quality debugger")
    parser.add_argument("input_json", help="synthetic reference and caption events JSON")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    with open(args.input_json, "r", encoding="utf-8") as f:
        report = analyze(json.load(f))
    if args.format == "markdown":
        sys.stdout.write(render_markdown(report))
    else:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
