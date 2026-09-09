#!/usr/bin/env python3
"""
Structural (byte-field-accurate, not heuristic) parser for HoMM3 .h3m map
files - RoE/AB/SoD formats. Every field layout here was verified against the
homm3tools h3mlib C source (see ../reference/), not just prose docs, after
the prose docs (h3m-The-Corpus.txt) turned out to describe the player struct
incorrectly.

Validated: 150/151 real fan .h3m maps parse to a clean end (0 or 124
trailing bytes - 124 is the known "HD Edition padding" seen in the original
C source). The one known failure (Marshland Menace.h3m) has a still-unexplained
drift inside the SoD hero_settings[156] block; see H3M_H3C_FORMAT_NOTES.md.

Usage as a library:
    from h3m_parser import parse_h3m
    r, fmt, texts, obj_count, event_count = parse_h3m(decompressed_bytes)
    # r.remaining() should be 0 or 124 if the parse is clean
    # texts is a list of (label, raw_bytes) - decode with cp1252 (EN) / cp1251 (UA)

See H3M_H3C_FORMAT_NOTES.md in this folder for the full story, known gaps,
and how to resume this work.
"""
import struct
from typing import NamedTuple

# The single encoding every text field in .h3m/.h3c binary data is decoded
# with in this project, REGARDLESS of which language it holds. This is not
# a shortcut: cp1251 (Windows Cyrillic) is a strict superset of ASCII, so
# it decodes plain English text identically to cp1252 (Windows Western) -
# every byte actually used in this project's English source files is
# ASCII, so there is no real EN/UA encoding split to make here (unlike the
# flat LOD *.TXT files' own pipeline in 002_TOOLS/scripts/002_build_raw.py
# etc, where EN and UA genuinely are two different physical files in two
# different encodings, and that split matters).
TEXT_ENCODING = 'cp1251'

# Upper bound on any length-prefixed COUNT this parser reads (list/table
# entry counts, e.g. object count, event count, heroes_count) - NOT on
# pstr's own string length (see ImplausibleLengthError below, which has
# its own, much larger bound already). A corrupted or truncated file can
# make a count field decode to a huge number (up to 2^32-1); looping that
# many times before hitting real data (or the end of the buffer) can take
# effectively forever - this bound turns that into an immediate, clear
# error instead. 100,000 is generous: no real HoMM3 map has remotely this
# many objects/events/owned heroes in one table.
MAX_PLAUSIBLE_COUNT = 100_000


class H3Error(ValueError):
    """Base class for every error this project's parser/writers raise.
    Subclasses ValueError (not a fresh Exception) so any existing
    `except ValueError` in older code (this project's own history
    included) keeps working unchanged - this hierarchy only ADDS the
    ability to catch something more specific than "some ValueError
    happened somewhere in a parse."""


class ParseError(H3Error):
    """The byte stream didn't match what this parser expected at some
    position. In this project's experience so far, this has always meant
    the reader position already desynced somewhere upstream (a genuine
    parser bug - see H3M_H3C_FORMAT_NOTES.md for several examples found
    this way), not that the input file itself is corrupt - but a
    corrupted/truncated/hand-edited file would raise the same way, which
    is the intended, safe behavior either way."""


class ImplausibleLengthError(ParseError):
    """A pstr()'s uint32 length prefix decoded to a value past the sanity
    ceiling (see R.pstr()) - almost always a desynced read position."""


class ImplausibleCountError(ParseError):
    """A list/table count field (object count, event count, heroes_count,
    rumors_count, ...) decoded past MAX_PLAUSIBLE_COUNT - see that
    constant's docstring for why this is checked at all."""


class UnknownFieldValueError(ParseError):
    """A typed/enum-like field (object class, win/lose condition type,
    meta_type, reward_type) held a value this parser has no case for -
    either a genuinely new map feature this parser hasn't been taught
    about yet, or (far more often historically) a desynced read position
    landing on the wrong byte entirely."""


class HeaderStructureError(ParseError):
    """h3c_writer.py-specific: the .h3c wrapper's own container structure
    (gzip member boundaries, the header block's expected field sequence)
    didn't match what read_header_segments()/split_h3c() expect - e.g. no
    gzip member found at all, a scenario's filename search came up empty,
    or the header's fields didn't add up to exactly its own known
    decompressed length. See H3M_H3C_FORMAT_NOTES.md - several of this
    project's hardest bugs looked exactly like this before being found."""


def _check_count(n: int, what: str) -> int:
    """Guard called right after reading any list/table count field. In: n
    (the count just read), what (a short label for the error message, e.g.
    'heroes_count'). Out: n unchanged, for `count = _check_count(r.u32(),
    ...)`-style one-liners. Raises ImplausibleCountError if n exceeds
    MAX_PLAUSIBLE_COUNT - see that constant's docstring."""
    if n > MAX_PLAUSIBLE_COUNT:
        raise ImplausibleCountError(f"implausible {what} {n} (> {MAX_PLAUSIBLE_COUNT})")
    return n


class FixedSegment(NamedTuple):
    """An opaque byte span - copied verbatim on rebuild, never substituted.
    Still a plain 3-tuple under the hood (NamedTuple IS a tuple), so every
    existing `kind, start, end = seg` / `_, s, e = seg` unpacking call site
    elsewhere in this project keeps working unchanged - this only adds
    `.kind`/`.start`/`.end` attribute access and a real type for readers/
    type-checkers on top, it changes no behavior."""
    kind: str  # always 'fixed'
    start: int
    end: int


class PstrSegment(NamedTuple):
    """A length-prefixed string span, substitutable by `label` on rebuild
    (see h3m_writer.rebuild_map_bytes / h3m_parser.rebuild_from_segments).
    Also a plain tuple - see FixedSegment's note."""
    kind: str  # always 'pstr'
    label: str
    start: int
    end: int


class H3mSizeSegment(NamedTuple):
    """h3c_writer.py-only: marks one scenario's `h3m_size` field so
    h3c_writer.patch_h3m_sizes() can find and correct it without a second
    parse. h3m_parser.py itself never produces this kind - only
    h3c_writer.read_header_segments() does, for the .h3c WRAPPER header,
    not for map bodies."""
    kind: str  # always 'h3m_size'
    scenario_idx: int
    start: int
    end: int


Segment = FixedSegment | PstrSegment | H3mSizeSegment

# Every parse_* function below appends to a shared list of this shape as it
# finds translatable text - (label, raw_undecoded_bytes) pairs, in the
# order encountered. Decode with cp1251 for Ukrainian, cp1252 for English.
TextsList = list[tuple[str, bytes]]


def rebuild_from_segments(data: bytes, segments: list[Segment],
                           replacements: dict, encoding: str = TEXT_ENCODING) -> bytes:
    """Shared core of every "rebuild bytes from a segment list" operation
    in this project (h3c_writer.rebuild() and h3m_writer.rebuild_map_bytes()
    both used to duplicate this loop separately - factored out here so the
    two can't quietly drift apart). Walks segments once, in order:
    'fixed' spans are copied verbatim; 'pstr' spans are replaced with
    `replacements[label]` (re-encoded with its own fresh 4-byte length
    prefix) when that label has a non-empty entry, else also copied
    verbatim; 'h3m_size' spans (only ever appear in h3c_writer.py's usage,
    never here) are always copied verbatim - patch_h3m_sizes() corrects
    those separately, after the real member sizes are known.
    In: data (the original bytes the segments' start/end offsets index
    into), segments (a list from R(track=True) or
    h3c_writer.read_header_segments - anything shaped like Segment above),
    replacements ({label: new_text} - a missing key or falsy value means
    "keep the original"), encoding (cp1251 for Ukrainian - the only
    encoding this project's writers have ever needed; pass cp1252 if you
    genuinely need to write English back out unchanged-but-reserialized).
    Out: the fully reassembled bytes - same total structure as data, with
    only the substituted pstr spans changed in length."""
    out = bytearray()
    for seg in segments:
        # isinstance, not `seg[0] == 'fixed'` string comparison: since
        # Segment is a Union of three differently-shaped NamedTuples,
        # isinstance is what lets a type-checker (mypy) actually narrow
        # which one `seg` is in each branch below, instead of flagging
        # every positional unpack as "might be the wrong shape."
        if isinstance(seg, (FixedSegment, H3mSizeSegment)):
            out += data[seg.start:seg.end]
        else:  # PstrSegment
            replacement = replacements.get(seg.label)
            if replacement:
                encoded = replacement.encode(encoding, errors='replace')
                out += struct.pack('<I', len(encoded)) + encoded
            else:
                out += data[seg.start:seg.end]
    return bytes(out)


class R:
    """Reader for the h3m binary format. Optionally tracks every byte it
    reads as a Segment (FixedSegment/PstrSegment, see above) in
    self.segments. Pass track=True to enable this (used by h3m_writer.py
    for editing map text in place; plain reads via h3m_parser.py's own
    CLI/tests don't need it and leave it off to avoid the bookkeeping cost)."""
    def __init__(self, data: bytes, track: bool = False):
        self.d = data
        self.p = 0
        self.track = track
        self.segments: list[Segment] | None = [] if track else None

    def _fixed(self, start: int) -> None:
        """Internal: if tracking, records [start, self.p) as an opaque
        FixedSegment. In: start (byte offset before the read that just
        happened). Out: None (mutates self.segments)."""
        if self.track and self.p > start:
            assert self.segments is not None  # true whenever self.track is - see __init__
            self.segments.append(FixedSegment('fixed', start, self.p))

    def _require(self, n: int) -> None:
        """Bounds check called at the top of every primitive read below.
        In: n (bytes about to be read from the current position). Out:
        None. Raises ParseError if fewer than n bytes remain - without
        this, a truncated/corrupted file's reads would eventually hit a
        raw builtin IndexError (single-byte indexing) or silently return
        SHORT data (bytes slicing never raises, it just truncates - the
        one gap a bare `try/except IndexError` wouldn't have caught
        either), neither of which is part of this project's H3Error
        hierarchy and both of which a caller has no clean way to catch
        specifically. Found by writing a fuzz test (tests/test_fuzz.py)
        that deliberately corrupts real files - this bounds check is what
        that test verifies never regresses."""
        if self.p + n > len(self.d):
            raise ParseError(
                f"unexpected end of data: need {n} byte(s) at offset {self.p}, "
                f"only {len(self.d) - self.p} remain")

    def u8(self) -> int:
        """In: nothing (reads from current position). Out: int 0-255;
        advances position by 1 byte."""
        self._require(1)
        start = self.p
        v = self.d[self.p]; self.p += 1
        self._fixed(start); return v

    def i8(self) -> int:
        """Out: signed int -128..127; advances position by 1 byte."""
        self._require(1)
        start = self.p
        v = struct.unpack_from('<b', self.d, self.p)[0]; self.p += 1
        self._fixed(start); return v

    def u16(self) -> int:
        """Out: int 0-65535, little-endian; advances position by 2 bytes."""
        self._require(2)
        start = self.p
        v = struct.unpack_from('<H', self.d, self.p)[0]; self.p += 2
        self._fixed(start); return v

    def u32(self) -> int:
        """Out: int 0-2^32-1, little-endian; advances position by 4 bytes."""
        self._require(4)
        start = self.p
        v = struct.unpack_from('<I', self.d, self.p)[0]; self.p += 4
        self._fixed(start); return v

    def i32(self) -> int:
        """Out: signed 32-bit int, little-endian; advances position by 4 bytes."""
        self._require(4)
        start = self.p
        v = struct.unpack_from('<i', self.d, self.p)[0]; self.p += 4
        self._fixed(start); return v

    def bytes_(self, n: int) -> bytes:
        """In: n (byte count). Out: raw bytes object of that length;
        advances position by n."""
        self._require(n)
        start = self.p
        v = self.d[self.p:self.p+n]; self.p += n
        self._fixed(start); return v

    def pstr(self, label: str | None = None) -> bytes:
        """Reads a Pascal-style string: uint32 length prefix + that many
        raw bytes (the format's universal text encoding - see module
        docstring for which cp125x to decode with). In: label (optional -
        when tracking, tags this span 'pstr' with this name instead of
        lumping it into an opaque 'fixed' span; every text-producing call
        site in this file passes one, e.g. 'map_name', 'obj16_town_name').
        Out: raw bytes (NOT decoded - caller decides cp1251 vs cp1252);
        advances position by 4+len(bytes). Raises ValueError if the length
        prefix reads back implausibly large (>200000) - almost always means
        the reader position already desynced upstream, not a genuinely
        huge string."""
        start = self.p
        n = self.u32()  # NOTE: this already records a 'fixed' segment for
        # the length prefix itself via u32() above when tracking - harmless
        # (rebuild just needs the string segment's OWN start to include the
        # 4-byte prefix, handled below by using `start`, not p-after-u32).
        if self.track:
            assert self.segments is not None  # true whenever self.track is - see __init__
            self.segments.pop()  # undo the u32()-call's own fixed-segment;
            # the pstr segment below covers those same 4 bytes + the string.
        if n > 200000:
            raise ImplausibleLengthError(f"implausible string length {n} at {self.p-4}")
        self._require(n)
        v = self.d[self.p:self.p+n]; self.p += n
        if self.track:
            assert self.segments is not None
            if label:
                self.segments.append(PstrSegment('pstr', label, start, self.p))
            else:
                self.segments.append(FixedSegment('fixed', start, self.p))
        return v

    def peek(self, off: int = 0) -> int | None:
        """Reads one byte WITHOUT advancing position - for the rare
        lookahead-needed spots. In: off (byte offset from current
        position, default 0 = the very next byte). Out: int 0-255, or None
        if that offset is past the end of the buffer."""
        i = self.p + off
        return self.d[i] if i < len(self.d) else None

    def skip(self, n: int) -> None:
        """Advances position by n bytes without interpreting them (still
        recorded as an opaque 'fixed' span when tracking - use this for
        binary data no text pipeline needs to touch). In: n. Out: None.
        Bounds-checked eagerly (like every other primitive here) so a
        corrupted/truncated file fails right where the bad skip happened,
        not confusingly at some unrelated later read."""
        self._require(n)
        start = self.p
        self.p += n
        self._fixed(start)

    def remaining(self) -> int:
        """Out: int - bytes left unread between the current position and
        the end of the buffer. Should be 0 or 124 (the known "HD Edition
        padding") after a fully clean parse_h3m() - anything else means
        the parse desynced somewhere."""
        return len(self.d) - self.p


FORMAT_ROE = 0x0E
FORMAT_AB = 0x15
FORMAT_SOD = 0x1C

# Named sizes for the otherwise-bare r.skip(N) calls in parse_ai_section()
# that have bitten this project before (a hardcoded-looking constant that
# turns out to vary, or an easy-to-lose-count-of block) - giving them
# names makes a future format quirk (like FINAL's preconditions bitmask
# in h3c_writer.py) easier to spot by inspection instead of only by
# re-deriving the byte math from scratch again.
TEAM_ASSIGNMENTS_SIZE = 8         # 1 byte/player, only present if teams_count != 0
AVAILABLE_HEROES_SIZE_ROE = 16    # bitmask, 1 bit per HOTRAITS.TXT entry
AVAILABLE_HEROES_SIZE_ABSOD = 20  # AB/SoD added more hero slots -> wider bitmask
AI_SECTION_RESERVED_BYTES = 31    # asserted to be all-zero in the original C source
AB_TAIL_PADDING = 17              # AB-format-only bytes after the reserved block
SOD_TAIL_PADDING = 18             # SoD equivalent of AB_TAIL_PADDING
SOD_AVAILABLE_SPELLS_SIZE = 9     # bitmask, 1 bit per SPTRAITS.TXT entry
SOD_AVAILABLE_SKILLS_SIZE = 4     # bitmask, 1 bit per SSTRAITS.TXT entry
SOD_HERO_SETTINGS_COUNT = 156     # fixed-size table, 1 entry per hero type, SoD only


def is_ab_or_sod(fmt: int) -> bool:
    """In: a format byte read from the map header (FORMAT_ROE/AB/SOD).
    Out: bool - True unless it's exactly RoE (AB and SoD share most of the
    extra fields RoE lacks, so most call sites only need this coarse split)."""
    return fmt != FORMAT_ROE

def is_sod(fmt: int) -> bool:
    """In: a format byte. Out: bool - True for SoD (and any hypothetical
    later format sharing its numeric value or above)."""
    return fmt >= FORMAT_SOD


# ---------------------------------------------------------------- header ---

def parse_header(r: R, texts: TextsList) -> tuple[int, int, int]:
    """Reads the map's fixed opening header (format, playability flag, map
    size, over/underground flag, name, description, difficulty, and - for
    AB/SoD - the hero experience level cap).
    In: r (positioned at byte 0), texts (list to append (label, raw_bytes)
    text finds into - here: 'map_name', 'map_desc').
    Out: (fmt, map_size, has_two_levels) - all three are needed by later
    sections (fmt gates almost every conditional field in this file;
    map_size/has_two_levels size the tile grid in parse_tiles)."""
    fmt = r.u32()
    r.u8()  # is_playable
    map_size = r.u32()
    has_two_levels = r.u8()
    name = r.pstr('map_name'); texts.append(('map_name', name))
    desc = r.pstr('map_desc'); texts.append(('map_desc', desc))
    r.u8()  # difficulty
    if is_ab_or_sod(fmt):
        r.u8()  # hero level cap
    return fmt, map_size, has_two_levels


# --------------------------------------------------------------- players ---

def parse_players(r: R, fmt: int, texts: TextsList) -> None:
    """Reads all 8 fixed player slots (red/blue/tan/green/orange/purple/
    teal/pink, always 8 regardless of how many are actually used on the
    map). In: r, fmt, texts (appends 'p{0-7}_hero_name' and
    'p{0-7}_owned_hero_name' text finds). Out: None (advances r in place).
    Verified against homm3tools' h3m_player.h struct layouts (e0..e3 unions)
    AND, critically, h3m_player_ai.h's H3M_PLAYER_AI_ABSOD struct - a
    completely separate per-player block (own hero roster, used for
    campaign hero carry-over) that follows EVERY player's main struct in
    AB/SoD maps, UNCONDITIONALLY - regardless of has_main_town or whether
    that player has a specific (non-0xFF) starting hero type. This was the
    actual root cause of every campaign-embedded AB/SoD scenario failing to
    parse (see "Open issue: AB/SoD campaign player section" in
    H3M_H3C_FORMAT_NOTES.md before this fix - the old code only read this
    block when htype != 0xFF, desyncing the rest of the file the moment a
    player without a specific starting hero still owned carried-over
    heroes, which is exactly what happens after finishing an earlier
    scenario in a multi-map campaign)."""
    absod = is_ab_or_sod(fmt)
    for pid in range(8):
        r.u8()  # can_human
        r.u8()  # can_computer
        r.u8()  # behavior
        if is_sod(fmt):
            r.u8()  # allowed_alignments
        r.u8()  # town_types
        if absod:
            r.u8()  # town_conflux
        r.u8()  # unknown1 ("random town" flag)
        has_main_town = r.u8()

        if has_main_town == 0:
            r.u8()  # is_random
            htype = r.u8()  # e0: just 2 bytes if 0xFF, RoE and AB/SoD alike
            if htype != 0xFF:
                r.u8()  # face
                name = r.pstr(f'p{pid}_hero_name')
                if name: texts.append((f'p{pid}_hero_name', name))
        else:
            if absod:
                r.u8(); r.u8()  # create_hero, town_type
            r.u8(); r.u8(); r.u8()  # xpos ypos zpos
            r.u8()  # is_random
            htype = r.u8()  # e1: 5 bytes total if 0xFF, RoE and AB/SoD alike
            if htype != 0xFF:
                r.u8()  # face
                name = r.pstr(f'p{pid}_hero_name')
                if name: texts.append((f'p{pid}_hero_name', name))

        if absod:
            r.u8()  # unknown1 (player_ai's own, separate from the one above)
            heroes_count = _check_count(r.u32(), 'heroes_count')
            for _ in range(heroes_count):
                r.u8()  # type
                hname = r.pstr(f'p{pid}_owned_hero_name')
                if hname: texts.append((f'p{pid}_owned_hero_name', hname))


# ---------------------------------------------------------------- AI/etc ---

def parse_win_cond(r: R, fmt: int) -> None:
    """Reads the map's special victory condition, if any (0xFF = none/
    "normal" win, else one of 11 typed condition structs). In: r, fmt (RoE
    has narrower fields for two condition types). Out: None (no text in
    this section; advances r past whichever variant was present)."""
    c = r.u8()
    if c == 0xFF:
        return
    if c == 0x00:  # acquire artifact
        r.u8(); r.u8()
        r.u8() if fmt == FORMAT_ROE else r.u16()
    elif c == 0x01:  # accumulate creatures
        r.u8(); r.u8()
        (r.u8() if fmt == FORMAT_ROE else r.u16())
        r.u32()
    elif c == 0x02:  # accumulate resources
        r.u8(); r.u8(); r.u8(); r.u32()
    elif c == 0x03:  # upgrade town
        r.u8(); r.u8(); r.u8(); r.u8(); r.u8(); r.u8(); r.u8()
    elif c in (0x04, 0x05, 0x06, 0x07):  # build grail/defeat hero/capture town/defeat monster
        r.u8(); r.u8(); r.u8(); r.u8(); r.u8()
    elif c in (0x08, 0x09):  # flag dwellings/mines
        r.u8(); r.u8()
    elif c == 0x0A:  # transport artifact
        r.u8(); r.u8(); r.u8(); r.u8(); r.u8(); r.u8()
    else:
        raise UnknownFieldValueError(f"unhandled win_cond_type {c}")


def parse_lose_cond(r: R) -> None:
    """Reads the map's special loss condition, if any (0xFF = none, else
    lose-town/lose-hero/time-limit). In: r. Out: None (no text; advances r)."""
    c = r.u8()
    if c == 0xFF:
        return
    if c in (0x00, 0x01):  # lose town / lose hero
        r.u8(); r.u8(); r.u8()
    elif c == 0x02:  # time
        r.u16()
    else:
        raise UnknownFieldValueError(f"unhandled lose_cond_type {c}")


def parse_ai_section(r: R, fmt: int, texts: TextsList) -> None:
    """Reads the big "everything else about how the AI/map plays" block:
    win/lose conditions, teams, the 20-byte available-heroes bitmask,
    AB/SoD placeholder-hero list, SoD custom-hero definitions, 31 reserved
    bytes, format-specific padding, the rumor list, and (SoD only) the
    156-entry per-hero customization table (experience/skills/artifacts/
    biography/gender/spells/primary-skills - see the inline comment on why
    each entry's fields must be read interleaved with their own flags, not
    all 7 flags up front).
    In: r, fmt, texts (appends 'custom_hero_name', 'rumor{i}_name',
    'rumor{i}_desc', 'hero_bio' text finds). Out: None (advances r)."""
    parse_win_cond(r, fmt)
    parse_lose_cond(r)

    teams_count = r.u8()
    if teams_count != 0:
        r.skip(TEAM_ASSIGNMENTS_SIZE)

    r.skip(AVAILABLE_HEROES_SIZE_ABSOD if is_ab_or_sod(fmt) else AVAILABLE_HEROES_SIZE_ROE)

    if is_ab_or_sod(fmt):
        placeholder_count = _check_count(r.u32(), 'placeholder_count')
        r.skip(placeholder_count)  # 1 byte (hero type) each

    if is_sod(fmt):
        custom_heroes_count = r.u8()
        for _ in range(custom_heroes_count):
            r.u8(); r.u8()  # type, face
            name = r.pstr('custom_hero_name')
            if name: texts.append(('custom_hero_name', name))
            r.u8()  # allowed_players

    r.skip(AI_SECTION_RESERVED_BYTES)

    if fmt == FORMAT_AB:
        r.skip(AB_TAIL_PADDING)
    elif is_sod(fmt):
        r.skip(SOD_TAIL_PADDING)
        r.skip(SOD_AVAILABLE_SPELLS_SIZE)
        r.skip(SOD_AVAILABLE_SKILLS_SIZE)

    rumors_count = _check_count(r.u32(), 'rumors_count')
    for ridx in range(rumors_count):
        name = r.pstr(f'rumor{ridx}_name')
        if name: texts.append((f'rumor{ridx}_name', name))
        desc = r.pstr(f'rumor{ridx}_desc')
        if desc: texts.append((f'rumor{ridx}_desc', desc))

    if is_sod(fmt):
        # Each has_X flag is immediately followed by its own payload (if
        # set) before the next flag - NOT 7 flags read up front. Confirmed
        # against reference/h3m_corpus.txt lines 264-313. Reading all flags
        # consecutively (the old, wrong code) only happened to work when
        # every hero's sub-flags were all zero (has_settings=1 just for a
        # name/portrait override) - the moment any hero has a real
        # secondary-skill list, artifact loadout or biography set in the
        # editor, that data has to be consumed right after its own flag or
        # everything after desyncs (this was the GEM/SANDRO/FINAL failure).
        for _ in range(SOD_HERO_SETTINGS_COUNT):
            has_settings = r.u8()
            if not has_settings:
                continue
            has_exp = r.u8()
            if has_exp:
                r.u32()
            has_ss = r.u8()
            if has_ss:
                cnt = r.u32()
                for _ in range(cnt):
                    r.u8(); r.u8()
            has_art = r.u8()
            if has_art:
                r.skip(19 * 2)
                backpack = r.u16()
                r.skip(backpack * 2)
            has_bio = r.u8()
            if has_bio:
                bio = r.pstr('hero_bio')
                if bio: texts.append(('hero_bio', bio))
            r.u8()  # gender
            has_spells = r.u8()
            if has_spells:
                r.skip(9)
            has_ps = r.u8()
            if has_ps:
                r.skip(4)


def parse_tiles(r: R, map_size: int, has_two_levels: int) -> None:
    """Skips the terrain grid wholesale (7 bytes/tile: terrain type,
    texture index, river/road type+direction, mirroring flags - none of it
    is human text, so this project has no reason to decode it further).
    In: r, map_size (width=height, from parse_header), has_two_levels
    (whether there's an underground level too). Out: None (advances r by
    exactly levels*map_size*map_size*7 bytes)."""
    levels = 2 if has_two_levels else 1
    r.skip(levels * map_size * map_size * 7)


def parse_object_attributes(r: R, texts: TextsList) -> list[int]:
    """Reads the map's object-TYPE definitions table (one entry per
    distinct object appearance used anywhere on the map - e.g. "a red
    dragon", "Castle-alignment town" - NOT one per placed object instance;
    see parse_object_details for that). Each entry embeds its own sprite
    (.def) filename length + bytes, which is skipped (not human text).
    In: r, texts (unused - kept for signature symmetry with the other
    parse_* functions, no text lives in this table). Out: list of raw
    object-class integers, one per entry, in table order - the caller maps
    these through CLASS_TO_META before indexing into it from
    parse_object_details (object instances reference this table by
    position, not by class)."""
    count = _check_count(r.u32(), 'object_attributes count')
    attrs = []
    for _ in range(count):
        defsz = r.u32()
        r.skip(defsz)
        r.skip(6); r.skip(6)  # passable, active
        r.u16(); r.u16()  # allowed_landscapes, landscape_group
        object_class = r.u32()
        r.u32()  # object_number
        r.u8()  # object_group
        r.u8()  # above
        r.skip(16)
        attrs.append(object_class)
    return attrs


# ------------------------------------------------------------ meta types ---

(GENERIC_IMPASSABLE, GENERIC_IMPASSABLE_ABSOD, GENERIC_VISITABLE, GENERIC_VISITABLE_ABSOD,
 ARTIFACT, ABANDONED_MINE, DWELLING, EVENT, GARRISON, GARRISON_ABSOD, BOAT,
 PASSABLE_TERRAIN_SOD, PASSABLE_TERRAIN, PANDORAS_BOX, GRAIL, HERO, LIGHTHOUSE,
 MONSTER, OCEAN_BOTTLE, PRISON, QUEST_GUARD, RANDOM_DWELLING, RANDOM_DWELLING_LVL,
 RANDOM_DWELLING_FACTION, RANDOM_HERO, PLACEHOLDER_HERO, RESOURCE, RESOURCE_GENERATOR,
 SCHOLAR, SEERS_HUT, SHIPYARD, SHRINE, SIGN, SPELL_SCROLL, SUBTERRANEAN_GATE, TOWN,
 WITCH_HUT, GENERIC_TREASURE) = range(38)

CLASS_TO_META = {}
for c in (0, 40, 114,115,116,117,118,119,120,121,122,123,126,127,128,129,130,131,132,
          133,134,135,136,137,138,143,147,148,149,150,151,152,153,154,155,156,157,
          158,159,160,161):
    CLASS_TO_META[c] = GENERIC_IMPASSABLE
for c in (165,166,167,168,169,170,171,172,173,174,177,178,179,180,181,182,183,184,
          185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,
          203,204,205,206,207,208,209,210,211):
    CLASS_TO_META[c] = GENERIC_IMPASSABLE_ABSOD
for c in (2,3,4,7,13,11,14,15,16,22,23,24,25,27,28,30,31,32,35,37,38,39,41,
          47,48,49,51,52,55,56,57,58,60,61,64,9,10,78,80,84,85,92,94,95,96,
          97,99,100,102,104,105,106,107,108,109,110,111,112,50,1):
    CLASS_TO_META[c] = GENERIC_VISITABLE
for c in (221,63,212,213,43,44):
    CLASS_TO_META[c] = GENERIC_VISITABLE_ABSOD
for c in (5,65,66,67,68,69):
    CLASS_TO_META[c] = ARTIFACT
CLASS_TO_META[220] = ABANDONED_MINE
for c in (17,18,19,20):
    CLASS_TO_META[c] = DWELLING
CLASS_TO_META[45] = GENERIC_VISITABLE_ABSOD  # two-way monolith, per parse_oa_meta_type.c
CLASS_TO_META[26] = EVENT
CLASS_TO_META[33] = GARRISON
CLASS_TO_META[219] = GARRISON_ABSOD
CLASS_TO_META[8] = BOAT
for c in (124,21,46,125,176,175):
    CLASS_TO_META[c] = PASSABLE_TERRAIN
for c in (222,224,225,226,227,228,229,231,223,230,139,141,142,144,145,146):
    CLASS_TO_META[c] = PASSABLE_TERRAIN_SOD
CLASS_TO_META[6] = PANDORAS_BOX
CLASS_TO_META[36] = GRAIL
CLASS_TO_META[34] = HERO
CLASS_TO_META[42] = LIGHTHOUSE
for c in (54,71,72,73,74,75,162,163,164):
    CLASS_TO_META[c] = MONSTER
CLASS_TO_META[59] = OCEAN_BOTTLE
CLASS_TO_META[62] = PRISON
CLASS_TO_META[215] = QUEST_GUARD
CLASS_TO_META[216] = RANDOM_DWELLING
CLASS_TO_META[217] = RANDOM_DWELLING_LVL
CLASS_TO_META[218] = RANDOM_DWELLING_FACTION
CLASS_TO_META[70] = RANDOM_HERO
CLASS_TO_META[214] = PLACEHOLDER_HERO
for c in (79, 76):
    CLASS_TO_META[c] = RESOURCE
CLASS_TO_META[53] = RESOURCE_GENERATOR
CLASS_TO_META[81] = SCHOLAR
CLASS_TO_META[83] = SEERS_HUT
CLASS_TO_META[87] = SHIPYARD
for c in (88, 89, 90):
    CLASS_TO_META[c] = SHRINE
CLASS_TO_META[91] = SIGN
CLASS_TO_META[93] = SPELL_SCROLL
CLASS_TO_META[103] = SUBTERRANEAN_GATE
for c in (98, 77):
    CLASS_TO_META[c] = TOWN
CLASS_TO_META[113] = WITCH_HUT
for c in (12,29,82,86,101):
    CLASS_TO_META[c] = GENERIC_TREASURE
for c in (221, 63, 212, 213):
    CLASS_TO_META[c] = GENERIC_VISITABLE_ABSOD


# -------------------------------------------------------------- quest ext ---

def parse_ext_quest(r: R, quest_type: int, texts: TextsList, ctx_name: str) -> None:
    """Reads one "extended quest" body - the mission-requirement details
    attached to a Quest Guard or (AB/SoD) Seer's Hut object - plus its 3
    dialogue strings (shown at "not done yet", "in progress", "done").
    In: r, quest_type (0=none/skip type-specific fields but still read
    deadline+messages, 1-9=experience/primary-skills/defeat-hero/
    defeat-monster/artifacts/creatures/resources/be-hero/be-player), texts,
    ctx_name (e.g. 'obj42' - prefixes the emitted labels so multiple quest
    objects on one map don't collide). Out: None (appends
    '{ctx_name}_quest_proposal/_progress/_completion' text finds, advances r)."""
    if quest_type == 0x01:  # experience
        r.u32()
    elif quest_type == 0x02:  # primary skills
        r.skip(4)
    elif quest_type == 0x03:  # defeat hero
        r.u32()
    elif quest_type == 0x04:  # defeat monster
        r.u32()
    elif quest_type == 0x05:  # artifacts
        cnt = r.u8()
        r.skip(cnt * 2)
    elif quest_type == 0x06:  # creatures
        cnt = r.u8()
        r.skip(cnt * 4)
    elif quest_type == 0x07:  # resources
        r.skip(4 * 7)
    elif quest_type == 0x08:  # be hero
        r.u8()
    elif quest_type == 0x09:  # be player
        r.u8()
    # deadline + messages
    r.u32()  # deadline
    if quest_type != 0:
        m = r.pstr(f'{ctx_name}_quest_proposal')
        if m: texts.append((f'{ctx_name}_quest_proposal', m))
        m = r.pstr(f'{ctx_name}_quest_progress')
        if m: texts.append((f'{ctx_name}_quest_progress', m))
        m = r.pstr(f'{ctx_name}_quest_completion')
        if m: texts.append((f'{ctx_name}_quest_completion', m))


def parse_guardians(r: R, fmt: int, texts: TextsList, ctx_name: str) -> None:
    """Reads an optional "message + guarding creatures" block, shared by
    several object types (Pandora's Box, Event, Artifact, Spell Scroll,
    Resource) when their has_guardians flag is set.
    In: r, fmt (creature-slot width differs: 3 bytes in RoE, 4 in AB/SoD),
    texts, ctx_name. Out: None (appends '{ctx_name}_guardian_mesg', advances r)."""
    m = r.pstr(f'{ctx_name}_guardian_mesg')
    if m: texts.append((f'{ctx_name}_guardian_mesg', m))
    has_creatures = r.u8()
    if has_creatures:
        r.skip(7 * (3 if fmt == FORMAT_ROE else 4))
    r.skip(4)  # unknown1


def parse_contents(r: R, fmt: int, texts: TextsList, ctx_name: str) -> None:
    """Reads a Pandora's-Box-style "bag of rewards" body (experience, spell
    points, morale/luck deltas, resources, primary skills, secondary
    skills, artifacts, spells, creatures) - no text of its own, just opaque
    numeric reward data. In: r, fmt (slot widths vary by format, same
    pattern as elsewhere in this file), texts (unused, kept for call-site
    symmetry), ctx_name (unused, ditto). Out: None (advances r)."""
    r.u32(); r.u32(); r.u8(); r.u8()  # experience, spell_points, morale, luck
    r.skip(4 * 7)  # resources
    r.skip(4)  # primary skills
    ss_count = r.u8()
    r.skip(ss_count * 2)
    art_count = r.u8()
    r.skip(art_count * (1 if fmt == FORMAT_ROE else 2))
    spell_count = r.u8()
    r.skip(spell_count * 1)
    creature_count = r.u8()
    r.skip(creature_count * (3 if fmt == FORMAT_ROE else 4))
    r.skip(8)  # unknown


def sizeof_reward(fmt: int, reward_type: int) -> int:
    """Pure lookup, no reading: how many bytes a Seer's Hut reward's own
    payload occupies, given its type byte (already consumed by the
    caller). In: fmt (artifact/creature slot width varies by format),
    reward_type (0x00 none .. 0x0A creature). Out: int byte count (0-5)."""
    if reward_type == 0x00:
        return 0
    if reward_type in (0x01, 0x02):  # experience, spell points
        return 4
    if reward_type == 0x08:  # artifact
        return 1 if fmt == FORMAT_ROE else 2
    if reward_type in (0x03, 0x04, 0x09):  # morale, luck, spell
        return 1
    if reward_type == 0x05:  # resource
        return 5
    if reward_type in (0x06, 0x07):  # primary/secondary skill
        return 2
    if reward_type == 0x0A:  # creature
        return 3 if fmt == FORMAT_ROE else 4
    raise UnknownFieldValueError(f"unknown reward_type {reward_type}")


def parse_town_events(r: R, fmt: int, texts: TextsList, ctx_name: str) -> None:
    """Reads a Town object's list of scheduled "town events" (scripted
    resource/building/creature grants on a day-of-week schedule - the
    in-editor "Town Events" tab), each with its own name + message text.
    In: r, fmt, texts, ctx_name (the owning town's context prefix). Out:
    None (appends '{ctx_name}_event_name'/'_event_mesg' per event, advances r)."""
    event_count = _check_count(r.u32(), 'town_event_count')
    for _ in range(event_count):
        name = r.pstr(f'{ctx_name}_event_name')
        if name: texts.append((f'{ctx_name}_event_name', name))
        mesg = r.pstr(f'{ctx_name}_event_mesg')
        if mesg: texts.append((f'{ctx_name}_event_mesg', mesg))
        r.skip(4 * 7)  # resources
        r.u8()  # applies_to_players
        if is_sod(fmt):
            r.u8()  # applies_to_human
        r.u8()  # applies_to_computer
        r.u16()  # first_occurence
        r.u8()  # subsequent_occurences
        r.skip(17)  # unknown1
        r.skip(6)  # buildings
        r.skip(14)  # creature_quantities[7] uint16
        r.skip(4)  # unknown2


def parse_object_body(r: R, fmt: int, meta_type: int, texts: TextsList, ctx_name: str) -> None:
    """Dispatches to the right field layout for ONE placed object instance,
    based on its meta_type (from CLASS_TO_META, via the object-attributes
    table) - e.g. a Town reads name/garrison/buildings/events, a Sign reads
    one message string, a generic-impassable/visitable object reads
    nothing further. This is the single largest source of text labels in
    the whole map ('{ctx_name}_town_name', '_hero_name', '_hero_bio',
    '_sign_mesg', '_monster_mesg', '_event_name'/'_event_mesg',
    '_quest_proposal'/'_progress'/'_completion', '_guardian_mesg', plus
    whatever parse_town_events/parse_guardians/parse_contents/
    parse_ext_quest add for that object).
    In: r, fmt, meta_type (one of the GENERIC_.../TOWN/HERO/... constants
    above), texts, ctx_name (e.g. 'obj42', unique per placed object - NOT
    per object-attributes-table entry, since many instances can share one
    appearance). Out: None (advances r past exactly this one object's body;
    raises ValueError on a meta_type this function doesn't know - see
    CLASS_TO_META for the class->meta_type mapping that feeds it)."""
    absod = is_ab_or_sod(fmt)

    if meta_type in (GENERIC_IMPASSABLE, GENERIC_IMPASSABLE_ABSOD, GENERIC_VISITABLE,
                      GENERIC_VISITABLE_ABSOD, BOAT, PASSABLE_TERRAIN, PASSABLE_TERRAIN_SOD,
                      GENERIC_TREASURE, SUBTERRANEAN_GATE):
        return  # no body

    if meta_type == PLACEHOLDER_HERO:
        r.u8()  # owner
        htype = r.u8()
        if htype == 0xFF:
            r.u8()  # power_rating
        return

    if meta_type == QUEST_GUARD:
        qt = r.u8()
        if qt != 0:
            parse_ext_quest(r, qt, texts, ctx_name)
        return

    if meta_type == PANDORAS_BOX:
        has_g = r.u8()
        if has_g:
            parse_guardians(r, fmt, texts, ctx_name)
        parse_contents(r, fmt, texts, ctx_name)
        return

    if meta_type in (SIGN, OCEAN_BOTTLE):
        m = r.pstr(f'{ctx_name}_sign_mesg')
        if m: texts.append((f'{ctx_name}_sign_mesg', m))
        r.skip(4)
        return

    if meta_type in (GARRISON, GARRISON_ABSOD):
        r.u32()  # owner
        r.skip(7 * (3 if fmt == FORMAT_ROE else 4))
        if absod:
            r.u8()  # removable_units
        r.skip(8)
        return

    if meta_type == EVENT:
        has_g = r.u8()
        if has_g:
            parse_guardians(r, fmt, texts, ctx_name)
        parse_contents(r, fmt, texts, ctx_name)
        r.u8(); r.u8(); r.u8()  # applies_to_players, applies_to_computer, cancel_after_visit
        r.skip(4)
        return

    if meta_type == GRAIL:
        r.u32()
        return

    if meta_type in (DWELLING, LIGHTHOUSE, RESOURCE_GENERATOR, SHIPYARD, ABANDONED_MINE):
        r.u32()  # owner (or potential bitfield for abandoned mine - same size)
        return

    if meta_type == TOWN:
        if absod:
            r.u32()  # absod_id
        r.u8()  # owner
        has_name = r.u8()
        if has_name:
            name = r.pstr(f'{ctx_name}_town_name')
            if name: texts.append((f'{ctx_name}_town_name', name))
        has_creatures = r.u8()
        if has_creatures:
            r.skip(7 * (3 if fmt == FORMAT_ROE else 4))
        r.u8()  # formation
        has_buildings = r.u8()
        if has_buildings:
            r.skip(12)
        else:
            r.u8()  # has_fort
        if absod:
            r.skip(9)  # must_have_spells
        r.skip(9)  # may_have_spells
        parse_town_events(r, fmt, texts, ctx_name)
        if is_sod(fmt):
            r.u8()  # alignment
        r.skip(3)  # unknown1
        return

    if meta_type in (RANDOM_DWELLING, RANDOM_DWELLING_LVL, RANDOM_DWELLING_FACTION):
        r.u32()  # owner
        if meta_type != RANDOM_DWELLING_FACTION:
            castle_absod_id = r.u32()
            if castle_absod_id == 0:
                r.skip(2)  # alignment
        if meta_type != RANDOM_DWELLING_LVL:
            r.u8(); r.u8()  # min_level, max_level
        return

    if meta_type in (HERO, RANDOM_HERO, PRISON):
        if absod:
            r.u32()  # absod_id
        r.u8()  # owner
        r.u8()  # type
        has_name = r.u8()
        if has_name:
            name = r.pstr(f'{ctx_name}_hero_name')
            if name: texts.append((f'{ctx_name}_hero_name', name))
        if is_sod(fmt):
            has_exp = r.u8()
            if has_exp:
                r.u32()
        else:
            r.u32()  # experience always present
        has_face = r.u8()
        if has_face:
            r.u8()
        has_ss = r.u8()
        if has_ss:
            cnt = r.u32()
            r.skip(cnt * 2)
        has_creatures = r.u8()
        if has_creatures:
            r.skip(7 * (3 if fmt == FORMAT_ROE else 4))
        r.u8()  # formation
        has_artifacts = r.u8()
        if has_artifacts:
            worn_size = 18 if fmt == FORMAT_ROE else (36 if fmt == FORMAT_AB else 38)
            r.skip(worn_size)
            backpack_count = r.u16()
            r.skip(backpack_count * (1 if fmt == FORMAT_ROE else 2))
        r.u8()  # patrol_radius
        if absod:
            has_bio = r.u8()
            if has_bio:
                bio = r.pstr(f'{ctx_name}_hero_bio')
                if bio: texts.append((f'{ctx_name}_hero_bio', bio))
            r.u8()  # gender
        if is_sod(fmt):
            has_spells = r.u8()
            if has_spells:
                r.skip(9)
        elif fmt == FORMAT_AB:
            r.u8()  # single spell, unconditional
        if is_sod(fmt):
            has_ps = r.u8()
            if has_ps:
                r.skip(4)
        r.skip(16)  # unknown2
        return

    if meta_type in (MONSTER,):
        if absod:
            r.u32()  # absod_id
        r.u16()  # quantity
        r.u8()  # disposition
        has_mt = r.u8()
        if has_mt:
            m = r.pstr(f'{ctx_name}_monster_mesg')
            if m: texts.append((f'{ctx_name}_monster_mesg', m))
            r.skip(4 * 7)
            r.skip(1 if fmt == FORMAT_ROE else 2)  # treasure artifact
        r.u8(); r.u8()  # never_flees, does_not_grow
        r.skip(2)
        return

    if meta_type in (ARTIFACT,):
        has_g = r.u8()
        if has_g:
            parse_guardians(r, fmt, texts, ctx_name)
        return

    if meta_type == SHRINE:
        r.u32()
        return

    if meta_type == SPELL_SCROLL:
        has_g = r.u8()
        if has_g:
            parse_guardians(r, fmt, texts, ctx_name)
        r.u32()  # spell
        return

    if meta_type == RESOURCE:
        has_g = r.u8()
        if has_g:
            parse_guardians(r, fmt, texts, ctx_name)
        r.u32()  # quantity
        r.skip(4)
        return

    if meta_type == WITCH_HUT:
        if fmt >= FORMAT_AB:
            r.skip(4)
        return

    if meta_type == SEERS_HUT:
        quest_type = r.u8()
        if fmt == FORMAT_ROE:
            pass  # quest_type IS the artifact type (0xFF none), no further quest struct
        else:
            if quest_type != 0:
                parse_ext_quest(r, quest_type, texts, ctx_name)
        reward_type = r.u8()
        if reward_type != 0:
            r.skip(sizeof_reward(fmt, reward_type))
        r.skip(2)
        return

    if meta_type == SCHOLAR:
        r.u8(); r.u8()
        r.skip(6)
        return

    raise UnknownFieldValueError(f"unhandled meta_type {meta_type}")


def parse_object_details(r: R, fmt: int, oa_types: list[int], texts: TextsList) -> int:
    """Reads every placed object INSTANCE on the map (position + which
    object-attributes-table entry it uses + its type-specific body via
    parse_object_body). This is where the bulk of a map's translatable
    text actually lives.
    In: r, fmt, oa_types (the CLASS_TO_META-mapped list from
    parse_object_attributes, indexed by each instance's oa_index), texts.
    Out: int - how many object instances were read (informational; callers
    use it only for a sanity-check print, not further parsing)."""
    count = _check_count(r.u32(), 'object_details count')
    for i in range(count):
        r.u8(); r.u8(); r.u8()  # x, y, z
        oa_index = r.u32()
        r.skip(5)  # unknown1
        if oa_index >= len(oa_types):
            raise ParseError(
                f"object {i}: oa_index {oa_index} is past the object-attributes "
                f"table's own length ({len(oa_types)}) - reader position likely "
                f"desynced upstream")
        meta_type = oa_types[oa_index]
        ctx_name = f'obj{i}'
        parse_object_body(r, fmt, meta_type, texts, ctx_name)
    return count


def parse_map_events(r: R, fmt: int, texts: TextsList) -> int:
    """Reads the map-wide (not town-scoped) "timed events" list - the
    in-editor Map Specifications "Events" tab: scripted resource grants
    with a name + popup message, on a schedule, not tied to any object.
    In: r, fmt, texts. Out: int - how many map events were read
    (informational only, same as parse_object_details' return). Appends
    'mapevent{i}_name'/'mapevent{i}_mesg' per event."""
    count = _check_count(r.u32(), 'map_events count')
    for i in range(count):
        name = r.pstr(f'mapevent{i}_name')
        if name: texts.append((f'mapevent{i}_name', name))
        mesg = r.pstr(f'mapevent{i}_mesg')
        if mesg: texts.append((f'mapevent{i}_mesg', mesg))
        r.skip(4 * 7)  # resources
        r.u8()  # applies_to_players
        if is_sod(fmt):
            r.u8()  # applies_to_human
        r.u8()  # applies_to_computer
        r.u16()  # first_occurence
        r.u8()  # subsequent_occurences
        r.skip(17)  # unknown
    return count


def parse_h3m(data: bytes) -> tuple[R, int, TextsList, int, int]:
    """Top-level entry point: runs the full field sequence over one
    decompressed .h3m map in order (header -> players -> AI/rumors/hero
    settings -> tiles -> object-attributes table -> object instances ->
    map events). See the module docstring's "Usage as a library" example.
    In: data - the DECOMPRESSED map bytes (caller does the gzip.decompress
    first; this function never touches compression). Out: (r, fmt, texts,
    obj_count, event_count) - r is the reader (r.p is how many bytes were
    consumed, r.remaining() should be 0 or 124 for a clean parse - see
    module docstring; pass track=True yourself and call the section
    functions directly, as h3m_writer.parse_h3m_tracked does, if you need
    r.segments for editing rather than just reading), texts is
    [(label, raw_bytes), ...] for every text field found (decode
    raw_bytes as cp1251 for Ukrainian, cp1252 for English), obj_count/
    event_count are informational counts. Raises ValueError on any object
    class this file doesn't recognize (see CLASS_TO_META) or any
    implausible string length (see R.pstr) - both indicate either a
    genuinely new/unhandled map feature or (more often historically) a
    parser bug upstream that desynced the read position."""
    r = R(data)
    texts: TextsList = []
    fmt, map_size, has_two_levels = parse_header(r, texts)
    parse_players(r, fmt, texts)
    parse_ai_section(r, fmt, texts)
    parse_tiles(r, map_size, has_two_levels)
    oa_types_raw = parse_object_attributes(r, texts)
    oa_types = [CLASS_TO_META.get(c, -1) for c in oa_types_raw]
    unknown = [c for c, m in zip(oa_types_raw, oa_types, strict=True) if m == -1]
    if unknown:
        raise UnknownFieldValueError(f"unknown object classes: {sorted(set(unknown))}")
    obj_count = parse_object_details(r, fmt, oa_types, texts)
    event_count = parse_map_events(r, fmt, texts)
    return r, fmt, texts, obj_count, event_count


if __name__ == '__main__':
    import gzip
    import sys
    path = sys.argv[1]
    with open(path, 'rb') as f:
        data = gzip.decompress(f.read())
    r, fmt, texts, obj_count, event_count = parse_h3m(data)
    print(f"format={hex(fmt)} objects={obj_count} events={event_count} "
          f"consumed={r.p}/{len(data)} remaining={r.remaining()} texts={len(texts)}")
    if r.remaining() not in (0, 124):
        print("WARNING: remaining bytes are neither 0 nor the usual 124-byte padding - "
              "this map may not have parsed cleanly.")
