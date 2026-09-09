#!/usr/bin/env python3
"""
flac-to-alac.py

Convert every FLAC under a directory to ALAC (.m4a) using ffmpeg.
Metadata and embedded album art are preserved (-map 0, -c:v copy).

Requires ffmpeg: brew install ffmpeg

SAFETY
    The source FLAC is deleted only after the conversion has been verified
    lossless (decoded PCM of source and destination hash identically). If
    verification fails, or is disabled with --no-verify, the FLAC is kept.
    Output is written to a temporary file and atomically renamed into place,
    so an interrupted run never leaves a truncated .m4a behind.

USAGE
    python3 flac-to-alac.py --root /path/to/music              # dry run
    python3 flac-to-alac.py --root /path/to/music --apply      # convert + delete FLAC
    python3 flac-to-alac.py --root /path/to/music --apply --keep-original  # convert only

OPTIONS
    --root PATH         Directory to scan (default: current directory).
    --apply             Execute the conversions (default is dry run).
    --keep-original     Do not delete the FLAC after a verified conversion.
    --no-verify         Skip the lossless verification step. Implies the FLAC is
                        kept unless --force-delete is also given.
    --force-delete      Delete the FLAC even when verification is skipped.
    --jobs N            Convert N files in parallel (default: 4, capped at CPU count).
"""

import argparse
import concurrent.futures
import hashlib
import os
import signal
import subprocess
import sys
import tempfile

try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, OSError):
    pass

TMP_PREFIX = ".flac-to-alac-"
READ_CHUNK = 1 << 20


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
        print(f"Error: ffmpeg not found. Install with: {hint}", file=sys.stderr)
        sys.exit(1)


def find_flacs(root):
    flacs = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if fn.startswith("._"):      # macOS AppleDouble sidecar
                continue
            if fn.lower().endswith(".flac"):
                flacs.append(os.path.join(dirpath, fn))
    return sorted(flacs)


def sweep_stale_temps(root):
    """Remove leftover temp files from a previously interrupted run."""
    removed = 0
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if fn.startswith(TMP_PREFIX):
                try:
                    os.remove(os.path.join(dirpath, fn))
                    removed += 1
                except OSError:
                    pass
    return removed


def _run_ffmpeg(src, dst, keep_art):
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", src, "-c:a", "alac"]
    if keep_art:
        cmd += ["-c:v", "copy", "-map", "0"]
    else:
        cmd += ["-map", "0:a", "-vn"]
    cmd.append(dst)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, (result.stderr or "").strip()


def convert(src, dst):
    """Convert src -> dst atomically. Returns (ok, note, error_text)."""
    directory = os.path.dirname(dst) or "."
    fd, tmp = tempfile.mkstemp(prefix=TMP_PREFIX, suffix=".m4a", dir=directory)
    os.close(fd)
    try:
        ok, err = _run_ffmpeg(src, tmp, keep_art=True)
        note = ""
        if not ok:
            # A cover image the MP4 container will not accept should not block
            # the audio conversion; retry without the artwork stream.
            ok, err2 = _run_ffmpeg(src, tmp, keep_art=False)
            if ok:
                note = "artwork dropped (cover stream not MP4-compatible)"
            else:
                err = err2 or err
        if not ok:
            return False, "", err
        os.replace(tmp, dst)
        tmp = None
        return True, note, ""
    finally:
        if tmp is not None:
            try:
                os.remove(tmp)
            except OSError:
                pass


def pcm_digest(path):
    """Stream-decode to raw PCM and return a digest. Constant memory."""
    proc = subprocess.Popen(
        ["ffmpeg", "-nostdin", "-loglevel", "error",
         "-i", path, "-map", "0:a:0", "-vn",
         "-f", "s32le", "-acodec", "pcm_s32le", "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.stdout, proc.stderr
    assert stdout is not None and stderr is not None
    digest = hashlib.blake2b(digest_size=16)
    try:
        for chunk in iter(lambda: stdout.read(READ_CHUNK), b""):
            digest.update(chunk)
    finally:
        stdout.close()
        stderr.read()
        stderr.close()
        code = proc.wait()
    return digest.digest() if code == 0 else None


def verify(src, dst):
    src_digest = pcm_digest(src)
    if src_digest is None:
        return False
    dst_digest = pcm_digest(dst)
    if dst_digest is None:
        return False
    return src_digest == dst_digest


def process(src, verify_on, remove):
    """Convert one file. Returns a result dict (runs on a worker thread)."""
    dst = src[:-5] + ".m4a"
    out = {"src": src, "dst": dst, "converted": False, "verified": None,
           "deleted": False, "note": "", "error": ""}

    ok, note, err = convert(src, dst)
    out["note"] = note
    if not ok:
        out["error"] = err or "ffmpeg failed"
        return out
    out["converted"] = True

    if verify_on:
        out["verified"] = verify(src, dst)
        if not out["verified"]:
            return out

    if remove:
        try:
            if os.path.getsize(dst) > 0:
                os.remove(src)
                out["deleted"] = True
            else:
                out["error"] = "destination is 0 bytes; source kept"
        except OSError as exc:
            out["error"] = f"could not delete source: {exc}"
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Convert FLAC files to ALAC using ffmpeg.",
    )
    ap.add_argument("--root", default=".", help="Directory to scan (default: .)")
    ap.add_argument("--apply", action="store_true",
                    help="Execute the conversions (default is dry run)")
    ap.add_argument("--keep-original", action="store_true",
                    help="Do not delete the FLAC after a verified conversion")
    ap.add_argument("--no-verify", action="store_true",
                    help="Skip lossless verification (implies --keep-original "
                         "unless --force-delete is given)")
    ap.add_argument("--force-delete", action="store_true",
                    help="Delete the FLAC even when verification is skipped")
    ap.add_argument("--jobs", type=int, default=4,
                    help="Convert N files in parallel (default: 4)")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    apply = args.apply
    verify_on = not args.no_verify
    remove = apply and not args.keep_original
    if remove and not verify_on and not args.force_delete:
        remove = False

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    check_ffmpeg()

    jobs = max(1, min(args.jobs, os.cpu_count() or 1))

    if remove:
        remove_label = "on (verified)" if verify_on else "on (UNVERIFIED)"
    elif args.keep_original:
        remove_label = "off (--keep-original)"
    elif not verify_on and apply:
        remove_label = "off (verification disabled; pass --force-delete to override)"
    else:
        remove_label = "off"

    print(f"root={root}  mode={'APPLY' if apply else 'DRY RUN'}  "
          f"verify={'on' if verify_on else 'off'}  "
          f"remove={remove_label}  jobs={jobs}")
    print("-" * 70)

    if apply:
        stale = sweep_stale_temps(root)
        if stale:
            print(f"  cleaned {stale} stale temp file(s) from a previous run")

    flacs = find_flacs(root)
    todo = []
    skipped = 0
    for src in flacs:
        dst = src[:-5] + ".m4a"
        if os.path.exists(dst):
            print(f"  (exists) {os.path.relpath(dst, root)}")
            skipped += 1
            continue
        todo.append(src)

    if not todo:
        print("-" * 70)
        print(f"nothing to convert   skipped: {skipped}")
        return

    if not apply:
        for src in todo:
            dst = src[:-5] + ".m4a"
            print(f"{os.path.relpath(src, root)} -> {os.path.relpath(dst, root)}")
        print("-" * 70)
        print(f"planned: {len(todo)}   skipped: {skipped}   "
              f"(DRY RUN — re-run with --apply to execute)")
        return

    converted = deleted = failed = verified = unverified = 0
    total = len(todo)
    interrupted = False

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(process, src, verify_on, remove): src for src in todo}
        try:
            for index, future in enumerate(
                concurrent.futures.as_completed(futures), start=1
            ):
                res = future.result()
                rel = os.path.relpath(res["src"], root)
                if not res["converted"]:
                    failed += 1
                    print(f"[{index}/{total}] FAIL {rel}", file=sys.stderr)
                    for line in (res["error"] or "").splitlines():
                        print(f"    {line}", file=sys.stderr)
                    continue

                converted += 1
                flags = []
                if res["verified"] is True:
                    verified += 1
                    flags.append("verified")
                elif res["verified"] is False:
                    unverified += 1
                    flags.append("VERIFY FAILED — source kept")
                if res["deleted"]:
                    deleted += 1
                    flags.append("source removed")
                if res["note"]:
                    flags.append(res["note"])
                if res["error"]:
                    flags.append(res["error"])
                suffix = f"  [{'; '.join(flags)}]" if flags else ""
                print(f"[{index}/{total}] {rel}{suffix}")
        except KeyboardInterrupt:
            interrupted = True
            print("\nInterrupted — cancelling queued work...", file=sys.stderr)
            for future in futures:
                future.cancel()

    print("-" * 70)
    print(f"converted: {converted}   failed: {failed}   deleted: {deleted}   "
          f"skipped: {skipped}"
          + (f"   verified: {verified}" if verify_on else "")
          + (f"   VERIFY FAILED: {unverified}" if unverified else ""))
    if unverified:
        print("Some conversions did not verify as lossless. Their FLAC sources were "
              "kept; inspect the .m4a files listed above.", file=sys.stderr)
    if interrupted:
        sys.exit(130)
    if failed or unverified:
        sys.exit(1)


if __name__ == "__main__":
    main()
