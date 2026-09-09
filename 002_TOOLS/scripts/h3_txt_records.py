#!/usr/bin/env python3
"""
Shared, correct record-splitter for HoMM3's flat "resource" .TXT files
(GENRLTXT.TXT, ADVEVENT.TXT, ARTEVENT.TXT, HELP.TXT, CAMPTEXT.TXT, and
every other file injected by 006_build_mod.py alongside them).

THE BUG THIS FIXES: 002_build_raw.py and 006_build_mod.py both used to
count "lines" in these files with plain `text.splitlines()`, and compare
the English count against the Ukrainian count to decide whether it's safe
to inject a translation (see 006_build_mod.py's line_count_ok()). That is
WRONG for this file format and produced 16 false "line count mismatch"
warnings when this project first tried a from-scratch clean rebuild
(006_build_mod.py skipped injecting all 16, leaving them in English).

THE REAL FORMAT (confirmed against VCMI's lib/texts/CLegacyConfigParser.cpp
- an open-source, from-scratch reimplementation of the original game's own
loader, so its parsing rules ARE the original engine's rules, reverse
engineered): this is a tab-separated-values format, CSV-style, where:
  - Fields on one record are separated by a literal TAB character.
  - A record ends at a '\n' that occurs OUTSIDE an open double-quote span.
  - A '\n' (or '\r', or a literal tab) INSIDE an open double-quote span is
    just ordinary text content, not a separator - a single record's quoted
    field can legitimately span several physical lines in the file (this
    project found dozens of real examples: a short quoted title line like
    `"{Artifact}`, an intentional blank line, then the message body, all
    one record, closed by a lone `"` at the very end of the body).
  - '""' (two quotes back to back) is the CSV-style escape for one literal
    '"' character inside a quoted field. For this module's purposes
    (finding record BOUNDARIES, not decoding field values) this needs no
    special case: toggling the "inside a quote" flag on every '"' already
    treats '""' as two toggles that cancel out and leave the flag exactly
    where a real "insert one literal quote and stay in the same span"
    escape would - so the naive per-character toggle below is already
    correct for counting/splitting, even though it is NOT a full field
    decoder (it does not un-escape '""' to '"' in the output).
  - A bare '\r' (this project's files are all Windows CRLF) is discarded
    outright rather than treated as content or as a separator by itself -
    only the '\n' half of a CRLF pair ever ends a record.

Once records are counted this way instead of by raw physical line, most of
the 16 "mismatched" files turn out to already be correctly translated -
the "line count" the naive method saw was never the real record count.
See H3_TXT_FORMAT_NOTES.md for the full per-file investigation and the
handful of files that had a REAL problem (a stray unescaped quote, or
genuinely extra/reordered content) once compared this way.

Usage (library only, no __main__):
    from h3_txt_records import split_txt_records
    records = split_txt_records(open(path, 'rb').read().decode(encoding))
"""


def split_txt_records(text: str) -> list[str]:
    """In: text - the fully-decoded (cp1251 or cp1252) contents of one of
    this project's flat resource .TXT files. Out: list[str] - one entry
    per logical record, in file order, with '\\r' bytes removed and the
    field-separating '\\n' characters stripped (a record whose quoted
    field spans several physical lines keeps its embedded '\\n'/'\\r'
    bytes verbatim - see the module docstring for why this is right).
    A trailing blank line at end-of-file does not produce a phantom empty
    trailing record (matches how a text editor's "line count" would not
    count a final newline as one more line either)."""
    records = []
    current: list[str] = []
    in_quotes = False
    for ch in text:
        if ch == '\r':
            continue
        if ch == '"':
            in_quotes = not in_quotes
            current.append(ch)
        elif ch == '\n' and not in_quotes:
            records.append(''.join(current))
            current = []
        else:
            current.append(ch)
    if current:
        records.append(''.join(current))
    return records


def record_count(text: str) -> int:
    """In: text (same as split_txt_records). Out: int - just the count,
    for the common case (e.g. 006_build_mod.py's line_count_ok() check)
    where the records themselves aren't needed, only how many there are."""
    return len(split_txt_records(text))
