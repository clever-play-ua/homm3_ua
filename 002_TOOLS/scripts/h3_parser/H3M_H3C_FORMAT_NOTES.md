# HoMM3 .h3m / .h3c structural parser — status & notes

**Goal:** extract every piece of translatable text (hero bios, guard/quest
messages, seer's hut text, sign posts, town/hero names, campaign prolog/
epilog, rumors...) out of the game's binary map and campaign files, EN and
UA side by side, the same way `002_TOOLS/scripts/build_raw.py` already does
for the flat `*.TXT` files in `H3bitmap.lod`.

This turned out to need two things that don't exist anywhere as a ready
tool: a byte-accurate `.h3m` map parser, and a `.h3c` campaign-wrapper
parser built on top of it. Both now exist here, from scratch, verified
against a real open-source C implementation rather than guessed. This file
is the map of what's solid, what's shaky, and where to pick the work back
up.

## TL;DR status

**This is now a working READ-EDIT-WRITE pipeline, not just a reader, for
ALL 20 official campaigns (RoE + AB + SoD), not just the original 7.**
You can extract a campaign's translatable text (wrapper AND in-map) to
`{var, en, ua}` JSON pre-filled from Hurtom's fan translation, hand-correct
it, and rebuild a working, crash-free, in-game-verified translated `.h3c`
— confirmed end-to-end in-game for `GOOD1.h3c`: **the full 3-mission
campaign was played through to completion** with the campaign name/desc,
every scenario's prolog/epilog, every map's name/desc/rumors/events/
signs/town names all in Ukrainian, no crashes, no missing heroes, hero
carry-over between missions working normally. Getting from "looks right
in every static check" to "actually works in-game" took finding one
extremely non-obvious, load-bearing bug - **read
[the h3m_size section below](#the-actual-root-cause-of-old-map-format--missing-heroes-stale-h3m_size)
before touching this area again**, it will save hours.

**UPDATE - the AB/SoD campaign-player blocker is fixed too** (see
[Open issue, now resolved](#open-issue-absod-campaign-player-section)) -
all 20 campaigns / 87 scenarios now parse structurally clean, and the
fix was verified against all 160 standalone maps in the game's own
`Maps` folder with zero regressions. Not yet re-verified in-game for an
AB/SoD scenario the way GOOD1 was (that's the natural next step, and may
still turn up an h3m_size-style "passes every static check but breaks
in-game" surprise - budget time for that before declaring AB/SoD done).

| Piece | State |
|---|---|
| `h3m_parser.py` — standalone `.h3m` map parser (read) | **160 / 160** maps in the game's own `Maps` folder parse cleanly (RoE + AB + SoD), plus all 87 campaign scenarios below |
| `h3c_parser.py` — `.h3c` campaign wrapper (read) | Wrapper-level parsing works on every campaign tried |
| `h3c_writer.py` — rewrite the `.h3c` wrapper's text (campaign name/desc, per-scenario prolog/epilog) | **Working, in-game verified.** See [Multi-gzip-member format](#critical-a-h3c-file-is-multiple-independent-gzip-streams-not-one) below - this is the part that was wrong for a long time this session |
| `h3m_writer.py` — rewrite one scenario's in-map text (map name/desc, hero names/bios, events, town names, quest/sign/guard messages, rumors...) | **Working, in-game verified** for `GOOD1.h3c` scenario 0; structurally clean (not yet in-game verified) for all AB/SoD scenarios too |
| `build_mission_texts.py` — lay out a whole campaign's wrapper+map text as one `{var,en,ua}` JSON per numbered mission folder, matching the `005_RAW` convention | **Working**, run for `GOOD1` → `005_RAW/001_Long_Live_the_Queen/missions/001_Homecoming/` etc. |
| End-to-end `.h3c` → per-scenario `.h3m` structural parse, fully clean | **20 / 20** official campaigns, **87 / 87** scenarios - see [Open issue, now resolved](#open-issue-absod-campaign-player-section) |
| Fallback that already covers all 20 campaigns for *reading* today | `extract_campaigns.py`'s heuristic string-scan + DP alignment, `005_RAW/<NNN>_<Campaign>/texts.json` — reading only, not wired to a writer |

If you're picking this up cold and just want to translate any campaign:
use `build_mission_texts.py` to get JSON, hand-correct the "ua" fields,
then `h3c_writer.py rebuild` + `h3m_writer.py rebuild` (chained, wrapper
first) to get a working `.h3c` back, inject with `mmarch add` into
`H3bitmap.lod`/`H3ab_bmp.lod`, **and run `fix_lod_sort_order.py` on both
archives afterward - not optional, see below.** AB/SoD campaigns are now
structurally reachable the same way RoE ones are - just budget time for
an in-game smoke test before trusting them the way GOOD1 is trusted.

## Files in this folder

- `h3m_parser.py` — the `.h3m` parser. Import `parse_h3m(decompressed_bytes)`,
  get back `(reader, format, texts, object_count, event_count)`. `texts` is
  a list of `(label, raw_bytes)` — decode `raw_bytes` as `cp1252` for the
  English game files, `cp1251` for the Hurtom Ukrainian ones (same
  convention as everywhere else in this repo). Run standalone:
  `python h3m_parser.py SomeMap.h3m` (it gzip-decompresses for you).
- `h3c_parser.py` — the `.h3c` campaign wrapper, layers on `h3m_parser.py`.
  `parse_h3c(decompressed_bytes)` returns campaign name/desc, a list of
  per-scenario dicts (name, prolog, epilog, blob bytes, parsed texts...).
  Run standalone: `python h3c_parser.py SomeCampaign.h3c`.
- `reference/` — the actual C source this was verified against (MIT-licensed
  `homm3tools`, see `reference/ATTRIBUTION.md`), so the next session doesn't
  need internet access to re-derive any of this. Worth reading directly
  when extending the parser — it's more reliable than this document's prose.
- `h3c_writer.py` — rewrites the `.h3c` wrapper's own text fields (campaign
  name/desc, per-scenario prolog/epilog). `extract(h3c_path, out_json,
  ua_source_path=None)` writes `{var, field, en, ua}` JSON (var prefixed by
  the file's stem, e.g. `GOOD1_campaign_name`); pass `--ua-source` pointing
  at a Hurtom-translated `.h3c` of the same campaign to pre-fill "ua"
  automatically (same structure, so field-for-field matching just works).
  `rebuild(h3c_path, json_path, out_path)` writes a new `.h3c` with "ua"
  values substituted wherever non-empty, everything else byte-for-byte
  identical. Run standalone: `python h3c_writer.py extract Good1.h3c out.json
  --ua-source ../../001_ORIGINAL_HOMM3_FILES_HURTOM/GOOD1.H3C` /
  `python h3c_writer.py rebuild Good1.h3c out.json Good1_ua.h3c`. **Read
  the "critical" section below before touching this** - an earlier version
  of this file got the container format wrong in a way that silently broke
  the game while still passing every check this project's own parser did.
- `h3m_writer.py` — same idea, for ONE scenario's own in-map text (map
  name/desc, hero names/bios, event/quest/sign/guard messages, town names,
  rumors - anything `h3m_parser.py`'s `texts` list finds). Needs a
  scenario index (0-based, matching `h3c_writer.split_h3c()`'s scenario
  order). `extract(h3c_path, scenario_idx, out_json, ua_source_path=None)`
  / `rebuild(h3c_path, scenario_idx, json_path, out_path)`. Chain with
  `h3c_writer.py` (wrapper first, its output as this one's input) to
  translate both levels into one final file. Run standalone:
  `python h3m_writer.py extract Good1.h3c 0 out.json --ua-source ...`
  / `python h3m_writer.py rebuild Good1.h3c 0 out.json Good1_ua.h3c`.
- `build_mission_texts.py` — the practical one-shot tool: runs both writers'
  `extract` for every scenario in a campaign and lays the combined
  `{var, field, en, ua}` records out as `NNN_<MapName>/texts.json` under a
  given output folder, matching this project's `005_RAW` numbering
  convention. `field` values are prefixed `wrapper_` (prolog/epilog) or
  `map_` (everything from inside the `.h3m`) so it's obvious which writer a
  correction needs to go back through. Run:
  `python build_mission_texts.py Good1.h3c ../../../005_RAW/001_Long_Live_the_Queen/missions --ua-source ../../../001_ORIGINAL_HOMM3_FILES_HURTOM/GOOD1.H3C --stem GOOD1`
- `fix_lod_sort_order.py` (in `002_TOOLS/scripts/`, one level up, not in
  this folder) — **mandatory** last step any time a `.h3c` (or any other
  file) is injected into `H3bitmap.lod`/`H3ab_bmp.lod`/etc via `mmarch
  add`. See [LOD sort-order bug](#unrelated-but-load-bearing-the-lod-sort-order-bug) below.

## CRITICAL: a `.h3c` file is MULTIPLE independent gzip streams, not one

This cost a large amount of debugging time this session and is the
single most important correction to internalize before touching `.h3c`
writing again. The wrong model (which this document itself stated until
now, and which `h3c_parser.py`'s docstring still describes for *reading*
- reading happens to work under the wrong model, see why below) was:
"the whole `.h3c` file is one `gzip.decompress()` call's worth of data."

**The real structure:** a `.h3c` file is N+1 separate, independently
gzip-compressed streams concatenated back-to-back in the raw file. Member
0 is the "header block" (campaign name/desc + every scenario's own
filename/`h3m_size`/prolog/epilog, back-to-back, nothing else). Members
1..N are each one scenario's embedded `.h3m` map, in scenario order,
completely independent of each other and of the header.

**Proof:** search the raw file for the gzip magic bytes (`1f 8b 08`) -
you'll find exactly N+1 hits for an N-scenario campaign (verified:
`Good1.h3c`, 3 scenarios, hits at raw offsets `0, 1272, 27470, 37209`).
Decompressing each byte range between consecutive hits *separately*
reconstructs the exact same flat content that one big `gzip.decompress()`
over the whole file produces - **this is why reading always worked**:
Python's gzip module transparently walks through concatenated members and
returns their content concatenated, so treating the file as "one stream"
for *reading* gives the right bytes purely by accident of how multi-member
gzip decoding works, not because the file actually is one stream.

**This also resolves the `h3m_size` mystery documented below as
unusable:** `h3m_size` is not the decompressed map size (which is what
everyone, including `homm3tools`' own struct comment, assumed) - it's the
exact **compressed byte length of that scenario's own gzip member**.
Verified exactly: `Good1.h3c` scenario 0's `h3m_size` field reads `26198`,
and its raw gzip member (from the 2nd magic-byte hit to the 3rd) is
*exactly* 26198 bytes. VCMI's own from-scratch engine reimplementation
(`lib/campaign/CampaignHandler.cpp`, confirmed by reading its source)
reads the file the same way - as a compressed stream of discrete blocks,
first block header, one block per map - and explicitly comments that this
field ("packedMapSize") is "not used" for navigation, only sequential
per-block reading is.

**Why this matters for WRITING and not reading:** decompressing the whole
file as one blob, editing it, and recompressing the result as a NEW SINGLE
gzip stream (the wrong approach an earlier version of `h3c_writer.py` in
this session took) produces a file whose *decompressed content* can be
byte-identical to a correct rebuild and which still passes every
consistency check this project's own from-scratch parser runs (the
0-or-124-trailing-bytes rule, object/event counts matching) - **but
breaks the real game**, because the real game's reader expects to find a
fresh, independent gzip member exactly where the next one should start,
and a single-member file has no such boundary after the header.
**Symptom when this goes wrong:** the top-level campaign name/description
can still show up translated correctly (that part is read while still
inside member 0, which was genuinely intact), but every individual
scenario shows a generic "old map format" fallback for its own name and a
blank description, and the game crashes outright when you actually try to
start a scenario.

**The fix, implemented in the current `h3c_writer.py`/`h3m_writer.py`:**
- Split the raw file into its true members first (`split_h3c()` in
  `h3c_writer.py`, by scanning for gzip magic bytes).
- Decompress and edit ONLY the header member (for wrapper text) or ONE map
  member (for in-map text) on its own.
- Re-compress ONLY the member(s) you actually changed as their own
  complete, independent gzip streams.
- Concatenate: (possibly new) header member + each scenario member
  (possibly new for the one you edited, otherwise the ORIGINAL raw
  compressed bytes, untouched, never even decompressed).

This is also good news for future in-map editing: because each scenario's
map is a fully independent gzip member, editing scenario 2's text can
never affect scenario 0 or 1's bytes at all, or the header - there is no
shared offset table anywhere across members to keep in sync, only within
one member's own sequential byte stream (which itself has no offset table
either - see next section).

## THE actual root cause of "old map format" / missing heroes: stale `h3m_size`

This is the single most important thing in this document. It cost an
entire, very long, very confusing debugging session (crash reports,
"old map format" fallback shown for a translated scenario, heroes missing
after a scenario transition, "mission 2 loads mission 1's content") that
kept recurring across multiple supposedly-fixed rebuilds, because every
OTHER check available kept passing: this project's own from-scratch
parser reported a clean parse (0-or-124 trailing bytes) on the rebuilt
file, a full segment-by-segment diff against the pristine original showed
**zero** unexpected byte differences outside the intended text
substitutions, the standalone extracted `.h3m` opened perfectly in the
real Heroes 3 Map Editor (`h3maped.exe`) with all heroes/objects present,
and even the gzip container header bytes were made to match the original
exactly (see `compress_h3_gzip()` above) - and it STILL broke in-game.

**The actual bug:** each scenario's `h3m_size` field in the `.h3c`
header (see the wrapper layout above) records that scenario's own gzip
member's COMPRESSED byte length - confirmed exactly correct earlier in
this document. What wasn't appreciated until much later: **the game
apparently relies on this value being accurate** (most likely to size a
read/allocation buffer before decompressing that member) - it is not
just informational. Translating a scenario's map text changes its
compressed size (almost always - even a handful of translated characters
shifts DEFLATE's back-reference patterns enough to change the output
byte count), but nothing in the original `h3c_writer.py`/`h3m_writer.py`
touched this field - `h3c_writer.py`'s own header rebuild just copies the
4 bytes through unchanged (correctly, from ITS perspective, since it
never touches map data), and `h3m_writer.py` never touched the header at
all. Left stale, that ONE scenario silently breaks the moment the game
tries to actually load it - while remaining structurally perfect by
every static check, because none of those checks cross-reference this
field against the real member size.

**How this was finally found** (repeat this method if a similarly
"impossible" bug shows up again - trust reproducible isolation over
theorizing from the format spec):
1. Bisected by rebuilding with only ONE side of the pipeline touched at
   a time - "wrapper fully translated + maps 100% untouched" (played a
   full campaign through to completion, zero issues) vs "wrapper
   untouched + one map translated" (loaded fine when reached directly).
   This ruled out the wrapper-text-length-change theory that seemed most
   obvious at first (it's genuinely harmless - independent gzip members
   don't care how long the header member is).
2. Combined both (wrapper translated + that same one map translated) and
   the bug reappeared on that specific scenario - proving it needs BOTH
   an edited map AND being read as part of an assembled multi-scenario
   file, not something wrong with the map bytes in isolation (which the
   map editor test had already cleared).
3. A user-requested direct comparison ("compare almost byte-for-byte
   against Hurtom's own known-working translated file") led to spotting
   the gzip container header metadata mismatch first (real, but turned
   out to be a red herring or at best a minor contributing factor - see
   below) - fixing it did NOT resolve the bug on its own.
4. Only checking the ACTUAL compressed member size against the
   DECLARED `h3m_size` in the header (a check nobody had run until this
   point - everything else checks the DEcompressed content, not this one
   header field) revealed the mismatch immediately and unambiguously.

**Fix:** `h3c_writer.patch_h3m_sizes(raw_h3c_bytes)` re-derives every
scenario's `h3m_size` from the real current compressed member size and
returns the corrected file. `h3m_writer.py`'s own `rebuild()` now calls
this automatically as its last step, so a normal `h3m_writer.py rebuild`
invocation can no longer produce a file with a stale `h3m_size` - but
if you ever hand-roll a different pipeline that edits map members
without going through `h3m_writer.rebuild()`, you MUST call
`patch_h3m_sizes()` yourself as the final step, on the fully-assembled
output, after every map edit is done.

**On the gzip container header bytes (`compress_h3_gzip()`):** real
HoMM3 files (both the original English ones and Hurtom's Ukrainian
translation) have gzip members with header bytes
`1f8b080000000000000b` (mtime=0, XFL=0, OS byte 0x0B/NTFS), while
Python's `gzip.compress()` defaults produce something like
`1f8b08009e2e9d6a02ff` (real timestamp, XFL=2 for max-compression, OS
byte 0xFF/unknown). `compress_h3_gzip()` matches the original exactly
(compresslevel=6, mtime=0, then manually patches the OS byte since
Python's API doesn't expose it). This was fixed and tested BEFORE the
real `h3m_size` bug was found, on the reasonable theory that an old/
minimal custom decoder might be strict about these metadata bytes - and
it's kept, since matching a known-working format exactly costs nothing
and rules out one more variable - but it was NOT sufficient on its own
to fix the actual bug, so treat it as "correct and harmless, not proven
necessary" rather than load-bearing the way `h3m_size` is.

## Unrelated but load-bearing: the LOD sort-order bug

Not a `.h3c`/`.h3m` issue at all, but hit while testing `.h3c` injection
and it will silently break ANY translated file (not just `.h3c`) if
skipped: `mmarch add` replaces an existing `LOD` archive entry by deleting
it from its original table slot and appending the new one at the END of
the file's entry table, instead of overwriting in place. HoMM3's `.lod`
archives store entries in case-insensitive alphabetical order and the
game's own `ResourceManager` does a binary search assuming that order -
so any entry moved out of position becomes unfindable by the game, even
though the entry is still physically present and `mmarch` itself can
extract it fine (it does a generic/linear scan, so it doesn't care about
order). Confirmed symptom: `ResourceManager::GetText could not find the
"text" resource "campbttn.txt"` immediately on trying to open the
multiplayer/campaign menu, right after running `build_mod.py`.

**Fix:** `002_TOOLS/scripts/fix_lod_sort_order.py <archive.lod> [more...]`
re-sorts an LOD's entry table back into case-insensitive alphabetical
order in place (pure metadata reorder - the actual file data blobs don't
move, so this is cheap and safe). `build_mod.py` now calls this
automatically as its last step - **any other script or manual `mmarch
add` sequence that touches these archives must call it too, or the
translation will silently break the game the same way.**

## How both files were actually built (so you can trust — or distrust — them)

1. Started from `reference/h3m_corpus.txt`, a community-written prose
   description of the `.h3m` format. **It has at least one real error** (see
   `reference/ATTRIBUTION.md`) — don't treat it as ground truth.
2. Found `potmdehex/homm3tools` on GitHub — a real, working C library
   (`h3mlib`) that programs actually use to read/write `.h3m` files. Its
   struct definitions (`reference/h3m_headers/*.h`) and parsing code
   (`reference/h3m_parsing/*.c`) are the *actual* ground truth used here.
   Every field in `h3m_parser.py` was checked against these, not just the
   prose doc.
3. Validated by running the parser on 151 real, diverse fan-made `.h3m`
   maps (in `001_ORIGINAL_HOMM3_FILES_HURTOM/`) across all three game
   versions, and checking that it consumes the *entire* decompressed buffer
   down to exactly 0 or 124 trailing bytes. **124 is not arbitrary** — the
   original C source has a comment: *"Last 124 (0 for HD Edition maps)
   bytes are padding, we should have reached them"*. Hitting that number
   is a strong, cheap correctness signal — use it whenever you touch this
   code.
4. For `.h3c`: there is no reference struct at all (see below). Reverse-
   engineered by hand against `Good1.h3c` (byte-by-byte, hex dumps,
   confirmed hypotheses against 6 more campaigns).

## `.h3c` wrapper format (reverse-engineered, not from any doc)

After one `gzip.decompress()` of the whole `.h3c` file:

```
uint32  format              (encoding hint for the header strings)
uint8   campaign_map_id
pstr    campaign_name
pstr    campaign_description
uint8   fixed_difficulty
uint8   music

# repeated once per scenario, in campaign order, NO count field anywhere -
# keep reading scenarios until the next thing found is an h3m format marker
# (0x0E/0x15/0x1C/0x1D) instead of another filename pstr:
pstr    scenario_filename        e.g. "Good-1a.h3m" (cosmetic only)
uint32  h3m_size                 DO NOT TRUST THIS - see below
3 bytes unknown/flags
pstr    prolog_text              shown before the mission starts
3 bytes unknown/flags
pstr    epilog_text              shown after the mission ends
??? bytes "starting bonus" block - NOT understood, see below

# after ALL scenarios' map_info blocks (not interleaved!), the actual
# embedded map data, back to back, one raw (still-uncompressed, no nested
# gzip) .h3m byte stream per scenario, same order as above.
```

Concretely, `pstr` here is the same `uint32 length + bytes` Pascal string
used everywhere else in HoMM3 files (see the LOD `*.TXT` tooling).

### Why `h3m_size` can't be trusted

The `H3C_MAP_INFO` struct in `homm3tools`' own `h3c/h3clib/h3c.h` names this
field `h3m_size` and comments "size of this map's h3m data found in this
file". Empirically this is wrong, or at least not what it looks like: for
`Good1.h3c`'s first scenario it reads `26198`, but the actual embedded `.h3m`
blob is `126055` bytes (found by just running `h3m_parser.parse_h3m` on it
and seeing where it cleanly stops). Don't try to use this field for
anything. `h3c_parser.py` reads it (into `scenario['h3m_size']`) but then
**ignores it** for blob boundaries — see next section.

### How blob boundaries are actually found

Since `h3m_size` is unusable and the "starting bonus" block between a
scenario's epilog and the next scenario's filename has an unknown, variable
length, `h3c_parser.py` sidesteps understanding it byte-for-byte (this is
also what `homm3tools`' own `h3c/h3clib/h3clib.c` does — it's a hacky
`memmem()`-based format converter, not a real parser, because *even the
original library author* didn't fully reverse this):

- `find_next_h3m_name()` — regex-searches forward for the next
  `uint32 len + "*.h3m"` pstr, to find the next scenario's map_info.
- `find_next_h3m_blob_start()` — searches forward for a 4-byte format
  marker (`0x0E`/`0x15`/`0x1C`/`0x1D`) immediately followed by a plausible
  `is_playable` byte (`0` or `1`), to find where the map_info list ends and
  the actual embedded map data begins.
- Once inside the blob region: run `h3m_parser.parse_h3m()` on
  `data[offset:]`, trust `reader.p` (bytes actually consumed) as that
  scenario's true blob length, then skip forward over zero-padding bytes to
  the next format marker for the next scenario.

This worked end-to-end (down to the same 0-or-124-byte trailing rule as
standalone maps) for every RoE campaign tried. It is a legitimate, if
inelegant, strategy — not a hack you should feel obligated to replace,
*if* the underlying `h3m_parser.parse_h3m()` call succeeds. The open issue
below is about cases where it doesn't.

## Campaign name → file mapping, and RoE/AB/SoD split

Already worked out and hardcoded in `../extract_campaigns.py`'s `CAMPAIGNS`
list (20 entries, stem → display name, in campaign-select order). Reuse
that list rather than re-deriving it — it was cross-checked against
`CAMPTEXT.TXT`'s "Campaign Map Names" section and each file's own internal
name string.

The RoE/AB/SoD split mattered a lot here historically (before the fix
below): **RoE** (7 campaigns: `GOOD1`, `GOOD2`, `GOOD3`, `EVIL1`, `EVIL2`,
`NEUTRAL1`, `SECRET1`) always parsed end-to-end cleanly, while **AB** (6:
`AB`, `BLOOD`, `SLAYER`, `FESTIVAL`, `FOOL`, `FIRE`) and **SoD** (7:
`CRAG`, `YOG`, `GEM`, `GELU`, `SANDRO`, `FINAL`, `SECRET`) all failed
inside `parse_players()`'s per-player owned-hero block. **This is now
fixed — see [Open issue: AB/SoD campaign player section](#open-issue-absod-campaign-player-section-resolved)
— all 20 campaigns parse identically today.**

## Open issue: AB/SoD campaign player section — RESOLVED

**Symptom (historical):** inside a campaign-embedded AB/SoD scenario
(never in a standalone map), one of the 8 players' "owned hero names"
trailing block (the old `has_ai` branch in `parse_players()`) read an
absurd `heroes_count` (examples actually seen: `16384` = `0x4000`,
`131072257` = `0x07D00001`), which then read garbage names in a loop
until it ran off the end of the buffer.

**Actual root cause, found by taking `AB.h3c` (both the plain English
extract and Hurtom's Ukrainian translation of it — same underlying
structure, ruling out a "different resave" theory), hex-dumping the
player section byte-by-byte, and hand-decoding it field-by-field against
`reference/h3m_headers/players_h3m_player.h` /
`players_h3m_player_ai.h`:**

`H3M_PLAYER_AI_ABSOD` (the "owned heroes" block: `unknown1` byte +
`heroes_count` u32 + that many `(type, name)` entries) is **NOT**
conditional on the player having a specific (non-`0xFF`) starting hero
type. It is present **unconditionally, for every one of the 8 players,
immediately after that player's main struct, in every AB/SoD-format
scenario** (RoE has no such block at all). The old code only read it
when `htype != 0xFF`, which happened to work for the first scenario of
a campaign (nothing carried over yet, so every player's owned-hero list
is empty either way both models agree there) but broke the instant a
player had zero specific starting heroes on the map *and* one or more
heroes carried over from a previous scenario (`heroes_count > 0`) — a
completely normal, common case from mission 2 onward. Confirmed by
`AB.h3c` scenario 6, player 1: `htype == 0xFF` (no specific starting
hero shown) yet `heroes_count == 3` with three named types — real
carried-over heroes the old code never read, silently shifting every
byte after it.

A second, independent bug in the same area compounded this for some
campaigns: the SoD-only per-hero customization loop (156 entries, "does
this hero have custom experience/skills/artifacts/biography/gender") was
reading all 7 `has_X` flag bytes **up front**, then processing their
payloads afterward. The real, corpus-confirmed layout interleaves each
flag with its own payload (`has_experience` → `[experience]` →
`has_secondary_skills` → `[skills]` → `has_artifacts` → `[artifacts]` →
`has_biography` → `[bio]` → `gender` → `has_spells` → `[spells]` →
`has_primary_skills` → `[skills]`). The flat-read version only survives
when every hero's sub-flags are all zero, which is why it silently
worked for most maps and only broke `GEM`/`SANDRO`/two `FINAL` scenarios
— the ones where the map actually customizes a hero's skills, artifacts,
or biography.

**Fix (both bugs), in `h3m_parser.py`'s `parse_players()` and
`parse_ai_section()`:**
- `parse_players()`: read the owned-heroes block (`unknown1` + count +
  entries) unconditionally whenever `is_ab_or_sod(fmt)`, right after
  *every* player's main struct — not gated on that player's own starting
  hero type. Also stopped reading `face`/name unconditionally for the
  ABSOD "default hero" struct variants (`e0`/`e1` when `htype == 0xFF`)
  — empirically these behave like RoE's simpler 2-byte variant in real
  files, contradicting the theoretical struct layout in
  `players_h3m_player.h` (which itself calls some of these "never seen,
  merely predicted").
- `parse_ai_section()`'s 156-hero customization loop: interleaved each
  `has_X` flag with its own payload in the corpus's documented order,
  instead of reading all 7 flags before any payload.

**Verified:** all 20 official campaigns / 87 total scenarios now parse
structurally clean end-to-end (`h3m_writer.parse_h3m_tracked`, remaining
bytes = 0 or 124 in every case) — up from 7/20 (RoE only) before this
fix. Re-ran the same parser against all 160 standalone `.h3m` files in
the game's own `Maps` folder afterward: **zero regressions**, still
160/160 clean. Not yet re-verified *in-game* the way `GOOD1` was (full
playthrough) — do that before fully trusting an AB/SoD rebuild the way
GOOD1's pipeline is trusted; the `h3m_size` bug earlier in this document
is a reminder that "parses perfectly" and "works in-game" are not
automatically the same thing.

## Campaign-wide closing narration field (not per-scenario, easy to miss)

After the LAST scenario's epilog, some campaigns have ONE more optional
text field: a whole-campaign closing narration shown after the final
cutscene video (e.g. AB: "Lucifer Kreegan is dead..."). Found this by
literally grepping that English sentence into the raw `.h3c` header bytes
after a user reported an untranslated line on the campaign's closing
screen - it sat inside what `read_header_segments()` used to treat as one
opaque trailing "bonus block" blob for the last scenario, so it was never
extracted OR translated even though Hurtom's own file has a complete
Ukrainian translation for it sitting right there (this was never a video
problem - pulled frames from the actual `.smk` with ffmpeg and confirmed
zero baked-in text; the engine draws this as a text overlay from the
`.h3c`, same mechanism as every prolog/epilog). Same shape as every other
prolog/epilog (3 unknown bytes, then a normal length-prefixed string), tagged
`campaign_epilogue` in `read_header_segments()`. Empty (length 0) for
campaigns without this extra screen. Checked all 20: RoE campaigns and
`SLAYER`/`FESTIVAL`/`FOOL` are empty; `AB`, `BLOOD`, `FIRE`, `CRAG`, `YOG`,
`GEM`, `GELU`, `SANDRO`, `FINAL`, `SECRET` all have real closing text that
was silently being dropped on every previous rebuild. `build_mission_texts.py`
now includes it in the `000_..._description` folder's JSON alongside
`campaign_name`/`campaign_desc`.

## FINAL.h3c-specific bug: preconditions bitmask width

While fixing the above, `FINAL` (Unholy Alliance, 12 scenarios - the only
campaign with more than 8) crashed with a garbage prolog length for
scenario 0. Root cause: between each scenario's `h3m_size` and its prolog,
there are 2 fixed unknown bytes plus a "which earlier scenarios must be
completed first" bitmask (1 bit per scenario) - `ceil(scenario_count/8)`
bytes. Every other campaign has <=8 scenarios so this bitmask is always 1
byte, making the gap a hardcoded-looking "3 bytes" that worked by pure
coincidence everywhere except `FINAL`, which needs 2 bytes there (4 total).
Found by byte-diffing the exact gap size against a real string boundary
(searched for the known English prolog text, measured backward to find
where its real length prefix actually starts). Confirmed this bitmask
only affects the pre-prolog gap, not the pre-epilog one (that one stayed a
constant 3 bytes in the same file). Fixed in `read_header_segments()`:
`precond_bytes = (scenario_count + 7) // 8`, gap is `2 + precond_bytes`.
Verified: all 20 campaigns' wrapper headers now round-trip byte-identical
on a no-op extract+rebuild, and all 87 scenarios still parse clean.

## Bugs already found and fixed this session (don't reintroduce them)

1. **`parse_guardians()` was missing a trailing 4-byte `unknown1` skip**
   after the optional creatures block. Silent 4-byte drift that only
   surfaced ~24 objects later as a garbage string length. Fixed by adding
   `r.skip(4)` at the end of that function.
2. **AI-section order was wrong**: the SoD "custom heroes" list
   (`H3M_AI_CUSTOM_HERO_SOD`, i.e. named custom heroes with
   type/face/name/allowed_players) was being parsed *after* rumors and
   conflated with the *hero_settings[156]* per-hero-attributes block.
   The real order (per `H3M_AI_SOD` struct) is: teams → available_heroes →
   `empty`/placeholder-heroes → **custom_heroes** → reserved[31] →
   available_artifacts/spells/skills → rumors → **hero_settings[156]**.
   Both blocks now exist and are in the right place.
3. **Player struct field count for the "type == 0xFF" cases in ROE**: the
   corpus doc claims `face` + a name pstr always follow `is_random`+`type`.
   The real `H3M_PLAYER_EXT_ROE_DEFAULT`/`_WITH_TOWN_ROE` structs say
   otherwise — those two cases are *only* 2 bytes / 5 bytes total, no face
   or name at all. (AB/SoD is different again — there, even the
   `type == 0xFF` cases *do* always carry face+name. Don't conflate the two
   format families.)

## Validation

Re-run any time you change `h3m_parser.py`:

```bash
# against every standalone .h3m in the Hurtom map pack (RoE/AB/SoD mixed)
python - <<'PY'
import gzip, glob, os, sys
sys.path.insert(0, ".")
from h3m_parser import parse_h3m

folder = r"../../../001_ORIGINAL_HOMM3_FILES_HURTOM"
ok, bad = 0, []
for path in sorted(glob.glob(os.path.join(folder, "*.h3m"))):
    try:
        data = gzip.decompress(open(path, "rb").read())
        r, *_ = parse_h3m(data)
        (ok := ok + 1) if r.remaining() in (0, 124) else bad.append((path, r.remaining()))
    except Exception as e:
        bad.append((path, str(e)))
print(f"OK: {ok}, FAILED: {len(bad)}")
for p, e in bad: print(" ", os.path.basename(p), e)
PY
```

Last known result: **150/151 OK**. The one failure, `Marshland Menace.h3m`,
drifts inside the SoD `hero_settings[156]` loop in a way that was *not*
resolved (different symptom from, but possibly the same root cause as, the
AB/SoD campaign issue above — both involve a "which byte is `has_ss` /
`heroes_count` really at" confusion in a hero-attribute block). Worth
tackling both together.

For `.h3c`, re-run the per-campaign smoke test shown in the shell loop used
this session (extract all 20 EN `.h3c` files with `mmarch`, then
`python h3c_parser.py <file>` on each, and grep for `diff=124`).
