# Campaign video & voiceover — findings and WAV map

**Why this file exists:** so the real English narration clips can be found
fast later (e.g. to send to a translator/voice actor for UA dubbing),
without re-doing the investigation below.

## TL;DR — where the real narration audio actually lives

For the **7 original RoE campaigns**, the per-mission narration is in
**`Heroes3.snd`**, under short, non-obvious 2-4 character codes (`G1A`,
`E2AE`, `N1C_D`, ...) — **not** in the per-mission video files. Extract with:

```
mmarch extract "F:/Games/HoMM 3 Complete/Data/Heroes3.snd" <out_dir> G1A G1B G1C
```

This gives real `.wav` files (mmarch auto-converts `h3snd` → `wav`) — these
are exactly the clips a translator would need to reference for dubbing
timing, and the text they read aloud is `CAMPDIAG.TXT`'s entry for the
matching key (e.g. `G1A` narrates the same line as `CAMPDIAG.json`'s
`"Good1a"` entry, see `005_RAW/H3bitmap.lod/CAMPDIAG.json`).

## Investigation trail (so nobody re-derives this)

Three different places in the game files could plausibly hold this audio.
Only one actually does:

1. **`VIDEO.VID`'s `.BIK` files** (e.g. `GOOD1A.BIK`) — checked via
   `ffprobe`: **no audio stream at all.** Silent video only.
2. **`VIDEO.VID`'s `.SMK` files** (same name, `.SMK` extension — the older
   Smacker codec, stored alongside the `.BIK` re-encode of the same clip) —
   *do* have an audio stream (`smackaudio`, u8, stereo, 22050 Hz), but it
   **decodes to pure noise**. Verified two independent ways:
   - `ffmpeg -i GOOD1A.SMK -vn out.wav` then a spectrogram
     (`ffmpeg -i out.wav -lavfi showspectrumpic=... pic.png`) — flat
     broadband noise, no speech formants.
   - A from-scratch Python port of the Smacker DPCM audio algorithm
     (`smk_audio_decoder.py` in this folder, ported line-by-line from
     `libsmacker`, https://github.com/JonnyH/libsmacker, C, permissive
     license) — **agrees byte-for-byte** with ffmpeg's output (same length,
     same noise). Two independent implementations of the documented
     algorithm agreeing rules out "ffmpeg decoder bug" — the audio track
     genuinely is junk/unused data in these specific files, not a decode
     failure. Don't waste time trying to "fix" SMK audio decoding for this
     use case again; `smk_audio_decoder.py` is kept only in case some other
     game's SMK file needs a real (non-ffmpeg) decode later.
3. **`Heroes3.snd`, short codes** — the real one. Found by listing the
   archive and sorting by size (`mmarch list ... | sort -k2 -nr` after
   reformatting) — real narration clips are hundreds of KB, an order of
   magnitude bigger than the combat/UI sound effects that dominate the
   file, which makes them easy to spot once you stop guessing at
   descriptive names (searching for "good"/"vo"/"queen"/etc. finds
   nothing - the codes are terse and campaign-specific, not descriptive).
   Confirmed with a spectrogram: clear voiced-speech harmonic bands, pauses
   between phrases, ~11-41 second durations matching a full paragraph read
   aloud (vs. the SMK/BIK clips' 4-13 second silent loops).

## Full RoE voiceover map

All codes below confirmed present in `Heroes3.snd` (sizes are the packed
ADPCM size in bytes, not duration - `ffprobe` the extracted `.wav` for
exact seconds). CAMPDIAG key = the entry in
`005_RAW/H3bitmap.lod/CAMPDIAG.json` with the matching narration text.

| Campaign (005_RAW folder) | Mission | CAMPDIAG key | Video file | Voice code | Size (bytes) |
|---|---|---|---|---|---|
| 001_Long_Live_the_Queen | a/b/c | Good1a/b/c | GOOD1A/B/C.BIK | **G1A / G1B / G1C** | 254440 / 455400 / 277416 |
| 002_Liberation | a/b/c/d | Good2a/b/c/d | GOOD2A/B/C/D.BIK | **G2A / G2B / G2C / G2D** | 236112 / 508832 / 333092 / 473572 |
| 003_Song_for_the_Father | a/b/c | Good3a/b/c | GOOD3A/B/C.BIK | **G3A / G3B / G3C** | 482628 / 263688 / 494608 |
| 004_Dungeons_and_Devils | a/b/c | Evil1a/b/c | EVIL1A/B/C.BIK | **E1A / E1B / E1C** | 277608 / 373624 / 176400 |
| 005_Long_Live_the_King | a/b/c/d | Evil2a/b/c/d | EVIL2A/B/C/D.BIK (+AP1/AP2) | **E2A / E2AE / E2B / E2C / E2D** | 677912 / 292296 / 153280 / 257588 / 334640 |
| 006_Spoils_of_War | a/b/c | Neutral1a/b/c | NEUTRALA/B/C.BIK | **N1A / N1B / N1C_D** | 423036 / 525124 / 518472 |
| 007_Seeds_of_Discontent | a/b/c | Secret1a/b/c | SECRETA/B/C.BIK | **S1A / S1B / S1C** | 389392 / 366732 / 381552 |

Notes on the odd ones out: `E2AE` and `N1C_D` don't map 1:1 to a single
mission letter - only Good1's set (`G1A/B/C`) has been spectrogram-verified
as real speech; the rest are inferred from the same size/naming pattern and
should be spot-checked the same way before relying on them for anything
translator-facing.

## AB-era campaigns (different convention, already known-good)

The 6 Armageddon's Blade campaigns (`ab`, `blood`, `slayer`, `festival`,
`fool`, `fire`) use **one** narration clip per whole campaign (not per
mission), named `ABVO<code><n>` in `Heroes3.snd` — e.g. `ABVOAB1`..`ABVOAB9`
for the `ab` (Armageddon's Blade) campaign. These were already known from
earlier extraction work, not part of this investigation. The 7 SoD hero
campaigns (`crag`/`yog`/`gem`/`gelu`/`sandro`/`final`/`secret`) likewise use
a single video per campaign (`hack.bik`, `Birth.bik`, etc., in `VIDEO.VID`)
- whether *those* have real embedded audio or need the same Heroes3.snd
  treatment has not been checked yet.

## Encoding NEW video back into the game (working pipeline, one open risk)

The engine only plays video through the bundled `BINKW32.DLL` /
`SMACKW32.DLL` (proprietary RAD Game Tools runtimes) - a plain `.mp4` will
never work as a drop-in replacement, no matter the resolution. `ffmpeg` can
*decode* Bink/Smacker but has **no encoder** for either format - encoding a
new cutscene needs RAD's own tool.

### Two different RAD Video Tools builds - only one of them works here

- **Old build (2001, `binkconv.exe`, version 1.1.0.0)** - mirrored on
  archive.org / factionfiles.com
  (<https://www.factionfiles.com/ff.php?action=file&id=5465>, see
  [[homm3-rad-video-tools]]). **Crashes with `STATUS_ACCESS_VIOLATION`
  (fault in `radutil.dll`) on every single conversion attempt on Windows
  11** - tried plain mpeg4 AVI input, uncompressed rawvideo AVI input,
  `__COMPAT_LAYER=WINXPSP3`, the GUI Properties > Compatibility tab set to
  "Windows XP (Service Pack 2)" + "Run as administrator". Nothing helped.
  **Do not spend more time on this build - it does not run on modern
  Windows.**
- **Current build (downloaded fresh from RAD's own site, dated 14.06.2026)**
  - direct official link: `https://www.radgametools.com/down/Bink/RADTools.7z`
    (7z, password `RAD`). This does **not** need a license and is **not**
    player-only - it's a full working encoder (contradicts what was
    assumed earlier in this file). Extract with 7-Zip, run the resulting
    `radtools.exe /S /D=<install_dir>` for a silent install. Installed at
    `C:\Users\UserM\AppData\Local\RADVideoNew\` on this machine. This build
    does **not** crash.

### The `radvideo64.exe` command-line trap

`radvideo64.exe` is a multi-tool dispatched by a subcommand. Two
similarly-named subcommands exist and **only one of them encodes**:

- `radvideo64.exe BinkConv <in> <out> [/switches]` - this is a **decoder**
  (Bink/Smacker/etc -> avi/images/wav). Pointing it at a `.bik` output
  fails instantly with a GUI dialog: *"Unsupported output file type or
  color depth."* - no console output at all, so this looks exactly like a
  silent hang unless you inspect the window (confirmed via `EnumWindows`/
  `EnumChildWindows` from PowerShell - there's no hidden crash, just a
  dialog box).
- `radvideo64.exe Bink <input> <out.bik> [/switches]` - **this is the real
  encoder.** Works instantly, no crash, real playable `.bik` output.
  Useful switches: `/(W` scale to width, `/)H` scale to height, `/F#.#`
  force output frame rate, `/O` auto-overwrite. Full switch list is baked
  into the exe as plain strings (dump with a regex over the binary,
  searching for `"Video switches:"` - no `/?` console output either, it's
  a GUI dialog).
- The GUI window this opens does **not** close itself when done - it sits
  forever saying `"Bink Video Compressor - Done!"`. Any automation must
  poll for the output file to appear/stop growing and then kill the
  process; it will never exit on its own even after finishing
  successfully.

### Confirmed working end-to-end (inject-and-verify, not yet in-game-verified)

```
ffmpeg (optional pre-process) -> radvideo64.exe Bink -> mmarch add
```

`mmarch add "VIDEO.VID" NewClip.bik` (where `NewClip.bik` is renamed to
match the existing entry, e.g. `GOOD1A.BIK`) **replaces the existing
same-named entry in place** - confirmed by re-extracting after `add` and
byte-comparing against the source file (identical). No delete-then-add
dance needed.

Wrapper script: `002_TOOLS/scripts/008_mp4_to_bik_inject.py` (mp4/avi -> bik ->
injected into a **scratch copy** of the archive, never touches the live
game install directly - see its docstring for full detail and gotchas
above).

### Open risk - Bink bitstream revision mismatch (NOT YET CONFIRMED either way)

The new encoder writes the newest Bink 1 revision, tagged **`BIKi`** in the
file's first 4 bytes. The original game files are tagged **`BIKb`** - a
much older revision matching the ~2001 `binkw32.dll` HoMM3 ships with.
There is **no encoder switch to force an older output revision** (checked
- only `BIKf/g/h/i` are ever produced, `BIKb` isn't reachable from this
build). Bink decoders are not guaranteed backward-compatible with
bitstream revisions newer than they were built for.

**This has not been tested in the actual running game yet** - only
verified programmatically: encode → inject into a scratch `VIDEO.VID` copy
→ extract back out → byte-identical. Whether HoMM3's own decoder can
actually *play* a `BIKi` frame is unknown until someone launches the game
with the modified archive swapped in.

A ready-to-try test file exists at (gitignored, NOT in the repo - it's a
630MB full copy of the real archive with just `GOOD1A.BIK` replaced by the
exact same campaign-intro content, re-encoded through the new pipeline, so
any playback difference is purely the codec revision, not new content):
`C:\Users\UserM\AppData\Local\Temp\claude\c--Users-UserM-Documents-GitHub-homm3-ua\2dfbc7e2-cf8d-4533-acdf-023a54706d97\scratchpad\TEST_VIDEO_INJECT\VIDEO.VID`
(this is a session-temp path and may not survive - regenerate with
`008_mp4_to_bik_inject.py` if it's gone).

**To test:** back up the real `Data\VIDEO.VID`, copy the test file over it,
launch the game, start "Long Live the Queen" (first Good campaign) and
check whether the mission A intro cinematic plays correctly.

**If it fails to play / looks broken:** that's almost certainly the
`BIKb`→`BIKi` revision jump. The fix would be dropping a newer
`binkw32.dll` redistributable next to the game's exe (RAD's terms allow
freely redistributing the *decoder* DLL bundled with a compiled game,
unlike the encoder) - but no standalone download for just that DLL was
found on radgametools.com; it would have to come from the licensed SDK or
be sourced from another game/mod (e.g. HD mod, which solved this exact
problem) that already ships a compatible newer decoder.

## SMK encoding - the format that actually plays (major update)

**Critical discovery: for the original 7 RoE campaigns, the game reads the
`.SMK` file for the picture, not the `.BIK`.** Both exist side by side in
`VIDEO.VID` for every mission clip (e.g. `GOOD1A.SMK` + `GOOD1A.BIK`), but
replacing only the `.BIK` and leaving `.SMK` untouched shows the ORIGINAL
video in-game - the engine never even looks at the new `.BIK`. Replacing
only `.SMK` (leaving `.BIK` alone) does change what plays. This directly
contradicts the "just encode a new .bik" assumption the whole pipeline
above was built on - `.bik` replacement is only useful for content the
engine actually reads as Bink (untested here - may differ for AB/SoD
campaigns' single-clip-per-campaign videos).

### The real working pipeline, step by step

1. `ffmpeg` - render the source video to a still-image sequence (PNG), at
   the TARGET resolution/fps, no subtitles baked in via the `subtitles`
   filter directly (see the palette section below for why manual
   quantization is required instead).
2. Extract the ORIGINAL target archive entry's embedded palette:
   `ffmpeg -i original.SMK -vframes 1 -pix_fmt pal8 palette_ref.png`, then
   read it with PIL (`Image.open(...).getpalette()`).
3. **Quantize every frame to that exact palette with dithering** using
   PIL: `frame.convert("RGB").quantize(palette=pal_template,
   dither=Image.FLOYDSTEINBERG)`, save as 8-bit `.bmp`. This step is not
   optional - see "the truecolor bug" below.
4. Build a `.lst` file (plain text, one absolute Windows path per line,
   `.lst` extension required) listing the quantized BMP frames in order.
5. Encode: `radvideo64.exe Smack <frames.lst> <out.smk> /F<fps> /Z1` (Z1 =
   copy the existing palette from the input - now valid since step 3 gave
   every frame a real embedded palette to copy). GUI window never closes
   itself when done - poll for the output file to stop growing, don't wait
   for process exit (see `008_mp4_to_bik_inject.py` pattern, though that script
   is Bink-specific - no SMK equivalent script exists yet, this was all
   done by hand this session).
6. `mmarch add ARCHIVE.SMK` (or whichever archive) to inject, same as Bink.
7. **Audio is separate, not embedded** - see the voiceover section: for
   RoE campaigns, replace the matching `Heroes3.snd` short-code entry
   instead (e.g. `G1A` for Good1a) with a WAV **trimmed to the exact same
   duration as the new video** (IMA ADPCM, 22050 Hz, mono, matching the
   original's format) - a duration mismatch here was an actual bug caught
   late in this session (accidentally used the full 3-mission-concatenated
   audio for a single-mission video slot; fixed by trimming to the source
   mission's own duration before re-injecting).

### The truecolor-to-palette bug (don't waste time retrying encoder switches)

Encoding directly from a truecolor source (mp4/AVI, no pre-quantization)
via any combination of `/Z0` (truecolor), `/Z1` (default - "copy existing
palette", meaningless when there IS no existing palette), `/Z2` (new
best-case palette), `/Z2 /T1` (new palette + forced halftone/dither), or
`/&origfile` (explicit external palette source) - **all five produce
visually identical, severely corrupted/speckled output**, confirmed via
both the game (through DDrawCompat) and RAD's own current `SmackPlay`
preview tool, ruling out a game-side or DDrawCompat-side rendering bug.
This is a genuine bug in this encoder build's internal truecolor→palette
pipeline, not a switch you can fix your way out of. The ONLY thing that
produced a clean, correct result was quantizing frames ourselves in
Python/PIL to a fixed palette **before** handing them to the encoder (step
3 above) - i.e. never let this tool's Smack encoder see truecolor input.

### The old game DLL can't play new-format SMK at all - needs a decoder swap

HoMM3 Complete's own `Data/../SMACKW32.DLL` (game root, not `Data/`) is
version **3.2h**. Any SMK encoded by the current (2026.06) or even the
2021-08-26 RAD Video Tools build comes out as format tag **`SMK4`** (the
original game files are **`SMK2`` - see hex dump: original starts
`53 4D 4B 32` = "SMK2", new encodes start `53 4D 4B 34` = "SMK4"). The
stock 3.2h DLL cannot play an `SMK4` file **at all** - not corrupted, not
crashing, just silently skips it (confirmed: black screen, "game skipped
the intro" with zero errors, matching the earlier `BIKb`-vs-`BIKi`
Bink-revision problem in spirit).

**Fix: replace `SMACKW32.DLL` in the game's root folder** (back up the
original first!) **with a newer decoder DLL from another legitimately-owned
game that happens to ship one.** Found on this machine:
`D:\Games\StarCraft_OLD\Smackw32.dll`, version **4.1a** - newer than
HoMM3's 3.2h and old enough to still be a plain Win32 DLL with the same
exported function signatures (Smacker's API has been stable for decades).
Dropping this in **immediately fixed playback** - both the original videos
and new SMK4-encoded ones play correctly afterward. No official standalone
redistributable-only download exists for this DLL (checked - RAD's
installers don't ship it separately, only inside full player/tool exes
that statically link it) - sourcing it from another already-owned classic
RAD-Tools-using game is the practical path. `SMACKW32_BACKUP_ORIGINAL.DLL`
sits next to it in the game folder as the restore point.

### Resolution/frame-rate ceiling - real, but not a format limit

Tested extensively this session, results:

| Resolution | FPS | Frames | Result |
|---|---|---|---|
| 800x600 | 10 | 229-888 | **Works reliably**, multiple times |
| 800x600 | 20 | 459 | Encoder hangs (CPU flatlines, 0 progress for minutes) |
| 800x600 | 25 | 572 | Hangs on the 2026.06 build; on the 2021-08-26 build instead crashes right at 99% (both builds tested, both unreliable above 10fps) |
| 800x600 | 30, 60 | 688, 1375 | Hangs |
| 1024x768 | 15 | 344 | Hangs |
| 1280x720 | 15 | 344 | **Encodes fine**, but the GAME won't load/play it (crashes or black-screens depending on which DLL swap is in place) |
| 1280x720 | 30, 60 | 687, 1375 | Encoder hangs |

The Smacker file format itself has no resolution ceiling (header stores
Width/Height as 32-bit dwords - "Smacker" MultimediaWiki page confirms,
no documented practical max either). This is **not a documented limit** -
it's either (a) an undocumented bug/instability in this specific RAD Video
Tools GUI encoder under load (both the 2026.06 and 2021-08-26 builds show
different failure modes - hang vs. crash-near-completion - suggesting a
long-standing fragile code path, not a recent regression), or (b) for the
1280x720-plays-but-game-won't-load-it case specifically, a hardcoded
buffer size assumption inside `Heroes3.exe`'s own video playback code
(pre-allocated for at most ~800x600, guessed, not confirmed) that's
separate from the encoder or the DLL. **Practical conclusion: stick to
800x600 @ 10fps** (also happens to be the original game's exact native
rate for these clips) - it's the only combination that has never failed
across many repeated attempts. Higher settings are a real rabbit hole with
no confirmed fix, not worth revisiting without a specific new idea.

Direct **Bink** encoding (`radvideo64.exe Bink <mp4> <out.bik>`, no image
sequence, no manual quantization needed) was rock solid throughout this
whole investigation at every resolution/fps tried - the instability is
specific to the Smack-encoder-via-BMP-sequence path.

### UPDATE: found a far more reliable encoder build - and a confirmed hard engine ceiling

After the above was written, tried a THIRD RAD Video Tools build: version
**1.994i** (RAD's own internal versioning - files dated 2014, mirrored at
<https://www.videohelp.com/software/Rad-Video-Tools/old-versions>, plain
`.exe` NSIS installer, no 7z/password needed, `/S /D=<dir>` silent
install, installed at `C:\Program Files (x86)\RADVideo1994\` this
session). **This build's `smack.exe` never hung or crashed once**, across
every setting that reliably broke both the 2026.06 and 2021-08-26 builds:
800x600 @ 25/60fps (1375 frames), 1024x768 @ 60fps, 1280x720 @ 60fps - all
encoded cleanly in well under a minute each, with visually correct output
(confirmed via SmackPlay, no corruption). Still outputs `SMK4` (the
SMK2→SMK4 transition happened back in Smacker version 4.0a, December
1999, per `smkhist.htm` - "New Smacker 4.0 compression, double the
quality" - so any RAD build from the 2000s onward will produce SMK4
regardless; getting SMK2 output would need an actual pre-1999 Smacker
compressor, which was NOT found - videohelp.com's "old versions" archive
only goes back to this 2014-dated 1.994i package. Not worth pursuing
further; SMK4 already plays fine once the DLL is swapped, see below).

**Recommendation: use `C:\Program Files (x86)\RADVideo1994\smack.exe`
for all future Smack/SMK encoding, not `radvideo64.exe Smack`** from
either newer build. Command line differs slightly - this is the
standalone pre-unification tool, so no `Smack` subcommand prefix:
`smack.exe <frames.lst> <out.smk> /F<fps>` (no `/Z1` needed either -
tested without it and palette copying still worked correctly with
pre-quantized input). `009_mp4_to_smk_inject.py`'s `find_rad_exe`/`encode_smk`
should be updated to prefer this exe if present - **not yet done this
session**, the script still points at `radvideo64.exe Smack` from the
2026.06 install path.

**With this reliable encoder, the earlier "800x600 is the ceiling"
conclusion needed to be re-tested and now has a definitive, different
explanation.** Re-ran 1280x720@60fps and 1024x768@60fps through this
stable encoder (both produced perfectly valid, uncorrupted `.smk` files -
confirmed via ffprobe) and injected them in place of `GOOD1A.SMK` exactly
as before. **The game still crashes trying to load either one**, even
though the files themselves are now known-good (not encoder artifacts).
This proves the ceiling is real and is **not an encoding-quality problem
at all** - it's a hard limit somewhere in `Heroes3.exe`'s own video
playback code (most likely a fixed-size buffer allocated on the
assumption that no video will ever exceed the original ~800x600 assets),
present even in the "Complete" edition (RoE+AB+SoD bundled, the most
feature-complete official GOG release). **800x600 @ up to 60fps is now
confirmed as the practical ceiling for this specific game+DLL
combination** - frame rate is no longer a concern with the 1.994i
encoder, only resolution is a wall, and that wall is in the game exe
itself, not fixable by any encoder or DLL swap.

**BLOCKER for actually shipping this to other users (not solved, paused
here deliberately - revisit later):** the whole SMK approach depends on
replacing `SMACKW32.DLL` with a copy sourced from a different,
copyrighted commercial game (StarCraft's v4.1a, in this session's case).
That's fine for one person's own local install (you own both games), but
it means **this DLL cannot legally be bundled into a distributable
Ukrainian-translation mod/installer for other people** - redistributing
someone else's game binary isn't ours to give away. Before scaling the
video work to the full game and packaging it for others, this needs an
actual resolution - options to weigh later: (a) instruct end users to
source their own compatible DLL from a game they own, (b) find a legally
redistributable decoder DLL (none found so far - RAD doesn't offer one
standalone), (c) check whether HD mod sidesteps this entirely (see the
next paragraph - also unresolved), or (d) some other fix not yet
considered. Don't build a distributable video package until this is
actually settled.

**Next idea, not attempted this session:** the community-made **HD mod**
(aka HiRez mod / Multi-Resolution patch, see heroes3wog.net) patches
`Heroes3.exe` to support resolutions up to 4000x4000 for general
gameplay/UI rendering. Whether it also patches (or removes) the video
playback buffer limit specifically is unconfirmed - search results only
describe its gameplay-resolution features, nothing about cutscene/video
internals specifically. Worth testing directly in a future session: install
HD mod over this GOG Complete install, try injecting a 1024x768 or
1280x720 `GOOD1A.SMK` again (same file already sitting in this session's
scratchpad, or regenerate via `009_mp4_to_smk_inject.py` pointed at the
1994-build `smack.exe`), see if it now plays. If HD mod doesn't fix it
either, the Grayface binary-patching approach mentioned in the "external
validation" section below becomes the only remaining lead.

### Note: the "Ukrainian voiceover" produced this session is not a real dub

The audio injected into `Heroes3.snd`'s `G1A` slot is the **original
English narration**, re-extracted/re-encoded from the existing pipeline -
not synthesized or voice-acted Ukrainian speech. `011_burn_campaign_subtitles.py`
was always designed this way (real English audio + burned subtitle text in
whichever language) - nothing in this project has ever produced actual
Ukrainian dubbing audio. If real UA dubbing happens later (translator/voice
actor), that's a new recording to inject in `G1A`'s place, using this same
injection mechanism.

### External validation (community, not verified further)

A message shared by the user from someone in the HoMM3 modding community
independently corroborates the direction found here: no Bink1 encoder
exists anymore ("we don't have any tool to bik1"), Bink2 only works in
engines built for it (cites Heroes Chronicles), and the "final solution"
on the ERA2 modding platform is exactly a BIK→SMK conversion workflow
("SMK is easy to edit") - matching what this session independently found
and got working. Also mentioned: Grayface (MM6/MM7 modder) patched
`binkw32.dll` handling into that engine's exe directly -
<https://grayface.github.io/mm/> - potentially relevant reference if a
future session wants to attempt a similar binary patch of `Heroes3.exe`/
`BINKW32.DLL` instead of the DLL-swap workaround used here. Not explored
further this session since the DLL-swap + SMK-not-BIK approach already
works for the 800x600 case.

## Tools that use this

- `002_TOOLS/scripts/008_mp4_to_bik_inject.py` — the mp4→bik→inject pipeline
  described above. Encodes via the new `radvideo64.exe Bink` command and
  injects into a scratch copy of an archive via `mmarch add`. Read its
  docstring before touching this area again - it has the full trap list
  (crashing old build, BinkConv-vs-Bink subcommand trap, GUI-never-closes
  quirk, revision mismatch risk).
- `002_TOOLS/scripts/011_burn_campaign_subtitles.py` — builds a narrated,
  subtitled mp4 per campaign from this exact pipeline (BIK video looped to
  the real Heroes3.snd clip's duration + burned SRT timed proportionally
  to sentence length within that duration). Currently only `GOOD1` is
  wired up in its `CAMPAIGNS` dict; extend it with the rows from the table
  above to cover the other 6 RoE campaigns.
- `002_TOOLS/scripts/004_extract_campaign_videos.py` — the earlier, simpler
  tool that just converts every campaign's video(s) to silent mp4 (no
  audio, no subtitles). Still useful for a quick visual reference.
- `002_TOOLS/scripts/smk_audio_decoder.py` — standalone Smacker audio
  decoder (see investigation trail above). Not currently used by anything
  since it turned out unnecessary here, kept for future need.
