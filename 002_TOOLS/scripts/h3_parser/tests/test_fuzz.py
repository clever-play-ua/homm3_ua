"""
Robustness fuzz test: this project's whole existence is reverse-engineered
binary parsing, which this session's own history shows is genuinely easy
to get subtly wrong (the AB/SoD has_ai bug, FINAL's preconditions bitmask,
the h3m_size staleness bug - see H3M_H3C_FORMAT_NOTES.md). All of those
were found by a human noticing wrong BEHAVIOR (missing heroes, a crash),
not by the parser failing loudly and clearly. This test targets a
DIFFERENT, complementary property: given deliberately corrupted bytes (not
a real, valid-but-differently-shaped map - that's what test_roundtrip.py's
large real-file corpus already covers), the parser must never hang, never
exhaust memory, and never raise anything outside this project's own
H3Error hierarchy - it should fail cleanly and identifiably, the same way
a corrupted/truncated file a user actually hands it one day would.

This test is deterministic (fixed seed) - a failure here is 100%
reproducible by re-running it, not a flaky one-in-a-while flake.

Skipped automatically if the game isn't installed (same convention as
test_roundtrip.py's standalone-map tests).
"""
import glob
import gzip
import os
import random

import pytest
from conftest import MAPS_DIR
from h3m_parser import H3Error
from h3m_writer import parse_h3m_tracked

TRIALS_PER_FILE = 60
MAX_CORRUPTED_BYTES = 6
SEED = 20260906  # fixed - see module docstring on why this must stay deterministic


def _smallest_maps(n: int):
    """Out: the n smallest .h3m paths under MAPS_DIR (by file size) - fuzz
    trials are O(1) each in real time (a fast parse or a fast, bounded-size
    exception - see h3m_parser.MAX_PLAUSIBLE_COUNT / R._require for why
    this is guaranteed rather than hoped-for), but smaller files still
    means less to gzip.decompress() per trial, so this keeps the whole
    suite fast without weakening what it's actually testing (corruption
    can land anywhere in a small file just as well as a large one)."""
    if not os.path.isdir(MAPS_DIR):
        return []
    paths = glob.glob(os.path.join(MAPS_DIR, "*.h3m"))
    paths.sort(key=os.path.getsize)
    return paths[:n]


FUZZ_MAPS = _smallest_maps(5)


def _corrupt(data: bytes, rng: random.Random) -> bytes:
    """In: data (real, valid decompressed .h3m bytes), rng (seeded).
    Out: a mutated copy with 1..MAX_CORRUPTED_BYTES random bytes at random
    positions replaced with random values - simulates a truncated
    download, a bad disk sector, or a hand-edit gone wrong, not a
    different-but-valid map (that's the roundtrip test's job)."""
    mutable = bytearray(data)
    n = rng.randint(1, MAX_CORRUPTED_BYTES)
    for _ in range(n):
        pos = rng.randrange(len(mutable))
        mutable[pos] = rng.randrange(256)
    return bytes(mutable)


@pytest.mark.skipif(not FUZZ_MAPS, reason="game install / Maps folder not found (set HOMM3_GAME_DIR)")
@pytest.mark.parametrize("map_path", FUZZ_MAPS, ids=[os.path.basename(m) for m in FUZZ_MAPS])
def test_corrupted_map_fails_cleanly_or_not_at_all(map_path):
    original = gzip.decompress(open(map_path, "rb").read())
    rng = random.Random(f"{SEED}:{os.path.basename(map_path)}")

    for trial in range(TRIALS_PER_FILE):
        corrupted = _corrupt(original, rng)
        try:
            r = parse_h3m_tracked(corrupted)
            # A corrupted file CAN still happen to parse "cleanly" (e.g. a
            # mutated byte inside a long text string, or a count field
            # that happened to land on another small-but-valid number) -
            # that's fine, not a bug. What matters is nothing below fired.
            r.remaining()
        except H3Error:
            pass  # exactly the contract: a clean, identifiable failure
        except Exception as e:
            pytest.fail(
                f"{os.path.basename(map_path)} trial {trial}: corrupted input raised "
                f"{type(e).__name__} ({e}) instead of an h3m_parser.H3Error subclass - "
                f"seed={SEED}, reproducible by re-running this test as-is."
            )
