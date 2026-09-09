"""
Regression suite for h3_parser: turns the ad-hoc scratchpad checks that
found every bug documented in H3M_H3C_FORMAT_NOTES.md (the AB/SoD
has_ai bug, the SoD hero-settings interleaving bug, the apostrophe-in-
filename regex bug, FINAL's preconditions-bitmask bug, the campaign_epilogue
gap, the h3m_size staleness bug) into something that lives in git and
catches a REGRESSION of any of them automatically, instead of relying on
someone remembering to re-run a one-off script by hand.

Run with:
    cd 002_TOOLS/scripts/h3_parser
    python -m pytest tests/ -v

Needs the real game install for the two `requires_game` tests (path from
the HOMM3_GAME_DIR env var, default "F:/Games/HoMM 3 Complete" - see
conftest.py) - they're skipped automatically if that path doesn't exist,
so this suite still runs (partially) on a machine without the game
installed, e.g. in CI. The campaign tests only need this repo's own
005_RAW/ copies, no external install required.
"""
import glob
import gzip
import os

import pytest
from conftest import MAPS_DIR, RAW_DIR
from h3c_writer import extract as h3c_extract
from h3c_writer import rebuild as h3c_rebuild
from h3c_writer import split_h3c
from h3m_writer import parse_h3m_tracked


def _discover_campaigns():
    """Every top-level EN campaign .h3c under 005_RAW/<NNN>_<Name>/ (skips
    our own '*_UA.h3c' output files - those get their own, separate test).
    Out: list of (campaign_folder_name, h3c_path) sorted by folder name."""
    found = []
    for h3c_path in glob.glob(os.path.join(RAW_DIR, "*", "*.h3c")):
        if h3c_path.lower().endswith("_ua.h3c"):
            continue
        folder = os.path.basename(os.path.dirname(h3c_path))
        found.append((folder, h3c_path))
    return sorted(found)


def _discover_translated_outputs():
    """Out: list of (campaign_folder_name, h3c_path) for every already-
    deployed '*_UA.h3c' this project has produced (008_Armageddons_Blade
    onward, per deploy_campaign.py) - these get a lighter check (clean
    parse only, no wrapper no-op comparison, since they're deliberately
    NOT identical to the EN original)."""
    found = []
    for h3c_path in glob.glob(os.path.join(RAW_DIR, "*", "*_UA.h3c")):
        folder = os.path.basename(os.path.dirname(h3c_path))
        found.append((folder, h3c_path))
    return sorted(found)


CAMPAIGNS = _discover_campaigns()
TRANSLATED_OUTPUTS = _discover_translated_outputs()


@pytest.mark.parametrize("folder,h3c_path", CAMPAIGNS, ids=[c[0] for c in CAMPAIGNS])
def test_campaign_scenarios_parse_clean(folder, h3c_path):
    """Every scenario in every campaign must fully parse (h3m_parser
    consumes the whole decompressed map, remaining is 0 or the known
    124-byte HD-Edition pad) - this is the check that would have caught
    every h3m_parser.py bug found this project (has_ai gating, hero-
    settings interleaving, FINAL's bitmask) if it had existed sooner."""
    raw = open(h3c_path, "rb").read()
    _, scenario_members = split_h3c(raw)
    assert len(scenario_members) > 0, f"{folder}: no scenario members found"
    for i, member in enumerate(scenario_members):
        data = gzip.decompress(member)
        r = parse_h3m_tracked(data)
        assert r.remaining() in (0, 124), (
            f"{folder} scenario {i}: parse did not end cleanly "
            f"(consumed {r.p}/{len(data)}, remaining={r.remaining()})"
        )


@pytest.mark.parametrize("folder,h3c_path", CAMPAIGNS, ids=[c[0] for c in CAMPAIGNS])
def test_wrapper_noop_roundtrip_is_byte_identical(folder, h3c_path, tmp_path):
    """extract() then rebuild() with no actual translations applied must
    reproduce the original decompressed header byte-for-byte - this is
    the check that would have caught the apostrophe-in-filename regex bug
    (find_next_h3m_name silently failing to find "Oblivion's Edge.h3m")
    and the FINAL preconditions-bitmask bug (both broke BEFORE getting to
    a byte-comparison - read_header_segments() would raise first - but a
    successful run whose OUTPUT doesn't match the input is exactly the
    class of bug this guards against for any future change to
    read_header_segments)."""
    out_json = tmp_path / "wrapper.json"
    out_h3c = tmp_path / "rebuilt.h3c"
    h3c_extract(h3c_path, str(out_json))
    h3c_rebuild(h3c_path, str(out_json), str(out_h3c))

    orig_header, _ = split_h3c(open(h3c_path, "rb").read())
    new_header, _ = split_h3c(open(out_h3c, "rb").read())
    assert new_header == orig_header, f"{folder}: no-op wrapper rebuild changed the header bytes"


@pytest.mark.parametrize("folder,h3c_path", TRANSLATED_OUTPUTS, ids=[c[0] for c in TRANSLATED_OUTPUTS])
def test_translated_output_scenarios_parse_clean(folder, h3c_path):
    """Every already-deployed '*_UA.h3c' (the actual files injected into
    the live game) must still fully parse - guards against a future edit
    to a mission's texts.json plus a re-run of deploy_campaign.py silently
    producing a broken file (e.g. a hand-typed 'ua' value containing
    something that trips up re-encoding)."""
    raw = open(h3c_path, "rb").read()
    _, scenario_members = split_h3c(raw)
    for i, member in enumerate(scenario_members):
        data = gzip.decompress(member)
        r = parse_h3m_tracked(data)
        assert r.remaining() in (0, 124), (
            f"{folder} (translated) scenario {i}: parse did not end cleanly "
            f"(remaining={r.remaining()})"
        )


def _discover_standalone_maps():
    if not os.path.isdir(MAPS_DIR):
        return []
    return sorted(glob.glob(os.path.join(MAPS_DIR, "*.h3m")))


STANDALONE_MAPS = _discover_standalone_maps()


@pytest.mark.skipif(not STANDALONE_MAPS, reason="game install / Maps folder not found (set HOMM3_GAME_DIR)")
@pytest.mark.parametrize("map_path", STANDALONE_MAPS, ids=[os.path.basename(m) for m in STANDALONE_MAPS])
def test_standalone_map_parses_clean(map_path):
    """Every standalone (non-campaign) .h3m the game ships must fully
    parse too - this is the corpus that originally validated h3m_parser.py
    (RoE/AB/SoD formats) before the campaign-specific bugs were found, and
    it's the test most likely to catch a regression from a future change
    that "fixes" something for campaigns but breaks it for plain maps."""
    raw = open(map_path, "rb").read()
    data = gzip.decompress(raw)
    r = parse_h3m_tracked(data)
    assert r.remaining() in (0, 124), (
        f"{os.path.basename(map_path)}: parse did not end cleanly "
        f"(remaining={r.remaining()})"
    )


def test_discovered_all_20_campaigns():
    """Sanity check on the test suite's own discovery, not on h3_parser
    itself: catches a future accidental deletion/move of a campaign's
    005_RAW folder silently shrinking test coverage instead of failing."""
    assert len(CAMPAIGNS) == 20, (
        f"expected 20 campaign .h3c files under {RAW_DIR}, found {len(CAMPAIGNS)}: "
        f"{[c[0] for c in CAMPAIGNS]}"
    )
