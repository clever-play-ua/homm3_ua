#!/usr/bin/env python3
"""
Problem this solves: figure out WHICH game archive(s) (H3bitmap.lod,
H3sprite.lod, H3ab_bmp.lod, H3ab_spr.lod) each file in
001_ORIGINAL_HOMM3_FILES_HURTOM belongs to, by name-matching against the
real archive contents (bmp/pcx names are treated as interchangeable).

Usage:
    python 001_match_translated_files.py [--game "F:/Games/HoMM 3 Complete"]

Output:
    matches.json next to this script: {archive_name: [file_name, ...]}
    Also prints any file that could not be matched anywhere.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_TRANSLATED = os.path.join(REPO_ROOT, "001_ORIGINAL_HOMM3_FILES_HURTOM")
ARCHIVES = ["H3bitmap.lod", "H3sprite.lod", "H3ab_bmp.lod", "H3ab_spr.lod"]
SKIP = {"pack.ini", "tutorial.tut"}


def mmarch_path():
    p = shutil.which("mmarch")
    if not p:
        sys.exit("mmarch not found on PATH. Install with: npm i -g mmarch")
    return p


def list_archive(mmarch, game_data_dir, archive):
    """In: mmarch (its executable path), game_data_dir, archive (filename,
    e.g. 'H3bitmap.lod'). Out: list of entry names in that archive (via
    `mmarch list`), one per line, blanks stripped."""
    out = subprocess.run([mmarch, "list", os.path.join(game_data_dir, archive)],
                          check=True, capture_output=True, text=True)
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def name_variants(name):
    """HoMM3 archives sometimes store the "same" image under different
    extensions across the EN and Hurtom-translated versions (.bmp vs
    .pcx) - this generates both so a match isn't missed just because of
    that. In: name (a filename from 001_ORIGINAL_HOMM3_FILES_HURTOM). Out:
    a set of lowercased name variants to check against archive contents
    (just {name} unchanged for any extension other than .bmp/.pcx)."""
    stem, ext = os.path.splitext(name)
    ext = ext.lower()
    variants = {name.lower()}
    if ext == ".bmp":
        variants.add((stem + ".pcx").lower())
    if ext == ".pcx":
        variants.add((stem + ".bmp").lower())
    return variants


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="F:/Games/HoMM 3 Complete", help="Path to the game install folder")
    ap.add_argument("--translated", default=DEFAULT_TRANSLATED, help="Folder with translated loose files")
    args = ap.parse_args()

    mmarch = mmarch_path()
    game_data = os.path.join(args.game, "Data")

    archive_entries = {a: list_archive(mmarch, game_data, a) for a in ARCHIVES}

    matches = {a: [] for a in ARCHIVES}
    unmatched = []

    for fn in sorted(os.listdir(args.translated)):
        full = os.path.join(args.translated, fn)
        if not os.path.isfile(full):
            continue
        lower = fn.lower()
        if lower.endswith((".h3m", ".h3c")) or lower in SKIP:
            continue
        variants = name_variants(fn)
        found_in = [a for a in ARCHIVES
                    if variants & {e.lower() for e in archive_entries[a]}]
        if not found_in:
            unmatched.append(fn)
        else:
            for a in found_in:
                matches[a].append(fn)

    out_path = os.path.join(SCRIPT_DIR, "matches.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    print(f"Wrote {out_path}")
    for a in ARCHIVES:
        print(f"  {a}: {len(matches[a])} files")
    if unmatched:
        print(f"\nUNMATCHED ({len(unmatched)}) - not found in any archive:")
        for u in unmatched:
            print("  ", u)


if __name__ == "__main__":
    main()
