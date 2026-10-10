"""datastore.py: this is the equivalent of the database of my app, and conteins two json files:
data/dev_data.json (the built-in coentent I made, that is read only) 
and data/user_data.json (Everything the user adds or changes)

AI help (Claude): json was new to me, so Claude helped me understand how to actually
save and load it (json.dump to write a python dict to a file, json.load to read it back).
once I got it I wrote the rest of this file myself.

the plan: when I read I mix the two files together so my content and the user's show up
together, but when I save I only ever touch user_data.json. that way a bug in "add" or
"delete" can never wreck my built-in content."""

import json
import os
from datetime import date

from models import (Definition, Diagram, RealWorldExample, StudyKit,
                    Flashcard, Note)

data_dir = os.path.join(os.path.dirname(__file__), "data")
dev_file = os.path.join(data_dir, "dev_data.json")
user_file = os.path.join(data_dir, "user_data.json")
# AI help (Claude): I asked Claude to show me how to find the path to extract all the data I needed, since I was really confused with it.

model_for = {
    "definitions": Definition,
    "diagrams": Diagram,
    "examples": RealWorldExample,
    "kits": StudyKit,
    "notes": Note,
    "flashcards": Flashcard,
}

empty_user = {
    "definitions": [],
    "diagrams": [],
    "examples": [],
    "kits": [],
    "notes": [],
    "flashcards": [],
    "library": [], 
    "example_notes": {},    
}

class DataStore:
    
    def __init__(self, dev_file=dev_file, user_file=user_file):
        self.dev_file = dev_file
        self.user_file = user_file
        with open(self.dev_file, encoding="utf-8") as f:
            self.dev = json.load(f)
        self.user = self._load_user()

    def _load_user(self):
        if not os.path.exists(self.user_file):
            data = json.loads(json.dumps(empty_user))
            with open(self.user_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return data
        with open(self.user_file, encoding="utf-8") as f:
            data = json.load(f)
        for key, empty in empty_user.items():
            data.setdefault(key, json.loads(json.dumps(empty)))
        return data

    def save(self):
        with open(self.user_file, "w", encoding="utf-8") as f:
            json.dump(self.user, f, indent=2, ensure_ascii=False)

    # reading 

    def all(self, collection):
        cls = model_for[collection]
        dev = [cls.from_dict(d) for d in self.dev.get(collection, [])]
        user = [cls.from_dict(d) for d in self.user.get(collection, [])]
        return dev + user

    def get(self, collection, obj_id):
        for obj in self.all(collection):
            if obj.id == obj_id:
                return obj
        return None

    def filtered(self, collection, section=None, subtopic=None, level=None,
                 country=None):
        items = self.all(collection)
        if section:
            items = [i for i in items if i.section == section]
        if subtopic:
            items = [i for i in items if i.subtopic == subtopic]
        if level and level != "Both":
            items = [i for i in items
                     if getattr(i, "level", "Both") in (level, "Both")]
        if country:
            items = [i for i in items
                     if getattr(i, "country", None) == country]
        return items

    #  writing 

    def add(self, collection, obj):
        self.user[collection].append(obj.to_dict())   
        self.save()
        return obj

    def is_user_item(self, collection, obj_id):
        return any(d["id"] == obj_id for d in self.user.get(collection, []))

    def update(self, collection, obj_id, fields):
        for d in self.user.get(collection, []):
            if d["id"] == obj_id:
                for key, value in fields.items():
                    if key in d and key != "id":  
                        d[key] = value
                if "updated" in d:
                    d["updated"] = date.today().isoformat()
                self.save()
                return True
        return False

    def delete(self, collection, obj_id):
        before = len(self.user[collection])
        self.user[collection] = [d for d in self.user[collection]
                                 if d["id"] != obj_id]
        if len(self.user[collection]) == before:
            return False
        self.user["flashcards"] = [f for f in self.user["flashcards"]
                                   if f["source_id"] != obj_id]
        self.user["library"] = [s for s in self.user["library"]
                                if s["id"] != obj_id]
        self.save()
        return True

    #  library 

    def library_items(self):
        return self.user["library"]

    def in_library(self, obj_id):
        return any(s["id"] == obj_id for s in self.user["library"])

    def toggle_library(self, item_type, obj_id):
        if self.in_library(obj_id):
            self.user["library"] = [s for s in self.user["library"]
                                    if s["id"] != obj_id]
            saved = False
        else:
            self.user["library"].append({"type": item_type, "id": obj_id})
            saved = True
        self.save()
        return saved

    # private notes on examples 

    def example_notes(self, rwe_id):
        return self.user["example_notes"].get(rwe_id, [])

    def add_example_note(self, rwe_id, text):
        note = {"text": text, "created": date.today().isoformat()}
        self.user["example_notes"].setdefault(rwe_id, []).append(note)
        self.save()
        return note

    # flashcards 

    def flashcards(self):
        return [Flashcard.from_dict(d) for d in self.user["flashcards"]]

    def has_flashcard(self, source_id):
        return any(f["source_id"] == source_id
                   for f in self.user["flashcards"])

    def save_flashcard(self, card):
        for i, d in enumerate(self.user["flashcards"]):
            if d["id"] == card.id:
                self.user["flashcards"][i] = card.to_dict()
                self.save()
                return card
        self.user["flashcards"].append(card.to_dict())
        self.save()
        return card

    # flashcard front/back 

    def card_faces(self, card):
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
