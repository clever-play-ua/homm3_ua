#!/usr/bin/env python3
"""
Problem this solves: `014_organize_mission_media.py` places each mission's
`*_Intro*` video/audio/subtitle files loose inside the mission folder,
next to `texts.json` - fine, but scattered, and nothing on disk records
which original game archive + entry name each asset needs to become again
when it's time to build the mod back up (that mapping only lives in
Python, split across this file's own `004_extract_campaign_videos.py`
import and `014`'s `CAMPAIGNS`/`NARRATION_KEYS` tables). This script
bundles all of one mission's media into a single self-contained
`<Mission>_Media/` subfolder (e.g. `001_Borderlands/Borderlands_Media/` -
note the folder/manifest name drops the mission's own `NNN_` numbering,
unlike the files inside it) with a `<Mission>_Media.json` manifest next
to them recording exactly that mapping - so reassembling the mod later
only needs to read the manifest sitting next to the files, not re-derive
the mapping from source.

Requires `014_organize_mission_media.py` to have already been run (this
script MOVES its output, it doesn't regenerate it) and Hurtom-original
`005_RAW/<campaign>/videos/` + `voiceover_en/` to still exist (this is
where the manifest's `source_entry`/`target_archive` cross-reference comes
from - see `video_source_lookup()`).

Manifest shape (`<Mission>_Media.json`):
    {
      "video": [
        {"local_file": "001_Borderlands_Intro.mp4",
         "source_entry": "NEUTRALA.SMK", "target_archive": "VIDEO.VID"}
      ],
      "audio_en": {"local_file": "001_Borderlands_Intro_en.wav",
                    "source_entry": "N1A", "target_archive": "Heroes3.snd"}
                   (null if this mission never had extracted voiceover),
      "subtitles": {"en": "001_Borderlands_Intro_en.txt",
                    "ua": "001_Borderlands_Intro_ua.txt"}
    }
`video` is always a list (even for the common single-clip case) since a
few missions have 2-3 parts (see `014`'s own docstring for which ones and
why) - each part is its own archive entry, so each needs its own
`source_entry`.

**Voiceover source is always `Heroes3.snd`, entry name = the code with NO
extension** (confirmed via `mmarch list Heroes3.snd` - e.g. `G1A`, `N1C_D`,
not `G1A.wav`; the local `_en.wav` files are mmarch's own PCM extraction
of that raw entry, same convention as `011_burn_campaign_subtitles.py`
already relies on). Video source is always `VIDEO.VID` for per-mission
clips (confirmed empirically - none of the newly-found AB/SoD per-mission
files live in `H3ab_ahd.vid`, only the campaign-level intro clips this
project no longer bundles per mission do).

After bundling every mission, deletes each campaign's now-redundant flat
`videos/`/`voiceover_en/` extraction folders - safe to delete since
they're 100% regenerable from the live game via `004_extract_campaign_videos.py`
(the game files are the actual source of truth, not this local cache),
and everything mission-relevant in them has just been copied into a
`_Media/` folder. This includes silently discarding each campaign's
never-bundled intro clip (e.g. `CGOOD1.mp4`, `hack.mp4`) - deliberate,
per an explicit "we don't need that video, remove it everywhere" decision
(see git history/chat log around when `014` stopped copying it into
`000_..._description/`).

Usage:
    python 015_bundle_mission_media.py [--raw ../../005_RAW]
"""
import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_RAW = os.path.join(REPO_ROOT, "005_RAW")

sys.path.insert(0, SCRIPT_DIR)
organize_mod = importlib.import_module("014_organize_mission_media")
videos_mod = importlib.import_module("004_extract_campaign_videos")

CAMPAIGNS = organize_mod.CAMPAIGNS
NARRATION_KEYS = organize_mod.NARRATION_KEYS
VIDEOS = videos_mod.VIDEOS

AUDIO_ARCHIVE = "Heroes3.snd"
VIDEO_ARCHIVE = "VIDEO.VID"


def video_source_lookup() -> dict[str, tuple]:
    """Cross-references `004_extract_campaign_videos.py`'s `VIDEOS` table
    (original archive entry names, e.g. `GOOD1A.BIK`/`H3ABab2.smk`) against
    the already-converted local `.mp4` stems `014`'s `CAMPAIGNS` table
    uses (`GOOD1A.mp4`) - both ultimately name the same clip, just before/
    after ffmpeg conversion. In: nothing (reads both modules' constants
    directly). Out: {lowercased stem: (original_entry_name, archive)},
    e.g. {'good1a': ('GOOD1A.BIK', 'VIDEO.VID')}."""
    lookup = {}
    for _stem, (_folder, archive, files) in VIDEOS.items():
        for fn in files:
            stem = os.path.splitext(fn)[0].lower()
            lookup[stem] = (fn, archive)
    return lookup


def probe_audio_format(path: str) -> dict:
    """Reads the actual codec/rate/channel/depth of a `.wav` via `ffprobe`,
    recorded in the manifest so a future re-encode of a translated
    voiceover clip knows exactly what to match without re-probing. In:
    path to a `.wav` file. Out: {'codec', 'sample_rate', 'channels',
    'bits_per_sample'} - e.g. `{"codec": "adpcm_ima_wav", "sample_rate":
    22050, "channels": 1, "bits_per_sample": 4}`, confirmed this is the
    game's own original format (not an mmarch re-encode) by inspecting
    the extracted file's own RIFF header directly."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=codec_name,sample_rate,channels,bits_per_sample",
         "-of", "json", path],
        check=True, capture_output=True, text=True,
    ).stdout
    stream = json.loads(out)["streams"][0]
    return {
        "codec": stream["codec_name"],
        "sample_rate": int(stream["sample_rate"]),
        "channels": stream["channels"],
        "bits_per_sample": stream["bits_per_sample"],
    }


def strip_numbering(mission_folder: str) -> str:
    """In: a mission folder name (`001_Borderlands`, `000_Foo_description`).
    Out: the same name with a leading `NNN_` stripped (`Borderlands`) -
    matches how the user wants the bundle folder/manifest named, dropping
    the ordering prefix that only matters for sorting the folder listing."""
    return re.sub(r"^\d+_", "", mission_folder)


def bundle_mission(raw: str, campaign: str, mission_folder: str,
                    video_files: list, audio_file: str, video_lookup: dict) -> None:
    """Moves one mission's already-placed `*_Intro*` files into a new
    `<Mission>_Media/` subfolder and writes `<Mission>_Media.json` next to
    them. In: `raw`, campaign folder name, mission folder name, its
    `CAMPAIGNS` video-file list / audio filename, `video_source_lookup()`'s
    result. Out: none (mutates `raw/<campaign>/missions/<mission_folder>/`)."""
    mission_dir = os.path.join(raw, campaign, "missions", mission_folder)
    if not os.path.isdir(mission_dir):
        return
    base_name = f"{mission_folder}_Intro"
    media_name = f"{strip_numbering(mission_folder)}_Media"
    media_dir = os.path.join(mission_dir, media_name)

    manifest: dict[str, Any] = {"video": [], "audio_en": None, "subtitles": {}}
    moved_any = False

    if len(video_files) == 1:
        local_names = [f"{base_name}.mp4"]
    else:
        local_names = [f"{base_name}_{i + 1}.mp4" for i in range(len(video_files))]
    for local_name, orig_file in zip(local_names, video_files, strict=True):
        src = os.path.join(mission_dir, local_name)
        if not os.path.isfile(src):
            continue
        os.makedirs(media_dir, exist_ok=True)
        shutil.move(src, os.path.join(media_dir, local_name))
        moved_any = True
        orig_entry, archive = video_lookup.get(os.path.splitext(orig_file)[0].lower(),
                                                (orig_file, VIDEO_ARCHIVE))
        manifest["video"].append({"local_file": local_name, "source_entry": orig_entry,
                                   "target_archive": archive})

    if audio_file:
        local_name = f"{base_name}_en.wav"
        src = os.path.join(mission_dir, local_name)
        if os.path.isfile(src):
            os.makedirs(media_dir, exist_ok=True)
            dst = os.path.join(media_dir, local_name)
            shutil.move(src, dst)
            moved_any = True
            source_entry = os.path.splitext(audio_file)[0]  # snd entries have no extension
            manifest["audio_en"] = {"local_file": local_name, "source_entry": source_entry,
                                     "target_archive": AUDIO_ARCHIVE, "format": probe_audio_format(dst)}

    for lang in ("en", "ua"):
        local_name = f"{base_name}_{lang}.txt"
        src = os.path.join(mission_dir, local_name)
        if os.path.isfile(src):
            os.makedirs(media_dir, exist_ok=True)
            shutil.move(src, os.path.join(media_dir, local_name))
            moved_any = True
            manifest["subtitles"][lang] = local_name

    if not moved_any:
        return
    with open(os.path.join(media_dir, f"{media_name}.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  {mission_folder}/{media_name}/ ({len(manifest['video'])} video part(s), "
          f"audio={'yes' if manifest['audio_en'] else 'no'})")


def cleanup_flat_folders(raw: str, campaign: str) -> None:
    """Deletes the now-redundant flat `videos/`/`voiceover_en/` extraction
    folders for one campaign - see module docstring for why this is safe.
    In: `raw`, campaign folder name. Out: none (deletes
    `raw/<campaign>/videos/` and `.../voiceover_en/` if present)."""
    campaign_dir = os.path.join(raw, campaign)
    for name in ("videos", "voiceover_en"):
        path = os.path.join(campaign_dir, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"  removed {campaign}/{name}/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=DEFAULT_RAW)
    args = ap.parse_args()

    video_lookup = video_source_lookup()

    for campaign, spec in CAMPAIGNS.items():
        print(f"=== {campaign} ===")
        for mission_folder, video_files, audio_file in spec["missions"]:
            bundle_mission(args.raw, campaign, mission_folder, video_files, audio_file, video_lookup)
        cleanup_flat_folders(args.raw, campaign)


if __name__ == "__main__":
    main()
