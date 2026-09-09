#!/usr/bin/env python3
"""
Problem this solves: editing text INSIDE a scenario's own .h3m map data
(map name/description, hero names/bios, event messages, quest texts, town
names, sign messages, rumors, etc - anything h3m_parser.py's `texts` list
finds for reading) and writing a new .h3m back out, then re-injecting it
into its .h3c campaign's own independent gzip member (see h3c_writer.py's
docstring for why each scenario's map is its own completely independent
gzip stream that can be re-compressed on its own without touching
anything else in the .h3c file).

Uses h3m_parser.py's `R(data, track=True)` mode, which makes every read
call record its own (kind, ...) segment - 'fixed' (opaque, copied
verbatim) or ('pstr', label, start, end) (substitutable, labelled the
same way h3m_parser.py's own `texts` list labels them, e.g. 'map_name',
'obj12_town_name', 'mapevent0_mesg'). Rebuilding just walks the segment
list once, substituting matched labels and copying everything else
through unchanged - purely sequential, no offset table to fix up, exactly
like h3c_writer.py's header rebuild.

Usage:
    # extract this ONE scenario's map texts to a var/en/ua JSON, optionally
    # pre-filling "ua" from a Hurtom-translated .h3c's matching scenario:
    python h3m_writer.py extract Good1.h3c 0 map0_texts.json --ua-source ../../001_ORIGINAL_HOMM3_FILES_HURTOM/GOOD1.H3C

    # after hand-editing "ua" fields, rebuild just that one scenario's map
    # member and splice it back into a full .h3c:
    python h3m_writer.py rebuild Good1.h3c 0 map0_texts.json Good1_ua.h3c

Scenario index is 0-based, matching h3c_writer.py's split_h3c() scenario
order (same order the .h3c lists scenarios in, which is the same order
their map gzip members appear in the file).
"""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h3c_writer import compress_h3_gzip, patch_h3m_sizes, split_h3c
from h3m_parser import (
    CLASS_TO_META,
    TEXT_ENCODING,
    R,
    Segment,
    TextsList,
    parse_ai_section,
    parse_header,
    parse_map_events,
    parse_object_attributes,
    parse_object_details,
    parse_players,
    parse_tiles,
    rebuild_from_segments,
)


def parse_h3m_tracked(data: bytes) -> R:
    """Same call sequence as h3m_parser.parse_h3m, but with a tracking
    reader so r.segments captures every field's byte span. Returns the
    reader (r.segments is the payload; r.p should equal len(data) minus
    0-or-124 trailing pad bytes on a clean parse, same as parse_h3m)."""
    r = R(data, track=True)
    texts: TextsList = []
    fmt, map_size, has_two_levels = parse_header(r, texts)
    parse_players(r, fmt, texts)
    parse_ai_section(r, fmt, texts)
    parse_tiles(r, map_size, has_two_levels)
    oa_types_raw = parse_object_attributes(r, texts)
    oa_types = [CLASS_TO_META.get(c, -1) for c in oa_types_raw]
    parse_object_details(r, fmt, oa_types, texts)
    parse_map_events(r, fmt, texts)
    return r


def extract(h3c_path: str, scenario_idx: int, out_json: str,
            ua_source_path: str | None = None, stem: str | None = None) -> None:
    """Pulls every in-map text field (map name/desc, hero names/bios,
    events, town names, signs, quests, rumors, ...) out of ONE scenario's
    map into an editable JSON. In: h3c_path, scenario_idx (0-based, see
    module docstring), out_json (path to write), ua_source_path (optional
    Hurtom-translated .h3c of the same campaign, to pre-fill 'ua'), stem
    (the `var` prefix - defaults to '<FILESTEM>_S<scenario_idx>'). Out:
    None (writes out_json = a list of `{var, field, en, ua}` dicts; `field`
    is the raw label h3m_parser produced, e.g. 'obj16_town_name', needed by
    rebuild(); also prints a parse-health line - `remaining` should be 0 or
    124, anything else means this scenario didn't parse cleanly)."""
    raw = open(h3c_path, 'rb').read()
    _, scenario_members = split_h3c(raw)
    member = scenario_members[scenario_idx]
    data = gzip.decompress(member)
    r = parse_h3m_tracked(data)

    ua_values: dict[str, str] = {}
    if ua_source_path:
        ua_raw = open(ua_source_path, 'rb').read()
        _, ua_scenario_members = split_h3c(ua_raw)
        ua_data = gzip.decompress(ua_scenario_members[scenario_idx])
        ua_r = parse_h3m_tracked(ua_data)
        for seg in ua_r.segments:
            if seg[0] == 'pstr':
                _, label, s, e = seg
                ua_values.setdefault(label, ua_data[s + 4:e].decode(TEXT_ENCODING, errors='replace'))

    stem = stem or f"{os.path.splitext(os.path.basename(h3c_path))[0].upper()}_S{scenario_idx}"
    records = []
    for seg in r.segments:
        if seg[0] != 'pstr':
            continue
        _, label, s, e = seg
        en_text = data[s + 4:e].decode(TEXT_ENCODING, errors='replace')
        if not en_text:
            continue
        records.append({
            'var': f'{stem}_{label}',
            'field': label,
            'en': en_text,
            'ua': ua_values.get(label, ''),
        })

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(records)} field(s) to {out_json} "
          f"(parse consumed {r.p}/{len(data)}, remaining={r.remaining()} - "
          f"should be 0 or 124 for a clean parse)")


def rebuild_map_bytes(data: bytes, segments: list[Segment], ua_by_field: dict[str, str]) -> bytes:
    """Thin wrapper around h3m_parser.rebuild_from_segments (the shared
    core every rebuild function in this project now uses - see that
    function's docstring for the actual walk-and-substitute logic; this
    name is kept as this module's own public entry point, and for
    h3m-map-specific documentation, since map bodies never carry an
    'h3m_size' segment the way h3c_writer.rebuild() does).
    In: data (the original decompressed map bytes segments' offsets refer
    into), segments (r.segments from parse_h3m_tracked), ua_by_field
    ({label: replacement_text}). Out: new decompressed map bytes (NOT yet
    including the trailing pad bytes after the last segment - the caller,
    rebuild(), appends those separately since they're outside r.p).

    Segments may have duplicate labels appear more than once (e.g. two
    different heroes both named via 'p0_hero_name' style labels don't
    collide since pid is baked into the label, but a generic label used
    twice would apply the SAME replacement text to both occurrences) -
    this project's h3m labels are always contextualized (obj index,
    player id, event index) so this hasn't been an issue in practice."""
    return rebuild_from_segments(data, segments, ua_by_field, encoding=TEXT_ENCODING)


def rebuild(h3c_path: str, scenario_idx: int, json_path: str, out_path: str) -> None:
    """Writes a new .h3c with ONE scenario's in-map text replaced from a
    JSON of edits; every other scenario's map member and the header are
    copied through byte-identical. Always calls h3c_writer.patch_h3m_sizes()
    on the result before returning - this is the ONLY writer function in
    this project that touches map bodies, so it's the one place that fix
    is mandatory (h3c_writer.rebuild() alone never needs it, since it never
    changes a map's compressed size).
    In: h3c_path (original .h3c - can already have OTHER scenarios/the
    wrapper translated; this only touches scenario_idx), scenario_idx,
    json_path (a list of `{field, ua}` - same shape extract() writes;
    `field` must match the raw label from h3m_parser, e.g.
    'obj16_town_name'; entries with empty/missing 'ua' keep the original
    English), out_path. Out: None (writes out_path - a complete, valid,
    h3m_size-corrected .h3c, safe to feed straight to `mmarch add`)."""
    raw = open(h3c_path, 'rb').read()
    header, scenario_members = split_h3c(raw)
    member = scenario_members[scenario_idx]
    data = gzip.decompress(member)
    r = parse_h3m_tracked(data)

    with open(json_path, encoding='utf-8') as f:
        records = json.load(f)
    ua_by_field = {rec['field']: rec['ua'] for rec in records if rec.get('ua')}

    new_map_bytes = rebuild_map_bytes(data, r.segments, ua_by_field)
    new_map_bytes += data[r.p:]  # trailing pad bytes (0 or 124, "HD Edition padding") - not covered by any segment
    new_member = compress_h3_gzip(new_map_bytes)

    # `header` here is the DECOMPRESSED header bytes from split_h3c (we're
    # not editing it) - recompress as-is to reproduce its member unchanged.
    header_member = compress_h3_gzip(header)
    out_bytes = bytearray(header_member)
    for i, m in enumerate(scenario_members):
        out_bytes += new_member if i == scenario_idx else m

    # CRITICAL, easy to forget: the header's h3m_size field for this
    # scenario now points at the OLD compressed size - re-derive it from
    # the real new member size, or this scenario silently breaks in-game
    # (see patch_h3m_sizes()'s docstring - this was a major root cause
    # found only after a very long debugging session).
    out_bytes = patch_h3m_sizes(bytes(out_bytes))

    with open(out_path, 'wb') as f:
        f.write(out_bytes)
    print(f"Wrote {out_path} (scenario {scenario_idx}'s map recompressed, "
          f"{len(scenario_members) - 1} other member(s) + header untouched)")


def main() -> None:
    """CLI dispatch for `extract`/`rebuild` - see module docstring's Usage
    section for the exact argv shape. In: sys.argv. Out: None."""
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == 'extract':
        h3c_path, scenario_idx, out_json = sys.argv[2], int(sys.argv[3]), sys.argv[4]
        ua_source = None
        if '--ua-source' in sys.argv:
            ua_source = sys.argv[sys.argv.index('--ua-source') + 1]
        extract(h3c_path, scenario_idx, out_json, ua_source)
    elif cmd == 'rebuild':
        h3c_path, scenario_idx, json_path, out_path = sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
        rebuild(h3c_path, scenario_idx, json_path, out_path)
    else:
        sys.exit(f"unknown command {cmd!r}")


if __name__ == '__main__':
    main()
