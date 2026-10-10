"""leitner.py: this is the spaced repetition system for my flashcards,
the idea is that every card lives in a box (1 to 5) and the higher the box, the longer it waits
before showing up again. So cards I know well drift to box 5 and I barely see them,
and cards I forget get sent back to box 1 and I see them a lot and that's the whole point, it allows 
me to spend my time on the ones i actually keep forgetting."""

from datetime import date, timedelta

intervals = {1: 1, 2: 2, 3: 4, 4: 7, 5: 14}
max_box= 5

"""AI help (Claude): I used Claude to help me turn my four buttons into this
dictionary of small functions instead of four if-statements. I chose the
intervals and the min(...) cap myself and tested that each button behaves right.
how it works: each button name maps to a tiny function that takes the current box
and returns the new box. so picking what happens is just a lookup, not a big if/else."""
options = {
    "again": lambda box: 1,
    "hard": lambda box: box,
    "good": lambda box: min(box + 1, max_box),
    "easy": lambda box: min(box + 2, max_box), 
}
# Error message
def review(card, rating, today=None):
    if rating not in options:
        raise ValueError(f"Unknown rating: {rating!r}")

    today = today or date.today()
    card.box = options[rating](card.box)
    card.next_review = (today + timedelta(days=intervals[card.box])).isoformat()
    card.last_reviewed = today.isoformat()
    return card


def is_due(card, today=None):
    today = today or date.today()
    return card.next_review <= today.isoformat()


def due_cards(cards, today=None):
    return [c for c in cards if is_due(c, today)]
