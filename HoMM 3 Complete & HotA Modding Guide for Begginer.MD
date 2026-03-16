_HoMM 3 Complete & HotA Modding Guide for Begginers_  
http://heroescommunity.com/viewthread.php3?TID=47951&pagenumber=1
  
Hello everyone  
With this post I’m gonna try to explain the stuff I’ve learned about modding HoMM 3 Complete and HotA, here on this community, thanks to you.  
I also would like for you guys to help me enhance it, for all of us.  
  
First of all we are gonna need a few programs:  
A) MMArchive – https://drive.google.com/file/d/1zCsA1cRgBa8u3buxODNEmYWQOxHukZBF/view  
B) TextEdit – https://drive.google.com/file/d/1o-xqDFvSrjUzbEvxQNE_ERnrGHaqEhjm/view  
  
**Part 1: TXTs**  
  
**1st Step - MMArchive**  
  
We open MMArchive, in this Step it is used to extract the TXTs of the game so we can edit them later.  
  
**HoMM 3 Complete**  
We look for the archive “H3bitmap.lod” in the folder “Data” and open it.  
**HoMM 3 HotA**  
We look for the archives “HotA.lod” and “HotA_Ing.lod” in the folder “Data” and open them.  
  
We filter the archives by “.txt”.  
We look for the ones we are interested in, and extract them anywhere we want.  
  
List of some of them and their use:  
  
CRTRAITS: Stats, Value, Growth and AI Value of all Creatures.  
SPTRAITS: Stats, School, Level, AI Value and Text of all Spells.  
SSTRAITS: Text of all Secondary Skills.  
HOTRAITS: Initial quantity of creatures of the Heroes.  
HCTRAITS: Initial Stats, chance of Stats learned per Level, and chance of Skills learned per Level for each Class of Hero.  
CrBanks: Monster quantity and Treasure of Banks.  
Building: Cost of construction of every Building in every Town.  
Artraits: Some stuff about Artifacts and War Machines.  
And more...  
  
On HotA, note that the archives must be uploaded to it's correspondent place. There are two CRTRAITS (edit one, I think it is convenient to choose the one in Hota_Ing.lod, since the other TRAITS are there).  
**HotA.lod**  
Buildings  
CRTRAITS  
**Hota_Ing.lod**  
artraits  
CrBanks  
CRTRAITS  
HCTRAITS  
HOTRAITS  
SPTRAITS  
  
  
**2nd Step – TextEdit**  
  
We open the TXTs we want to edit.  
We study the table and once we understand it we edit the desired values.  
We save the changes.  
  
Personal recomendation:  
I made and Excel with all the Vanilla data and then made a copy of each page with my editions to keep track of what I am doing.  
Link to my Excel: https://docs.google.com/spreadsheets/d/1catQMGCOWmUR9iGTCkvspvyASTSCRgFA/edit?usp=sharing&ouid=115451005531609736023&rtpof=true&sd=true  
  
(Don't take into account Gold, AI Values and Growth of Creatures in it, that's some old stuff I modified and doesn't serve, you can look for them on Heroes Wiki)  
  
**3rd Step – MMArchive** (Again)  
  
We open MMArchive once again, this time to upload the changes.  
HoMM 3 Complete  
We open “H3bitmap.lod”.  
HoMM 3 HotA  
We open “HotA.lod” and “HotA_Ing.lod”.  
We go to “Edit/Add…”  
We look for the TXTs we edited and add them.  
  
----------  
  
**Part 2: Hex**  
  
We need a Hex Editor program like HxD https://drive.google.com/file/d/1DkzcZwv9CcHSSaX1lwpBGGedMHygP9sG/view  
  
We create a new shortcut with HD+ Mod, we will now edit that .exe.  
  
**Secondary Skills**  
  
**1st and only Step**  
  
We open HxD.  
We open the new .exe.  
  
Each pair of characters you see is 1 byte, the info we are gonna look for is divided in 4 parts of 4 bytes each (Normal, Basic, Advanced, Expert).  
  
We look for the offsets we want to modify.  
  
List of some of them:  
  
**HoMM 3 Complete**  
0023e998 (Luck)  
0023e9a8 (Leadership)  
0023e9b8 (Necromancy)  
0023e9c8 (Mysticism)  
0023e9d8 (Scouting)  
0023e9e8 (Archery)  
0023e9f8 (Offense)  
0023ea08 (Armorer)  
0023ea18 (Estates)  
0023ea28 (Eagle Eye)  
0023ea38 (Diplomacy)  
0023ea48 (Resistance)  
0023ea58 (Learning)  
0023ea68 (Logistics)  
0023ea78 (Sorcery)  
0023ea88 (Intelligence)  
0023ea98 (First Aid)  
  
**Secondary Skills not edited by HotA keep the same adress**  
  
**HotA**  
Mysticism  
0x00182616 Basic  
0x00182620 Advanced  
0x0018262A Expert  
  
Estates  
0x001825CE Basic  
0x001825DE Advanced  
0x001825E8 Expert  
  
(I'll to complete this list with the rest of the offsets as soon as I can)  
  
**How to find and edit them?**  
  
For example, we will try to find Necromancy (0023e9b8).  
We search for the line 0023e9b0 and we add 8 bytes to the right.  
We study the table and compare values so we know where we are located.  
On Necromancy we will find, the first 4 bytes will say “00”, and then "CD CC CC 3D CD CC 4C 3E 9A 99 99 3E", wich in this case will be:  
CD CC CC 3D = 10% (Basic)  
CD CC 4C 3E = 20% (Advanced)  
9A 99 99 3E = 30% (Expert)  
  
List of Values (they also serve as percentages):  
  
05 - CD CC 4C 3D  
07 - 29 5C 8F 3D  
10 - CD CC CC 3D  
14 - 29 5C 0F 3E  
15 - 9A 99 19 3E  
18 - EC 51 38 3E  
20 - CD CC 4C 3E  
25 - 00 00 80 3E  
30 - 9A 99 99 3E  
40 - CD CC CC 3E  
45 - 67 66 E6 3E  
60 - 9A 99 19 3F  
  
To find more values we need to use, for example, Windows calculator in “programmer mode” (I haven’t tested this), take into account the calculator will return results in Big Endian, while we need to put them in Little Endian in the .exe; so we have to translate them turning the code around.  
  
Example:  
Big Endian = 3D CC CC CD  
Little Endian = CD CC CC 3D  
  
Once we decide on wich changes to do, we interchange the values (without modifying the size of the archive nor the position of the characters).  
We now save the changes.  
  
Allright, that’s it for now.  
  
Stuff I'd like to add next:  
More complete guide for editing HotA's Secondary Skills.  
How to edit HotA's Creatures.  
Changing initial creature types for each hero.  
  
Happy modding!