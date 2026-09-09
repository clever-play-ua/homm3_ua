#!/usr/bin/env python3
"""
Problem this solves: build a narrated, subtitled showcase video for one
campaign's missions - real voiceover audio + burned-in subtitles (EN or UA)
- from the game's own assets.

Important lesson learned building this (don't redo the investigation):
- The per-mission video files (e.g. GOOD1A.BIK/.SMK in VIDEO.VID) do NOT
  carry the real narration audio for the original 7 RoE campaigns. The
  .BIK copies have no audio stream at all. The .SMK copies DO have an audio
  stream, but it decodes to pure noise (verified two ways: ffmpeg's own
  smackaudio decoder, and a from-scratch Python port of libsmacker's DPCM
  algorithm - both agree byte-for-byte, so this isn't a decoder bug, the
  track itself is junk/unused in these files).
- The REAL English narration lives in Heroes3.snd, under short 2-4 char
  codes with NO relation to campaign/scenario naming you'd guess by
  grepping for "good"/"vo"/etc - e.g. Good1's three missions are
  "G1A"/"G1B"/"G1C" (Good2 -> G2A..D, Good3 -> G3A..C, Evil1 -> E1A..C,
  Evil2 -> E2A..D(+AE), Neutral1 -> N1A..C, Secret1 -> S1A..C). Find them
  with `mmarch list Heroes3.snd`, sorted by size (real narration clips are
  tens to hundreds of KB; combat sound effects are a few KB) - don't trust
  name-based guessing.
- AB-era campaigns (ab/blood/slayer/festival/fool/fire) use a different,
  documented naming instead: "ABVO<CAMPAIGNCODE><N>" (e.g. ABVOAB1..9).
  Those extract cleanly as-is.
- CAMPDIAG.TXT's text for a given mission key (e.g. "Good1a") is exactly
  what's spoken in the matching narration clip - that's what this script
  times subtitles against.

Usage:
    python 011_burn_campaign_subtitles.py GOOD1 --lang en
    python 011_burn_campaign_subtitles.py GOOD1 --lang ua

Requires: mmarch (npm i -g mmarch), ffmpeg/ffprobe on PATH.
Output: 005_RAW/<NNN>_<Campaign>/videos/<Stem>_narrated_<LANG>.mp4
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
RAW_DIR = os.path.join(REPO_ROOT, "005_RAW")

# stem -> (campaign folder, [(campdiag_key, bik_filename, snd_voice_code), ...])
# Only RoE campaigns have this per-mission voice-clip pattern; AB/SoD
# campaigns use a single ABVOxxx-style clip per campaign instead (not yet
# wired up here - extend CAMPAIGNS below following the same shape if needed).
CAMPAIGNS = {
    "GOOD1": ("001_Long_Live_the_Queen", [
        ("Good1a", "GOOD1A.BIK", "G1A"),
        ("Good1b", "GOOD1B.BIK", "G1B"),
        ("Good1c", "GOOD1C.BIK", "G1C"),
    ]),
    "GOOD2": ("002_Liberation", [
        ("Good2a", "GOOD2A.BIK", "G2A"),
        ("Good2b", "GOOD2B.BIK", "G2B"),
        ("Good2c", "GOOD2C.BIK", "G2C"),
        ("Good2d", "GOOD2D.BIK", "G2D"),
    ]),
    "GOOD3": ("003_Song_for_the_Father", [
        ("Good3a", "GOOD3A.BIK", "G3A"),
        ("Good3b", "GOOD3B.BIK", "G3B"),
        ("Good3c", "GOOD3C.BIK", "G3C"),
    ]),
    "EVIL1": ("004_Dungeons_and_Devils", [
        ("Evil1a", "EVIL1A.BIK", "E1A"),
        ("Evil1b", "EVIL1B.BIK", "E1B"),
        ("Evil1c", "EVIL1C.BIK", "E1C"),
    ]),
    "EVIL2": ("005_Long_Live_the_King", [
        ("Evil2a", "EVIL2A.BIK", "E2A"),
        ("Evil2b", "EVIL2B.BIK", "E2B"),
        ("Evil2c", "EVIL2C.BIK", "E2C"),
        ("Evil2d", "EVIL2D.BIK", "E2D"),
    ]),
    "NEUTRAL1": ("006_Spoils_of_War", [
        ("Neutral1a", "NEUTRALA.BIK", "N1A"),
        ("Neutral1b", "NEUTRALB.BIK", "N1B"),
        ("Neutral1c/d", "NEUTRALC.BIK", "N1C_D"),
    ]),
    "SECRET1": ("007_Seeds_of_Discontent", [
        ("Secret1a", "SECRETA.BIK", "S1A"),
        ("Secret1b", "SECRETB.BIK", "S1B"),
        ("Secret1c", "SECRETC.BIK", "S1C"),
    ]),
}


def tool(name):
    p = shutil.which(name)
    if not p:
        sys.exit(f"{name} not found on PATH")
    return p


def get_text(campdiag, key, lang):
    """In: campdiag (CAMPTEXT.TXT/CAMPDIAG.TXT rows, already loaded as
    `{var, en, ua}` dicts - see 002_build_raw.py's output shape), key (a
    mission code, e.g. 'Good1a'), lang ('en' or 'ua'). Out: the matching
    row's text for that language, with the tab-prefixed key and
    surrounding quotes stripped and doubled quotes un-escaped. Raises
    KeyError if no row's `var` ends with '_'+key."""
    for r in campdiag:
        if r["var"].endswith("_" + key):
            line = r[lang]
            line = line.split("\t", 1)[1] if "\t" in line else line
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            line = line.replace('""', '"')
            return line.strip()
    raise KeyError(key)


def split_sentences(text):
    """In: text (one narration passage). Out: list of sentences, split on
    whitespace following . ! or ?, blanks dropped - the subtitle-timing
    unit build_srt_proportional() allots screen time to."""
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def srt_timestamp(seconds):
    """In: seconds (float). Out: str formatted as SRT's
    'HH:MM:SS,mmm' timestamp."""
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = round((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def get_duration(ffprobe, path):
    """In: ffprobe (path), path (a media file). Out: float seconds - its
    total duration, via ffprobe's format=duration field."""
    out = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=noprint_wrappers=1:nokey=1", path],
                          capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def build_srt_proportional(sentences, total_dur, out_path, lead_in=0.3, tail_out=0.5):
    """Times each sentence's subtitle card proportionally to its character
    count (no real speech-timing data is available - this is a best-effort
    approximation, not synced to actual word-level narration timing).
    In: sentences (from split_sentences), total_dur (the narration clip's
    real duration in seconds, from get_duration), out_path (.srt to
    write), lead_in/tail_out (seconds trimmed off the start/end before
    dividing up the remainder - avoids the first/last card feeling
    clipped). Out: None (writes out_path as a standard numbered SRT file)."""
    usable = max(total_dur - lead_in - tail_out, 1.0)
    total_chars = sum(len(s) for s in sentences) or 1
    t = lead_in
    with open(out_path, "w", encoding="utf-8") as f:
        for i, sent in enumerate(sentences, start=1):
            dur = usable * (len(sent) / total_chars)
            f.write(f"{i}\n{srt_timestamp(t)} --> {srt_timestamp(t + dur)}\n{sent}\n\n")
            t += dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("campaign", choices=sorted(CAMPAIGNS), help="Campaign stem, e.g. GOOD1")
    ap.add_argument("--lang", choices=["en", "ua"], required=True)
    ap.add_argument("--game", default="F:/Games/HoMM 3 Complete")
    args = ap.parse_args()

    mmarch = tool("mmarch")
    ffmpeg = tool("ffmpeg")
    ffprobe = tool("ffprobe")
    game_data = os.path.join(args.game, "Data")

    folder, missions = CAMPAIGNS[args.campaign]
    videos_dir = os.path.join(RAW_DIR, folder, "videos")
    voiceover_dir = os.path.join(RAW_DIR, folder, "voiceover_en")
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(voiceover_dir, exist_ok=True)

    campdiag = json.load(open(os.path.join(RAW_DIR, "H3bitmap.lod", "CAMPDIAG.json"), encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        bik_dir = os.path.join(tmp, "bik")
        vo_dir = os.path.join(tmp, "vo")
        os.makedirs(bik_dir, exist_ok=True)
        os.makedirs(vo_dir, exist_ok=True)

        subprocess.run([mmarch, "extract", os.path.join(game_data, "VIDEO.VID"), bik_dir] +
                        [m[1] for m in missions], check=True)
        subprocess.run([mmarch, "extract", os.path.join(game_data, "Heroes3.snd"), vo_dir] +
                        [m[2] for m in missions], check=True)

        # keep a permanent copy of the raw EN voiceover clips - handy to hand
        # a translator/voice actor without re-running extraction
        for _, _, voice_code in missions:
            src_wav = os.path.join(vo_dir, voice_code + ".wav")
            if os.path.isfile(src_wav):
                shutil.copy2(src_wav, os.path.join(voiceover_dir, voice_code + ".wav"))

        segments = []
        for key, bik_name, voice_code in missions:
            text = get_text(campdiag, key, args.lang)
            sentences = split_sentences(text)

            vo_path = os.path.join(vo_dir, voice_code + ".wav")
            vo_dur = get_duration(ffprobe, vo_path)

            safe_key = key.replace("/", "-")
            srt_path = os.path.join(tmp, f"{safe_key}.srt")
            build_srt_proportional(sentences, vo_dur, srt_path)

            bik_path = None
            for cand in os.listdir(bik_dir):
                if cand.lower() == bik_name.lower():
                    bik_path = os.path.join(bik_dir, cand)
                    break
            if bik_path is None:
                sys.exit(f"missing extracted video {bik_name}")

            looped = os.path.join(tmp, f"{safe_key}_video.mp4")
            subprocess.run([
                ffmpeg, "-y", "-loglevel", "error",
                "-stream_loop", "-1", "-i", bik_path,
                "-i", vo_path,
                "-t", f"{vo_dur:.2f}",
                "-vf", "fps=15,scale=800:600",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
                "-shortest",
                looped
            ], check=True)

            srt_ff = srt_path.replace("\\", "/").replace(":", "\\:")
            burned = os.path.join(tmp, f"{safe_key}_burned.mp4")
            style = ("FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                     "BorderStyle=1,Outline=2,Shadow=0,MarginV=30")
            subprocess.run([
                ffmpeg, "-y", "-loglevel", "error",
                "-i", looped,
                "-vf", f"subtitles='{srt_ff}':force_style='{style}'",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                "-c:a", "copy",
                burned
            ], check=True)
            segments.append(burned)
            print(f"{key}: {len(sentences)} lines, {vo_dur:.1f}s")

        concat_list = os.path.join(tmp, "concat.txt")
        with open(concat_list, "w", encoding="utf-8") as f:
            for p in segments:
                f.write(f"file '{p.replace(chr(92), '/')}'\n")

        out_path = os.path.join(videos_dir, f"{args.campaign.title()}_narrated_{args.lang.upper()}.mp4")
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", concat_list,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-c:a", "aac", "-b:a", "160k",
            out_path
        ], check=True)

    print(f"\nDone: {out_path}")


if __name__ == "__main__":
    main()
