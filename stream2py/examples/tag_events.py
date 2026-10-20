"""Tag events on a timeline with key presses, and save the timestamped tags.

The smallest useful version of "tag sound events": while audio plays (live or from a file,
played by whatever you like), you press a key per event type and each press is stored as
``{"t": <seconds>, "tag": <name>, "key": <key>}`` next to the media it refers to.

The two things that vary are injectable, so the tagger works with any player or key source:

* ``position`` - ``() -> float``, seconds into the media at the moment of a press. Default:
  wall-clock seconds since the tagger was created (right for live sources). With a player,
  pass its current-position getter; with a ``stream2py`` buffer, a function of the latest
  item's timestamp.
* the keys themselves - anything that yields them (:func:`tag_keys`): ``sys.stdin`` lines in
  the bundled CLI, a GUI callback, a MIDI pad.

Run it (type a key, then Enter; empty input or ``q`` ends)::

    python -m stream2py.examples.tag_events --media talk.wav --out talk.tags.json \\
        --keymap a=applause --keymap l=laughter

>>> now = iter([0.0, 1.5, 4.0])
>>> tagger = EventTagger({"a": "applause", "l": "laughter"}, position=lambda: next(now))
>>> [tagger.press(k) for k in "al"] == tagger.events
True
>>> tagger.events[1]
TagEvent(t=1.5, tag='laughter', key='l')
>>> tagger.press("x") is None  # a key without a tag is ignored
True
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

__all__ = ["TagEvent", "EventTagger", "tag_keys", "main"]


@dataclass(frozen=True)
class TagEvent:
    """One tagged moment: ``t`` seconds into the media."""

    t: float
    tag: str
    key: str


def _wall_clock_position() -> Callable[[], float]:
    start = time.monotonic()
    return lambda: time.monotonic() - start


@dataclass
class EventTagger:
    """Turn key presses into timestamped :class:`TagEvent`s (``keymap``: key -> tag name)."""

    keymap: Mapping[str, str]
    position: Callable[[], float] = field(default_factory=_wall_clock_position)
    events: list[TagEvent] = field(default_factory=list)

    def press(self, key: str) -> TagEvent | None:
        """Record ``key``'s tag at the current position; ``None`` if the key has no tag."""
        tag = self.keymap.get(key)
        if tag is None:
            return None
        event = TagEvent(round(float(self.position()), 3), tag, key)
        self.events.append(event)
        return event

    def to_dict(self, *, media: str | None = None) -> dict:
        return {"media": media, "events": [asdict(e) for e in self.events]}

    def save(self, path: str | Path, *, media: str | None = None) -> Path:
        """Write the events (and the ``media`` they refer to) as JSON."""
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(media=media), indent=2))
        return path


def tag_keys(tagger: EventTagger, keys: Iterable[str]) -> list[TagEvent]:
    """Feed ``keys`` to ``tagger``; return the events recorded for them."""
    return [e for k in keys if (e := tagger.press(k)) is not None]


def _parse_keymap(pairs: Iterable[str]) -> dict[str, str]:
    keymap = {}
    for pair in pairs:
        key, sep, tag = pair.partition("=")
        if not (sep and key and tag):
            raise argparse.ArgumentTypeError(f"expected KEY=TAG, got {pair!r}")
        keymap[key] = tag
    return keymap


def main(argv: list[str] | None = None, *, stdin=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--media", help="the audio file (or source name) the tags refer to")
    parser.add_argument("--out", default="tags.json", help="where to save the tags")
    parser.add_argument("--keymap", action="append", default=[], metavar="KEY=TAG")
    args = parser.parse_args(argv)
    keymap = _parse_keymap(args.keymap) or {"a": "event"}
    tagger = EventTagger(keymap)
    print(f"keys: {keymap}; key + Enter to tag, q to end", file=sys.stderr)
    for line in stdin or sys.stdin:
        key = line.strip()
        if key in ("", "q"):
            break
        tagger.press(key)
    print(tagger.save(args.out, media=args.media))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
