#!/usr/bin/env python3
"""
Structural parser for the HoMM3 .h3c CAMPAIGN wrapper format. Layers on top
of h3m_parser.py (same folder) to also decode the N embedded scenario maps.

There is NO public documentation of the .h3c wrapper's exact byte layout -
not even homm3tools' own h3clib fully parses it (it patches files via
string-search hacks instead of a real struct reader). Everything below was
reverse-engineered by hand against real Good1.h3c ("Long Live the Queen")
and cross-checked against several other campaigns. See
H3M_H3C_FORMAT_NOTES.md for the full derivation and open issues.

CORRECTION (this file's own layout description below predates it, and
`parse_h3c()` works around it by decompressing everything up front - see
`h3c_writer.py`'s module docstring for the full story before writing new
code against this file): a `.h3c` is NOT one gzip stream. It's N+1
*independent* gzip members concatenated - one for the header below, one
per scenario's own `.h3m` blob. `parse_h3c()` here still works because its
caller (`__main__` below) decompresses the WHOLE raw file as if it were
one stream before calling it, which happens to reproduce the same bytes
`h3c_writer.split_h3c()` gets by doing it the structurally correct
way - fine for read-only inspection, but do not build new EDITING code on
top of this file's model; use `h3c_writer.py`/`h3m_writer.py` for that.

Known-good byte layout (after the initial uint32 gzip decompression of the
whole .h3c file):

    header:
        uint32 format            (h3m-style format id of the header string
                                   encoding - NOT necessarily the format of
                                   the embedded maps)
        uint8  campaign_map_id
        pstr   campaign_name
        pstr   campaign_description
        uint8  fixed_difficulty
        uint8  music

    repeated once per scenario (count is NOT stored - keep going until the
    next thing found is an h3m format marker instead of another filename):
        pstr    scenario_filename          (e.g. "Good-1a.h3m" - not real)
        uint32  h3m_size                   (DO NOT TRUST - see notes: real
                                             blobs run well past this)
        3 bytes unknown/flags
        pstr    prolog_text                (shown before the mission; often
                                             the same content as CAMPDIAG.TXT)
        3 bytes unknown/flags
        pstr    epilog_text
        ??? bytes "starting bonus" block (heroKeeps flags + bonus choices,
            length NOT understood - skipped via string-search instead of
            parsed, see find_next_h3m_name/find_next_h3m_blob_start below)

    then, back to back with NO count field, N raw (already-decompressed -
    the whole .h3c is one gzip stream) h3m blobs, one per scenario in the
    same order as the map_infos above. Each blob's true end is found by
    just running h3m_parser.parse_h3m on it and trusting where it stops
    (checked against the same 0-or-124-trailing-bytes rule used for
    standalone .h3m files) - NOT by trusting h3m_size.

Usage:
    python h3c_parser.py path/to/Campaign.h3c
"""
import gzip
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h3m_parser import TEXT_ENCODING, R, parse_h3m

NAME_RE = re.compile(rb"^[A-Za-z0-9_\-' ]{1,40}\.h3m$", re.I)
FORMAT_MARKERS = {0x0E, 0x15, 0x1C, 0x1D}


def find_next_h3m_name(data: bytes, pos: int) -> tuple[int | None, str | None]:
    """Search forward for the next `uint32 len + name` pstr matching *.h3m -
    used to skip over each scenario's opaque "starting bonus" block (whose
    length isn't otherwise known) by finding where the NEXT scenario's own
    filename pstr begins. In: data (decompressed header bytes), pos (byte
    offset to start scanning from). Out: (offset, name_str) of the first
    match at or after pos, or (None, None) if nothing matches before the
    end of data (also used as evidence that the map_info list ended and
    the next thing is an h3m blob, not another scenario)."""
    i = pos
    n = len(data)
    while i + 4 < n:
        length = struct.unpack_from('<I', data, i)[0]
        if 1 <= length <= 40 and i + 4 + length <= n:
            candidate = data[i+4:i+4+length]
            if NAME_RE.match(candidate):
                return i, candidate.decode('ascii')
        i += 1
    return None, None


def find_next_h3m_blob_start(data: bytes, pos: int) -> tuple[int | None, int | None]:
    """Search forward for a 4-byte h3m format marker (0x0E/0x15/0x1C/0x1D)
    followed by a plausible is_playable byte (0 or 1) - marks where the
    map_info list ends and the first scenario's own decompressed .h3m
    bytes begin. In: data, pos. Out: (offset, format_int) of the first
    match at or after pos, or (None, None) if none found."""
    i = pos
    n = len(data)
    while i + 5 <= n:
        fmt = struct.unpack_from('<I', data, i)[0]
        if fmt in FORMAT_MARKERS and data[i+4] in (0, 1):
            return i, fmt
        i += 1
    return None, None


def parse_h3c(data: bytes) -> tuple[str, str, list[dict], list[tuple[str, bytes]], int]:
    """In: data - the FULLY decompressed bytes of an entire .h3c (header +
    all scenario blobs back to back - see the CORRECTION note above for
    how callers get this from the raw file with a single gzip.decompress()
    call). Out: (campaign_name, campaign_desc, scenarios, wrapper_texts, end_offset).

    Each scenario dict has: name, h3m_size (untrusted, see module docstring),
    blob_offset, blob (raw bytes, exactly as long as the parser consumed),
    format, object_count, event_count, h3m_texts (list of (label, raw_bytes)
    from inside that scenario's own map data - guards, seer huts, hero bios,
    town/hero names etc).
    """
    r = R(data)
    texts = []

    r.u32()  # format
    r.u8()  # campaign_map_id
    camp_name = r.pstr(); texts.append(('campaign_name', camp_name))
    camp_desc = r.pstr(); texts.append(('campaign_desc', camp_desc))
    r.u8()  # fixed_difficulty
    r.u8()  # music

    scenarios: list[dict] = []
    while True:
        mname = r.pstr()
        texts.append((f'scenario{len(scenarios)}_filename', mname))
        h3m_size = r.u32()
        r.skip(3)
        prolog = r.pstr()
        if prolog: texts.append((f'scenario{len(scenarios)}_prolog', prolog))
        r.skip(3)
        epilog = r.pstr()
        if epilog: texts.append((f'scenario{len(scenarios)}_epilog', epilog))

        scenarios.append({'name': mname.decode('ascii'), 'h3m_size': h3m_size})

        # find whether next thing is another scenario name, or the start of h3m blobs
        next_name_pos, _next_name = find_next_h3m_name(r.d, r.p)
        next_blob_pos, _next_blob_fmt = find_next_h3m_blob_start(r.d, r.p)

        if next_name_pos is not None and (next_blob_pos is None or next_name_pos < next_blob_pos):
            r.p = next_name_pos  # continue to next scenario's map_info
        else:
            # reached the end of map_info list; next_blob_pos marks first h3m blob
            r.p = next_blob_pos
            break

    # h3m_size does NOT reliably describe each blob's length (empirically,
    # actual maps run well past it) - instead use our own h3m parser to
    # self-determine where each embedded map ends, then skip zero padding
    # up to the next format marker for the following scenario.
    blob_start = r.p
    offset = blob_start
    for i, s in enumerate(scenarios):
        sub = data[offset:]
        r2, mfmt, mtexts, obj_count, event_count = parse_h3m(sub)
        s['blob_offset'] = offset
        s['blob'] = sub[:r2.p]
        s['format'] = mfmt
        s['object_count'] = obj_count
        s['event_count'] = event_count
        s['h3m_texts'] = mtexts
        offset += r2.p
        if i < len(scenarios) - 1:
            while offset + 5 <= len(data) and not (
                struct.unpack_from('<I', data, offset)[0] in FORMAT_MARKERS
                and data[offset + 4] in (0, 1)
            ):
                offset += 1

    return (camp_name.decode(TEXT_ENCODING, errors='replace'),
            camp_desc.decode(TEXT_ENCODING, errors='replace'), scenarios, texts, offset)


if __name__ == '__main__':
    path = sys.argv[1]
    with open(path, 'rb') as f:
        data = gzip.decompress(f.read())
    name, desc, scenarios, texts, end_offset = parse_h3c(data)
    print(f"Campaign: {name}")
    print(f"Scenarios: {len(scenarios)}")
    for s in scenarios:
        print(f"  {s['name']}  size={s['h3m_size']}  offset={s['blob_offset']}")
    diff = len(data) - end_offset
    print(f"Consumed through offset {end_offset} of {len(data)} (diff={diff})")
    if diff not in (0, 124):
        print("WARNING: trailing byte count is neither 0 nor the usual 124 - check for a parse error above.")

    for i, s in enumerate(scenarios):
        print(f"  scenario {i} ({s['name']}): format={hex(s['format'])} "
              f"objects={s['object_count']} events={s['event_count']} "
              f"blob_len={len(s['blob'])} texts={len(s['h3m_texts'])}")
