#!/usr/bin/env python3
"""
Problem this solves: convert a video (mp4) to a real .smk and inject it
into a HoMM3 archive, replacing an existing clip. Companion to
008_mp4_to_bik_inject.py - use THIS script instead of that one whenever the
target is one of the 7 original RoE campaigns' mission videos.

Why this script exists instead of just using 008_mp4_to_bik_inject.py:
- For the 7 original RoE campaigns (Good1/2/3, Evil1/2, Neutral1, Secret1),
  the game reads the mission's .SMK file for the picture, NOT the .BIK,
  even though both exist side by side in VIDEO.VID for every clip (e.g.
  GOOD1A.SMK + GOOD1A.BIK). Replacing only .BIK does nothing visible in
  game - confirmed by testing. Replace .SMK instead.
- Encoding to Bink works fine by just handing ffmpeg's mp4 output straight
  to the encoder. Encoding to Smacker (SMK) does NOT: feeding a truecolor
  mp4/AVI straight to `radvideo64.exe Smack` produces severely corrupted,
  speckled output NO MATTER which palette switch you use (/Z0 truecolor,
  /Z1 default, /Z2 new palette, /Z2+/T1 forced halftone, /&file external
  palette - all five tried, all five produce visually identical garbage,
  confirmed via ffprobe AND RAD's own current SmackPlay preview, so it's
  not a game/DDrawCompat rendering bug - it's a genuine bug in this
  encoder build's internal truecolor-to-palette pipeline). The only fix
  found: quantize every frame ourselves in Python/PIL to a FIXED palette
  (extracted from the original target file) with Floyd-Steinberg dithering
  BEFORE handing frames to the encoder, as a sequence of 8-bit BMP files
  via a .lst file. That's what this script does.
- The game's own bundled SMACKW32.DLL (root of the game install, NOT
  Data/) is an old version (e.g. 3.2h) that CANNOT play the newer SMK4
  format this encoder always produces (originals are SMK2 - check the
  first 4 bytes: original files start "SMK2", anything freshly encoded
  starts "SMK4"). Symptom: not a crash, just a silent black screen / the
  clip getting skipped. Fix: replace SMACKW32.DLL in the game's root
  folder with a newer decoder from another legitimately-owned classic
  game that ships one (Smacker's exported API has been stable for
  decades, so this is a drop-in swap) - e.g. StarCraft's Smackw32.dll
  (version 4.1a) worked. No standalone official redistributable-only
  download exists for this DLL. ALWAYS back up the original DLL first.
- The RAD Video Tools Smack-via-image-sequence encoder itself is flaky
  under load, independent of all of the above: reliably works at 800x600
  @ 10fps (which also happens to be the original game's exact native rate
  for these clips - not a coincidence to aim for), but hangs (CPU usage
  flatlines, progress freezes forever) or crashes near 99% at higher
  fps/resolution (tried 800x600 @ 20/25/30/60fps, 1024x768 @ 15fps,
  1280x720 @ 30/60fps - all unreliable; only 1280x720 @ 15fps encoded
  successfully but the GAME then wouldn't load/play the result, likely an
  unrelated hardcoded buffer-size assumption in Heroes3.exe itself).
  DON'T chase higher settings without a new idea - it's a real, repeatedly
  confirmed dead end, not bad luck. This script defaults to 800x600/10fps
  and does not expose a way to bypass that recommendation lightly.
- Audio is NOT embedded in the SMK for these campaigns (original SMK audio
  tracks are junk/noise - see AUDIO_VIDEO_NOTES.md). The real narration is
  a separate WAV in Heroes3.snd under a short code (e.g. "G1A" for
  Good1a) - inject a replacement there instead, trimmed to the SAME
  duration as your new video (a duration mismatch here was a real bug hit
  once: don't extract audio from a multi-mission concatenated file without
  trimming it to just the one mission's slice first).

Usage:
    python 009_mp4_to_smk_inject.py input.mp4 GOOD1A.SMK --archive VIDEO.VID
    python 009_mp4_to_smk_inject.py input.mp4 GOOD1A.SMK --width 800 --height 600 --fps 10

By default this only writes to a SCRATCH COPY of the archive (never
touches the real game install) - pass --game to copy from a specific
install, and manually swap the resulting archive into Data/ yourself once
verified in-game.

Requires: the RAD Video Tools "Smack" encoder installed (see
008_mp4_to_bik_inject.py's docstring for exact install steps - same tool,
different subcommand), mmarch (npm i -g mmarch), ffmpeg/ffprobe on PATH,
Pillow (pip install pillow).
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image

# The 2014-era standalone smack.exe (RAD's own internal version "1.994i")
# is FAR more reliable for this image-sequence encoding path than either
# the 2026.06 or 2021-08-26 unified "radvideo64.exe Smack" builds, which
# hang or crash unpredictably above 800x600/10fps. This one never hung
# across every setting tried (up to 1280x720 @ 60fps). Prefer it. Mirror:
# https://www.videohelp.com/software/Rad-Video-Tools/old-versions (plain
# .exe NSIS installer, no password, `/S /D=<dir>` silent install).
DEFAULT_SMACK_EXE = r"C:\Program Files (x86)\RADVideo1994\smack.exe"
# Fallback: the unified tool's Smack subcommand (works, but flaky above
# 800x600/10fps - see AUDIO_VIDEO_NOTES.md).
DEFAULT_RAD_EXE = r"C:\Users\UserM\AppData\Local\RADVideoNew\radvideo64.exe"


def find_smack_tool(explicit):
    """In: explicit (a user-supplied --rad-exe path, or None). Out:
    (exe_path, args_prefix) - args_prefix is [] for the standalone 2014
    smack.exe (preferred, see module docstring for why), ["Smack"] for the
    unified radvideo64.exe (fallback, prints a reliability warning). Exits
    with install instructions if neither is found."""
    candidates_standalone = [explicit] if explicit else []
    candidates_standalone += [
        DEFAULT_SMACK_EXE,
        r"C:\Program Files\RADVideo1994\smack.exe",
    ]
    for c in candidates_standalone:
        if c and os.path.isfile(c):
            return c, []

    candidates_unified = [
        DEFAULT_RAD_EXE,
        r"C:\Program Files\RADVideoNew\radvideo64.exe",
        r"C:\Program Files (x86)\RADVideoNew\radvideo64.exe",
    ]
    for c in candidates_unified:
        if c and os.path.isfile(c):
            print("WARNING: using the unified radvideo64.exe Smack command - "
                  "known unreliable above 800x600/10fps. Prefer the 2014 "
                  "standalone smack.exe instead (see this script's header).",
                  file=sys.stderr)
            return c, ["Smack"]

    sys.exit(
        "No Smack encoder found. Preferred: the 2014 standalone smack.exe "
        "from https://www.videohelp.com/software/Rad-Video-Tools/old-versions "
        "Fallback: current RAD Video Tools from "
        "https://www.radgametools.com/down/Bink/RADTools.7z (password: RAD) "
        "via `radtools.exe /S /D=<install_dir>`. Pass --rad-exe to point at "
        "either one explicitly."
    )


def tool(name):
    p = shutil.which(name)
    if not p:
        sys.exit(f"{name} not found on PATH")
    return p


def extract_palette(ffmpeg, ffprobe, orig_smk_path, tmp):
    """Grabs the target SMK's own 8-bit palette so new frames can be
    quantized to match it exactly (see module docstring - feeding
    truecolor straight to the encoder produces corrupted output). In:
    ffmpeg, ffprobe (tool paths - ffprobe currently unused but kept in the
    signature), orig_smk_path (the .smk being replaced), tmp (scratch
    dir). Out: a PIL "P"-mode Image carrying that palette, ready to pass
    as `palette=` to Image.quantize()."""
    ref_png = os.path.join(tmp, "palette_ref.png")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", orig_smk_path,
                     "-vframes", "1", "-pix_fmt", "pal8", ref_png], check=True)
    im = Image.open(ref_png)
    if im.mode != "P":
        sys.exit("failed to extract an 8-bit palette from the original SMK")
    pal_template = Image.new("P", (16, 16))
    pal_template.putpalette(im.getpalette())
    return pal_template


def render_and_quantize(ffmpeg, src, tmp, width, height, fps, duration, pal_template):
    """Renders src to a PNG-per-frame sequence at the target size/rate,
    then quantizes each frame to pal_template with Floyd-Steinberg
    dithering and saves it as an 8-bit BMP (the input format the Smack
    encoder needs). In: ffmpeg, src (input video), tmp (scratch dir),
    width, height, fps, duration (optional - loop/trim src to this many
    seconds first, e.g. to match a voiceover clip's length), pal_template
    (from extract_palette). Out: (lst_path, n_frames) - lst_path is a
    newline-separated list of BMP paths in order, the exact input format
    the Smack encoder's `<Input Graphics File>` argument expects; n_frames
    is how many were produced (for a progress-sanity print)."""
    frames_dir = os.path.join(tmp, "frames_png")
    bmp_dir = os.path.join(tmp, "frames_bmp")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(bmp_dir, exist_ok=True)

    args = [ffmpeg, "-y", "-loglevel", "error"]
    if duration:
        args += ["-stream_loop", "-1", "-i", src, "-t", str(duration)]
    else:
        args += ["-i", src]
    args += ["-vf", f"scale={width}:{height},fps={fps}",
             os.path.join(frames_dir, "f%04d.png")]
    subprocess.run(args, check=True)

    png_files = sorted(glob.glob(os.path.join(frames_dir, "*.png")))
    if not png_files:
        sys.exit("no frames rendered - check the input video/duration")

    lst_path = os.path.join(tmp, "frames.lst")
    with open(lst_path, "w") as f:
        for png in png_files:
            im = Image.open(png).convert("RGB")
            q = im.quantize(palette=pal_template, dither=Image.FLOYDSTEINBERG)
            bmp_path = os.path.join(bmp_dir, os.path.basename(png).replace(".png", ".bmp"))
            q.save(bmp_path)
            f.write(bmp_path + "\n")

    return lst_path, len(png_files)


def encode_smk(exe, args_prefix, lst_path, dst, fps, timeout):
    """In: exe, args_prefix (both from find_smack_tool), lst_path (from
    render_and_quantize), dst (output .smk path), fps, timeout (seconds of
    no file-size growth before giving up - a real safety net, see the
    comment below for why). Out: None (writes dst; exits with an error if
    nothing was produced)."""
    # Same GUI-never-exits problem as the Bink encoder - poll for the
    # output file to stop growing, then kill the process. The unified
    # radvideo64.exe Smack path is also known to hang outright (zero CPU,
    # no progress) above 800x600/10fps - the timeout here is a real safety
    # net for that case. The standalone 2014 smack.exe (args_prefix=[])
    # has not been observed to hang, but the timeout is kept as a general
    # safeguard either way.
    args = [exe, *args_prefix, lst_path, dst, f"/F{fps}"]
    if args_prefix:
        args.append("/Z1")  # only meaningful/needed for the unified tool
    proc = subprocess.Popen(args)
    try:
        deadline = time.time() + timeout
        last_size = -1
        stable_checks = 0
        while time.time() < deadline:
            time.sleep(2)
            if os.path.isfile(dst):
                size = os.path.getsize(dst)
                if size > 0 and size == last_size:
                    stable_checks += 1
                    if stable_checks >= 3:
                        break
                else:
                    stable_checks = 0
                last_size = size
        else:
            sys.exit(
                f"encode timed out after {timeout}s with no progress - this "
                "is a known reliability issue with this encoder above "
                "800x600/10fps, not necessarily a problem with your input. "
                "See 009_mp4_to_smk_inject.py's docstring / AUDIO_VIDEO_NOTES.md."
            )
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
    ap.add_argument("input", help="Source video (mp4)")
    ap.add_argument("smk_name", help="Archive entry name to replace, e.g. GOOD1A.SMK")
    ap.add_argument("--archive", default="VIDEO.VID", help="Archive file name (default: VIDEO.VID)")
    ap.add_argument("--game", default="F:/Games/HoMM 3 Complete", help="Game install to copy the archive from")
    ap.add_argument("--out-dir", default=None, help="Where to write the modified archive copy (default: script dir)")
    ap.add_argument("--width", type=int, default=800,
                     help="Default 800 - the game engine itself hard-crashes above this on any "
                          "encoder/DLL tried (confirmed not an encoding issue - see AUDIO_VIDEO_NOTES.md)")
    ap.add_argument("--height", type=int, default=600, help="Default 600 - see --width")
    ap.add_argument("--fps", type=int, default=10,
                     help="Default 10 (matches the original game's own rate) - higher fps is fine "
                          "with the 2014 smack.exe, only resolution is a real ceiling")
    ap.add_argument("--duration", type=float, default=None,
                     help="Loop/trim input to this many seconds (e.g. to match a voiceover clip's length)")
    ap.add_argument("--encode-timeout", type=int, default=180,
                     help="Give up if the encoder makes no progress for this many seconds (default 180)")
    ap.add_argument("--rad-exe", default=None, help="Path to radvideo64.exe if not auto-detected")
    args = ap.parse_args()

    if (args.width, args.height) != (800, 600):
        print("WARNING: the game engine itself (Heroes3.exe) crashes trying "
              "to load/play SMK video above 800x600 - confirmed with known-"
              "good, uncorrupted files, so this is not fixable by encoding "
              "settings. See AUDIO_VIDEO_NOTES.md before relying on a "
              "higher resolution for anything real.", file=sys.stderr)

    smack_exe, smack_args_prefix = find_smack_tool(args.rad_exe)
    mmarch = tool("mmarch")
    ffmpeg = tool("ffmpeg")
    ffprobe = tool("ffprobe")

    out_dir = os.path.abspath(args.out_dir) if args.out_dir else os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    src_archive = os.path.join(args.game, "Data", args.archive)
    if not os.path.isfile(src_archive):
        sys.exit(f"archive not found: {src_archive}")

    with tempfile.TemporaryDirectory() as tmp:
        orig_smk = os.path.join(tmp, args.smk_name)
        subprocess.run([mmarch, "extract", src_archive, tmp, args.smk_name], check=True)
        if not os.path.isfile(orig_smk):
            sys.exit(f"could not extract original {args.smk_name} from {src_archive} to derive its palette")

        print("Extracting original palette...")
        pal_template = extract_palette(ffmpeg, ffprobe, orig_smk, tmp)

        print(f"Rendering + quantizing frames ({args.width}x{args.height} @ {args.fps}fps)...")
        lst_path, n_frames = render_and_quantize(
            ffmpeg, os.path.abspath(args.input), tmp,
            args.width, args.height, args.fps, args.duration, pal_template)
        print(f"  {n_frames} frames ready")

        smk_path = os.path.join(tmp, args.smk_name)
        print(f"Encoding to {args.smk_name} (this can hang - see docstring; "
              f"timeout {args.encode_timeout}s)...")
        encode_smk(smack_exe, smack_args_prefix, lst_path, smk_path, args.fps, args.encode_timeout)
        print(f"  encoded ok, {os.path.getsize(smk_path)} bytes")

        out_archive = os.path.join(out_dir, args.archive)
        shutil.copy2(src_archive, out_archive)

        print(f"Injecting into scratch copy: {out_archive}")
        subprocess.run([mmarch, "add", out_archive, smk_path], check=True, cwd=tmp)

    print(f"\nDone: {out_archive}")
    print("This is a SCRATCH COPY, not the live game archive. Remember:")
    print("  - the game needs a newer SMACKW32.DLL in its root folder to")
    print("    play this (SMK4) - the stock one silently can't (black screen)")
    print("  - audio isn't embedded - replace the matching Heroes3.snd entry")
    print("    separately, trimmed to the SAME duration as this video")


if __name__ == "__main__":
    main()
