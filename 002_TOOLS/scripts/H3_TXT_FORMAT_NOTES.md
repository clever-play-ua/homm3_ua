# H3 flat .TXT resource format - investigation notes

Companion to `h3_parser/H3M_H3C_FORMAT_NOTES.md`, but for the OTHER text
format this project deals with: the flat, line/record-indexed `.TXT`
resource files inside `H3bitmap.lod`/`H3ab_bmp.lod` (`GENRLTXT.TXT`,
`ADVEVENT.TXT`, `ARTEVENT.TXT`, `CAMPTEXT.TXT`, `HELP.TXT`, ...). Read this
before touching `006_build_mod.py`'s/`002_build_raw.py`'s `.txt` handling,
or `h3_txt_records.py`, again.

## THE REAL ROOT CAUSE (found much later): line-ending bytes are part of the format, not cosmetics

Everything below this section was true and worth keeping, but it was all
downstream of chasing a SYMPTOM (record misalignment) while the actual
mechanism stayed hidden for a very long time - a right-click on a neutral
creature stack showed random garbage text ("Кулон мужності +3\"", "Загони
%d рас %d\"") instead of "Мало/Кілька/Загін/...", different garbage every
time, and it survived every fix attempt above, including bringing
`ArrayTxt.txt` to **zero structural differences** (record count, quote
count, embedded-newline count, all 1:1) against a confirmed-working
Russian reference file. That last fact should have been the giveaway
sooner: if two files are byte-for-byte structurally identical by every
metric `split_txt_records()` can see, and one works while the other
doesn't, the bug is in something that metric can't see.

**The actual rule**: inside a quoted multi-line record, the embedded line
break must be a **bare `\n` with no `\r`**. The `\r\n` sequence is
reserved exclusively for the real separator BETWEEN records. This project's
own `split_txt_records()` doesn't care about this distinction at all - it
strips every `\r` unconditionally (`if ch == '\r': continue`) before
looking at `\n`, so it reports the exact same "record count" and "shape"
whether a file follows this rule or not. The real, closed-source game
engine almost certainly does NOT do quote-aware parsing the way VCMI's
`CLegacyConfigParser` (and this project's own parser, modeled on it) does
- it appears to split records on literal `\r\n` directly, full stop. A
file where every embedded newline has been normalized to `\r\n` reads to
the real engine as having far MORE records than it actually has, and every
index after the first such multi-line record silently drifts - which
exactly explains "always garbage, different garbage each time, from
elsewhere in the same file."

Confirmed with raw counts across `ArrayTxt.txt` (EN/RU/French official
localizations, all working in-game, vs. this project's Ukrainian file):

| file | total `\n` | `\r\n` pairs | bare `\n` (no `\r`) |
|---|---|---|---|
| EN / RU / FR ArrayTxt.txt (all confirmed working) | 375 / 367 / — | **270 / 270 / 270** | 105 / 97 / 105 |
| **this project's UA ArrayTxt.txt (broken)** | 375 | **375** | **0** |
| EN / RU / FR ADVEVENT.txt (all working) | 423 | **191 / 191 / 191** | 232 / 232 / 233 |
| **this project's UA ADVEVENT.txt (broken)** | 423 | **423** | **0** |

In the working files, `\r\n`-pair-count equals the true record count
exactly (270, 191) - every embedded newline is bare `\n`. In the broken UA
files, EVERY newline was `\r\n` - zero bare `\n` anywhere. The three files
this exact corruption hit (`ArrayTxt.txt`, `ADVEVENT.txt`, `CMPEDITR.TXT`)
are precisely the three files a Python script rewrote earlier in this
project (fixing the stray-quote bugs described below) - Python's default
text-mode file writing on Windows silently converts every `\n` to `\r\n`
on write, which is exactly this corruption.

**A second, independent source of the same corruption, found at the same
time**: `git config core.autocrlf` was `true` and `.gitattributes` had
`* text=auto` repo-wide - meaning Git itself would silently re-introduce
this exact corruption (LF -> CRLF) on every future `checkout`/`clone`/
`pull` of these files, even after a byte-perfect manual fix. Fixed by
adding `001_ORIGINAL_HOMM3_FILES_HURTOM/** -text -diff` to
`.gitattributes` - the entire folder of original/translated game resource
files is now opaque bytes to Git, never line-ending-normalized, and shows
as a binary diff (`Bin X -> Y bytes`) instead of a text diff.

**The fix, mechanically**: walk the raw text tracking quote-parity (same
loop as `split_txt_records`, but instead of discarding `\r` characters,
only drop the `\r` of a `\r\n` pair when currently INSIDE a quoted span;
leave `\r\n` untouched outside quotes, since that's the real separator).
This is a pure line-ending-byte transform - verified before writing back
by asserting `original.replace('\r','') == fixed.replace('\r','')`, i.e.
zero textual content changed, only which newlines carry a `\r`.

**A second, unrelated bug this uncovered in `ADVEVENT.TXT` specifically**:
fixing the line-endings alone made the OLD garbage-text bug disappear, but
revealed a new, more specific symptom - the highlighted object-name title
(e.g. "Дерево пізнання"/"Tree of Knowledge") shown inside an event dialog
sometimes named the WRONG object relative to the dialog's own body text
and the status bar underneath it. Root cause: `ADVEVENT.TXT` had 203
records where the true English/Russian/French reference all agree on 191
- a leftover, self-inflicted corruption from an EARLIER pass in this
project (see "Solved with a language-independent signature diff" below)
that, while fixing a stray-quote bug, ALSO rotated every record's
`{Title}` marker one position backward: instead of `"{Title}\n\nBody"` (one
quoted span, title first) each affected record became `"Body."` + a
literal `\n` + `"{NextRecord'sTitle}` (title trailing, unclosed, glued onto
the WRONG record) - correct content, correct reading order, wrong
packaging, and 12 spurious pseudo-records worth of stray artifacts along
the way.

Fixed by full reconstruction, not a patch: walked every one of the 39
still-intact "content" records in the corrupted range (`records[126..202]`
in the pre-fix file), split each on literal `\n` to recover its individual
body pieces and its trailing (rotated) title fragment, then reassembled
each of the 65 true English-equivalent positions as `title_from_previous
+ body_from_current`, using the true English reference's per-position
shape (`"{Title}\n\nBody"` / `"Body"` / plain unquoted `Body` - HoMM3 mixes
all three even within one file) as the template for how to re-wrap each
reconstructed piece. Validated exhaustively before writing anything back:
final record count (191, matching English exactly), zero shape mismatches
against English at any of the 191 positions, and the untouched prefix
(records 0-124) provably byte-identical to what it was before the fix.

**Lesson for next time**: when a translated flat `.TXT` file needs any
programmatic edit, write the result with an explicit `.encode('cp1251')`
to raw bytes (`open(path, 'wb')`), NEVER through Python's default
text-mode file writing - and re-run the bare-`\n`-vs-`\r\n` check above on
any file that has multi-line quoted records, even if `record_count()`
reports a perfect match. A perfect record count is necessary but **not
sufficient** proof of a correctly-formed file.

## The bug: naive `.splitlines()` is the wrong way to count these files

A from-scratch clean rebuild of the mod (`006_build_mod.py` against a
freshly-verified GOG install) reported **16 flat `.TXT` files** with a
"line count mismatch" against Hurtom's translation, and skipped injecting
all of them - leaving GENRLTXT, HELP, HEROBIOS, CAMPTEXT and 12 others in
English. This had never been noticed before because this session was the
first time anyone ran a full from-scratch rebuild and actually read the
skip warnings; every previous deploy touched individual files or archives
directly, one at a time.

The check itself (comparing `len(text.splitlines())` between the English
original and the Ukrainian translation) turned out to be counting the
wrong thing. Confirmed against **VCMI's `lib/texts/CLegacyConfigParser.cpp`**
- an open-source, from-scratch reimplementation of the ORIGINAL game's own
resource loader, built by reverse-engineering the real executable, so its
parsing rules are as authoritative as decompiling the game itself:

- Fields on one record are TAB-separated.
- A record ends at a `\n` that occurs OUTSIDE an open double-quote span.
- A `\n` (or `\r`, or a literal tab) INSIDE an open quoted span is just
  ordinary text content, not a separator - **one record's quoted field
  can legitimately span several physical lines**. This project found the
  exact pattern live in `ADVEVENT.TXT`: a short quoted title on its own
  line (`"{Water Wheel}`), an intentional blank line, then the message
  body, closed by a lone `"` - three physical lines, one real record.
- `""` (two quotes back to back) is the CSV-style escape for one literal
  `"` inside a quoted field.
- A bare `\r` is discarded outright (these files are all Windows CRLF).

`h3_txt_records.py` (new, at the `002_TOOLS/scripts/` root, imported by
both `002_build_raw.py` and `006_build_mod.py`) implements exactly this
rule as `split_txt_records()` / `record_count()`. Once files are compared
by RECORD count instead of raw physical-line count, most of the 16 turned
out to already be correctly translated - the "mismatch" the naive method
saw was never real.

## Per-file resolution

Investigated by hand, one file at a time, comparing `split_txt_records()`
output against the live game's own `H3ab_bmp.lod` copy of each English
file. Three outcomes:

**Already correct - just needed the counting fix (3 files):**
`ARTRAITS.TXT`, `CREDITS.TXT`, `SPTRAITS.TXT` - record counts matched
exactly once quote-aware counting replaced `.splitlines()`. No data
changed at all.

**Real, small, fixable problems in the Ukrainian file (8 files):**

| File | Real problem | Fix |
|---|---|---|
| `ARTSLOTS.TXT` | 1 genuinely extra entry ("Місце 5", a 5th Misc. artifact slot the current build doesn't have) tacked onto the end | removed the 1 trailing line |
| `CMPEDCMD.TXT` | last 2 lines duplicated verbatim | removed the 2 trailing duplicate lines |
| `HEROBIOS.TXT` | 4 duplicate "Микула хоробрий" lines appended at the end | removed them |
| `OBJNAMES.TXT` | 10 extra object-name entries appended at the end, past the real content (which matches English 1:1 up to and including "Trading Post"/"Базар") | removed the 10 trailing lines |
| `ARTEVENT.TXT` | **two separate bugs stacked**: (1) one record (index 90) opens a `"` and never closes it, silently merging every record after it into one giant "quoted" blob when counted naively - found by walking the file and logging every quote-parity flip, which showed exactly one flip, at that record, that never flips back; (2) after fixing the missing `"`, a real +15 extra trailing records remained (same "extra content appended at the end" pattern as above) | added the missing closing `"`, then removed the 15 genuinely-extra trailing records |
| `MONOLITH.TXT` | badly scrambled: the 6 real color translations (green/orange/purple/blue/red/yellow) were present but scattered among 10 bogus, duplicated *ordinal-number* words ("fourth", "fifth", "sixth", "seventh", "eighth" - each appearing twice) that don't belong in a color list at all | rebuilt the file from just the 6 real color words, in the same order as English |
| `SEERHUT.TXT` | Ukrainian file has two entire extra quest-type blocks ("Be hero quest" and "Belong to player quest", 5 rows each = 10 rows) that this specific game build's English file doesn't define at all - pushes the 48 Seer names 10 slots out of alignment | removed the 10 extra quest-definition rows; the 48 names (Abraham...Zoe) line up 1:1 with English again |
| `CAMPTEXT.TXT` | Ukrainian file has full name + region-name support for **all 20** campaigns; this build's English file only defines names/regions for the first 13 (the 7 SoD-era short campaigns' names apparently come from somewhere else in this specific build, not this file) - found instantly via the `//<Campaign> Map Region Names` comment anchors, which showed `//Neutral 1...` sitting where `//Evil 2...` should be | removed the 7 extra campaign-name lines and the 7 extra trailing "Region Names" blocks (58 lines) they went with; verified the comment-header sequence now matches English exactly, ending at `// Armageddon Map Region Names` |

**Solved with a language-independent signature diff (2 more files):**
`ADVEVENT.TXT` and `ARRAYTXT.TXT` - both have both sides using the
multi-line quoted-record format, so a simple "extra records at the end"
pattern doesn't hold; the trick that cracked them: `%s`/`%d`/`%%`
placeholders and literal signed numbers (`+3`, `-1`) are never translated,
so a per-record signature of `(starts-with-a-title-brace, ordered tuple of
%-placeholders, ordered tuple of signed numbers)` is a genuinely
language-independent key. Running `difflib.SequenceMatcher` on the EN and
UA record-signature sequences (not the text itself) finds the true
alignment even when the actual Ukrainian and English sentences share
nothing in common. For `ADVEVENT.TXT` this immediately surfaced a second
stray-quote bug of the same shape as `ARTEVENT.TXT`'s (one record - the
"survivor refuses, no room for the artifact" variant - ends `."""` three
quotes in a row instead of two, silently merging every record after it
into a black hole of merged content until a human eye happened to notice
the "Shrine of Magic Incantation" title text leaking into the *previous*
record's tail); fixing that one stray quote alone took the file from 423
naive lines / 203 miscounted records down to a true, clean 191, then a
signature diff of the now-unstuck file found exactly one more genuinely
extra trailing record (a "Witch's Hut, no one lives here" variant) to
remove, landing on 190 = English's own count exactly. `ARRAYTXT.TXT`
needed no quote fix, just three separate extra blocks removed (a stray
`cMoraleInfo`-adjacent luck-bonus line, four Holy-Ground/Mist-of-Evil
morale entries, and a whole extra "Moat Names" section this build's
combat siege screen doesn't use) - 15 records removed, landing on 255 to
match English.

**A hazard specific to this technique, hit and reverted before it did any
damage:** the signature is intentionally coarse (many short menu-label
records share the same "no title, no placeholders, no numbers" empty
signature), so `SequenceMatcher` can align two completely unrelated
records that merely happen to look alike by signature - it did exactly
this on `CMPEDITR.TXT` (the Campaign Editor tool's OWN UI text, not
in-game content), initially reporting `"Відміна"`/`"Довідка"` (Cancel/Help)
as "extra" content to delete, when they were actually the correct,
needed translations of `EN[42]`/`EN[43]` - deleting them would have been a
real, silent, hard-to-notice content loss. Caught only by then re-running
the diff and noticing English's own `'Cancel'`/`'Help'` had become
orphaned with no Ukrainian counterpart anywhere. Reverted cleanly with
`git checkout` before injecting anywhere. **Lesson: always re-verify a
proposed "extra, delete this" block by confirming the EQUAL-classified
neighboring content still accounts for every real English record - if an
English record goes missing a counterpart only *after* your proposed
deletion, the diff mis-aligned, not the translation.**

## CRITICAL CORRECTION: every fix above was checked against the wrong archive's English reference

After deploying the fixes above and having the user screenshot the exact
same still-English text in-game (Keymaster's Tent, Followers, a dwelling's
recruit prompt, a region name), direct investigation found: **every one of
these flat `.TXT` files exists as a separate, same-named entry in BOTH
`H3bitmap.lod` and `H3ab_bmp.lod`, and the running game reads
`H3bitmap.lod`'s copy** - patching `H3ab_bmp.lod` alone (which every fix
above did, since that's where the original 16-file skip list was
reported) produces a build that verifies clean by every internal check
yet changes nothing the player actually sees. This is the exact same
shape of bug as the campaign `.h3c` "added `_UA.h3c` to the wrong archive"
mistake documented in the `homm3-campaign-deploy-replace-not-add` memory -
found the same way, by a screenshot of stubbornly-still-English text after
an already-"verified" fix.

Re-checking `H3bitmap.lod`'s own English reference for all 8 previously
"fixed" files revealed something more surprising than "wrong archive":
**Hurtom's ORIGINAL, completely untouched translation already matched
`H3bitmap.lod`'s true record count exactly**, for `ARTSLOTS.TXT`,
`CMPEDCMD.TXT`, `HEROBIOS.TXT`, `OBJNAMES.TXT`, `SEERHUT.TXT`,
`CAMPTEXT.TXT`, and `ARRAYTXT.TXT`. Every one of the earlier "extra
content" removals for these 7 files was solving a mismatch that only
existed against `H3ab_bmp.lod`'s smaller/older table - reverted all 7 with
`git checkout` back to Hurtom's pristine original, no changes needed at
all. Even more striking: `MONOLITH.TXT`'s apparently-scrambled 16-entry
structure (colors interleaved with stray, duplicated "four/five/six/
seven/eight" words) turned out to be a byte-faithful translation of
`H3bitmap.lod`'s own English file, which has that exact same odd
structure baked in - not a translation bug, Hurtom translated it
correctly and I mis-diagnosed it as garbage. `ADVEVENT.TXT` and
`ARTEVENT.TXT` were the two genuine exceptions: both have a real stray-
quote bug (`ARTEVENT.TXT` record ~90 missing its closing `"`;
`ADVEVENT.TXT`'s "survivor refuses" record ending `."""` instead of `."`)
that corrupts parsing under BOTH archives' identical quote-aware parsing
rule, so that one-character fix stayed for both; the additional "trim N
trailing records" step that followed each one was `H3ab_bmp.lod`-specific
and got reverted (`ADVEVENT.TXT` needed 191 records to match
`H3bitmap.lod`, not the 190 that matched `H3ab_bmp.lod`).

**Also caused a real, unrelated near-corruption incident while chasing
this**: a PowerShell command meant to extract "the last 3 elements" of a
`git show`-piped file used a negative array-index range
(`$array[($array.Length-4)..($array.Length-2)]`) against an array that,
due to `git show`'s output using bare `\n` line endings (git normalizes
CRLF on commit) rather than the `\r\n` the rest of the script assumed,
had only 1 element - producing an out-of-range slice that silently
returned a large, wrong chunk of text, which then got appended to the
real file before the mistake was noticed. Caught by the standard tell
(`record_count()` jumping to 395 instead of the expected ~191, `git diff
--stat` showing far more changed lines than intended) and fixed by a full
`git checkout` revert and redoing the single-line fix from scratch with
direct, verified string search (`-like '*known phrase*'`) instead of
positional slicing of a separately-fetched reference file.

**How to apply going forward:** when fixing ANY flat `.TXT` file, check
whether the same filename exists in more than one `.lod` archive
(`mmarch list <archive> | grep -i <name>` on each `.lod` under `Data/`)
- if so, get each archive's OWN English reference's record count
independently, do NOT assume they share one true count. Prefer
`H3bitmap.lod`'s reference when both exist (empirically the one the
engine actually reads for RoE/base content) but inject the same fixed
file into whichever OTHER archive(s) hold a copy too - it costs nothing
and covers the case where this priority assumption is wrong for some
other file. Most importantly: **never trust "byte-identical against the
file I intended to fix" as proof a fix mattered - always do one final
extraction straight from the live game path itself and decode the actual
bytes**, the same discipline this project already uses for campaign
`.h3c` deploys.

**Not resolved yet - genuinely need dedicated reconciliation (3 files):**
`CMPEDITR.TXT`, `GENRLTXT.TXT`, `HELP.TXT`.

`CMPEDITR.TXT` is the standalone Campaign Editor tool's (`h3ccmped.exe`)
own UI text - not used during actual gameplay, so low practical priority
- but it turned out to be extensively restructured (whole menu sections
reordered, not just appended-to), which the signature-diff technique
above cannot safely untangle on its own (see the Cancel/Help near-miss).
`GENRLTXT.TXT` and `HELP.TXT` are large (700-900+ records) and not yet
attempted with the signature-diff technique - worth trying next, since it
solved two files of similar size and complexity (`ADVEVENT.TXT`), but
budget real care for each proposed deletion given the demonstrated false-
positive risk. `006_build_mod.py` correctly continues to skip these 3 and
leave them in English until then.

## Open question: `H3bitmap.lod` vs `H3ab_bmp.lod` have DIFFERENT record
counts for the same filenames

Discovered while re-running `006_build_mod.py` after the fixes above:
`H3bitmap.lod` (the base, non-expansion archive) and `H3ab_bmp.lod` (the
Armageddon's Blade archive) each ship their OWN copy of files like
`ADVEVENT.TXT`/`ARTSLOTS.TXT`/`CAMPTEXT.TXT`/etc., and **the two copies
have different record counts** (`H3ab_bmp.lod`'s tables are larger/AB-
expanded). Cross-checking confirmed Hurtom's ORIGINAL, unfixed translation
already matched `H3bitmap.lod`'s (smaller, base-game) record counts
almost exactly - meaning the "16 mismatched files" problem this whole
document is about was **only ever a mismatch against `H3ab_bmp.lod`**.
Fixing these 8 files to match `H3ab_bmp.lod` (done above) necessarily
un-matches them against `H3bitmap.lod`'s own, different English reference
- so after this fix, `006_build_mod.py` skips these same filenames' entry
in `H3bitmap.lod` instead (still correctly refusing to inject a mismatch,
just now on the other archive).

This project is proceeding on the same assumption it already relies on
for the campaign `.h3c` files (verified in-game): with Armageddon's Blade
active - which Complete Edition always has - the engine's ResourceManager
resolves these shared filenames from `H3ab_bmp.lod`, and `H3bitmap.lod`'s
copies are simply shadowed/unused. This is an inference from precedent,
not independently re-verified for this specific handful of flat text
files. If any of `ADVEVENT`/`ARTEVENT`/`ARTSLOTS`/`CAMPTEXT`/`CMPEDCMD`/
`HEROBIOS`/`MONOLITH`/`OBJNAMES`/`SEERHUT`'s in-game text turns out to
still be the old/English content, this assumption is the first thing to
re-check.

## A hazard specific to editing these files: the `Edit` tool corrupts
cp1251

**Do not use the `Edit` tool (or any UTF-8-assuming text editor) to modify
files under `001_ORIGINAL_HOMM3_FILES_HURTOM/*.TXT`.** These files are
`cp1251` (single-byte Windows Cyrillic), and a `git diff` immediately
after an `Edit`-tool change to `ARTEVENT.TXT` in this investigation showed
273 changed lines for what should have been a single 1-character edit -
the tool had silently read the file as if it were UTF-8, replaced every
byte sequence that isn't valid UTF-8 with U+FFFD (the Unicode replacement
character), and written the file back out with those replacements as
real, permanent bytes. Checking the raw bytes confirmed it: the file was
full of literal `EF BF BD` (U+FFFD encoded as UTF-8) where real Cyrillic
text used to be - unrecoverable data loss for anything not still in `git
HEAD`. Caught immediately via `git diff --stat` (a 1-line intended change
showing hundreds of changed lines is the tell), and reverted cleanly with
`git checkout -- <file>` before it could reach a commit.

**The safe way to edit these files**: PowerShell with .NET's own
Windows-1251 encoding, which round-trips byte-for-byte correctly (verified
in this investigation - decode then immediately re-encode reproduced the
original bytes exactly):

```powershell
$enc = [System.Text.Encoding]::GetEncoding(1251)
$bytes = [System.IO.File]::ReadAllBytes($path)
$text = $enc.GetString($bytes)
# ... do the string-level edit on $text or a $text -split "`r`n" line array ...
[System.IO.File]::WriteAllBytes($path, $enc.GetBytes($newText))
```

After ANY edit to one of these files, verify no corruption slipped in
before trusting the result:

```python
data = open(path, 'rb').read()
assert data.count(b'\xef\xbf\xbd') == 0, "UTF-8 mojibake - do not use this file"
```

and check `git diff --stat` - a changed-line count wildly larger than the
edit you intended is the same tell that caught this the first time.
