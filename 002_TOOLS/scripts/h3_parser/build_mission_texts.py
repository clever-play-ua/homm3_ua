#!/usr/bin/env python3
"""
Problem this solves: lay out ALL translatable text for a campaign - both
the .h3c wrapper's per-scenario fields (prolog/epilog, via h3c_writer.py)
and each scenario's own in-map text (map name/desc, hero names/bios,
event messages, town names, etc, via h3m_writer.py) - into one numbered
folder per mission, each with a single {var, field, en, ua} JSON, matching
the rest of this project's 005_RAW convention (build_raw.py's LOD-file
JSONs, extract_campaigns.py's per-campaign JSONs).

Folder layout produced:
    005_RAW/<NNN>_<CampaignName>/
        <CampaignName>_description.json   (campaign-level fields only -
                                            name/desc/epilogue, belongs to
                                            no single scenario)
        missions/
            001_<MapName>/001_<MapName>_text.json
            002_<MapName>/002_<MapName>_text.json
            ...
(map name is read from the scenario's own map_name field, English, with
spaces/punctuation replaced so it's filesystem-safe)

**File names are prefixed with their own folder's name on purpose**
(`001_Homecoming_text.json`, not a bare `texts.json`) - every mission
folder across every campaign used to produce an identically-named
`texts.json`, which made it impossible to drop a handful of them into one
place (e.g. to hand off to a translator) without them colliding/
overwriting each other. `deploy_campaign.py` reads this same naming
convention back - if you rename the pattern here, update it there too.

"ua" values are pre-filled from a Hurtom-translated .h3c of the same
campaign when given (--ua-source) - same source used by both
h3c_writer.py and h3m_writer.py under the hood - so this is ready to
hand-correct rather than translate from scratch, for the 20 campaigns
where a Hurtom .h3c exists.

Usage:
    python build_mission_texts.py Good1.h3c 005_RAW/001_Long_Live_the_Queen/missions \
        --ua-source ../../001_ORIGINAL_HOMM3_FILES_HURTOM/GOOD1.H3C --stem GOOD1
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gzip

from h3c_writer import read_header_segments, split_h3c
from h3m_parser import TEXT_ENCODING
from h3m_writer import R, parse_h3m_tracked

Record = dict[str, str]  # {var, field, en, ua} - this project's universal text-record shape


def safe_name(s: str) -> str:
    """In: s (arbitrary English text, e.g. a map's own name field). Out:
    a filesystem-safe folder-name fragment (alphanumerics/spaces/hyphens
    kept, everything else stripped, spaces turned into underscores;
    'Untitled' if that leaves nothing)."""
    s = re.sub(r'[^\w\- ]', '', s).strip()
    return re.sub(r'\s+', '_', s) or 'Untitled'


def wrapper_records_for_scenario(header: bytes, ua_header: bytes | None, scenario_count: int,
                                  scenario_idx: int, stem: str) -> list[Record]:
    """Extracts just ONE scenario's own wrapper-level fields (prolog/
    epilog - not the campaign-wide name/desc/epilogue, see main()'s
    separate handling of those) as mission-folder-shaped records.
    In: header (decompressed .h3c header bytes, EN), ua_header (same, from
    a Hurtom file, or None), scenario_count, scenario_idx, stem (the `var`
    prefix). Out: list of `{var, field, en, ua}` dicts - `field` is
    'wrapper_prolog'/'wrapper_epilog' (note: NOT the raw h3c_writer label,
    which is 'scenarioN_prolog' - deploy_campaign.py re-derives that raw
    label from this shape + the folder's own scenario index when rebuilding)."""
    segments = read_header_segments(header, scenario_count)
    ua_values = {}
    if ua_header is not None:
        ua_segments = read_header_segments(ua_header, scenario_count)
        for seg in ua_segments:
            if seg[0] == 'pstr':
                _, field_name, s, e = seg
                ua_values[field_name] = ua_header[s + 4:e].decode(TEXT_ENCODING, errors='replace')

    records = []
    prefix = f'scenario{scenario_idx}_'
    for seg in segments:
        if seg[0] != 'pstr':
            continue
        _, field_name, s, e = seg
        if not field_name.startswith(prefix) or field_name.endswith('_filename'):
            continue
        en_text = header[s + 4:e].decode(TEXT_ENCODING, errors='replace')
        if not en_text:
            continue
        short_field = field_name[len(prefix):]  # 'prolog' / 'epilog'
        records.append({
            'var': f'{stem}_{records_var_suffix(scenario_idx)}_{short_field}',
            'field': f'wrapper_{short_field}',
            'en': en_text,
            'ua': ua_values.get(field_name, ''),
        })
    return records


def records_var_suffix(scenario_idx: int) -> str:
    """In: scenario_idx (0-based). Out: str - the 1-based 'M<N>' fragment
    used inside every `var` this script emits for that scenario (e.g.
    scenario_idx=0 -> 'M1'), so var names read as "mission 1", "mission 2"
    matching how the game numbers them, not the 0-based internal index."""
    return f'M{scenario_idx + 1}'


def map_records_for_scenario(data: bytes, ua_data: bytes | None, stem: str,
                              scenario_idx: int) -> tuple[list[Record], R]:
    """Extracts one scenario's in-map text (via h3m_writer.parse_h3m_tracked)
    as mission-folder-shaped records. In: data (decompressed map bytes,
    EN), ua_data (same, from a Hurtom file, or None), stem, scenario_idx.
    Out: (records, r) - records is a list of `{var, field, en, ua}` dicts
    (`field` = 'map_' + the raw h3m_parser label, e.g. 'map_obj16_town_name'
    - deploy_campaign.py strips the 'map_' prefix back off when rebuilding);
    r is the tracked reader, returned so the caller can report parse health
    (r.remaining()) without re-parsing."""
    r = parse_h3m_tracked(data)
    ua_values: dict[str, str] = {}
    if ua_data is not None:
        ua_r = parse_h3m_tracked(ua_data)
        for seg in ua_r.segments:
            if seg[0] == 'pstr':
                _, label, s, e = seg
                ua_values.setdefault(label, ua_data[s + 4:e].decode(TEXT_ENCODING, errors='replace'))

    records = []
    for seg in r.segments:
        if seg[0] != 'pstr':
            continue
        _, label, s, e = seg
        en_text = data[s + 4:e].decode(TEXT_ENCODING, errors='replace')
        if not en_text:
            continue
        records.append({
            'var': f'{stem}_{records_var_suffix(scenario_idx)}_{label}',
            'field': f'map_{label}',
            'en': en_text,
            'ua': ua_values.get(label, ''),
        })
    return records, r


def main() -> None:
    """CLI entry point - see module docstring's Usage line for the exact
    argv shape. In: h3c_path, out_missions_dir, --ua-source, --stem (all
    via argparse). Out: None (writes the campaign-root `*_description.json`
    and `missions/NNN_<MapName>/NNN_<MapName>_text.json` files described in
    the module docstring; also prints, per scenario, a parse-health line -
    anything other than "clean parse" means that scenario didn't fully
    parse and its extracted text may be incomplete/wrong)."""
    ap = argparse.ArgumentParser()
    ap.add_argument('h3c_path')
    ap.add_argument('out_missions_dir')
    ap.add_argument('--ua-source', default=None)
    ap.add_argument('--stem', default=None)
    args = ap.parse_args()

    raw = open(args.h3c_path, 'rb').read()
    header, scenario_members = split_h3c(raw)
    scenario_count = len(scenario_members)

    ua_header, ua_scenario_members = None, [None] * scenario_count
    if args.ua_source:
        ua_raw = open(args.ua_source, 'rb').read()
        ua_header, ua_scenario_members = split_h3c(ua_raw)
        if len(ua_scenario_members) != scenario_count:
            sys.exit(f"scenario count mismatch: {args.h3c_path} has {scenario_count}, "
                     f"{args.ua_source} has {len(ua_scenario_members)}")

    stem = args.stem or os.path.splitext(os.path.basename(args.h3c_path))[0].upper()
    os.makedirs(args.out_missions_dir, exist_ok=True)

    # Campaign-level fields (campaign_name/campaign_desc) belong to neither
    # scenario, so they'd otherwise never end up in ANY mission folder and
    # get silently lost on a from-scratch rebuild (hit this for real -
    # h3c_writer.rebuild only fills in fields it's handed, so a campaign
    # rebuilt purely from per-mission JSONs reverted these two to English).
    # Emit them as their own "mission 0" so nothing is missing.
    campaign_segments = read_header_segments(header, scenario_count)
    ua_campaign_values = {}
    if ua_header is not None:
        ua_campaign_segments = read_header_segments(ua_header, scenario_count)
        for seg in ua_campaign_segments:
            if seg[0] == 'pstr':
                _, field_name, s, e = seg
                ua_campaign_values[field_name] = ua_header[s + 4:e].decode(TEXT_ENCODING, errors='replace')
    campaign_records = []
    campaign_display_name = None
    for seg in campaign_segments:
        if seg[0] != 'pstr' or seg[1] not in ('campaign_name', 'campaign_desc', 'campaign_epilogue'):
            continue
        _, field_name, s, e = seg
        en_text = header[s + 4:e].decode(TEXT_ENCODING, errors='replace')
        if field_name == 'campaign_epilogue' and not en_text:
            continue  # most campaigns don't use this extra closing-narration field at all
        if field_name == 'campaign_name':
            campaign_display_name = en_text
        campaign_records.append({
            'var': f'{stem}_{field_name}',
            'field': f'wrapper_{field_name}',
            'en': en_text,
            'ua': ua_campaign_values.get(field_name, ''),
        })
    # Campaign root is out_missions_dir's parent (out_missions_dir is
    # conventionally "<campaign_root>/missions") - the description file
    # lives there, a sibling of missions/, not nested inside it.
    campaign_root = os.path.dirname(os.path.normpath(args.out_missions_dir))
    campaign_name_safe = safe_name(campaign_display_name or stem)
    desc_path = os.path.join(campaign_root, f'{campaign_name_safe}_description.json')
    with open(desc_path, 'w', encoding='utf-8') as f:
        json.dump(campaign_records, f, ensure_ascii=False, indent=2)
    print(f"{desc_path}: {len(campaign_records)} field(s)")

    for i in range(scenario_count):
        data = gzip.decompress(scenario_members[i])
        ua_data = gzip.decompress(ua_scenario_members[i]) if ua_scenario_members[i] else None

        map_records, r = map_records_for_scenario(data, ua_data, stem, i)
        wrapper_records = wrapper_records_for_scenario(header, ua_header, scenario_count, i, stem)

        map_name = next((rec['en'] for rec in map_records if rec['field'] == 'map_map_name'), f'Scenario{i}')
        folder_name = f'{i + 1:03d}_{safe_name(map_name)}'
        folder = os.path.join(args.out_missions_dir, folder_name)
        os.makedirs(folder, exist_ok=True)

        all_records = wrapper_records + map_records
        with open(os.path.join(folder, f'{folder_name}_text.json'), 'w', encoding='utf-8') as f:
            json.dump(all_records, f, ensure_ascii=False, indent=2)

        clean = 'clean' if r.remaining() in (0, 124) else f'DRIFT (remaining={r.remaining()})'
        print(f"{folder}: {len(all_records)} field(s) ({clean} parse)")


if __name__ == '__main__':
    main()
