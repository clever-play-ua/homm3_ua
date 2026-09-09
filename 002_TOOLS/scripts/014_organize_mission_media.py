#!/usr/bin/env python3
"""
Problem this solves: `003_extract_campaigns.py`/`004_extract_campaign_videos.py`
dump every cutscene into one flat `005_RAW/<NNN>_<Campaign>/videos/` folder
per campaign, using the game's own cryptic short codes as filenames
(`GOOD1A.mp4`, `G1A.wav`, `EVIL2AP1.mp4`, ...) - fine for extraction, but
awkward for actually working mission-by-mission, since `.../missions/<NNN>_<Mission>/`
already holds that mission's `<Mission>_text.json` and is where a future `.srt` +
translation would naturally belong too. This script copies (never moves -
the flat `videos/`/`voiceover_en/` folders stay put, nothing here depends
on them going away) each cutscene/voiceover file into the mission folder
it actually belongs to, renamed to `<MissionFolder>_Intro.mp4` /
`<MissionFolder>_Intro_en.wav` (multi-part missions get `_Intro_1.mp4`,
`_Intro_2.mp4`, ...) plus a plain-text `<MissionFolder>_Intro_en.txt` (and
`..._ua.txt`, since Hurtom's translation of this text already exists -
see below) - so `.../missions/<NNN>_<Mission>/` ends up self-contained:
`<Mission>_text.json` (the mission's OTHER text - quests, map events, etc, a
separate concern from this) + this intro package, ready to hand to a
translator or build a `.srt` from later. **Deliberately does NOT copy the
campaign-level intro clip anywhere** - that one plays on the campaign
SELECTION menu, before you even pick a mission, not during a mission -
out of scope for this per-mission package.

**Only the 7 original RoE campaigns (001-007) have real per-mission
voiceover** - confirmed by inspecting every campaign's `voiceover_en/`
folder; every campaign (all 20) DOES have a per-mission intro VIDEO once
you know the right archive filenames to look for (see
`004_extract_campaign_videos.py`'s "CORRECTED" docstring note - AB/SoD's
per-mission clips use much less obvious `H3AB<code><N>.smk`/
`H3x2_<CODE><letter>.smk` names that an early pass here missed entirely).

**The letter-suffix-to-mission mapping below is empirically confirmed,
not inferred generically** - built by counting each campaign's actual
mission folders against its video-letter count (they always matched) and,
for the irregular cases (`005_Long_Live_the_King`'s mission 1 has THREE
video parts, `009_Dragons_Blood`'s mission 3 and
`018_Rise_of_the_Necromancer`'s mission 4 have two), by checking each
part's actual duration with `ffprobe` to confirm play order (e.g. EVIL2's
1.4s/10.9s/3.1s - a short title card, the real cutscene, a short tail).
Multi-part missions get `_Intro_1.mp4`, `_Intro_2.mp4`, ... in order;
everyone else gets a single `_Intro.mp4`. `006_Spoils_of_War`'s `N1C_D.wav`
(one audio file apparently covering two letters) is mapped to mission 3
(`Greed`) as a best-effort guess - flagged in `CAMPAIGNS`' own comment,
worth a manual listen to confirm before relying on it for subtitle timing.
`014_Hack_and_Slash`'s per-mission clip series skips letter `b` entirely -
mission 1 (`Bashing_Skulls`) has no dedicated intro clip at all (text
only), see `004_extract_campaign_videos.py` for the reasoning.

**Text source differs by campaign group, but the OUTPUT shape is the
same**: for the 7 RoE campaigns, it's `CAMPDIAG.TXT` (already extracted as
`005_RAW/H3bitmap.lod/CAMPDIAG.json`) - the actual narration/caption
script that plays alongside the voiceover, keyed by the same short codes
as the video/audio filenames (`Good1a`, `Evil2ap`, `Neutral1c/d`, ...).
For the other 13 (AB/SoD), there's no `CAMPDIAG.TXT` entry at all - their
per-mission intro screen shows the `.h3c` wrapper's own
`wrapper_prolog`/`wrapper_epilog` text instead, already extracted (EN+UA,
already translated) into each mission's own `<Mission>_text.json` - confirmed by
matching a live screenshot's on-screen text word-for-word against
`017_Elixir_of_Life/missions/002_Cutthroats/002_Cutthroats_text.json`'s
`wrapper_epilog`. Either way, this script joins however many text records
a mission has (some have 2 - one narration entry per video part, or
prolog+epilog) into one EN and one UA plain-text file, records separated
by a blank line - this is raw source text for a FUTURE `.srt`, not itself
timed against the audio; building real subtitle timing is a separate,
not-yet-done step.

Usage:
    python 014_organize_mission_media.py [--raw ../../005_RAW]
"""
import argparse
import glob
import json
import os
import shutil
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_RAW = os.path.join(REPO_ROOT, "005_RAW")

# campaign folder -> {
#   "intro": <videos/ filename for the campaign-level cutscene, or None>,
#   "missions": [ (mission folder name, [video filenames in play order], audio filename or None), ... ]
# }
CAMPAIGNS: dict[str, dict[str, Any]] = {
    "001_Long_Live_the_Queen": {
        "intro": "CGOOD1.mp4",
        "missions": [
            ("001_Homecoming", ["GOOD1A.mp4"], "G1A.wav"),
            ("002_Guardian_Angels", ["GOOD1B.mp4"], "G1B.wav"),
            ("003_Griffin_Cliff", ["GOOD1C.mp4"], "G1C.wav"),
        ],
    },
    "002_Liberation": {
        "intro": "CGOOD2.mp4",
        "missions": [
            ("001_Steadwicks_Liberation", ["GOOD2A.mp4"], "G2A.wav"),
            ("002_Deal_With_the_Devil", ["GOOD2B.mp4"], "G2B.wav"),
            ("003_Neutral_Affairs", ["GOOD2C.mp4"], "G2C.wav"),
            ("004_Tunnels_and_Troglodytes", ["GOOD2D.mp4"], "G2D.wav"),
        ],
    },
    "003_Song_for_the_Father": {
        "intro": "CGOOD3.mp4",
        "missions": [
            ("001_Safe_Passage", ["GOOD3A.mp4"], "G3A.wav"),
            ("002_United_Front", ["GOOD3B.mp4"], "G3B.wav"),
            ("003_For_King_and_Country", ["GOOD3C.mp4"], "G3C.wav"),
        ],
    },
    "004_Dungeons_and_Devils": {
        "intro": "CEVIL1.mp4",
        "missions": [
            ("001_A_Devilish_Plan", ["EVIL1A.mp4"], "E1A.wav"),
            ("002_Groundbreaking", ["EVIL1B.mp4"], "E1B.wav"),
            ("003_Steadwicks_Fall", ["EVIL1C.mp4"], "E1C.wav"),
        ],
    },
    "005_Long_Live_the_King": {
        "intro": "CEVIL2.mp4",
        "missions": [
            # 3 video parts confirmed by duration (ffprobe): 1.4s title
            # card, 10.9s real cutscene, 3.1s tail - "A, AP1, AP2" order.
            ("001_A_Gryphons_Heart", ["EVIL2A.mp4", "EVIL2AP1.mp4", "EVIL2AP2.mp4"], "E2A.wav"),
            ("002_Season_of_Harvest", ["EVIL2B.mp4"], "E2B.wav"),
            ("003_Corporeal_Punishment", ["EVIL2C.mp4"], "E2C.wav"),
            ("004_From_Day_to_Night", ["EVIL2D.mp4"], "E2D.wav"),
        ],
    },
    "006_Spoils_of_War": {
        "intro": "CNEUTRAL.mp4",
        "missions": [
            ("001_Borderlands", ["NEUTRALA.mp4"], "N1A.wav"),
            ("002_Gold_Rush", ["NEUTRALB.mp4"], "N1B.wav"),
            # N1C_D.wav's name suggests it may cover two letters' worth of
            # audio - best-effort guess, worth a manual listen to confirm.
            ("003_Greed", ["NEUTRALC.mp4"], "N1C_D.wav"),
        ],
    },
    "007_Seeds_of_Discontent": {
        "intro": "CSECRET.mp4",
        "missions": [
            ("001_The_Grail", ["SECRETA.mp4"], "S1A.wav"),
            ("002_Independence", ["SECRETB.mp4"], "S1B.wav"),
            ("003_The_Road_Home", ["SECRETC.mp4"], "S1C.wav"),
        ],
    },
    # AB/SoD campaigns: DO have per-mission clips after all, just under a
    # much less obvious naming series that an earlier pass here missed
    # entirely - see 004_extract_campaign_videos.py's "CORRECTED" docstring
    # note for the full story (H3ABxxN.smk / H3x2_XXletter.smk in
    # VIDEO.VID). None ever had extracted voiceover, so `audio_file` is
    # always None here - confirmed no such files exist for these archives.
    "008_Armageddons_Blade": {
        "intro": "C1ab7.mp4",
        "missions": [
            ("001_Catherines_Charge", ["H3ABab2.mp4"], None),
            ("002_Seeking_Armageddon", ["H3ABab3.mp4"], None),
            ("003_Shadows_of_the_Forest", ["H3ABab4.mp4"], None),
            ("004_Maker_of_Sorrows", ["H3ABab5.mp4"], None),
            ("005_Return_of_the_King", ["H3ABab6.mp4"], None),
            ("006_A_Blade_in_the_Back", ["H3ABab7.mp4"], None),
            ("007_To_Kill_A_Hero", ["H3ABab8.mp4"], None),
            ("008_Oblivions_Edge", ["H3ABab9.mp4"], None),
        ],
    },
    "009_Dragons_Blood": {
        "intro": "C1db2.mp4",
        "missions": [
            ("001_Culling_the_Weak", ["H3ABdb2.mp4"], None),
            ("002_Savaging_the_Scavengers", ["H3ABdb3.mp4"], None),
            # 2-part mission, same shape as RoE's EVIL2A/EVIL2AP1/AP2.
            ("003_Blood_of_the_Dragon_Father", ["H3ABdb4.mp4", "H3ABdb4b.mp4"], None),
            ("004_Blood_Thirsty", ["H3ABdb5.mp4"], None),
        ],
    },
    "010_Dragon_Slayer": {
        "intro": "C1ds1.mp4",
        "missions": [
            ("001_Rust_Dragons", ["H3ABds2.mp4"], None),
            ("002_Faerie_Dragons", ["H3ABds3.mp4"], None),
            ("003_Azure_Dragons", ["H3ABds4.mp4"], None),
            ("004_Crystal_Dragons", ["H3ABds5.mp4"], None),
        ],
    },
    "011_Festival_of_Life": {
        "intro": "C1fl3.mp4",
        "missions": [
            ("001_For_the_Throne", ["H3ABfl2.mp4"], None),
            ("002_Clan_War", ["H3ABfl3.mp4"], None),
            ("003_Taming_of_the_wild", ["H3ABfl4.mp4"], None),
            ("004_Razor_Claw", ["H3ABfl5.mp4"], None),
        ],
    },
    "012_Foolhardy_Waywardness": {
        "intro": "C1fw1.mp4",
        "missions": [
            ("001_Lost_at_Sea", ["H3ABfw2.mp4"], None),
            ("002_Here_There_Be_Pirates", ["H3ABfw3.mp4"], None),
            ("003_Hurry_Up_and_Wait", ["H3ABfw4.mp4"], None),
            ("004_Their_End_of_the_Bargain", ["H3ABfw5.mp4"], None),
        ],
    },
    "013_Playing_with_Fire": {
        "intro": "C1pf2.mp4",
        "missions": [
            ("001_Farming_Towns", ["H3ABpf2.mp4"], None),
            ("002_March_of_the_Undead", ["H3ABpf3.mp4"], None),
            ("003_Burning_of_Tatalia", ["H3ABpf4.mp4"], None),
        ],
    },
    "014_Hack_and_Slash": {
        "intro": "hack.mp4",
        "missions": [
            # letter 'b' never existed (only a,c,d,e) - mission 1 has no
            # dedicated clip of its own (empty video list, text-only),
            # see docstring note.
            ("001_Bashing_Skulls", [], None),
            ("002_Black_Sheep", ["H3x2_HSc.mp4"], None),
            ("003_A_Cage_in_the_Hand", ["H3x2_HSd.mp4"], None),
            ("004_Grave_Robber", ["H3x2_HSe.mp4"], None),
        ],
    },
    "015_Birth_of_a_Barbarian": {
        "intro": "Birth.mp4",
        "missions": [
            ("001_On_the_Run", ["H3x2_BBb.mp4"], None),
            ("002_The_Meeting", ["H3x2_BBc.mp4"], None),
            ("003_A_Tough_Start", ["H3x2_BBd.mp4"], None),
            ("004_Falor_and_Terwen", ["H3x2_BBe.mp4"], None),
            ("005_Returning_to_Bracada", ["H3x2_BBf.mp4"], None),
        ],
    },
    "016_New_Beginning": {
        "intro": "new.mp4",
        "missions": [
            ("001_Clearing_the_Border", ["H3x2_NBb.mp4"], None),
            ("002_After_the_Amulet", ["H3x2_NBc.mp4"], None),
            ("003_Retrieving_the_Cowl", ["H3x2_NBd.mp4"], None),
            ("004_Driving_for_the_Boots", ["H3x2_NBe.mp4"], None),
        ],
    },
    "017_Elixir_of_Life": {
        "intro": "elixir.mp4",
        "missions": [
            ("001_Graduation_Exercise", ["H3x2_ELb.mp4"], None),
            ("002_Cutthroats", ["H3x2_ELc.mp4"], None),
            ("003_Valley_of_the_Dragon_Lords", ["H3x2_ELd.mp4"], None),
            ("004_A_Thief_in_the_Night", ["H3x2_ELe.mp4"], None),
        ],
    },
    "018_Rise_of_the_Necromancer": {
        "intro": "rise.mp4",
        "missions": [
            ("001_Target", ["H3x2_RNb.mp4"], None),
            ("002_Master", ["H3x2_RNc.mp4"], None),
            ("003_Finneas_Vilmar", ["H3x2_RNd.mp4"], None),
            # 2-part mission.
            ("004_Duke_Alarice", ["H3x2_RNe1.mp4", "H3x2_RNe2.mp4"], None),
        ],
    },
    "019_Unholy_Alliance": {
        "intro": "unholy.mp4",
        "missions": [
            ("001_Harvest", ["H3x2_UAb.mp4"], None),
            ("002_Gathering_the_Legion", ["H3x2_UAc.mp4"], None),
            ("003_Search_for_a_Killer", ["H3x2_UAd.mp4"], None),
            ("004_Final_Peace", ["H3x2_UAe.mp4"], None),
            ("005_Secrets_Revealed", ["H3x2_UAf.mp4"], None),
            ("006_Agents_of_Vengeance", ["H3x2_UAg.mp4"], None),
            ("007_Wrath_of_Sandro", ["H3x2_UAh.mp4"], None),
            ("008_Invasion", ["H3x2_UAi.mp4"], None),
            ("009_To_Strive_To_Seek", ["H3x2_UAj.mp4"], None),
            ("010_Barbarian_Brothers", ["H3x2_UAk.mp4"], None),
            ("011_Union", ["H3x2_UAl.mp4"], None),
            ("012_Fall_of_Sandro", ["H3x2_UAm.mp4"], None),
        ],
    },
    "020_Specter_of_Power": {
        "intro": "spectre.mp4",
        "missions": [
            ("001_Poison_Fit_for_a_King", ["H3x2_SPb.mp4"], None),
            ("002_To_Build_a_Tunnel", ["H3x2_SPc.mp4"], None),
            ("003_Kreegan_Alliance", ["H3x2_SPd.mp4"], None),
            ("004_With_Blinders_On", ["H3x2_SPe.mp4"], None),
        ],
    },
}

# campaign folder -> {mission folder -> [CAMPDIAG.TXT key(s), in order]}.
# Only the 7 RoE campaigns have CAMPDIAG.TXT entries at all - see
# docstring for how these keys were matched to missions (they're
# literally the same short codes as the video/voiceover filenames).
NARRATION_KEYS: dict[str, dict[str, list[str]]] = {
    "001_Long_Live_the_Queen": {
        "001_Homecoming": ["Good1a"],
        "002_Guardian_Angels": ["Good1b"],
        "003_Griffin_Cliff": ["Good1c"],
    },
    "002_Liberation": {
        "001_Steadwicks_Liberation": ["Good2a"],
        "002_Deal_With_the_Devil": ["Good2b"],
        "003_Neutral_Affairs": ["Good2c"],
        "004_Tunnels_and_Troglodytes": ["Good2d"],
    },
    "003_Song_for_the_Father": {
        "001_Safe_Passage": ["Good3a"],
        "002_United_Front": ["Good3b"],
        "003_For_King_and_Country": ["Good3c"],
    },
    "004_Dungeons_and_Devils": {
        "001_A_Devilish_Plan": ["Evil1a"],
        "002_Groundbreaking": ["Evil1b"],
        "003_Steadwicks_Fall": ["Evil1c"],
    },
    "005_Long_Live_the_King": {
        "001_A_Gryphons_Heart": ["Evil2a", "Evil2ap"],
        "002_Season_of_Harvest": ["Evil2b"],
        "003_Corporeal_Punishment": ["Evil2c"],
        "004_From_Day_to_Night": ["Evil2d"],
    },
    "006_Spoils_of_War": {
        "001_Borderlands": ["Neutral1a"],
        "002_Gold_Rush": ["Neutral1b"],
        "003_Greed": ["Neutral1c/d"],
    },
    "007_Seeds_of_Discontent": {
        "001_The_Grail": ["Secret1a"],
        "002_Independence": ["Secret1b"],
        "003_The_Road_Home": ["Secret1c"],
    },
}


def load_campdiag(raw: str) -> dict[str, dict[str, str]]:
    """In: `raw` (005_RAW root). Out: {code: {'en': ..., 'ua': ...}} for
    every `CAMPDIAG.TXT` entry, with the redundant leading "code\\t"
    `002_build_raw.py` leaves on each value (it's the raw record content,
    which starts with the code as plain text in the file itself) stripped
    off both languages."""
    path = os.path.join(raw, "H3bitmap.lod", "CAMPDIAG.json")
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    out = {}
    for e in entries:
        code = e["var"].removeprefix("CAMPDIAG_")
        texts = {}
        for lang in ("en", "ua"):
            text = e[lang]
            prefix = code + "\t"
            texts[lang] = text[len(prefix):] if text.startswith(prefix) else text
        out[code] = texts
    return out


def narration_records_campdiag(campaign: str, mission_folder: str, campdiag: dict) -> list:
    """RoE campaigns' narration source: `CAMPDIAG.TXT`. In: campaign
    folder name, mission folder name, `load_campdiag()`'s result. Out:
    list of `{key, en, ua}`, one per `NARRATION_KEYS` entry for this
    mission (empty list if this mission has none)."""
    records = []
    for key in NARRATION_KEYS.get(campaign, {}).get(mission_folder, []):
        if key not in campdiag:
            print(f"  WARNING: CAMPDIAG key {key!r} not found for {mission_folder}")
            continue
        records.append({"key": key, **campdiag[key]})
    return records


def narration_records_texts_json(mission_dir: str) -> list:
    """AB/SoD campaigns' narration source: the mission's own
    `<MissionFolder>_text.json` (build_mission_texts.py's per-mission
    output - see that file's docstring for why it's named this way, not a
    bare `texts.json`)'s `wrapper_prolog`/`wrapper_epilog` fields (already
    extracted, already translated - see module docstring for how this was
    confirmed correct against a live screenshot). In: the mission folder's
    path. Out: list of `{key, en, ua}` for whichever of the two fields are
    present (empty list if the file is missing or has neither)."""
    texts_candidates = glob.glob(os.path.join(mission_dir, "*_text.json"))
    if not texts_candidates:
        return []
    texts_path = texts_candidates[0]
    with open(texts_path, encoding="utf-8") as f:
        entries = {e["field"]: e for e in json.load(f) if "field" in e}
    return [{"key": field, "en": entries[field]["en"], "ua": entries[field]["ua"]}
            for field in ("wrapper_prolog", "wrapper_epilog") if field in entries]


def write_intro_texts(mission_dir: str, base_name: str, records: list) -> None:
    """Writes `<base_name>_en.txt` / `<base_name>_ua.txt`, each record's
    text joined by a blank line in order. In: the mission folder, the
    shared base filename (`<MissionFolder>_Intro`), the records from
    either `narration_records_*` function above. Out: none (writes the
    two `.txt` files; does nothing if `records` is empty)."""
    if not records:
        return
    for lang in ("en", "ua"):
        text = "\n\n".join(r[lang] for r in records)
        with open(os.path.join(mission_dir, f"{base_name}_{lang}.txt"), "w", encoding="utf-8") as f:
            f.write(text)
    print(f"  {base_name}_en.txt / _ua.txt <- {[r['key'] for r in records]}")


def copy_if_present(src: str, dst: str) -> bool:
    """In: source and destination paths. Out: True if `src` existed and
    was copied (skipped silently, not an error, if it didn't - some
    campaigns' folders are smaller subsets, see module docstring)."""
    if not os.path.isfile(src):
        return False
    shutil.copy2(src, dst)
    return True


def organize_campaign(raw: str, campaign: str, spec: dict, campdiag: dict) -> None:
    """Copies every mission's video(s)/audio into their respective
    `missions/<NNN>_<Mission>/` folders as `<MissionFolder>_Intro*`, and
    writes the matching `_en.txt`/`_ua.txt`. Deliberately does NOT touch
    the campaign-level intro clip (`spec["intro"]`) - see module
    docstring for why that one is out of scope here. In: `raw` (005_RAW
    root), campaign folder name, its `CAMPAIGNS` entry, `load_campdiag()`'s
    result. Out: none (writes into `raw/<campaign>/missions/*/`)."""
    campaign_dir = os.path.join(raw, campaign)
    videos_dir = os.path.join(campaign_dir, "videos")
    voiceover_dir = os.path.join(campaign_dir, "voiceover_en")
    missions_dir = os.path.join(campaign_dir, "missions")
    uses_campdiag = campaign in NARRATION_KEYS

    for mission_folder, video_files, audio_file in spec["missions"]:
        mission_dir = os.path.join(missions_dir, mission_folder)
        if not os.path.isdir(mission_dir):
            print(f"  SKIP {mission_folder}: folder not found under {missions_dir}")
            continue
        base_name = f"{mission_folder}_Intro"

        if len(video_files) == 1:
            targets = [(video_files[0], f"{base_name}.mp4")]
        else:
            targets = [(vf, f"{base_name}_{i + 1}.mp4") for i, vf in enumerate(video_files)]
        for src_name, dst_name in targets:
            if copy_if_present(os.path.join(videos_dir, src_name),
                                os.path.join(mission_dir, dst_name)):
                print(f"  {dst_name} <- {src_name}")

        if audio_file and copy_if_present(os.path.join(voiceover_dir, audio_file),
                                           os.path.join(mission_dir, f"{base_name}_en.wav")):
            print(f"  {base_name}_en.wav <- {audio_file}")

        records = (narration_records_campdiag(campaign, mission_folder, campdiag) if uses_campdiag
                   else narration_records_texts_json(mission_dir))
        write_intro_texts(mission_dir, base_name, records)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=DEFAULT_RAW)
    args = ap.parse_args()

    campdiag = load_campdiag(args.raw)

    for campaign, spec in CAMPAIGNS.items():
        print(f"=== {campaign} ===")
        organize_campaign(args.raw, campaign, spec, campdiag)


if __name__ == "__main__":
    main()
