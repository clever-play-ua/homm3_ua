#!/usr/bin/env python3
"""
Problem this solves: HoMM3 campaign (.h3c) files are gzip + a large, deeply
conditional binary map format - there's no simple flat text table like the
LOD *.TXT files. Fully parsing that format field-by-field is a much bigger
project, so this instead heuristically scans the decompressed bytes for
Pascal-style strings (uint32 length + text) and pairs up the EN/UA
occurrences with a banded sequence-alignment DP (cost = normalized string
length difference) - translated text is a different length than the
original, but the two streams drift only a little relative to each other, so
a near-diagonal alignment finds the true 1:1 correspondence and cleanly
isolates the handful of entries that don't have a confident match.

This is NOT a guaranteed 1:1 structural parse. Entries with no confident
match on the other side are still emitted with a null partner and
"aligned": false - those want a human check (could be a genuinely unmatched
string, or two nearly-identical-length candidates the DP guessed wrong on).

Usage:
    python 003_extract_campaigns.py [--game "F:/Games/HoMM 3 Complete"]

Output: <repo>/005_RAW/<NNN>_<CampaignName>/<Stem>.h3c (EN) + texts.json
"""
import argparse
import gzip
import json
import os
import shutil
import struct
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_TRANSLATED = os.path.join(REPO_ROOT, "001_ORIGINAL_HOMM3_FILES_HURTOM")
DEFAULT_OUT = os.path.join(REPO_ROOT, "005_RAW")

# stem -> (display name, order). Display name/order verified by extracting each
# campaign's own embedded name string and cross-checking the RoE/SoD groups
# against CAMPTEXT.TXT's "Campaign Map Names" list (which gives 1-7 and 14-20
# but not the AB group - the AB block there turned out to be ab.h3c's own
# scenario/region names, not campaign titles).
CAMPAIGNS = [
    ("GOOD1", "Long Live the Queen"),
    ("GOOD2", "Liberation"),
    ("GOOD3", "Song for the Father"),
    ("EVIL1", "Dungeons and Devils"),
    ("EVIL2", "Long Live the King"),
    ("NEUTRAL1", "Spoils of War"),
    ("SECRET1", "Seeds of Discontent"),
    ("AB", "Armageddons Blade"),
    ("BLOOD", "Dragons Blood"),
    ("SLAYER", "Dragon Slayer"),
    ("FESTIVAL", "Festival of Life"),
    ("FOOL", "Foolhardy Waywardness"),
    ("FIRE", "Playing with Fire"),
    ("CRAG", "Hack and Slash"),
    ("YOG", "Birth of a Barbarian"),
    ("GEM", "New Beginning"),
    ("GELU", "Elixir of Life"),
    ("SANDRO", "Rise of the Necromancer"),
    ("FINAL", "Unholy Alliance"),
    ("SECRET", "Specter of Power"),
]

CYR_EXTRA = {0xA8, 0xB8, 0xAA, 0xBA, 0xAF, 0xBF, 0xB2, 0xB3}  # UA/RU extras in cp1251


def mmarch_path():
    p = shutil.which("mmarch")
    if not p:
        sys.exit("mmarch not found on PATH. Install with: npm i -g mmarch")
    return p


def is_letter(b):
    """In: b (one byte, 0-255). Out: bool - True for ASCII letters, Latin-1
    high-byte letters (covers cp1252 accented chars), or a cp1251 Cyrillic
    extra byte (see CYR_EXTRA)."""
    return (0x41 <= b <= 0x5A or 0x61 <= b <= 0x7A or 0xC0 <= b <= 0xFF or b in CYR_EXTRA)


def is_textish(b):
    """In: b. Out: bool - True for tab/LF/CR, printable ASCII, or
    is_letter(b) - the full "could plausibly be part of human text" set."""
    return b in (9, 10, 13) or 0x20 <= b <= 0x7E or is_letter(b)


def looks_like_text(chunk):
    """Heuristic filter deciding whether a candidate length-prefixed byte
    span is real text or just numeric/binary data that happened to look
    like a valid length prefix. In: chunk (candidate bytes). Out: bool -
    True if empty, or every byte is_textish AND (for very short chunks)
    all letters/hyphens, or (for longer ones) at least 55% letters."""
    if len(chunk) == 0:
        return True
    if not all(is_textish(b) for b in chunk):
        return False
    if len(chunk) <= 3:
        return all(is_letter(b) or b == 0x2D for b in chunk)
    return sum(1 for b in chunk if is_letter(b)) / len(chunk) >= 0.55


def scan_strings(data, max_len=4000):
    """Slides a 1-byte-at-a-time window over data looking for
    `uint32 length + bytes` spans that pass looks_like_text - the
    heuristic heart of this script (no real structural parsing, just
    "does this length prefix make sense and does the content look like
    text"). In: data (decompressed .h3c bytes), max_len (reject candidate
    lengths above this - keeps runtime sane and rejects obviously-wrong
    prefixes). Out: list of raw byte chunks found, in file order (advances
    byte-by-byte past non-matches, jumps past a match's full length when
    one is found - so genuine adjacent strings are still each found once)."""
    i, n = 0, len(data)
    out = []
    while i + 4 <= n:
        length = struct.unpack_from("<I", data, i)[0]
        if length <= max_len and i + 4 + length <= n:
            chunk = data[i + 4:i + 4 + length]
            if looks_like_text(chunk):
                out.append(chunk)
                i += 4 + length
                continue
        i += 1
    return out


def decode_best(b, encodings=("cp1252", "cp1251")):
    """In: b (raw bytes), encodings (tried in order). Out: str - the first
    encoding that decodes without error, or latin1 (which never raises) as
    a last resort."""
    for enc in encodings:
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("latin1")


def banded_align(en_lens, ua_lens, band=250, gap_cost=0.5):
    """Monotonic alignment between two sequences using normalized length
    difference as substitution cost, restricted to a band around the diagonal
    (translations drift only a little, so this is both accurate and fast -
    O(n*band) instead of O(n*m) full edit-distance DP).
    In: en_lens, ua_lens (parallel-ish lists of string lengths, NOT the
    strings themselves - see align() for the caller that maps indices back
    to actual strings), band (how far off-diagonal to search), gap_cost
    (cost of leaving one side's entry unmatched). Out: list of (i, j) index
    pairs in order (i or j is None for an unmatched entry on the other side)."""
    n, m = len(en_lens), len(ua_lens)
    INF = float("inf")
    scale = (m / n) if n else 1.0

    def mcost(i, j):
        a, b = en_lens[i], ua_lens[j]
        return abs(a - b) / max(a, b, 1)

    def jrange(i):
        center = int(i * scale)
        return max(0, center - band), min(m, center + band)

    prev_row = {0: (0.0, None)}
    rows = [prev_row]
    for i in range(1, n + 1):
        lo, hi = jrange(i)
        row = {}
        for j in range(lo, hi + 1):
            best = (INF, None)
            if (j - 1) in prev_row:
                c = prev_row[j - 1][0] + (mcost(i - 1, j - 1) if j > 0 else gap_cost)
                if c < best[0]:
                    best = (c, ("d", i - 1, j - 1))
            if j in prev_row:
                c = prev_row[j][0] + gap_cost
                if c < best[0]:
                    best = (c, ("u", i - 1, j))
            if (j - 1) in row:
                c = row[j - 1][0] + gap_cost
                if c < best[0]:
                    best = (c, ("l", i, j - 1))
            if best[0] < INF:
                row[j] = best
        prev_row = row
        rows.append(row)

    if not rows[n]:
        return []
    end_j = min(rows[n].keys(), key=lambda j: rows[n][j][0])
    pairs = []
    i, j = n, end_j
    while i > 0 or j > 0:
        if i == 0:
            pairs.append((None, j - 1)); j -= 1; continue
        if j == 0:
            pairs.append((i - 1, None)); i -= 1; continue
        _, back = rows[i][j]
        kind = back[0]
        if kind == "d":
            pairs.append((i - 1, j - 1)); i, j = i - 1, j - 1
        elif kind == "u":
            pairs.append((i - 1, None)); i -= 1
        else:
            pairs.append((None, j - 1)); j -= 1
    pairs.reverse()
    return pairs


def align(en_strings, ua_strings):
    """Pair EN/UA extracted strings up using length-based banded alignment.
    Unmatched entries (present in one side only) get a null partner and
    aligned=False, so they're still visible for a human to check by hand.
    In: en_strings, ua_strings (raw byte chunks from scan_strings(), run
    separately over the EN and UA files). Out: list of `{en, ua, aligned}`
    dicts in file order (en/ua already decoded via decode_best; aligned is
    False when either side is None - no confident match found)."""
    pairs = banded_align([len(s) for s in en_strings], [len(s) for s in ua_strings])
    records = []
    for i, j in pairs:
        en_s = en_strings[i] if i is not None else None
        ua_s = ua_strings[j] if j is not None else None
        records.append({
            "en": decode_best(en_s, ("cp1252",)) if en_s is not None else None,
            "ua": decode_best(ua_s, ("cp1251",)) if ua_s is not None else None,
            "aligned": en_s is not None and ua_s is not None,
        })
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="F:/Games/HoMM 3 Complete")
    ap.add_argument("--translated", default=DEFAULT_TRANSLATED)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    mmarch = mmarch_path()
    game_data = os.path.join(args.game, "Data")
    archives = ["H3bitmap.lod", "H3ab_bmp.lod"]

    archive_listings = {}
    for a in archives:
        out = subprocess.run([mmarch, "list", os.path.join(game_data, a)], check=True, capture_output=True, text=True)
        archive_listings[a] = {line.strip().lower(): line.strip() for line in out.stdout.splitlines() if line.strip()}

    total_mismatched_segments = 0

    for order, (stem, name) in enumerate(CAMPAIGNS, start=1):
        want = (stem + ".h3c").lower()
        archive, real_name = None, None
        for a in archives:
            if want in archive_listings[a]:
                archive, real_name = a, archive_listings[a][want]
                break
        if archive is None:
            print(f"SKIP {stem}: not found in any archive")
            continue

        folder_name = f"{order:03d}_{name.replace(' ', '_')}"
        out_dir = os.path.join(args.out, folder_name)
        os.makedirs(out_dir, exist_ok=True)

        # extract EN .h3c straight into the campaign folder
        subprocess.run([mmarch, "extract", os.path.join(game_data, archive), out_dir, real_name], check=True)
        en_path = os.path.join(out_dir, real_name)

        ua_path = os.path.join(args.translated, stem + ".H3C")
        if not os.path.isfile(ua_path):
            ua_path = os.path.join(args.translated, stem + ".h3c")

        with open(en_path, "rb") as f:
            en_data = gzip.decompress(f.read())
        with open(ua_path, "rb") as f:
            ua_data = gzip.decompress(f.read())

        en_strings = [s for s in scan_strings(en_data) if len(s) >= 2]
        ua_strings = [s for s in scan_strings(ua_data) if len(s) >= 2]

        records = align(en_strings, ua_strings)
        mismatched = sum(1 for r in records if not r["aligned"])
        total_mismatched_segments += mismatched

        out_records = []
        for i, r in enumerate(records, start=1):
            out_records.append({
                "var": f"{stem}_{i}",
                "en": r["en"],
                "ua": r["ua"],
                "aligned": r["aligned"],
            })

        with open(os.path.join(out_dir, "texts.json"), "w", encoding="utf-8") as f:
            json.dump(out_records, f, ensure_ascii=False, indent=2)

        flag = f"  ({mismatched} unaligned entries - needs a human check)" if mismatched else ""
        print(f"{folder_name}: EN={len(en_strings)} UA={len(ua_strings)} entries={len(out_records)}{flag}")

    print(f"\nTotal unaligned entries across all campaigns: {total_mismatched_segments}")


if __name__ == "__main__":
    main()
