# Voice-over — who says how much

## Totals by character

| Character | Gender | Mission lines (files) | +Intro | **Total** | Campaigns |
|---|---|---:|---:|---:|---|
| **Catherine** | female | 11 | 3 | **14** | 001_Long_Live_the_Queen, 002_Liberation, 003_Song_for_the_Father, 008_Armageddons_Blade |
| **Unnamed male general** | male | 10 | 3 | **13** | 004_Dungeons_and_Devils, 005_Long_Live_the_King, 007_Seeds_of_Discontent |
| **Sandro** | male | 10 | 2 | **12** | 018_Rise_of_the_Necromancer, 019_Unholy_Alliance, 020_Specter_of_Power |
| **Yog** | male | 8 | 1 | **9** | 015_Birth_of_a_Barbarian, 019_Unholy_Alliance |
| **Gem** | female | 7 | 1 | **8** | 016_New_Beginning, 019_Unholy_Alliance |
| **Crag Hack** | male | 5 | 1 | **6** | 014_Hack_and_Slash, 019_Unholy_Alliance |
| **Gelu** | male | 5 | 0 | **5** | 008_Armageddons_Blade, 019_Unholy_Alliance |
| **Mutare** | female | 4 | 1 | **5** | 009_Dragons_Blood |
| **Dracon** | male | 4 | 1 | **5** | 010_Dragon_Slayer |
| **Kilgor** | male | 4 | 1 | **5** | 011_Festival_of_Life |
| **Sir Christian** | male | 4 | 1 | **5** | 012_Foolhardy_Waywardness |
| **Forest Guard commander** | unspecified | 4 | 1 | **5** | 017_Elixir_of_Life |
| **Unnamed female retainer** | female | 3 | 1 | **4** | 006_Spoils_of_War |
| **Adrienne** | female | 3 | 1 | **4** | 013_Playing_with_Fire |
| **Xeron** | male | 2 | 0 | **2** | 008_Armageddons_Blade |
| **Dorrell** | male | 1 | 0 | **1** | 002_Liberation |
| **Winstan Langer** | male | 1 | 0 | **1** | 002_Liberation |
| **Roland** | male | 1 | 0 | **1** | 008_Armageddons_Blade |
| **TOTAL** | | **87** | **18** | **105** | |

**Gender** is determined from actual pronouns in the original
`HEROBIOS.TXT` (`005_RAW/H3bitmap.lod/HEROBIOS.json`) and in the prolog
text itself, not guessed from the name — e.g. `Gem`/`Mutare` are "she"/
"her" there, even though the names alone don't give that away.
`Forest Guard commander` is a generic title with no confirmed gender in
any source, left as `unspecified`.

## Important: "Total" is NOT simply a file count

**"Mission lines (files)" (87 total) are real, already-extracted audio
files**, living in
`005_RAW/<NNN>_<Campaign>/missions/*/*_Media/*_Media.json`
(`audio_en`).

**"+Intro" (18 lines) are NOT files we have.** This is one extra line per
campaign for its own selection-menu intro clip (played before you even
pick a mission - e.g. `CGOOD1.mp4`), added to a character's count on
request. Two different situations hide behind that single number:

- **For 11 of the 13 AB/SoD campaigns**, a dedicated intro audio entry
  really does exist in `Heroes3.snd` - it just hasn't been extracted/
  bundled (deliberately, the intro clip itself was left out of scope) -
  e.g. `ABVOAB1` for campaign 008, `H3X2HSA` for campaign 014. It could
  be pulled in the same way the other 64 voiceover files were.
- **For all 7 RoE campaigns** (001-007), no separate intro code was
  ever found in `Heroes3.snd` at all (see `AUDIO_VIDEO_NOTES.md`'s "Full
  RoE voiceover map" - only per-mission letters a/b/c/d, no distinct
  "intro" slot). The "+1" there is an inference from
  `Heroes_III_Complete.md`'s "overall campaign voice" description, not a
  confirmed recording.
- **008 and 019 deliberately get no "+Intro" at all** - the narrator
  changes mission to mission and the source material doesn't name a
  single intro voice for either; guessing one would be an unsupported
  claim.

## Source

`Heroes_III_Complete.md` (repo root) - matched here **by mission name**,
not by that file's own mission-number column, which turned out to be
wrong for `Armageddon's Blade` (missions 2/3 swapped relative to the
`.h3c`'s real scenario order) - verified against the actual English
prolog text of both missions before trusting the rest of the table.

## Per-campaign breakdown

| # | Campaign | Missions | Intro voice | Notes |
|---|---|---:|---|---|
| 001_Long_Live_the_Queen | Long Live the Queen | 3 | Catherine | whole campaign |
| 002_Liberation | Liberation | 4 | Catherine | missions 2/3 are Dorrell/Winstan Langer |
| 003_Song_for_the_Father | Song for the Father | 3 | Catherine | whole campaign |
| 004_Dungeons_and_Devils | Dungeons and Devils | 3 | Unnamed male general | whole campaign |
| 005_Long_Live_the_King | Long Live the King | 4 | Unnamed male general | Sandro is a central character but never the narrator |
| 006_Spoils_of_War | Spoils of War | 3 | Unnamed female retainer | whole campaign |
| 007_Seeds_of_Discontent | Seeds of Discontent | 3 | Unnamed male general | whole campaign |
| 008_Armageddons_Blade | Armageddon's Blade | 8 | *(not attributed)* | Catherine → Xeron → Gelu → Xeron → Roland → Gelu → Catherine → Catherine |
| 009_Dragons_Blood | Dragon's Blood | 4 | Mutare | whole campaign |
| 010_Dragon_Slayer | Dragon Slayer | 4 | Dracon | whole campaign |
| 011_Festival_of_Life | Festival of Life | 4 | Kilgor | whole campaign |
| 012_Foolhardy_Waywardness | Foolhardy Waywardness | 4 | Sir Christian | whole campaign |
| 013_Playing_with_Fire | Playing with Fire | 3 | Adrienne | whole campaign |
| 014_Hack_and_Slash | Hack and Slash | 4 | Crag Hack | whole campaign (mission 1 has no video, audio only) |
| 015_Birth_of_a_Barbarian | Birth of a Barbarian | 5 | Yog | whole campaign |
| 016_New_Beginning | New Beginning | 4 | Gem | whole campaign |
| 017_Elixir_of_Life | Elixir of Life | 4 | Forest Guard commander | Gelu is the hero but never narrates himself |
| 018_Rise_of_the_Necromancer | Rise of the Necromancer | 4 | Sandro | whole campaign |
| 019_Unholy_Alliance | Unholy Alliance | 12 | *(not attributed)* | rotates: Yog → Crag Hack → Gelu → Gem → Yog → Gelu → Sandro → Sandro → Gelu → Yog → Gem → Gem |
| 020_Specter_of_Power | Specter of Power | 4 | Sandro | whole campaign |
