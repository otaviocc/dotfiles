#!/usr/bin/env python3
"""
flac-to-alac.py

Convert every FLAC under a directory to ALAC (.m4a) using ffmpeg.
Metadata and embedded album art are preserved (-map 0, -c:v copy).

Requires ffmpeg: brew install ffmpeg

USAGE
    python3 flac-to-alac.py --root /path/to/music              # dry run
    python3 flac-to-alac.py --root /path/to/music --apply      # convert + delete FLAC
    python3 flac-to-alac.py --root /path/to/music --apply --keep-original  # convert only

OPTIONS
    --root PATH         Directory to scan (default: current directory).
    --apply             Execute the conversions (default is dry run).
    --keep-original     Do not delete the FLAC after a verified conversion.
    --no-verify         Skip the lossless verification step.
"""

import argparse
import os
import signal
import subprocess
import sys

try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, OSError):
    pass


def check_ffmpeg():
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except FileNotFoundError:
        if sys.platform == "darwin":
            hint = "brew install ffmpeg"
        else:
            hint = "your package manager (apt install ffmpeg, dnf install ffmpeg, etc.)"
        print(f"Error: ffmpeg not found. Install with: {hint}",
              file=sys.stderr)
        sys.exit(1)


def find_flacs(root):
    flacs = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith(".flac"):
                flacs.append(os.path.join(dirpath, fn))
    return sorted(flacs)


def convert(src, dst):
    cmd = [
        "ffmpeg", "-nostdin", "-loglevel", "error", "-y",
        "-i", src,
        "-c:a", "alac", "-c:v", "copy", "-map", "0",
        dst,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAIL: {src}", file=sys.stderr)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                print(f"    {line}", file=sys.stderr)
        return False
    return True


def verify(src, dst):
    """Decode both files to raw PCM and compare byte-for-byte."""
    def decode(path):
        return subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-y",
             "-i", path, "-f", "s32le", "-acodec", "pcm_s32le", "-"],
            capture_output=True,
        )

    src_pcm = decode(src)
    dst_pcm = decode(dst)

    if src_pcm.returncode != 0 or dst_pcm.returncode != 0:
        return False
    return src_pcm.stdout == dst_pcm.stdout


def main():
    ap = argparse.ArgumentParser(
        description="Convert FLAC files to ALAC using ffmpeg",
    )
    ap.add_argument("--root", default=".", help="Directory to scan (default: .)")
    ap.add_argument("--apply", action="store_true",
                    help="Execute the conversions (default is dry run)")
    ap.add_argument("--keep-original", action="store_true",
                    help="Do not delete the FLAC after conversion")
    ap.add_argument("--no-verify", action="store_true",
                    help="Skip lossless verification via PCM comparison")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    apply = args.apply
    remove = apply and not args.keep_original
    verify_on = not args.no_verify

    check_ffmpeg()

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"root={root}  mode={'APPLY' if apply else 'DRY RUN'}  "
          f"verify={'on' if verify_on else 'off'}  "
          f"remove={'on' if remove else 'off'}")
    print("-" * 70)

    flacs = find_flacs(root)

    planned = converted = deleted = skipped = failed = verified = 0

    for src in flacs:
        dst = src[:-5] + ".m4a"

        if os.path.exists(dst):
            print(f"  (exists) {os.path.relpath(dst, root)}")
            skipped += 1
            continue

        print(f"{os.path.relpath(src, root)} -> {os.path.relpath(dst, root)}")
        planned += 1

        if apply:
            if convert(src, dst):
                converted += 1
                if verify_on:
                    if verify(src, dst):
                        verified += 1
                    else:
                        print(f"  WARNING: verification failed for {src}",
                              file=sys.stderr)
                if remove and os.path.exists(dst) and os.path.getsize(dst) > 0:
                    os.remove(src)
                    deleted += 1
            else:
                failed += 1
                if os.path.exists(dst):
                    os.remove(dst)

    print("-" * 70)
    if apply:
        vstr = f"  verified: {verified}" if verify_on else ""
        print(f"converted: {converted}   failed: {failed}   "
              f"deleted: {deleted}   skipped: {skipped}{vstr}"
              f"   remaining FLAC: {len(find_flacs(root))}")
    else:
        print(f"planned: {planned}   skipped: {skipped}"
              f"   (DRY RUN — re-run with --apply to execute)")


if __name__ == "__main__":
    main()
