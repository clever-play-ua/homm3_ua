"""
Regression suite for h3_txt_records.py - locks in the record-boundary rule
this project reverse-engineered (and cross-checked against VCMI's
lib/texts/CLegacyConfigParser.cpp, an independent from-scratch
reimplementation of the original game's own loader) after a from-scratch
clean rebuild surfaced 16 flat .TXT files that 006_build_mod.py refused to
inject due to a "line count mismatch" that turned out to be a bug in how
this project counted lines, not a real translation problem for most of
them. See H3_TXT_FORMAT_NOTES.md for the full investigation.
"""
from h3_txt_records import record_count, split_txt_records


def test_simple_single_line_records():
    text = "Head\nShoulders\nNeck"
    assert split_txt_records(text) == ["Head", "Shoulders", "Neck"]


def test_crlf_is_treated_same_as_lf():
    text = "Head\r\nShoulders\r\nNeck"
    assert split_txt_records(text) == ["Head", "Shoulders", "Neck"]


def test_quoted_field_can_span_multiple_physical_lines():
    """The real, repeatedly-observed pattern in ADVEVENT.TXT/GENRLTXT.TXT:
    a quoted record whose content includes a blank line - this is ONE
    record, not three."""
    text = '"{Artifact}\n\nYou have found a mighty relic."\nNext entry'
    records = split_txt_records(text)
    assert len(records) == 2
    assert records[0] == '"{Artifact}\n\nYou have found a mighty relic."'
    assert records[1] == 'Next entry'


def test_escaped_double_quote_does_not_end_the_record():
    """'""' is the CSV-style escape for one literal quote character inside
    a quoted field - it must NOT be treated as closing the field early."""
    text = '"The Arena guards say ""Go away!"" and slam the gate."\nNext'
    records = split_txt_records(text)
    assert len(records) == 2
    assert records[1] == 'Next'


def test_trailing_newline_does_not_create_a_phantom_empty_record():
    text = "One\nTwo\n"
    assert split_txt_records(text) == ["One", "Two"]


def test_no_trailing_newline_still_captures_the_last_record():
    text = "One\nTwo"
    assert split_txt_records(text) == ["One", "Two"]


def test_empty_lines_are_real_records_when_outside_quotes():
    """A genuinely blank line OUTSIDE any quoted span (as opposed to one
    embedded inside a quoted multi-line record - see the test above) is
    still its own, real, empty record - these show up throughout the
    resource files as intentional spacers between numbered sections."""
    text = "One\n\nTwo"
    assert split_txt_records(text) == ["One", "", "Two"]


def test_record_count_matches_len_of_split():
    text = '"{Artifact}\n\nBody."\nNext\nLast'
    assert record_count(text) == len(split_txt_records(text))


def test_real_artifact_pattern_from_advevent_txt():
    """A trimmed-down, real excerpt of ADVEVENT.TXT's actual structure
    (three 'title + blank + would-be body' records back to back) - this
    is the exact shape that made naive `.splitlines()` counting wrong."""
    text = (
        '"You cannot pick up this artifact, you already have a full load!"\n'
        '"{Artifact}\n'
        '\n'
        'placeholder"\n'
        "You've found the humble dwelling of a withered hermit.\n"
        '"{Artifact}\n'
        '\n'
        'placeholder"\n'
    )
    records = split_txt_records(text)
    assert len(records) == 4
