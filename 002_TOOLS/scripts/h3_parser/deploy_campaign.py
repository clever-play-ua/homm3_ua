#!/usr/bin/env python3
"""
Problem this solves: build_mission_texts.py lays out a campaign's text as
one {var,field,en,ua} JSON per mission folder (005_RAW/<campaign>/
<CampaignName>_description.json for the campaign-level fields, then
missions/001_<Map>/001_<Map>_text.json, missions/002_<Map>/..., etc for
each scenario) for easy hand-editing, but h3c_writer.rebuild()/
h3m_writer.rebuild() each expect a flat JSON keyed by the RAW field name
they use internally (e.g. 'scenario0_prolog', 'map_name', not
build_mission_texts.py's 'wrapper_prolog'/'map_map_name'). This script
bridges the two: read the campaign-level description file plus every
mission folder's `*_text.json`, re-key each record back to what the
writers expect, and chain h3c_writer.rebuild + h3m_writer.rebuild (one
call per scenario) into a single final translated .h3c.

Usage:
    python deploy_campaign.py Ab.h3c 005_RAW/008_Armageddons_Blade/missions out_Ab.h3c
"""
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h3c_writer import rebuild as h3c_rebuild
from h3c_writer import split_h3c
from h3m_writer import rebuild as h3m_rebuild

Field = dict[str, str]  # {field, ua} - the raw-keyed shape h3c_rebuild()/h3m_rebuild() expect


def deploy(h3c_path: str, missions_dir: str, out_path: str) -> None:
    """The actual re-keying + chained-rebuild logic (see module docstring)
    - factored out of main() so it's directly callable/testable without
    going through argv, the same shape every other file in this package
    uses (main() below is now just the argv-parsing shim).
    In: h3c_path - the campaign file to rebuild FROM (its scenario count/
    order must match missions_dir's folders - usually the same EN
    original build_mission_texts.py was pointed at, but any .h3c with the
    same scenario layout works, e.g. one already partially translated),
    missions_dir - the `missions/` folder produced (and by now
    hand-edited) by build_mission_texts.py, out_path - where to write the
    final result. Out: None (writes out_path - one fully-rebuilt .h3c with
    every non-empty 'ua' field from every mission folder applied, ready
    for `mmarch add`; also leaves small `_tmp_*` intermediate JSON/`.h3c`
    files next to out_path - harmless, safe to delete). Only fields with a
    non-empty 'ua' are ever touched; everything else is left as whatever
    h3c_path already had (so re-running this after fixing just one field
    in one mission folder is cheap and safe). Exits the process (via
    sys.exit) on a folder-count mismatch - see the check below."""
    raw = open(h3c_path, 'rb').read()
    _, scenario_members = split_h3c(raw)
    scenario_count = len(scenario_members)

    # campaign-level fields (campaign-root "<Name>_description.json",
    # a sibling of missions_dir - see build_mission_texts.py's docstring
    # for why this isn't nested inside missions_dir as its own fake
    # "mission 0" anymore): field is 'wrapper_campaign_name'/
    # 'wrapper_campaign_desc' -> raw field is 'campaign_name'/
    # 'campaign_desc' (no scenario prefix).
    wrapper_records: list[Field] = []
    campaign_root = os.path.dirname(os.path.normpath(missions_dir))
    desc_files = glob.glob(os.path.join(campaign_root, '*_description.json'))
    for desc_path in desc_files:
        loaded = json.load(open(desc_path, encoding='utf-8'))
        # build_mission_texts.py originally wrote this file as a bare
        # list of {var,field,en,ua} records; it may also be a dict with
        # that same list under 'campaign_fields' plus other, unrelated
        # top-level keys (e.g. 'voice_over' - reference data for a future
        # .srt build, not consumed here) added by a later, separate pass.
        # Accept either shape so adding new top-level keys never breaks
        # this reader.
        recs = loaded['campaign_fields'] if isinstance(loaded, dict) else loaded
        for r in recs:
            if r['field'].startswith('wrapper_') and r.get('ua'):
                raw_field = r['field'][len('wrapper_'):]
                wrapper_records.append({'field': raw_field, 'ua': r['ua']})

    scenario_folders = sorted(glob.glob(os.path.join(missions_dir, '*')))
    if len(scenario_folders) != scenario_count:
        sys.exit(f"folder count mismatch: {h3c_path} has {scenario_count} scenarios, "
                 f"{missions_dir} has {len(scenario_folders)} mission folders")

    map_records_per_scenario: list[list[Field]] = []
    for i, folder in enumerate(scenario_folders):
        text_files = glob.glob(os.path.join(folder, '*_text.json'))
        if len(text_files) != 1:
            sys.exit(f"{folder}: expected exactly one *_text.json, found {len(text_files)}")
        recs = json.load(open(text_files[0], encoding='utf-8'))
        map_recs: list[Field] = []
        for r in recs:
            if not r.get('ua'):
                continue
            if r['field'].startswith('wrapper_'):
                raw_field = f'scenario{i}_{r["field"][len("wrapper_"):]}'
                wrapper_records.append({'field': raw_field, 'ua': r['ua']})
            elif r['field'].startswith('map_'):
                raw_label = r['field'][len('map_'):]
                map_recs.append({'field': raw_label, 'ua': r['ua']})
        map_records_per_scenario.append(map_recs)

    tmp_dir = os.path.dirname(out_path) or '.'
    wrapper_json_path = os.path.join(tmp_dir, '_tmp_wrapper.json')
    with open(wrapper_json_path, 'w', encoding='utf-8') as f:
        json.dump(wrapper_records, f, ensure_ascii=False)

    current = os.path.join(tmp_dir, '_tmp_step0.h3c')
    h3c_rebuild(h3c_path, wrapper_json_path, current)
    print(f"wrapper rebuilt: {len(wrapper_records)} field(s) applied")

    for i, map_recs in enumerate(map_records_per_scenario):
        mj = os.path.join(tmp_dir, f'_tmp_s{i}.json')
        with open(mj, 'w', encoding='utf-8') as f:
            json.dump(map_recs, f, ensure_ascii=False)
        nxt = os.path.join(tmp_dir, f'_tmp_step{i + 1}.h3c')
        h3m_rebuild(current, i, mj, nxt)
        print(f"scenario {i} rebuilt: {len(map_recs)} field(s) applied")
        current = nxt

    shutil.copy2(current, out_path)
    print(f"\nWrote final translated campaign: {out_path}")


def main() -> None:
    """CLI entry point - see module docstring's Usage line for the exact
    argv shape. In: sys.argv = [h3c_path, missions_dir, out_path]. Out:
    None (delegates to deploy(), see its docstring)."""
    deploy(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == '__main__':
    main()
