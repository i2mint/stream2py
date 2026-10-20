"""The tag-events example: key presses become timestamped tags saved as JSON."""

import io
import json

from stream2py.examples.tag_events import EventTagger, main, tag_keys


def _clock(*times):
    it = iter(times)
    return lambda: next(it)


def test_press_records_tag_at_position_and_ignores_unmapped_keys():
    tagger = EventTagger({"a": "applause"}, position=_clock(1.23456, 9.0))
    assert tag_keys(tagger, "xaa")[0].t == 1.235
    assert [e.tag for e in tagger.events] == ["applause", "applause"]


def test_save_roundtrip(tmp_path):
    tagger = EventTagger({"l": "laughter"}, position=_clock(2.0))
    tagger.press("l")
    path = tagger.save(tmp_path / "t.json", media="talk.wav")
    assert json.loads(path.read_text()) == {
        "media": "talk.wav",
        "events": [{"t": 2.0, "tag": "laughter", "key": "l"}],
    }


def test_cli_reads_keys_until_q(tmp_path):
    out = tmp_path / "o.json"
    rc = main(
        ["--media", "m.wav", "--out", str(out), "--keymap", "a=applause"],
        stdin=io.StringIO("a\nz\na\nq\na\n"),
    )
    saved = json.loads(out.read_text())
    assert rc == 0 and saved["media"] == "m.wav"
    assert [e["tag"] for e in saved["events"]] == ["applause", "applause"]
