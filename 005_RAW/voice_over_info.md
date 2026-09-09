# Voice-over — who says how much

## Totals by character

| Character | Total | Gender | Campaigns |
|---|---:|---|---|
| **Catherine** | **12** | female | 000_Intro, 001_Long_Live_the_Queen, 002_Liberation, 003_Song_for_the_Father, 008_Armageddons_Blade |
| **Unnamed male general** | **10** | male | 004_Dungeons_and_Devils, 005_Long_Live_the_King, 007_Seeds_of_Discontent |
| **Sandro** | **10** | male | 018_Rise_of_the_Necromancer, 019_Unholy_Alliance, 020_Specter_of_Power |
| **Yog** | **8** | male | 015_Birth_of_a_Barbarian, 019_Unholy_Alliance |
| **Gem** | **7** | female | 016_New_Beginning, 019_Unholy_Alliance |
| **Crag Hack** | **5** | male | 014_Hack_and_Slash, 019_Unholy_Alliance |
| **Gelu** | **5** | male | 008_Armageddons_Blade, 019_Unholy_Alliance |
| **Mutare** | **4** | female | 009_Dragons_Blood |
| **Dracon** | **4** | male | 010_Dragon_Slayer |
| **Kilgor** | **4** | male | 011_Festival_of_Life |
| **Sir Christian** | **4** | male | 012_Foolhardy_Waywardness |
| **Forest Guard commander** | **4** | unspecified | 017_Elixir_of_Life |
| **Unnamed female retainer** | **3** | female | 006_Spoils_of_War |
| **Adrienne** | **3** | female | 013_Playing_with_Fire |
| **Xeron** | **2** | male | 008_Armageddons_Blade |
| **Dorrell** | **1** | male | 002_Liberation |
| **Winstan Langer** | **1** | male | 002_Liberation |
| **Roland** | **1** | male | 008_Armageddons_Blade |
| **TOTAL** | **88** | | |

**Gender** is determined from actual pronouns in the original
`HEROBIOS.TXT` (`005_RAW/H3bitmap.lod/HEROBIOS.json`) and in the prolog
text itself, not guessed from the name — e.g. `Gem`/`Mutare` are "she"/
"her" there, even though the names alone don't give that away.
`Forest Guard commander` is a generic title with no confirmed gender in
any source, left as `unspecified`.

## `000_Intro` (`H3INTRO.mp4`) — Catherine, confirmed (not a guess)

This is the game's own single overall opening cinematic (played once,
before any campaign is even selected) - a genuinely different thing from
each campaign's own selection-menu intro clip (`CGOOD1.mp4` etc), and
**the only "extra" line added to any character's count in this table** -
every other total above is exactly the number of real per-mission
narration files, nothing added or guessed.

Unlike every campaign-selection-menu intro (deliberately left OUT of this
table - see below), this one is backed by a real transcript
(`005_RAW/000_Intro/H3INTRO.srt`, Whisper-transcribed from the actual
`H3INTRO.mp4` audio) that settles the speaker directly: *"I think of my
beloved Rowand and my son Nikolai..."* - "Rowand" is Whisper mishearing
**Roland** (Catherine's husband, King Roland Ironfist), and "Nikolai" is
their son - a first-person self-identification, not an inference.

## Every OTHER campaign's own selection-menu intro is deliberately NOT counted

An earlier version of this table added +1 to 18 of the 20 campaigns for
their own selection-menu intro clip (`CGOOD1.mp4`, `CNEUTRAL.mp4`, etc.)
on the assumption that it shares its campaign's single dominant voice -
**this was walked back**: unlike `000_Intro` above, none of those 18 have
an actual transcript or confirmed recording backing the guess, and for
the 7 RoE campaigns specifically, `AUDIO_VIDEO_NOTES.md`'s "Full RoE
voiceover map" shows there isn't even a distinct audio *code* for a
campaign-level intro in `Heroes3.snd` at all (only per-mission letters
a/b/c/d). For the 13 AB/SoD campaigns a real corresponding file does
exist in `Heroes3.snd` (e.g. `ABVOAB1`, `H3X2HSA`) but has never been
extracted or transcribed. Every mission-line total above is the real
narration count only - no per-campaign guesswork mixed in.

## Source

`Heroes_III_Complete.md` (repo root) - matched here **by mission name**,
not by that file's own mission-number column, which turned out to be
wrong for `Armageddon's Blade` (missions 2/3 swapped relative to the
`.h3c`'s real scenario order) - verified against the actual English
prolog text of both missions before trusting the rest of the table.

## Per-campaign breakdown

| # | Campaign | Missions | Speaker(s) |
|---|---|---:|---|
| 000_Intro | *(game intro, not a campaign)* | — | Catherine (confirmed by transcript) |
| 001_Long_Live_the_Queen | Long Live the Queen | 3 | Catherine |
| 002_Liberation | Liberation | 4 | Catherine (missions 2/3: Dorrell / Winstan Langer) |
| 003_Song_for_the_Father | Song for the Father | 3 | Catherine |
| 004_Dungeons_and_Devils | Dungeons and Devils | 3 | Unnamed male general |
| 005_Long_Live_the_King | Long Live the King | 4 | Unnamed male general (Sandro is a central character but never the narrator) |
| 006_Spoils_of_War | Spoils of War | 3 | Unnamed female retainer |
| 007_Seeds_of_Discontent | Seeds of Discontent | 3 | Unnamed male general |
| 008_Armageddons_Blade | Armageddon's Blade | 8 | Catherine → Xeron → Gelu → Xeron → Roland → Gelu → Catherine → Catherine |
| 009_Dragons_Blood | Dragon's Blood | 4 | Mutare |
| 010_Dragon_Slayer | Dragon Slayer | 4 | Dracon |
| 011_Festival_of_Life | Festival of Life | 4 | Kilgor |
| 012_Foolhardy_Waywardness | Foolhardy Waywardness | 4 | Sir Christian |
| 013_Playing_with_Fire | Playing with Fire | 3 | Adrienne |
| 014_Hack_and_Slash | Hack and Slash | 4 | Crag Hack (mission 1 has no video, audio only) |
| 015_Birth_of_a_Barbarian | Birth of a Barbarian | 5 | Yog |
| 016_New_Beginning | New Beginning | 4 | Gem |
| 017_Elixir_of_Life | Elixir of Life | 4 | Forest Guard commander (Gelu is the hero but never narrates himself) |
| 018_Rise_of_the_Necromancer | Rise of the Necromancer | 4 | Sandro |
| 019_Unholy_Alliance | Unholy Alliance | 12 | rotates: Yog → Crag Hack → Gelu → Gem → Yog → Gelu → Sandro → Sandro → Gelu → Yog → Gem → Gem |
| 020_Specter_of_Power | Specter of Power | 4 | Sandro |
