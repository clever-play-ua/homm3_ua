#!/usr/bin/env python3
"""
Problem this solves: puts the campaign intro cutscene(s) next to each
campaign's extracted text, converted from the game's Bink (.BIK) format to
.mp4 so they're actually viewable. The source .BIK files have no audio
track of their own (voiceover is a separate .snd entry the engine plays
alongside) - the resulting .mp4 is silent, that's not a conversion bug.

Video filename -> campaign mapping was worked out by hand from `mmarch list`
on VIDEO.VID / H3ab_ahd.vid: the 7 original RoE campaigns have one intro
video per campaign ("CGOOD1.BIK" etc) plus one video per scenario/mission
("GOOD1A.BIK", "GOOD1B.BIK", ...); the 13 AB/SoD-era campaigns only ever
had a single video for the whole campaign, reused across missions.

Usage:
    python 004_extract_campaign_videos.py [--game "F:/Games/HoMM 3 Complete"]

Requires: mmarch (npm i -g mmarch) and ffmpeg on PATH.
Output: <repo>/005_RAW/<NNN>_<CampaignName>/videos/<name>.mp4
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_OUT = os.path.join(REPO_ROOT, "005_RAW")

# stem -> (folder_name matching 003_extract_campaigns.py's numbering, archive, [video files])
# archive is "VIDEO.VID" (main) or "H3ab_ahd.vid" (Armageddon's Blade only)
VIDEOS = {
    "GOOD1":    ("001_Long_Live_the_Queen",       "VIDEO.VID",
                 ["CGOOD1.BIK", "GOOD1A.BIK", "GOOD1B.BIK", "GOOD1C.BIK"]),
    "GOOD2":    ("002_Liberation",                "VIDEO.VID",
                 ["CGOOD2.BIK", "GOOD2A.BIK", "GOOD2B.BIK", "GOOD2C.BIK", "GOOD2D.BIK"]),
    "GOOD3":    ("003_Song_for_the_Father",       "VIDEO.VID",
                 ["CGOOD3.BIK", "GOOD3A.BIK", "GOOD3B.BIK", "GOOD3C.BIK"]),
    "EVIL1":    ("004_Dungeons_and_Devils",       "VIDEO.VID",
                 ["CEVIL1.BIK", "EVIL1A.BIK", "EVIL1B.BIK", "EVIL1C.BIK"]),
    "EVIL2":    ("005_Long_Live_the_King",        "VIDEO.VID",
                 ["CEVIL2.BIK", "EVIL2A.BIK", "EVIL2AP1.BIK", "EVIL2AP2.BIK",
                  "EVIL2B.BIK", "EVIL2C.BIK", "EVIL2D.BIK"]),
    "NEUTRAL1": ("006_Spoils_of_War",             "VIDEO.VID",
                 ["CNEUTRAL.BIK", "NEUTRALA.BIK", "NEUTRALB.BIK", "NEUTRALC.BIK"]),
    "SECRET1":  ("007_Seeds_of_Discontent",       "VIDEO.VID",
                 ["CSECRET.BIK", "SECRETA.BIK", "SECRETB.BIK", "SECRETC.BIK"]),

    "AB":       ("008_Armageddons_Blade",         "H3ab_ahd.vid", ["C1ab7.bik"]),
    "BLOOD":    ("009_Dragons_Blood",             "H3ab_ahd.vid", ["C1db2.bik"]),
    "SLAYER":   ("010_Dragon_Slayer",             "H3ab_ahd.vid", ["C1ds1.bik"]),
    "FESTIVAL": ("011_Festival_of_Life",          "H3ab_ahd.vid", ["C1fl3.bik"]),
    "FOOL":     ("012_Foolhardy_Waywardness",     "H3ab_ahd.vid", ["C1fw1.bik"]),
    "FIRE":     ("013_Playing_with_Fire",         "H3ab_ahd.vid", ["C1pf2.bik"]),

    "CRAG":     ("014_Hack_and_Slash",            "VIDEO.VID", ["hack.bik"]),
    "YOG":      ("015_Birth_of_a_Barbarian",      "VIDEO.VID", ["Birth.bik"]),
    "GEM":      ("016_New_Beginning",             "VIDEO.VID", ["new.bik"]),
    "GELU":     ("017_Elixir_of_Life",            "VIDEO.VID", ["elixir.bik"]),
    "SANDRO":   ("018_Rise_of_the_Necromancer",   "VIDEO.VID", ["rise.bik"]),
    "FINAL":    ("019_Unholy_Alliance",           "VIDEO.VID", ["unholy.bik"]),
    "SECRET":   ("020_Specter_of_Power",          "VIDEO.VID", ["spectre.bik"]),
}


def tool_path(name):
    p = shutil.which(name)
    if not p:
        sys.exit(f"{name} not found on PATH")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="F:/Games/HoMM 3 Complete")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    mmarch = tool_path("mmarch")
    ffmpeg = tool_path("ffmpeg")
    game_data = os.path.join(args.game, "Data")

    with tempfile.TemporaryDirectory() as tmp:
        by_archive = {}
        for _stem, (_folder, archive, files) in VIDEOS.items():
            by_archive.setdefault(archive, []).extend(files)

        extracted_dir = {}
        for archive, files in by_archive.items():
            out_dir = os.path.join(tmp, archive)
            os.makedirs(out_dir, exist_ok=True)
            subprocess.run(
                [mmarch, "extract", os.path.join(game_data, archive), out_dir, *sorted(set(files))], check=True
            )
            extracted_dir[archive] = out_dir

        total = 0
        for _stem, (folder, archive, files) in VIDEOS.items():
            out_dir = os.path.join(args.out, folder, "videos")
            os.makedirs(out_dir, exist_ok=True)
            for fn in files:
                src = None
                for cand in os.listdir(extracted_dir[archive]):
                    if cand.lower() == fn.lower():
                        src = os.path.join(extracted_dir[archive], cand)
                        break
                if src is None:
                    print(f"  MISSING {archive}/{fn}")
                    continue
                dst = os.path.join(out_dir, os.path.splitext(fn)[0] + ".mp4")
                subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", src,
                                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", dst], check=True)
                total += 1
            print(f"{folder}: {len(files)} video(s)")

    print(f"\nDone. {total} videos converted under {args.out}/<NNN>_<Campaign>/videos/")


if __name__ == "__main__":
    main()
