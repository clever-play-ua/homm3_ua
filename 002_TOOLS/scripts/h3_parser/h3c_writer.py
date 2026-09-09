#!/usr/bin/env python3
"""
Problem this solves: h3c_parser.py can READ the .h3c wrapper's text fields
(campaign name/desc, per-scenario prolog/epilog) but there was no way to
EDIT them and write a new .h3c back out. This gives that read-edit-write
loop the same shape as the rest of the project's translation pipeline
(build_raw.py/build_mod.py's {var, en, ua} JSON files).

CRITICAL CORRECTED UNDERSTANDING (h3c_parser.py's docstring is now
outdated on this point - fix it too if touching this area again): a .h3c
file is NOT one big gzip stream. It is N+1 SEPARATE, independently
gzip-compressed streams concatenated back to back in the raw file: member
0 is the "header block" (campaign name/desc + every scenario's
filename/h3m_size/prolog/epilog, back to back, nothing else), and members
1..N are each one scenario's embedded .h3m map, in scenario order. Proof:
searching the raw file for gzip magic (1f 8b 08) finds exactly N+1 hits,
and `h3m_size` in the header turns out to be EXACTLY the compressed byte
length of that scenario's own member (verified empirically: h3m_size=26198
for scenario 0 of Good1.h3c, and its raw gzip member is exactly 26198
bytes) - not the decompressed map size (which is much larger and was
previously, wrongly, assumed to be what h3m_size almost-but-not-quite
described).

This matters enormously for WRITING: naively decompressing the whole file
as one stream (works fine - Python's gzip.decompress transparently
concatenates multi-member content) and recompressing the result as one
new single-member stream (the previous, WRONG version of this script did
exactly this) produces a file whose decompressed bytes can be
byte-identical to the original and which still passes our own from-scratch
parser's validation - but breaks the real game, because the real game's
reader (confirmed against VCMI's own from-scratch engine reimplementation,
lib/campaign/CampaignHandler.cpp) reads the file as a sequence of
independent gzip members via a block-based compressed stream reader, not
as one flat decompressed blob. Symptom when this is done wrong: the
campaign name/description (read while still inside member 0) can appear
translated just fine, but EVERY scenario's own name/description shows a
generic "old map format" fallback and the game crashes on actually
starting a scenario - because the reader can no longer find a valid
second gzip member where it expects one.

The fix: only ever re-compress the HEADER block (member 0) on its own as
a complete, independent gzip stream. Every map member (1..N) is copied
through as raw, already-compressed bytes, completely unchanged - never
decompressed, never re-encoded. This is also why editing scenario map
content is a separate, much bigger job (would need decompressing that
one member, editing, and re-compressing IT as its own independent
stream) - not attempted here, only the header block's text fields.

Scope: this only covers the .h3c HEADER block's own text fields (campaign
name/description, each scenario's prolog/epilog). It does NOT touch text
embedded inside the scenarios' own .h3m map data (hero bios, guard/seer
hut messages, custom object names like town names) - h3m_parser.py can
find these for reading but there's no writer for them yet.

Header block internal layout (purely sequential, no offsets to fix up -
replacing a pstr with a different-length string needs no adjustment to
anything else, since every field is read immediately after the previous
one ends and the member's own gzip framing supplies its own natural end,
with no length prefix at the container level to keep in sync):
    uint32 format
    uint8  campaign_map_id
    pstr   campaign_name
    pstr   campaign_desc
    uint8  fixed_difficulty
    uint8  music
    repeated once per scenario, continuing until the header block's own
    bytes are exhausted (a scenario count is never stored - VCMI's reader
    doesn't need one either, since each scenario's data implicitly ends
    where the next one's or the block's own end is):
        pstr    scenario_filename
        uint32  h3m_size            (compressed byte length of this
                                      scenario's OWN gzip member later in
                                      the file - keep verbatim, unaffected
                                      by header-only edits)
        3 bytes unknown/flags
        pstr    prolog_text
        3 bytes unknown/flags
        pstr    epilog_text
        ??? bytes "starting bonus" block (heroKeeps flags + bonus
            choices) - length not understood, but no longer needs to be:
            since we know the header block's total decompressed length
            from its own gzip stream, whatever's left over after the
            last scenario's epilog (down to the last byte of the
            decompressed header) IS this trailing data, definitionally,
            with no marker-search heuristic required.

Usage:
    python h3c_writer.py extract Good1.h3c wrapper_texts.json \
        --ua-source ../../001_ORIGINAL_HOMM3_FILES_HURTOM/GOOD1.H3C
    python h3c_writer.py rebuild Good1.h3c wrapper_texts.json Good1_ua.h3c
"""
import gzip
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h3c_parser import find_next_h3m_name
from h3m_parser import (
    TEXT_ENCODING,
    FixedSegment,
    H3mSizeSegment,
    HeaderStructureError,
    ImplausibleLengthError,
    PstrSegment,
    Segment,
    rebuild_from_segments,
)

GZIP_MAGIC = re.compile(rb'\x1f\x8b\x08')

# Every scenario's prolog/epilog (and, for the last scenario, the closing
# campaign_epilogue) is preceded by this many unknown/flag bytes - see
# read_header_segments() for the one place this ISN'T a bare constant
# (the pre-prolog gap also embeds a scenario-count-dependent preconditions
# bitmask - found via the FINAL.h3c bug, see H3M_H3C_FORMAT_NOTES.md).
PRE_PSTR_UNKNOWN_BYTES = 3


def compress_h3_gzip(data: bytes) -> bytes:
    """gzip-compress exactly the way the real game's files (and Hurtom's
    translated ones) are compressed - CRITICAL, do not replace with a bare
    gzip.compress(data) call. Found by comparing gzip header bytes between
    a working file and this project's own (broken) output: Python's
    gzip.compress() defaults (compresslevel=9, current mtime, OS byte 0xFF
    "unknown") produce a header like `1f8b08009e2e9d6a02ff`, while every
    real HoMM3 .h3c/.h3m file - both the original English ones AND
    Hurtom's own working Ukrainian translation - uses
    `1f8b080000000000000b` (mtime=0, XFL=0 i.e. not "max compression",
    OS byte 0x0b = NTFS). The game's own gzip/zlib decoder is old and
    evidently doesn't tolerate the mismatch: a member recompressed with
    Python's defaults reliably shows as "old map format" / fails to load
    in-game, even though it decompresses to byte-identical content and
    passes every check this project's own parser can run (confirmed by
    extensive testing this session - don't waste time re-deriving this,
    just always compress through this function). Fix: compresslevel=6
    (matches XFL=0) + mtime=0, then patch the OS byte (offset 9) since
    Python's gzip module doesn't expose it directly.
    """
    out = bytearray(gzip.compress(data, compresslevel=6, mtime=0))
    out[9] = 0x0B  # OS byte: NTFS, matching every real HoMM3 file
    return bytes(out)


def find_gzip_member_bounds(raw: bytes) -> list[tuple[int, int]]:
    """Returns a list of (start, end) compressed byte ranges, one per
    gzip member, covering the whole file. Relies on gzip magic bytes only
    appearing at real member starts (true for these files in practice -
    verified against h3m_size cross-check in split_h3c below)."""
    starts = [m.start() for m in GZIP_MAGIC.finditer(raw)]
    if not starts or starts[0] != 0:
        raise HeaderStructureError("file doesn't start with a gzip member")
    bounds = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(raw)
        bounds.append((s, e))
    return bounds


def split_h3c(raw: bytes) -> tuple[bytes, list[bytes]]:
    """Returns (header_bytes_decompressed, scenario_member_raw_list) where
    scenario_member_raw_list[i] is scenario i's own gzip member, exactly
    as it appears in the file (still compressed, untouched bytes)."""
    bounds = find_gzip_member_bounds(raw)
    header_start, header_end = bounds[0]
    header = gzip.decompress(raw[header_start:header_end])
    scenario_members = [raw[s:e] for s, e in bounds[1:]]
    return header, scenario_members


def read_header_segments(header: bytes, scenario_count: int) -> list[Segment]:
    """Walk the decompressed header block, recording Segment spans -
    FixedSegment (copy verbatim), PstrSegment (replaceable by field_name),
    or H3mSizeSegment (see patch_h3m_sizes()) - see h3m_parser.py for the
    Segment type definitions (these are the same types R(track=True)
    produces for map bodies; this function is this module's equivalent for
    the .h3c wrapper header, hand-walked since there's no reader class
    reused here - the header's field sequence is short and campaign-
    specific enough that it hasn't needed one).

    scenario_count MUST be passed in (= number of map members the file
    has, i.e. len(scenario_members) from split_h3c) - it is NOT
    determinable from the header block's own length alone. Each
    scenario's fixed prolog/epilog fields are followed by an opaque
    "starting bonus" block of undetermined length (heroKeeps flags +
    bonus choices) BEFORE the next scenario's filename pstr - this still
    needs a marker search (find_next_h3m_name) to skip over, same as the
    old (pre-multi-gzip-member-fix) parser did. What's new/simpler here:
    for the LAST scenario, there's no "next filename" to search for -
    everything remaining down to the header's own end (known exactly,
    since it's a complete, independent gzip member) is that scenario's
    trailing bonus block, taken as-is with no search needed.
    """
    segments: list[Segment] = []
    p = 0
    n = len(header)

    def fixed(new_p: int) -> None:
        nonlocal p
        if new_p > p:
            segments.append(FixedSegment('fixed', p, new_p))
        p = new_p

    def pstr(field_name: str) -> None:
        nonlocal p
        length_start = p
        length = struct.unpack_from('<I', header, p)[0]
        if length > 200000:
            raise ImplausibleLengthError(f"implausible string length {length} at {p}")
        end = p + 4 + length
        segments.append(PstrSegment('pstr', field_name, length_start, end))
        p = end

    fixed(p + 4)          # format
    fixed(p + 1)          # campaign_map_id
    pstr('campaign_name')
    pstr('campaign_desc')
    fixed(p + 1)          # fixed_difficulty
    fixed(p + 1)          # music

    for scenario_idx in range(scenario_count):
        pstr(f'scenario{scenario_idx}_filename')
        # h3m_size: the scenario's own gzip member's COMPRESSED byte length.
        # NOT just informational - CRITICAL that this stays accurate. If a
        # scenario's map gets re-translated (changing its compressed size)
        # and this field is left at the OLD value, the game reads/allocates
        # based on the STALE size and that scenario silently breaks in-game
        # (missing heroes, "old map format") while still passing every
        # static check this project's own parser can run - this was the
        # actual root cause of a very long, confusing debugging session.
        # Tagged as its own segment kind (not lumped into 'fixed') so
        # rebuild() can patch it to the real new size - see patch_h3m_sizes().
        segments.append(H3mSizeSegment('h3m_size', scenario_idx, p, p + 4))
        p += 4
        # 2 fixed bytes + a "which earlier scenarios must be completed
        # first" bitmask (1 bit/scenario, so ceil(scenario_count/8) bytes -
        # 1 byte for every campaign except FINAL's 12 scenarios, which
        # needs 2). Found by hex-diffing FINAL.h3c's scenario 0 (the only
        # campaign with >8 scenarios) against this same gap in campaigns
        # that parse fine - reading a hardcoded 3 here desyncs everything
        # after it for FINAL specifically (galaxy-brained garbage prolog
        # length, cascading failure) while working by coincidence for
        # every other campaign, which all have <=8 scenarios.
        precond_bytes = (scenario_count + 7) // 8
        fixed(p + 2 + precond_bytes)   # unknown flags + preconditions bitmask
        pstr(f'scenario{scenario_idx}_prolog')
        fixed(p + PRE_PSTR_UNKNOWN_BYTES)
        pstr(f'scenario{scenario_idx}_epilog')

        if scenario_idx < scenario_count - 1:
            next_name_pos, _ = find_next_h3m_name(header, p)
            if next_name_pos is None:
                raise HeaderStructureError(f"couldn't find scenario {scenario_idx + 1}'s filename after {p}")
            fixed(next_name_pos)   # this scenario's opaque "starting bonus" block
        else:
            # After the LAST scenario's epilog there's one more optional
            # field: a whole-campaign closing narration (shown after the
            # final cutscene video, e.g. AB's "Lucifer Kreegan is dead...").
            # Found by grepping a known English closing line straight into
            # the raw header bytes - it sat inside what this function used
            # to treat as one opaque trailing blob, so it was silently
            # never extracted/translated even though Hurtom's own file has
            # a full Ukrainian translation for it sitting right there. Empty
            # (length 0) for campaigns without this extra screen (e.g.
            # GOOD1) - same 3-unknown-bytes-then-pstr shape as every other
            # prolog/epilog, just with no marker search needed since it's
            # still the last thing before the header's own known end.
            fixed(p + PRE_PSTR_UNKNOWN_BYTES)
            pstr('campaign_epilogue')
            fixed(n)   # trailing bonus block - just take the rest, no search needed

    if p != n:
        raise HeaderStructureError(f"header parse ended at {p}, expected exactly {n}")

    return segments


def extract(h3c_path: str, out_json: str, ua_source_path: str | None = None,
            stem: str | None = None) -> None:
    """Pulls every wrapper-level text field (campaign name/desc/closing-
    narration epilogue, each scenario's prolog/epilog) out of a .h3c into
    an editable JSON. In: h3c_path (the .h3c to read - EN original or
    already-translated, either works), out_json (path to write),
    ua_source_path (optional - a Hurtom-translated .h3c of the SAME
    campaign; when given, its matching field values pre-fill 'ua' instead
    of leaving it blank), stem (the `var` prefix, e.g. 'GOOD1' - defaults
    to the input filename uppercased). Out: None (writes out_json = a list
    of `{var, field, en, ua}` dicts - `field` is the raw label
    read_header_segments() used, e.g. 'scenario0_prolog', needed later by
    rebuild(); `var` is just `field` prefixed with `stem` for readability/
    uniqueness across files). Skips `*_filename` fields (not translatable
    content - map filenames)."""
    raw = open(h3c_path, 'rb').read()
    header, scenario_members = split_h3c(raw)
    segments = read_header_segments(header, len(scenario_members))

    ua_values = {}
    if ua_source_path:
        ua_raw = open(ua_source_path, 'rb').read()
        ua_header, ua_scenario_members = split_h3c(ua_raw)
        ua_segments = read_header_segments(ua_header, len(ua_scenario_members))
        for seg in ua_segments:
            if seg[0] == 'pstr':
                _, field_name, s, e = seg
                ua_values[field_name] = ua_header[s + 4:e].decode(TEXT_ENCODING, errors='replace')

    stem = stem or os.path.splitext(os.path.basename(h3c_path))[0].upper()
    records = []
    for seg in segments:
        if seg[0] != 'pstr':
            continue
        _, field_name, s, e = seg
        if field_name.endswith('_filename'):
            continue  # not translatable content, skip
        en_text = header[s + 4:e].decode(TEXT_ENCODING, errors='replace')
        records.append({
            'var': f'{stem}_{field_name}',
            'field': field_name,
            'en': en_text,
            'ua': ua_values.get(field_name, ''),
        })

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(records)} field(s) to {out_json}")


def rebuild(h3c_path: str, json_path: str, out_path: str) -> None:
    """Writes a new .h3c with wrapper-level text fields replaced from a
    JSON of edits, and every scenario map member copied through byte-
    identical (this function never touches map bodies - see
    h3m_writer.rebuild() for that, and its note about needing
    patch_h3m_sizes() afterward if it's used too).
    In: h3c_path (original .h3c), json_path (a list of `{field, ua}` -
    same shape extract() writes; `field` must match the raw label from
    read_header_segments(), e.g. 'campaign_epilogue', 'scenario2_epilog' -
    entries with an empty/missing 'ua' are left as the original English).
    Out: None (writes out_path - a complete, valid .h3c: header
    recompressed as its own gzip member with the edits applied, followed
    by all scenario members unchanged)."""
    raw = open(h3c_path, 'rb').read()
    header, scenario_members = split_h3c(raw)
    segments = read_header_segments(header, len(scenario_members))

    with open(json_path, encoding='utf-8') as f:
        records = json.load(f)
    ua_by_field = {r['field']: r['ua'] for r in records if r.get('ua')}

    # h3m_size segments are covered by rebuild_from_segments() too (always
    # copied through as-is, same as 'fixed' - see its docstring) since this
    # function never touches map bodies; if a LATER step re-translates a
    # scenario's map (h3m_writer.py), it MUST call patch_h3m_sizes()
    # afterward or this field goes stale - see that function's docstring.
    new_header = rebuild_from_segments(header, segments, ua_by_field)

    # Compress the (possibly modified) header as its OWN independent gzip
    # member. Every map member is appended completely untouched, still
    # compressed, exactly as extracted from the original file.
    out = compress_h3_gzip(bytes(new_header))
    for member in scenario_members:
        out += member

    with open(out_path, 'wb') as f:
        f.write(out)
    print(f"Wrote {out_path} (header {len(new_header)} bytes decompressed, "
          f"{len(scenario_members)} map member(s) copied unchanged)")


def patch_h3m_sizes(raw: bytes) -> bytes:
    """THE ACTUAL ROOT CAUSE FIX for a very long, confusing bug this
    session: each scenario's `h3m_size` field in the header records that
    scenario's map member's COMPRESSED byte length - not just for display,
    the game apparently relies on it being accurate (probably to size a
    read/decompress buffer). If a scenario's map gets re-translated
    (h3m_writer.py) its compressed size almost always changes, but nothing
    updates this field automatically - h3c_writer.py's own rebuild() just
    copies it through unchanged from the original. Left stale, that ONE
    scenario silently breaks in-game (heroes missing, "old map format")
    while every static check available (this project's own parser, byte-
    identical no-op tests, gzip header comparisons) keeps passing, because
    none of them cross-check this field against the real member size.

    Call this as the LAST step of any pipeline that edits one or more
    scenario maps, on the fully-assembled output file. It re-derives every
    h3m_size field from the ACTUAL compressed size of that scenario's
    member (whether or not that particular scenario was actually edited -
    harmless and correct either way) and returns the corrected file bytes.
    """
    header, scenario_members = split_h3c(raw)
    segments = read_header_segments(header, len(scenario_members))

    new_header = bytearray(header)
    for seg in segments:
        if seg[0] == 'h3m_size':
            _, scenario_idx, s, _e = seg
            real_size = len(scenario_members[scenario_idx])
            struct.pack_into('<I', new_header, s, real_size)

    out = compress_h3_gzip(bytes(new_header))
    for member in scenario_members:
        out += member
    return out


def main() -> None:
    """CLI dispatch for `extract`/`rebuild` - see module docstring's Usage
    section for the exact argv shape. In: sys.argv. Out: None (calls
    extract()/rebuild(), or exits with an error message)."""
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == 'extract':
        h3c_path, out_json = sys.argv[2], sys.argv[3]
        ua_source = None
        if '--ua-source' in sys.argv:
            ua_source = sys.argv[sys.argv.index('--ua-source') + 1]
        extract(h3c_path, out_json, ua_source)
    elif cmd == 'rebuild':
        h3c_path, json_path, out_path = sys.argv[2], sys.argv[3], sys.argv[4]
        rebuild(h3c_path, json_path, out_path)
    else:
        sys.exit(f"unknown command {cmd!r}")


if __name__ == '__main__':
    main()
