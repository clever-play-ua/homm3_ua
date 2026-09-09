#!/usr/bin/env python3
"""
Problem this solves: every real deploy this project has done to the live
game this session followed the same 4 manual steps - back up the archive
(if not already backed up), `mmarch add` the new file(s) in, re-sort a LOD
archive's entry table (007_fix_lod_sort_order.py - mandatory, see its own
docstring), then extract the injected file(s) back out and byte-compare
against the source to actually confirm the injection took. Doing this by
hand, every time, is exactly the kind of repetitive manual step a person
eventually skips once under time pressure - this happened for real once
this session (a 688MB VIDEO.VID got modified without a backup being taken
first; caught and fixed by luck, not process). This script makes the whole
sequence one command and impossible to accidentally shorten.

What "safe" means here, precisely:
  1. If <archive>'s backup (under UA_Patch_DEPLOY_BACKUPS/, next to the
     archive's own game install, mirroring its Data/ subpath) doesn't
     exist yet, copy the CURRENT (pre-injection) archive there first. If a
     backup already exists, it is NEVER overwritten - it stays whatever
     the archive looked like the first time this script ever touched it.
     (This is deliberately a different, dedicated backup folder from this
     project's older ad-hoc `UA_Patch_Backup` / `*_BACKUP_ORIGINAL.*`
     copies made by hand earlier in the project's history - this script
     never assumes those exist or touches them, to avoid silently
     clobbering a hand-made backup with a different retention intent.)
  2. `mmarch add` every given file into the archive.
  3. If the archive's extension is `.lod`, run 007_fix_lod_sort_order.py
     on it (mandatory - see that script's docstring for why; harmless/
     idempotent to run on `.vid` archives too, but they don't need it and
     this script skips them to avoid a confusing "not a LOD file" exit).
  4. Extract every injected file back out to a scratch temp dir and
     byte-compare it against the source file that was injected. Reports
     PASS/FAIL per file; exits non-zero if anything didn't verify.

Usage:
    python 012_safe_deploy.py "F:/Games/HoMM 3 Complete/Data/H3ab_bmp.lod" file1.h3c file2.DEF ...
    python 012_safe_deploy.py "F:/Games/HoMM 3 Complete/Data/VIDEO.VID" H3INTRO.BIK --no-sort

Requires: mmarch (npm i -g mmarch).
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR_NAME = "UA_Patch_DEPLOY_BACKUPS"


def mmarch_path() -> str:
    """Out: str - path to the mmarch executable, or exits with an install
    hint if it's not on PATH."""
    p = shutil.which("mmarch")
    if not p:
        sys.exit("mmarch not found on PATH. Install with: npm i -g mmarch")
    return p


def backup_path_for(archive_path: str) -> str:
    """In: archive_path (e.g. 'F:/Games/HoMM 3 Complete/Data/H3ab_bmp.lod').
    Out: the dedicated backup path for it, e.g.
    'F:/Games/HoMM 3 Complete/UA_Patch_DEPLOY_BACKUPS/Data/H3ab_bmp.lod' -
    mirrors the archive's own path structure under the game install root,
    one level up from wherever the archive itself sits, so multiple
    archives (Data/*.lod, Data/VIDEO.VID) never collide."""
    game_dir = os.path.dirname(os.path.dirname(os.path.abspath(archive_path)))
    rel = os.path.relpath(os.path.abspath(archive_path), game_dir)
    return os.path.join(game_dir, BACKUP_DIR_NAME, rel)


def ensure_backup(archive_path: str) -> str:
    """In: archive_path. Out: the backup path (whether it already existed
    or was just created) - creates one from the CURRENT file contents only
    if none exists yet; never overwrites an existing backup."""
    dst = backup_path_for(archive_path)
    if os.path.isfile(dst):
        print(f"  backup already exists: {dst} (not touching it)")
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(archive_path, dst)
    print(f"  created backup: {dst}")
    return dst


def main() -> None:
    """CLI entry point - see module docstring's Usage line. In: sys.argv
    (archive path, one or more files to inject, --no-sort to skip
    007_fix_lod_sort_order.py even for a .lod archive). Out: None; exits
    with status 1 if any injected file fails its post-injection byte
    comparison, so this is safe to use as a CI/script gate, not just an
    interactively-read report."""
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", help="Path to the .lod/.vid archive to modify, e.g. Data/H3ab_bmp.lod")
    ap.add_argument("files", nargs="+", help="File(s) to inject (mmarch add)")
    ap.add_argument("--no-sort", action="store_true",
                     help="Skip 007_fix_lod_sort_order.py even for a .lod archive (rarely needed)")
    args = ap.parse_args()

    archive_path = os.path.abspath(args.archive)
    if not os.path.isfile(archive_path):
        sys.exit(f"archive not found: {archive_path}")

    mmarch = mmarch_path()

    print(f"=== {os.path.basename(archive_path)} ===")
    ensure_backup(archive_path)

    print(f"  injecting {len(args.files)} file(s)...")
    subprocess.run([mmarch, "add", archive_path, *args.files], check=True)

    is_lod = archive_path.lower().endswith(".lod")
    if is_lod and not args.no_sort:
        fix_script = os.path.join(SCRIPT_DIR, "007_fix_lod_sort_order.py")
        print("  re-sorting LOD entry table (mandatory, see 007's docstring)...")
        subprocess.run([sys.executable, fix_script, archive_path], check=True)
    elif is_lod:
        print("  WARNING: --no-sort passed for a .lod archive - entries may now be unfindable by the game!")

    print("  verifying...")
    entry_names = [os.path.basename(f) for f in args.files]
    all_ok = True
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([mmarch, "extract", archive_path, tmp, *entry_names], check=True)
        for src, name in zip(args.files, entry_names, strict=True):
            extracted = None
            for cand in os.listdir(tmp):
                if cand.lower() == name.lower():
                    extracted = os.path.join(tmp, cand)
                    break
            if extracted is None:
                print(f"    FAIL {name}: not found in archive after injection")
                all_ok = False
                continue
            ok = filecmp.cmp(src, extracted, shallow=False)
            print(f"    {'OK  ' if ok else 'FAIL'} {name}")
            all_ok = all_ok and ok

    if not all_ok:
        sys.exit(1)
    print("All files verified byte-identical after injection.")


if __name__ == "__main__":
    main()
