"""
HoMM3 .h3m/.h3c structural parser and writer - the real, byte-field-
accurate replacement for the old heuristic string-scan pipeline
(../003_extract_campaigns.py). See H3M_H3C_FORMAT_NOTES.md and
../README.md's "h3_parser/" section for the full story.

Design note - why this package exists ALONGSIDE per-file sys.path hacks,
not instead of them: every .py file in this folder is also meant to be run
directly as a standalone script (`python h3m_writer.py extract ...`, per
each file's own Usage docstring) - that has been this project's actual,
heavily-used, in-game-verified way of running these tools all along, and
changing it to rely on relative imports (`from .h3c_writer import ...`)
would break every one of those direct invocations (a relative import
raises "attempted relative import with no known parent package" when its
module is executed directly as __main__, not imported). So each module
keeps its own `sys.path.insert(0, os.path.dirname(...))` + plain
`from h3c_writer import ...` for that case - this file adds the OTHER,
missing capability: something outside this folder (this project's own
pytest suite, or any future tool) can now do a normal
`from h3_parser import h3m_parser` / `import h3_parser` without needing
any sys.path manipulation of its own, because this directory is now a
real Python package. Both import styles reach the exact same module
objects; neither is a fallback for the other.

Re-exports the small, stable public surface most callers actually need,
so `from h3_parser import parse_h3m, H3Error` works without knowing which
submodule each name lives in:
"""
from .h3c_parser import find_next_h3m_name, parse_h3c
from .h3c_writer import (
    compress_h3_gzip,
    patch_h3m_sizes,
    read_header_segments,
    split_h3c,
)
from .h3c_writer import (
    extract as extract_h3c_wrapper,
)
from .h3c_writer import (
    rebuild as rebuild_h3c_wrapper,
)
from .h3m_parser import (
    TEXT_ENCODING,
    FixedSegment,
    H3Error,
    H3mSizeSegment,
    HeaderStructureError,
    ImplausibleCountError,
    ImplausibleLengthError,
    ParseError,
    PstrSegment,
    R,
    Segment,
    UnknownFieldValueError,
    parse_h3m,
    rebuild_from_segments,
)
from .h3m_writer import (
    extract as extract_h3m_scenario,
)
from .h3m_writer import (
    parse_h3m_tracked,
)
from .h3m_writer import (
    rebuild as rebuild_h3m_scenario,
)

__all__ = [
    "TEXT_ENCODING",
    "FixedSegment",
    "H3Error",
    "H3mSizeSegment",
    "HeaderStructureError",
    "ImplausibleCountError",
    "ImplausibleLengthError",
    "ParseError",
    "PstrSegment",
    "R",
    "Segment",
    "UnknownFieldValueError",
    "compress_h3_gzip",
    "extract_h3c_wrapper",
    "extract_h3m_scenario",
    "find_next_h3m_name",
    "parse_h3c",
    "parse_h3m",
    "parse_h3m_tracked",
    "patch_h3m_sizes",
    "read_header_segments",
    "rebuild_from_segments",
    "rebuild_h3c_wrapper",
    "rebuild_h3m_scenario",
    "split_h3c",
]
