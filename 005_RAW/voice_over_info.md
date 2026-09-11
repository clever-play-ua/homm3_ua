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

Quick overview first, full per-mission text below it.

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
| 008_Armageddons_Blade | Armageddon's Blade | 8 | Catherine → Gelu → Xeron → Xeron → Roland → Gelu → Catherine → Catherine |
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

## Full per-mission text

Mission numbers/order match the current `005_RAW` folder layout (verified against
heroes.thelazy.net — see [readme_chronicles.md](../readme_chronicles.md) sibling project
for the same treatment applied to Heroes Chronicles).

### 000_Intro — Intro Cinematic

**H3INTRO.mp4 — Catherine**

> Seven weeks have passed since we set sail from Enroth. Slaves freed from our skirmishes with Regnan fleets talk of the turmoil in Arathia. I suspect their stories are true, but I must see the evidence with my own eyes.
>
> The ocean tides were kind enough to bury the fallen on its shores. However, the smoking ruins of Cloudfire greeted us with nothing but destruction and a stench of death. With no survivors, only the battlefield could tell me what happened here.
>
> Despite the breath of devastation, the presence of Minotaurs suggests a raiding party. However, the ranks were too well organized. This is the work of the Dungeon Overlords. Evidently, the wizards were prepared, but overrun nevertheless.
>
> These atrocities rend my heart and fuel my anger. Arathia's banner must be respected, never disgraced. I think of my beloved Rowand and my son Nikolai and how much further this war will carry me from them, but my duty is clear. My father's kingdom must survive. Arathia must not fall to its enemies.


### 001_Long_Live_the_Queen — Long Live the Queen

**1. Homecoming — Catherine**

> Our initial landing has captured a devastated outpost.  Information is scarce and unreliable at best.  Neighboring citizens have fled their villages.  Remaining survivors tell conflicting stories.  Evidence points to a Nighon invasion.  Rally local militia and train them quickly.  Destroy all hostile forces you encounter.  Assume the worst.  Assume we are at war.

**2. Guardian Angels — Catherine**

> "Pressing toward Erathia’s capitol of Steadwick, we have encountered peasants talking of Fair Feather, a town to the north. Though surrounded, it has withstood the Nighon invasion.  Reports are unconfirmed, but these peasants believe 'angels' watch over the town.  Angels have been spotted in Erathia before. During the Kreegan infestation, scattered reports told of winged beings massacring large Kreegan forces. Either the angels have returned, or they never left. How long Fair Feather can last against the Nighon and Kreegan onslaught is unknown.  If Fair Feather falls, a potential ally may be lost."

**3. Griffin Cliff — Catherine**

> "Each year, griffins from around the world migrate to Griffin Cliff.  Armies of King Gryphonheart the First tamed the griffins and trained them for war. With these great beasts, King Gryphonheart unified the divergent human colonies and formed Erathia. King Gryphonheart felt the land’s native griffins were key to any Erathian war. To secure Steadwick, we need the griffins."


### 002_Liberation — Liberation

**1. Steadwicks Liberation — Catherine**

> Early intelligence reports forces from Nighon and Eeofol have barricaded themselves inside Steadwick. All land access to the capitol has been blocked. Their reinforcements arrive via underground tunnels. Armies from the west will meet us on the field of battle. There is little else to say. We do not stop until Steadwick is liberated.

**2. Deal With the Devil — Dorrell**

> "My name is Dorrell, ambassador from AvLee. I bring a message from Queen Catherine. After the liberation of Steadwick, a Kreegan envoy appeared before the royal court. He claims they have captive, King Roland Ironfist of Enroth. They are asking for one million gold ransom. We cannot validate this claim. True or not, Queen Catherine is unwilling to pay.  After interrogating the envoy, we learned Roland is held deep inside Eeofol by Clan Kreelah. Locate Clan Kreelah's base of operations and rescue Roland.  In addition to your Erathian army, we will support you from AvLee. This mission is of utmost seriousness. You may rescue Roland, or find yourself the victim of a trap."

**3. Neutral Affairs — Winstan Langer**

> "My name is Winstan Langer, ambassador from Bracada, ruled by Grand Vizier Gavin Magnus. Forces from Tatalia and Krewlod are fighting in west Erathia. After months of conflict, the battle still rages.  Though weary of yet another war, my king sends reinforcements to aid your efforts.  Brilliant tactics will not win this battle. Body count will determine the victor. Good luck."

**4. Tunnels and Troglodytes — Catherine**

> "We now know how Erathia fell to Nighon and Eeofol. Through an extensive network of underground tunnels dug by the Overlord’s armies, they struck simultaneously in many areas with overwhelming numbers. Credit the military for holding the invasion to half the country.  We have discovered the main artery for transporting forces from Nighon to Erathia; it is under the ocean, connecting the Nighon underworld to the Erathian mainland. Bracada and Avlee have sent armies to join the fight.  First we must eliminate the remaining Kreegans and Nighon forces from the mainland, then pursue them underground, and drive them back to the shores of Nighon."


### 003_Song_for_the_Father — Song for the Father

**1. Safe Passage — Catherine**

> "Upon liberating Steadwick, my fears were confirmed.  My father did not die of natural causes.  He was poisoned. Investigations conducted by General Morgan Kendal prior to the war yielded no suspects. Now I learn the necromancers, seeking a military tactician equal to myself, have resurrected my father, King Gryphonheart. After killing King Vilmar, he took command of their military and their throne.  Now they come to us.  They cannot stop the monster they have created.  As a gesture of good faith, they send a messenger to speak only to me. He will tell me who killed my father. Find this hero and deliver him to me safely."

**2. United Front — Catherine**

> "I grow weary of this war. So do the necromancers. We have agreed to co-operate in the destruction of King Gryphonheart. I never thought I would fight alongside the necromancers, but today we forge weapons for both our armies. With their help, along with the forces from Bracada and AvLee, we should be able to repel all undead from Erathia."

**3. For King and Country — Catherine**

> "What remains of my father's undead army is the Necropolis where he resides. His last legions of undead are significant.  I will join this difficult battle, but you will command the field.  There is one more order you must follow without question. Lord Haart must not die. He is our traitor. We have confirmed the information the necromancers gave to us. Lord Haart was part of King Vilmar's necromantic cult. With Lord Haart's access to Steadwick, poisoning King Gryphonheart's food was a simple task. Acting on orders from King Vilmar, he sought to avenge the banishment of the necromancers from Erathia. I have special plans for Lord Haart."


### 004_Dungeons_and_Devils — Dungeons and Devils

**1. A Devilish Plan — Unnamed male general**

> "A large elvish population inhabits Erathia’s southeastern coast.  Green and gold dragons, native to the region, augment their military strength.  Before we conquer this region, and detour our forces to Steadwick, we must annihilate these dragons.  Our Kreegan allies from Eeofol requested the honor of this mission.  The Kreegans are fierce warriors.  They will enjoy the slaughter."

**2. Groundbreaking — Unnamed male general**

> "Reports claim a fleet of Enrothian warships have landed on the southern coast of Erathia. We do not know who commands this force, or its size. Through sources in Eeofol, we know Roland Ironfist cannot lead this fleet. Regardless, our plans remain unchanged.  We start the last phase of our underground invasion and solidify our position along the southeastern coast.  Afterwards, we can transport more reinforcements from Nighon.  We have dug the last tunnels to this area.  You will have the tactical advantage."

**3. Steadwicks Fall — Unnamed male general**

> "Catherine Ironfist has enlisted aid from Bracada and AvLee.  She knows we are close to Steadwick.  We must occupy Steadwick before she arrives.  Once we own Erathia's capitol, not even Catherine Ironfist will wrench it from our hands."


### 005_Long_Live_the_King — Long Live the King

**1. A Gryphons Heart — Unnamed male general**

> "Our nation's goal was to kill the man who banished us from Erathia. However, Nighon and Eeofol's subsequent invasion has done us an unexpected favor.  Erathia is strewn with the dead.  For the necromancers, this is a season of harvest. This is a season for war.  Queen Catherine is a formidable foe. To defeat Erathia's remaining military, we need a tactician greater than her. We have a plan... an ironic plan. While Catherine organizes the last stages of her war with Nighon and Eeofol, you will sneak into Erathia and locate King Gryphonheart’s grave. Be wary. The region is occupied by scattered Erathian. When the gravesite is found, we will resurrect the dead king and make him our pawn. With King Gryphonheart commanding our armies, his former home will become our land of the dead."
>
> "While resurrecting King Gryphonheart from the dead, former King Vilmar met with an unfortunate accident. King Gryphonheart has taken command of the military... and the throne. His control over the dead is beyond anything we have seen. This bodes well for our invasion. However, our lords watch their new king, searching for a sign of weakness."

**2. Season of Harvest — Unnamed male general**

> "Before we begin our large scale invasion of Erathia, we must fill our ranks. Erathia’s populous will provide the recruits we need. Invade the local region and resurrect the needed troops."

**3. Corporeal Punishment — Unnamed male general**

> "A Death Knight named Mot, refuses to obey King Gryphonheart’s orders.  An example must be made so others will not contemplate such traitorous action.  Mot has insulated himself with his armies.  Infiltrate his troops, kill him, and take his command.  When he is dead, resurrect his corpse and employ him in your ranks."

**4. From Day to Night — Unnamed male general**

> "Erathia's military lies before us. It is time to make a bold strike. King Gryphonheart has trained their generals and knows their tactics. Morale will decide this battle.  Morale is not a factor for the undead.  Once we fill our ranks with their dead, our horde will grow and their morale will falter.  Then we will swarm over them. Soon King Gryphonheart will rule Erathia once again."


### 006_Spoils_of_War — Spoils of War

**1. Borderlands — Unnamed female retainer**

> "As you foresaw milord, King Gryphonheart’s death brings many opportunities for your mercenary skills.  A messenger from Tatalia, on behalf of King Tralossk, has contacted us.  Twenty years ago, following numerous border skirmishes along the western shore of Erathia, Tatalia signed an agreement to cease hostilities. King Gryphonheart is dead.  Their agreement has died with him.  Aggressive tactics have never been part of Tatalia's military character.  Their ranks are vast, and once they possess Erathian land, they will hold it.  However, they need generals to guide their heroes to expand their borders and accommodate their growing population."

**2. Gold Rush — Unnamed female retainer**

> "Your abilities have been brought to the attention of the barbarian nation of Krewlod. Their skirmishes with the Erathian military on their eastern border are legendary. Many credit them for hardening Erathian soldiers. Recently, a border raid resulted in victory, and uncharacteristically, a large numbers of prisoners. Upon interrogation, their suspicions were confirmed. Without King Gryphonheart, Erathia has lost its soul.  Your goal is to quickly plunder the Erathian land within Krewlod’s immediate reach. Once they have the resources they need... war will be discussed. Until then, your independent participation is needed.  Should you be captured, Krewlod will claim you were an over zealous clan leader, acting outside the interests of the nation."

**3. Greed — Unnamed female retainer**

> "Representatives from both Tatalia and Krewlod seek your services... again. Both nations claim the last strip of Erathian land between their countries. Few Erathian castles remain in the area.  They are nothing more than token resistance.  The most ferocious battles will occur between Tatalia and Krewlod.  Ironically, this land has little value. This is a border war. Tatalia seeks to further extend its reach from the lowlands to the hills. Krewlod wants to halt Tatalia’s march before it reaches their northern border. No matter which side you fight for, the other will perceive you as a traitor. Choose wisely.  Choose the winning side.  Your life depends upon it."


### 007_Seeds_of_Discontent — Seeds of Discontent

**1. The Grail — Unnamed male general**

> "For the first time in the history of the Contested Lands, humans and elves have fought alongside one another to defend the region from invaders. When the celebration is over, old hatreds will return and we will be citizens of a land in conflict. We must think about the future of the Contested Lands.  It is time to shape its future.  If our fight for independence is to succeed, we need something greater than our armies to motivate the populous. We need a symbolic cornerstone. Seek out the Grail in the enchanted lands where the Unicorns converse with the trees."

**2. Independence — Unnamed male general**

> "Our cause is public.  Ironically, many humans have joined the elfin population in our vision of an independent state. Already, factions loyal to Erathia and AvLee organize to stop us. We cannot continue without a strong base of operations. Faruk Welnin, mayor of the town of Welnin, has sent a messenger.  He offers his protection and support. Our war for independence begins now. We must fight our way to Welnin and establish the Grail. When we have accomplished this, Welnin will become our foundation."

**3. The Road Home — Unnamed male general**

> "We have come far very quickly. Armies from Erathia and AvLee have arrived to 'restore order.' This jeopardizes our quest for independence, and such hostile elements could ignite a larger war. It is our duty to establish Welnin as the capitol of the Contested Lands and the drive rule of Erathia and AvLee from this territory. If we do not, we will lose all we have fought for and two great nations may once again re-enact the carnage of the Timber Wars.  Today we declare our independence from the nations of Erathia and AvLee."


### 008_Armageddons_Blade — Armageddon's Blade

**1. Catherines Charge — Catherine**

> Eeofol troops have pushed to Erathia's border.  Queen Catherine herself has chosen to stay the tide of these invaders by controlling the border and digging in until reinforcements can arrive.  Catherine must not fail.
>
> I have underestimated my opponent's strength and resolve.  During the Restoration Wars, the Kreegans were of minor concern.  Now they fight with an urgency neither I nor Roland have encountered.  I have pulled the bulk of my forces back behind Erathia's border.  Between us and the Kreegans lies Moss Valley.  It is one of Erathia's more beautiful landscapes.  Tactically, it is ideal.  If I can hold this valley, I can close the border.  Then I can determine how to destroy the demon king Lucifer and his quest to set the world on fire with Armageddon's Blade.

**2. Shadows of the Forest — Gelu**

> Gelu, the half-Vori elf leader of Erathia's elite unit known as the Forestguard, has been ordered to wage a shadow war along the Avlee-Eeofol border.  This area is rife with small garrisons and outposts.  It is from these levies that Gelu shall draw his guerilla force.
>
> Messengers inform me Queen Catherine and Roland Ironfist are retreating to the Erathian border.  Avlee has chosen to turn a blind eye toward the war, but have purposely left local heroes to their own will.  Under the Queen's orders we are to wage a 'hit-and-run' war along the Avlee border.  Our only support will be local militia hostile toward the Kreegans.  Should we be captured, Erathia and Avlee will disavow any knowledge of our actions.  Otherwise... this task is no different than before.

**3. Seeking Armageddon — Xeron**

> The greatest hero in all Eeofol is Xeron the Terrible.  He has been attempting to fulfill King Lucifer's vision for some time now, but every time he has gotten close to one of the objects needed to build Armageddon's Blade, a hero from the Elemental Conflux has arrived to take it.  Now he has them cornered in Avlee and they are ripe for the picking.
>
> My quest is sacred, given to me by the king himself.  I have searched the continent for the relics he desires.  When I have come close, a mysterious hero has spirited my prize away.  I have pursued these heroes for months.  Now, I have them cornered.  They will either surrender the relics, their lives... or both.

**4. Maker of Sorrows — Xeron**

> Xeron must seek out the Grand Forgesmith, Khazandar.  He is the only man with the knowledge and skill to build Armageddon's Blade and it is vital that he "convince" him to do this.  There shall be interference from the accrused Conflux towns.  He must complete this quest and then return to the capitol.
>
> My king seeks to build Armageddon's Blade.  With this fabled weapon he will set the world on fire.  I have the elements to build the blade, but only the grand forgesmith Khazandar can fashion it from the relics I carry.  Again, a collection of mysterious heroes gather to end my quest.  Ironically, they have surrounded Khazandar, but have not killed him as I would.  This proves they are soft.  They will not stand in my way.

**5. Return of the King — Roland**

> King Roland and General Morgan Kendal are on the western shores of the Great Lake and must take a mixed Erathian-Conflux army deep into Kreegan territory.  They must cross the lake and go through the mountains and prepare to make a push towards Catherine's army in the north, thus trapping the devils between the two forces.
>
> Heroes from the Confluxes tell us the elemental gods have sent them to us, so together, we might destroy Lucifer Kreegan and his quest to set the world on fire.  Catherine trusts these new allies.  I am not as giving.  However, we do not have a choice as support for the war wanes and our forces dwindle.  If these elemental heroes are to be our allies, they will prove themselves in this forthcoming battle... under my command.

**6. A Blade in the Back — Gelu**

> Gelu must take his army to cut off any escape routes the Eeofol army might be able to use.  King Roland and general Kendal are moving against the Kreegans and pushing them towards him, along with Queen Catherine's forces.  To ensure King Lucifer is defeated, the Kreegans must not be allowed to escape.
>
> In my operations, information is always scarce, and never given full trust.  Now I am told the elemental Confluxes we have encountered, have allied with Queen Catherine in her war to destroy King Lucifer Kreegan.  I have orders to move deep into Eeofol, behind the main Kreegan force Catherine holds at the border.  There I am to cut off any potential escape route.  I pray this is not a trap.

**7. To Kill A Hero — Catherine**

> Catherine has lost support in Erathia.  They are tired of war and do not wish to pursue this any further.  To ensure victory, Catherine has stepped down as Queen and joined Roland with the Conflux army, pushing deeper into Eeofol.  General Kendal has been left to see to the task of picking Erathia's next ruler.  In secret, he has dispatched Gelu and his Forestguard to help his former Queen and good friend in this most serious of endeavors.
>
> With the majority of the Kreegan forces destroyed, Erathia's lords have grown weary of this war and have withdrawn their support.  They do not understand.  This is a critical moment.  To continue this war, I have stepped down as Erathia's Queen.   Myself, Roland, and the Conflux forces will continue to press to the capitol of Eeofol.  However, between us and the demon king stands the hero Xeron.  We are told he wields Armageddon's Blade.  We must succeed for the safety of Erathia, and the world.

**8. Oblivions Edge — Catherine**

> The Kreegan race borders on extinction, yet remains defiant.  King Lucifer has sent for aid from the Overlords of Nighon.  It is estimated that it shall take no more than 60 days for an army to arrive and reinforce the Kreegan king.  The tide has turned as Catherine's army now has the Blade and the irony of Lucifer's downfall under the Blade he created to destroy the world has not escaped Catherine.  She intends to bring the Blade to Hell itself if need be.
>
> Armageddon's Blade is no longer a threat.  However, King Lucifer Kreegan still sits upon the throne of Eeofol.  What few clans remain have rallied to defend their king and his lost cause.  Erathian spies tell us the demon king has requested support from the dungeon overlords of Nighon.  We cannot confirm this.  If it is true, we cannot allow Lucifer to receive this aid.  We must dethrone the demon king.   Time is short, but now we wield Armageddon's Blade.  It is time we take armageddon into the heart of hell itself.


### 009_Dragons_Blood — Dragon's Blood

**1. Culling the Weak — Mutare**

> Ordwald, your near neighbor, is the oldest lord in Nighon.  Age has started to effect the old warlock, but he is still able to beat off the other young lords.  Unlike the others, you have patiently waited for Ordwald to stumble before you move.  Last week, Ordwald slipped.  Time to take him down.
>
> Ordwald.  I find the name distasteful.  This old man has held rich Nighon lands given to him by a much greater father.  He has squandered his time and done little to earn his stature.  I have stood in his shadow and by his borders too long.  His lands will be mine.

**2. Savaging the Scavengers — Mutare**

> Interrogation reveals Ordwald didn't personally defend his lands because he is seeking the fabled Vial of Dragon Blood. Unfortunately, Caomham and Preuet have also heard about the Vial. They will certainly follow you into the Deep Caverns after Ordwald if they can. You need to dispose of them first.
>
> Ordwald is absent.  No wonder his lands were so easy to take.  It seems he has spent his life and his father's fortune in pursuit of the fabled Vial of Dragon Blood.  It is said to hold blood taken from the Dragon Father.  It is believed drinking it will transform the user into a sentient dragon.  Orwald isn't as stupid as I believed.  Still, he is old.  I will find him and the vial, but first, I must dispose of the young lords who have heard the news and nip at my heels.

**3. Blood of the Dragon Father — Mutare**

> Whoever gains the Vial of Dragon Blood and drinks the Blood of the Dragon Father with transform into a Sentient Dragon.  You MUST beat Ordwald to the Vial and defeat its guardians.  Nothing else matters.  Nothing!
>
> I have found Ordwald.  He is close to the vial, but his conservative actions and slow thinking leaves the way open for me to surpass him.  As much as I must worry about Ordwald, I must consider the vial.  Once I have passed him, there is the vial, and no doubt, it will have guardians... dragon guardians.

**4. Blood Thirsty — Mutare**

> Ordwald lied to three powerful Nighon Lords.  He told them, if they were to drink your blood they would also transform into dragons.  Now your old opponent Ordwald and three powerful lords block your access to the upper tunnels.  They want to kill you and drink your blood.  You plan to drink theirs.
>
> I am successful.  Now Ordwald and his lacky's seek to slay me and drink my blood.  They believe it will transform them as the vial transformed me.  They will never drink my blood.  I will be the one to drink their blood.


### 010_Dragon_Slayer — Dragon Slayer

**1. Crystal Dragons — Dracon**

> You face the last challenge in becoming a Dragon Slayer.  You must complete the test course in six months or fail the test.  The Crystal Dragons will be well guarded, the paths watched by other creations.  Golems, Gargoyles and Elementals will try and stop you before you can kill the Crystal Dragon.
>
> My mother has finished preperations for my final test.  The finest crystal, stealthly taken from the caverns of Krewlod, has been used to create a great dragon golem.   This creature's construction is a feat of magical prowess.  To destroy it... is an even greater feat.  Yet, I have heard the greatest feat a dragon slayer can accomplish is to kill the rare a mighty Azure Dragon.

**2. Rust Dragons — Dracon**

> Now in search of the mighty Azure  you hear of disturbances to the North.   Burned villages and destroyed mines are causing the region to suffer.   Without the mines in full production the region will not have the resources to defend themselves against Krewlod invasions or eat.  Knowing you are the destined Dragon Slayer, it is time to follow the road north in search of ways to hone your skills.
>
> Rust dragons have taken to feeding from the mines near the town of Ochre.  These uncommon beasts have chased off the peasantry and now their livelihoods are in jeopardy.  As a hero, I should do this for the town's people.  Yet, I do this to hone my skills.  Where rust dragons abound, the Azure may be nearby.

**3. Faerie Dragons — Dracon**

> Now seeking the famed and elusive Azure Dragons you hear of sightings to the west.   Following the leads you find only a mischevious Faerie Dragon playing tricks on the locals.  Disappointed at first, but soon you discover there are several such dragons and they are relocating towns, maidens and generally mucking about.  This should prove challenging enough for you.
>
> I have never seen a Faerie Dragon.  Little is known about these notorious troublemakers.  What is known is found more in storybooks than magical tomes.   Some say they are invisible.  Some say they can cast spells.  Some say they are only three feet high.  Some say they are the henchmen of the Azure Dragons.   I do not know what to expect or how my skills will be tested.  Nevertheless, the more I know, the better I will be prepared for the Azure Dragons.

**4. Azure Dragons — Dracon**

> Finally, you have tracked down the Azure Dragons.  Now it is time to face the great dragon in their home territory.  The locals are willing to join your cause, but the paths are guarded by dragons.  Clear these paths and you can gain support.  The Azure Dragons are both mighty and elusive.  Track them down and kill them before they moves on to new territory.  You estimate in six months they will move again. Once you have gained their support you can then seek your prize.  Beware the other Dragons who guard the Azure, keeping out the fainthearted and unworthy of such a challenge.
>
> I have found a nest of  mighty Azure Dragons.  I have also found my destiny.  Azure Dragons do not nest for long and commands an entourage of dragons of all colors.  The task is great, but I am determined.


### 011_Festival_of_Life — Festival of life

**1. Razor Claw — Kilgor**

> The time has come for you to challenge the elders for leadership.  Like other young prospects of the tribe you must pass through three tests.  The first test is simple, kill an Ancient Behemoth.  For three generations the Ancient Behemoth Razor Claw has resisted attempts to kill it off, now it is your time to make the attempt.  Complete this simple task to continue with the festival of life.
>
> Alongside my father I have killed Behemoth before, but never an Ancient Behemoth.  To contest the throne, I must slay one of these fearsome beasts.  I relish the encounter.  After I have slain this one, I will know how to subdue them.  Then I will employ them in my bloody ascension to kingship.

**2. Taming of the wild — Kilgor**

> This area is kept wild and is only culled every thirty years during the Festival of Life.  Each prospective is given a small section to clear and three allies to command in order to prove your capabilities as a leader.  In order to prove you are truly capable you must eliminate all creatures in this region, once this is completed you will have passed this test.
>
> I have tamed a great beast.  Now I must tame the monsters of the land.  As the carnage grows, so does my power and bloodlust.  I will sit upon the throne of Krewlod.  Neither man or beast will stand in my way.

**3. Clan War — Kilgor**

> Excellent work young one!  Now you and three others must compete for the chance to challenge the king.  Defeat them and their lieutenants in order to claim victory.  The three allies that helped you in the second mission will assist you in this one, good luck.
>
> In the Festival of Life, those who fail, either die at the hands of their enemies, or by their own hand after capture.  I will be merciful toward my opponents.  I will take no prisoners.

**4. For the Throne — Kilgor**

> You have risen through the ranks quickly, proving your worth and capabilities as a warrior and leader.  Now you challenge King Boragus for the Throne of Krewlod itself.  If you can defeat the powerful Boragus it will prove your battle skills and determination are unrivaled in all of Krewlod.  This one is to the death.  The winner rules.
>
> Many respect King Boragus.  Many feel he is one of the greatest rulers Krewlod has ever known.  I do not know this king personally and I find his accomplishments unimpressive.  If he is to earn my respect, he will do so only when he stands over my grave.


### 012_Foolhardy_Waywardness — Foolhardy Waywardness

**1. Lost at Sea — Sir Christian**

> While on a three-hour sight seeing tour Sir Christian's ship was blown off course by a sudden summer storm. When the storm cleared the captain and crew had no idea what their position might be. For nearly a week they sailed under an overcast sky, completely unable to determine their heading. Finally, a small rocky island was spotted. While landing their ship a large rock found it's way into the hull making the craft irreapirable.The curious natives seemed friendly in meeting with Sir Christian. They agreed to help him get off the island if he built them a capitol.
>
> All I wanted was a simple vacation.  One hurriance later and I am here on this island with these foul smelling natives.  Perhaps my father was right when I told him about my dream to become a fragrance alchemist.  Maybe my military training can help me get off this forsaken sand prision.

**2. Their End of the Bargain — Sir Christian**

> The natives where so happy at Sir Christian's success, they completely forgot about the agreement to help him in return. The days and days of celebration turned into weeks of endless parties leaving Sir Christian very angry.  While the natives were celebrating he traveled to the tavern and met with the former leaders of the towns he'd just beaten. The leaders come to the conclusion Sir Christian was too dangerous to have around.  The bargain was struck and Sir Christian would gain their lands and they would gladly help him to leave.
>
> I swear... these natives only know two things: how to start a war and how to throw a party.  Apparantly, the natives I just defeated want me off the island as much as I want off.  One condition, I must reclaim the lands I just took from them.   Ugh.   The stench.

**3. Here There Be Pirates — Sir Christian**

> Sir Christian was on his way home when one of his crewmembers discovered that the boat had no navigational equipment. Instead of getting a sailing ship, they got a dinghy for short distance traveling.  After many days and nights at sea, they found their salvation and discovered another small island... full of pirates.
>
> I do not know if it is poetic justice, a bad joke, or plain rudeness, but I was informed my native friends 'forgot' the rather important navigational equipment.  After many days and nights, we found our salvation and discovered another small island... full of pirates.  Apparently they too do not understand the art of the fragarance alchemist.

**4. Hurry Up and Wait — Sir Christian**

> After finding out he was being used as a tool against his own land and queen, Sir Christian finished his quest and fled the island, stole a real sailing ship and went to Queen Catherine's military island to protect it. The four surrounding islands that once protected the main island are now infested with Regnan Pirates. Queen Catherine may pay a visit to this island in four months.
>
> If you were to ask me where my loyalities lie, in all honesty, I would answer, "To whomever could get me home."  So, when I learned of the nearby Erathian outpost, I knew I had found my esacpe.  So, I left those filthy pirates in the middle of the night and arrived at the Erathian outpost the following morning.  Little did I know the outpost was the next target of my former pirate allies.


### 013_Playing_with_Fire — Playing with Fire

**1. Farming Towns — Adrienne**

> The peasantry has been slaughtered to make an undead army.  It is as if someone is farming the people to grow a mammoth crop of mindless soldiers.  The purpose of this army is still unknown, but someone must restore order on the Ertahian-Tatalian border.  That someone is you.
>
> Traveling from Erathia to my homeland of Tatalia, I have passed through several towns.   I have yet to encounter a living soul.  There is only the lingering stench of the undead.  I fear a necromancer in the area is raising an army.  'Who...' is unknown.  'Why...' is unknown.

**2. March of the Undead — Adrienne**

> It has been confirmed.  Lord Haart was raised from the dead and is now sweeping through Tatalia creating an undead army of mammoth proportions.  Behind the Undead Knight lies a trail of death and destruction.  To track him down is the easy thing.  Restoring the land he has destroyed is another matter all together.  Free the inhabitants from their undead captors and they will join your cause.
>
> With the conclusion of the Restoration War, Lord Haart's necromantic cult disbanded and went into hiding.  It appears they have resurfaced and resurrected their leader.   Now Lord Haart walks the Tatalian lands a Death Knight.  If I am to continue my hunt for the dead warrior, I will need help.  I hope my countrymen will be wise and not shun a hero who embraces fire magic.

**3. Burning of Tatalia — Adrienne**

> It is time to confront the Death Knight Lord Haart.  Take your armies and defeat the traitorous fiend.  His loyal followers assist this force of death as he mows a path through Tatalia several miles wide all the way to the ocean.
>
> I do not know what the dead remember from their time among the living.  If Lord Haart had memory of Tatalia, it has failed him.  Scouts report the dead knight has turned northwest and set up along the coast.  Now I have him trapped.  However, army morale is low.   My people do not like following a fire witch, yet they dislike becoming undead even more.


### 014_Hack_and_Slash — Hack and Slash

**1. Bashing Skulls — Crag Hack**

> This relatively rocky part of Avauntnell has been home to many a Barbarian group over the centuries (probably due to it being close to Krewlod).  Numerous attempts at Erathian settlement in this area have mostly failed due to the harsh environment and the barbarian raids, but one or two towns might still be found.
>
> After watching me clobber a pack of goblins in a bar fight, a Wizard named Sandro asked me to come to his table.  He wants to pay me to find him something called a Skull Helmet.  I'll probably have to bash someone's head in to get it.  Sounds like it's going to be fun!

**2. Black Sheep — Crag Hack**

> This part of Avauntnell was once home to wandering tribes of barbarians, but of late the lush grassland and forests (with only a few swamps) have attracted settlers.  These settlers, needing to fend off the occasional barbarian raid and bandit strike, have started their own offshoot of the Erathian militia.  Any non-Erathian who enters this region should beware.
>
> I went back to the Tavern to give Sandro this ugly Helmet he wanted.  Now he wants me to get some kind of sword from a Death Knight.  That tin plated corpse is hiding out in a swamp, so I have to trudge through miles of muck before I get a chance to hack the sword out of his cold dead hands!

**3. A Cage in the Hand — Crag Hack**

> A small group of Necromancers called "The Ebon Hand" live in this part of Avauntnell.  Erathia hasn't really dealt with them, for this is an out of the way swampy area, and it really isn't worth the time and expense to mount a campaign against them.  It is said they worship one of the undead races as gods and keep them under lock and key to be worshiped day and night.
>
> I got Sandro his cursed sword, and now he wants me to fight more moldy Necromancers to get some kind of armor made out of bones.  Hah!  It'll be their bones I smash!

**4. Grave Robber — Crag Hack**

> Another group of Necromancers live in this region of Avauntnell along with a small group of former Erathian Militia who have been bribed by the Necromancers to leave them alone.  The Necromancers, called the "Hand of Death," have been relatively quiet, and Erathia hasn't realized yet that some of their militia has been bribed, so they have been left alone over the past few decades.
>
> Now that I gave him the Death Knight's Sword, Sandro wants me to fight some more Necromancers for a shield.  More stinking Undead to fight!  This is not as much fun as I thought.  Grrrr!  At least this is the last thing I have to find for that puny Wizard to get my reward.


### 015_Birth_of_a_Barbarian — Birth of a Barbarian

**1. On the Run — Yog**

> You have never really been that good at magic.  Not even your Genie blood helped you much.  But still, life was fine up until a few months ago when the love of your life, Vidomina, became overconfident.  Her magic corrupted her and turned her into a Necromancer.  Since then, you have grown to despise magic.  Now you have made a decision to leave the life of a Wizard and become what you have always dreamed of... a Barbarian.
>
> All my life I have been studying magic under the Wizards of Bracada to please my mother, a Genie.  But it is the blood of my Barbarian father that runs through my veins, and I feel that my hands were meant to carry a sword rather than a staff.  Fate seems to agree, for I have received an invitation from Duke Winston Boragus of Krewlod to join his army.  The time has come for me to leave this place, but I know that my teachers will not permit that without a fight.

**2. The Meeting — Yog**

> Not long after you conquered the town of Groa a messenger arrived from Ulgak, the capital city of Krewlod.  To your surprise, it was from the Duke himself.  As you read through the letter you found out that the Barbarians of Krewlod are quite interested in your skills.
>
> Since escaping from Bracada, I have been attacked by a number of Krewlod's armies.  I do not understand why this would be, for I was invited here by the Duke himself!  I must travel to the capital to find out why Winston Boragus and all of his forces have turned against me.

**3. A Tough Start — Yog**

> You left the meeting with Boragus in a very happy mood.  Wanting to prove yourself, you hurry off to Tatalia to deliver the first two pieces of the Armor of the Angelic.  At first you thought this would be an easy task: you would walk into town and give the first two pieces of the Angelic Alliance to Alendora.  After a few days ride from the border, you discover that Tatalians aren't going to make it that easy for you.
>
> When I confronted Winston Boragus, he admitted to setting Krewlod's armies against me to test my worthiness to join them.  At first I was angry at this deception until the Duke pointed out that it was I who wanted to be a fighter.  The Barbarian within me saw his point.  But Boragus has a test designed to see whether I am truly ready to part with the Wizards of Bracada.  I must take the magical Angelic Alliance sword, break it apart and distribute the pieces throughout Tatalia, Erathia and Bracada.

**4. Falor and Terwen — Yog**

> The time spent in Tatalia wasn't very long, and you were quickly on your way to Erathia in search of Falor and Terwen.  With any luck, the Erathians will be less hostile than the Tatalians were.
>
> I gave up the first piece of the Sword, although I had to resist all of my wizardly training to do so.  Now I am to find the hut of a seer named Falor and give him two more pieces: the Celestial Necklace of Bliss and the Lion's Shield of Courage.  This will be no simple errand, for the Erathians don't take kindly to large armies traipsing across their country.

**5. Returning to Bracada — Yog**

> The last leg of your journey has taken you back to Bracada.  You realize that Aine will probably be waiting for you.  Despite this, you decide you don't really have a choice, so you break camp and set out to search for Beleg and Orruk.
>
> The last of Winston Boragus' tests will take me back to Bracada, my forsaken homeland.  I am to find a couple named Beleg and Orruk and give them the two most powerful pieces of the Angelic Alliance: the Sword of Judgment and the Helm of Heavenly Enlightenment.  That will be the easy part, now that I am certain I am ready to give up the ways of magic.  The hard part will be fighting my way past Bracada's armies, for they will not be as willing to give me up.


### 016_New_Beginning — New Beginning

**1. Clearing the Border — Gem**

> You have agreed to take command of the town of Clovergreen's militia and clear this area of the border of undead raiders.
>
> It is hard to believe a year has passed since Archibald and his Necromancer allies were defeated, ending the Succession Wars.  In that time I have been living a nightmare, for I see the ghosts of the fallen all throughout Enroth.  I hope my former teacher, Amanda, is right.  I hope moving to a new land, to Antagarich, will still the ghosts of the war.

**2. After the Amulet — Gem**

> You have agreed to help a wizard's apprentice named Sandro.  Sandro's master, Ethric, needs an Amulet of the Undertaker to perform anti-necromancy research, but Ethric is an academician and Sandro is too inexperienced to go after the Amulet himself.
>
> I have met a Wizard named Sandro who is conducting research to combat necromancy.  He is creating a magical amulet, which will ward off the undead and wants to pay me a large sum of gold to find the pieces he needs to construct it.  He seems to think me quite the mercenary.

**3. Retrieving the Cowl — Gem**

> Terek, Sandro's agent, managed to steal a Vampire's Cowl.  Unfortunately, on his way across the Border Lands bandits captured him.  You must ransom Terek and obtain the Cowl.
>
> When I delivered the Amulet of the Undertaker to Sandro, he told me he had also hired a Barbarian named Tarek to locate another artifact, The Vampire's Cowl.  However, Tarek is long overdue and Sandro fears for his life.  From what I can see, bandits have captured Tarek and are holding him for ransom in an underground prison near the Deyja border.

**4. Driving for the Boots — Gem**

> The last item Gem needs to acquire for Sandro's master is very close to the Deyja border, maybe even inside the border.  The Deyjan Border Lords are not going to be happy with Gem's presence.
>
> I begin my quest for the last item Sandro needs - the Dead Man's Boots.  Unlike the other artifacts, these may actually be inside Deyja, for the borders are in dispute.  One thing is certain: there will be several Deyjan Border Lords in the area, and they will not like me being there.  This is going to be a tough fight, but it will be worth it.  Important things are never free.


### 017_Elixir_of_Life — Elixir of Life

**1. Graduation Exercise — Forest Guard commander**

> This area is a special training area and is the site for your final exam.  Many have failed this test, while more have passed it.  Good luck.
>
> The Forest Guard is Erathia's eyes and ears.  We go where we are needed most and that is usually places difficult for traditional fighting forces to reach.  We are shadows of the forest that see all and bring silent death with a single, unseen bowshot.  You have done well in your training, Gelu, but now has come the time to take the final test.  A small valley near Gaia's Crest will be the site of this trial.  Clear the region of all the enemies to earn your place among the ranks of the Forest Guard.  Good luck.

**2. Cutthroats — Forest Guard commander**

> Bandits infest this region.  Wherever possible, enlist the aid of the Thieves' Guild, as they can be very informative.
>
> Rumor has it that the Ring of Health, one of the essential components of the Elixir of Life, is located in the Shantanna region of southern AvLee.  Time is of the essence, for a Death Knight has been spotted talking to bandits who have long been terrorizing the area, and we believe that he has hired them to find the Ring first.

**3. Valley of the Dragon Lords — Forest Guard commander**

> The Dragon Lords are not known for being all that reasonable, but perhaps you persuade them to part with the Ring without any bloodshed.
>
> The Ring of Life, the second component of the Elixir of Life, is hidden in the valley of Dagrond.  There lives a group of powerful Elven nobility who are the caretakers of several warrens of gold and green dragons.  These Dragon Lords have always been loyal to AvLee, but we fear that one of these lords has been corrupted by the Necromancers.  If this treacherous Dragon Lord gets the Ring before you, he will become an enemy too powerful for the forces of AvLee to withstand.

**4. A Thief in the Night — Forest Guard commander**

> The Vampire Lord Vokial has been using the Vial of Lifeblood to supplement his feedings.  Take it, and he will be forced to suffer the indignation of feeding the old fashioned way.  Stealing it from him will cause him great harm and embarrassment.
>
> The final artifact needed to construct the Elixir of Life is in the undead hands of the Vampire Lord Vokial.  It is said the Vial of Lifeblood allows him to sustain himself without having to resort to more distasteful means of bloodletting.  Although this artifact can be said to be preventing some evil where it is, our need for the Vial is even more desperate.  You must find a way to steal the Vial from this Vampire.  But keep in mind that not every task need be accomplished by direct means.  Use your training wisely and stay sharp.


### 018_Rise_of_the_Necromancer — Rise of the Necromancer

**1. Target — Sandro**

> Ethric is a sly old Warlock.  He has spread word of Sandro and the artifacts he carries to the lords of this region.  Some of the lords want these artifacts for their own use; others want to destroy them.  Sandro must defeat all these lords and get into Deyja.
>
> It seems Ethric, my old master, has finally tracked me down.  He hasn't been too happy about me becoming a Necromancer and wants to remove the blight from his career.  Ethric is no fool.  He spread word of my location to those who would stop me.  It does not matter.  I will defeat these fools, soundly beat my master and continue on to Deyja, where they will appreciate my talents.

**2. Master — Sandro**

> Sandro now faces Ethric and one of his allies.  He must defeat the old Warlock before moving on to Deyja.
>
> Ethric just doesn't give up, but I have found an ally.  Vidomina is a young wizard with aspirations of being a Necromancer.  For the time being she will be useful, but we will part ways once we get past Ethric and into Deyja proper.

**3. Finneas Vilmar — Sandro**

> Sandro and Finneas Vilmar are going to wipe out Lord Alarice before he can tell the others of Finneas' transgressions against the old King of Deyja.  Once they have completed this trivial task, they will be able to work on removing other bothersome lords from the Deyja court.
>
> Traveling to Deyja, I met Finneas Vilmar, an ambitious but slightly foolish Necromancer.  He has some holdings here and is trying to increase his realm of power.  With my skills of persuasion he should soon find himself in the position he craves.  Of course, I will be the shadow whispering orders into his ear.

**4. Duke Alarice — Sandro**

> All Finneas or Sandro must do is remove the Duke of this area.  Once he is gone, they will be literally a step away from the throne.  The new king is still not settled into his throne and will be easily replaced.  With any luck, he will suffer an accident in the future.
>
> Soon Duke Alarice will find himself permanently among the dead.  Right now our plans go well as we prepare to launch an assault.  Finneas does not agree with my tactics, but I know that his tactics are certain death.  It is only a matter of time before he realizes his error and follows my direction.  Soon he will come to see that he cannot survive without my guidance.


### 019_Unholy_Alliance — Unholy Alliance

**1. Harvest — Yog**

> Like fields of wheat, the peasants of this area are harvested to swell the ranks of the undead.  There's no need to ask yourself why the undead would do such a thing.  Why pretend to know the ways of evil?  However, you can't shake the suspicion that something far more sinister is at work.
>
> A Necromancer is at work here.  Peasants all throughout this land are turning up as walking corpses.  But no noble or lord has come forward to put a stop to this.  I will take it upon myself to destroy this menace!

**2. Gathering the Legion — Crag Hack**

> The town of Hartferd has remained independent because the two lords of this region have been too busy fighting each other to turn their greedy eyes on new territories.  Recent rumors place the Legion artifact in the vicinity, so life in Hartferd is likely to get a bit more complicated.
>
> On my way to visit some relatives in Erathia, I came across a village that had its sacred artifact, The Head of Legion, stolen.  The mayor wants the head back as well as the other pieces of Legion, if I can find them.  This is just what I need to lift my spirits, some fun!

**3. Search for a Killer — Gelu**

> Gelu has been summoned to investigate the death of Lord Falorel.  Many believe poison is the cause.  But Gelu quickly discovers that Falorel was never among the living.  He was a vampire masquerading as an AvLee lord!
>
> This morning I learned Lord Falorel was dead, apparently from poison.  What was learned soon afterwards has sent shockwaves throughout all of AvLee.  He was actually a Vampire disguised as an Elvish warlord.  I must find out who poisoned him and how he came to such a high position within AvLee.

**4. Final Peace — Gem**

> Gem's employer, the AvLee border lord Fayette, has been killed by the Necromancers while on a secret mission.  Never able to leave an enemy defeated, the Necromancers have further humiliated Fayette by raising him as a Death Knight.  Gem can't accept this insult.  Lord Fayette's undead body must be destroyed to grant him final peace.
>
> When I went to tell Lord Fayette about Sandro tricking me, I learned he left on a mission into Deyja while I was searching for the boots and had not yet returned.  So I scryed for Lord Fayette and discovered his mission had gone horribly wrong.  He had been killed by the Necromancers and... and... resurrected as a Death Knight!  Curse all Necromancers!  There is one last service I can do for my lord.  I will grant his soul final peace by destroying the undead body chaining it to this world.  I owe him that much.

**5. Secrets Revealed — Yog**

> The presence of the Necromancers in Erathia is much stronger than you first anticipated.  It's apparent you can't win this battle alone, so you seek help.  Your choice of an ally was obvious, but Crag Hack wasn't easy to find.  It took even longer to convince him that these "spell casters" had to be stopped.  In the end, it was Crag Hack's unquenchable desire to smash undead that convinced him.
>
> We two Barbarians were glad to have found each other in this land of strangers.  Both of us are following the trail of the Necromancers, but I am shocked that their actions seem to have gone unnoticed by Erathian leaders.  Crag was not interested in investigating my concern further until I mentioned his glorious battle.  That always works with Barbarians like him.

**6. Agents of Vengeance — Gelu**

> Gelu and Gem have been ordered by the Council of Elders to avenge the murders of Lord Fayette and the numerous other victims of the Necromancers.  Their goal lies through Deyja toward the Erathian border and the Necromancer's Castle, where information about Lord Fayette's death is sure to be found.
>
> Several days ago the AvLee Council of Elders commanded Gem and myself to avenge the deaths of Lords Falorel, Lord Fayette, the Dragon Lords and all the other victims of the Necromancer's raids.  At the border we encountered this... this horrific scene.  The Deyjan lords must be destroyed before all of AvLee is harvested for their undead armies.

**7. Wrath of Sandro — Sandro**

> With Finneas on the throne it's time for the next step of your plan.  AvLee, Erathia and Krewlod troops have all invaded Deyja territory, thinking they have you where they want you.  But it's just the opposite, isn't it?  It was you who drew them here, right where you want them, and now your goal of world domination is a little closer.
>
> Four very brave but foolish heroes have entered my realm.  They seek to dissuade me from invading Erathia and AvLee with their combined forces.  However, I welcome their intrusion, for my undead armies could use more recruits.  I shall harvest these heroes, and they will pay for their impudence with their eternal souls.

**8. Invasion — Sandro**

> The battle is half over.  Now you and Finneas must simultaneously invade AvLee and Erathia.  Concentrating your troops on one of the countries will give the other a great tactical advantage.  Therefore, your troops must be divided.  Some call AvLee's armies "the Wall of Destruction," and everyone knows Erathia's defenders are just shy of invincible.  This will be no easy task.
>
> It was easy to remove the AvLee, Erathian and Krewlod troops from Deyja, but the invasion itself will be much more difficult.  To launch an offensive that will not leave one border open, we must assault both borders simultaneously.  Once again, Finneas wishes me to handle the matter personally.  His faith in my abilities is touching, but even a puppet King must someday learn how to command if he is to be an effective tool.

**9. To Strive To Seek — Gelu**

> Gem and Gelu are seeking parts of the "Angelic Alliance" in a region of Erathia bordering AvLee.  Two warlords rule this land, and their allegiance is loosely tied to Erathia, so they'll have to be "persuaded" to relinquish these artifacts of power.
>
> I know this region well.  The lords who control this area are loyal to Erathia but only when it suits them.  We must be careful, for they are formidable foes and deeply entrenched.  But if we are to locate the pieces of the Angelic Alliance, we may need to "persuade" these lords to assist us.

**10. Barbarian Brothers — Yog**

> "Traveler's Be Warned" is on so many signs leading to this region that some even call it the "Land of the Be-warned."  Three Barbarian brothers rule this contested border between Erathia and Krewlod.  They hardly trust each other, let alone outsiders.  You've been warned.
>
> Crag and I have been scouring the contested border between Erathia and Krewlod for three Barbarian brothers, each holding one of the artifacts we seek.  However, we have been warned that the brothers hardly trust each other, let alone outsiders.  They will not give up the artifacts without a fight.  For that is what we Barbarians do best.

**11. Union — Gem**

> Sandro used his force to drive a wedge between the four heroes to stop them from building the Angelic Alliance.  If this powerful artifact is ever completed, Sandro's defeat seems likely and his plans of conquest will be ruined.
>
> We have collected the pieces of the Angelic Alliance, but Sandro learned of our efforts and blocked our path.  The bulk of his army now separates us from each other.  We must break through the Necromancer's army and converge upon one point.  Once we join the pieces of the Angelic Alliance, we can defeat Sandro.  If we fail, he will dominate all of Antagarich.

**12. Fall of Sandro — Gem**

> Sandro must be conquered to ensure that he will never rise to power and threaten Antagarich again.  The only certain way is to destroy the artifact that gave him his power and disperse the pieces throughout the world.
>
> We face the Necromancer in his lair.  The time of reckoning has come, but our vengeance must be carried out swiftly.  Sandro has sent for reinforcements from others within Deyja.  Slow moving as undead are, they will still be here in four months.  If we have not defeated Sandro by then, he will surely rule all of Antagarich.  I shudder at the thought.  Failure is simply not an option.


### 020_Specter_of_Power — Specter of Power

**1. Poison Fit for a King — Sandro**

> Lord Haart has agreed to take the poison to King Gryphonheart.  A clever ruse in the form of a border skirmish will plant the poison in Lord Haart's castle, and then you will leave the area to let him recover his lands and the poison.
>
> Lord Haart has agreed to take the Vial of Poison to King Gryphonheart.  All I must do is leave the Vial in Haart's castle after I raid it.  Fortunately for me, he is problem with overpopulation, so I will add his wasted peasants to my own ranks.  This will be a good day for harvesting skeletons!

**2. To Build a Tunnel — Sandro**

> The Dungeon Overlords are quite interested in your plans to overthrow Erathia.  There is one slight catch: they do not have enough gold to pay for the labor or the wood needed to build the actual tunnels.  You must provide them with the materials they need.
>
> To secure the Dungeon Overlord's support, I need to provide them with the gold and wood necessary to build a tunnel.  Wood is desperately needed to keep the tunnels from collapsing, and the gold is for paying the workers.  The greedy cave dwellers refuse to supply the raw materials themselves.  If I did not need their support, I would lock them up in their own underground dungeons!

**3. Kreegan Alliance — Sandro**

> The Kreegans do not believe your sincerity.  To them, Necromancers are weak wraiths feeding off the living, unable to initiate any good plan.  To prove your sincerity they want you to turn over the Eversmoking Ring of Sulfur.  A Druid stole it some years ago and they want it back.
>
> Kreegans are so arrogant, but I have need of their creatures to invade Erathia and crush her military.  Without their brute strength I would not be able to carry out all my plans.  So I will play their little game and find their precious artifact, the Eversmoking Ring of Sulfur.

**4. With Blinders On — Sandro**

> All of your plans are laid, but there is one lord who opposes the plan.  Finneas has told you his name is Lord Smedth and suggested that this insignificant bug be squashed.  You decide to do so yourself; he has been a minor thorn for some time now, always harassing you in court and attempting to usurp your position as Finneas Vilmar's closest aid.  It will be your pleasure to send him to Hell.
>
> Finneas has discovered that Smedth, an upstart lord, has gotten too ambitious.  He is trying to usurp my position as Finneas' top advisor.  To calm Finneas, I have agreed to take care of this little matter myself.  It will be my pleasure sending the conniving lich to Hell.

