#!/usr/bin/env python3
"""
Problem this solves: mmarch's `add` command replaces a LOD entry by
removing it from its original table slot and appending the new entry at
the END of the file table, instead of overwriting it in place. HoMM3's own
LOD archives store entries in case-insensitive alphabetical order and the
game's ResourceManager does a binary search over that order to find files
- so any entry moved out of its correct alphabetical position becomes
unfindable by the game (confirmed bug: "ResourceManager::GetText could
not find the "text" resource "campbttn.txt"" even though the entry is
still physically present and even mmarch itself can extract it fine -
mmarch does a generic/linear scan so it doesn't care about order, but the
real game's binary search does).

Fix: re-sort the LOD file's entry table by name (case-insensitive) after
running 006_build_mod.py / mmarch add. This only reorders the fixed-size table
entries (16-byte name + offset + full_size + type + comp_size, 32 bytes
each) - the actual file data blobs referenced by offset don't move at all,
so this is a cheap, safe, purely-metadata fix.

LOD header format (reverse-engineered and confirmed against real game
files this session - not officially documented anywhere found):
  offset 0: 4 bytes magic "LOD\0"
  offset 4: 4 bytes version (u32, e.g. 200)
  offset 8: 4 bytes entry count (u32)
  offset 12-91: reserved/padding (80 bytes)
  offset 92: entry table, 32 bytes per entry:
    0-15:  filename, null-padded
    16-19: file data offset (u32)
    20-23: full/uncompressed size (u32)
    24-27: type (u32) - NOT just a compression flag, see below
    28-31: compressed size (u32)

Usage:
    python 007_fix_lod_sort_order.py path/to/H3bitmap.lod [more.lod ...]
Modifies the file(s) in place. Always run this as the LAST step after
006_build_mod.py, on every archive it touches, before distributing/installing.
"""
import struct
import sys

HEADER_SIZE = 92
ENTRY_SIZE = 32
# LOD entry names are DOS-style 8.3 filenames - always plain ASCII in
# practice, so any single-byte codepage decodes them identically; named
# for clarity, not because a different encoding has ever actually mattered
# here (unlike real translated TEXT content elsewhere in this project).
FILENAME_ENCODING = "cp1252"


def fix_one(path):
    """In: path (a .LOD file to fix IN PLACE). Out: None (rewrites the
    file's 32-byte-per-entry table in case-insensitive alphabetical order
    if it wasn't already; leaves every entry's actual data bytes at their
    existing offsets untouched - purely a metadata reorder). No-ops with a
    message if the table was already sorted (idempotent - safe to call on
    an archive that's already fine)."""
    with open(path, "rb") as f:
        data = bytearray(f.read())

    magic = bytes(data[0:4])
    if magic != b"LOD\x00":
        sys.exit(f"{path}: not a LOD file (magic={magic})")

    count = struct.unpack_from("<I", data, 8)[0]
    entries = []
    for i in range(count):
        off = HEADER_SIZE + i * ENTRY_SIZE
        raw = bytes(data[off:off + ENTRY_SIZE])
        name = raw[0:16].split(b"\x00")[0].decode(FILENAME_ENCODING, errors="replace")
        entries.append((name, raw))

    already_sorted = all(
        entries[i][0].lower() <= entries[i + 1][0].lower()
        for i in range(len(entries) - 1)
    )
    if already_sorted:
        print(f"{path}: already sorted, nothing to do")
        return

    entries.sort(key=lambda e: e[0].lower())

    for i, (_name, raw) in enumerate(entries):
        off = HEADER_SIZE + i * ENTRY_SIZE
        data[off:off + ENTRY_SIZE] = raw

    with open(path, "wb") as f:
        f.write(data)
    print(f"{path}: re-sorted {count} entries")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        fix_one(path)


if __name__ == "__main__":
    main()
