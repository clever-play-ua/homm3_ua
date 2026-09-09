#!/usr/bin/env python3
"""
Problem this solves: every full "clean rebuild + redeploy to the live
game" this project has ever done was a manual, error-prone sequence of
~6 separate steps run by hand (rebuild the 4 flat archives, copy them
over the live install, stage all 20 campaign `.h3c` files under their
CORRECT original entry names into the two archives that actually hold
them, inject + re-sort + verify each) - see git history/chat logs for how
many times this exact sequence was redone from scratch this project. This
script is that whole sequence as one command, so a fresh clone of this
repo can go from "pristine English GOG install" to "fully patched,
byte-verified Ukrainian install" without needing to know any of the
archive-routing trivia below by heart.

**Read before running**: this script OVERWRITES `--game`'s `Data/*.lod`
files and its `Maps/Tutorial.tut`. It backs up each archive it touches
under `<game>/UA_Patch_DEPLOY_BACKUPS/` (mirroring `012_safe_deploy.py`'s
own backup - never overwritten once created), but that backup is only
ever taken from whatever the archive looked like the FIRST time any
script in this project touched it. If `--game` is not a genuinely clean
install (e.g. it's a previous partial deploy, or a non-English GOG
language pack was ever active on it), that unclean state is what gets
backed up as "the original" - **verify `--game` is a pristine, English-
language GOG "HoMM 3 Complete" install before the very first run.** After
that, re-running this script is always safe and idempotent.

**Which archive(s) hold which campaign is discovered at run time, not
hardcoded** (see `homm3_campaign_deploy_replace_not_add` in this
project's notes for the two real bugs this avoided): most campaigns have
an INDEPENDENT copy in more than one archive - e.g. `Good1.h3c` exists in
both `H3ab_bmp.lod` (what actual mission gameplay reads) AND
`H3bitmap.lod` (what the pre-game campaign-overview screen reads) - and
injecting into only one leaves the other showing stale English text.
`resolve_campaign_archives()` runs `mmarch list` on every archive in
`CAMPAIGN_ARCHIVES` and injects each campaign into every archive actually
found to contain it, so this self-corrects if a future SoD/AB re-release
changes which archive holds what - nothing here needs to be hand-updated
for that.

Usage:
    python 013_deploy_full.py [--game "F:/Games/HoMM 3 Complete"]
                               [--raw ../../005_RAW] [--force]
                               [--skip-archives] [--skip-maps] [--skip-campaigns]
                               [--package [DIR]]

`--package` (optionally with a path, default `006_EASY_INSTALL/gog_complete`)
packages exactly what was just verified in `--game` into a ready-to-zip
release folder - the correct way to build a Nexus/easy-install release,
since it ships the actual verified state rather than a separately-built
copy that could silently drift from it (see `step_package_release`'s
docstring for why the OLD `004_HOMM3_complete` build folder alone was
never safe to ship - it never contained the campaign `.h3c` files).

Requires: mmarch (npm i -g mmarch), and everything 006_build_mod.py /
012_safe_deploy.py / deploy_campaign.py already require.
"""
import argparse
import importlib
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_RAW = os.path.join(REPO_ROOT, "005_RAW")
DEFAULT_TRANSLATED = os.path.join(REPO_ROOT, "001_ORIGINAL_HOMM3_FILES_HURTOM")
DEFAULT_BUILD_OUT = os.path.join(REPO_ROOT, "004_HOMM3_complete")
DEFAULT_RELEASE_OUT = os.path.join(REPO_ROOT, "006_EASY_INSTALL", "gog_complete")
ARCHIVES = ["H3bitmap.lod", "H3sprite.lod", "H3ab_bmp.lod", "H3ab_spr.lod"]

sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, "h3_parser"))
# 012_safe_deploy's module name starts with a digit, so it can't be a plain
# `import` statement - go through importlib instead (same reason
# 006_build_mod.py shells out to 007_fix_lod_sort_order.py as a subprocess
# rather than importing it; here we DO want the actual functions, so
# importlib is the one legal way to get them).
safe_deploy = importlib.import_module("012_safe_deploy")
from deploy_campaign import deploy as deploy_campaign  # noqa: E402  (must follow the sys.path.insert above)

# entry name -> (005_RAW campaign folder, stem). Deliberately NOT
# archive-scoped, unlike an earlier version of this table: a real,
# concretely-verified bug found that `Good1.h3c` (and, it turns out, all
# 13 RoE/AB-era campaigns) has a SEPARATE, independently-tracked copy in
# BOTH `H3ab_bmp.lod` and `H3bitmap.lod` - the pre-game "campaign
# overview" screen (title/description before you click Start) reads
# `H3bitmap.lod`'s copy, while actual mission gameplay reads
# `H3ab_bmp.lod`'s. Injecting into only one leaves the OTHER screen
# showing stale English text - a subtler variant of the same two-archive
# trap as [[homm3-flat-txt-h3bitmap-wins]], just for `.h3c` instead of
# flat `.TXT`. `resolve_campaign_archives()` below discovers, at run
# time, EVERY archive that actually has an entry with this name (via
# `mmarch list`) and injects into all of them - this table only says
# WHICH translated file goes with which entry name, not which archive(s).
CAMPAIGNS = {
    "Good1.h3c": ("001_Long_Live_the_Queen", "Good1"),
    "Good2.h3c": ("002_Liberation", "Good2"),
    "Good3.h3c": ("003_Song_for_the_Father", "Good3"),
    "Evil1.h3c": ("004_Dungeons_and_Devils", "Evil1"),
    "Evil2.h3c": ("005_Long_Live_the_King", "Evil2"),
    "Neutral1.h3c": ("006_Spoils_of_War", "Neutral1"),
    "Secret1.h3c": ("007_Seeds_of_Discontent", "Secret1"),
    "ab.h3c": ("008_Armageddons_Blade", "Ab"),
    "blood.h3c": ("009_Dragons_Blood", "blood"),
    "slayer.h3c": ("010_Dragon_Slayer", "slayer"),
    "festival.h3c": ("011_Festival_of_Life", "festival"),
    "fool.h3c": ("012_Foolhardy_Waywardness", "fool"),
    "fire.h3c": ("013_Playing_with_Fire", "fire"),
    "Crag.h3c": ("014_Hack_and_Slash", "Crag"),
    "Yog.h3c": ("015_Birth_of_a_Barbarian", "Yog"),
    "Gem.h3c": ("016_New_Beginning", "Gem"),
    "Gelu.h3c": ("017_Elixir_of_Life", "Gelu"),
    "Sandro.h3c": ("018_Rise_of_the_Necromancer", "Sandro"),
    "Final.h3c": ("019_Unholy_Alliance", "Final"),
    "Secret.h3c": ("020_Specter_of_Power", "Secret"),
}
# The two archives ever known to hold campaign .h3c entries. If a future
# GOG patch adds a third, add it here too - resolve_campaign_archives()
# checks every archive in this list for every campaign, it doesn't
# hardcode which campaign lives where.
CAMPAIGN_ARCHIVES = ["H3ab_bmp.lod", "H3bitmap.lod"]


def resolve_campaign_archives(game: str) -> dict:
    """Lists every `.h3c` entry actually present in each of
    `CAMPAIGN_ARCHIVES`, case-insensitively, so callers don't have to
    hardcode (and risk under-discovering, as happened for real - see
    `CAMPAIGNS`'s docstring) which archive(s) hold which campaign. In:
    --game. Out: {entry_name_lower: [archive_name, ...]} - e.g.
    `{'good1.h3c': ['H3ab_bmp.lod', 'H3bitmap.lod']}`."""
    mmarch = safe_deploy.mmarch_path()
    found: dict = {}
    for archive in CAMPAIGN_ARCHIVES:
        archive_path = os.path.join(game, "Data", archive)
        # no explicit separator arg: "|" (or most other punctuation) as an
        # argv element gets misinterpreted as a shell metacharacter when
        # subprocess launches mmarch's .CMD wrapper (Windows always runs
        # .CMD/.BAT through cmd.exe) - default newline-separated output is
        # safe to pass positionally instead.
        out = subprocess.run([mmarch, "list", archive_path],
                              check=True, capture_output=True, text=True).stdout
        for entry in out.splitlines():
            entry = entry.strip()
            if entry.lower().endswith(".h3c"):
                found.setdefault(entry.lower(), []).append(archive)
    return found


def step_rebuild_archives(game: str, out: str, force: bool) -> None:
    """Shells out to 006_build_mod.py (never imported - see that file's
    own note on why these top-level scripts stay independent) to build
    fresh copies of the 4 flat archives with every translated file
    injected. In: --game, --out, --force. Out: none (writes `out`)."""
    print("=== Step 1/4: rebuilding flat-text/image archives ===")
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, "006_build_mod.py"),
           "--game", game, "--out", out]
    if force:
        cmd.append("--force")
    subprocess.run(cmd, check=True)


def step_copy_archives(game: str, out: str) -> None:
    """Copies the freshly built archives + Tutorial.tut over the live
    install, taking a one-time backup of each archive first (never
    overwritten - see `safe_deploy.ensure_backup`). In: --game, the build
    output folder. Out: none (mutates `game`)."""
    print("\n=== Step 2/4: copying rebuilt archives over the live install ===")
    game_data = os.path.join(game, "Data")
    for name in ARCHIVES:
        dst = os.path.join(game_data, name)
        safe_deploy.ensure_backup(dst)
        shutil.copy2(os.path.join(out, "Data", name), dst)
        print(f"  copied {name}")
    tut_src = os.path.join(out, "Maps", "Tutorial.tut")
    if os.path.isfile(tut_src):
        shutil.copy2(tut_src, os.path.join(game, "Maps", "Tutorial.tut"))
        print("  copied Tutorial.tut")


def step_deploy_maps(game: str, translated: str) -> None:
    """Copies every standalone `*.h3m` in `translated` (Hurtom's original
    translation package - these are plain files, never rebuilt by any
    pipeline step, unlike the `.h3c` campaigns) over the live install's
    `Maps/` folder, one-time-backing-up each original first. A handful of
    maps in a live GOG install (later-patch additions, a `ZZ_TEST_*` dev
    map) have no Hurtom counterpart at all - left untouched, in English,
    since no translation exists for them; this is expected, not an error.
    In: --game, `translated` (default `001_ORIGINAL_HOMM3_FILES_HURTOM`).
    Out: none (mutates `game`'s `Maps/` folder)."""
    print("\n=== Step 3/4: deploying standalone single-player maps ===")
    maps_dir = os.path.join(game, "Maps")
    backup_dir = os.path.join(game, "UA_Patch_DEPLOY_BACKUPS", "Maps")
    count = 0
    for name in sorted(os.listdir(translated)):
        if not name.lower().endswith(".h3m"):
            continue
        dst = os.path.join(maps_dir, name)
        if not os.path.isfile(dst):
            continue  # this build's GOG install doesn't have this map at all
        backup_dst = os.path.join(backup_dir, name)
        if not os.path.isfile(backup_dst):
            os.makedirs(backup_dir, exist_ok=True)
            shutil.copy2(dst, backup_dst)
        shutil.copy2(os.path.join(translated, name), dst)
        count += 1
    print(f"  deployed {count} map(s)")


def resolve_campaign_h3c(raw: str, game: str, entry_name: str, folder: str,
                          stem: str, archives: list, tmp: str) -> str:
    """Finds (or builds) the translated `<stem>_UA.h3c` for one campaign.
    In: `raw` (005_RAW root), `game` + `archives` (for extracting the
    current EN original as deploy_campaign()'s input if a rebuild is
    needed - any one of `archives` has it, they're all the same original
    content by construction), the campaign's entry name/005_RAW folder/
    stem, a scratch tmp dir. Out: path to a ready-to-inject `.h3c` file -
    either the pre-built one already in the repo, or freshly rebuilt from
    `<folder>/missions/` on the spot."""
    prebuilt = os.path.join(raw, folder, f"{stem}_UA.h3c")
    if os.path.isfile(prebuilt):
        return prebuilt

    missions_dir = os.path.join(raw, folder, "missions")
    if not os.path.isdir(missions_dir):
        sys.exit(f"no pre-built {stem}_UA.h3c AND no {missions_dir} to "
                  f"rebuild it from - cannot deploy this campaign")
    print(f"  {stem}: no pre-built _UA.h3c, rebuilding from {missions_dir} ...")
    mmarch = safe_deploy.mmarch_path()
    orig_en = os.path.join(tmp, f"{stem}_orig.h3c")
    subprocess.run([mmarch, "extract", os.path.join(game, "Data", archives[0]),
                     tmp, entry_name], check=True)
    shutil.move(os.path.join(tmp, entry_name), orig_en)
    out_path = os.path.join(tmp, f"{stem}_UA_rebuilt.h3c")
    deploy_campaign(orig_en, missions_dir, out_path)
    return out_path


def step_deploy_campaigns(game: str, raw: str) -> None:
    """Stages every campaign's translated `.h3c` under its ORIGINAL entry
    name (never `_UA.h3c` alongside - see
    `homm3_campaign_deploy_replace_not_add`) and injects it into EVERY
    archive `resolve_campaign_archives()` finds actually holding that
    entry name - see `CAMPAIGNS`'s docstring for why a campaign can
    legitimately need injecting into more than one archive. In: --game,
    --raw. Out: none (mutates `game`'s campaign-holding archives); exits
    non-zero if any injected campaign fails verification."""
    print("\n=== Step 4/4: deploying all 20 campaigns ===")
    archive_map = resolve_campaign_archives(game)
    # invert to archive -> [(entry_name, folder, stem), ...] so each
    # archive gets exactly one 012_safe_deploy call for all its campaigns
    by_archive: dict = {}
    for entry_name, (folder, stem) in CAMPAIGNS.items():
        archives = archive_map.get(entry_name.lower())
        if not archives:
            sys.exit(f"{entry_name}: not found in any of {CAMPAIGN_ARCHIVES} "
                      f"- is --game a genuine HoMM 3 Complete install?")
        for archive in archives:
            by_archive.setdefault(archive, []).append((entry_name, folder, stem, archives))

    with tempfile.TemporaryDirectory() as tmp:
        for archive, campaigns in by_archive.items():
            stage_dir = os.path.join(tmp, archive)
            os.makedirs(stage_dir, exist_ok=True)
            staged_paths = []
            for entry_name, folder, stem, archives in campaigns:
                src = resolve_campaign_h3c(raw, game, entry_name, folder, stem, archives, tmp)
                dst = os.path.join(stage_dir, entry_name)
                shutil.copy2(src, dst)
                staged_paths.append(dst)
            print(f"\n  --- {archive} ({len(staged_paths)} campaigns) ---")
            safe_deploy_main([os.path.join(game, "Data", archive), *staged_paths])


def safe_deploy_main(argv: list) -> None:
    """Calls 012_safe_deploy.py's own main() with a synthetic argv,
    reusing its backup+inject+sort+verify sequence exactly instead of
    re-implementing it. In: [archive_path, file1, file2, ...]. Out: none;
    lets SystemExit propagate (safe_deploy.main() exits non-zero on any
    verification failure)."""
    old_argv = sys.argv
    try:
        sys.argv = ["012_safe_deploy.py", *argv]
        safe_deploy.main()
    finally:
        sys.argv = old_argv


def step_package_release(game: str, translated: str, release_dir: str) -> None:
    """Packages exactly what was just deployed and byte-verified in
    `game` into a ready-to-zip release folder (matching
    `006_EASY_INSTALL/gog_complete`'s existing layout: `Data/*.lod` +
    `Maps/*.h3m` + `Maps/Tutorial.tut`) - this ships what was actually
    verified in the live install, not a separately-built copy that could
    drift from it (the earlier `004_HOMM3_complete` build folder, notably,
    never contained the campaign `.h3c` files at all - only
    `006_build_mod.py`'s flat-text/image injections - so copying IT into a
    release package would have silently shipped a translation missing all
    20 campaigns). In: `game`, `translated` (for the list of which `.h3m`
    filenames are actually translated - only those are copied, the same
    "some maps have no UA counterpart" rule as `step_deploy_maps`). Out:
    none (overwrites `release_dir` in place)."""
    print(f"\n=== Packaging release at {release_dir} ===")
    os.makedirs(os.path.join(release_dir, "Data"), exist_ok=True)
    os.makedirs(os.path.join(release_dir, "Maps"), exist_ok=True)
    for name in ARCHIVES:
        shutil.copy2(os.path.join(game, "Data", name),
                     os.path.join(release_dir, "Data", name))
        print(f"  packaged Data/{name}")
    tut = os.path.join(game, "Maps", "Tutorial.tut")
    if os.path.isfile(tut):
        shutil.copy2(tut, os.path.join(release_dir, "Maps", "Tutorial.tut"))
        print("  packaged Maps/Tutorial.tut")
    count = 0
    for name in sorted(os.listdir(translated)):
        if not name.lower().endswith(".h3m"):
            continue
        src = os.path.join(game, "Maps", name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(release_dir, "Maps", name))
            count += 1
    print(f"  packaged {count} standalone map(s)")


def main() -> None:
    # line-buffer our own stdout so its prints interleave with subprocess
    # output in the order they actually happen, instead of all landing in
    # one block at process exit (subprocess.run's inherited fd writes
    # immediately regardless of the parent's buffering mode)
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[union-attr]

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--game", default="F:/Games/HoMM 3 Complete")
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--translated", default=DEFAULT_TRANSLATED)
    ap.add_argument("--out", default=DEFAULT_BUILD_OUT)
    ap.add_argument("--force", action="store_true",
                     help="passthrough to 006_build_mod.py --force")
    ap.add_argument("--skip-archives", action="store_true",
                     help="skip steps 1-2 (rebuild+copy flat archives)")
    ap.add_argument("--skip-maps", action="store_true",
                     help="skip step 3 (standalone .h3m map deploy)")
    ap.add_argument("--skip-campaigns", action="store_true",
                     help="skip step 4 (campaign .h3c deploy)")
    ap.add_argument("--package", metavar="DIR", nargs="?",
                     const=DEFAULT_RELEASE_OUT, default=None,
                     help="after deploying, also package a ready-to-zip "
                          "release folder from what was just verified in "
                          "--game (default when given with no path: "
                          "006_EASY_INSTALL/gog_complete)")
    args = ap.parse_args()

    if not args.skip_archives:
        step_rebuild_archives(args.game, args.out, args.force)
        step_copy_archives(args.game, args.out)
    if not args.skip_maps:
        step_deploy_maps(args.game, args.translated)
    if not args.skip_campaigns:
        step_deploy_campaigns(args.game, args.raw)
    if args.package:
        step_package_release(args.game, args.translated, args.package)

    print("\nDone. Full deploy verified byte-identical from the live game path.")


if __name__ == "__main__":
    main()
