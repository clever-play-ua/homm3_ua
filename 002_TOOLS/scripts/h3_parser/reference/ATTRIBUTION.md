# Reference material attribution

Everything under `h3m_headers/`, `h3m_parsing/`, `h3clib/`, and `h3m_oa_class.h`
is copied from:

**potmdehex/homm3tools** — https://github.com/potmdehex/homm3tools
MIT License, Copyright (c) 2016 John Åkerblom.

```
The MIT License (MIT)
Copyright (c) 2016 John Åkerblom
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
```

`h3m_corpus.txt` is `h3m-The-Corpus.txt` from **HeroWO-js/h3m2json**
(https://github.com/HeroWO-js/h3m2json), released to the public domain /
Unlicense by the HeroWO.js project. Note: this document's description of
the *players* section (§ "if has_main_town == 0/<>0 and Nth byte below ==
0xFF") turned out to be **wrong** - it claims a `face` + name pstr always
follows in ROE even when the hero type is 0xFF, which the real
`H3M_PLAYER_EXT_ROE_DEFAULT` struct in homm3tools contradicts (that case is
just 2 bytes, no face/name at all). When the two sources disagreed, the
homm3tools C struct definitions were treated as authoritative, since they
were written against real game files and predate the corpus text.

`vcmi_campaign_format.md` is `docs/modders/Campaign_Format.md` from
**vcmi/vcmi** (https://github.com/vcmi/vcmi), GPL-2.0. It documents VCMI's
own modern `.vcmp` JSON campaign format, not the legacy binary `.h3c` this
tool actually parses - kept here only because its *logical* model (prolog/
epilog each with video+music+voice+text, "bonuses", "heroKeeps") is what
let us make sense of the anonymous bytes found empirically in real `.h3c`
files.
