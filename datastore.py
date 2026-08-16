# datastore.py
# this is the "database" of my app, except it's just two json files (SC-05):
#   data/seed_data.json  -> the built-in content i made (read only, never gets changed)
#   data/user_data.json  -> everything the user adds or changes
#
# AI help (Claude): json was new to me, so Claude helped me understand how to actually
# save and load it (json.dump to write a python dict to a file, json.load to read it back).
# once i got it i wrote the rest of this file myself.
#
# the plan: when i READ i mix the two files together so my content and the user's show up
# together, but when i SAVE i only ever touch user_data.json. that way a bug in "add" or
# "delete" can never wreck my built-in content.

import json
import os
from datetime import date

from models import (Definition, Diagram, RealWorldExample, StudyKit,
                    Flashcard, Note)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SEED_FILE = os.path.join(DATA_DIR, "seed_data.json")
USER_FILE = os.path.join(DATA_DIR, "user_data.json")

# which class to rebuild each collection with (so "definitions" -> Definition, etc.)
MODEL_FOR = {
    "definitions": Definition,
    "diagrams": Diagram,
    "examples": RealWorldExample,
    "kits": StudyKit,
    "notes": Note,
    "flashcards": Flashcard,
}

# what a brand new (empty) user file looks like
EMPTY_USER_DATA = {
    "definitions": [],
    "diagrams": [],
    "examples": [],
    "kits": [],
    "notes": [],
    "flashcards": [],
    "library": [],          # things the user saved, like [{"type": ..., "id": ...}]
    "example_notes": {},    # private notes on examples: rwe_id -> list of notes
}


class DataStore:
    # loads both files once when the app starts, then keeps them in memory

    def __init__(self, seed_file=SEED_FILE, user_file=USER_FILE):
        self.seed_file = seed_file
        self.user_file = user_file
        with open(self.seed_file, encoding="utf-8") as f:
            self.seed = json.load(f)       # read my built-in content
        self.user = self._load_user()

    def _load_user(self):
        # first time the app ever runs there's no user file yet, so make an empty one
        if not os.path.exists(self.user_file):
            # json.loads(json.dumps(...)) is a quick way to deep-copy the dict so i don't
            # accidentally edit the EMPTY_USER_DATA template itself (Claude showed me this).
            data = json.loads(json.dumps(EMPTY_USER_DATA))
            with open(self.user_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return data
        with open(self.user_file, encoding="utf-8") as f:
            data = json.load(f)
        # if i added a new key later, older save files won't have it, so add any missing ones
        # so the app doesn't crash on an old save
        for key, empty in EMPTY_USER_DATA.items():
            data.setdefault(key, json.loads(json.dumps(empty)))
        return data

    def save(self):
        # write everything the user has to the file. this is what makes stuff persist (SC-05)
        with open(self.user_file, "w", encoding="utf-8") as f:
            json.dump(self.user, f, indent=2, ensure_ascii=False)

    # ---------------- reading ----------------

    def all(self, collection):
        # give me everything in a collection: my built-in stuff first, then the user's.
        # from_dict turns each saved dictionary back into a proper object.
        cls = MODEL_FOR[collection]
        seed = [cls.from_dict(d) for d in self.seed.get(collection, [])]
        user = [cls.from_dict(d) for d in self.user.get(collection, [])]
        return seed + user

    def get(self, collection, obj_id):
        # find one thing by its id (or None if it's not there). i use this to follow the
        # links, e.g. a study kit stores a diagram_id and i get() the actual diagram.
        for obj in self.all(collection):
            if obj.id == obj_id:
                return obj
        return None

    def filtered(self, collection, section=None, subtopic=None, level=None,
                 country=None):
        # the filtering for the search/filter buttons (SC-03).
        items = self.all(collection)
        if section:
            items = [i for i in items if i.section == section]
        if subtopic:
            items = [i for i in items if i.subtopic == subtopic]
        if level and level != "Both":
            # important bit: if i pick "SL" i still want the "Both" items too, because a
            # "Both" term applies to SL students. this is the bug i found in testing (T-03)
            # where SL was hiding the Both items. getattr(...,"Both") is just in case the
            # object has no level (examples don't).
            items = [i for i in items
                     if getattr(i, "level", "Both") in (level, "Both")]
        if country:
            items = [i for i in items
                     if getattr(i, "country", None) == country]
        return items

    # ---------------- writing (only ever the user file) ----------------

    def add(self, collection, obj):
        self.user[collection].append(obj.to_dict())   # store it as a dict
        self.save()
        return obj

    def is_user_item(self, collection, obj_id):
        # only stuff the USER made can be edited/deleted. my built-in content is protected.
        # any() is True if at least one user item has this id.
        return any(d["id"] == obj_id for d in self.user.get(collection, []))

    def update(self, collection, obj_id, fields):
        # find the user item with this id and change the fields that were sent
        for d in self.user.get(collection, []):
            if d["id"] == obj_id:
                for key, value in fields.items():
                    if key in d and key != "id":   # never let the id be changed
                        d[key] = value
                if "updated" in d:
                    d["updated"] = date.today().isoformat()
                self.save()
                return True
        return False

    def delete(self, collection, obj_id):
        before = len(self.user[collection])
        # rebuild the list without the one i'm deleting
        self.user[collection] = [d for d in self.user[collection]
                                 if d["id"] != obj_id]
        if len(self.user[collection]) == before:
            return False    # nothing was removed (id wasn't there)
        # cascade: because things link by id, i also have to remove any flashcard or saved
        # library item that pointed at this, otherwise they'd point at something that's gone.
        self.user["flashcards"] = [f for f in self.user["flashcards"]
                                   if f["source_id"] != obj_id]
        self.user["library"] = [s for s in self.user["library"]
                                if s["id"] != obj_id]
        self.save()
        return True

    # ---------------- library (the save/bookmark feature) ----------------

    def library_items(self):
        return self.user["library"]

    def in_library(self, obj_id):
        return any(s["id"] == obj_id for s in self.user["library"])

    def toggle_library(self, item_type, obj_id):
        # one button that saves if it's not saved, and unsaves if it already is
        if self.in_library(obj_id):
            self.user["library"] = [s for s in self.user["library"]
                                    if s["id"] != obj_id]
            saved = False
        else:
            self.user["library"].append({"type": item_type, "id": obj_id})
            saved = True
        self.save()
        return saved

    # ---------------- private notes on examples ----------------

    def example_notes(self, rwe_id):
        return self.user["example_notes"].get(rwe_id, [])

    def add_example_note(self, rwe_id, text):
        note = {"text": text, "created": date.today().isoformat()}
        # setdefault makes an empty list first if this example has no notes yet
        self.user["example_notes"].setdefault(rwe_id, []).append(note)
        self.save()
        return note

    # ---------------- flashcards ----------------

    def flashcards(self):
        return [Flashcard.from_dict(d) for d in self.user["flashcards"]]

    def has_flashcard(self, source_id):
        # so i don't make two flashcards for the same thing
        return any(f["source_id"] == source_id
                   for f in self.user["flashcards"])

    def save_flashcard(self, card):
        # if a card with this id already exists, replace it (this is how a review gets saved),
        # otherwise it's a new card so just add it
        for i, d in enumerate(self.user["flashcards"]):
            if d["id"] == card.id:
                self.user["flashcards"][i] = card.to_dict()
                self.save()
                return card
        self.user["flashcards"].append(card.to_dict())
        self.save()
        return card

    # ---------------- flashcard front/back ----------------

    def card_faces(self, card):
        # builds what shows on the front and back of a card, depending on what it was made from.
        # i only store the id on the card, so i look up the real object here. that means if i
        # edit the definition later, the flashcard updates on its own (no old copy).
        if card.source_type == "definition":
            obj = self.get("definitions", card.source_id)
            if obj:
                return {"front": obj.term, "back": obj.definition,
                        "image": None, "tag": f"{obj.subtopic} · {obj.level}"}
        elif card.source_type == "diagram":
            obj = self.get("diagrams", card.source_id)
            if obj:
                return {"front": obj.title, "back": obj.explanation,
                        "image": obj.image, "tag": f"{obj.subtopic} · {obj.level}"}
        elif card.source_type == "rwe":
            obj = self.get("examples", card.source_id)
            if obj:
                return {"front": f"{obj.subtopic}: {obj.title}",
                        "back": obj.description, "image": None,
                        "tag": f"{obj.country}"}
        return None
