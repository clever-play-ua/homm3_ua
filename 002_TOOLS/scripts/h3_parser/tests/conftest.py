"""
Shared pytest fixtures/config for the h3_parser test suite.

Problem this solves: every test here needs to import h3_parser's modules
(h3m_parser, h3c_writer, h3m_writer) by plain module name (`from h3m_parser
import ...`), the same way the modules import each other - see the "why
these files aren't numbered" note in ../../README.md. That only works if
h3_parser/ itself is on sys.path, which pytest doesn't do automatically
for a tests/ subfolder.
"""
import os
import sys

H3_PARSER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if H3_PARSER_DIR not in sys.path:
    sys.path.insert(0, H3_PARSER_DIR)

REPO_ROOT = os.path.abspath(os.path.join(H3_PARSER_DIR, "..", "..", ".."))
RAW_DIR = os.path.join(REPO_ROOT, "005_RAW")

# Overridable via env var so this suite can run against a different game
# install without editing the file (matches every top-level script's own
# --game default of "F:/Games/HoMM 3 Complete").
GAME_DIR = os.environ.get("HOMM3_GAME_DIR", "F:/Games/HoMM 3 Complete")
MAPS_DIR = os.path.join(GAME_DIR, "Maps")
