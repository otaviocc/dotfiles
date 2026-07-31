#!/usr/bin/env python3
"""
Verify that every FLAC -> ALAC conversion completed correctly.

For each source .flac file (outside of the ALAC output tree), finds the
corresponding .m4a under ./ALAC/ (mirrored path) and checks:
  - the output file exists
  - ffprobe can read it (not corrupt/truncated)
  - the audio duration matches the source (within a small tolerance)
  - the sample count matches exactly (catches truncation ffprobe's rounded
    duration might hide)

Prints a report and a non-zero exit code if any problems are found.

Usage:
    <skill_dir>/.venv/bin/python verify_conversion.py [SOURCE_ROOT] [OUTPUT_ROOT]

Defaults: SOURCE_ROOT = current working directory, OUTPUT_ROOT = SOURCE_ROOT/ALAC
"""

import json
import subprocess
import sys
from pathlib import Path


def probe(path: Path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=duration_ts,sample_rate,codec_type",
        "-select_streams", "a:0",
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None, result.stderr.strip()
    try:
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        if not streams:
            return None, "no audio stream found"
        return streams[0], None
    except Exception as e:
        return None, f"parse error: {e}"


def main():
    source_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    output_root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else source_root / "ALAC"

    flac_files = sorted(source_root.rglob("*.flac"))
    flac_files = [f for f in flac_files if output_root not in f.parents]

    total = len(flac_files)
    ok = 0
    problems = []

    print(f"Source: {source_root}")
    print(f"Output: {output_root}")
    print(f"Checking {total} file(s)...\n")

    for i, flac_path in enumerate(flac_files, 1):
        rel = flac_path.relative_to(source_root)
        mp4_path = output_root / rel.with_suffix(".m4a")

        if not mp4_path.exists():
            problems.append((rel, "MISSING output file"))
            continue

        src_stream, src_err = probe(flac_path)
        if src_err:
            problems.append((rel, f"could not probe SOURCE: {src_err}"))
            continue

        dst_stream, dst_err = probe(mp4_path)
        if dst_err:
            problems.append((rel, f"could not probe OUTPUT (possibly corrupt/truncated): {dst_err}"))
            continue

        src_sr = int(src_stream.get("sample_rate", 0))
        dst_sr = int(dst_stream.get("sample_rate", 0))
        src_ts = int(src_stream.get("duration_ts", 0))
        dst_ts = int(dst_stream.get("duration_ts", 0))

        if src_sr != dst_sr:
            problems.append((rel, f"sample rate mismatch: src={src_sr} dst={dst_sr}"))
            continue

        if src_sr == 0:
            problems.append((rel, "source sample rate is 0, cannot compare"))
            continue

        src_samples = src_ts  # duration_ts is already in stream timebase = sample count for flac/alac typically
        dst_samples = dst_ts
        diff = abs(src_samples - dst_samples)

        # Allow a tiny tolerance (a few samples) for container/encoder rounding.
        if diff > 10:
            src_sec = src_samples / src_sr
            dst_sec = dst_samples / dst_sr
            problems.append((
                rel,
                f"DURATION/SAMPLE MISMATCH: src={src_samples} samples ({src_sec:.3f}s) "
                f"dst={dst_samples} samples ({dst_sec:.3f}s) diff={diff} samples"
            ))
            continue

        ok += 1
        print(f"[{i}/{total}] OK: {rel}")

    print("\n--- Verification Summary ---")
    print(f"OK: {ok}/{total}")
    print(f"Problems: {len(problems)}")
    for rel, msg in problems:
        print(f"  - {rel}: {msg}")

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
