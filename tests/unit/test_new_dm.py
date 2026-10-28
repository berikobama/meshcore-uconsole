"""Starting a DM from the Messages view: which contacts the picker offers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from meshcore_console.core.models import Peer
from meshcore_console.ui_gtk.views.messages import dm_candidates

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


def peer(name: str, key: str, minutes_ago: int | None = None, **kw) -> Peer:
    heard = NOW - timedelta(minutes=minutes_ago) if minutes_ago is not None else None
    return Peer(peer_id=key, display_name=name, public_key=key, last_advert_time=heard, **kw)


ALICE = peer("Alice", "a1" * 32, 5)
BOB = peer("Bob", "b0" * 32, 1)
MALLORY = peer("Mallory", "ce" * 32, 60, is_favorite=True)
HILLTOP = peer("Hilltop", "13" * 32, 2, is_repeater=True)
ME = peer("DF9ES", "46" * 32, 30)
ALL = [ALICE, BOB, MALLORY, HILLTOP, ME]


def names(peers: list[Peer]) -> list[str]:
    return [p.display_name for p in peers]


def test_no_query_lists_contacts_favourites_first_then_most_recently_heard() -> None:
    # no repeater (they take no messages), not this device (a stale self row)
    assert names(dm_candidates(ALL, "", ME.public_key)) == ["Mallory", "Bob", "Alice"]


def test_query_matches_part_of_the_name_ignoring_case_prefix_matches_first() -> None:
    assert names(dm_candidates(ALL, "AL", ME.public_key)) == ["Alice", "Mallory"]


def test_query_matches_the_start_of_the_public_key() -> None:
    # tells apart two contacts with the same name
    assert names(dm_candidates(ALL, "b0b0", ME.public_key)) == ["Bob"]
    assert dm_candidates(ALL, "0b0b", ME.public_key) == []  # not inside the key


def test_never_heard_contacts_come_last() -> None:
    quiet = peer("Quinn", "99" * 32)
    assert names(dm_candidates([quiet, ALICE], "")) == ["Alice", "Quinn"]


def test_a_channel_message_is_answered_as_the_contact_of_that_name() -> None:
    from meshcore_console.core.models import Message
    from meshcore_console.ui_gtk.views.messages import sender_contact

    def said(sender: str, **kw) -> Message:
        return Message(message_id="m", sender_id=sender, body="hi", **kw)

    assert sender_contact(said("Bob"), ALL) is BOB
    assert sender_contact(said("bob"), ALL) is None  # the name is all there is: exact
    assert sender_contact(said("Carol"), ALL) is None  # advert not heard yet
    assert sender_contact(said("Hilltop"), ALL) is None  # a repeater takes no DMs
    assert sender_contact(said("Bob", is_outgoing=True), ALL) is None
