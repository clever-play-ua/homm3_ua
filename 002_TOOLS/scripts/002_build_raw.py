#!/usr/bin/env python3
"""
Problem this solves: build the human-readable 005_RAW/ folder - for every
translated text file, a JSON with {var, en, ua} per line/entry; for every
translated graphic, the original EN and translated UA file side by side.

Requires matches.json (run 001_match_translated_files.py first).

Usage:
    python 002_build_raw.py [--game "F:/Games/HoMM 3 Complete"]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h3_txt_records import split_txt_records

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_TRANSLATED = os.path.join(REPO_ROOT, "001_ORIGINAL_HOMM3_FILES_HURTOM")
DEFAULT_OUT = os.path.join(REPO_ROOT, "005_RAW")

# Unlike h3_parser/'s binary campaign/map data (which gets away with a
# single encoding for both languages - see h3m_parser.TEXT_ENCODING's
# docstring for why), the flat LOD *.TXT files genuinely are two separate
# physical files in two different encodings - this split matters here.
EN_ENCODING = "cp1252"
UA_ENCODING = "cp1251"


def mmarch_path():
    p = shutil.which("mmarch")
    if not p:
        sys.exit("mmarch not found on PATH. Install with: npm i -g mmarch")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="F:/Games/HoMM 3 Complete")
    ap.add_argument("--translated", default=DEFAULT_TRANSLATED)
    ap.add_argument("--matches", default=os.path.join(SCRIPT_DIR, "matches.json"))
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    mmarch = mmarch_path()
    game_data = os.path.join(args.game, "Data")

    with open(args.matches, encoding="utf-8") as f:
        matches = json.load(f)

    imgs_dir = os.path.join(args.out, "imgs")
    issues = []

    with tempfile.TemporaryDirectory() as tmp:
        for archive, files in matches.items():
            if not files:
                continue
            en_dir = os.path.join(tmp, archive)
            os.makedirs(en_dir, exist_ok=True)
            subprocess.run([mmarch, "extract", os.path.join(game_data, archive), en_dir, *files], check=True)

            for fn in files:
                stem, ext = os.path.splitext(fn)
                ext = ext.lower()
                ua_path = os.path.join(args.translated, fn)

                en_path = None
                for cand in os.listdir(en_dir):
                    if cand.lower() == fn.lower():
                        en_path = os.path.join(en_dir, cand)
                        break
                    cand_stem, cand_ext = os.path.splitext(cand)
                    if (cand_stem.lower() == stem.lower() and ext in (".bmp", ".pcx")
                            and cand_ext.lower() in (".bmp", ".pcx")):
                        en_path = os.path.join(en_dir, cand)
                        break
                if en_path is None:
                    issues.append(f"EN file missing after extract: {archive}/{fn}")
                    continue

                if ext == ".txt":
                    en_text = open(en_path, "rb").read().decode(EN_ENCODING, errors="replace")
                    ua_text = open(ua_path, "rb").read().decode(UA_ENCODING, errors="replace")
                    # RECORD count, not raw physical line count - a single
                    # record's quoted field can legitimately span several
                    # physical lines (see h3_txt_records.py's module
                    # docstring / H3_TXT_FORMAT_NOTES.md). Comparing raw
                    # `.splitlines()` here used to produce false "mismatch"
                    # warnings on every file that uses this multi-line
                    # quoting, which is common in this format.
                    en_lines = split_txt_records(en_text)
                    ua_lines = split_txt_records(ua_text)
                    if len(en_lines) != len(ua_lines):
                        issues.append(f"Record count mismatch {archive}/{fn}: en={len(en_lines)} ua={len(ua_lines)}")

                    n = max(len(en_lines), len(ua_lines))
                    records = []
                    for i in range(n):
                        en_line = en_lines[i] if i < len(en_lines) else None
                        ua_line = ua_lines[i] if i < len(ua_lines) else None
                        var = str(i + 1)
                        if en_line and "\t" in en_line:
                            key = en_line.split("\t", 1)[0].strip()
                            if key:
                                var = key
                        # prefix with the source file's stem so every var stays
                        # globally unique if all JSONs are ever merged into one
                        var = f"{stem.upper()}_{var}"
                        records.append({"var": var, "en": en_line, "ua": ua_line})

                    out_dir = os.path.join(args.out, archive)
                    os.makedirs(out_dir, exist_ok=True)
                    with open(os.path.join(out_dir, stem.upper() + ".json"), "w", encoding="utf-8") as f:
                        json.dump(records, f, ensure_ascii=False, indent=2)
                else:
                    en_out = os.path.join(imgs_dir, archive, "en")
                    ua_out = os.path.join(imgs_dir, archive, "ua")
                    os.makedirs(en_out, exist_ok=True)
                    os.makedirs(ua_out, exist_ok=True)
                    shutil.copy2(en_path, os.path.join(en_out, os.path.basename(en_path)))
                    shutil.copy2(ua_path, os.path.join(ua_out, fn))

    print(f"Done. Wrote raw text/images under {args.out}")
    if issues:
        print(f"\n{len(issues)} issue(s):")
        for i in issues:
            print("  -", i)


if __name__ == "__main__":
    main()
