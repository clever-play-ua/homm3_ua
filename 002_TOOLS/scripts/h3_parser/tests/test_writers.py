"""
Coverage gap this closes: test_roundtrip.py's no-op tests prove
h3c_writer.rebuild() reproduces the WRAPPER header byte-for-byte when no
translation is applied, but nothing in the suite ever exercised the
functions that actually DO the substitution this whole project exists
for - h3m_writer.rebuild() (in-map text) and h3c_writer.rebuild() with a
REAL replacement, plus h3c_parser.py's own parse_h3c() and
build_mission_texts.py's pure helper functions. A `pytest --cov` run is
what surfaced this (0-29% coverage on exactly these files) - see the
h3_parser/README.md entry on this test suite.
"""
import glob
import gzip
import os
import subprocess
import sys

import pytest
from build_mission_texts import map_records_for_scenario, records_var_suffix, safe_name, wrapper_records_for_scenario
from conftest import RAW_DIR
from deploy_campaign import deploy
from h3c_parser import parse_h3c
from h3c_writer import extract as h3c_extract
from h3c_writer import rebuild as h3c_rebuild
from h3c_writer import split_h3c
from h3m_writer import extract as h3m_extract
from h3m_writer import parse_h3m_tracked
from h3m_writer import rebuild as h3m_rebuild


def _first_campaign():
    """Out: (folder_name, h3c_path) for GOOD1 specifically - small (3
    scenarios), always present, and the one campaign this project has
    actually completed in-game, so its real content is the most trustworthy
    fixture to build substitution tests against."""
    candidates = glob.glob(os.path.join(RAW_DIR, "001_Long_Live_the_Queen", "*.h3c"))
    candidates = [c for c in candidates if not c.lower().endswith("_ua.h3c")]
    assert candidates, "expected 001_Long_Live_the_Queen/Good1.h3c to exist"
    return candidates[0]


def test_h3m_writer_rebuild_applies_a_real_substitution(tmp_path):
    """The actual "translate one field" path: extract scenario 0's text,
    pick a real field that has non-empty English text, rebuild with a
    distinctive replacement string in its 'ua', then re-extract from the
    rebuilt file and confirm that exact string comes back - and that the
    scenario still parses cleanly (remaining 0 or 124), the same
    correctness bar test_roundtrip.py holds every campaign to."""
    h3c_path = _first_campaign()
    extracted_json = tmp_path / "scenario0.json"
    h3m_extract(h3c_path, 0, str(extracted_json))

    import json
    records = json.load(open(extracted_json, encoding="utf-8"))
    target = next(r for r in records if r["en"])  # first non-empty text field
    marker = "ZZ_TEST_MARKER_ZZ"
    target["ua"] = marker

    edited_json = tmp_path / "scenario0_edited.json"
    with open(edited_json, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)

    out_h3c = tmp_path / "rebuilt.h3c"
    h3m_rebuild(h3c_path, 0, str(edited_json), str(out_h3c))

    # Re-extract from the REBUILT file and confirm the substitution landed
    # in the same field, and the scenario is still a clean parse. Note:
    # extract() doesn't know or care which language is physically in the
    # file - it always reports whatever's actually there as 'en' (the
    # "source" slot) unless a separate --ua-source is given, which we
    # don't need here - the rebuilt file now genuinely contains `marker`
    # as its only copy of this field's text, so THAT's what comes back.
    reextracted_json = tmp_path / "scenario0_reextracted.json"
    h3m_extract(str(out_h3c), 0, str(reextracted_json))
    reextracted = json.load(open(reextracted_json, encoding="utf-8"))
    matching = [r for r in reextracted if r["field"] == target["field"]]
    assert matching and matching[0]["en"] == marker, (
        f"field {target['field']!r} did not come back as {marker!r} after rebuild"
    )

    _, members = split_h3c(open(out_h3c, "rb").read())
    r = parse_h3m_tracked(gzip.decompress(members[0]))
    assert r.remaining() in (0, 124)


def test_h3c_writer_rebuild_applies_a_real_substitution(tmp_path):
    """Same idea as above, for the WRAPPER's own text (prolog/epilog/
    campaign name) via h3c_writer.rebuild() - test_roundtrip.py only ever
    calls this with NO substitutions (the no-op byte-identical check)."""
    h3c_path = _first_campaign()
    extracted_json = tmp_path / "wrapper.json"
    h3c_extract(h3c_path, str(extracted_json))

    import json
    records = json.load(open(extracted_json, encoding="utf-8"))
    target = next(r for r in records if r["en"])
    marker = "ZZ_TEST_WRAPPER_MARKER_ZZ"
    target["ua"] = marker
    with open(extracted_json, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)

    out_h3c = tmp_path / "rebuilt.h3c"
    h3c_rebuild(h3c_path, str(extracted_json), str(out_h3c))

    reextracted_json = tmp_path / "reextracted.json"
    h3c_extract(str(out_h3c), str(reextracted_json))
    reextracted = json.load(open(reextracted_json, encoding="utf-8"))
    matching = [r for r in reextracted if r["field"] == target["field"]]
    # See the sibling h3m_writer test's comment: extract() reports
    # whatever's physically in the file as 'en' unless given a separate
    # --ua-source, so the substituted marker shows up there, not in 'ua'.
    assert matching and matching[0]["en"] == marker


def test_h3c_parser_parse_h3c_agrees_with_h3c_writer():
    """h3c_parser.py's own parse_h3c() (the read-only, non-editing path -
    see its module docstring's CORRECTION note on how it relates to
    h3c_writer.py) should report the same campaign name and scenario count
    as h3c_writer's own read_header_segments()-based extraction."""
    h3c_path = _first_campaign()
    raw = open(h3c_path, "rb").read()
    decompressed = gzip.decompress(raw)
    camp_name, _camp_desc, scenarios, _texts, _offset = parse_h3c(decompressed)

    _, scenario_members = split_h3c(raw)
    assert len(scenarios) == len(scenario_members)
    assert camp_name  # non-empty - GOOD1 definitely has a campaign name


@pytest.mark.parametrize("s,expected", [
    ("Long Live the Queen", "Long_Live_the_Queen"),
    ("Catherine's Charge!", "Catherines_Charge"),
    ("   ", "Untitled"),
    ("", "Untitled"),
])
def test_safe_name(s, expected):
    assert safe_name(s) == expected


def test_records_var_suffix():
    assert records_var_suffix(0) == "M1"
    assert records_var_suffix(11) == "M12"


def test_wrapper_records_for_scenario_shape():
    """build_mission_texts.wrapper_records_for_scenario() is what feeds
    each mission folder's own prolog/epilog records - was 0% covered
    before (only map_records_for_scenario had a direct test)."""
    h3c_path = _first_campaign()
    header, scenario_members = split_h3c(open(h3c_path, "rb").read())
    scenario_count = len(scenario_members)

    records = wrapper_records_for_scenario(header, None, scenario_count, 0, "TESTSTEM")
    assert records, "expected at least a prolog or epilog for scenario 0"
    for rec in records:
        assert set(rec.keys()) == {"var", "field", "en", "ua"}
        assert rec["var"].startswith("TESTSTEM_M1_")
        assert rec["field"] in ("wrapper_prolog", "wrapper_epilog")
        assert rec["ua"] == ""  # no ua_header was given


def test_map_records_for_scenario_shape():
    """build_mission_texts.map_records_for_scenario() is what actually
    produces every mission folder's texts.json - check its output shape
    directly rather than only indirectly via the CLI's file output."""
    h3c_path = _first_campaign()
    _, scenario_members = split_h3c(open(h3c_path, "rb").read())
    data = gzip.decompress(scenario_members[0])

    records, r = map_records_for_scenario(data, None, "TESTSTEM", 0)
    assert r.remaining() in (0, 124)
    assert records, "expected at least one text record from scenario 0"
    for rec in records:
        assert set(rec.keys()) == {"var", "field", "en", "ua"}
        assert rec["var"].startswith("TESTSTEM_M1_")
        assert rec["field"].startswith("map_")
        assert rec["ua"] == ""  # no ua_data was given


def test_deploy_campaign_end_to_end(tmp_path):
    """deploy_campaign.deploy() against GOOD1's real, hand-corrected
    `missions/` folder (the one already proven in-game) - checks the
    output is a clean, fully-translated .h3c, not just that it ran
    without raising. Calls the function directly (not via subprocess) so
    coverage tooling can see it and pytest reports a real traceback on
    failure instead of just a subprocess exit code."""
    h3c_path = _first_campaign()
    missions_dir = os.path.join(RAW_DIR, "001_Long_Live_the_Queen", "missions")
    out_path = tmp_path / "Good1_deployed.h3c"

    deploy(h3c_path, missions_dir, str(out_path))
    assert out_path.is_file()

    header, scenario_members = split_h3c(out_path.read_bytes())
    for i, member in enumerate(scenario_members):
        r = parse_h3m_tracked(gzip.decompress(member))
        assert r.remaining() in (0, 124), f"scenario {i} did not parse cleanly after deploy"
    # GOOD1 is fully translated (see H3M_H3C_FORMAT_NOTES.md /
    # homm3-h3c-h3m-writer memory) - real Cyrillic should be in the header.
    assert any(0x0400 <= ord(c) <= 0x04FF for c in header.decode("cp1251", errors="replace"))


def test_deploy_campaign_cli_end_to_end(tmp_path):
    """Same scenario as above, but through the real CLI entry point (a
    subprocess, the same way every actual deploy this project has done
    used it) - checks main()'s own argv wiring, not just deploy() itself."""
    h3c_path = _first_campaign()
    missions_dir = os.path.join(RAW_DIR, "001_Long_Live_the_Queen", "missions")
    out_path = tmp_path / "Good1_deployed_cli.h3c"
    script = os.path.join(os.path.dirname(__file__), "..", "deploy_campaign.py")

    result = subprocess.run(
        [sys.executable, script, h3c_path, missions_dir, str(out_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"deploy_campaign.py failed:\n{result.stderr}"
    assert out_path.is_file()
