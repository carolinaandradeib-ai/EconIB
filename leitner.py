# leitner.py
# this is the spaced repetition system for my flashcards (SC-04).
# idea: every card lives in a box (1 to 5). the higher the box, the longer it waits
# before showing up again. so cards i know well drift to box 5 and i barely see them,
# and cards i forget get sent back to box 1 and i see them a lot. that's the whole point,
# i spend my time on the ones i actually keep forgetting.

from datetime import date, timedelta

# box -> how many days to wait before the next review
INTERVALS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 14}
MAX_BOX = 5

# AI help (Claude): I used Claude to help me turn my four buttons into this
# dictionary of small functions instead of four if-statements. I chose the
# intervals and the min(...) cap myself and tested that each button behaves right.
# how it works: each button name maps to a tiny function that takes the current box
# and returns the new box. so picking what happens is just a lookup, not a big if/else.
RATING_MOVES = {
    "again": lambda box: 1,                    # forgot it -> straight back to box 1
    "hard": lambda box: box,                   # struggled -> stay in the same box
    "good": lambda box: min(box + 1, MAX_BOX),  # got it -> up one box (min stops it going past 5)
    "easy": lambda box: min(box + 2, MAX_BOX),  # too easy -> jump up two boxes
}


def review(card, rating, today=None):
    # this runs when i press a button on a card.
    # if the rating isn't one of my 4 buttons something is wrong, so stop before it breaks.
    if rating not in RATING_MOVES:
        raise ValueError(f"Unknown rating: {rating!r}")

    today = today or date.today()
    card.box = RATING_MOVES[rating](card.box)   # move the box using the dict above
    # work out the next date: today + however many days that box waits.
    # timedelta does the calendar maths for me so "7 days from now" lands on the right date.
    # i save it as text (isoformat) because json can't store an actual date object.
    card.next_review = (today + timedelta(days=INTERVALS[card.box])).isoformat()
    card.last_reviewed = today.isoformat()
    return card


def is_due(card, today=None):
    # a card is "due" if its next_review is today or already in the past.
    # note: next_review is a text date like "2026-08-15". comparing text dates only works
    # because in this format (year-month-day) they sort in the same order as real dates,
    # so <= on the strings gives the right answer. (claude pointed this out to me.)
    today = today or date.today()
    return card.next_review <= today.isoformat()


def due_cards(cards, today=None):
    # keep only the cards that are due right now
    return [c for c in cards if is_due(c, today)]
