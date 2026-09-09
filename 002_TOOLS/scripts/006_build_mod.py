#!/usr/bin/env python3
"""
Problem this solves: build a ready-to-copy Data/ (+Maps/) folder with the
Ukrainian translation injected into fresh copies of the game archives.

Requires matches.json (run 001_match_translated_files.py first).

For .txt files, an archive copy of a file is skipped (with a warning) if its
English line count doesn't match the translated file's line count - that
means this archive holds a different/older text structure than the one the
translation was made for, and blindly injecting would desync indexed lines.
Use --force to inject anyway.

IMPORTANT bug fixed here: `mmarch add` replaces an existing LOD entry by
deleting it from its original table slot and appending the new one at the
END of the file table, instead of overwriting in place. HoMM3's LOD
archives store entries in case-insensitive alphabetical order and the
game's own ResourceManager does a binary search assuming that order - so
any entry moved out of position becomes unfindable by the game (confirmed
bug: "ResourceManager::GetText could not find the "text" resource
"campbttn.txt"" even though the entry is still physically present and
mmarch itself can extract it fine - mmarch does a generic scan so it
doesn't care about order, the real game's binary search does). This
script now re-sorts every archive it touches via 007_fix_lod_sort_order.py as
a mandatory last step - do not skip this if hand-rolling a similar
pipeline elsewhere.

Usage:
    python 006_build_mod.py [--game "F:/Games/HoMM 3 Complete"]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h3_txt_records import record_count

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_TRANSLATED = os.path.join(REPO_ROOT, "001_ORIGINAL_HOMM3_FILES_HURTOM")
DEFAULT_OUT = os.path.join(REPO_ROOT, "004_HOMM3_complete")
ARCHIVES = ["H3bitmap.lod", "H3sprite.lod", "H3ab_bmp.lod", "H3ab_spr.lod"]
EN_ENCODING = "cp1252"
UA_ENCODING = "cp1251"


def mmarch_path():
    p = shutil.which("mmarch")
    if not p:
        sys.exit("mmarch not found on PATH. Install with: npm i -g mmarch")
    return p


def line_count_ok(mmarch, game_data, archive, fn, translated_path):
    """Safety check before injecting a .TXT translation: these flat
    resource files are RECORD-indexed (game code reads "entry N" for a
    given string), so a translated file with a different record count
    than what's actually in the target archive means that archive holds
    an older/different text layout than the one the translation was made
    against - injecting anyway would silently desync every entry after
    the mismatch.

    NOTE: "record" here is NOT the same as "physical line" - see
    h3_txt_records.py's module docstring (and H3_TXT_FORMAT_NOTES.md) for
    why a naive `.splitlines()` count is wrong for this format (a single
    record's quoted field can legitimately span several physical lines)
    and produced 16 false positives here before record_count() replaced
    it. Comparing record_count() on both sides is what the original
    engine's own record boundaries actually look like.

    In: mmarch (path), game_data (Data/ folder), archive, fn (entry name,
    e.g. 'GENRLTXT.TXT'), translated_path (the candidate replacement file).
    Out: bool - True for any non-.txt file (this check only applies to
    record-indexed text), or when the archive's current English record
    count equals the translated file's record count; False otherwise (or
    if fn can't even be found in the archive)."""
    _stem, ext = os.path.splitext(fn)
    if ext.lower() != ".txt":
        return True
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([mmarch, "extract", os.path.join(game_data, archive), tmp, fn], check=True)
        cand = None
        for f in os.listdir(tmp):
            if f.lower() == fn.lower():
                cand = os.path.join(tmp, f)
                break
        if cand is None:
            return False
        en_text = open(cand, "rb").read().decode(EN_ENCODING, errors="replace")
    ua_text = open(translated_path, "rb").read().decode(UA_ENCODING, errors="replace")
    return record_count(en_text) == record_count(ua_text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="F:/Games/HoMM 3 Complete")
    ap.add_argument("--translated", default=DEFAULT_TRANSLATED)
    ap.add_argument("--matches", default=os.path.join(SCRIPT_DIR, "matches.json"))
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--force", action="store_true", help="Inject text even when line counts mismatch")
    args = ap.parse_args()

    mmarch = mmarch_path()
    game_data = os.path.join(args.game, "Data")

    with open(args.matches, encoding="utf-8") as f:
        matches = json.load(f)

    out_data = os.path.join(args.out, "Data")
    out_maps = os.path.join(args.out, "Maps")
    os.makedirs(out_data, exist_ok=True)
    os.makedirs(out_maps, exist_ok=True)

    for archive in ARCHIVES:
        src = os.path.join(game_data, archive)
        dst = os.path.join(out_data, archive)
        print(f"Copying {archive} ...")
        shutil.copy2(src, dst)

    skipped = []
    for archive, files in matches.items():
        dst = os.path.join(out_data, archive)
        to_add = []
        for fn in files:
            translated_path = os.path.join(args.translated, fn)
            if not args.force and not line_count_ok(mmarch, game_data, archive, fn, translated_path):
                skipped.append((archive, fn))
                continue
            to_add.append(translated_path)
        if to_add:
            subprocess.run([mmarch, "add", dst, *to_add], check=True)
            print(f"  {archive}: injected {len(to_add)} file(s)")

    print("\nRe-sorting archive entry tables (mandatory - see docstring)...")
    fix_script = os.path.join(SCRIPT_DIR, "007_fix_lod_sort_order.py")
    touched = [os.path.join(out_data, a) for a in ARCHIVES]
    subprocess.run([sys.executable, fix_script, *touched], check=True)

    tut_src = os.path.join(args.translated, "Tutorial.tut")
    if os.path.isfile(tut_src):
        shutil.copy2(tut_src, os.path.join(out_maps, "Tutorial.tut"))
        print("Copied Tutorial.tut")

    print(f"\nDone. Copy the contents of {out_data} and {out_maps} over the matching")
    print(f'folders in "{args.game}" (back up originals first).')
    if skipped:
        print(f"\nSkipped {len(skipped)} text file(s) due to line-count mismatch (use --force to override):")
        for a, fn in skipped:
            print(f"  - {a}/{fn}")


if __name__ == "__main__":
    main()
