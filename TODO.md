# TODO — what's left to do

## 0. [FIXED] Right-click on creatures showed random garbage — root cause found

**Summary**: not an engine bug, not quotes, not special characters — it
was line endings. Full investigation and the fix code live in
`H3_TXT_FORMAT_NOTES.md`, section "THE REAL ROOT CAUSE".

1. Inside quoted multi-line records, the line break must be a bare `\n`
   with no `\r`; `\r\n` is the separator BETWEEN records. The game splits
   records on literal `\r\n`. Python's text-mode file writing on Windows
   silently turns every `\n` into `\r\n` on write — this is exactly what
   broke `ArrayTxt.txt`/`ADVEVENT.txt`/`CMPEDITR.TXT` (the only 3 files a
   Python script had rewritten during an earlier "broken quote" fix).
   Plus `git config core.autocrlf=true` + `.gitattributes` threatened to
   redo the same damage on every future checkout — fixed
   (`.gitattributes` now marks the whole `001_ORIGINAL_HOMM3_FILES_HURTOM/`
   folder as binary for Git).
2. Separately in `ADVEVENT.TXT`: after fixing the line endings, an object
   title shift surfaced (203 records instead of the true 191) — rebuilt
   from scratch, 191 records, 0 shape mismatches against English.

Deployed and verified byte-for-byte from the live game. `ArrayTxt.txt`
and `ADVEVENT.txt` in `H3bitmap.lod` now carry the real Ukrainian
translation (the temporary Russian stopgap has been removed).

Diagnostic files (safe to delete if no longer needed for reference):
`002_TOOLS/scripts/_lang_diag/*`, the `ArrayTxt_ADVEVENT_compare` folder
on the desktop (EN/RU/FR/UA copies for manual comparison).


## 1. [13/16 DONE] 3 flat-text files still need fixing

`ADVEVENT.TXT` and `ARRAYTXT.TXT` are **fixed** (method found: compare
records by a language-independent "signature" — `%s`/`%d` placeholders +
signed numbers like +3/-1 — via `difflib.SequenceMatcher`). ADVEVENT also
turned out to have a second broken quote (`."""` instead of `."`) that
glued half the file into one blob.

Remaining: `CMPEDITR.TXT` (the standalone Campaign Editor's
(`h3ccmped.exe`) own UI text — NOT used during actual play, low priority,
but whole menu sections are genuinely reshuffled there, and the
signature-based method nearly deleted the needed translation
"Відміна"/"Довідка" — see the warning in the notes), `GENRLTXT.TXT` and
`HELP.TXT` (large, 700-900+ records, haven't tried the new method on them
yet).

**How to approach it:** see `002_TOOLS/scripts/H3_TXT_FORMAT_NOTES.md` —
the whole method is written up there in detail, including how to tell a
genuine "extra" record from a diff false positive (if the proposed
deletion leaves an English record with no Ukrainian counterpart at all —
the diff misaligned, not the translator).

**Important:** only edit these files via PowerShell +
`[System.Text.Encoding]::GetEncoding(1251)` — the `Edit` tool corrupts
cp1251 encoding (see the same file, section on the data-corruption
incident). After every edit, check for `\xef\xbf\xbd` (corruption marker)
and `git diff --stat` (an unexpectedly large diff for a small edit is a
bad sign).

## 2. [FIXED, but needed real action] `H3bitmap.lod` vs `H3ab_bmp.lod` —
the priority assumption was WRONG

Originally assumed that with AB active, the engine always reads
`H3ab_bmp.lod` and `H3bitmap.lod`'s copies of same-named files go unused.
**This turned out to be wrong for campaigns** — 7 SoD-era campaigns
(Crag/Yog/Gem/Gelu/Sandro/Final/Secret) physically have their originals
in `H3bitmap.lod`, and the engine read them from exactly there, entirely
ignoring what had been injected into `H3ab_bmp.lod`. This meant the whole
SoD chapter showed no translation at all in-game — found and fixed (see
memory `homm3-campaign-deploy-replace-not-add`).

**[Also FIXED] Confirmed in practice:** the same trap existed for flat
files too. Screenshots showed Keymaster's Tent/Followers/Stables still in
English even though `H3ab_bmp.lod` had been patched and verified
byte-identical. Turned out the game actually reads `H3bitmap.lod`, and
for 7 of the 8 re-checked files (ARTSLOTS, CMPEDCMD, HEROBIOS, OBJNAMES,
SEERHUT, CAMPTEXT, ARRAYTXT), Hurtom's **original, untouched** translation
already matched `H3bitmap.lod`'s structure exactly — every one of my
earlier "fixes" was unnecessary and got reverted. ADVEVENT/ARTEVENT kept
the real broken-quote fix (relevant to both archives), but the
`H3ab_bmp.lod`-specific tail trim was reverted too. All 10 files are now
deployed to `H3bitmap.lod` and verified directly from the live game.
Details and warnings — `H3_TXT_FORMAT_NOTES.md`, section "CRITICAL
CORRECTION".

**[FIXED, same trap a third time] Campaigns were affected too — partially.**
User noticed: on the campaign selection screen, "Long Live the Queen"
(Good1)'s title and description were in English ("Long Live the Queen",
"Our landing has confirmed..."), even though the actual mission play was
in Ukrainian. Cause: all 13 RoE/AB-era campaigns (Good1-3, Evil1-2,
Neutral1, Secret1 + everything supposedly "only in `H3ab_bmp.lod`") ALSO
have an independent copy in `H3bitmap.lod` — the campaign preview screen
reads that one, while actual gameplay reads the copy in `H3ab_bmp.lod`.
We had only ever been patching `H3ab_bmp.lod`. `H3bitmap.lod` holds
copies of ALL 20 campaigns except the 6 pure-AB ones
(ab/blood/slayer/festival/fool/fire) — 14 entries in total.

Fixed properly: `013_deploy_full.py` no longer hardcodes "campaign →
single archive" — on every run it queries `mmarch list` on both archives,
finds EVERY place a `.h3c` with that name actually lives, and injects
into all of them. Deployed and verified — `Good1.h3c` in `H3bitmap.lod`
is now Ukrainian too.

**[FIXED, same trap a fourth time] And splash-screen images too.**
`gamselbk.pcx`/`mainmenu.pcx` also exist in both `H3ab_bmp.lod` and
`H3bitmap.lod`. Injecting a new `gamselbk` image into only `H3ab_bmp.lod`
produced no visible change in-game — the title screen reads
`H3bitmap.lod`'s copy. Injected into both, verified pixel-identical (the
raw-byte check in `012_safe_deploy.py` gives a false FAIL here because
`mmarch` re-encodes BMP↔PCX and normalizes the BMP header dialect on the
way back out — compare decoded pixels with PIL instead of raw bytes for
this file type).

## 3. Intro video: subtitles unresolved

`BIKi` (what every available encoder writes) vs `BIKb` (what the game
reads) — still haven't found a `binkw32.dll` from the same SDK
generation. A Whisper transcript and a draft Ukrainian translation of the
video's narration are already done (see `005_RAW/000_Intro/H3INTRO.srt`),
but there's currently no way to burn them into the video. Agreed: leave
the video untouched for now, wait for a separate solution or a ready
re-dubbed audio track.

## 4. Nexus Mods release

Decided: ship pre-built, ready-to-use archives, not the toolkit (see
memory `homm3-ua-mod-distribution`). The release package is now built
with one command:
`python 002_TOOLS/scripts/013_deploy_full.py --game "..." --package`
— deploys everything to the live game AND simultaneously packages exactly
what was verified into `006_EASY_INSTALL/gog_complete/` (4 archives + 151
translated single-player maps + Tutorial.tut, ~226MB). Ready to zip and
upload.

**Decided**: the `.bat` installer was removed from the package (the user
chose not to risk it — Nexus has blocked scripts before). Replaced with
`ІНСТРУКЦІЯ.txt` — manual steps ("copy Data+Maps over your own, confirm
overwrite"). `006_EASY_INSTALL/gog_complete/` is now pure data (archives +
maps) + a text instruction file, no executable at all — ready to upload
to Nexus as-is.

## 5. Guillemets («») instead of `""`

Piloted (mission 001 GOOD1) — found an approach (only change the inner
quotes of direct speech, not the outer wrapper around the whole message)
and, along the way, a live bug (`GOOD1_M1_mapevent5_mesg`: an opening
guillemet paired with a regular closing quote). Waiting on the user to
confirm the rule before scaling it up across the whole corpus — separately
worth noting that in flat `.TXT` files (`GENRLTXT.TXT` etc.), `"` is a
structural record delimiter (see `H3_TXT_FORMAT_NOTES.md`) — only the
inner doubled `""` may be touched there, never a lone outer one.

## 6. Systematic check: "same English phrase → different translations in
different places"

Mentioned once as a desired future check (in the spirit of the pass
already done for Russianisms), not started yet.
