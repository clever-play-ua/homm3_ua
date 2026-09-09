#!/usr/bin/env python3
"""
Problem this solves: convert a video (mp4/avi/etc) to a real .bik and inject
it into a HoMM3 archive (VIDEO.VID / H3ab_ahd.vid), replacing an existing clip.

Important lessons learned finding a working encoder (don't redo this):
- The OLD "RAD Video Tools" build (2001-era, e.g. mirrored on factionfiles.com)
  ships binkconv.exe, which crashes with STATUS_ACCESS_VIOLATION on modern
  Windows on every input tried (mpeg4 AVI, uncompressed AVI; with/without
  compatibility-mode shims; as admin). Crash is inside radutil.dll. Do not
  waste time on this build again - it does not work on Windows 11.
- The CURRENT official build is downloaded from the RAD Game Tools site
  itself: https://www.radgametools.com/down/Bink/RADTools.7z (7z, password
  "RAD"). It's an NSIS installer (radtools.exe) - silent-install it with:
      radtools.exe /S /D=<install_dir>
  This installs radvideo64.exe (+ radvideo32.exe, binkplay.exe, etc) - NOT
  binkconv.exe. This new build does NOT crash.
- radvideo64.exe is a multi-tool dispatched by a subcommand as argv[1].
  THE TRAP: there are TWO similarly-named subcommands and only one encodes:
    - "BinkConv" (RADVideo64.exe BinkConv <in> <out> [/switches]) is a
      DECODER - it converts Bink/Smacker/etc INTO avi/images/wav. Pointing
      it at a .bik OUTPUT fails immediately with a GUI dialog saying
      "Unsupported output file type or color depth." (silent - no console
      output, no exception, just a dialog + the window closing).
    - "Bink" (RADVideo64.exe Bink <input graphics/video file> <out.bik>
      [/switches]) is the actual ENCODER. This is the one to use.
  Full switch reference: run `radvideo64.exe Bink /?` (opens a dialog with
  the text, doesn't print to console - or grep the printable strings out of
  the exe for "Video switches:"/"Audio switches:").
- Useful switches for our use case: /(W - scale to width, /)H - scale to
  height, /F#.# - force output frame rate, /O - auto-overwrite output file.
- KNOWN OPEN RISK (not yet confirmed either way - needs an actual in-game
  test): this encoder writes the newest Bink 1 bitstream revision, tagged
  "BIKi" in the file's magic bytes (see `ffprobe`/hexdump of byte 0-3). The
  original game files are tagged "BIKb" - a much older revision, matching
  the ~2001 binkw32.dll HoMM3 ships with. Bink decoders are NOT guaranteed
  backward compatible with newer-revision bitstreams than they were built
  for. There's no encoder switch to force an older output revision. Nobody
  has confirmed yet whether the game's bundled binkw32.dll can actually
  play a "BIKi" file - if the video doesn't play / crashes / shows garbage
  in-game, that revision mismatch is almost certainly why, and the fix
  would be dropping in a newer binkw32.dll redistributable alongside the
  game (RAD allows redistributing the *decoder* DLL, unlike the encoder -
  but no direct download for a standalone one was found on radgametools.com;
  it'd need to come from the licensed SDK or another game that already
  ships a newer one).
- mmarch's `add` command replaces an existing same-named archive entry in
  place (confirmed: re-extracting after `add` byte-matched the new file
  exactly) - no separate "replace"/"delete then add" dance needed.

Usage:
    python 008_mp4_to_bik_inject.py input.mp4 GOOD1A.BIK --archive VIDEO.VID
    python 008_mp4_to_bik_inject.py input.mp4 GOOD1A.BIK --width 800 --height 600 --fps 15

By default this only writes to a SCRATCH COPY of the archive (never touches
the real game install) - pass --game to copy from a specific install, and
manually swap the resulting archive into Data/ yourself once you've verified
it plays correctly in-game.

Requires: the RAD Video Tools "Bink" encoder installed (see notes above),
mmarch (npm i -g mmarch).
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

DEFAULT_RAD_EXE = r"C:\Users\UserM\AppData\Local\RADVideoNew\radvideo64.exe"


def find_rad_exe(explicit):
    """In: explicit (a user-supplied --rad-exe path, or None). Out: str -
    the first existing path among explicit, the default install location,
    and two common alternates; exits with an install-instructions message
    if none exist."""
    candidates = [explicit] if explicit else []
    candidates += [
        DEFAULT_RAD_EXE,
        r"C:\Program Files\RADVideoNew\radvideo64.exe",
        r"C:\Program Files (x86)\RADVideoNew\radvideo64.exe",
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    sys.exit(
        "radvideo64.exe not found. Install it from "
        "https://www.radgametools.com/down/Bink/RADTools.7z (password: RAD) "
        "via `radtools.exe /S /D=<install_dir>`, then pass --rad-exe."
    )


def tool(name):
    p = shutil.which(name)
    if not p:
        sys.exit(f"{name} not found on PATH")
    return p


def encode_bik(rad_exe, src, dst, width=None, height=None, fps=None, timeout=120):
    """In: rad_exe (path from find_rad_exe), src (input video/image
    sequence), dst (output .bik path), width/height/fps (optional encoder
    scale/rate overrides, passed through as /( /) /F switches), timeout
    (seconds of no file-size growth before giving up). Out: None (writes
    dst; exits with an error if nothing was produced). Known open risk:
    always writes the `BIKi` bitstream revision - see this module's
    docstring and 002_TOOLS/scripts/README.md's entry for this script."""
    # radvideo64.exe's "Bink" encoder is a GUI tool that does NOT exit on its
    # own when done - it leaves a "Bink Video Compressor - Done!" window open
    # forever. So we can't subprocess.run(check=True) and wait for exit; we
    # poll for the output file to appear and its size to stop growing, then
    # kill the process ourselves.
    args = [rad_exe, "Bink", src, dst, "/O"]
    if width:
        args.append(f"/({width}")
    if height:
        args.append(f"/){height}")
    if fps:
        args.append(f"/F{fps}")

    proc = subprocess.Popen(args)
    try:
        deadline = time.time() + timeout
        last_size = -1
        stable_checks = 0
        while time.time() < deadline:
            time.sleep(1)
            if os.path.isfile(dst):
                size = os.path.getsize(dst)
                if size > 0 and size == last_size:
                    stable_checks += 1
                    if stable_checks >= 2:
                        break
                else:
                    stable_checks = 0
                last_size = size
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    if not os.path.isfile(dst) or os.path.getsize(dst) == 0:
        sys.exit(f"encode failed - no output produced at {dst}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Source video (mp4, avi, etc)")
    ap.add_argument("bik_name", help="Archive entry name to replace, e.g. GOOD1A.BIK")
    ap.add_argument("--archive", default="VIDEO.VID", help="Archive file name (default: VIDEO.VID)")
    ap.add_argument("--game", default="F:/Games/HoMM 3 Complete", help="Game install to copy the archive from")
    ap.add_argument("--out-dir", default=None, help="Where to write the modified archive copy (default: script dir)")
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--fps", type=float, default=None)
    ap.add_argument("--rad-exe", default=None, help="Path to radvideo64.exe if not auto-detected")
    args = ap.parse_args()

    rad_exe = find_rad_exe(args.rad_exe)
    mmarch = tool("mmarch")

    out_dir = os.path.abspath(args.out_dir) if args.out_dir else os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    src_archive = os.path.join(args.game, "Data", args.archive)
    if not os.path.isfile(src_archive):
        sys.exit(f"archive not found: {src_archive}")

    with tempfile.TemporaryDirectory() as tmp:
        bik_path = os.path.join(tmp, args.bik_name)
        print(f"Encoding {args.input} -> {args.bik_name} ...")
        encode_bik(rad_exe, os.path.abspath(args.input), bik_path,
                   args.width, args.height, args.fps)
        print(f"  encoded ok, {os.path.getsize(bik_path)} bytes")

        out_archive = os.path.join(out_dir, args.archive)
        shutil.copy2(src_archive, out_archive)

        print(f"Injecting into scratch copy: {out_archive}")
        subprocess.run([mmarch, "add", out_archive, bik_path], check=True, cwd=tmp)

    print(f"\nDone: {out_archive}")
    print("This is a SCRATCH COPY, not the live game archive. To test in-game:")
    print(f'  1. Back up the real Data\\{args.archive}')
    print(f'  2. Copy {out_archive} over it')
    print("  3. Launch the game and check the replaced clip plays correctly")
    print("     (if it doesn't play / looks broken, see the BIKi vs BIKb revision")
    print("     note in this script's docstring - that's the most likely cause).")


if __name__ == "__main__":
    main()
