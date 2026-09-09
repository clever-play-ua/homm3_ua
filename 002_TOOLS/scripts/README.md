Requires: `npm i -g mmarch`, and Python with `pip install pillow numpy pytest`.
Dev-only (not needed just to run the tools, only to work on them - see
"Code quality tooling" below): `pip install pytest-cov mypy ruff`.

## Numbering

The scripts directly in this folder (`002_TOOLS/scripts/*.py`) are numbered
`001_`-`012_` in the order you'd normally run them - they're independent CLI
tools invoked one at a time (`python 001_....py ...`), never imported by each
other as Python modules (except `006_build_mod.py`, which shells out to
`007_fix_lod_sort_order.py` as a subprocess, not an import), so numbering the
filenames is safe.

`h3_parser/` is different: those `.py` files import each other directly
(`from h3c_writer import ...`), and Python does not allow a module name to
start with a digit (`from 001_h3m_parser import X` is a syntax error) - so
that subfolder's files keep plain names, and the "numbering" below is just
documentation order (dependency order: each one only depends on the ones
before it). It's also a real, importable Python package now (`h3_parser/__init__.py`)
- `from h3_parser import parse_h3m, H3Error` (etc - see `__init__.py`'s
`__all__`) works from outside the folder with no `sys.path` hacks of your
own, e.g. from `002_TOOLS/scripts` with `sys.path.insert(0, '.')`. This is
in ADDITION to, not instead of, every file's own direct-script usage
(`python h3m_writer.py extract ...`) - both work, see `__init__.py`'s own
docstring for why both exist rather than picking one.

## The one command to deploy everything: `013_deploy_full.py`

Every other script below is a building block; this is the assembled
machine. Given a pristine, English-language GOG "HoMM 3 Complete" install,
one command rebuilds all 4 flat archives (text/images), copies them over
the live install, and deploys all 20 translated campaigns to their
correct (empirically-discovered, see the script's own docstring) archive
- with a backup and a byte-identical verification at every step, exiting
non-zero if anything didn't actually take:

```
python 013_deploy_full.py --game "F:/Games/HoMM 3 Complete"
```

Add `--force` to inject flat-text files even where the English record
count doesn't match this build's own copy (see `006_build_mod.py` below
for why that check exists and when overriding it is safe - it always has
been, so far, for the specific mismatches this project's files produce).
`--skip-archives`/`--skip-campaigns` run only one half, e.g. for a fast
campaign-only re-deploy after touching `005_RAW/<campaign>/`. If a
campaign's pre-built `<Stem>_UA.h3c` is missing from `005_RAW/`, it's
rebuilt on the spot from that campaign's `missions/` folder (via
`deploy_campaign.py`) rather than failing - so a from-scratch clone with
only the `missions/` JSON edits (no committed `.h3c` binaries) still
deploys correctly.

**This is genuinely the whole project's output, verified end-to-end,
every time it's run** - re-running it after any edit to
`001_ORIGINAL_HOMM3_FILES_HURTOM/*` or `005_RAW/<campaign>/missions/*` is
the correct way to test that edit in the actual game, not a partial
manual `mmarch add`.

## `h3_txt_records.py` - shared correct record-splitter for flat .TXT files

Used by `002_build_raw.py` and `006_build_mod.py` to decide whether a
translated flat `.TXT` resource file (`GENRLTXT.TXT`, `ADVEVENT.TXT`,
`HELP.TXT`, ...) is safe to inject: compares the English and Ukrainian
**record** counts, not raw physical line counts - a single record's
quoted field can legitimately span several physical lines in this format
(confirmed against VCMI's own from-scratch reimplementation of the
original game's resource loader). **Read `H3_TXT_FORMAT_NOTES.md` before
touching this area** - it has the investigation that found this, the
per-file fixes applied to Hurtom's translation as a result, and a real
hazard specific to editing these particular files (the `Edit` tool
silently corrupts their `cp1251` encoding - use PowerShell + .NET's own
`GetEncoding(1251)` instead, see that doc for the exact recipe).

- **`split_txt_records(text) -> list[str]`** - **in:** the fully-decoded
  contents of one of these files; **out:** one entry per logical record,
  in file order.
- **`record_count(text) -> int`** - convenience wrapper, `len(split_txt_records(text))`.

## Top-level scripts, in run order

1. **`001_match_translated_files.py`** — scans `001_ORIGINAL_HOMM3_FILES_HURTOM`
   and figures out which game archive(s) each file belongs to. Writes
   `matches.json` here (consumed by `002_build_raw.py` and `006_build_mod.py`).
   - **In:** `--game` (install path, for reading the real archives to match
     filenames against). **Out:** `matches.json` = `{archive_name: [file_name, ...]}`.

2. **`002_build_raw.py`** — uses `matches.json` to build `../../005_RAW/`: one
   JSON per text file (`{var, en, ua}` per line) plus original/translated
   graphics side by side under `005_RAW/imgs/<archive>/en|ua/`.
   - **In:** `matches.json`, `--game`, `--translated` (default
     `001_ORIGINAL_HOMM3_FILES_HURTOM`). **Out:** `005_RAW/<archive>/*.json`,
     `005_RAW/imgs/<archive>/{en,ua}/*`.

3. **`003_extract_campaigns.py`** — campaign (`.h3c`) files have no flat text
   table like the LOD `*.TXT` files, so this decompresses each of the 20
   campaigns, heuristically scans for embedded Pascal-strings, and pairs the
   EN/UA occurrences with a length-based DP alignment (**not** a full
   structural parse - see `h3_parser/` below for that). Superseded for
   editing by `h3_parser/`, but still useful as a quick "does this string
   exist anywhere, and roughly what does Hurtom's version say" lookup.
   - **In:** `--game`. **Out:** `005_RAW/<NNN>_<CampaignName>/<Stem>.h3c` (EN
     copy) + `texts.json` = list of `{var, en, ua, aligned}` (`aligned: false`
     = no confident match found, check by hand).

4. **`004_extract_campaign_videos.py`** — pulls each campaign's cutscene(s)
   out of `VIDEO.VID`/`H3ab_ahd.vid` and converts them to silent `.mp4` (the
   source `.BIK`s have no usable audio of their own - see
   `AUDIO_VIDEO_NOTES.md`).
   - **In:** `--game`, `--out` (default `005_RAW`). **Out:**
     `005_RAW/<NNN>_<Campaign>/videos/<name>.mp4`.

5. **`005_def_to_png.py`** — decodes a `.DEF` sprite/animation file (or a
   whole folder of them) into transparent PNG frames, e.g.
   `python 005_def_to_png.py ../../005_RAW/imgs/H3sprite.lod/en ./png_out`.
   No PNG-back-to-DEF direction exists yet - ask if you need it.
   - **In:** a `.DEF` file or a folder, an output folder. **Out:**
     `<outdir>/<name>.dir/<group>_<frame>.png` + `<name>.json` (frame/group
     order manifest).

6. **`006_build_mod.py`** — uses `matches.json` to build
   `../../004_HOMM3_complete/`: fresh copies of the game archives with every
   translated file injected, ready to copy over the real game folder. Skips
   injecting a text file into an archive when that archive's English line
   count doesn't match the translation (older/different text layout in that
   archive) - use `--force` to override. Always finishes by calling
   `007_fix_lod_sort_order.py` on every archive it touched - **do not skip
   this step if hand-rolling a similar pipeline elsewhere** (see next entry).
   - **In:** `matches.json`, `--game`, `--translated`, `--out`, `--force`.
     **Out:** `004_HOMM3_complete/Data/*.lod` (translated, sorted) +
     `004_HOMM3_complete/Maps/Tutorial.tut`.

7. **`007_fix_lod_sort_order.py`** — re-sorts an LOD archive's entry table
   back into the case-insensitive alphabetical order the game's own
   `ResourceManager` requires (it does a binary search assuming that order).
   **Mandatory** after any `mmarch add` into `H3bitmap.lod`/`H3sprite.lod`/
   `H3ab_bmp.lod`/`H3ab_spr.lod` (or any other LOD) - `mmarch add` appends
   replaced entries at the end of the table instead of overwriting in place,
   which silently makes them unfindable by the game (not by `mmarch` itself,
   which doesn't care about order) even though the file data is completely
   intact. Confirmed root cause of a real crash
   (`ResourceManager::GetText could not find the "text" resource
   "campbttn.txt"`) that looked unrelated to anything just changed.
   - **In:** one or more `.lod` file paths (edited in place). **Out:** none
     (mutates the file(s) given).

8. **`008_mp4_to_bik_inject.py`** — encodes a video (mp4/avi) to real `.bik`
   and injects it into an archive, replacing an existing clip (e.g. to swap
   in a custom-translated/dubbed cutscene). Needs the current RAD Video
   Tools build installed (NOT the old crashing 2001 mirror) - see the
   script's docstring and `AUDIO_VIDEO_NOTES.md` for exact install steps and
   the `Bink`-vs-`BinkConv` subcommand trap. **For the 7 original RoE
   campaigns specifically, use `009_mp4_to_smk_inject.py` instead** - the
   game reads those missions' `.SMK`, not their `.BIK`. Open, unresolved risk
   (confirmed, not yet fixed): this encoder always writes the `BIKi`
   bitstream revision; the original game files (and the game's bundled
   `binkw32.dll`) are `BIKb` - a file encoded this way did not play in-game
   in testing (silent no-op, not a crash) and no local RAD Video Tools build
   exposes a switch to force an older revision (checked - dumped every
   switch string from the exe, none control this). Swapping in another
   game's `binkw32.dll` needs to be the SAME Bink SDK generation as whatever
   encoded the video, not just "newer" - a mismatched one (tried once) can
   outright crash the game, not just silently fail to play.
   - **In:** source video path, target archive entry name (e.g.
     `GOOD1A.BIK`), `--archive`, `--game`, `--width/--height/--fps`.
     **Out:** a modified **scratch copy** of the archive (never touches the
     live install directly - copy it over `Data/` yourself once verified).

9. **`009_mp4_to_smk_inject.py`** — the SMK counterpart, for the 7 original
   RoE campaigns' mission videos (the ones the game actually reads there).
   Read its docstring before touching this area again - full trap list: a
   genuine encoder bug that corrupts truecolor input regardless of palette
   switch (fixed by pre-quantizing frames in Python/PIL to the original
   file's exact palette before encoding), the game's bundled `SMACKW32.DLL`
   being too old to play the new SMK4 format at all (fix: swap in a newer
   decoder DLL from another owned classic RAD-tools game - confirmed working
   for this SMK path specifically), and a real reliability ceiling in the
   encoder itself - only 800x600 @ 10fps (the script's default, and the
   original game's own native rate) has worked reliably; higher
   resolutions/frame rates hang or crash the encoder unpredictably.
   - **In:** source video path, target archive entry name (e.g.
     `GOOD1A.SMK`), `--archive`, `--game`, `--width/--height/--fps/--duration`.
     **Out:** a modified **scratch copy** of the archive (same caveat as
     above - copy it over `Data/` yourself once verified, and remember
     audio isn't embedded - see script docstring).

10. **`010_smk_audio_decoder.py`** — not a CLI tool, a library module: a
    from-scratch (ported from `libsmacker`) Smacker container + audio-only
    decoder, used to double-check whether a given `.smk`'s audio track is
    real speech or junk noise (ffmpeg's own smackaudio decoder produces pure
    noise for these HoMM3 files - confirmed by spectrogram - so this exists
    to rule out "is this a decoder bug" before writing that track off).
    - **In (function `decode_smk_audio(path) -> wave-writable PCM samples`,
      see the module for the exact call)**: a `.smk` file path. **Out:** raw
      PCM audio samples (track 0 only - video isn't decoded, ffmpeg already
      handles that part correctly).

11. **`011_burn_campaign_subtitles.py`** — builds a narrated + subtitled
    showcase `.mp4` for one campaign's missions, using the game's own real
    voiceover audio (found under non-obvious short codes in `Heroes3.snd`,
    RoE campaigns only - see `AUDIO_VIDEO_NOTES.md` for the full code map)
    and `CAMPDIAG.TXT`'s matching text, timed against it. This is a
    demo/reference video, not something injected back into the game.
    - **In:** campaign stem (e.g. `GOOD1`), `--lang en|ua`. **Out:**
      `005_RAW/<NNN>_<Campaign>/videos/<Stem>_narrated_<LANG>.mp4` +
      the raw voiceover `.wav`s under `voiceover_en/`.

12. **`012_safe_deploy.py`** — wraps the "back up, `mmarch add`, re-sort a
    LOD, verify byte-identical" sequence every real deploy to the live game
    needs into one command, so that sequence can't be accidentally
    shortened under time pressure (this actually happened once - a 688MB
    `VIDEO.VID` got modified without a backup, caught by luck). Never
    overwrites a backup that's already there.
    - **In:** archive path (e.g. `Data/H3ab_bmp.lod`), one or more files to
      inject, `--no-sort` (skip `007_fix_lod_sort_order.py`, rarely
      needed). **Out:** none printed beyond a PASS/FAIL report per file;
      exits non-zero if any injected file doesn't verify byte-identical
      afterward (safe to use as a script gate, not just to read).

13. **`013_deploy_full.py`** — see "The one command to deploy everything"
    above. Orchestrates `006_build_mod.py` + `012_safe_deploy.py` +
    `deploy_campaign.py` into the single full clean-rebuild-and-redeploy
    sequence this project actually runs before every playtest.
    - **In:** `--game`, `--raw` (default `005_RAW`), `--out` (default
      `004_HOMM3_complete`), `--force`, `--skip-archives`,
      `--skip-campaigns`. **Out:** none (mutates `--game`); exits
      non-zero if any archive or campaign fails its post-injection
      byte-identical check.

## Tests

Two separate `pytest` suites - `cd 002_TOOLS/scripts && python -m pytest`
picks up both.

- **`tests/`** (this folder) - `h3_txt_records.py`'s own regression suite
  (`test_h3_txt_records.py`): locks in the record-boundary rule itself
  (quoted multi-line fields, the `""` escape, CRLF, trailing-newline
  handling) with small, self-contained inputs - see `H3_TXT_FORMAT_NOTES.md`
  for the real files that motivated each case.
- **`h3_parser/tests/`** is a real `pytest` suite (`pip install pytest`, then
`cd h3_parser && python -m pytest tests/ -v`) - it turns the ad-hoc
one-off scripts that found every bug in `H3M_H3C_FORMAT_NOTES.md` into
something that lives in git and runs in seconds. 231 tests total, across
four files:

- **`test_roundtrip.py`** - the "did I just break something" net: every
  campaign's every scenario parses clean, every campaign's wrapper
  survives a no-op extract+rebuild byte-identical, every already-deployed
  `*_UA.h3c` still parses clean, and (skipped automatically if the game
  isn't installed at `HOMM3_GAME_DIR`/`F:/Games/HoMM 3 Complete`) all 160
  standalone maps in the game's own `Maps` folder parse clean too. Run
  this after touching anything in `h3_parser/` - before this suite
  existed, this could only be answered by remembering to re-run a scratch
  script by hand.
- **`test_writers.py`** - exercises the actual *editing* paths (not just
  no-op roundtrips): `h3m_writer.rebuild()`/`h3c_writer.rebuild()` with a
  real substitution applied and re-extracted, `h3c_parser.parse_h3c()`
  cross-checked against `h3c_writer.split_h3c()`, `build_mission_texts.py`'s
  pure helper functions, and `deploy_campaign.py`'s `deploy()` end-to-end
  (both called directly and via its real CLI/`subprocess` entry point).
  Added specifically because a `pytest --cov` run showed these paths were
  at or near 0% covered despite being this project's actual reason to
  exist - see "Coverage" below.
- **`test_fuzz.py`** - a deterministic (fixed seed) robustness check:
  corrupts 1-6 random bytes in 5 real small `.h3m` files, 60 trials each,
  and asserts the parser either completes cleanly or raises one of this
  project's own `H3Error` subclasses (see `h3m_parser.py`'s exception
  hierarchy below) - never a raw `IndexError`/`struct.error`/hang. This is
  what a corrupted or truncated file someone hands the tool one day would
  look like, as opposed to `test_roundtrip.py`'s corpus of real,
  differently-*shaped*-but-valid files. Its first run (before this
  session's fix) failed on every one of its 5 files with a real
  `IndexError` inside `parse_object_details()` - see `H3M_H3C_FORMAT_NOTES.md`.

## Code quality tooling

Three tools, each catching a different class of problem; none of them
change runtime behavior, all are safe to skip if you just want to run the
scripts (see "Requires" at the top).

### Coverage (`pytest-cov`)

`cd h3_parser && python -m pytest tests/ --cov=. --cov-report=term-missing`
(the `.coveragerc` in this folder excludes `tests/*` itself from the
denominator, so the % reflects library code only). Currently **86%**.
The uncovered ~14% is, deliberately, almost entirely `main()`/
`if __name__ == '__main__':` CLI-dispatch glue (`argparse` wiring,
`sys.argv` indexing) in `h3c_writer.py`/`h3m_writer.py`/
`build_mission_texts.py` - the actual logic each of those calls into
(`extract()`, `rebuild()`, `parse_h3m()`, ...) is exercised directly by
`test_writers.py`/`test_roundtrip.py`. Chasing 100% here would mean
testing that `argparse` parses argv correctly, not this project's own
code - not worth doing unless a real bug shows up in one of those
dispatch blocks specifically.

### Type checking (`mypy`)

From `002_TOOLS/scripts` (the *parent* of `h3_parser/`, not from inside
it - see `mypy.ini`'s own note on why):
`python -m mypy --config-file h3_parser/mypy.ini -p h3_parser`.
Currently clean (0 issues, 16 source files). Running it from inside
`h3_parser/` itself, or on bare filenames, raises a "Source file found
twice under different module names" error because of `h3_parser/__init__.py`
existing alongside each file's own direct-script `sys.path` insert - `-p
h3_parser` from the parent avoids the ambiguity.

### Linting/formatting (`ruff`)

`ruff check .` from `002_TOOLS/scripts` (config: `ruff.toml`, also in
this folder). Currently clean (0 issues). The rule selection is
deliberately curated, not `ruff`'s default/maximal set - see the comments
in `ruff.toml` itself for the two explicit exclusions (`SIM115`, and
`E701`/`E702`) and why: both would fight established, deliberate idioms
in this codebase (one-shot `open(path).read()`, and packing a "read and
discard N known-but-unused bytes" pair onto one line in the binary
field-reading code, e.g. `r.u8(); r.u8()  # experience, spell_points`).
Where a finding was real (unused variables, ambiguous names, string
concatenation instead of unpacking, printf-style formatting, etc.), it
was fixed rather than suppressed - for a "read a field just to advance
the buffer position, the value itself is never used" case specifically,
the fix is a bare `r.u8()  # field_name` call (matching how genuinely
skipped/reserved bytes are already written throughout this codebase),
not a discarded assignment.

## `h3_parser/` — the real structural `.h3m`/`.h3c` parser and writer

A byte-field-accurate parser AND writer (not a heuristic scan), built from
scratch and verified against the open-source `homm3tools` C library
(reading) and VCMI's own engine reimplementation (writing). Validated on all
160 standalone maps in the game's own `Maps` folder and all 20 official
campaigns / 87 scenarios, structurally clean end-to-end. **Read
`h3_parser/H3M_H3C_FORMAT_NOTES.md` before touching this area** - it has the
full, hard-won debugging trail (multi-gzip-member structure, the stale
`h3m_size` bug, the AB/SoD player-section bug, the `FINAL`-specific
preconditions-bitmask bug, and more) that is much easier to re-read than to
rediscover.

Files, in dependency order (each one only imports the ones listed before it
- this is also the order data flows through them):

1. **`h3m_parser.py`** — the core, read-only `.h3m` map parser. Entry point
   `parse_h3m(decompressed_bytes)` for a quick read, or use the `R(data,
   track=True)` reader class directly (see below) when you need byte-offset
   segments for editing. Also home to the shared `Segment` types
   (`FixedSegment`/`PstrSegment`/`H3mSizeSegment` - plain `NamedTuple`s, so
   old-style `_, s, e = seg` / `_, label, s, e = seg` unpacking still works
   everywhere, they just add `.kind`/`.start`/`.end`/`.label` attribute
   access and real types on top) and `rebuild_from_segments()`, the one
   "walk segments, substitute pstr, copy fixed" loop every writer in this
   project (`h3c_writer.rebuild()`, `h3m_writer.rebuild_map_bytes()`) calls
   into, instead of each keeping its own copy.
   - **In:** decompressed `.h3m` bytes. **Out:** `(reader, format, texts,
     object_count, event_count)` where `texts` is `[(label, raw_bytes), ...]`
     (decode `raw_bytes` as `TEXT_ENCODING` = `cp1251` - a strict ASCII
     superset, so it decodes English content identically to `cp1252` too,
     confirmed empirically) and, when constructed with `track=True`,
     `reader.segments` is a list of `Segment` (see above) spans covering
     the entire buffer sequentially - the basis every writer function
     below rebuilds from.
   - **Exception hierarchy** (all subclass `H3Error(ValueError)`, so any
     pre-existing `except ValueError` still works): `ParseError` (a
     corrupted/truncated file - out-of-bounds read, bad count field) with
     subclasses `ImplausibleLengthError`/`ImplausibleCountError` (a length
     or count field far outside anything a real map could contain -
     guarded by `MAX_PLAUSIBLE_COUNT = 100_000` via a `_check_count()`
     helper before every list/table count read, so a corrupted count
     can't turn into an effectively-infinite loop), `UnknownFieldValueError`
     (an object class this file's `CLASS_TO_META` table doesn't recognize),
     and `HeaderStructureError` (in `h3c_writer.py` - the `.h3c` wrapper
     header didn't match the expected shape). `R._require(n)` is called at
     the top of every primitive read (`u8`/`u16`/`u32`/`bytes_`/`skip`/
     inside `pstr`) and raises `ParseError` cleanly instead of an eventual
     raw `IndexError`/`struct.error` on truncated input - this is what
     makes `tests/test_fuzz.py`'s "never anything but an `H3Error`"
     contract actually hold.

2. **`h3c_parser.py`** — read-only `.h3c` campaign-wrapper parser (the
   original heuristic-free structural one, superseding
   `003_extract_campaigns.py` for reading). Also exports
   `find_next_h3m_name(data, pos)`, a small helper both this file and
   `h3c_writer.py` use to skip over each scenario's opaque "starting bonus"
   block by searching forward for the next scenario's `<name>.h3m` string.
   - **In:** raw (still-gzipped) `.h3c` bytes via `parse_h3c(decompressed_header)`.
     **Out:** `(campaign_name, campaign_desc, scenarios, wrapper_texts,
     end_offset)` - each `scenarios[i]` dict has `name`, `h3m_size`
     (untrusted - see `h3c_writer.py`), `blob_offset`, `blob`, `format`,
     `object_count`, `event_count`, `h3m_texts`.

3. **`h3c_writer.py`** — read AND write the `.h3c` wrapper's own text
   (campaign name/description/closing-narration epilogue, each scenario's
   prolog/epilog) plus the critical `h3m_size` bookkeeping every other
   writer here depends on.
   - **`split_h3c(raw_h3c_bytes) -> (header_bytes_decompressed, [scenario_gzip_member_bytes, ...])`**
     - splits the file into its N+1 *independent* gzip members (see
       `H3M_H3C_FORMAT_NOTES.md` - this is NOT one gzip stream).
   - **`read_header_segments(header_bytes, scenario_count) -> [('fixed',s,e) | ('pstr',label,s,e) | ('h3m_size',scenario_idx,s,e), ...]`**
     - walks the decompressed header sequentially; `scenario_count` MUST be
       passed in (not derivable from the header alone).
   - **`extract(h3c_path, out_json, ua_source_path=None, stem=None)`** - **in:**
     a `.h3c` path (+ optionally a Hurtom-translated `.h3c` of the same
     campaign to pre-fill `ua`); **out:** writes `out_json` =
     `[{var, field, en, ua}, ...]` for every wrapper-level text field.
   - **`rebuild(h3c_path, json_path, out_path)`** - **in:** the original
     `.h3c`, a JSON of `{field, ua}` edits (`field` = the raw label from
     `read_header_segments`, e.g. `scenario0_prolog`, `campaign_epilogue`);
     **out:** writes a new `.h3c` with those fields replaced and every other
     byte untouched. Does **not** touch map bodies - see `h3m_writer.py` for
     that, and note its `rebuild()` must run `patch_h3m_sizes()` afterward.
   - **`patch_h3m_sizes(raw_h3c_bytes) -> new_h3c_bytes`** - re-derives every
     scenario's `h3m_size` header field from its *actual current* compressed
     gzip-member length. **Critical, load-bearing**: a stale `h3m_size` (left
     over after any scenario's map bytes change size) makes that one
     scenario break in-game while passing every other check - this was the
     root cause of a very long debugging session, see
     `H3M_H3C_FORMAT_NOTES.md`.
   - **`compress_h3_gzip(data) -> gzip_bytes`** - gzip-compress exactly the
     way real HoMM3 files do (`compresslevel=6, mtime=0`, OS byte patched to
     `0x0B`) - use this, never a bare `gzip.compress()`, everywhere in this
     codebase.

4. **`h3m_writer.py`** — read AND write ONE scenario's own in-map text (map
   name/desc, hero names/bios, event messages, town names, sign/quest/guard
   messages, rumors...).
   - **`parse_h3m_tracked(decompressed_map_bytes) -> reader`** - same field
     sequence as `h3m_parser.parse_h3m`, but returns the tracking `R`
     instance so `reader.segments` is available for rebuilding.
   - **`extract(h3c_path, scenario_idx, out_json, ua_source_path=None, stem=None)`**
     - **in:** a `.h3c` path + 0-based scenario index (same order
       `split_h3c` lists them in) + optionally a Hurtom-translated `.h3c` to
       pre-fill `ua`; **out:** writes `out_json` = `[{var, field, en, ua}, ...]`
       for that one scenario's map text.
   - **`rebuild(h3c_path, scenario_idx, json_path, out_path)`** - **in:** the
     original `.h3c`, the scenario index, a JSON of `{field, ua}` edits
     (`field` = the raw label from `h3m_parser`'s `texts`, e.g.
     `obj16_town_name`, `rumor3_desc`); **out:** writes a new `.h3c` with
     that ONE scenario's map recompressed (all other scenarios + the header
     copied through byte-identical) and `h3c_writer.patch_h3m_sizes()`
     already applied - safe to feed straight to `mmarch add`.

5. **`build_mission_texts.py`** — orchestrates both writers above into the
   project's actual `005_RAW/<NNN>_<Campaign>/missions/` layout: one
   `texts.json` per mission folder (wrapper + map text combined, pre-filled
   from a Hurtom `.h3c` when given) plus a `000_<Campaign>_description/`
   folder for the two/three campaign-level-only fields that belong to no
   single scenario.
   - **In:** a `.h3c` path, an output `missions/` folder, `--ua-source`
     (Hurtom `.h3c`), `--stem` (e.g. `GOOD1`). **Out:** one
     `missions/NNN_<MapName>/texts.json` per scenario + one
     `missions/000_<CampaignName>_description/texts.json`, each a list of
     `{var, field, en, ua}`.

6. **`deploy_campaign.py`** — the missing link back the other way: takes
   `build_mission_texts.py`'s per-mission-folder JSON layout (keyed by
   `field` values like `wrapper_prolog`/`map_map_name`) and re-keys each
   record back to the raw field name `h3c_writer.rebuild()`/
   `h3m_writer.rebuild()` expect (`scenario0_prolog`/`map_name`), then
   chains one wrapper rebuild + one map rebuild per scenario into a single
   final translated `.h3c`.
   - **In:** the original `.h3c` path, the `missions/` folder (already
     hand-edited), an output path. **Out:** one fully-rebuilt, ready-to-
     `mmarch add` translated `.h3c` at the output path (plus small `_tmp_*`
     intermediate files next to the source `.h3c` - safe to delete after).

All scripts default to game path `F:/Games/HoMM 3 Complete` - pass `--game "..."` to override.
